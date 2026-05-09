"""
ui/tabs/offers_tab.py
=====================
تبويب العروض — تسعير مجموعة منتجات بخصم على سعر التسعير.

المنطق:
  السعر الأساسي  = سعر المنتج من جدول pricing × الكمية
  سعر البيع      = الأساسي × (1 - خصم%)
  الربح           = سعر البيع - إجمالي التكلفة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QTabWidget, QFrame, QScrollArea,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QLabel, QMessageBox, QHeaderView,
    QComboBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.connection  import get_connection
from db.items_repo  import fetch_items_by_type
from db.offers_repo import (
    fetch_all_offers, fetch_offer, fetch_offer_items,
    insert_offer, update_offer, delete_offer,
    replace_offer_items, calc_offer_summary,
)
from models.costing import calc_cost
from ui.helpers     import (
    make_table, buttons_row, section_label,
    danger_button, confirm_delete,
)
from ui.widgets.category_manager import CategoryManager, CategoryCombo
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


def _stat_lbl(color="#1565c0"):
    lbl = QLabel("─")
    lbl.setStyleSheet(
        f"font-size:13px; font-weight:bold; color:{color};"
        "background:#f9f9f9; border:1px solid #e0e0e0;"
        "border-radius:4px; padding:3px 10px;"
    )
    lbl.setAlignment(Qt.AlignCenter)
    return lbl


# ══════════════════════════════════════════════════════════
# صف منتج واحد في العرض
# ══════════════════════════════════════════════════════════

class _OfferItemRow(QFrame):
    def __init__(self, conn, on_remove, on_change, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_remove = on_remove
        self._on_change = on_change
        self._build()
        self._load_products()
        bus.data_changed.connect(self._reload_products)

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

        # بحث
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(120)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 6px; font-size: 11px;
            }
            QLineEdit:focus { border-color: #e65100; }
        """)
        self.inp_search.textChanged.connect(
            lambda t: self._load_products(filter_text=t.strip())
        )

        # اختيار المنتج
        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumWidth(180)
        self.cmb_product.setMinimumHeight(28)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        # التكلفة/وحدة
        self.lbl_cost = QLabel("─")
        self.lbl_cost.setFixedWidth(72)
        self.lbl_cost.setStyleSheet(
            "color:#1565c0; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_cost.setAlignment(Qt.AlignCenter)
        self.lbl_cost.setToolTip("تكلفة الإنتاج / وحدة")

        # سعر التسعير/وحدة
        self.lbl_listed = QLabel("─")
        self.lbl_listed.setFixedWidth(72)
        self.lbl_listed.setStyleSheet(
            "color:#2e7d32; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_listed.setAlignment(Qt.AlignCenter)
        self.lbl_listed.setToolTip("سعر التسعير / وحدة")

        # الكمية
        self.sp_qty = _spin(99999, 4)
        self.sp_qty.setValue(1.0)
        self.sp_qty.setFixedWidth(85)
        self.sp_qty.valueChanged.connect(self._on_product_changed)

        # إجمالي السطر (سعر قبل الخصم)
        self.lbl_line = QLabel("─")
        self.lbl_line.setFixedWidth(80)
        self.lbl_line.setStyleSheet(
            "color:#e65100; font-weight:bold; font-size:11px;"
            "background:transparent; border:none;"
        )
        self.lbl_line.setAlignment(Qt.AlignCenter)
        self.lbl_line.setToolTip("إجمالي سعر السطر قبل الخصم")

        # تحذير لو مفيش تسعير
        self.lbl_warn = QLabel("⚠️")
        self.lbl_warn.setStyleSheet(
            "color:#e65100; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_warn.setFixedWidth(20)
        self.lbl_warn.setToolTip("هذا المنتج ليس له سعر في التسعير")
        self.lbl_warn.setVisible(False)

        # حذف
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
        lay.addWidget(QLabel("سعر:"))
        lay.addWidget(self.lbl_listed)
        lay.addWidget(QLabel("×"))
        lay.addWidget(self.sp_qty)
        lay.addWidget(QLabel("="))
        lay.addWidget(self.lbl_line)
        lay.addWidget(self.lbl_warn)
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
                if q and q not in row["name"].lower():
                    continue
                self.cmb_product.addItem(f"{icon} {row['name']}", row["id"])
        self.cmb_product.blockSignals(False)
        if prev_id is not None:
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev_id:
                    self.cmb_product.setCurrentIndex(i)
                    return
        # بعد تحميل المنتجات، نحدّث الإحصائيات فوراً
        self._on_product_changed()

    def _reload_products(self):
        self._load_products(filter_text=self.inp_search.text().strip())

    def _on_product_changed(self):
        item_id = self.get_item_id()
        if item_id is None:
            self.lbl_cost.setText("─")
            self.lbl_listed.setText("─")
            self.lbl_line.setText("─")
            self.lbl_warn.setVisible(False)
            if self._on_change:
                self._on_change()
            return

        unit_cost = calc_cost(self.conn, item_id)
        pricing_row = self.conn.execute(
            "SELECT price FROM pricing WHERE item_id=?", (item_id,)
        ).fetchone()
        unit_price  = pricing_row["price"] if pricing_row else 0.0
        has_pricing = pricing_row is not None

        self.lbl_cost.setText(f"{unit_cost:.2f}")
        self.lbl_listed.setText(f"{unit_price:.2f}" if has_pricing else "─")
        self.lbl_warn.setVisible(not has_pricing)

        line_total = unit_price * self.sp_qty.value()
        self.lbl_line.setText(f"{line_total:.2f}" if has_pricing else "─")

        if self._on_change:
            self._on_change()

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
        # نحدّث الإحصائيات بعد تحديد القيم
        self._on_product_changed()


# ══════════════════════════════════════════════════════════
# فورم العرض
# ══════════════════════════════════════════════════════════

class _OfferForm(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
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
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(14, 12, 14, 12)
        h_lay.setSpacing(8)

        self.lbl_mode = QLabel("─── عرض جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#e65100; font-size:12px;")
        h_lay.addWidget(self.lbl_mode)

        # صف المعلومات الأساسية
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        lbl_name = QLabel("اسم العرض:")
        lbl_name.setStyleSheet("font-weight:bold;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: عرض رمضان، باقة العيد...")
        self.inp_name.setMinimumHeight(30)

        # ── الخصم % — الـ spinbox بدون suffix والـ % كـ label برا ──
        lbl_disc = QLabel("الخصم:")
        lbl_disc.setStyleSheet("font-weight:bold;")
        self.sp_discount = _spin(100, 2)
        self.sp_discount.setValue(0)
        self.sp_discount.setFixedWidth(90)
        lbl_disc_pct = QLabel("%")
        lbl_disc_pct.setStyleSheet("font-weight:bold; color:#e65100;")

        lbl_cat = QLabel("التصنيف:")
        lbl_cat.setStyleSheet("font-weight:bold;")
        self.cmb_category = CategoryCombo(self.conn, scope="all")
        self.cmb_category.setMinimumHeight(30)
        self.cmb_category.setFixedWidth(150)

        lbl_notes = QLabel("ملاحظات:")
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("اختياري...")
        self.inp_notes.setMinimumHeight(30)

        info_row.addWidget(lbl_name)
        info_row.addWidget(self.inp_name, stretch=2)
        info_row.addWidget(lbl_disc)
        info_row.addWidget(self.sp_discount)
        info_row.addWidget(lbl_disc_pct)
        info_row.addWidget(lbl_cat)
        info_row.addWidget(self.cmb_category)
        info_row.addWidget(lbl_notes)
        info_row.addWidget(self.inp_notes, stretch=1)
        h_lay.addLayout(info_row)

        # ── ربط sp_discount بعد بناء كل العناصر ──
        self.sp_discount.valueChanged.connect(self._update_totals)

        # صناديق الإحصائيات
        stats_row = QHBoxLayout()
        stats_row.setSpacing(6)

        def _stat(title, color):
            col = QVBoxLayout()
            col.setSpacing(1)
            t = QLabel(title)
            t.setStyleSheet(
                "font-size:9px; color:#888; background:transparent; border:none;"
            )
            t.setAlignment(Qt.AlignCenter)
            v = _stat_lbl(color)
            col.addWidget(t)
            col.addWidget(v)
            stats_row.addLayout(col, stretch=1)
            return v

        self.lbl_total_listed = _stat("إجمالي السعر قبل الخصم", "#1565c0")
        self.lbl_discount_amt = _stat("قيمة الخصم", "#e53935")
        self.lbl_sell_price   = _stat("سعر البيع النهائي", "#2e7d32")
        self.lbl_total_cost   = _stat("إجمالي التكلفة", "#555")
        self.lbl_profit       = _stat("الربح", "#1b5e20")

        h_lay.addLayout(stats_row)
        root.addWidget(header)

        # ── رؤوس الأعمدة ──
        ch = QWidget()
        ch.setStyleSheet("background:transparent;")
        ch_lay = QHBoxLayout(ch)
        ch_lay.setContentsMargins(8, 0, 8, 0)
        ch_lay.setSpacing(8)

        def _hdr(text, w=None, stretch=0):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-size:9px; font-weight:bold; color:#888;"
                "border-bottom:1px solid #eee; background:transparent;"
            )
            if w:
                lbl.setFixedWidth(w)
            ch_lay.addWidget(lbl, stretch=stretch)

        _hdr("بحث", 120)
        _hdr("المنتج", stretch=1)
        _hdr("تكلفة/و", 72)
        _hdr("سعر/و", 72)
        _hdr("الكمية", 85)
        _hdr("إجمالي", 80)
        _hdr("", 20)
        _hdr("", 28)
        root.addWidget(ch)

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
        scroll.setMinimumHeight(110)
        scroll.setMaximumHeight(260)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ffe0b2;
                border-radius: 6px;
                background: #fffaf5;
            }
        """)
        root.addWidget(scroll, stretch=1)

        # ── أزرار ──
        btn_add_row = QPushButton("➕  إضافة منتج للعرض")
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

        self._add_item_row()

    # ══════════════════════════════════════════════════════
    # إدارة الصفوف
    # ══════════════════════════════════════════════════════

    def _add_item_row(self, item_id=None, qty=1.0):
        row = _OfferItemRow(
            self.conn,
            on_remove=self._remove_item_row,
            on_change=self._update_totals,
        )
        self._item_rows.append(row)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)
        if item_id is not None:
            row.set_values(item_id, qty)
        # نحدّث الإجماليات بعد إضافة الصف مباشرة
        self._update_totals()

    def _remove_item_row(self, row_widget):
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
    # حساب الإجماليات — المنطق الرئيسي
    # ══════════════════════════════════════════════════════

    def _update_totals(self):
        total_listed = 0.0
        total_cost   = 0.0

        for row in self._item_rows:
            item_id = row.get_item_id()
            if item_id is None:
                continue
            qty = row.get_qty()

            pr = self.conn.execute(
                "SELECT price FROM pricing WHERE item_id=?", (item_id,)
            ).fetchone()
            if pr:
                total_listed += pr["price"] * qty

            total_cost += calc_cost(self.conn, item_id) * qty

        disc_pct   = self.sp_discount.value() / 100.0
        disc_amt   = total_listed * disc_pct
        sell_price = total_listed - disc_amt
        profit     = sell_price - total_cost

        self.lbl_total_listed.setText(f"{total_listed:.2f}  ج")
        self.lbl_discount_amt.setText(f"{disc_amt:.2f}  ج")
        self.lbl_sell_price.setText(f"{sell_price:.2f}  ج")
        self.lbl_total_cost.setText(f"{total_cost:.2f}  ج")

        color = "#1b5e20" if profit >= 0 else "#b71c1c"
        self.lbl_profit.setText(f"{profit:.2f}  ج")
        self.lbl_profit.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{color};"
            "background:#f9f9f9; border:1px solid #e0e0e0;"
            "border-radius:4px; padding:3px 10px;"
        )

    # ══════════════════════════════════════════════════════
    # حفظ / تحميل / إعادة تعيين
    # ══════════════════════════════════════════════════════

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العرض أولاً")
            return
        items = [r.get_values() for r in self._item_rows if r.get_values()]
        if not items:
            QMessageBox.warning(self, "تنبيه", "أضف منتجاً واحداً على الأقل")
            return

        discount    = self.sp_discount.value()
        notes       = self.inp_notes.text().strip()
        category_id = self.cmb_category.get_category()

        if self._editing_id is not None:
            update_offer(self.conn, self._editing_id, name, discount,
                         notes, category_id)
            replace_offer_items(self.conn, self._editing_id, items)
        else:
            oid = insert_offer(self.conn, name, discount, notes, category_id)
            replace_offer_items(self.conn, oid, items)

        self.reset()
        bus.data_changed.emit()

    def load_offer(self, offer_id: int):
        offer = fetch_offer(self.conn, offer_id)
        if not offer:
            return
        self._editing_id = offer_id
        self.inp_name.setText(offer["name"])
        self.sp_discount.setValue(offer["discount"])
        self.inp_notes.setText(offer["notes"] or "")
        self.cmb_category.set_category(offer["category_id"])
        self._clear_rows()
        for row in fetch_offer_items(self.conn, offer_id):
            self._add_item_row(item_id=row["item_id"], qty=row["qty"])
        self.lbl_mode.setText(f"─── تعديل: {offer['name']} ───")
        self.btn_cancel.setVisible(True)
        self._update_totals()

    def reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self.sp_discount.setValue(0)
        self.inp_notes.clear()
        self.cmb_category.setCurrentIndex(0)
        self._clear_rows()
        self._add_item_row()
        self.lbl_mode.setText("─── عرض جديد ───")
        self.btn_cancel.setVisible(False)
        for lbl in (self.lbl_total_listed, self.lbl_discount_amt,
                    self.lbl_sell_price, self.lbl_total_cost, self.lbl_profit):
            lbl.setText("─")


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
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        self.lbl_title = QLabel("اختر عرضاً لعرض تفاصيله")
        self.lbl_title.setStyleSheet(
            "font-weight:bold; color:#e65100; font-size:13px;"
            "background:transparent; border:none;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        # جدول السطور
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["المنتج", "التصنيف", "الكمية",
             "تكلفة/و", "سعر/و", "إجمالي السطر"]
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for i, w in enumerate([100, 60, 70, 70, 100], start=1):
            hh.setSectionResizeMode(i, QHeaderView.Fixed)
            self.table.setColumnWidth(i, w)
        self.table.setMinimumHeight(100)
        root.addWidget(self.table, stretch=1)

        # ملخص
        summary = QFrame()
        summary.setStyleSheet("""
            QFrame {
                background: #fff3e0;
                border: 1px solid #ffcc80;
                border-radius: 6px;
            }
        """)
        s_lay = QHBoxLayout(summary)
        s_lay.setContentsMargins(10, 8, 10, 8)
        s_lay.setSpacing(14)

        def _st(title, color="#e65100"):
            col = QVBoxLayout()
            col.setSpacing(1)
            t = QLabel(title)
            t.setStyleSheet(
                "font-size:9px; color:#888; background:transparent; border:none;"
            )
            t.setAlignment(Qt.AlignCenter)
            v = QLabel("─")
            v.setStyleSheet(
                f"font-size:12px; font-weight:bold; color:{color};"
                "background:transparent; border:none;"
            )
            v.setAlignment(Qt.AlignCenter)
            col.addWidget(t)
            col.addWidget(v)
            s_lay.addLayout(col, stretch=1)
            return v

        self.sl_listed  = _st("إجمالي السعر",     "#1565c0")
        self.sl_disc    = _st("الخصم",             "#e53935")
        self.sl_sell    = _st("سعر البيع",         "#2e7d32")
        self.sl_cost    = _st("التكلفة",           "#555")
        self.sl_profit  = _st("الربح",             "#1b5e20")

        root.addWidget(summary)

        self.lbl_notes = QLabel("")
        self.lbl_notes.setStyleSheet(
            "font-size:10px; color:#999; background:transparent; border:none;"
        )
        self.lbl_notes.setWordWrap(True)
        root.addWidget(self.lbl_notes)

    def load(self, offer_id: int):
        s = calc_offer_summary(self.conn, offer_id)
        if not s:
            return

        self.lbl_title.setText(
            f"📋  {s['offer_name']}  —  {s['created_at']}"
            + (f"  │  🏷 {s['category_name']}" if s.get('category_name') else "")
        )

        self.table.setRowCount(0)
        for line in s["lines"]:
            r = self.table.rowCount()
            self.table.insertRow(r)
            icon = "🏭" if line["item_type"] == "final" else "🔧"
            self.table.setItem(r, 0, QTableWidgetItem(f"{icon} {line['item_name']}"))
            self.table.setItem(r, 1, QTableWidgetItem(line["category_name"] or "—"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{line['qty']:.4g}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{line['unit_cost']:.2f}"))
            price_text = f"{line['unit_price']:.2f}" if line["has_pricing"] else "─ ⚠️"
            self.table.setItem(r, 4, QTableWidgetItem(price_text))
            listed_text = f"{line['line_listed']:.2f}" if line["has_pricing"] else "─"
            self.table.setItem(r, 5, QTableWidgetItem(listed_text))

        disc_pct = s["discount"]
        disc_amt = s["total_listed"] - s["sell_price"]

        self.sl_listed.setText(f"{s['total_listed']:.2f}  ج")
        self.sl_disc.setText(f"{disc_amt:.2f}  ج  ({disc_pct:.1f}%)")
        self.sl_sell.setText(f"{s['sell_price']:.2f}  ج")
        self.sl_cost.setText(f"{s['total_cost']:.2f}  ج")

        profit = s["profit"]
        color  = "#1b5e20" if profit >= 0 else "#b71c1c"
        self.sl_profit.setText(f"{profit:.2f}  ج")
        self.sl_profit.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

        self.lbl_notes.setText(f"📝 {s['notes']}" if s.get("notes") else "")

    def clear(self):
        self.lbl_title.setText("اختر عرضاً لعرض تفاصيله")
        self.table.setRowCount(0)
        for lbl in (self.sl_listed, self.sl_disc, self.sl_sell,
                    self.sl_cost, self.sl_profit):
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

        self._filter = FilterBar(self.conn, scope="all")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "اسم العرض", "التصنيف", "عدد المنتجات",
             "خصم %", "إجمالي السعر", "سعر البيع", "التكلفة", "الربح", "التاريخ"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 35)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 55)
        self.table.setColumnWidth(5, 85)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 75)
        self.table.setColumnWidth(8, 75)
        self.table.setColumnWidth(9, 120)
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
        return int(self.table.item(row, 0).text()) if row >= 0 else None

    def _on_selection(self):
        oid = self.selected_id()
        if oid is not None:
            self._on_select(oid)

    def _load(self):
        self._all_rows = list(fetch_all_offers(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        for offer in self._all_rows:
            if not self._filter.match(offer["name"], offer["category_id"]):
                continue
            s = calc_offer_summary(self.conn, offer["id"])
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(offer["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(offer["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(offer["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(str(len(s.get("lines", [])))))
            self.table.setItem(r, 4, QTableWidgetItem(f"{offer['discount']:.1f} %"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{s.get('total_listed', 0):.2f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{s.get('sell_price', 0):.2f}"))
            self.table.setItem(r, 7, QTableWidgetItem(f"{s.get('total_cost', 0):.2f}"))

            profit = s.get("profit", 0)
            pi = QTableWidgetItem(f"{profit:.2f}")
            pi.setForeground(QColor("#1b5e20") if profit >= 0 else QColor("#b71c1c"))
            self.table.setItem(r, 8, pi)
            self.table.setItem(r, 9, QTableWidgetItem(offer["created_at"]))
            shown += 1

        self._filter.set_count(shown, len(self._all_rows))


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

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color: #e65100; border-top: 2px solid #e65100; }
        """)

        main_widget = QWidget()
        main_lay = QVBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form = _OfferForm(self.conn)
        splitter.addWidget(self._form)

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
        bottom.setSizes([520, 380])

        splitter.addWidget(bottom)
        splitter.setSizes([300, 500])
        splitter.setCollapsible(0, True)

        main_lay.addWidget(splitter)

        tabs.addTab(main_widget,                               "🎁  العروض")
        tabs.addTab(CategoryManager(self.conn, scope="all"),   "🏷️  تصنيفات العروض")

        root.addWidget(tabs)

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