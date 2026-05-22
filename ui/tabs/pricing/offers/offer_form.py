"""
ui/tabs/pricing/offers/offer_form.py
=============================
_OfferForm — فورم إنشاء / تعديل العرض الكامل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QScrollArea, QLabel,
    QLineEdit, QPushButton, QDoubleSpinBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt

from db.pricing.offers_repo import (
    fetch_offer, fetch_offer_items,
    insert_offer, update_offer,
    replace_offer_items,
)
from models.costing     import calc_cost
from ui.helpers         import buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.events          import bus

from .offer_item_row import _OfferItemRow


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


class _OfferForm(QWidget):

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn       = conn
        self._editing_id = None
        self._item_rows: list[_OfferItemRow] = []
        self._build()

    # ── connection صالح دايماً ────────────────────────────
    def _live_conn(self):
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

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
        self.cmb_category = CategoryCombo(self._live_conn(), scope="all")
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

        # رؤوس الأعمدة
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

    # ── إدارة الصفوف ─────────────────────────────────────
    def _add_item_row(self, item_id=None, qty=1.0):
        row = _OfferItemRow(
            self._live_conn(),
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

    # ── حساب الإجماليات ──────────────────────────────────
    def _update_totals(self):
        total_listed = 0.0
        total_cost   = 0.0

        try:
            conn = self._live_conn()
        except Exception:
            return

        for row in self._item_rows:
            item_id = row.get_item_id()
            if item_id is None:
                continue
            qty = row.get_qty()
            try:
                pr = conn.execute(
                    "SELECT price FROM pricing WHERE item_id=?", (item_id,)
                ).fetchone()
                if pr:
                    total_listed += pr["price"] * qty
                total_cost += calc_cost(conn, item_id) * qty
            except Exception:
                pass

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

    # ── حفظ / تحميل / إعادة تعيين ────────────────────────
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العرض أولاً")
            return
        items = [r.get_values() for r in self._item_rows if r.get_values()]
        if not items:
            QMessageBox.warning(self, "تنبيه", "أضف منتجاً واحداً على الأقل")
            return

        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        discount    = self.sp_discount.value()
        notes       = self.inp_notes.text().strip()
        category_id = self.cmb_category.get_category()

        if self._editing_id is not None:
            update_offer(conn, self._editing_id, name, discount, notes, category_id)
            replace_offer_items(conn, self._editing_id, items)
        else:
            oid = insert_offer(conn, name, discount, notes, category_id)
            replace_offer_items(conn, oid, items)

        self.reset()
        bus.data_changed.emit()

    def load_offer(self, offer_id: int):
        try:
            conn = self._live_conn()
        except Exception:
            return
        offer = fetch_offer(conn, offer_id)
        if not offer:
            return
        self._editing_id = offer_id
        self.inp_name.setText(offer["name"])
        self.sp_discount.setValue(offer["discount"])
        self.inp_notes.setText(offer["notes"] or "")
        self.cmb_category.set_category(offer["category_id"])
        self._clear_rows()
        for row in fetch_offer_items(conn, offer_id):
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