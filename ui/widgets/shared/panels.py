"""
ui/widgets/shared/table_utils.py
================================
أدوات موحدة لإنشاء وإدارة الجداول في كل أقسام التطبيق.
نسخة محسّنة — تصميم متسق ومهني.

الدوال:
  make_list_table    — جدول قائمة رئيسية (يسار الـ splitter)
  make_detail_table  — جدول تفاصيل داخل الصفحات
  make_compact_table — جدول صغير للـ sidebars والبطاقات
  apply_row_height   — تعيين ارتفاع موحد للصفوف
  make_table_item    — إنشاء خلية مع بيانات مخفية
  color_item         — تلوين خلية
  bold_item          — تغليظ خلية
  muted_item         — تلوين خلية بلون خافت
  insert_row         — إضافة صف بارتفاع موحد
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings import _C, get_font_size, fs


# ══════════════════════════════════════════════════════════
# ثوابت الارتفاع
# ══════════════════════════════════════════════════════════

ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_LARGE   = 48


# ══════════════════════════════════════════════════════════
# stylesheet الجداول الموحد
# ══════════════════════════════════════════════════════════

def _table_stylesheet(variant: str = "normal") -> str:
    base = get_font_size()
    c    = _C

    if variant == "compact":
        item_pad   = "3px 8px"
        header_pad = "4px 8px"
        font_sz    = fs(base, -1)
        radius     = "6px"
    elif variant == "large":
        item_pad   = "8px 14px"
        header_pad = "8px 14px"
        font_sz    = fs(base, 0)
        radius     = "8px"
    elif variant == "list":
        item_pad   = "6px 12px"
        header_pad = "6px 12px"
        font_sz    = fs(base, 0)
        radius     = "0px"
    else:
        item_pad   = "5px 12px"
        header_pad = "6px 12px"
        font_sz    = fs(base, 0)
        radius     = "8px"

    return f"""
        QTableWidget {{
            font-size: {font_sz}pt;
            color: {c['text_primary']};
            background: {c['bg_input']};
            border: 1px solid {c['border']};
            border-radius: {radius};
            gridline-color: {c['border']};
            alternate-background-color: {c['bg_surface']};
            outline: none;
            selection-background-color: {c['accent_light']};
        }}
        QTableWidget::item {{
            padding: {item_pad};
            border: none;
            border-bottom: 1px solid {c['border']};
        }}
        QTableWidget::item:selected {{
            background: {c['accent_light']};
            color: {c['accent_text']};
        }}
        QTableWidget::item:hover:!selected {{
            background: {c['bg_hover']};
        }}
        QHeaderView {{
            background: {c['bg_surface_2']};
            border: none;
        }}
        QHeaderView::section {{
            font-size: {fs(base,-1)}pt;
            font-weight: 600;
            color: {c['text_muted']};
            background: {c['bg_surface_2']};
            border: none;
            border-bottom: 2px solid {c['border_med']};
            border-left: 1px solid {c['border']};
            padding: {header_pad};
            letter-spacing: 0.2px;
        }}
        QHeaderView::section:first {{
            border-left: none;
        }}
        QHeaderView::section:last {{
            border-left: 1px solid {c['border']};
        }}
        QHeaderView::section:hover {{
            background: {c['bg_hover']};
            color: {c['text_primary']};
        }}
    """


# ══════════════════════════════════════════════════════════
# دالة بناء الجدول الأساسية
# ══════════════════════════════════════════════════════════

def _build_table(
    columns: list,
    stretch_col: int = -1,
    col_widths: dict = None,
    variant: str = "normal",
    max_height: int = None,
    min_height: int = None,
    alternating: bool = True,
    row_height: int = None,
) -> QTableWidget:

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

    _row_h = row_height or {
        "compact": ROW_HEIGHT_COMPACT,
        "large":   ROW_HEIGHT_LARGE,
        "list":    ROW_HEIGHT_LARGE,
    }.get(variant, ROW_HEIGHT_NORMAL)

    vh.setDefaultSectionSize(_row_h)
    vh.setMinimumSectionSize(_row_h - 6)
    vh.setSectionResizeMode(QHeaderView.Fixed)

    if col_widths:
        for i in range(len(columns)):
            if i in col_widths:
                hh.setSectionResizeMode(i, QHeaderView.Fixed)
                table.setColumnWidth(i, col_widths[i])
            elif i == stretch_col or (stretch_col < 0 and i == len(columns) - 1):
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
    else:
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
        if stretch_col < 0:
            hh.setStretchLastSection(True)

    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
    hh.setHighlightSections(False)
    hh.setMinimumSectionSize(36)

    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    if max_height:
        table.setMaximumHeight(max_height)
    if min_height:
        table.setMinimumHeight(min_height)

    return table


# ══════════════════════════════════════════════════════════
# make_list_table — جدول قائمة رئيسية (يسار الـ splitter)
# ══════════════════════════════════════════════════════════

def make_list_table(
    columns: list,
    stretch_col: int = -1,
    col_widths: dict = None,
) -> QTableWidget:
    """
    جدول القائمة الرئيسية — بدون حدود خارجية، خلفية نظيفة.
    يُستخدم في الجانب الأيسر من الـ splitter.
    """
    table = _build_table(
        columns, stretch_col, col_widths,
        variant="list",
        row_height=ROW_HEIGHT_LARGE,
    )
    # إزالة الحدود الخارجية — يندمج مع الـ panel
    table.setStyleSheet(table.styleSheet() + """
        QTableWidget {
            border: none;
            border-radius: 0px;
        }
    """)
    return table


# ══════════════════════════════════════════════════════════
# make_detail_table — جدول تفاصيل داخل الصفحات
# ══════════════════════════════════════════════════════════

def make_detail_table(
    columns: list,
    stretch_col: int = -1,
    col_widths: dict = None,
    max_height: int = None,
    min_height: int = 80,
    row_height: int = ROW_HEIGHT_NORMAL,
) -> QTableWidget:
    """جدول تفاصيل موحد للاستخدام داخل صفحات التفاصيل."""
    return _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        max_height=max_height,
        min_height=min_height,
        row_height=row_height,
    )


# ══════════════════════════════════════════════════════════
# make_compact_table — جدول صغير
# ══════════════════════════════════════════════════════════

def make_compact_table(
    columns: list,
    stretch_col: int = -1,
    col_widths: dict = None,
    max_height: int = 200,
) -> QTableWidget:
    """جدول صغير للـ sidebars والبطاقات والـ dialogs."""
    return _build_table(
        columns, stretch_col, col_widths,
        variant="compact",
        max_height=max_height,
        row_height=ROW_HEIGHT_COMPACT,
    )


# ══════════════════════════════════════════════════════════
# أدوات الخلايا
# ══════════════════════════════════════════════════════════

def make_table_item(
    text: str = "",
    user_data=None,
    align: int = None,
    tooltip: str = None,
) -> QTableWidgetItem:
    """إنشاء خلية جدول مع بيانات مخفية واختياريات."""
    item = QTableWidgetItem(str(text) if text is not None else "")
    if user_data is not None:
        item.setData(Qt.UserRole, user_data)
    if align is not None:
        item.setTextAlignment(align | Qt.AlignVCenter)
    else:
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    if tooltip:
        item.setToolTip(str(tooltip))
    elif text:
        item.setToolTip(str(text))
    return item


def color_item(item: QTableWidgetItem, color: str) -> QTableWidgetItem:
    """يطبق لون النص على الخلية ويرجعها."""
    item.setForeground(QColor(color))
    return item


def bold_item(item: QTableWidgetItem,
              also_medium: bool = False) -> QTableWidgetItem:
    """يجعل نص الخلية bold ويرجعها."""
    f = QFont()
    if also_medium:
        f.setWeight(QFont.Medium)
    else:
        f.setBold(True)
    item.setFont(f)
    return item


def muted_item(item: QTableWidgetItem) -> QTableWidgetItem:
    """يطبق لون النص الخافت على الخلية."""
    return color_item(item, _C['text_muted'])


def apply_row_height(table: QTableWidget, height: int = ROW_HEIGHT_NORMAL):
    """يعيّن ارتفاع موحد لكل صفوف الجدول."""
    for r in range(table.rowCount()):
        table.setRowHeight(r, height)


def insert_row(table: QTableWidget,
               height: int = ROW_HEIGHT_NORMAL) -> int:
    """يضيف صف ويرجع رقمه."""
    r = table.rowCount()
    table.insertRow(r)
    table.setRowHeight(r, height)
    return r