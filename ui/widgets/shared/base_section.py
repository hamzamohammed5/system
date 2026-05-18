"""
ui/widgets/shared/base_section.py
===================================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.

القاعدة:
  - الـ list panel عرضه Fixed = عرض الأعمدة بالضبط (من _auto_resize)
  - الـ detail panel Expanding يأخذ كل الزيادة عند تكبير النافذة
  - الـ horizontal scroll في الـ list panel معطّل دايماً
  - لما النافذة تكبر، الـ list panel مش بيتأثر
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QSplitter
from PyQt5.QtCore    import Qt, QTimer

from ui.app_settings import _C


class BaseSection(QWidget):
    """
    قاعدة مشتركة للأقسام اللي فيها list + detail.

    Override:
      _create_list()       → يرجع list panel
      _create_detail()     → يرجع detail panel
      _connect_signals()   → يربط الـ signals
      LIST_MIN_W, LIST_MAX_W
    """

    LIST_MIN_W : int = 280
    LIST_MAX_W : int = 560

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._connect_signals()
        QTimer.singleShot(0, self._fit_splitter)

    # ══════════════════════════════════════════════════════
    # override في الـ subclass
    # ══════════════════════════════════════════════════════

    def _create_list(self):
        raise NotImplementedError

    def _create_detail(self):
        raise NotImplementedError

    def _connect_signals(self):
        pass

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; }}
            QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
            QSplitter::handle:pressed {{ background: {_C['accent']}; }}
        """)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        # الـ detail: Expanding — يأخذ كل المساحة الزيادة
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setStretchFactor(0, 0)   # list: لا stretch
        self._splitter.setStretchFactor(1, 1)   # detail: كل الزيادة

        root.addWidget(self._splitter)

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _fit_splitter(self):
        """يضبط الـ splitter بناءً على العرض الفعلي للـ list panel."""
        list_w = self._list.width()
        if list_w <= 0:
            list_w = self.LIST_MIN_W
        total = self._splitter.width()
        if total <= list_w:
            total = self.width()
        detail_w = max(200, total - list_w - self._splitter.handleWidth())
        self._splitter.setSizes([list_w, detail_w])

    def _fit_splitter_delayed(self, delay_ms: int = 80):
        QTimer.singleShot(delay_ms, self._fit_splitter)

    def refresh(self):
        if hasattr(self._list, 'refresh'):
            self._list.refresh()
        self._fit_splitter_delayed()