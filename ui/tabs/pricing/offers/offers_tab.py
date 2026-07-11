"""
ui/tabs/pricing/offers/offers_tab.py
==============================
OffersTab — التبويب الرئيسي للعروض.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTabWidget, QMessageBox,
)
from PyQt5.QtCore import Qt

from services.pricing.offers_service import get_offer, remove_offer
from ui.widgets.dialogs.confirm      import confirm_delete
from ui.widgets.managers.category import CategoryManager
from ui.widgets.core.i18n import tr
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    OFFERS_TAB_SPLITTER_HANDLE_W,
    OFFERS_TAB_FORM_SIZE, OFFERS_TAB_BOTTOM_SIZE,
    OFFERS_TAB_TABLE_SIZE, OFFERS_TAB_DETAILS_SIZE,
    TAB_INDICATOR_BORDER_W,
    SPLITTER_HANDLE_BORDER_W,
)

from .offer_form    import _OfferForm
from .offer_details import _OfferDetails
from .offers_table  import _OffersTable


class OffersTab(QWidget, WidgetMixin):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget_mixin(theme=True, font=False, lang=False, data=False)
        self._build()
        self._refresh_style()

    # ── connection صالح دايماً ────────────────────────────

    def _live_conn(self):
        from services.companies.company_service import CompanyService
        return CompanyService.get_active_erp_conn()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self._tabs_widget.setStyleSheet(f"""
            QTabBar::tab:selected {{
                color: {_C['orange']};
                border-top: {TAB_INDICATOR_BORDER_W}px solid {_C['orange']};
            }}
        """)
        _splitter_style = f"""
            QSplitter::handle {{
                background: {_C['border']};
                border-top: {SPLITTER_HANDLE_BORDER_W}px solid {_C['border_light']};
            }}
            QSplitter::handle:hover {{ background: {_C['orange_bg']}; }}
        """
        self._splitter.setStyleSheet(_splitter_style)
        self._bottom_splitter.setStyleSheet(_splitter_style)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        self._tabs_widget = tabs

        main_widget = QWidget()
        main_lay = QVBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)

        _splitter_style = ""

        splitter = QSplitter(Qt.Vertical)
        self._splitter = splitter
        splitter.setHandleWidth(OFFERS_TAB_SPLITTER_HANDLE_W)

        self._form = _OfferForm(self._live_conn())
        splitter.addWidget(self._form)

        bottom = QSplitter(Qt.Horizontal)
        self._bottom_splitter = bottom
        bottom.setHandleWidth(OFFERS_TAB_SPLITTER_HANDLE_W)

        self._offers_table = _OffersTable(
            self._live_conn(),
            on_edit   = self._edit_offer,
            on_delete = self._delete_offer,
            on_select = self._show_details,
        )
        self._details = _OfferDetails(self._live_conn())
        bottom.addWidget(self._offers_table)
        bottom.addWidget(self._details)
        bottom.setSizes([OFFERS_TAB_TABLE_SIZE, OFFERS_TAB_DETAILS_SIZE])

        splitter.addWidget(bottom)
        splitter.setSizes([OFFERS_TAB_FORM_SIZE, OFFERS_TAB_BOTTOM_SIZE])
        splitter.setCollapsible(0, True)

        main_lay.addWidget(splitter)

        tabs.addTab(main_widget, tr("offer_products_tab"))
        tabs.addTab(
            CategoryManager(self._live_conn(), scope="all"),
            tr("offer_categories_tab"),
        )

        root.addWidget(tabs)

    def _edit_offer(self, offer_id):
        if offer_id is None:
            QMessageBox.information(self, tr("warning"), tr("offer_select_first"))
            return
        self._form.load_offer(offer_id)

    def _delete_offer(self, offer_id):
        if offer_id is None:
            QMessageBox.information(self, tr("warning"), tr("offer_select_first"))
            return
        try:
            conn = self._live_conn()
            offer = get_offer(conn, offer_id)
        except Exception:
            return
        if not offer:
            return
        if confirm_delete(self, offer["name"]):
            if self._form._editing_id == offer_id:
                self._form.reset()
            remove_offer(conn, offer_id)
            self._details.clear()
            emit_company_data_changed()

    def _show_details(self, offer_id):
        self._details.load(offer_id)
