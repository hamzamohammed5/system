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

from services.pricing.offers_service import (
    get_offer, get_offer_items,
    create_offer, modify_offer,
    save_offer_items,
    get_item_price, get_item_cost,
)
from ui.widgets.combo.category import CategoryCombo
from ui.widgets.core.i18n import tr
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.widget_mixin import WidgetMixin

from ui.constants import (
    FORM_LAYOUT_MARGIN, SPACING_MD, SPACING_SM, SPACING_LG, SPACING_XS,
    BTN_MIN_HEIGHT,
    TABLE_BORDER_RADIUS, STAT_BOX_BORDER_RADIUS, FILTER_COMBO_BORDER_RADIUS,
    STAT_CARD_MARGIN_NORMAL,
    OFFER_FORM_SCROLL_MIN_H, OFFER_FORM_SCROLL_MAX_H,
    OFFER_FORM_DISC_W, OFFER_FORM_CAT_W,
    OFFER_FORM_HDR_ICON_W, OFFER_FORM_HDR_DEL_W,
    OFFER_FORM_HDR_SEARCH_W, OFFER_FORM_HDR_COST_W,
    OFFER_FORM_HDR_PRICE_W, OFFER_FORM_HDR_QTY_W, OFFER_FORM_HDR_TOTAL_W,
    OFFER_ADD_ROW_BTN_PAD_V, OFFER_ADD_ROW_BTN_PAD_H, OFFER_SAVE_BTN_PAD_H,
)

from .offer_item_row import _OfferItemRow
from ..pricing._stat_box import stat_box

def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(SPACING_SM)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row

def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(BTN_MIN_HEIGHT)
    return s


class _OfferForm(QWidget, WidgetMixin):

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn         = conn
        self._editing_id   = None
        self._editing_name = None
        self._item_rows: list[_OfferItemRow] = []
        self._init_widget_mixin(theme=True, font=True, lang=True, data=False)
        self._build()
        self._refresh_style()

    # ── connection صالح دايماً ────────────────────────────
    def _live_conn(self):
        from services.companies.company_service import CompanyService
        if CompanyService.is_conn_alive(self._conn):
            return self._conn
        return CompanyService.get_active_erp_conn()

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import FS_XS, FS_BASE, FS_LG
        self._header_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['orange_border']};
                border-radius: {TABLE_BORDER_RADIUS}px;
            }}
        """)
        self.lbl_mode.setStyleSheet(
            f"font-weight:bold; color:{_C['orange']}; font-size:{FS_BASE}px;"
        )
        self._lbl_disc_pct.setStyleSheet(f"font-weight:bold; color:{_C['orange']};")
        for lbl in self._hdr_labels:
            lbl.setStyleSheet(
                f"font-size:{FS_XS}px; font-weight:bold; color:{_C['text_muted']};"
                f"border-bottom:1px solid {_C['border']}; background:transparent;"
            )
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {_C['orange_border']};
                border-radius: {STAT_BOX_BORDER_RADIUS}px;
                background: {_C['scroll_warm_bg']};
            }}
        """)
        self._btn_add_row.setStyleSheet(f"""
            QPushButton {{
                background: {_C['orange_bg']};
                border: 1px solid {_C['orange_border']};
                border-radius: {FILTER_COMBO_BORDER_RADIUS}px;
                color: {_C['orange']};
                font-weight: bold;
                padding: {OFFER_ADD_ROW_BTN_PAD_V}px {OFFER_ADD_ROW_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['orange_border']}; }}
        """)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_C['orange']};
                color: {_C['bg_input']};
                font-weight: bold;
                border-radius: {STAT_BOX_BORDER_RADIUS}px;
                padding: 0 {OFFER_SAVE_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['orange_hover']}; }}
        """)

    def _build(self):
        root = QVBoxLayout(self)
        m = FORM_LAYOUT_MARGIN
        root.setContentsMargins(m[0], m[1], m[2], m[3])
        root.setSpacing(SPACING_MD)

        header = QFrame()
        self._header_frame = header
        h_lay = QVBoxLayout(header)
        mn = STAT_CARD_MARGIN_NORMAL
        h_lay.setContentsMargins(mn[0], mn[1], mn[2], mn[3])
        h_lay.setSpacing(SPACING_MD)

        self.lbl_mode = QLabel(tr("offer_new_mode"))
        h_lay.addWidget(self.lbl_mode)

        info_row = QHBoxLayout()
        info_row.setSpacing(SPACING_LG)

        lbl_name = QLabel(tr("offer_name_field"))
        lbl_name.setStyleSheet("font-weight:bold;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("offer_name_placeholder"))
        self.inp_name.setMinimumHeight(BTN_MIN_HEIGHT)

        lbl_disc = QLabel(tr("offer_discount_field"))
        lbl_disc.setStyleSheet("font-weight:bold;")
        self.sp_discount = _spin(100, 2)
        self.sp_discount.setValue(0)
        self.sp_discount.setFixedWidth(OFFER_FORM_DISC_W)
        lbl_disc_pct = QLabel(tr("offer_discount_pct_sym"))
        self._lbl_disc_pct = lbl_disc_pct

        lbl_cat = QLabel(tr("offer_category_field"))
        lbl_cat.setStyleSheet("font-weight:bold;")
        self.cmb_category = CategoryCombo(self._live_conn(), scope="all")
        self.cmb_category.setMinimumHeight(BTN_MIN_HEIGHT)
        self.cmb_category.setFixedWidth(OFFER_FORM_CAT_W)

        lbl_notes = QLabel(tr("offer_notes_field"))
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("offer_notes_placeholder"))
        self.inp_notes.setMinimumHeight(BTN_MIN_HEIGHT)

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
        stats_row.setSpacing(SPACING_SM)
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
        ch_lay.setContentsMargins(SPACING_MD, 0, SPACING_MD, 0)
        ch_lay.setSpacing(SPACING_MD)

        self._hdr_labels = []

        def _hdr(text, w=None, stretch=0):
            lbl = QLabel(text)
            if w:
                lbl.setFixedWidth(w)
            ch_lay.addWidget(lbl, stretch=stretch)
            self._hdr_labels.append(lbl)

        _hdr(tr("offer_header_search"), OFFER_FORM_HDR_SEARCH_W)
        _hdr(tr("offer_col_product"), stretch=1)
        _hdr(tr("offer_col_unit_cost"), OFFER_FORM_HDR_COST_W)
        _hdr(tr("offer_col_unit_price"), OFFER_FORM_HDR_PRICE_W)
        _hdr(tr("offer_col_qty"), OFFER_FORM_HDR_QTY_W)
        _hdr(tr("offer_header_total_col"), OFFER_FORM_HDR_TOTAL_W)
        _hdr("", OFFER_FORM_HDR_ICON_W)
        _hdr("", OFFER_FORM_HDR_DEL_W)
        root.addWidget(ch)

        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background:transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(SPACING_XS)
        self._rows_layout.setContentsMargins(0, 0, SPACING_XS, 0)
        self._rows_layout.addStretch()

        scroll = QScrollArea()
        self._scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_container)
        scroll.setMinimumHeight(OFFER_FORM_SCROLL_MIN_H)
        scroll.setMaximumHeight(OFFER_FORM_SCROLL_MAX_H)
        root.addWidget(scroll, stretch=1)

        btn_add_row = QPushButton(tr("offer_add_product_btn"))
        self._btn_add_row = btn_add_row
        btn_add_row.setMinimumHeight(BTN_MIN_HEIGHT)
        btn_add_row.clicked.connect(lambda: self._add_item_row())

        self.btn_save = QPushButton(tr("offer_save_btn"))
        self.btn_save.setMinimumHeight(BTN_MIN_HEIGHT)
        self.btn_save.clicked.connect(self._save)

        self.btn_cancel = QPushButton(tr("offer_cancel_btn"))
        self.btn_cancel.setMinimumHeight(BTN_MIN_HEIGHT)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.reset)

        root.addLayout(buttons_row(btn_add_row, self.btn_save, self.btn_cancel))

        self._add_item_row()

    def _refresh_lang(self, *_):
        self.lbl_mode.setText(
            tr("offer_edit_mode").format(name=self._editing_name)
            if self._editing_id is not None and getattr(self, "_editing_name", None)
            else tr("offer_new_mode")
        )
        self.inp_name.setPlaceholderText(tr("offer_name_placeholder"))
        self.inp_notes.setPlaceholderText(tr("offer_notes_placeholder"))
        self.btn_save.setText(tr("offer_save_btn"))
        self.btn_cancel.setText(tr("offer_cancel_btn"))

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
                total_listed += get_item_price(conn, item_id) * qty
                total_cost   += get_item_cost(conn, item_id) * qty
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
        from ui.theme import _C
        from ui.font import FS_LG
        self.lbl_profit.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C[profit_key]};"
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
            modify_offer(conn, self._editing_id, name, discount, notes, category_id)
            save_offer_items(conn, self._editing_id, items)
        else:
            oid = create_offer(conn, name, discount, notes, category_id)
            save_offer_items(conn, oid, items)

        self.reset()
        emit_company_data_changed()

    def load_offer(self, offer_id: int):
        try:
            conn = self._live_conn()
        except Exception:
            return
        offer = get_offer(conn, offer_id)
        if not offer:
            return
        self._editing_id   = offer_id
        self._editing_name = offer["name"]
        self.inp_name.setText(offer["name"])
        self.sp_discount.setValue(offer["discount"])
        self.inp_notes.setText(offer["notes"] or "")
        self.cmb_category.set_category(offer["category_id"])
        self._clear_rows()
        for row in get_offer_items(conn, offer_id):
            self._add_item_row(item_id=row["item_id"], qty=row["qty"])
        self.lbl_mode.setText(
            tr("offer_edit_mode").format(name=offer["name"])
        )
        self.btn_cancel.setVisible(True)
        self._update_totals()

    def reset(self):
        self._editing_id   = None
        self._editing_name = None
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
            lbl.setText(tr("empty_placeholder"))
