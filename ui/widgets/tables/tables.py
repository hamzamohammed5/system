"""
ui/widgets/tables/tables.py
============================
دمج builders.py + items.py — أدوات بناء الجداول الموحدة.

[إصلاح 3.2] from ..styles import ROW_HEIGHT_*
         → from ..theme.table_styles import ROW_HEIGHT_*
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QSplitter, QWidget,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont, QBrush

from ui.theme import _C
from ui.constants import (
    COL_MIN_WIDTH, COL_MAX_WIDTH,
    TABLE_MIN_SECTION_SIZE, TABLE_MIN_HEIGHT_DEFAULT,
    TABLE_COMPACT_MAX_HEIGHT, TABLE_SPLITTER_MIN_HEIGHT,
    TABLE_SPLITTER_EXTRA_PAD, TABLE_SPLITTER_HANDLE_W,
    CALC_WIDTH_EXTRA_PAD, TABLE_COL_DEFAULT_W,
    TABLE_FIXED_COL_DEFAULT_W, TABLE_FIXED_WIDTH_PAD,
    TABLE_ROW_MIN_SECTION_PAD,
)
from ..theme.table_styles import (       # [إصلاح 3.2]
    table_style, splitter_style,
    ROW_HEIGHT_NORMAL, ROW_HEIGHT_COMPACT, ROW_HEIGHT_LARGE,
)


# ══════════════════════════════════════════════════════════
# أدوات خلايا الجداول
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


def muted_item(text: str, align: int = None, user_data=None,
              tooltip: str = None) -> QTableWidgetItem:
    return colored_item(text, _C['text_muted'], align=align,
                        user_data=user_data, tooltip=tooltip)


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


def calc_width(table: QTableWidget, extra_pad: int = CALC_WIDTH_EXTRA_PAD) -> int:
    total = extra_pad
    for col in range(table.columnCount()):
        total += table.columnWidth(col)
    vh = table.verticalHeader()
    if not vh.isHidden():
        total += vh.width()
    return total


def auto_fit_columns(table: QTableWidget, fixed_cols: list = None,
                     stretch_col: int = -1,
                     min_width: int = COL_MIN_WIDTH, max_width: int = COL_MAX_WIDTH):
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
# دوال بناء الجداول
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
    table.setProperty("_table_variant", variant)

    hh = table.horizontalHeader()
    vh = table.verticalHeader()
    hh.setSectionsMovable(False)
    hh.setSectionsClickable(True)
    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
    hh.setHighlightSections(False)
    hh.setMinimumSectionSize(TABLE_MIN_SECTION_SIZE)

    _row_h = row_height or (
        ROW_HEIGHT_COMPACT if variant == "compact"
        else ROW_HEIGHT_LARGE if variant == "large"
        else ROW_HEIGHT_NORMAL
    )
    vh.setDefaultSectionSize(_row_h)
    vh.setMinimumSectionSize(_row_h - TABLE_ROW_MIN_SECTION_PAD)
    vh.setSectionResizeMode(QHeaderView.Fixed)

    if col_widths:
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
                table.setColumnWidth(i, col_widths.get(i, TABLE_COL_DEFAULT_W))
    else:
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
                table.setColumnWidth(i, TABLE_COL_DEFAULT_W)
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
               min_height: int = TABLE_MIN_HEIGHT_DEFAULT,
               row_height: int = ROW_HEIGHT_NORMAL) -> QTableWidget:
    return _build_table(columns, stretch_col, col_widths,
                        max_height=max_height, min_height=min_height,
                        row_height=row_height)


def make_compact_table(columns: list, stretch_col: int = -1,
                       col_widths: dict = None,
                       max_height: int = TABLE_COMPACT_MAX_HEIGHT) -> QTableWidget:
    return _build_table(columns, stretch_col, col_widths,
                        variant="compact", max_height=max_height,
                        row_height=ROW_HEIGHT_COMPACT)


def make_list_table(columns: list, stretch_col: int = -1,
                    col_widths: dict = None) -> QTableWidget:
    table = _build_table(columns, stretch_col, col_widths,
                         row_height=ROW_HEIGHT_LARGE)
    table.setProperty("_table_extra_qss", "QTableWidget { border:none; border-radius:0; }")
    table.setStyleSheet(table.styleSheet() + table.property("_table_extra_qss"))
    return table


def make_fixed_table(columns: list, col_widths: dict,
                     max_height: int = None, min_height: int = TABLE_SPLITTER_MIN_HEIGHT,
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
    total_w = sum(col_widths.get(i, TABLE_FIXED_COL_DEFAULT_W) for i in range(len(columns))) + TABLE_FIXED_WIDTH_PAD
    table.setFixedWidth(total_w)
    table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    return table


def make_splitter_table(columns: list, stretch_col: int = -1,
                        col_widths: dict = None, max_height: int = None,
                        min_height: int = TABLE_SPLITTER_MIN_HEIGHT, row_height: int = None,
                        variant: str = "normal",
                        extra_pad: int = TABLE_SPLITTER_EXTRA_PAD) -> tuple:
    table = _build_table(columns, stretch_col, col_widths,
                         variant=variant, max_height=max_height,
                         min_height=min_height, row_height=row_height)
    table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    spacer = QWidget()
    spacer.setStyleSheet("background:transparent;")
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(TABLE_SPLITTER_HANDLE_W)
    splitter.setStyleSheet(splitter_style())
    splitter.addWidget(table)
    splitter.addWidget(spacer)
    splitter.setCollapsible(0, False)
    splitter.setCollapsible(1, True)
    splitter.setSizes([calc_width(table, extra_pad), 9999])

    return splitter, table


def make_splitter_table_guarded(columns: list, stretch_col: int = -1,
                                col_widths: dict = None, max_height: int = None,
                                min_height: int = TABLE_SPLITTER_MIN_HEIGHT, row_height: int = None,
                                variant: str = "normal",
                                extra_pad: int = TABLE_SPLITTER_EXTRA_PAD) -> tuple:
    from ..utils.splitter import SplitterScrollGuard

    splitter, table = make_splitter_table(
        columns=columns, stretch_col=stretch_col, col_widths=col_widths,
        max_height=max_height, min_height=min_height, row_height=row_height,
        variant=variant, extra_pad=extra_pad,
    )
    guard = SplitterScrollGuard(splitter, table, table_index=0, extra_pad=extra_pad)
    return splitter, table, guard


def fit_splitter_table(splitter: QSplitter, table: QTableWidget,
                       extra_pad: int = TABLE_SPLITTER_EXTRA_PAD, delay_ms: int = 0):
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


# ══════════════════════════════════════════════════════════
# [Fix - dark theme tables] إعادة تطبيق ستايل الجداول عند تغيير الثيم
# ══════════════════════════════════════════════════════════
#
# المشكلة: _build_table() كانت بتطبق table_style(variant) مرة واحدة بس
# وقت الإنشاء. أي widget بيبني جدول عبر make_table/make_list_table/
# make_fixed_table/make_splitter_table وميعملش setStyleSheet(table_style())
# بنفسه داخل _refresh_style() الخاصة بيه، كان الجدول بيفضل بستايل الثيم
# اللي كان موجود وقت الإنشاء (غالبًا فاتح) حتى بعد التحويل لـ dark.
# هذا بالظبط سبب الجداول الفاتحة في income_statement_tab, _investors_table،
# وأي جدول تاني مبني بنفس الطريقة من غير override يدوي لـ _refresh_style.
#
# الحل: نفس نمط refresh_visible_buttons() في button.py — بنحفظ الـ variant
# (وأي QSS إضافي زي في make_list_table) كـ Qt property وقت البناء،
# وبنوفر دالة عامة تدور على كل QTableWidget في شجرة الـ widgets وتعيد
# تطبيق الستايل الصحيح للثيم الحالي.

def refresh_table_styles(root_widget) -> int:
    """
    يُعيد تطبيق table_style() على كل QTableWidget في شجرة الـ widget
    اللي اتبنت عبر make_table/make_list_table/make_fixed_table/
    make_splitter_table (أي جدول عليه property "_table_variant").

    يُستدعى من _refresh_style() الخاصة بأي widget أب بدل ما كل widget
    يكتب self.table.setStyleSheet(table_style()) يدويًا.

    مثال:
        def _refresh_style(self, *_):
            from ui.widgets.tables.tables import refresh_table_styles
            refresh_table_styles(self)
    """
    count = 0
    try:
        for tbl in root_widget.findChildren(QTableWidget):
            variant = tbl.property("_table_variant")
            if variant is None:
                continue
            try:
                ss = table_style(variant)
                extra = tbl.property("_table_extra_qss")
                if extra:
                    ss += extra
                tbl.setStyleSheet(ss)
                count += 1
            except RuntimeError:
                pass
    except RuntimeError:
        pass
    return count