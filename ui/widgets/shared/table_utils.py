"""
ui/widgets/shared/table_utils.py
================================
أدوات موحدة لإنشاء وإدارة الجداول في كل أقسام التطبيق.
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy, QSplitter, QWidget,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings import _C, get_font_size, fs


ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_LARGE   = 48


def _table_stylesheet(variant: str = "normal") -> str:
    base = get_font_size()
    c    = _C

    if variant == "compact":
        item_padding = "4px 6px"
        header_pad   = "4px 6px"
        font_size    = fs(base, -1)
    elif variant == "large":
        item_padding = "8px 12px"
        header_pad   = "8px 12px"
        font_size    = fs(base, 0)
    else:
        item_padding = "5px 10px"
        header_pad   = "6px 10px"
        font_size    = fs(base, 0)

    return f"""
        QTableWidget {{
            font-size: {font_size}pt;
            color: {c['text_primary']};
            background: {c['bg_input']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            gridline-color: {c['border']};
            alternate-background-color: {c['bg_surface']};
            outline: none;
        }}
        QTableWidget::item {{
            padding: {item_padding};
            border: none;
            border-bottom: 1px solid {c['border']};
        }}
        QTableWidget::item:selected {{
            background: {c['accent_light']};
            color: {c['accent_text']};
        }}
        QTableWidget::item:hover {{
            background: {c['bg_hover']};
        }}
        QHeaderView::section {{
            font-size: {fs(base,-1)}pt;
            font-weight: 600;
            color: {c['text_muted']};
            background: {c['bg_surface_2']};
            border: none;
            border-bottom: 2px solid {c['border_med']};
            border-right: 1px solid {c['border']};
            padding: {header_pad};
            letter-spacing: 0.2px;
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
        QHeaderView::section:hover {{
            background: {c['bg_hover']};
            color: {c['text_primary']};
        }}
    """


def _splitter_stylesheet() -> str:
    return f"""
        QSplitter::handle {{
            background: {_C['border_med']};
            border-radius: 3px;
        }}
        QSplitter::handle:hover {{
            background: {_C['accent_mid']};
        }}
        QSplitter::handle:pressed {{
            background: {_C['accent']};
        }}
    """


def _build_table(columns: list,
                 stretch_col: int = -1,
                 col_widths: dict = None,
                 variant: str = "normal",
                 max_height: int = None,
                 min_height: int = None,
                 alternating: bool = True,
                 row_height: int = None,
                 fixed_width: bool = False) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setAlternatingRowColors(alternating)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(False)
    table.setStyleSheet(_table_stylesheet(variant))

    hh = table.horizontalHeader()
    vh = table.verticalHeader()

    hh.setSectionsMovable(False)
    hh.setSectionsClickable(True)

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

    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
    hh.setHighlightSections(False)
    hh.setMinimumSectionSize(30)

    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    if max_height:
        table.setMaximumHeight(max_height)
    if min_height:
        table.setMinimumHeight(min_height)

    return table


# ══════════════════════════════════════════════════════════

def make_detail_table(columns: list,
                      stretch_col: int = -1,
                      col_widths: dict = None,
                      max_height: int = None,
                      min_height: int = 100,
                      row_height: int = ROW_HEIGHT_NORMAL) -> QTableWidget:
    return _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        max_height=max_height, min_height=min_height,
        row_height=row_height
    )


def make_compact_table(columns: list,
                       stretch_col: int = -1,
                       col_widths: dict = None,
                       max_height: int = 200) -> QTableWidget:
    return _build_table(
        columns, stretch_col, col_widths,
        variant="compact",
        max_height=max_height,
        row_height=ROW_HEIGHT_COMPACT
    )


def make_list_table(columns: list,
                    stretch_col: int = -1,
                    col_widths: dict = None) -> QTableWidget:
    table = _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        row_height=ROW_HEIGHT_LARGE
    )
    table.setStyleSheet(table.styleSheet() + """
        QTableWidget { border: none; border-radius: 0; }
    """)
    return table


def make_fixed_table(columns: list,
                     col_widths: dict,
                     max_height: int = None,
                     min_height: int = 60,
                     row_height: int = ROW_HEIGHT_NORMAL) -> QTableWidget:
    table = _build_table(
        columns, stretch_col=-1, col_widths=col_widths,
        variant="normal",
        max_height=max_height, min_height=min_height,
        row_height=row_height
    )
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


# ══════════════════════════════════════════════════════════
# make_splitter_table ★
# ══════════════════════════════════════════════════════════

def make_splitter_table(columns: list,
                        stretch_col: int = -1,
                        col_widths: dict = None,
                        max_height: int = None,
                        min_height: int = 60,
                        row_height: int = None,
                        variant: str = "normal",
                        extra_pad: int = 20) -> tuple:
    """
    يبني جدول جوا QSplitter أفقي — نفس pattern الـ dashboard.
    - الجدول على اليسار بعرضه الطبيعي
    - spacer على اليمين يأخذ المساحة الزيادة
    - المستخدم يقدر يوسّع/يضيّق بالـ handle

    Returns: (QSplitter, QTableWidget)
    بعد ملء البيانات استدعِ: fit_splitter_table(splitter, table)
    """
    table = _build_table(
        columns, stretch_col, col_widths,
        variant=variant,
        max_height=max_height,
        min_height=min_height,
        row_height=row_height,
    )
    table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    spacer = QWidget()
    spacer.setStyleSheet("background: transparent;")
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(6)
    splitter.setStyleSheet(_splitter_stylesheet())
    splitter.addWidget(table)
    splitter.addWidget(spacer)
    splitter.setCollapsible(0, False)
    splitter.setCollapsible(1, True)

    table_w = calc_table_width(table, extra_pad)
    splitter.setSizes([table_w, 9999])

    return splitter, table


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


# ══════════════════════════════════════════════════════════
# أدوات الخلايا
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
