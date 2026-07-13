# """
# ui/tabs/design/designs_tab.py  — v2
# ======================================

"""
ui/tabs/design/designs_tab.py  — v2
======================================
تبويب التصميمات — تصميم محسّن:

  يسار (220px) : DesignsCategoriesPanel — تصنيفات مستقلة للتصميمات
  وسط  (flex)  : _DesignsTable — كروت Grid بـ thumbnail كبير
  يمين (flex)  : _DesignDetailPanel — تفاصيل + إضافة مقاسات
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout,
    QSplitter,
)
from PyQt5.QtCore import Qt

from ui.widgets.panels.themed_inputs import ThemedFrame


from .designs._designs_table            import _DesignsTable
from .designs._design_detail_panel      import _DesignDetailPanel
from .designs._designs_categories_panel import DesignsCategoriesPanel
from ui.theme import _C
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    MARGIN_ZERO, SPACING_ZERO, SMART_SPLITTER_HANDLE_W,
    DESIGNS_TAB_SPLITTER_LIST_W, DESIGNS_TAB_SPLITTER_DETAIL_W,
)


class DesignsTab(QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
            }}
            QSplitter::handle:hover {{
                background: {_C['accent_mid']};
            }}
        """)
        self._sep.setStyleSheet(f"color: {_C['border']};")

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.setSpacing(SPACING_ZERO)

        # ══ 1. Sidebar التصنيفات ══════════════════════
        self._cats_panel = DesignsCategoriesPanel(self.conn)

        # ══ 2. Splitter: قائمة + تفاصيل ══════════════
        splitter = QSplitter(Qt.Horizontal)
        self._splitter = splitter
        splitter.setHandleWidth(SMART_SPLITTER_HANDLE_W)

        # لوحة التفاصيل (تُنشأ أولاً لأن _DesignsTable تحتاجها)
        self._detail = _DesignDetailPanel(self.conn)

        # قائمة الكروت
        self._table = _DesignsTable(self.conn, self._detail)

        # ── ربط الـ signals ──
        self._detail.saved.connect(self._on_detail_saved)
        self._detail.cleared.connect(self._table.refresh)
        self._table.design_deleted.connect(self._table.refresh)
        self._table.set_filter_changed.connect(self._detail.filter_by_set)

        # فلتر التصنيفات من الـ sidebar
        self._cats_panel.category_changed.connect(self._on_category_changed)

        # ── ربط تحديث combo التصنيف في لوحة التفاصيل ──
        # لما يتضاف/يتعدل/يتحذف تصنيف من الـ sidebar،
        # الـ combo في لوحة التفاصيل يتحدث تلقائياً
        self._detail.connect_categories_panel(self._cats_panel)

        splitter.addWidget(self._table)
        splitter.addWidget(self._detail)
        splitter.setSizes([DESIGNS_TAB_SPLITTER_LIST_W, DESIGNS_TAB_SPLITTER_DETAIL_W])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        # ترتيب: sidebar | splitter
        root.addWidget(self._cats_panel)

        self._sep = ThemedFrame()
        sep = self._sep
        sep.setFrameShape(ThemedFrame.VLine)
        root.addWidget(sep)

        root.addWidget(splitter, stretch=1)

    def _on_category_changed(self, cat_id):
        """عند اختيار تصنيف من الـ sidebar."""
        self._table.filter_by_category(cat_id)

    def _on_detail_saved(self):
        """بعد حفظ التصميم — تحديث القائمة والـ sidebar."""
        self._table.refresh()
        self._cats_panel.refresh()

    def refresh(self):
        self._table.refresh()
        self._detail._reload_categories()
        self._cats_panel.refresh()