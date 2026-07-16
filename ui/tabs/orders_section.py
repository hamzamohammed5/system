"""
ui/tabs/orders_section.py
==========================
قسم إدارة الطلبات والعملاء.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from services.orders.order_service import get_orders_conn_and_init
from ui.tabs.orders.orders_tab    import OrdersTab
from ui.tabs.orders.customers_tab import CustomersTab
from ui.tabs.orders.dashboard_tab import OrdersDashboardTab
from ui.widgets.theme.layout_styles import tab_style, apply_tab_widths, normalize_tab_widget
from ui.theme                        import _C
from ui.widgets.core.i18n import tr
from ui.font                        import FS_MD
from ui.constants                    import SECTION_HEADER_HEIGHT, SECTION_HEADER_BORDER_W, SECTION_HEADER_PAD_RIGHT
from ui.widgets.core.widget_mixin import WidgetMixin


class OrdersSection(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_orders_conn_and_init()
        self._build()
        self._init_widget_mixin(theme=True, font=False, lang=True, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        # [إصلاح dark-theme] tab_style() كانت بتتطبق مرة واحدة بس وقت
        # الإنشاء في _build(). OrdersSection ماكانتش مشتركة في
        # bus.theme_changed أصلًا (theme=False) ومكانش عندها _refresh_style()
        # خالص، فالتاب بار (لوحة المتابعة / الطلبات / العملاء) كان يفضل
        # بالستايل القديم (الفاتح) بعد التحويل لـ dark.
        if hasattr(self, "_header"):
            self._header.setStyleSheet(f"""
                QLabel {{
                    background: {_C['bg_surface']};
                    border-bottom: {SECTION_HEADER_BORDER_W}px solid {_C['border']};
                    font-size: {FS_MD}px;
                    font-weight: bold;
                    color: {_C['success']};
                    padding-right: {SECTION_HEADER_PAD_RIGHT}px;
                }}
            """)
        if hasattr(self, "_tabs"):
            self._tabs.setStyleSheet(tab_style())
            apply_tab_widths(self._tabs)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ── (كان ناقص مقارنة بباقي الأقسام)
        self._header = QLabel(f"  {tr('nav_icon_orders')}  {tr('nav_orders')}")
        self._header.setFixedHeight(SECTION_HEADER_HEIGHT)
        layout.addWidget(self._header)

        self._tabs = QTabWidget()
        normalize_tab_widget(self._tabs)
        self._tabs.setStyleSheet(tab_style())

        self._dashboard_tab = OrdersDashboardTab(self.conn)
        self._orders_tab    = OrdersTab(self.conn)
        self._customers_tab = CustomersTab(self.conn)

        self._tabs.addTab(self._dashboard_tab, tr("orders_section_tab_dashboard"))
        self._tabs.addTab(self._orders_tab,    tr("orders_section_tab_orders"))
        self._tabs.addTab(self._customers_tab, tr("orders_section_tab_customers"))
        apply_tab_widths(self._tabs)

        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs)

    def _refresh_lang(self, *_):
        if hasattr(self, "_header"):
            self._header.setText(f"  {tr('nav_icon_orders')}  {tr('nav_orders')}")
        if not hasattr(self, "_tabs"):
            return
        self._tabs.setTabText(0, tr("orders_section_tab_dashboard"))
        self._tabs.setTabText(1, tr("orders_section_tab_orders"))
        self._tabs.setTabText(2, tr("orders_section_tab_customers"))
        apply_tab_widths(self._tabs)

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
