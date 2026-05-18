"""
ui/widgets/shared/base_section.py
===================================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.

القاعدة:
  - الـ list panel عرضه يتحدد مرة واحدة عند التحميل من _auto_resize
  - الـ splitter قابل للسحب بحرية بعد كده
  - الـ detail panel يأخذ كل المساحة الزيادة عند تكبير النافذة
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QSplitter
from PyQt5.QtCore    import Qt, QTimer

from ui.app_settings import _C


class BaseSection(QWidget):

    LIST_MIN_W : int = 280
    LIST_MAX_W : int = 560

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._connect_signals()
        QTimer.singleShot(50, self._apply_sizes)

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

        # رفع القيود عن الـ list عشان الـ splitter يتحرك بحرية
        self._list.setMinimumWidth(self.LIST_MIN_W)
        self._list.setMaximumWidth(self.LIST_MAX_W)
        self._list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        root.addWidget(self._splitter)

    # ══════════════════════════════════════════════════════
    # ضبط الأحجام — مرة واحدة عند التحميل فقط
    # ══════════════════════════════════════════════════════

    def _apply_sizes(self):
        """يضبط الـ splitter مرة واحدة بناءً على عرض الـ list الفعلي."""
        # اقرأ الـ fixed width اللي حدده _auto_resize
        list_w = self._list.minimumSizeHint().width()
        # لو الـ list له fixed width، استخدمه
        if self._list.minimumWidth() == self._list.maximumWidth():
            list_w = self._list.minimumWidth()
        else:
            list_w = self._list.width()
            if list_w <= 0:
                list_w = self.LIST_MIN_W

        list_w = max(self.LIST_MIN_W, min(list_w, self.LIST_MAX_W))

        total    = self._splitter.width()
        if total <= 0:
            total = self.width()
        detail_w = max(400, total - list_w - self._splitter.handleWidth())
        self._splitter.setSizes([list_w, detail_w])

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _fit_splitter(self):
        self._apply_sizes()

    def _fit_splitter_delayed(self, delay_ms: int = 80):
        QTimer.singleShot(delay_ms, self._apply_sizes)

    def refresh(self):
        if hasattr(self._list, 'refresh'):
            self._list.refresh()
        self._fit_splitter_delayed()