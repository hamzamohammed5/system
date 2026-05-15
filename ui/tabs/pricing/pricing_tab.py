"""
ui/tabs/pricing/pricing_tab.py
================================
PricingTab — التبويب الرئيسي للتسعير.

التقسيم الداخلي:
  pricing/_stat_box.py      → دالة stat_box المساعدة
  pricing/_pricing_panel.py → _PricingPanel (اللوحة الرئيسية)
  pricing_tab.py            → PricingTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.shared.connection import get_connection
from ui.widgets.shared.category_manager import CategoryManager

from .pricing._pricing_panel import _PricingPanel


class PricingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        tabs.addTab(_PricingPanel(self.conn),                  "💰  الأسعار")
        tabs.addTab(CategoryManager(self.conn, scope="final"), "🏷️  التصنيفات")
        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)