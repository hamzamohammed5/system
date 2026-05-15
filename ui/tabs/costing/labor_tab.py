"""
ui/tabs/costing/labor_tab.py
====================================
LaborTab — التبويب الرئيسي للعمالة.

التقسيم الداخلي:
  labor_settings.py  → _LaborSettingsPanel
  labor_op_form.py   → _LaborOpForm
  labor_op_table.py  → _LaborOpTable
  labor_tab.py       → _LaborOpsTab, LaborTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QSplitter
from PyQt5.QtCore import Qt

from db.shared.connection import get_connection
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


class LaborTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._settings = _LaborSettingsPanel(self.conn)

        tabs = QTabWidget()
        tabs.addTab(self._settings,                                "⚙️  إعدادات العمالة")
        tabs.addTab(_LaborOpsTab(self.conn, self._settings),       "📋  عمليات العمالة")
        tabs.addTab(CategoryManager(self.conn, scope="labor"),     "🏷️  التصنيفات")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)