"""
ui/widgets/shared/splitter_scroll_guard.py
==========================================
_SplitterScrollGuard — يربط الـ splitter الداخلي للجدول (جدول + spacer)
بالـ horizontal scrollbar.

الفكرة:
  - لو الجدول بيتشاف كامل (scrollbar.maximum() == 0)
    → الـ splitter handle مش بيتوسع أكتر من العرض الحالي للجدول.
  - لو المستخدم ضيّق الـ splitter وظهر scroll تاني
    → الـ handle بيتحرك عادي.

الاستخدام (بعد make_splitter_table):
    splitter, table = make_splitter_table(...)
    guard = _SplitterScrollGuard(splitter, table, table_index=0)
    self._guard = guard   # لازم تحتفظ بيه عشان GC

أو استخدم make_splitter_table_guarded() مباشرة:
    splitter, table, guard = make_splitter_table_guarded(...)
    self._guard = guard
"""

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QSplitter, QTableWidget


class _SplitterScrollGuard(QObject):
    """
    يراقب الـ horizontal scrollbar للجدول ويمنع الـ splitter
    من التوسع أكتر من اللازم لما الجدول بيتشاف كامل.

    المعاملات:
        splitter    : QSplitter (الداخلي — جدول + spacer)
        table       : QTableWidget المراقَب
        table_index : index الـ table جوا الـ splitter (عادةً 0)
        extra_pad   : مسافة إضافية للعرض (بكسل)
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
        from PyQt5.QtCore import QEvent
        if event.type() in (QEvent.Resize, QEvent.Show):
            self._timer.start()
        return False
