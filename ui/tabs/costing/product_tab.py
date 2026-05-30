"""
ui/tabs/costing/product_tab.py
================================
ProductTab — التبويب الرئيسي للمنتجات (نصف مصنع / منتج نهائي).

يستخدم TabSectionBase للنمط الموحد.

التقسيم:
  product/product_form.py        → _FormPanel
  product/product_table.py       → _ProductTable, _WarningBar
  product/product_main_panel.py  → _ProductMainPanel
  product_tab.py                 → ProductTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QTabWidget

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager

from .product.product_main_panel import _ProductMainPanel

_SCOPE_MAP = {
    "semi":  "semi",
    "final": "final",
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
        icon  = "🔧" if self.product_type == "semi" else "🏭"

        tabs.addTab(
            _ProductMainPanel(self.conn, self.product_type),
            f"{icon}  المنتجات",
        )
        tabs.addTab(
            CategoryManager(self.conn, scope=scope),
            "🏷️  التصنيفات",
        )