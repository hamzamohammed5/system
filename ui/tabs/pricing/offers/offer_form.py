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
from models.costing import calc_cost
from ui.helpers import buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.core.i18n import tr
from ui.widgets.core.events import emit_company_data_changed
from ui.theme import _C

from .offer_item_row import _OfferItemRow
from ..pricing._stat_box import stat_box


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


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
        header.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['orange_border']};
                border-radius: 8px;
            }}
        """)
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(14, 12, 14, 12)
        h_lay.setSpacing(8)

        self.lbl_mode = QLabel(tr("offer_new_mode"))
        self.lbl_mode.setStyleSheet(
            f"font-weight:bold; color:{_C['orange']}; font-size:12px;"
        )
        h_lay.addWidget(self.lbl_mode)

        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        lbl_name = QLabel(tr("offer_name_field"))
        lbl_name.setStyleSheet("font-weight:bold;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("offer_name_placeholder"))
        self.inp_name.setMinimumHeight(30)

        lbl_disc = QLabel(tr("offer_discount_field"))
        lbl_disc.setStyleSheet("font-weight:bold;")
        self.sp_discount = _spin(100, 2)
        self.sp_discount.setValue(0)
        self.sp_discount.setFixedWidth(90)
        lbl_disc_pct = QLabel(tr("offer_times_sym").replace("×", "%"))
        lbl_disc_pct.setStyleSheet(f"font-weight:bold; color:{_C['orange']};")

        lbl_cat = QLabel(tr("offer_category_field"))
        lbl_cat.setStyleSheet("font-weight:bold;")
        self.cmb_category = CategoryCombo(self._live_conn(), scope="all")
        self.cmb_category.setMinimumHeight(30)
        self.cmb_category.setFixedWidth(150)

        lbl_notes = QLabel(tr("offer_notes_field"))
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("offer_notes_placeholder"))
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
        f1, self.lbl_total_listed = stat_box(tr("offer_total_before_disc"), "journal_dr_accent")
        f2, self.lbl_discount_amt = stat_box(tr("offer_discount_value"),    "danger_strong")
        f3, self.lbl_sell_price   = stat_box(tr("offer_sell_price"),        "success")
        f4, self.lbl_total_cost   = stat_box(tr("offer_total_cost"),        "text_neutral")
        f5, self.lbl_profit       = stat_box(tr("offer_profit"),            "success")
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
                f"font-size:9px; font-weight:bold; color:{_C['text_muted']};"
                f"border-bottom:1px solid {_C['border']}; background:transparent;"
            )
            if w:
                lbl.setFixedWidth(w)
            ch_lay.addWidget(lbl, stretch=stretch)

        _hdr(tr("offer_header_search"), 120)
        _hdr(tr("offer_col_product"), stretch=1)
        _hdr(tr("offer_col_unit_cost"), 72)
        _hdr(tr("offer_col_unit_price"), 72)
        _hdr(tr("offer_col_qty"), 85)
        _hdr(tr("offer_header_total_col"), 80)
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
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {_C['orange_border']};
                border-radius: 6px;
                background: {_C['scroll_warm_bg']};
            }}
        """)
        root.addWidget(scroll, stretch=1)

        btn_add_row = QPushButton(tr("offer_add_product_btn"))
        btn_add_row.setMinimumHeight(30)
        btn_add_row.setStyleSheet(f"""
            QPushButton {{
                background: {_C['orange_bg']};
                border: 1px solid {_C['orange_border']};
                border-radius: 4px;
                color: {_C['orange']};
                font-weight: bold;
                padding: 4px 12px;
            }}
            QPushButton:hover {{ background: {_C['orange_border']}; }}
        """)
        btn_add_row.clicked.connect(lambda: self._add_item_row())

        self.btn_save = QPushButton(tr("offer_save_btn"))
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_C['orange']};
                color: {_C['bg_input']};
                font-weight: bold;
                border-radius: 6px;
                padding: 0 18px;
            }}
            QPushButton:hover {{ background: {_C['orange_hover']}; }}
        """)
        self.btn_save.clicked.connect(self._save)

        self.btn_cancel = QPushButton(tr("offer_cancel_btn"))
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

        self.lbl_total_listed.setText(tr("amount_fmt").format(amount=total_listed))
        self.lbl_discount_amt.setText(tr("amount_fmt").format(amount=disc_amt))
        self.lbl_sell_price.setText(tr("amount_fmt").format(amount=sell_price))
        self.lbl_total_cost.setText(tr("amount_fmt").format(amount=total_cost))

        profit_key = "success" if profit >= 0 else "danger"
        self.lbl_profit.setText(tr("amount_fmt").format(amount=profit))
        self.lbl_profit.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{_C[profit_key]};"
            "background:transparent; border:none;"
        )

    # ── حفظ / تحميل / إعادة تعيين ────────────────────────
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("offer_name_required"))
            return
        items = [r.get_values() for r in self._item_rows if r.get_values()]
        if not items:
            QMessageBox.warning(self, tr("warning"), tr("offer_product_required"))
            return

        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), str(e))
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
        emit_company_data_changed()

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
        self.lbl_mode.setText(
            tr("offer_edit_mode").format(name=offer["name"])
        )
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
        self.lbl_mode.setText(tr("offer_new_mode"))
        self.btn_cancel.setVisible(False)
        for lbl in (self.lbl_total_listed, self.lbl_discount_amt,
                    self.lbl_sell_price, self.lbl_total_cost, self.lbl_profit):
            lbl.setText("─")
