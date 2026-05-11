"""
ui/tabs/costing_section.py
==========================
قسم "حساب التكلفة" — تبويبات داخلية:
  📦 الخامات | 🔧 نصف مصنع | 🏭 منتج نهائي | 👷 العمالة | ⚙️ التشغيل
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from ui.tabs.costing_section import RawTab
from ui.tabs.costing_section import ProductTab
from ui.tabs.costing_section import LaborTab
from ui.tabs.costing_section import MachineTab

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
        color: #1565c0;
        font-weight: bold;
        border-top: 2px solid #1565c0;
    }
    QTabBar::tab:hover:!selected {
        background: #e8f0fe;
        color: #1565c0;
    }
"""


class CostingSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  📊  حساب التكلفة")
        header.setFixedHeight(42)
        header.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                color: #1565c0;
                padding-right: 16px;
            }
        """)
        layout.addWidget(header)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setStyleSheet(_TAB_STYLE)

        self._tabs.addTab(RawTab(),            "📦  الخامات")
        self._tabs.addTab(ProductTab("semi"),  "🔧  نصف مصنع")
        self._tabs.addTab(ProductTab("final"), "🏭  منتج نهائي")
        self._tabs.addTab(LaborTab(),          "👷  العمالة")
        self._tabs.addTab(MachineTab(),        "⚙️  التشغيل")

        layout.addWidget(self._tabs)