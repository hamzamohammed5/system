"""
ui/tabs/offers_tab.py
=====================
تبويب العروض — تسعير مجموعة منتجات بهامش ربح موحد.

الواجهة:
  ① فورم إنشاء/تعديل العرض (اسم + هامش + ملاحظات)
  ② إضافة منتجات للعرض (اختيار منتج + كمية)
  ③ جدول العروض المحفوظة مع FilterBar
  ④ لوحة تفاصيل العرض المحدد (breakdown)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QTabWidget, QFrame, QScrollArea,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QLabel, QMessageBox, QHeaderView,
    QTextEdit, QComboBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from db.connection  import get_connection
from db.items_repo  import fetch_items_by_type
from db.offers_repo import (
    fetch_all_offers, fetch_offer, fetch_offer_items,
    insert_offer, update_offer, delete_offer,
    replace_offer_items, calc_offer_summary,
)
from models.costing import calc_cost
from ui.helpers     import make_table, buttons_row, section_label, danger_button, confirm_delete
from ui.widgets.filter_bar import FilterBar
from ui.events import bus

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #ffe0b2; }
"""


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


# ══════════════════════════════════════════════════════════
# صف منتج واحد في العرض
# ══════════════════════════════════════════════════════════

class _OfferItemRow(QFrame):
    """صف اختيار منتج + كمية داخل فورم العرض."""

    def __init__(self, conn, on_remove, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._on_remove = on_remove
        self._build()
        self._load_products()
        bus.data_changed.connect(self._load_products)

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8e8e8;
                border-radius: 6px;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        # ── بحث ──
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث بالاسم...")
        self.inp_search.setFixedWidth(130)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 6px; font-size: 11px;
            }
            QLineEdit:focus { border-color: #e65100; }
        """)
        self.inp_search.textChanged.connect(self._on_search)

        # ── اختيار المنتج ──
        self.cmb_product = QComboBox()
        self.cmb_product.setSizePolicy(
            self.cmb_product.sizePolicy().horizontalPolicy(),
            self.cmb_product.sizePolicy().verticalPolicy()
        )
        self.cmb_product.setMinimumWidth(180)
        self.cmb_product.setMinimumHeight(28)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        # ── التكلفة ──
        self.lbl_cost = QLabel("─")
        self.lbl_cost.setFixedWidth(80)
        self.lbl_cost.setStyleSheet(
            "color:#1565c0; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_cost.setAlignment(Qt.AlignCenter)

        # ── الكمية ──
        lbl_qty = QLabel("الكمية:")
        lbl_qty.setStyleSheet("font-size:11px; background:transparent; border:none;")
        self.sp_qty = _spin(99999, 4)
        self.sp_qty.setValue(1.0)
        self.sp_qty.setFixedWidth(90)
        self.sp_qty.valueChanged.connect(self._on_product_changed)

        # ── إجمالي السطر ──
        self.lbl_line = QLabel("─")
        self.lbl_line.setFixedWidth(90)
        self.lbl_line.setStyleSheet(
            "color:#1a6e1a; font-weight:bold; font-size:11px;"
            "background:transparent; border:none;"
        )
        self.lbl_line.setAlignment(Qt.AlignCenter)

        # ── حذف ──
        btn_del = QPushButton("❌")
        btn_del.setFixedSize(28, 28)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; font-size:13px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))

        lay.addWidget(self.inp_search)
        lay.addWidget(self.cmb_product, stretch=1)
        lay.addWidget(QLabel("تكلفة:"))
        lay.addWidget(self.lbl_cost)
        lay.addWidget(lbl_qty)
        lay.addWidget(self.sp_qty)
        lay.addWidget(QLabel("إجمالي:"))
        lay.addWidget(self.lbl_line)
        lay.addWidget(btn_del)

    def _load_products(self, filter_text: str = ""):
        prev_id = self.get_item_id()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()

        q = filter_text.lower()
        for item_type in ("final", "semi"):
            rows = fetch_items_by_type(self.conn, item_type)
            icon = "🏭" if item_type == "final" else "🔧"
            for row in rows:
                name = row["name"]
                if q and q not in name.lower():
                    continue
                self.cmb_product.addItem(f"{icon} {name}", row["id"])

        self.cmb_product.blockSignals(False)

        # استعادة الاختيار
        if prev_id is not None:
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev_id:
                    self.cmb_product.setCurrentIndex(i)
                    break

        self._on_product_changed()

    def _on_search(self, text: str):
        self._load_products(filter_text=text.strip())

    def _on_product_changed(self):
        item_id = self.get_item_id()
        if item_id is None:
            self.lbl_cost.setText("─")
            self.lbl_line.setText("─")
            return
        cost      = calc_cost(self.conn, item_id)
        line_cost = cost * self.sp_qty.value()
        self.lbl_cost.setText(f"{cost:.2f}")
        self.lbl_line.setText(f"{line_cost:.2f}")

    def get_item_id(self):
        return self.cmb_product.currentData()

    def get_qty(self) -> float:
        return self.sp_qty.value()

    def get_values(self) -> tuple | None:
        item_id = self.get_item_id()
        if item_id is None:
            return None
        return item_id, self.sp_qty.value()

    def set_values(self, item_id: int, qty: float):
        for i in range(self.cmb_product.count()):
            if self.cmb_product.itemData(i) == item_id:
                self.cmb_product.setCurrentIndex(i)
                break
        self.sp_qty.setValue(qty)


# ══════════════════════════════════════════════════════════
# فورم العرض
# ══════════════════════════════════════════════════════════

class _OfferForm(QWidget):
    def __init__(self, conn, on_saved, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_saved  = on_saved
        self._editing_id = None
        self._item_rows: list[_OfferItemRow] = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── رأس الفورم ──
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ffe0b2;
                border-radius: 8px;
            }
        """)
        h_lay = QFormLayout(header)
        h_lay.setContentsMargins(14, 12, 14, 12)
        h_lay.setSpacing(8)
        h_lay.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── عرض جديد ───")
        self.lbl_mode.setStyleSheet(
            "font-weight:bold; color:#e65100; font-size:12px;"
        )

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: عرض رمضان، باقة العيد...")
        self.inp_name.setMinimumHeight(32)

        self.sp_margin = _spin(1000, 2)
        self.sp_margin.setSuffix("  %")
        self.sp_margin.setValue(30)
        self.sp_margin.setFixedWidth(120)
        self.sp_margin.valueChanged.connect(self._update_totals)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        self.inp_notes.setMinimumHeight(30)

        # ملخص أسفل الهيدر
        self.lbl_summary = QLabel("التكلفة: ─   │   السعر: ─   │   الربح: ─")
        self.lbl_summary.setStyleSheet(
            "color:#e65100; font-weight:bold; font-size:12px;"
            "background:#fff3e0; border:1px solid #ffcc80;"
            "border-radius:4px; padding:6px 12px;"
        )
        self.lbl_summary.setAlignment(Qt.AlignCenter)

        h_lay.addRow(self.lbl_mode)
        h_lay.addRow("اسم العرض :", self.inp_name)

        margin_row = QHBoxLayout()
        margin_row.addWidget(self.sp_margin)
        margin_row.addWidget(QLabel("  (هامش الربح يُضرب في إجمالي التكلفة)"))
        margin_row.addStretch()
        h_lay.addRow("هامش الربح :", margin_row)
        h_lay.addRow("ملاحظات :", self.inp_notes)
        h_lay.addRow("", self.lbl_summary)

        root.addWidget(header)

        # ── رؤوس الأعمدة ──
        col_headers = QWidget()
        col_headers.setStyleSheet("background:transparent;")
        ch_lay = QHBoxLayout(col_headers)
        ch_lay.setContentsMargins(8, 0, 8, 0)
        ch_lay.setSpacing(8)

        def _hdr(text, w=None, stretch=0):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#888;"
                "border-bottom:1px solid #eee; padding-bottom:2px;"
                "background:transparent;"
            )
            if w:
                lbl.setFixedWidth(w)
            ch_lay.addWidget(lbl, stretch=stretch)

        _hdr("بحث", 130)
        _hdr("المنتج", stretch=1)
        _hdr("تكلفة/وحدة", 90)
        _hdr("الكمية", 90)
        _hdr("إجمالي السطر", 90)
        _hdr("", 28)
        root.addWidget(col_headers)

        # ── منطقة الصفوف ──
        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background:transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(4)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        self._rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_container)
        scroll.setMinimumHeight(120)
        scroll.setMaximumHeight(280)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ffe0b2;
                border-radius: 6px;
                background: #fffaf5;
            }
        """)
        root.addWidget(scroll, stretch=1)

        # ── أزرار ──
        btn_add_row = QPushButton("➕  إضافة منتج")
        btn_add_row.setMinimumHeight(30)
        btn_add_row.setStyleSheet(
            "QPushButton { background:#fff3e0; border:1px solid #ffcc80;"
            "border-radius:4px; color:#e65100; font-weight:bold; padding:4px 12px; }"
            "QPushButton:hover { background:#ffe0b2; }"
        )
        btn_add_row.clicked.connect(lambda: self._add_item_row())

        self.btn_save = QPushButton("💾  حفظ العرض")
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #e65100; color: white;
                font-weight: bold; border-radius: 6px; padding: 0 18px;
            }
            QPushButton:hover { background: #bf360c; }
        """)
        self.btn_save.clicked.connect(self._save)

        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_cancel.setMinimumHeight(32)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.reset)

        root.addLayout(buttons_row(btn_add_row, self.btn_save, self.btn_cancel))

        # صف أول افتراضي
        self._add_item_row()

    # ══════════════════════════════════════════════════════
    # إدارة الصفوف
    # ══════════════════════════════════════════════════════

    def _add_item_row(self, item_id=None, qty=1.0):
        row = _OfferItemRow(self.conn, on_remove=self._remove_item_row)
        row.sp_qty.valueChanged.connect(self._update_totals)
        row.cmb_product.currentIndexChanged.connect(self._update_totals)
        self._item_rows.append(row)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)
        if item_id is not None:
            row.set_values(item_id, qty)
        self._update_totals()

    def _remove_item_row(self, row_widget: _OfferItemRow):
        if row_widget in self._item_rows:
            self._item_rows.remove(row_widget)
        self._rows_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self._update_totals()

    def _clear_rows(self):
        for row in list(self._item_rows):
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._item_rows.clear()

    # ══════════════════════════════════════════════════════
    # حساب الإجماليات
    # ══════════════════════════════════════════════════════

    def _calc_totals(self) -> tuple[float, float, float]:
        total_cost = 0.0
        for row in self._item_rows:
            item_id = row.get_item_id()
            if item_id:
                total_cost += calc_cost(self.conn, item_id) * row.get_qty()
        margin      = self.sp_margin.value() / 100.0
        total_price = total_cost * (1 + margin)
        profit      = total_price - total_cost
        return total_cost, total_price, profit

    def _update_totals(self):
        cost, price, profit = self._calc_totals()
        self.lbl_summary.setText(
            f"التكلفة: {cost:.2f}  │  السعر: {price:.2f}  │  الربح: {profit:.2f}"
        )

    # ══════════════════════════════════════════════════════
    # حفظ / تحميل / إعادة تعيين
    # ══════════════════════════════════════════════════════

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العرض أولاً")
            return

        items = []
        for row in self._item_rows:
            val = row.get_values()
            if val:
                items.append(val)

        if not items:
            QMessageBox.warning(self, "تنبيه", "أضف منتجاً واحداً على الأقل")
            return

        margin = self.sp_margin.value()
        notes  = self.inp_notes.text().strip()

        if self._editing_id is not None:
            update_offer(self.conn, self._editing_id, name, margin, notes)
            replace_offer_items(self.conn, self._editing_id, items)
        else:
            oid = insert_offer(self.conn, name, margin, notes)
            replace_offer_items(self.conn, oid, items)

        self.reset()
        bus.data_changed.emit()
        if self._on_saved:
            self._on_saved()

    def load_offer(self, offer_id: int):
        offer = fetch_offer(self.conn, offer_id)
        if not offer:
            return
        self._editing_id = offer_id
        self.inp_name.setText(offer["name"])
        self.sp_margin.setValue(offer["margin"])
        self.inp_notes.setText(offer["notes"] or "")

        self._clear_rows()
        for row in fetch_offer_items(self.conn, offer_id):
            self._add_item_row(item_id=row["item_id"], qty=row["qty"])

        self.lbl_mode.setText(f"─── تعديل: {offer['name']} ───")
        self.btn_cancel.setVisible(True)
        self._update_totals()

    def reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self.sp_margin.setValue(30)
        self.inp_notes.clear()
        self._clear_rows()
        self._add_item_row()
        self.lbl_mode.setText("─── عرض جديد ───")
        self.btn_cancel.setVisible(False)
        self.lbl_summary.setText("التكلفة: ─   │   السعر: ─   │   الربح: ─")


# ══════════════════════════════════════════════════════════
# لوحة تفاصيل العرض
# ══════════════════════════════════════════════════════════

class _OfferDetails(QFrame):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ffe0b2;
                border-radius: 8px;
            }
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        # ── عنوان ──
        self.lbl_title = QLabel("اختر عرضاً لعرض تفاصيله")
        self.lbl_title.setStyleSheet(
            "font-weight:bold; color:#e65100; font-size:13px;"
            "background:transparent; border:none;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        # ── جدول السطور ──
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["المنتج", "التصنيف", "الكمية", "تكلفة/وحدة", "إجمالي السطر"]
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.Fixed)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 110)
        self.table.setMinimumHeight(120)
        root.addWidget(self.table, stretch=1)

        # ── ملخص ──
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: #fff3e0;
                border: 1px solid #ffcc80;
                border-radius: 6px;
            }
        """)
        s_lay = QHBoxLayout(summary_frame)
        s_lay.setContentsMargins(12, 8, 12, 8)
        s_lay.setSpacing(20)

        def _stat(label):
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl_title = QLabel(label)
            lbl_title.setStyleSheet(
                "font-size:10px; color:#888; background:transparent; border:none;"
            )
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_val = QLabel("─")
            lbl_val.setStyleSheet(
                "font-size:13px; font-weight:bold; color:#e65100;"
                "background:transparent; border:none;"
            )
            lbl_val.setAlignment(Qt.AlignCenter)
            col.addWidget(lbl_title)
            col.addWidget(lbl_val)
            s_lay.addLayout(col)
            return lbl_val

        self.lbl_cost  = _stat("إجمالي التكلفة")
        sep1 = QLabel("│")
        sep1.setStyleSheet("color:#ffcc80; background:transparent; border:none;")
        s_lay.addWidget(sep1)
        self.lbl_margin = _stat("هامش الربح")
        sep2 = QLabel("│")
        sep2.setStyleSheet("color:#ffcc80; background:transparent; border:none;")
        s_lay.addWidget(sep2)
        self.lbl_price = _stat("سعر البيع")
        sep3 = QLabel("│")
        sep3.setStyleSheet("color:#ffcc80; background:transparent; border:none;")
        s_lay.addWidget(sep3)
        self.lbl_profit = _stat("الربح")
        self.lbl_notes  = QLabel("")
        self.lbl_notes.setStyleSheet(
            "font-size:10px; color:#999; background:transparent; border:none;"
        )
        self.lbl_notes.setWordWrap(True)

        root.addWidget(summary_frame)
        root.addWidget(self.lbl_notes)

    def load(self, offer_id: int):
        summary = calc_offer_summary(self.conn, offer_id)
        if not summary:
            return

        self.lbl_title.setText(
            f"📋  {summary['offer_name']}  —  {summary['created_at']}"
        )

        self.table.setRowCount(0)
        for line in summary["lines"]:
            r = self.table.rowCount()
            self.table.insertRow(r)
            icon = "🏭" if line["item_type"] == "final" else "🔧"
            self.table.setItem(r, 0, QTableWidgetItem(f"{icon} {line['item_name']}"))
            self.table.setItem(r, 1, QTableWidgetItem(line["category_name"] or "—"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{line['qty']:.4g}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{line['unit_cost']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{line['line_cost']:.2f}"))

        self.lbl_cost.setText(f"{summary['total_cost']:.2f}  ج")
        self.lbl_margin.setText(f"{summary['margin']:.1f} %")
        self.lbl_price.setText(f"{summary['total_price']:.2f}  ج")

        profit = summary["profit"]
        color  = "#1b5e20" if profit >= 0 else "#b71c1c"
        self.lbl_profit.setText(f"{profit:.2f}  ج")
        self.lbl_profit.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

        notes = summary.get("notes", "")
        self.lbl_notes.setText(f"📝 {notes}" if notes else "")

    def clear(self):
        self.lbl_title.setText("اختر عرضاً لعرض تفاصيله")
        self.table.setRowCount(0)
        for lbl in (self.lbl_cost, self.lbl_margin, self.lbl_price, self.lbl_profit):
            lbl.setText("─")
        self.lbl_notes.setText("")


# ══════════════════════════════════════════════════════════
# جدول العروض
# ══════════════════════════════════════════════════════════

class _OffersTable(QWidget):
    def __init__(self, conn, on_edit, on_delete, on_select, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._on_select = on_select
        self._all_rows  = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 10)
        root.setSpacing(6)

        root.addWidget(section_label("─── العروض المحفوظة ───"))

        # ── فلتر بحث بالاسم فقط (لا تصنيف للعروض) ──
        search_row = QHBoxLayout()
        lbl_s = QLabel("🔍")
        lbl_s.setStyleSheet("font-size:13px;")
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: #f0f4ff; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #e65100; }
        """)
        self.inp_search.textChanged.connect(self._apply_filter)

        btn_clear = QPushButton("↺")
        btn_clear.setFixedSize(28, 28)
        btn_clear.setStyleSheet(
            "QPushButton { background:#e8eaf6; border:1px solid #c5cae9;"
            "border-radius:4px; color:#3949ab; }"
            "QPushButton:hover { background:#c5cae9; }"
        )
        btn_clear.clicked.connect(lambda: self.inp_search.clear())

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            "color:#e65100; font-size:10px; font-weight:bold;"
        )

        search_row.addWidget(lbl_s)
        search_row.addWidget(self.inp_search, stretch=1)
        search_row.addWidget(btn_clear)
        search_row.addWidget(self.lbl_count)
        root.addLayout(search_row)

        # ── الجدول ──
        self.table = make_table(
            ["ID", "اسم العرض", "عدد المنتجات", "الهامش %",
             "التكلفة", "السعر", "الربح", "التاريخ"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 85)
        self.table.setColumnWidth(5, 85)
        self.table.setColumnWidth(6, 85)
        self.table.setColumnWidth(7, 130)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(lambda: self._on_edit(self.selected_id()))
        btn_del.clicked.connect(lambda: self._on_delete(self.selected_id()))
        root.addLayout(buttons_row(btn_edit, btn_del))

    def selected_id(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        return int(self.table.item(row, 0).text())

    def _on_selection(self):
        oid = self.selected_id()
        if oid is not None:
            self._on_select(oid)

    def _load(self):
        self._all_rows = list(fetch_all_offers(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        q = self.inp_search.text().strip().lower()
        self.table.setRowCount(0)
        shown = 0
        for offer in self._all_rows:
            if q and q not in offer["name"].lower():
                continue
            from db.offers_repo import calc_offer_summary
            summary = calc_offer_summary(self.conn, offer["id"])

            items_count = len(summary.get("lines", []))
            cost        = summary.get("total_cost", 0)
            price       = summary.get("total_price", 0)
            profit      = summary.get("profit", 0)

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(offer["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(offer["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(str(items_count)))
            self.table.setItem(r, 3, QTableWidgetItem(f"{offer['margin']:.1f} %"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{cost:.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{price:.2f}"))

            profit_item = QTableWidgetItem(f"{profit:.2f}")
            if profit >= 0:
                profit_item.setForeground(QColor("#1b5e20"))
            else:
                profit_item.setForeground(QColor("#b71c1c"))
            self.table.setItem(r, 6, profit_item)
            self.table.setItem(r, 7, QTableWidgetItem(offer["created_at"]))
            shown += 1

        total = len(self._all_rows)
        self.lbl_count.setText(
            f"({shown})" if shown == total else f"({shown} / {total})"
        )


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class OffersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        # ── فورم العرض ──
        self._form = _OfferForm(self.conn, on_saved=None)
        splitter.addWidget(self._form)

        # ── جدول + تفاصيل ──
        bottom = QSplitter(Qt.Horizontal)
        bottom.setHandleWidth(6)
        bottom.setStyleSheet(_SPLITTER_STYLE)

        self._offers_table = _OffersTable(
            self.conn,
            on_edit   = self._edit_offer,
            on_delete = self._delete_offer,
            on_select = self._show_details,
        )
        self._details = _OfferDetails(self.conn)

        bottom.addWidget(self._offers_table)
        bottom.addWidget(self._details)
        bottom.setSizes([500, 400])

        splitter.addWidget(bottom)
        splitter.setSizes([320, 480])
        splitter.setCollapsible(0, True)

        root.addWidget(splitter)

    def _edit_offer(self, offer_id):
        if offer_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عرضاً أولاً")
            return
        self._form.load_offer(offer_id)

    def _delete_offer(self, offer_id):
        if offer_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عرضاً أولاً")
            return
        offer = fetch_offer(self.conn, offer_id)
        if not offer:
            return
        if confirm_delete(self, offer["name"]):
            if self._form._editing_id == offer_id:
                self._form.reset()
            delete_offer(self.conn, offer_id)
            self._details.clear()
            bus.data_changed.emit()

    def _show_details(self, offer_id):
        self._details.load(offer_id)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
