"""
ui/tabs/costing_section.py
==========================
قسم "حساب التكلفة" — تبويبات داخلية:
  📦 الخامات | 🔧 نصف مصنع | 🏭 منتج نهائي | 👷 العمالة | ⚙️ التشغيل
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSizePolicy
from PyQt5.QtCore import Qt

from .costing.raw_tab import RawTab
from .costing.product_tab import ProductTab
from .costing.labor_tab import LaborTab
from .costing.machine_tab import MachineTab

_TAB_STYLE = """
    QTabWidget::pane {
        border: none;
        background: #f9f9f9;
    }

    QTabBar {
        alignment: right;
    }

    QTabBar::tab {
        background: #f0f0f0;
        border: 1px solid #ddd;
        border-bottom: none;
        padding: 8px 14px;
        margin-left: 3px;
        font-size: 12px;
        color: #555;
        min-width: 90px;
        max-width: 200px;
    }

    QTabBar::tab:selected {
        background: #ffffff;
        color: #1565c0;
        font-weight: bold;
        border-top: 3px solid #1565c0;
        padding-top: 6px;
    }

    QTabBar::tab:hover:!selected {
        background: #e8f0fe;
        color: #1565c0;
    }

    QTabBar::scroller {
        width: 28px;
    }

    QTabBar QToolButton {
        background: #e8eaf6;
        border: 1px solid #c5cae9;
        border-radius: 3px;
        color: #3949ab;
        font-size: 12px;
        min-width: 24px;
        min-height: 24px;
    }

    QTabBar QToolButton:hover {
        background: #c5cae9;
    }

    QTabBar QToolButton:disabled {
        background: #f5f5f5;
        color: #bbb;
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

        # السماح للتبويبات بالتمرير عند الضيق بدلاً من الاختصار
        self._tabs.setUsesScrollButtons(True)
        self._tabs.setElideMode(Qt.ElideNone)
        tab_bar = self._tabs.tabBar()
        tab_bar.setExpanding(False)      # لا تمد التبويبات قسراً
        tab_bar.setDrawBase(True)

        self._tabs.addTab(RawTab(),            "📦  الخامات")
        self._tabs.addTab(ProductTab("semi"),  "🔧  نصف مصنع")
        self._tabs.addTab(ProductTab("final"), "🏭  منتج نهائي")
        self._tabs.addTab(LaborTab(),          "👷  العمالة")
        self._tabs.addTab(MachineTab(),        "⚙️  التشغيل")

        layout.addWidget(self._tabs)