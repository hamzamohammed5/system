"""
ui/tabs/design/dimension_sets_tab.py
=====================================
تبويب إدارة مجموعات المقاسات.

التغييرات:
  1. _FieldDialog  — خانة الاعتمادية تختار مجموعة مقاسات + حقل منها (cross-set)
  2. _ValuesPanel  — لما تختار مجموعة مصدر في الاعتمادية، القيم بتتحمل منها تلقائياً
                     + حقل "الاسم" لكل صف يتحفظ في value_text
  3. _GroupsPanel  — تبويب "المجموعات" يحتوي الآن على إدارة كاملة للتصنيفات
                     (إضافة / تعديل / حذف) بجانب عرض المجموعات
  4. _SetsPanel    — أُزيل منه فورم التصنيفات؛ الـ combo يكتفي بالاختيار فقط
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,
    QTabWidget
)
from PyQt5.QtCore import Qt


from .dimension_sets._sets_panel import _SetsPanel
from .dimension_sets._fields_panel import _FieldsPanel
from .dimension_sets._values_panel import _ValuesPanel
from .dimension_sets._groups_panel import _GroupsPanel



# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class DimensionSetsTab(QWidget):
    """
    التبويب الرئيسي لإدارة مجموعات المقاسات.

    التخطيط:
      [تبويب: مجموعات المقاسات]
        └── Splitter أفقي:
              ├── يسار:  _SetsPanel   (قائمة + فورم — بدون فورم تصنيفات)
              └── يمين:  Splitter رأسي:
                    ├── أعلى: _FieldsPanel  (الحقول + اعتماديات)
                    └── أسفل: _ValuesPanel  (إدخال قيم)

      [تبويب: المجموعات]
        └── _GroupsPanel
              ├── يسار: _CategoriesPanel  (إدارة التصنيفات: شجرة + فورم)
              └── يمين: جدول المجموعات
    """

    def __init__(self, conn, parent=None):
        super().__init__(conn if False else None)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        inner_tabs = QTabWidget()

        # ── تبويب المجموعات + الحقول + الإدخال ──
        sets_widget = QWidget()
        sets_layout = QVBoxLayout(sets_widget)
        sets_layout.setContentsMargins(0, 0, 0, 0)

        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(5)
        h_splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        self._sets_panel = _SetsPanel(self.conn)

        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(5)
        v_splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        self._fields_panel = _FieldsPanel(self.conn)
        self._values_panel = _ValuesPanel(self.conn)

        v_splitter.addWidget(self._fields_panel)
        v_splitter.addWidget(self._values_panel)
        v_splitter.setSizes([280, 380])

        h_splitter.addWidget(self._sets_panel)
        h_splitter.addWidget(v_splitter)
        h_splitter.setSizes([340, 660])

        self._sets_panel.set_selected.connect(self._fields_panel.load_set)
        self._fields_panel.set_selected.connect(self._on_set_selected_for_values)
        self._fields_panel.fields_changed.connect(self._on_fields_changed)

        sets_layout.addWidget(h_splitter)
        inner_tabs.addTab(sets_widget, "📏  إدخال المقاسات")

        # ── تبويب المجموعات (إدارة التصنيفات + عرض المجموعات) ──
        self._groups_panel = _GroupsPanel(self.conn)
        # لما يتغير تصنيف، نحدّث combo التصنيفات في _SetsPanel
        self._groups_panel._cats_panel.changed.connect(self._sets_panel.refresh)
        inner_tabs.addTab(self._groups_panel, "📋  المجموعات")

        inner_tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(inner_tabs)

    def _on_set_selected_for_values(self, set_id: int):
        self._values_panel.load_set(set_id)

    def _on_tab_changed(self, index):
        if index == 1:
            self._groups_panel.refresh()

    def _on_fields_changed(self):
        if self._values_panel._set_id is not None:
            self._values_panel.load_set(self._values_panel._set_id)