"""
ui/tabs/costing/raw_tab.py
================================
RawTab — التبويب الرئيسي للخامات.

يستخدم TabSectionBase للنمط الموحد.

[Fix E1] استبدال hardcoded strings بـ tr()
"""

from PyQt5.QtWidgets import QTabWidget

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager
from ui.widgets.core.i18n         import tr

from .raw.raw_section import RawSection


class RawTab(TabSectionBase):
    """
    التبويب الرئيسي للخامات:
      📦 الخامات   → _RawSection
      🏷️ التصنيفات → CategoryManager
    """

    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(RawSection(self.conn),
                    f"📦  {tr('raw_tab')}")
        tabs.addTab(CategoryManager(self.conn, scope="raw"),
                    f"🏷️  {tr('categories_tab')}")