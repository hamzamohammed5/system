"""
ui/widgets/tables/tables.py
============================
دمج builders.py + items.py — أدوات بناء الجداول الموحدة.

الملفات المحذوفة: builders.py, items.py
يبقى منفرداً: flexible.py (منطق مختلف — delegates + tree)
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QSplitter, QWidget,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont, QBrush

from ui.theme import _C
from ..styles import (
    table_style, splitter_style,
    ROW_HEIGHT_NORMAL, ROW_HEIGHT_COMPACT, ROW_HEIGHT_LARGE,
)


# ══════════════════════════════════════════════════════════
# أدوات خلايا الجداول  (كان في items.py)
# ══════════════════════════════════════════════════════════

def make_item(text: str = "", user_data=None,
              align: int = None, tooltip: str = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text) if text is not None else "")
    if user_data is not None:
        item.setData(Qt.UserRole, user_data)
    if align is not None:
        item.setTextAlignment(align | Qt.AlignVCenter)
    if tooltip:
        item.setToolTip(tooltip)
    return item


def bold_item(text: str, color: str = None, align: int = None,
              user_data=None, tooltip: str = None) -> QTableWidgetItem:
    item = make_item(text, user_data, align, tooltip)
    f = QFont()
    f.setBold(True)
    item.setFont(f)
    if color:
        item.setForeground(QBrush(QColor(color)))
    return item


def colored_item(text: str, color: str, align: int = None,
                 user_data=None, tooltip: str = None) -> QTableWidgetItem:
    item = make_item(text, user_data, align, tooltip)
    item.setForeground(QBrush(QColor(color)))
    return item


def center_item(text: str, color: str = None, bold: bool = False,
                user_data=None) -> QTableWidgetItem:
    item = make_item(text, user_data, Qt.AlignCenter)
    if color:
        item.setForeground(QBrush(QColor(color)))
    if bold:
        f = QFont()
        f.setBold(True)
        item.setFont(f)
    return item


def muted_item(text: str) -> QTableWidgetItem:
    return colored_item(text, _C['text_muted'])


def insert_row(table: QTableWidget, height: int = ROW_HEIGHT_NORMAL) -> int:
    r = table.rowCount()
    table.insertRow(r)
    table.setRowHeight(r, height)
    return r


def set_row_bg(table: QTableWidget, row: int, color: str):
    brush = QBrush(QColor(color))
    for c in range(table.columnCount()):
        item = table.item(row, c)
        if item:
            item.setBackground(brush)
        else:
            new = QTableWidgetItem("")
            new.setBackground(brush)
            table.setItem(row, c, new)


def apply_row_height(table: QTableWidget, height: int = ROW_HEIGHT_NORMAL):
    for r in range(table.rowCount()):
        table.setRowHeight(r, height)


def calc_width(table: QTableWidget, extra_pad: int = 4) -> int:
    total = extra_pad
    for col in range(table.columnCount()):
        total += table.columnWidth(col)
    vh = table.verticalHeader()
    if not vh.isHidden():
        total += vh.width()
    return total


def auto_fit_columns(table: QTableWidget, fixed_cols: list = None,
                     stretch_col: int = -1,
                     min_width: int = 40, max_width: int = 300):
    hh   = table.horizontalHeader()
    n    = table.columnCount()
    cols = fixed_cols if fixed_cols is not None else list(range(n))
    for col in cols:
        if col == stretch_col:
            continue
        hh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        ideal = max(min_width, min(table.columnWidth(col), max_width))
        hh.setSectionResizeMode(col, QHeaderView.Interactive)
        table.setColumnWidth(col, ideal)
    if 0 <= stretch_col < n:
        hh.setSectionResizeMode(stretch_col, QHeaderView.Stretch)


def apply_tooltips(table: QTableWidget, cols: list = None):
    n_cols      = table.columnCount()
    target_cols = cols if cols is not None else list(range(n_cols))
    for r in range(table.rowCount()):
        for c in target_cols:
            item = table.item(r, c)
            if item and item.text() and not item.toolTip():
                item.setToolTip(item.text())


# ══════════════════════════════════════════════════════════
# دوال بناء الجداول  (كان في builders.py)
# ══════════════════════════════════════════════════════════

def _build_table(columns: list, stretch_col: int = -1,
                 col_widths: dict = None, variant: str = "normal",
                 max_height: int = None, min_height: int = None,
                 alternating: bool = True, row_height: int = None) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setAlternatingRowColors(alternating)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(False)
    table.setStyleSheet(table_style(variant))

    hh = table.horizontalHeader()
    vh = table.verticalHeader()
    hh.setSectionsMovable(False)
    hh.setSectionsClickable(True)
    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
    hh.setHighlightSections(False)
    hh.setMinimumSectionSize(30)

    _row_h = row_height or (
        ROW_HEIGHT_COMPACT if variant == "compact"
        else ROW_HEIGHT_LARGE if variant == "large"
        else ROW_HEIGHT_NORMAL
    )
    vh.setDefaultSectionSize(_row_h)
    vh.setMinimumSectionSize(_row_h - 4)
    vh.setSectionResizeMode(QHeaderView.Fixed)

    if col_widths:
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
                table.setColumnWidth(i, col_widths.get(i, 100))
    else:
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
                table.setColumnWidth(i, 100)
        if stretch_col < 0:
            hh.setStretchLastSection(True)

    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    if max_height:
        table.setMaximumHeight(max_height)
    if min_height:
        table.setMinimumHeight(min_height)

    return table


def make_table(columns: list, stretch_col: int = -1,
               col_widths: dict = None, max_height: int = None,
               min_height: int = 100,
               row_height: int = ROW_HEIGHT_NORMAL) -> QTableWidget:
    return _build_table(columns, stretch_col, col_widths,
                        max_height=max_height, min_height=min_height,
                        row_height=row_height)


def make_compact_table(columns: list, stretch_col: int = -1,
                       col_widths: dict = None,
                       max_height: int = 200) -> QTableWidget:
    return _build_table(columns, stretch_col, col_widths,
                        variant="compact", max_height=max_height,
                        row_height=ROW_HEIGHT_COMPACT)


def make_list_table(columns: list, stretch_col: int = -1,
                    col_widths: dict = None) -> QTableWidget:
    table = _build_table(columns, stretch_col, col_widths,
                         row_height=ROW_HEIGHT_LARGE)
    table.setStyleSheet(table.styleSheet() + """
        QTableWidget { border:none; border-radius:0; }
    """)
    return table


def make_fixed_table(columns: list, col_widths: dict,
                     max_height: int = None, min_height: int = 60,
                     row_height: int = ROW_HEIGHT_NORMAL) -> QTableWidget:
    table = _build_table(columns, stretch_col=-1, col_widths=col_widths,
                         max_height=max_height, min_height=min_height,
                         row_height=row_height)
    hh = table.horizontalHeader()
    for i in range(len(columns)):
        hh.setSectionResizeMode(i, QHeaderView.Fixed)
        if i in col_widths:
            table.setColumnWidth(i, col_widths[i])
    hh.setStretchLastSection(False)
    total_w = sum(col_widths.get(i, 80) for i in range(len(columns))) + 4
    table.setFixedWidth(total_w)
    table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    return table


def make_splitter_table(columns: list, stretch_col: int = -1,
                        col_widths: dict = None, max_height: int = None,
                        min_height: int = 60, row_height: int = None,
                        variant: str = "normal",
                        extra_pad: int = 20) -> tuple:
    table = _build_table(columns, stretch_col, col_widths,
                         variant=variant, max_height=max_height,
                         min_height=min_height, row_height=row_height)
    table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    spacer = QWidget()
    spacer.setStyleSheet("background:transparent;")
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(6)
    splitter.setStyleSheet(splitter_style())
    splitter.addWidget(table)
    splitter.addWidget(spacer)
    splitter.setCollapsible(0, False)
    splitter.setCollapsible(1, True)
    splitter.setSizes([calc_width(table, extra_pad), 9999])

    return splitter, table


def make_splitter_table_guarded(columns: list, stretch_col: int = -1,
                                col_widths: dict = None, max_height: int = None,
                                min_height: int = 60, row_height: int = None,
                                variant: str = "normal",
                                extra_pad: int = 20) -> tuple:
    from ..utils.splitter import SplitterScrollGuard

    splitter, table = make_splitter_table(
        columns=columns, stretch_col=stretch_col, col_widths=col_widths,
        max_height=max_height, min_height=min_height, row_height=row_height,
        variant=variant, extra_pad=extra_pad,
    )
    guard = SplitterScrollGuard(splitter, table, table_index=0, extra_pad=extra_pad)
    return splitter, table, guard


def fit_splitter_table(splitter: QSplitter, table: QTableWidget,
                       extra_pad: int = 20, delay_ms: int = 0):
    """يضبط عرض الـ splitter حسب عرض الجدول — المصدر الوحيد."""
    def _fit():
        table_w   = calc_width(table, extra_pad)
        total     = splitter.width()
        remaining = max(0, total - table_w)
        splitter.setSizes([table_w, remaining])

    if delay_ms > 0:
        QTimer.singleShot(delay_ms, _fit)
    else:
        _fit()