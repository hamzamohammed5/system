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

    def __init__(self, parent=None):
        from services.companies.company_service import CompanyService
        super().__init__(conn_fn=CompanyService.get_active_erp_conn, parent=parent)

    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(RawSection(self.conn),
                    f"{tr('tab_icon_raw')}  {tr('raw_tab')}")
        tabs.addTab(CategoryManager(self.conn, scope="raw"),
                    f"{tr('categories_tab_icon')}  {tr('categories_tab')}")

    def _tab_label(self, index: int):
        # [إصلاح lang] hook TabSectionBase الجديدة — بتخلي عناوين
        # التابين ("الخامات"/"التصنيفات") تتحدث لايف عند تغيير اللغة.
        return {
            0: f"{tr('tab_icon_raw')}  {tr('raw_tab')}",
            1: f"{tr('categories_tab_icon')}  {tr('categories_tab')}",
        }.get(index)