"""
ui/tabs/costing/product_tab.py
================================
ProductTab — التبويب الرئيسي للمنتجات (نصف مصنع / منتج نهائي).

التقسيم:
  product_form.py       → _FormPanel
  product_table.py      → _ProductTable, _WarningBar
  product_main_panel.py → _ProductMainPanel, _catalog_for_component_row
  product_tab.py        → ProductTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.connection import get_connection
from ui.widgets.shared.category_manager import CategoryManager

from .product.product_main_panel import _ProductMainPanel

_PRODUCT_SCOPE = {
    "semi":  "semi",
    "final": "final",
}


class ProductTab(QWidget):
    def __init__(self, product_type: str, parent=None):
        super().__init__(parent)
        self.product_type = product_type
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scope = _PRODUCT_SCOPE.get(self.product_type, self.product_type)
        tabs  = QTabWidget()

        icon       = "🔧" if self.product_type == "semi" else "🏭"
        label_main = f"{icon}  المنتجات"
        tabs.addTab(_ProductMainPanel(self.conn, self.product_type), label_main)
        tabs.addTab(CategoryManager(self.conn, scope=scope), "🏷️  التصنيفات")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)