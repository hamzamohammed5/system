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
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.theme.layout_styles import tab_style, apply_tab_widths, normalize_tab_widget
from ui.constants import MARGIN_ZERO


class DimensionSetsTab(QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._init_widget_mixin(theme=True, font=False, data=False)
        self._refresh_lang()

    def _refresh_style(self, *_):
        if hasattr(self, "_inner_tabs"):
            self._inner_tabs.setStyleSheet(tab_style())
            apply_tab_widths(self._inner_tabs)

    def _refresh_lang(self, *_):
        idx_values = self._inner_tabs.indexOf(self._values_panel)
        idx_groups = self._inner_tabs.indexOf(self._groups_panel)
        self._inner_tabs.setTabText(idx_values, tr("dimension_sets_tab_values"))
        self._inner_tabs.setTabText(idx_groups, tr("dimension_sets_tab_groups"))
        apply_tab_widths(self._inner_tabs)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)

        self._inner_tabs = QTabWidget()
        normalize_tab_widget(self._inner_tabs)
        inner_tabs = self._inner_tabs

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

        self._refresh_style()
        root.addWidget(inner_tabs)

    def _on_tab_changed(self, index):
        if index == 1:
            self._groups_panel.refresh()