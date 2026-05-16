"""
ui/tabs/design/designs_tab.py
==============================
تبويب إدارة التصميمات — نسخة جديدة كاملة.

التخطيط:
  ┌─────────────────┬──────────────────────────────────────┐
  │  قائمة التصميم  │         لوحة تفاصيل التصميم          │
  │  (جدول + فلتر)  │  اسم + ملاحظات                       │
  │                 │  ─────────────────────────────────── │
  │                 │  مقاسات التصميم (بطاقات)              │
  │                 │  كل بطاقة: مجموعة + instance + مسار  │
  │                 │  + أزرار (فتح GIMP / تعيين مسار)      │
  └─────────────────┴──────────────────────────────────────┘
"""



from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,

)
from PyQt5.QtCore import Qt





# ── ألوان ──
_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_GREEN_LT   = "#e8f5e9"
_ORANGE     = "#e65100"
_ORANGE_LT  = "#fff3e0"
_RED        = "#c62828"
_RED_LT     = "#fdecea"
_GRAY_BG    = "#f8f9fc"
_BORDER     = "#e0e7f3"
_TEXT       = "#1a2340"
_TEXT_MUTED = "#7a869a"



from .designs._designs_table import _DesignsTable
from .designs._design_detail_panel import _DesignDetailPanel




# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class DesignsTab(QWidget):
    """التبويب الرئيسي لإدارة التصميمات."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_BORDER}; }}
            QSplitter::handle:hover {{ background: {_BLUE_MID}; }}
        """)

        # ── يمين: لوحة التفاصيل ──
        self._detail = _DesignDetailPanel(self.conn)

        # ── يسار: جدول التصميمات ──
        self._table = _DesignsTable(self.conn, self._detail)

        self._detail.saved.connect(self._table.refresh)
        self._detail.cleared.connect(self._table.refresh)
        self._table.design_deleted.connect(self._table.refresh)

        splitter.addWidget(self._table)
        splitter.addWidget(self._detail)
        splitter.setSizes([340, 660])

        root.addWidget(splitter)

    def refresh(self):
        self._table.refresh()
        self._detail._reload_categories()