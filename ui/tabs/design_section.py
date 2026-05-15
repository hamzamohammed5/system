"""
ui/tabs/design_section.py
==========================
قسم "التصميمات" — تبويبات داخلية:
  📐 الأشكال | 📏 المجموعات | 📂 التصنيفات | 🏷 تصنيفات الأشكال | 📊 الجدول المقارن

التغيير: DimCategoriesTab الآن يعمل على designs.db فقط
(dim_set_categories بدل categories scope=design في erp.db)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from PyQt5.QtCore import Qt

from db.design.design_schema import get_design_connection, create_design_tables

from ui.tabs.design.shapes_tab             import ShapesTab
from ui.tabs.design.dimension_sets_tab     import DimensionSetsTab
from ui.tabs.design.dim_categories_tab     import DimCategoriesTab
from ui.tabs.design.design_categories_tab  import DesignCategoriesTab
from ui.tabs.design.compare_tab            import CompareTab

_TAB_STYLE = """
    QTabWidget::pane { border:none; background:#f9f9f9; }
    QTabBar { alignment: right; }
    QTabBar::tab {
        background:#f0f0f0; border:1px solid #ddd; border-bottom:none;
        padding:8px 14px; margin-left:3px; font-size:12px; color:#555;
        min-width:90px;
    }
    QTabBar::tab:selected {
        background:#ffffff; color:#1565c0; font-weight:bold;
        border-top:3px solid #1565c0; padding-top:6px;
    }
    QTabBar::tab:hover:!selected { background:#e3f2fd; color:#1565c0; }
"""


class DesignSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn = get_design_connection()
        create_design_tables(self._conn)
        self._ensure_migrations()
        self._build()

    def _ensure_migrations(self):
        """يضيف الأعمدة الناقصة بأمان."""
        try:
            cols = {r["name"] for r in
                    self._conn.execute(
                        "PRAGMA table_info(dimension_sets)"
                    ).fetchall()}
            if "category_id" not in cols:
                self._conn.execute(
                    "ALTER TABLE dimension_sets ADD COLUMN category_id INTEGER "
                    "REFERENCES dim_set_categories(id) ON DELETE SET NULL"
                )
                self._conn.commit()
        except Exception as e:
            print(f"[DesignSection] migration dimension_sets: {e}")

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  🎨  إدارة التصميمات")
        header.setFixedHeight(42)
        header.setStyleSheet("""
            QLabel {
                background:#ffffff; border-bottom:1px solid #e0e0e0;
                font-size:14px; font-weight:bold; color:#1565c0;
                padding-right:16px;
            }
        """)
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet(_TAB_STYLE)
        tabs.setUsesScrollButtons(True)
        tabs.setElideMode(Qt.ElideNone)
        tabs.tabBar().setExpanding(False)

        # كل التبويبات تستخدم self._conn (designs.db) فقط
        tabs.addTab(ShapesTab(self._conn),
                    "📐  الأشكال")
        tabs.addTab(DimensionSetsTab(self._conn),
                    "📏  مجموعات المقاسات")
        tabs.addTab(DimCategoriesTab(self._conn),
                    "📂  تصنيفات المقاسات")
        tabs.addTab(DesignCategoriesTab(self._conn),
                    "🏷  تصنيفات الأشكال")
        tabs.addTab(CompareTab(self._conn),
                    "📊  الجدول المقارن")

        layout.addWidget(tabs)