"""
ui/tabs/pricing_section.py
==========================
قسم "التسعير" — يحتوي على تبويبات داخلية:
  💰 الأسعار الأساسية (وبداخله: الأسعار + التصنيفات)

ملاحظة:
  تبويب التصنيفات بات موجوداً داخل PricingTab مباشرة،
  بنفس نمط ProductTab — لا يوجد تغيير مطلوب في هذا الملف
  إلا لو أردت إضافة تبويبات جديدة على مستوى القسم.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore    import Qt

from ui.tabs.pricing_tab import PricingTab

_TAB_STYLE = """
    QTabWidget::pane {
        border: none;
        background: #f9f9f9;
    }
    QTabBar::tab {
        background: #f0f0f0;
        border: 1px solid #ddd;
        border-bottom: none;
        padding: 8px 18px;
        margin-left: 2px;
        font-size: 12px;
        color: #555;
    }
    QTabBar::tab:selected {
        background: #ffffff;
        color: #e65100;
        font-weight: bold;
        border-top: 2px solid #e65100;
    }
    QTabBar::tab:hover:!selected {
        background: #fff3e0;
        color: #e65100;
    }
"""


class PricingSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  💰  التسعير")
        header.setFixedHeight(42)
        header.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                color: #e65100;
                padding-right: 16px;
            }
        """)
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet(_TAB_STYLE)

        # PricingTab نفسه بقى يحتوي على تبويبين داخليين:
        #   ① الأسعار  ② التصنيفات
        tabs.addTab(PricingTab(), "💰  الأسعار الأساسية")

        layout.addWidget(tabs)