"""
ui/tabs/costing/raw_tab.py
================================
RawTab — التبويب الرئيسي للخامات.

التقسيم الداخلي:
  raw_input_panel.py → _InputPanel
  raw_table_panel.py → _TablePanel
  raw_tab.py         → _RawItemsTab, RawTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QSplitter
from PyQt5.QtCore import Qt

from db.connection import get_connection
from ui.widgets.category_manager import CategoryManager

from .raw.raw_input_panel import _InputPanel
from .raw.raw_table_panel import _TablePanel

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #bbdefb; }
"""


class _RawItemsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._input = _InputPanel(conn)
        self._table = _TablePanel(conn, self._input)

        splitter.addWidget(self._input)
        splitter.addWidget(self._table)
        splitter.setSizes([300, 400])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


class RawTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tabs = QTabWidget()
        tabs.addTab(_RawItemsTab(self.conn),                  "📦  الخامات")
        tabs.addTab(CategoryManager(self.conn, scope="raw"),  "🏷️  التصنيفات")
        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)