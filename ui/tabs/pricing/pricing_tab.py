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

from db.companies.company_state import company_state
from ui.widgets.core.i18n import tr
from ui.widgets.managers.category import CategoryManager
from ui.constants import MARGIN_ZERO

from .pricing._pricing_panel import _PricingPanel


class PricingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _live_conn(self):
        return company_state.get_erp_conn()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        tabs = QTabWidget()
        tabs.addTab(_PricingPanel(self._live_conn()),                  tr("pricing_prices_tab"))
        tabs.addTab(CategoryManager(self._live_conn(), scope="final"), tr("pricing_categories_tab"))
        root.addWidget(tabs)