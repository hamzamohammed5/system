"""
ui/tabs/costing/product_tab.py
================================
ProductTab — التبويب الرئيسي للمنتجات (نصف مصنع / منتج نهائي).

يستخدم TabSectionBase للنمط الموحد.

[Fix E2] استبدال hardcoded strings بـ tr()
"""

from PyQt5.QtWidgets import QTabWidget

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager
from ui.widgets.core.i18n         import tr

from .product.product_main_panel import _ProductMainPanel

_SCOPE_MAP = {
    "semi":  "semi",
    "final": "final",
}

_ICON_MAP = {
    "semi":  "🔧",
    "final": "🏭",
}


class ProductTab(TabSectionBase):
    """
    التبويب الرئيسي للمنتجات.

    المعاملات:
        product_type : "semi" أو "final"

    ملاحظة: product_type يجب أن يُضبط قبل استدعاء super().__init__()
    لأن TabSectionBase يستدعي _build_tabs مباشرة.
    """

    def __init__(self, product_type: str, parent=None):
        self.product_type = product_type  # ← قبل super()
        super().__init__(parent=parent)

    def _build_tabs(self, tabs: QTabWidget):
        scope = _SCOPE_MAP.get(self.product_type, self.product_type)
        icon  = _ICON_MAP.get(self.product_type, "🏭")

        tabs.addTab(
            _ProductMainPanel(self.conn, self.product_type),
            f"{icon}  {tr('product_tab')}",
        )
        tabs.addTab(
            CategoryManager(self.conn, scope=scope),
            f"🏷️  {tr('categories_tab')}",
        )