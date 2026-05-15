"""
ui/tabs/design_section.py
==========================
قسم "التصميمات" — يحتوي على تبويبات داخلية:
  📐 الأشكال | 📏 المقاسات | 🏷 التصنيفات | 📊 الجدول المقارن
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
)
from PyQt5.QtCore import Qt

from db.design_schema import get_design_connection, create_design_tables

# ── Import التبويبات الداخلية ──
from ui.tabs.design.shapes_tab        import ShapesTab
from ui.tabs.design.dimension_sets_tab import DimensionSetsTab
from ui.tabs.design.design_categories_tab import DesignCategoriesTab
from ui.tabs.design.compare_tab       import CompareTab

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
    }
    QTabBar::tab:selected {
        background: #ffffff;
        color: #6a1b9a;
        font-weight: bold;
        border-top: 3px solid #6a1b9a;
        padding-top: 6px;
    }
    QTabBar::tab:hover:!selected {
        background: #f3e5f5;
        color: #6a1b9a;
    }
"""


class DesignSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # تهيئة قاعدة البيانات
        self._conn = get_design_connection()
        create_design_tables(self._conn)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── رأس القسم ──
        header = QLabel("  🎨  إدارة التصميمات")
        header.setFixedHeight(42)
        header.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                color: #6a1b9a;
                padding-right: 16px;
            }
        """)
        layout.addWidget(header)

        # ── التبويبات ──
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet(_TAB_STYLE)
        tabs.setUsesScrollButtons(True)
        tabs.setElideMode(Qt.ElideNone)
        tabs.tabBar().setExpanding(False)

        tabs.addTab(ShapesTab(self._conn),          "📐  الأشكال")
        tabs.addTab(DimensionSetsTab(self._conn),   "📏  مجموعات المقاسات")
        tabs.addTab(DesignCategoriesTab(self._conn),"🏷  التصنيفات")
        tabs.addTab(CompareTab(self._conn),         "📊  الجدول المقارن")

        layout.addWidget(tabs)