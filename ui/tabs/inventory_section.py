"""
ui/tabs/inventory_tab.py
========================
التبويب الرئيسي للمخزن — يجمع التبويبات الفرعية.

التقسيم:
  inventory_items_tab.py    → _ItemForm, _ItemsTable, _ItemsTab
  inventory_inbound_tab.py  → _InboundTab
  inventory_outbound_tab.py → _OutboundTab
  inventory_report_tab.py   → _ReportTab, _MovesPanel

[تحديث] توحيد القسم مع باقي الأقسام:
  - النصوص عبر tr() بدلاً من نصوص مباشرة (ar.py / en.py).
  - الألوان عبر _C من ui.theme (المصدر: ui.theme_manager).
  - tab_style() الموحّد بدلاً من stylesheet محلي جزئي.
  - تحديث الثيم الديناميكي عبر bus.theme_changed.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.shared.connection import get_accounting_connection, get_inventory_connection

from ui.widgets.theme.layout_styles import tab_style
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.widgets.core.events         import bus

from .inventory.inventory_items_tab    import _ItemsTab
from .inventory.inventory_inbound_tab  import _InboundTab
from .inventory.inventory_outbound_tab import _OutboundTab
from .inventory.inventory_report_tab   import _ReportTab, _MovesPanel


class InventoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inv_conn     = get_inventory_connection()
        self.acc_conn     = get_accounting_connection()
        self._moves_panel = None
        self._tabs         = None
        self._build()
        bus.theme_changed.connect(self._apply_theme)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._moves_panel = _MovesPanel(self.inv_conn)

        self._tabs = QTabWidget()
        self._apply_theme()

        self._tabs.addTab(
            _ItemsTab(self.inv_conn, self.acc_conn, self._on_item_selected),
            tr("inventory_items_tab")
        )
        self._tabs.addTab(_InboundTab(self.inv_conn, self.acc_conn),  tr("inventory_inbound_tab"))
        self._tabs.addTab(_OutboundTab(self.inv_conn),                tr("inventory_outbound_tab"))
        self._tabs.addTab(_ReportTab(self.inv_conn),                  tr("inventory_report_tab"))
        self._tabs.addTab(self._moves_panel,                          tr("inventory_section_tab_moves"))

        root.addWidget(self._tabs)

    def _on_item_selected(self, inv_id):
        if inv_id and self._moves_panel:
            self._moves_panel.load(inv_id)

    def _apply_theme(self, _=None):
        if not self._tabs:
            return
        self._tabs.setStyleSheet(
            tab_style() + f"""
            QTabBar::tab:selected {{
                color: {_C['stock_ok_fg']};
                border-top: 2px solid {_C['stock_ok_fg']};
            }}
            """
        )

    def closeEvent(self, event):
        self.inv_conn.close()
        self.acc_conn.close()
        super().closeEvent(event)
