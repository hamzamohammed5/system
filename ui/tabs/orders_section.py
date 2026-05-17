"""
ui/tabs/orders_section.py
==========================
قسم إدارة الطلبات والعملاء — تبويبات داخلية:
  📋 الطلبات     → OrdersTab
  👥 العملاء     → CustomersTab
  📊 الإحصائيات → OrdersDashboardTab
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore    import Qt

from db.orders.orders_schema import get_orders_connection, create_orders_tables
from ui.tabs.orders.orders_tab     import OrdersTab
from ui.tabs.orders.customers_tab  import CustomersTab
from ui.tabs.orders.dashboard_tab  import OrdersDashboardTab

_TAB_STYLE = """
    QTabWidget::pane {
        border: none;
        background: #f9f9f9;
    }
    QTabBar::tab {
        background: #f0f0f0;
        border: 1px solid #ddd;
        border-bottom: none;
        padding: 8px 18px;
        margin-left: 2px;
        font-size: 12px;
        color: #555;
    }
    QTabBar::tab:selected {
        background: #ffffff;
        color: #1565c0;
        font-weight: bold;
        border-top: 2px solid #1565c0;
    }
    QTabBar::tab:hover:!selected {
        background: #e8f0fe;
        color: #1565c0;
    }
"""


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

        header = QLabel("  📋  إدارة الطلبات والعملاء")
        header.setFixedHeight(42)
        header.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                color: #1565c0;
                padding-right: 16px;
            }
        """)
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet(_TAB_STYLE)

        self._orders_tab    = OrdersTab(self.conn)
        self._customers_tab = CustomersTab(self.conn)
        self._dashboard_tab = OrdersDashboardTab(self.conn)

        tabs.addTab(self._dashboard_tab, "📊  لوحة المتابعة")
        tabs.addTab(self._orders_tab,    "📋  الطلبات")
        tabs.addTab(self._customers_tab, "👥  العملاء")

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