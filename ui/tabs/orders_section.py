"""
ui/tabs/orders_section.py
==========================
قسم إدارة الطلبات والعملاء.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.orders.orders_schema import get_orders_connection, create_orders_tables
from ui.tabs.orders.orders_tab    import OrdersTab
from ui.tabs.orders.customers_tab import CustomersTab
from ui.tabs.orders.dashboard_tab import OrdersDashboardTab
from ui.widgets.theme.layout_styles import tab_style
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin


class OrdersSection(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_orders_connection()
        create_orders_tables(self.conn)
        self._build()
        self._init_widget_mixin(theme=False, font=False, lang=True, data=False)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setStyleSheet(tab_style())

        self._dashboard_tab = OrdersDashboardTab(self.conn)
        self._orders_tab    = OrdersTab(self.conn)
        self._customers_tab = CustomersTab(self.conn)

        self._tabs.addTab(self._dashboard_tab, tr("orders_section_tab_dashboard"))
        self._tabs.addTab(self._orders_tab,    tr("orders_section_tab_orders"))
        self._tabs.addTab(self._customers_tab, tr("orders_section_tab_customers"))

        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs)

    def _refresh_lang(self, *_):
        if not hasattr(self, "_tabs"):
            return
        self._tabs.setTabText(0, tr("orders_section_tab_dashboard"))
        self._tabs.setTabText(1, tr("orders_section_tab_orders"))
        self._tabs.setTabText(2, tr("orders_section_tab_customers"))

    def _on_tab_changed(self, index):
        if index == 0:
            self._dashboard_tab.refresh()
        elif index == 1:
            self._orders_tab.refresh()
        elif index == 2:
            self._customers_tab.refresh()

    def closeEvent(self, event):
        try:
            self.conn.close()
        except Exception:
            pass
        super().closeEvent(event)
