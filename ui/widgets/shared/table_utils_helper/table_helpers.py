"""
ui/widgets/shared/table_utils/table_helpers.py
================================================
دوال مساعدة لخلايا الجداول وعمليات القياس.

لا تُستورد مباشرة — يُستورد من table_utils.py.
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont, QBrush

from ui.app_settings import _C
from .table_styles import ROW_HEIGHT_NORMAL


# ══════════════════════════════════════════════════════════
# قياس عرض الجدول
# ══════════════════════════════════════════════════════════

def calc_table_width(table: QTableWidget, extra_pad: int = 4) -> int:
    total = extra_pad
    for col in range(table.columnCount()):
        total += table.columnWidth(col)
    vh = table.verticalHeader()
    if not vh.isHidden():
        total += vh.width()
    return total


def fit_table_width(table: QTableWidget,
                    min_w: int = 0,
                    max_w: int = 99999,
                    extra_pad: int = 4):
    hh = table.horizontalHeader()
    hh.resizeSections(QHeaderView.ResizeToContents)
    for i in range(table.columnCount()):
        if hh.sectionResizeMode(i) != QHeaderView.Stretch:
            w = table.columnWidth(i)
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            table.setColumnWidth(i, w)
    total_w = calc_table_width(table, extra_pad)
    total_w = max(min_w, min(total_w, max_w))
    table.setMinimumWidth(total_w)


def fit_splitter_table(splitter: QSplitter, table: QTableWidget,
                       extra_pad: int = 20, delay_ms: int = 0):
    """يعيد ضبط عرض الجدول في الـ splitter بعد ملء البيانات."""
    def _fit():
        table_w   = calc_table_width(table, extra_pad)
        total     = splitter.width()
        remaining = max(0, total - table_w)
        splitter.setSizes([table_w, remaining])

    if delay_ms > 0:
        QTimer.singleShot(delay_ms, _fit)
    else:
        _fit()


def fit_splitter_to_table(splitter,
                           list_index: int,
                           table: QTableWidget,
                           min_w: int = 280,
                           max_w: int = 560,
                           extra_pad: int = 4):
    sizes = splitter.sizes()
    if not sizes or len(sizes) <= list_index:
        return

    ideal  = calc_table_width(table, extra_pad)
    target = max(min_w, min(ideal, max_w))
    total  = sum(sizes)
    if total <= 0:
        return

    new_sizes             = list(sizes)
    new_sizes[list_index] = target
    remaining             = total - target
    other_total           = sum(s for i, s in enumerate(sizes) if i != list_index)

    for i in range(len(sizes)):
        if i != list_index:
            ratio        = sizes[i] / other_total if other_total > 0 else 1.0
            new_sizes[i] = max(300, int(remaining * ratio))

    splitter.setSizes(new_sizes)


# ══════════════════════════════════════════════════════════
# أدوات الخلايا — الأصلية
# ══════════════════════════════════════════════════════════

def make_table_item(text: str = "",
                    user_data=None,
                    align: int = None,
                    tooltip: str = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text) if text is not None else "")
    if user_data is not None:
        item.setData(Qt.UserRole, user_data)
    if align is not None:
        item.setTextAlignment(align | Qt.AlignVCenter)
    if tooltip:
        item.setToolTip(tooltip)
    return item


def color_item(item: QTableWidgetItem, color: str) -> QTableWidgetItem:
    item.setForeground(QColor(color))
    return item


def bold_item(item: QTableWidgetItem,
              also_medium: bool = False) -> QTableWidgetItem:
    f = QFont()
    if also_medium:
        f.setWeight(QFont.Medium)
    else:
        f.setBold(True)
    item.setFont(f)
    return item


def muted_item(item: QTableWidgetItem) -> QTableWidgetItem:
    return color_item(item, _C['text_muted'])


def apply_row_height(table: QTableWidget, height: int = ROW_HEIGHT_NORMAL):
    for r in range(table.rowCount()):
        table.setRowHeight(r, height)


def insert_row(table: QTableWidget,
               height: int = ROW_HEIGHT_NORMAL) -> int:
    r = table.rowCount()
    table.insertRow(r)
    table.setRowHeight(r, height)
    return r


def auto_fit_columns(table: QTableWidget,
                     fixed_cols: list = None,
                     stretch_col: int = -1,
                     min_width: int = 40,
                     max_width: int = 300):
    hh   = table.horizontalHeader()
    n    = table.columnCount()
    cols = fixed_cols if fixed_cols is not None else list(range(n))

    for col in cols:
        if col == stretch_col:
            continue
        hh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        ideal = table.columnWidth(col)
        ideal = max(min_width, min(ideal, max_width))
        hh.setSectionResizeMode(col, QHeaderView.Interactive)
        table.setColumnWidth(col, ideal)

    if 0 <= stretch_col < n:
        hh.setSectionResizeMode(stretch_col, QHeaderView.Stretch)


# ══════════════════════════════════════════════════════════
# أدوات الخلايا المحسّنة
# ══════════════════════════════════════════════════════════

def bold_table_item(text: str,
                    color: str = None,
                    align: int = None,
                    user_data=None,
                    tooltip: str = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text) if text is not None else "")
    f = QFont()
    f.setBold(True)
    item.setFont(f)
    if color:
        item.setForeground(QBrush(QColor(color)))
    if align is not None:
        item.setTextAlignment(align | Qt.AlignVCenter)
    if user_data is not None:
        item.setData(Qt.UserRole, user_data)
    if tooltip:
        item.setToolTip(tooltip)
    return item


def colored_table_item(text: str,
                       color: str,
                       align: int = None,
                       user_data=None,
                       tooltip: str = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text) if text is not None else "")
    item.setForeground(QBrush(QColor(color)))
    if align is not None:
        item.setTextAlignment(align | Qt.AlignVCenter)
    if user_data is not None:
        item.setData(Qt.UserRole, user_data)
    if tooltip:
        item.setToolTip(tooltip)
    return item


def center_table_item(text: str,
                      color: str = None,
                      bold: bool = False,
                      user_data=None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text) if text is not None else "")
    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    if color:
        item.setForeground(QBrush(QColor(color)))
    if bold:
        f = QFont()
        f.setBold(True)
        item.setFont(f)
    if user_data is not None:
        item.setData(Qt.UserRole, user_data)
    return item


def set_row_background(table: QTableWidget, row: int, color: str):
    brush = QBrush(QColor(color))
    for c in range(table.columnCount()):
        item = table.item(row, c)
        if item:
            item.setBackground(brush)
        else:
            new_item = QTableWidgetItem("")
            new_item.setBackground(brush)
            table.setItem(row, c, new_item)