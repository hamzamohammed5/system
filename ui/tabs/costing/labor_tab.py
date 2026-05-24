"""
ui/tabs/costing/labor_tab.py
====================================
LaborTab — التبويب الرئيسي للعمالة.

يرث من TabSectionBase للتوحيد مع RawTab و ProductTab.
"""

from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.shared.tab_section_base import TabSectionBase
from ui.widgets.shared.category_manager import CategoryManager

from .labor.labor_settings import _LaborSettingsPanel
from .labor.labor_op_form  import _LaborOpForm
from .labor.labor_op_table import _LaborOpTable

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #bbdefb; }
"""


class _LaborOpsTab(QWidget):
    def __init__(self, conn, settings, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form  = _LaborOpForm(conn, settings)
        self._table = _LaborOpTable(conn, settings, self._form)

        splitter.addWidget(self._form)
        splitter.addWidget(self._table)
        splitter.setSizes([280, 400])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


class LaborTab(TabSectionBase):
    """
    التبويب الرئيسي للعمالة — يرث من TabSectionBase للتوحيد البصري.
    """

    def _build_tabs(self, tabs: QTabWidget):
        # _LaborSettingsPanel محتاج conn — نبنيه هنا ونمرره للـ ops tab
        self._settings = _LaborSettingsPanel(self.conn)

        tabs.addTab(self._settings,                                "⚙️  إعدادات العمالة")
        tabs.addTab(_LaborOpsTab(self.conn, self._settings),       "📋  عمليات العمالة")
        tabs.addTab(CategoryManager(self.conn, scope="labor"),     "🏷️  التصنيفات")