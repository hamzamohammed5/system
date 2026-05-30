"""
ui/tabs/costing/machine_tab.py
================================
MachineTab — التبويب الرئيسي للماكينات وعمليات التشغيل.

يرث من TabSectionBase للتوحيد مع RawTab و ProductTab و LaborTab.

[Refactor] استبدال hardcoded strings بـ tr().
[Refactor] ربط _SPLITTER_STYLE بـ _C بدل ألوان ثابتة.
"""

from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager
from ui.widgets.core.i18n         import tr
from ui.app_settings              import _C

from .machine.machine_form     import _MachineForm
from .machine.machine_table    import _MachineTable
from .machine.machine_op_form  import _MachineOpForm
from .machine.machine_op_table import _MachineOpTable


def _splitter_style() -> str:
    """style موحد للـ QSplitter مربوط بـ _C."""
    return f"""
        QSplitter::handle {{
            background: {_C['border']};
            border-top: 1px solid {_C['border_med']};
        }}
        QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
        QSplitter::handle:pressed {{ background: {_C['accent']}; }}
    """


class _MachinesTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_splitter_style())

        form  = _MachineForm(conn)
        table = _MachineTable(conn, form)

        splitter.addWidget(form)
        splitter.addWidget(table)
        splitter.setSizes([260, 380])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


class _MachineOpsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_splitter_style())

        form  = _MachineOpForm(conn)
        table = _MachineOpTable(conn, form)

        splitter.addWidget(form)
        splitter.addWidget(table)
        splitter.setSizes([300, 400])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


class MachineTab(TabSectionBase):
    """
    التبويب الرئيسي للماكينات — يرث من TabSectionBase للتوحيد البصري.
    """

    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(_MachinesTab(self.conn),
                    f"🖥️  {tr('الماكينات')}")
        tabs.addTab(_MachineOpsTab(self.conn),
                    f"⚙️  {tr('عمليات التشغيل')}")
        tabs.addTab(CategoryManager(self.conn, scope="machine"),
                    f"🏷️  {tr('التصنيفات')}")