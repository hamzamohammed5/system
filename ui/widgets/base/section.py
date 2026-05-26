"""
widgets/base/section.py
========================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QSplitter
from PyQt5.QtCore    import Qt, QTimer

from ..theme.styles  import splitter_style   # المصدر الوحيد
from ..mixins.bus    import BusConnectedMixin


class BaseSection(QWidget, BusConnectedMixin):
    """
    قاعدة مشتركة للأقسام ذات التخطيط list + detail.

    Override المطلوب:
        _create_list()   → QWidget
        _create_detail() → QWidget

    Override الاختياري:
        _connect_signals()
        _on_data_changed()
        LIST_MIN_W, LIST_MAX_W, DETAIL_MIN_W
        CONNECT_BUS, LAYOUT_REVERSED
    """

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

    def _create_list(self) -> QWidget:
        raise NotImplementedError

    def _create_detail(self) -> QWidget:
        raise NotImplementedError

    def _connect_signals(self):
        if hasattr(self._list, "item_selected") and hasattr(self._detail, "load_item"):
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
        self._splitter.setStyleSheet(splitter_style())
        self._splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        self._list.setMinimumWidth(self.LIST_MIN_W)
        self._list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._detail.setMinimumWidth(self.DETAIL_MIN_W)
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.LAYOUT_REVERSED:
            widgets  = [self._detail, self._list]
            stretches = [1, 0]
        else:
            widgets  = [self._list, self._detail]
            stretches = [0, 1]

        for i, w in enumerate(widgets):
            self._splitter.addWidget(w)
            self._splitter.setCollapsible(i, False)
            self._splitter.setStretchFactor(i, stretches[i])

        root.addWidget(self._splitter)

    def _apply_sizes(self):
        total = self._splitter.width() or self.width()
        if total <= 0:
            QTimer.singleShot(100, self._apply_sizes)
            return

        list_w   = max(self.LIST_MIN_W, min(self.LIST_MIN_W + 60, self.LIST_MAX_W))
        detail_w = max(self.DETAIL_MIN_W, total - list_w - self._splitter.handleWidth())

        self._splitter.blockSignals(True)
        sizes = [detail_w, list_w] if self.LAYOUT_REVERSED else [list_w, detail_w]
        self._splitter.setSizes(sizes)
        self._splitter.blockSignals(False)

    # ── API ───────────────────────────────────────────────

    def refresh(self):
        if hasattr(self._list, "refresh"):
            self._list.refresh()
        QTimer.singleShot(80, self._apply_sizes)

    def clear_detail(self):
        if hasattr(self._detail, "clear"):
            self._detail.clear()

    @property
    def list_panel(self) -> QWidget:
        return self._list

    @property
    def detail_panel(self) -> QWidget:
        return self._detail