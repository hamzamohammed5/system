"""
ui/widgets/tables/items.py
===========================
أدوات خلايا الجداول الموحدة.
"""
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor, QFont, QBrush

from ui.app_settings import _C
from ..theme.styles import ROW_HEIGHT_NORMAL


# ── بناء خلايا ────────────────────────────────────────────

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


# ── عمليات على الصفوف ──────────────────────────────────────

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


# ── قياس وضبط أعمدة ───────────────────────────────────────

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


# ── Tooltip helpers ────────────────────────────────────────

def apply_tooltips(table: QTableWidget, cols: list = None):
    n_cols      = table.columnCount()
    target_cols = cols if cols is not None else list(range(n_cols))
    for r in range(table.rowCount()):
        for c in target_cols:
            item = table.item(r, c)
            if item and item.text() and not item.toolTip():
                item.setToolTip(item.text())


# ── Aliases للتوافق مع الكود القديم ───────────────────────
make_table_item    = make_item
bold_table_item    = bold_item
colored_table_item = colored_item
center_table_item  = center_item
set_row_background = set_row_bg
color_item         = lambda item, color: (item.setForeground(QColor(color)), item)[1]