"""
ui/tabs/design/dimension_sets_tab.py
=====================================
تبويب إدارة مجموعات المقاسات.

التخطيط:
  [تبويب: إدخال المقاسات]
    └── Splitter أفقي:
          ├── يسار:  _SetsPanel   (اختيار المجموعة فقط)
          └── يمين:  _ValuesPanel (إدخال القيم)

  [تبويب: المجموعات]
    └── _GroupsPanel
          ├── يسار: _CategoriesPanel  (إدارة التصنيفات)
          └── يمين: _SetsManagerPanel (إدارة المجموعات + _FieldsPanel)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTabWidget,
)
from PyQt5.QtCore import Qt

from .dimension_sets._sets_panel   import _SetsPanel
from .dimension_sets._values_panel import _ValuesPanel
from .dimension_sets._groups_panel import _GroupsPanel


class DimensionSetsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        inner_tabs = QTabWidget()

        # ══ تبويب 1: إدخال المقاسات ══
        sets_widget = QWidget()
        sets_layout = QVBoxLayout(sets_widget)
        sets_layout.setContentsMargins(0, 0, 0, 0)

        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(5)
        h_splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        self._sets_panel   = _SetsPanel(self.conn)
        self._values_panel = _ValuesPanel(self.conn)

        h_splitter.addWidget(self._sets_panel)
        h_splitter.addWidget(self._values_panel)
        h_splitter.setSizes([340, 660])

        # لما تختار مجموعة → تتحمل قيمها
        self._sets_panel.set_selected.connect(self._values_panel.load_set)

        sets_layout.addWidget(h_splitter)
        inner_tabs.addTab(sets_widget, "📏  إدخال المقاسات")

        # ══ تبويب 2: المجموعات ══
        self._groups_panel = _GroupsPanel(self.conn)
        # لما تتغير التصنيفات → نحدّث فلتر _SetsPanel
        self._groups_panel._cats_panel.changed.connect(self._sets_panel.refresh)
        inner_tabs.addTab(self._groups_panel, "📋  المجموعات")

        inner_tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(inner_tabs)

    def _on_tab_changed(self, index):
        if index == 1:
            self._groups_panel.refresh()