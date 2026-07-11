"""
ui/tabs/costing/labor_tab.py
====================================
LaborTab — التبويب الرئيسي للعمالة.

يرث من TabSectionBase للتوحيد مع RawTab و ProductTab.

[Fix A1] استبدال from ui.app_settings import _C بـ from ui.theme import _C
[Fix A6] إصلاح from ui.events import bus → from ui.widgets.core.events import bus
[Fix C4] استبدال tr() بنصوص عربية مباشرة بمفاتيح i18n صحيحة
[Fix C-const] استخدام LABOR_TAB_SPLITTER_HANDLE_W و LABOR_TAB_SPLITTER_SIZES في _LaborOpsTab
[Fix B] تحويل _LaborOpsTab إلى WidgetMixin لتحديث stylesheet الـ splitter ديناميكياً
"""

from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager
from ui.widgets.core.i18n         import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    LABOR_TAB_SPLITTER_HANDLE_W, LABOR_TAB_SPLITTER_SIZES,
)

from .labor.labor_settings import _LaborSettingsPanel
from .labor.labor_op_form  import LaborOpForm
from .labor.labor_op_table import LaborOpTable


class _LaborOpsTab(QWidget, WidgetMixin):
    def __init__(self, conn, settings, parent=None):
        super().__init__(parent)
        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(LABOR_TAB_SPLITTER_HANDLE_W)

        self._form  = LaborOpForm(conn, settings)
        self._table = LaborOpTable(conn, settings, self._form)

        self._splitter.addWidget(self._form)
        self._splitter.addWidget(self._table)
        self._splitter.setSizes(list(LABOR_TAB_SPLITTER_SIZES))
        self._splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._splitter)

        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
                border-top: 1px solid {_C['border_med']};
            }}
            QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
            QSplitter::handle:pressed {{ background: {_C['accent']}; }}
        """)


class LaborTab(TabSectionBase):
    """
    التبويب الرئيسي للعمالة — يرث من TabSectionBase للتوحيد البصري.
    """

    def __init__(self, parent=None):
        from services.companies.company_service import CompanyService
        super().__init__(conn_fn=CompanyService.get_active_erp_conn, parent=parent)

    def _build_tabs(self, tabs: QTabWidget):
        self._settings = _LaborSettingsPanel(self.conn)

        tabs.addTab(self._settings,
                    f"{tr('labor_settings_icon')}  {tr('labor_settings')}")
        tabs.addTab(_LaborOpsTab(self.conn, self._settings),
                    f"{tr('labor_operations_icon')}  {tr('labor_operations')}")
        tabs.addTab(CategoryManager(self.conn, scope="labor"),
                    f"{tr('categories_tab_icon')}  {tr('categories_tab')}")
