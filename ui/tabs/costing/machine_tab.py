"""
ui/tabs/costing/machine_tab.py
================================
MachineTab — التبويب الرئيسي للماكينات وعمليات التشغيل.

[M2] تحويل _MachinesTab و_MachineOpsTab القديمتين (QSplitter يدوي)
     إلى _MachinesSection و_MachineOpsSection
     باستخدام QSplitter Vertical موحد من splitter_style().
"""

from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.shared.tab_section_base import TabSectionBase
from ui.widgets.shared.category_manager import CategoryManager
from ui.widgets.theme.styles import splitter_style

from .machine.machine_form     import _MachineForm
from .machine.machine_table    import _MachineTable
from .machine.machine_op_form  import _MachineOpForm
from .machine.machine_op_table import _MachineOpTable


class _MachinesSection(QWidget):
    """
    قسم الماكينات — فورم فوق + جدول تحت.

    يستخدم QSplitter(Vertical) بـ style موحد من splitter_style().
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(splitter_style())

        self._form_panel = _MachineForm(self._conn)
        self._list_panel = _MachineTable(self._conn, self._form_panel)

        splitter.addWidget(self._form_panel)
        splitter.addWidget(self._list_panel)
        splitter.setSizes([260, 380])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)

        self._connect_signals()
        root.addWidget(splitter)

    def _connect_signals(self):
        if hasattr(self._form_panel, "saved"):
            self._form_panel.saved.connect(self._list_panel.refresh)


class _MachineOpsSection(QWidget):
    """
    قسم عمليات التشغيل — فورم فوق + جدول تحت.

    يستخدم QSplitter(Vertical) بـ style موحد من splitter_style().
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(splitter_style())

        self._form_panel = _MachineOpForm(self._conn)
        self._list_panel = _MachineOpTable(self._conn, self._form_panel)

        splitter.addWidget(self._form_panel)
        splitter.addWidget(self._list_panel)
        splitter.setSizes([300, 400])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)

        self._connect_signals()
        root.addWidget(splitter)

    def _connect_signals(self):
        if hasattr(self._form_panel, "saved"):
            self._form_panel.saved.connect(self._list_panel.refresh)


class MachineTab(TabSectionBase):
    """
    التبويب الرئيسي للماكينات — يرث من TabSectionBase للتوحيد البصري.
    """

    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(_MachinesSection(self.conn),                    "🖥️  الماكينات")
        tabs.addTab(_MachineOpsSection(self.conn),                  "⚙️  عمليات التشغيل")
        tabs.addTab(CategoryManager(self.conn, scope="machine"),    "🏷️  التصنيفات")