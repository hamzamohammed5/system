"""
ui/tabs/inventory_tab.py
========================
التبويب الرئيسي للمخزن — يجمع التبويبات الفرعية.

التقسيم:
  inventory_items_tab.py    → _ItemForm, _ItemsTable, _ItemsTab
  inventory_inbound_tab.py  → _InboundTab
  inventory_outbound_tab.py → _OutboundTab
  inventory_report_tab.py   → _ReportTab, _MovesPanel
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.connection import get_accounting_connection, get_inventory_connection

from ui.tabs.inventory.inventory_items_tab    import _ItemsTab
from ui.tabs.inventory.inventory_inbound_tab  import _InboundTab
from ui.tabs.inventory.inventory_outbound_tab import _OutboundTab
from ui.tabs.inventory.inventory_report_tab   import _ReportTab, _MovesPanel


class InventoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inv_conn     = get_inventory_connection()
        self.acc_conn     = get_accounting_connection()
        self._moves_panel = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._moves_panel = _MovesPanel(self.inv_conn)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#2e7d32; border-top:2px solid #2e7d32; }
        """)

        tabs.addTab(
            _ItemsTab(self.inv_conn, self.acc_conn, self._on_item_selected),
            "📦  الأصناف"
        )
        tabs.addTab(_InboundTab(self.inv_conn, self.acc_conn), "📥  وارد / شراء")
        tabs.addTab(_OutboundTab(self.inv_conn),               "📤  صادر / صرف")
        tabs.addTab(_ReportTab(self.inv_conn),                 "📊  تقرير المخزن")
        tabs.addTab(self._moves_panel,                         "🔄  حركات الصنف")

        root.addWidget(tabs)

    def _on_item_selected(self, inv_id):
        if inv_id and self._moves_panel:
            self._moves_panel.load(inv_id)

    def closeEvent(self, event):
        self.inv_conn.close()
        self.acc_conn.close()
        super().closeEvent(event)
