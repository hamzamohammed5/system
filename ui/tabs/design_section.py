"""
ui/tabs/design_section.py
==========================
قسم "التصميمات" — تبويبات داخلية:
  📐 المقاسات     → DimensionSetsTab
  🎨 التصميمات   → DesignsTab
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore    import Qt

from db.designs.design_schema import get_designs_connection, create_designs_tables

from .design.dimension_sets_tab import DimensionSetsTab
from .design.designs_tab        import DesignsTab

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
        color: #7b1fa2;
        font-weight: bold;
        border-top: 2px solid #7b1fa2;
    }
    QTabBar::tab:hover:!selected {
        background: #f3e5f5;
        color: #7b1fa2;
    }
"""


class DesignSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # إنشاء قاعدة بيانات التصميمات
        self.conn = get_designs_connection()
        create_designs_tables(self.conn)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  🎨  التصميمات")
        header.setFixedHeight(42)
        header.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                color: #7b1fa2;
                padding-right: 16px;
            }
        """)
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet(_TAB_STYLE)

        self._dim_tab     = DimensionSetsTab(self.conn)
        self._designs_tab = DesignsTab(self.conn)

        tabs.addTab(self._dim_tab,     "📐  المقاسات")
        tabs.addTab(self._designs_tab, "🎨  التصميمات")

        # عند تغيير التبويب لـ "التصميمات"، نعمل refresh لتحميل أي مجموعات جديدة
        tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(tabs)

    def _on_tab_changed(self, index):
        if index == 1:  # تبويب التصميمات
            self._designs_tab.refresh()

    def closeEvent(self, event):
        try:
            self.conn.close()
        except Exception:
            pass
        super().closeEvent(event)