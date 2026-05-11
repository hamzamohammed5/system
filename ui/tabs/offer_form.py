"""
ui/tabs/offer_form.py
=====================
فورم إنشاء / تعديل العروض مع صفوف المنتجات.

يحتوي على:
  _OfferItemRow — صف منتج واحد داخل العرض
  _OfferForm    — فورم العرض الكامل مع الإحصائيات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QScrollArea, QLabel,
    QLineEdit, QPushButton, QDoubleSpinBox, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.items_repo  import fetch_items_by_type
from db.offers_repo import (
    fetch_offer, fetch_offer_items,
    insert_offer, update_offer,
    replace_offer_items,
)
from models.costing import calc_cost
from ui.helpers     import buttons_row, danger_button
from ui.widgets.category_manager import CategoryCombo
from ui.events import bus


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _stat_box(title: str, color: str = "#1565c0"):
    frame = QFrame()
    frame.setStyleSheet("""
        QFrame {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 4px;
        }
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lay.setSpacing(2)
    lbl_t = QLabel(title)
    lbl_t.setStyleSheet(
        "font-size:10px; color:#888; background:transparent; border:none;"
    )
    lbl_t.setAlignment(Qt.AlignCenter)
    lbl_v = QLabel("─")
    lbl_v.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lbl_v.setAlignment(Qt.AlignCenter)
    lay.addWidget(lbl_t)
    lay.addWidget(lbl_v)
    return frame, lbl_v


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

        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumWidth(180)
        self.cmb_product.setMinimumHeight(28)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        self.lbl_cost = QLabel("─")
        self.lbl_cost.setFixedWidth(72)
        self.lbl_cost.setStyleSheet(
            "color:#1565c0; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_cost.setAlignment(Qt.AlignCenter)
        self.lbl_cost.setToolTip("تكلفة الإنتاج / وحدة")

        self.lbl_listed = QLabel("─")
        self.lbl_listed.setFixedWidth(72)
        self.lbl_listed.setStyleSheet(
            "color:#2e7d32; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_listed.setAlignment(Qt.AlignCenter)
        self.lbl_listed.setToolTip("سعر التسعير / وحدة")

        self.sp_qty = _spin(99999, 4)
        self.sp_qty.setValue(1.0)
        self.sp_qty.setFixedWidth(85)
        self.sp_qty.valueChanged.connect(self._on_product_changed)

        self.lbl_line = QLabel("─")
        self.lbl_line.setFixedWidth(80)
        self.lbl_line.setStyleSheet(
            "color:#e65100; font-weight:bold; font-size:11px;"
            "background:transparent; border:none;"
        )
        self.lbl_line.setAlignment(Qt.AlignCenter)
        self.lbl_line.setToolTip("إجمالي سعر السطر قبل الخصم")

        self.lbl_warn = QLabel("⚠️")
        self.lbl_warn.setStyleSheet(
            "color:#e65100; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_warn.setFixedWidth(20)
        self.lbl_warn.setToolTip("هذا المنتج ليس له سعر في التسعير")
        self.lbl_warn.setVisible(False)

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

        priced_ids = {
            r["item_id"]
            for r in self.conn.execute("SELECT item_id FROM pricing").fetchall()
        }

        for item_type in ("final", "semi"):
            rows = fetch_items_by_type(self.conn, item_type)
            icon = "🏭" if item_type == "final" else "🔧"
            for row in rows:
                if row["id"] not in priced_ids:
                    continue
                if q and q not in row["name"].lower():
                    continue
                self.cmb_product.addItem(f"{icon} {row['name']}", row["id"])

        self.cmb_product.blockSignals(False)
        if prev_id is not None:
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev_id:
                    self.cmb_product.setCurrentIndex(i)
                    return
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

        unit_cost   = calc_cost(self.conn, item_id)
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
        self.lbl_mode.setStyleSheet(
            "font-weight:bold; color:#e65100; font-size:12px;"
        )
        h_lay.addWidget(self.lbl_mode)

        # ── صف المعلومات الأساسية ──
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        lbl_name = QLabel("اسم العرض:")
        lbl_name.setStyleSheet("font-weight:bold;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: عرض رمضان، باقة العيد...")
        self.inp_name.setMinimumHeight(30)

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

        self.sp_discount.valueChanged.connect(self._update_totals)

        # ── صناديق الإحصائيات ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(6)
        f1, self.lbl_total_listed = _stat_box("إجمالي السعر قبل الخصم", "#1565c0")
        f2, self.lbl_discount_amt = _stat_box("قيمة الخصم",             "#e53935")
        f3, self.lbl_sell_price   = _stat_box("سعر البيع النهائي",      "#2e7d32")
        f4, self.lbl_total_cost   = _stat_box("إجمالي التكلفة",         "#555555")
        f5, self.lbl_profit       = _stat_box("الربح",                   "#1b5e20")
        for f in (f1, f2, f3, f4, f5):
            stats_row.addWidget(f, stretch=1)
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

    # ── إدارة الصفوف ──────────────────────────────────────

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

    # ── حساب الإجماليات ───────────────────────────────────

    def _update_totals(self):
        total_listed = 0.0
        total_cost   = 0.0

        for row in self._item_rows:
            item_id = row.get_item_id()
            if item_id is None:
                continue
            qty = row.get_qty()
            pr  = self.conn.execute(
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
            f"font-size:14px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

    # ── حفظ / تحميل / إعادة تعيين ─────────────────────────

    def _save(self):
        from PyQt5.QtWidgets import QMessageBox
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
            update_offer(self.conn, self._editing_id, name,
                         discount, notes, category_id)
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