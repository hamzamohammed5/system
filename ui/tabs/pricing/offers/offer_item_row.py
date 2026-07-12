"""
ui/tabs/pricing/offers/offer_item_row.py
=================================
_OfferItemRow — صف منتج واحد داخل فورم العرض.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox,
)
from PyQt5.QtCore import Qt
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from services.pricing.offers_service import (
    get_offer_candidate_items, get_priced_ids,
    get_item_price, get_item_cost,
    has_pricing as has_pricing_fn,
)
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.constants import (
    BTN_MIN_HEIGHT, SPACING_MD, SPACING_SM,
    FILTER_SEARCH_H, FILTER_COMBO_MIN_H,
    OFFER_FORM_HDR_ICON_W, OFFER_FORM_HDR_DEL_W,
    OFFER_FORM_HDR_SEARCH_W, OFFER_FORM_HDR_COST_W,
    OFFER_FORM_HDR_PRICE_W, OFFER_FORM_HDR_QTY_W, OFFER_FORM_HDR_TOTAL_W,
    OFFER_ROW_PRODUCT_COMBO_W,
    OFFER_ROW_SEARCH_PAD_V, OFFER_ROW_SEARCH_PAD_H,
    STAT_BOX_BORDER_RADIUS,
)


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(BTN_MIN_HEIGHT)
    return s


class _OfferItemRow(QFrame, WidgetMixin):
    """صف منتج واحد داخل فورم العرض."""

    def __init__(self, conn, on_remove, on_change, parent=None):
        super().__init__(parent)
        self._conn      = conn
        self._on_remove = on_remove
        self._on_change = on_change
        self._init_widget_mixin(theme=True, font=True, lang=False, data=True)
        self._build()
        self._refresh_style()
        self._load_products()

    # ── connection صالح دايماً ────────────────────────────
    def _live_conn(self):
        from services.companies.company_service import CompanyService
        if CompanyService.is_conn_alive(self._conn):
            return self._conn
        return CompanyService.get_active_erp_conn()

    def _refresh_data(self, company_id=None):
        self._reload_products()

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import FS_SM, FS_MD
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['row_alt_bg']};
                border: 1px solid {_C['row_alt_border']};
                border-radius: {STAT_BOX_BORDER_RADIUS}px;
            }}
        """)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1px solid {_C['input_accent_border']};
                border-radius: {STAT_BOX_BORDER_RADIUS}px;
                padding: {OFFER_ROW_SEARCH_PAD_V}px {OFFER_ROW_SEARCH_PAD_H}px;
                font-size: {FS_SM}px;
            }}
            QLineEdit:focus {{ border-color: {_C['orange']}; }}
        """)
        self.lbl_cost.setStyleSheet(
            f"color:{_C['journal_dr_accent']}; font-size:{FS_SM}px;"
            "background:transparent; border:none;"
        )
        self.lbl_listed.setStyleSheet(
            f"color:{_C['success']}; font-size:{FS_SM}px; background:transparent; border:none;"
        )
        self.lbl_line.setStyleSheet(
            f"color:{_C['orange']}; font-weight:bold; font-size:{FS_SM}px;"
            "background:transparent; border:none;"
        )
        self.lbl_warn.setStyleSheet(
            f"color:{_C['orange']}; font-size:{FS_SM}px; background:transparent; border:none;"
        )
        self._btn_del.setStyleSheet(
            f"QPushButton {{ background:transparent; border:none; font-size:{FS_MD}px; }}"
            f"QPushButton:hover {{ color:{_C['danger']}; }}"
        )

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
        lay.setSpacing(SPACING_MD)

        self.inp_search = ThemedLineEdit()
        self.inp_search.setPlaceholderText(tr("offer_select_product_search"))
        self.inp_search.setFixedWidth(OFFER_FORM_HDR_SEARCH_W)
        self.inp_search.setMinimumHeight(FILTER_SEARCH_H)
        self.inp_search.textChanged.connect(
            lambda t: self._load_products(filter_text=t.strip())
        )

        self.cmb_product = ThemedComboBox()
        self.cmb_product.setMinimumWidth(OFFER_ROW_PRODUCT_COMBO_W)
        self.cmb_product.setMinimumHeight(FILTER_COMBO_MIN_H)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        self.lbl_cost = QLabel(tr("empty_placeholder"))
        self.lbl_cost.setFixedWidth(OFFER_FORM_HDR_COST_W)
        self.lbl_cost.setAlignment(Qt.AlignCenter)
        self.lbl_cost.setToolTip(tr("offer_col_unit_cost"))

        self.lbl_listed = QLabel(tr("empty_placeholder"))
        self.lbl_listed.setFixedWidth(OFFER_FORM_HDR_PRICE_W)
        self.lbl_listed.setAlignment(Qt.AlignCenter)
        self.lbl_listed.setToolTip(tr("offer_col_unit_price"))

        self.sp_qty = _spin(99999, 4)
        self.sp_qty.setValue(1.0)
        self.sp_qty.setFixedWidth(OFFER_FORM_HDR_QTY_W)
        self.sp_qty.valueChanged.connect(self._on_product_changed)

        self.lbl_line = QLabel(tr("empty_placeholder"))
        self.lbl_line.setFixedWidth(OFFER_FORM_HDR_TOTAL_W)
        self.lbl_line.setAlignment(Qt.AlignCenter)
        self.lbl_line.setToolTip(tr("offer_col_line_total"))

        self.lbl_warn = QLabel(tr("offer_row_warn_icon"))
        self.lbl_warn.setFixedWidth(OFFER_FORM_HDR_ICON_W)
        self.lbl_warn.setToolTip(tr("offer_no_price_tooltip"))
        self.lbl_warn.setVisible(False)

        btn_del = QPushButton(tr("offer_row_remove_btn"))
        btn_del.setFixedSize(OFFER_FORM_HDR_DEL_W, OFFER_FORM_HDR_DEL_W)
        btn_del.clicked.connect(lambda: self._on_remove(self))
        self._btn_del = btn_del

        lay.addWidget(self.inp_search)
        lay.addWidget(self.cmb_product, stretch=1)
        lay.addWidget(QLabel(tr("offer_cost_lbl")))
        lay.addWidget(self.lbl_cost)
        lay.addWidget(QLabel(tr("offer_price_lbl")))
        lay.addWidget(self.lbl_listed)
        lay.addWidget(QLabel(tr("offer_times_sym")))
        lay.addWidget(self.sp_qty)
        lay.addWidget(QLabel(tr("offer_equals_sym")))
        lay.addWidget(self.lbl_line)
        lay.addWidget(self.lbl_warn)
        lay.addWidget(btn_del)

    def _load_products(self, filter_text: str = ""):
        try:
            conn = self._live_conn()
        except Exception:
            return

        prev_id = self.get_item_id()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        q = filter_text.lower()

        try:
            priced_ids = get_priced_ids(conn)
            for item_type in ("final", "semi"):
                rows = get_offer_candidate_items(conn, item_type)
                icon_key = "offer_item_final_icon" if item_type == "final" else "offer_item_semi_icon"
                for row in rows:
                    if row["id"] not in priced_ids:
                        continue
                    if q and q not in row["name"].lower():
                        continue
                    self.cmb_product.addItem(
                        tr(icon_key).format(name=row["name"]),
                        row["id"],
                    )
        except Exception:
            pass

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
            self.lbl_cost.setText(tr("empty_placeholder"))
            self.lbl_listed.setText(tr("empty_placeholder"))
            self.lbl_line.setText(tr("empty_placeholder"))
            self.lbl_warn.setVisible(False)
            if self._on_change:
                self._on_change()
            return

        try:
            conn = self._live_conn()
            unit_cost   = get_item_cost(conn, item_id)
            has_pricing = has_pricing_fn(conn, item_id)
            unit_price  = get_item_price(conn, item_id) if has_pricing else 0.0
        except Exception:
            return

        self.lbl_cost.setText(f"{unit_cost:.2f}")
        self.lbl_listed.setText(f"{unit_price:.2f}" if has_pricing else tr("empty_placeholder"))
        self.lbl_warn.setVisible(not has_pricing)

        line_total = unit_price * self.sp_qty.value()
        self.lbl_line.setText(f"{line_total:.2f}" if has_pricing else tr("empty_placeholder"))

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
