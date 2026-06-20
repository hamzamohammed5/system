"""
ui/tabs/design_section.py
==========================
قسم "التصميمات" — تبويبات داخلية:
  📐 المقاسات     → DimensionSetsTab
  🎨 التصميمات   → DesignsTab

[تحديث] توحيد القسم مع باقي الأقسام:
  - النصوص عبر tr() بدلاً من نصوص مباشرة (ar.py / en.py).
  - الألوان عبر _C من ui.theme (المصدر: ui.theme_manager).
  - الخط عبر font.py (FS_*).
  - تحديث الثيم الديناميكي عبر bus.theme_changed.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from db.designs.design_schema import get_designs_connection, create_designs_tables

from ui.widgets.theme.layout_styles import tab_style
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.widgets.core.events         import bus
from ui.font                        import FS_MD

from .design.dimension_sets_tab import DimensionSetsTab
from .design.designs_tab        import DesignsTab


class DesignSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # إنشاء قاعدة بيانات التصميمات
        self.conn = get_designs_connection()
        create_designs_tables(self.conn)
        self._build()
        bus.theme_changed.connect(self._apply_theme)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ──
        self._header = QLabel(f"  🎨  {tr('nav_design')}")
        self._header.setFixedHeight(42)
        self._apply_theme()
        layout.addWidget(self._header)

        # ── التبويبات ──
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setStyleSheet(tab_style())

        self._dim_tab     = DimensionSetsTab(self.conn)
        self._designs_tab = DesignsTab(self.conn)

        self._tabs.addTab(self._dim_tab,     tr("design_section_tab_dimensions"))
        self._tabs.addTab(self._designs_tab, tr("design_section_tab_designs"))

        # عند تغيير التبويب لـ "التصميمات"، نعمل refresh لتحميل أي مجموعات جديدة
        self._tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self._tabs)

    def _on_tab_changed(self, index):
        if index == 1:  # تبويب التصميمات
            self._designs_tab.refresh()

    def _apply_theme(self, _=None):
        self._header.setStyleSheet(f"""
            QLabel {{
                background: {_C['bg_surface']};
                border-bottom: 1px solid {_C['border']};
                font-size: {FS_MD}px;
                font-weight: bold;
                color: {_C['purple']};
                padding-right: 16px;
            }}
        """)
        if hasattr(self, "_tabs"):
            self._tabs.setStyleSheet(tab_style())

    def closeEvent(self, event):
        try:
            self.conn.close()
        except Exception:
            pass
        super().closeEvent(event)