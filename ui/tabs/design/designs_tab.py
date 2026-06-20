"""
ui/tabs/design/designs_tab.py  — v2
======================================
تبويب التصميمات — تصميم محسّن:

  يسار (220px) : DesignsCategoriesPanel — تصنيفات مستقلة للتصميمات
  وسط  (flex)  : _DesignsTable — كروت Grid بـ thumbnail كبير
  يمين (flex)  : _DesignDetailPanel — تفاصيل + إضافة مقاسات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel,
)
from PyQt5.QtCore import Qt

from .designs._designs_table            import _DesignsTable
from .designs._design_detail_panel      import _DesignDetailPanel
from .designs._designs_categories_panel import DesignsCategoriesPanel
from ui.theme import _C


class DesignsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══ 1. Sidebar التصنيفات ══════════════════════
        self._cats_panel = DesignsCategoriesPanel(self.conn)

        # ══ 2. Splitter: قائمة + تفاصيل ══════════════
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
            }}
            QSplitter::handle:hover {{
                background: {_C['accent_mid']};
            }}
        """)

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
        splitter.setSizes([360, 640])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        # ترتيب: sidebar | splitter
        root.addWidget(self._cats_panel)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {_C['border']};")
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