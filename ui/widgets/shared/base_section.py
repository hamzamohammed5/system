"""
ui/widgets/shared/base_section.py
===================================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.

القاعدة:
  - الـ list panel عرضه يتحدد من الـ splitter بحرية كاملة
  - الـ detail panel يأخذ كل المساحة الزيادة عند تكبير النافذة
  - لو الـ content أكبر من النافذة يظهر horizontal scrollbar
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QSizePolicy, QSplitter, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer

from ui.app_settings import _C

_SCROLL_SS = f"""
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        border-radius: 4px;
        margin: 0 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {_C['border_med']};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""


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
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ✅ Scroll area أفقية تحيط بالكل
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(_SCROLL_SS)

        # الـ container الداخلي
        self._container = QWidget()
        self._container.setStyleSheet(f"background:{_C['bg_page']};")
        container_lay = QHBoxLayout(self._container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)

        # ✅ الـ splitter بدون قيود
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(5)
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
            }}
            QSplitter::handle:hover {{
                background: {_C['accent_mid']};
            }}
            QSplitter::handle:pressed {{
                background: {_C['accent']};
            }}
        """)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        # ✅ الـ list: حد أدنى وأقصى فقط — الـ splitter يتحرك بحرية
        self._list.setMinimumWidth(self.LIST_MIN_W)
        self._list.setMaximumWidth(self.LIST_MAX_W)
        self._list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # ✅ الـ detail: يأخذ كل المساحة الزيادة
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._detail.setMinimumWidth(300)

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setStretchFactor(0, 0)   # الـ list لا يتمدد تلقائياً
        self._splitter.setStretchFactor(1, 1)   # الـ detail يتمدد

        container_lay.addWidget(self._splitter)
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll)

    # ══════════════════════════════════════════════════════
    # ضبط الأحجام الابتدائية للـ splitter
    # ══════════════════════════════════════════════════════

    def _apply_sizes(self):
        """يضبط الـ splitter مرة واحدة عند التحميل."""
        total = self._splitter.width()
        if total <= 0:
            total = self.width()
        if total <= 0:
            QTimer.singleShot(100, self._apply_sizes)
            return

        list_w   = max(self.LIST_MIN_W, min(self._list.width() or self.LIST_MIN_W, self.LIST_MAX_W))
        detail_w = max(300, total - list_w - self._splitter.handleWidth())
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