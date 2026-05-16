"""
ui/tabs/design/designs_tab.py
==============================
تبويب إدارة التصميمات.
يربط signal تغيير فلتر المجموعة من الجدول بلوحة التفاصيل.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from .designs._designs_table       import _DesignsTable
from .designs._design_detail_panel import _DesignDetailPanel

_BORDER  = "#e0e7f3"
_BLUE_MID = "#bbdefb"


class DesignsTab(QWidget):
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

        # لوحة التفاصيل أولاً (تحتاجها _DesignsTable)
        self._detail = _DesignDetailPanel(self.conn)

        # جدول التصميمات
        self._table = _DesignsTable(self.conn, self._detail)

        # ── ربط الـ signals ──
        self._detail.saved.connect(self._table.refresh)
        self._detail.cleared.connect(self._table.refresh)
        self._table.design_deleted.connect(self._table.refresh)

        # فلتر مجموعة المقاسات → فلترة بطاقات لوحة التفاصيل
        self._table.set_filter_changed.connect(self._detail.filter_by_set)

        splitter.addWidget(self._table)
        splitter.addWidget(self._detail)
        splitter.setSizes([340, 660])

        root.addWidget(splitter)

    def refresh(self):
        self._table.refresh()
        self._detail._reload_categories()