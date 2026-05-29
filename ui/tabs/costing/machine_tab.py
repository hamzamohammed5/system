"""
ui/tabs/costing/machine_tab.py
================================
MachineTab — التبويب الرئيسي للماكينات وعمليات التشغيل.

يرث من TabSectionBase للتوحيد مع RawTab و ProductTab و LaborTab.
"""

from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.shared.tab_section_base import TabSectionBase
from ui.widgets.shared.category_manager import CategoryManager

from .machine.machine_form     import _MachineForm
from .machine.machine_table    import _MachineTable
from .machine.machine_op_form  import _MachineOpForm
from .machine.machine_op_table import _MachineOpTable

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #bbdefb; }
"""


class _MachinesTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

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
        splitter.setStyleSheet(_SPLITTER_STYLE)

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
        tabs.addTab(_MachinesTab(self.conn),                       "🖥️  الماكينات")
        tabs.addTab(_MachineOpsTab(self.conn),                     "⚙️  عمليات التشغيل")
        tabs.addTab(CategoryManager(self.conn, scope="machine"),   "🏷️  التصنيفات")