"""
ui/tabs/costing/raw_tab.py
================================
RawTab — التبويب الرئيسي للخامات.

يستخدم TabSectionBase للنمط الموحد.

التقسيم الداخلي:
  raw/raw_input_panel.py  → _InputPanel
  raw/raw_table_panel.py  → _TablePanel
  raw/raw_section.py      → _RawSection  (input + table)
  raw_tab.py              → RawTab       (هذا الملف)
"""

from PyQt5.QtWidgets import QTabWidget

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager

from .raw.raw_section import _RawSection


class RawTab(TabSectionBase):
    """
    التبويب الرئيسي للخامات:
      📦 الخامات   → _RawSection
      🏷️ التصنيفات → CategoryManager
    """

    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(_RawSection(self.conn),                  "📦  الخامات")
        tabs.addTab(CategoryManager(self.conn, scope="raw"), "🏷️  التصنيفات")