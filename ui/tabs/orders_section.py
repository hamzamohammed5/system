"""
ui/tabs/orders_section.py
==========================
قسم إدارة الطلبات والعملاء.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore    import Qt

from db.orders.orders_schema import get_orders_connection, create_orders_tables
from ui.tabs.orders.orders_tab    import OrdersTab
from ui.tabs.orders.customers_tab import CustomersTab
from ui.tabs.orders.dashboard_tab import OrdersDashboardTab
from ui.app_settings import _C, get_font_size, fs


class OrdersSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_orders_connection()
        create_orders_tables(self.conn)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)

        # ✅ التبويبات تأخذ مساحة كافية — بدون min-width ضيق
        base = get_font_size()
        tabs.setStyleSheet(f"""
            QTabBar::tab {{
                min-width: 110px;
                padding: 8px 14px;
            }}
        """)

        self._dashboard_tab = OrdersDashboardTab(self.conn)
        self._orders_tab    = OrdersTab(self.conn)
        self._customers_tab = CustomersTab(self.conn)

        tabs.addTab(self._dashboard_tab, "📊 لوحة المتابعة")
        tabs.addTab(self._orders_tab,    "📋 الطلبات")
        tabs.addTab(self._customers_tab, "👥 العملاء")

        tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(tabs)

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