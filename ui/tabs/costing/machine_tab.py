# ui/tabs/costing/machine_tab.py
# ================================
# MachineTab — التبويب الرئيسي للماكينات وعمليات التشغيل.
"""
ui/tabs/costing/machine_tab.py
================================
MachineTab — التبويب الرئيسي للماكينات وعمليات التشغيل.

يرث من TabSectionBase للتوحيد مع RawTab و ProductTab و LaborTab.

[Fix A1] استبدال from ui.app_settings import _C بـ from ui.theme import _C
[Fix C3] استبدال tr() بنصوص عربية مباشرة بمفاتيح i18n صحيحة
[Fix E-icons] استبدال إيموجي hardcoded بمفاتيح tr() جديدة
[Fix C-const] استبدال أحجام splitter الـ hardcoded بثوابت constants.py
[Fix B] تحويل _MachinesTab و _MachineOpsTab إلى WidgetMixin لتحديث stylesheet الـ splitter ديناميكياً
"""

from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager
from ui.widgets.core.i18n         import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    MACHINE_TAB_SPLITTER_HANDLE_W,
    MACHINE_TAB_MACHINES_SPLITTER_SIZES,
    MACHINE_TAB_OPS_SPLITTER_SIZES,
)

from .machine.machine_form     import _MachineForm
from .machine.machine_table    import _MachineTable
from .machine.machine_op_form  import _MachineOpForm
from .machine.machine_op_table import _MachineOpTable


class _MachinesTab(QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(MACHINE_TAB_SPLITTER_HANDLE_W)

        form  = _MachineForm(conn)
        table = _MachineTable(conn, form)

        self._splitter.addWidget(form)
        self._splitter.addWidget(table)
        self._splitter.setSizes(list(MACHINE_TAB_MACHINES_SPLITTER_SIZES))
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


class _MachineOpsTab(QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(MACHINE_TAB_SPLITTER_HANDLE_W)

        form  = _MachineOpForm(conn)
        table = _MachineOpTable(conn, form)

        self._splitter.addWidget(form)
        self._splitter.addWidget(table)
        self._splitter.setSizes(list(MACHINE_TAB_OPS_SPLITTER_SIZES))
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


class MachineTab(TabSectionBase):
    """
    التبويب الرئيسي للماكينات — يرث من TabSectionBase للتوحيد البصري.
    """

    def __init__(self, parent=None):
        from services.companies.company_service import CompanyService
        super().__init__(conn_fn=CompanyService.get_active_erp_conn, parent=parent)

    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(_MachinesTab(self.conn),
                    f"{tr('machines_icon')}  {tr('machines')}")
        tabs.addTab(_MachineOpsTab(self.conn),
                    f"{tr('machine_operations_icon')}  {tr('machine_operations')}")
        tabs.addTab(CategoryManager(self.conn, scope="machine"),
                    f"{tr('categories_tab_icon')}  {tr('categories_tab')}")

    def _tab_label(self, index: int):
        # [إصلاح lang] hook TabSectionBase الجديدة.
        return {
            0: f"{tr('machines_icon')}  {tr('machines')}",
            1: f"{tr('machine_operations_icon')}  {tr('machine_operations')}",
            2: f"{tr('categories_tab_icon')}  {tr('categories_tab')}",
        }.get(index)
