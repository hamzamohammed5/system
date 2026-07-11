"""
ui/tabs/pricing/pricing_tab.py
================================
PricingTab — التبويب الرئيسي للتسعير.

التقسيم الداخلي:
  pricing/_stat_box.py      → دالة stat_box المساعدة
  pricing/_pricing_panel.py → _PricingPanel (اللوحة الرئيسية)
  pricing_tab.py            → PricingTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui.widgets.core.i18n import tr
from ui.widgets.managers.category import CategoryManager
from ui.constants import MARGIN_ZERO
from ui.widgets.core.widget_mixin import WidgetMixin

from .pricing._pricing_panel import _PricingPanel


class PricingTab(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._init_widget_mixin(theme=False, font=False, lang=True, data=False)

    def _refresh_lang(self, *_):
        idx_prices = self._tabs.indexOf(self._panel_prices)
        if idx_prices != -1:
            self._tabs.setTabText(idx_prices, tr("pricing_prices_tab"))
        idx_categories = self._tabs.indexOf(self._panel_categories)
        if idx_categories != -1:
            self._tabs.setTabText(idx_categories, tr("pricing_categories_tab"))

    def _live_conn(self):
        from services.companies.company_service import CompanyService
        return CompanyService.get_active_erp_conn()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        self._tabs = QTabWidget()
        self._panel_prices = _PricingPanel(self._live_conn())
        self._panel_categories = CategoryManager(self._live_conn(), scope="final")
        self._tabs.addTab(self._panel_prices,     tr("pricing_prices_tab"))
        self._tabs.addTab(self._panel_categories, tr("pricing_categories_tab"))
        root.addWidget(self._tabs)