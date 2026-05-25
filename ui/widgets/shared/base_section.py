"""
ui/widgets/shared/base_section.py
===================================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.

[تحديث v4]:
  - get_splitter_style() مستوردة من panels مباشرة (لا inline CSS)
  - BusConnectedMixin للربط التلقائي بالـ bus
  - _apply_sizes أنظف مع fallback timer
  - دعم LAYOUT_DIRECTION لتغيير ترتيب list/detail
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSizePolicy, QSplitter,
)
from PyQt5.QtCore import Qt, QTimer

from ui.widgets.shared.panles_helper.theme import get_splitter_style
from ui.widgets.shared.shared_ui_mixins import BusConnectedMixin


class BaseSection(QWidget, BusConnectedMixin):
    LIST_MIN_W      : int  = 280
    LIST_MAX_W      : int  = 560
    DETAIL_MIN_W    : int  = 320
    CONNECT_BUS     : bool = False
    LAYOUT_REVERSED : bool = False

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._connect_signals()
        if self.CONNECT_BUS:
            self._connect_bus(data=True)
        QTimer.singleShot(50, self._apply_sizes)

    # ── override ──────────────────────────────────────────

    def _create_list(self):
        raise NotImplementedError

    def _create_detail(self):
        raise NotImplementedError

    def _connect_signals(self):
        if hasattr(self._list, 'item_selected') and hasattr(self._detail, 'load_item'):
            self._list.item_selected.connect(self._detail.load_item)

    def _on_data_changed(self):
        self.refresh()

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(5)
        self._splitter.setStyleSheet(get_splitter_style())
        self._splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        self._list.setMinimumWidth(self.LIST_MIN_W)
        self._list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._detail.setMinimumWidth(self.DETAIL_MIN_W)
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.LAYOUT_REVERSED:
            self._splitter.addWidget(self._detail)
            self._splitter.addWidget(self._list)
            self._splitter.setCollapsible(0, False)
            self._splitter.setCollapsible(1, False)
            self._splitter.setStretchFactor(0, 1)
            self._splitter.setStretchFactor(1, 0)
        else:
            self._splitter.addWidget(self._list)
            self._splitter.addWidget(self._detail)
            self._splitter.setCollapsible(0, False)
            self._splitter.setCollapsible(1, False)
            self._splitter.setStretchFactor(0, 0)
            self._splitter.setStretchFactor(1, 1)

        root.addWidget(self._splitter)

    def _apply_sizes(self):
        total = self._splitter.width()
        if total <= 0:
            total = self.width()
        if total <= 0:
            QTimer.singleShot(100, self._apply_sizes)
            return
        list_w = max(
            self.LIST_MIN_W,
            min(getattr(self._list, 'width', lambda: self.LIST_MIN_W)() or self.LIST_MIN_W,
                self.LIST_MAX_W)
        )
        detail_w = max(
            self.DETAIL_MIN_W,
            total - list_w - self._splitter.handleWidth()
        )
        self._splitter.blockSignals(True)
        if self.LAYOUT_REVERSED:
            self._splitter.setSizes([detail_w, list_w])
        else:
            self._splitter.setSizes([list_w, detail_w])
        self._splitter.blockSignals(False)

    # ── API عام ───────────────────────────────────────────

    def refresh(self):
        if hasattr(self._list, 'refresh'):
            self._list.refresh()
        QTimer.singleShot(80, self._apply_sizes)

    def clear_detail(self):
        if hasattr(self._detail, 'clear'):
            self._detail.clear()

    def _fit_splitter_delayed(self, delay_ms: int = 80):
        QTimer.singleShot(delay_ms, self._apply_sizes)

    @property
    def list_panel(self) -> QWidget:
        return self._list

    @property
    def detail_panel(self) -> QWidget:
        return self._detail