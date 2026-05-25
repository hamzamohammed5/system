"""
ui/widgets/shared/splitter_utils.py
=====================================
SmartSplitter — أدوات مساعدة للـ splitter.

[إصلاح v3]:
  - SmartSplitter._apply_style تستخدم get_splitter_style() مستوردة في أعلى الملف
    بدل lazy import داخل الدالة
  - fit_list_panel_delayed موحّدة في branch واحد
"""

from PyQt5.QtWidgets import QSplitter, QTableWidget, QWidget, QSizePolicy
from PyQt5.QtCore    import Qt, QTimer

from ui.widgets.shared.panles_helper.theme import get_splitter_style


_MIN_LIST_W  = 280
_MAX_LIST_W  = 620
_TOOLBAR_PAD = 24
_SCROLLBAR_W = 18


def _calc_table_ideal_width(table: QTableWidget,
                             extra_pad: int = _TOOLBAR_PAD) -> int:
    total = _SCROLLBAR_W + extra_pad
    for col in range(table.columnCount()):
        total += table.columnWidth(col)
    vh = table.verticalHeader()
    if not vh.isHidden():
        total += vh.width()
    return total


def fit_list_panel(splitter: QSplitter,
                   list_index: int,
                   table: QTableWidget,
                   min_w: int = _MIN_LIST_W,
                   max_w: int = _MAX_LIST_W,
                   extra_pad: int = _TOOLBAR_PAD) -> int:
    sizes = splitter.sizes()
    if not sizes or len(sizes) <= list_index:
        return min_w

    total = sum(sizes)
    if total <= 0:
        return min_w

    ideal  = _calc_table_ideal_width(table, extra_pad)
    target = max(min_w, min(ideal, max_w))

    remaining  = total - target
    old_list_w = sizes[list_index]
    old_other  = total - old_list_w

    new_sizes = list(sizes)
    new_sizes[list_index] = target

    if len(sizes) > 1 and old_other > 0:
        for i, sz in enumerate(sizes):
            if i != list_index:
                ratio = sz / old_other if old_other > 0 else 1.0
                new_sizes[i] = max(200, int(remaining * ratio))

    diff = total - sum(new_sizes)
    if diff != 0:
        detail_idx = 1 if list_index == 0 else 0
        if detail_idx < len(new_sizes):
            new_sizes[detail_idx] = max(200, new_sizes[detail_idx] + diff)

    splitter.setSizes(new_sizes)
    return target


def fit_list_panel_delayed(splitter: QSplitter,
                            list_index: int,
                            table: QTableWidget,
                            delay_ms: int = 0,
                            min_w: int = _MIN_LIST_W,
                            max_w: int = _MAX_LIST_W):
    """
    يضبط عرض لوحة القائمة بعد delay اختياري.
    delay_ms=0 يعمل synchronously عبر QTimer.singleShot(0, ...).
    """
    QTimer.singleShot(
        delay_ms,
        lambda: fit_list_panel(splitter, list_index, table, min_w, max_w)
    )


class SmartSplitter(QSplitter):
    """
    QSplitter مساعد — محتفظ به للتوافق مع الكود القديم.
    """

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._list_index  = 0
        self._table       = None
        self._min_w       = _MIN_LIST_W
        self._max_w       = _MAX_LIST_W
        self._list_widget = None

        self.setHandleWidth(4)
        self.setStyleSheet(get_splitter_style())   # ← مباشرة، لا lazy import

    def set_list_widget(self, widget: QWidget,
                        list_table: QTableWidget,
                        list_index: int = 0,
                        min_w: int = _MIN_LIST_W,
                        max_w: int = _MAX_LIST_W):
        self._list_index  = list_index
        self._table       = list_table
        self._min_w       = min_w
        self._max_w       = max_w
        self._list_widget = widget

        detail_idx = 1 if list_index == 0 else 0
        detail_widget = self.widget(detail_idx)
        if detail_widget:
            detail_widget.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )

    def fit_now(self) -> int:
        if self._table is None:
            return self._min_w
        return fit_list_panel(
            self, self._list_index, self._table,
            self._min_w, self._max_w
        )

    def fit_delayed(self, delay_ms: int = 50):
        if self._table is None:
            return
        fit_list_panel_delayed(
            self, self._list_index, self._table,
            delay_ms, self._min_w, self._max_w
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)