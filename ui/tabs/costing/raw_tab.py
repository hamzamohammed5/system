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

from ui.widgets.shared.tab_section_base  import TabSectionBase
from ui.widgets.shared.category_manager  import CategoryManager

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