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

from services.design import get_designs_conn_and_init

from ui.widgets.theme.layout_styles import tab_style, apply_tab_style
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.font                        import FS_MD
from ui.constants                    import SECTION_HEADER_HEIGHT, SECTION_HEADER_BORDER_W, SECTION_HEADER_PAD_RIGHT
from ui.widgets.core.widget_mixin   import WidgetMixin

from .design.dimension_sets_tab import DimensionSetsTab
from .design.designs_tab        import DesignsTab


class DesignSection(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        # إنشاء قاعدة بيانات التصميمات
        self.conn = get_designs_conn_and_init()
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ──
        self._header = QLabel(f"  {tr('nav_icon_design')}  {tr('nav_design')}")
        self._header.setFixedHeight(SECTION_HEADER_HEIGHT)
        self._refresh_style()
        layout.addWidget(self._header)

        # ── التبويبات ──
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        apply_tab_style(self._tabs)

        self._dim_tab     = DimensionSetsTab(self.conn)
        self._designs_tab = DesignsTab(self.conn)

        self._tabs.addTab(self._dim_tab,     tr("dimension_sets_tab"))
        self._tabs.addTab(self._designs_tab, tr("designs_tab"))

        # عند تغيير التبويب لـ "التصميمات"، نعمل refresh لتحميل أي مجموعات جديدة
        self._tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self._tabs)

    def _on_tab_changed(self, index):
        if index == 1:  # تبويب التصميمات
            self._designs_tab.refresh()

    def _refresh_style(self, *_):
        self._header.setStyleSheet(f"""
            QLabel {{
                background: {_C['bg_surface']};
                border-bottom: {SECTION_HEADER_BORDER_W}px solid {_C['border']};
                font-size: {FS_MD}px;
                font-weight: bold;
                color: {_C['purple']};
                padding-right: {SECTION_HEADER_PAD_RIGHT}px;
            }}
        """)
        if hasattr(self, "_tabs"):
            apply_tab_style(self._tabs)

    def closeEvent(self, event):
        try:
            self.conn.close()
        except Exception:
            pass
        super().closeEvent(event)