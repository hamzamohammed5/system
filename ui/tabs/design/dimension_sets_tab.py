"""
ui/tabs/design/dimension_sets_tab.py
=====================================
تبويب إدارة مجموعات المقاسات.

التخطيط:
  [تبويب: إدخال المقاسات]
    └── _ValuesPanel (قايمة المجموعات + جدول القيم + popup تعديل)

  [تبويب: المجموعات]
    └── _GroupsPanel
          ├── يسار: _CategoriesPanel  (إدارة التصنيفات)
          └── يمين: _SetsManagerPanel (إدارة المجموعات + _FieldsPanel)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import Qt

from .dimension_sets._values_panel import _ValuesPanel
from .dimension_sets._groups_panel import _GroupsPanel
from ui.widgets.core.i18n import tr


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
        self._values_panel = _ValuesPanel(self.conn)
        inner_tabs.addTab(self._values_panel, tr("dimension_sets_tab_values"))

        # ══ تبويب 2: المجموعات ══
        self._groups_panel = _GroupsPanel(self.conn)

        # لما تتغير المجموعات أو التصنيفات → نحدّث قايمة المجموعات في تبويب الإدخال
        self._groups_panel.sets_changed.connect(
            self._values_panel._sets_list.refresh
        )
        self._groups_panel._cats_panel.changed.connect(
            self._values_panel._sets_list.refresh
        )

        inner_tabs.addTab(self._groups_panel, tr("dimension_sets_tab_groups"))
        inner_tabs.currentChanged.connect(self._on_tab_changed)

        root.addWidget(inner_tabs)

    def _on_tab_changed(self, index):
        if index == 1:
            self._groups_panel.refresh()