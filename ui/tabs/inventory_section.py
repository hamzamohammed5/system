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

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from ui.widgets.theme.layout_styles import tab_style, apply_tab_widths, normalize_tab_widget
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.font                        import FS_MD
from ui.constants                    import SECTION_HEADER_HEIGHT, SECTION_HEADER_BORDER_W, SECTION_HEADER_PAD_RIGHT
from ui.widgets.core.widget_mixin   import WidgetMixin

from .inventory.items._items_tab    import _ItemsTab
from .inventory.inventory_inbound_tab  import _InboundTab
from .inventory.inventory_outbound_tab import _OutboundTab
from .inventory.inventory_report_tab   import _ReportTab, _MovesPanel


class InventoryTab(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        from services.companies.company_service import CompanyService
        self.inv_conn     = CompanyService.get_active_inventory_conn()
        self.acc_conn     = CompanyService.get_active_accounting_conn()
        self._moves_panel = None
        self._tabs         = None
        self._build()
        self._init_widget_mixin(theme=True, font=False, lang=True, data=False)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── هيدر القسم ── (كان ناقص مقارنة بباقي الأقسام: التكلفة/الحسابات/التسعير/التصميمات)
        self._header = QLabel(f"  {tr('nav_icon_inventory')}  {tr('nav_inventory')}")
        self._header.setFixedHeight(SECTION_HEADER_HEIGHT)
        root.addWidget(self._header)

        self._moves_panel = _MovesPanel(self.inv_conn)

        self._tabs = QTabWidget()
        normalize_tab_widget(self._tabs)
        self._tabs.setStyleSheet(tab_style())

        self._tabs.addTab(
            _ItemsTab(self.inv_conn, self.acc_conn, self._on_item_selected),
            tr("inventory_items_tab")
        )
        self._tabs.addTab(_InboundTab(self.inv_conn, self.acc_conn),  tr("inventory_inbound_tab"))
        self._tabs.addTab(_OutboundTab(self.inv_conn),                tr("inventory_outbound_tab"))
        self._tabs.addTab(_ReportTab(self.inv_conn),                  tr("inventory_report_tab"))
        self._tabs.addTab(self._moves_panel,                          tr("inventory_section_tab_moves"))
        apply_tab_widths(self._tabs)

        root.addWidget(self._tabs)

    def _on_item_selected(self, inv_id):
        if inv_id and self._moves_panel:
            self._moves_panel.load(inv_id)

    def _refresh_style(self, *_):
        if hasattr(self, "_header"):
            self._header.setStyleSheet(f"""
                QLabel {{
                    background: {_C['bg_surface']};
                    border-bottom: {SECTION_HEADER_BORDER_W}px solid {_C['border']};
                    font-size: {FS_MD}px;
                    font-weight: bold;
                    color: {_C['accent']};
                    padding-right: {SECTION_HEADER_PAD_RIGHT}px;
                }}
            """)
        if not self._tabs:
            return
        self._tabs.setStyleSheet(tab_style())
        apply_tab_widths(self._tabs)

    def _refresh_lang(self, *_):
        if hasattr(self, "_header"):
            self._header.setText(f"  {tr('nav_icon_inventory')}  {tr('nav_inventory')}")
        if not self._tabs:
            return
        self._tabs.setTabText(0, tr("inventory_items_tab"))
        self._tabs.setTabText(1, tr("inventory_inbound_tab"))
        self._tabs.setTabText(2, tr("inventory_outbound_tab"))
        self._tabs.setTabText(3, tr("inventory_report_tab"))
        self._tabs.setTabText(4, tr("inventory_section_tab_moves"))
        # [حل مركزي] لازم يُعاد الحساب هنا كمان: النص العربي والإنجليزي
        # مش نفس الطول، فتغيير اللغة لازم يعيد ضبط min-width.
        apply_tab_widths(self._tabs)

    def closeEvent(self, event):
        self.inv_conn.close()
        self.acc_conn.close()
        super().closeEvent(event)
