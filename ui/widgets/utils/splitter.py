"""
ui/widgets/utils/splitter.py
=============================
أدوات الـ splitter الموحدة.
"""
import logging
from PyQt5.QtWidgets import QSplitter, QTableWidget, QWidget, QSizePolicy
from PyQt5.QtCore    import Qt, QTimer, QObject, QEvent

from ui.app_settings import _C

logger = logging.getLogger(__name__)

_MIN_LIST_W = 280
_MAX_LIST_W = 620


def splitter_style() -> str:
    return f"""
        QSplitter::handle {{ background:{_C['border']}; }}
        QSplitter::handle:hover {{ background:{_C['accent_mid']}; }}
        QSplitter::handle:pressed {{ background:{_C['accent']}; }}
    """


def fit_list_panel(splitter: QSplitter, list_index: int,
                   table: QTableWidget, min_w: int = _MIN_LIST_W,
                   max_w: int = _MAX_LIST_W, extra_pad: int = 24) -> int:
    """يضبط عرض لوحة القائمة في الـ splitter."""
    from ..tables.items import calc_width

    sizes = splitter.sizes()
    if not sizes or len(sizes) <= list_index:
        return min_w

    total = sum(sizes)
    if total <= 0:
        return min_w

    ideal  = calc_width(table, extra_pad)
    target = max(min_w, min(ideal, max_w))

    remaining  = total - target
    old_other  = total - sizes[list_index]
    new_sizes  = list(sizes)
    new_sizes[list_index] = target

    if len(sizes) > 1 and old_other > 0:
        for i, sz in enumerate(sizes):
            if i != list_index:
                ratio = sz / old_other if old_other > 0 else 1.0
                new_sizes[i] = max(200, int(remaining * ratio))

    diff = total - sum(new_sizes)
    if diff != 0:
        other = 1 - list_index
        if other < len(new_sizes):
            new_sizes[other] = max(200, new_sizes[other] + diff)

    splitter.setSizes(new_sizes)
    return target


def fit_list_panel_delayed(splitter: QSplitter, list_index: int,
                            table: QTableWidget, delay_ms: int = 0,
                            min_w: int = _MIN_LIST_W, max_w: int = _MAX_LIST_W):
    QTimer.singleShot(
        delay_ms,
        lambda: fit_list_panel(splitter, list_index, table, min_w, max_w)
    )


class SmartSplitter(QSplitter):
    """QSplitter مع ضبط تلقائي لعرض لوحة القائمة."""

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._list_index = 0
        self._table      = None
        self._min_w      = _MIN_LIST_W
        self._max_w      = _MAX_LIST_W
        self.setHandleWidth(4)
        self.setStyleSheet(splitter_style())

    def set_list_widget(self, widget: QWidget, list_table: QTableWidget,
                        list_index: int = 0,
                        min_w: int = _MIN_LIST_W, max_w: int = _MAX_LIST_W):
        self._list_index = list_index
        self._table      = list_table
        self._min_w      = min_w
        self._max_w      = max_w

        detail_idx = 1 - list_index
        w = self.widget(detail_idx)
        if w:
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def fit_now(self) -> int:
        if self._table is None:
            return self._min_w
        return fit_list_panel(self, self._list_index, self._table,
                              self._min_w, self._max_w)

    def fit_delayed(self, delay_ms: int = 50):
        if self._table is None:
            return
        fit_list_panel_delayed(self, self._list_index, self._table,
                               delay_ms, self._min_w, self._max_w)


class SplitterScrollGuard(QObject):
    """
    يمنع الـ splitter من التوسع أكتر من عرض الجدول
    لما الـ horizontal scrollbar مش ظاهر.
    """

    def __init__(self, splitter: QSplitter, table: QTableWidget,
                 table_index: int = 0, extra_pad: int = 20,
                 parent: QObject = None):
        super().__init__(parent)
        self._splitter    = splitter
        self._table       = table
        self._table_index = table_index
        self._extra_pad   = extra_pad
        self._locked_w    = None

        splitter.splitterMoved.connect(self._on_moved)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._check_scroll)

        if table.viewport():
            table.viewport().installEventFilter(self)
        table.horizontalScrollBar().rangeChanged.connect(
            self._on_scroll_range_changed
        )

    def _on_scroll_range_changed(self, min_val: int, max_val: int):
        if max_val == 0:
            sizes = self._splitter.sizes()
            if sizes and self._table_index < len(sizes):
                self._locked_w = sizes[self._table_index]
        else:
            self._locked_w = None

    def _on_moved(self, pos: int, index: int):
        if self._locked_w is None:
            return
        sizes = self._splitter.sizes()
        if not sizes or self._table_index >= len(sizes):
            return
        current_w = sizes[self._table_index]
        if current_w > self._locked_w:
            new_sizes = list(sizes)
            diff = current_w - self._locked_w
            new_sizes[self._table_index] = self._locked_w
            other = 1 - self._table_index
            if other < len(new_sizes):
                new_sizes[other] += diff
            self._splitter.blockSignals(True)
            self._splitter.setSizes(new_sizes)
            self._splitter.blockSignals(False)

    def _check_scroll(self):
        sb = self._table.horizontalScrollBar()
        self._on_scroll_range_changed(sb.minimum(), sb.maximum())

    def refresh(self):
        self._timer.start()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Resize, QEvent.Show):
            self._timer.start()
        return super().eventFilter(obj, event)


# aliases
_SplitterScrollGuard = SplitterScrollGuard