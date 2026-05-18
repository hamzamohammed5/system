"""
ui/widgets/shared/base_section.py
===================================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSizePolicy, QSplitter,
)
from PyQt5.QtCore import Qt, QTimer

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

    def _create_list(self):
        raise NotImplementedError

    def _create_detail(self):
        raise NotImplementedError

    def _connect_signals(self):
        pass

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(5)
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
                width: 5px;
            }}
            QSplitter::handle:hover {{
                background: {_C['accent_mid']};
            }}
            QSplitter::handle:pressed {{
                background: {_C['accent']};
            }}
        """)
        self._splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        # ✅ الـ list: حد أدنى وأقصى — الـ splitter يتحرك بحرية بينهم
        self._list.setMinimumWidth(self.LIST_MIN_W)
        self._list.setMaximumWidth(self.LIST_MAX_W)
        self._list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # ✅ الـ detail: يتمدد ويأخذ كل المساحة الزيادة
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._detail.setMinimumWidth(300)

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        root.addWidget(self._splitter)

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

    def _fit_splitter(self):
        self._apply_sizes()

    def _fit_splitter_delayed(self, delay_ms: int = 80):
        QTimer.singleShot(delay_ms, self._apply_sizes)

    def refresh(self):
        if hasattr(self._list, 'refresh'):
            self._list.refresh()
        self._fit_splitter_delayed()