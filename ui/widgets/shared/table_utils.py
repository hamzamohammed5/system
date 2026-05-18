"""
ui/widgets/shared/table_utils.py
================================
أدوات موحدة لإنشاء وإدارة الجداول في كل أقسام التطبيق.

القاعدة:
  - الأعمدة Interactive — المستخدم يقدر يحرك عرضها بحرية
  - stretch_col هو العمود الوحيد اللي بيتمدد تلقائياً
  - الـ splitter يتحرك بحرية بين MIN_W و MAX_W

الدوال:
  make_detail_table   — جدول تفاصيل موحد (بنود، سجل، ...)
  make_compact_table  — جدول صغير للـ sidebars والبطاقات
  make_list_table     — جدول قائمة رئيسية (يسار الـ splitter)
  make_fixed_table    — جدول بعرض ثابت بالكامل (للـ dashboards)
  make_table_item     — إنشاء خلية مع بيانات مخفية وتوسيط اختياري
  color_item          — تلوين خلية
  bold_item           — تغليظ خلية
  muted_item          — تلوين خلية بلون خافت
  insert_row          — إضافة صف بارتفاع موحد
  auto_fit_columns    — ضبط عرض الأعمدة تلقائياً (Interactive)
  calc_table_width    — حساب العرض الكلي المثالي للجدول
  fit_splitter_to_table — ضبط عرض الـ splitter على الجدول
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings import _C, get_font_size, fs


# ══════════════════════════════════════════════════════════
# ثوابت الارتفاع الموحد
# ══════════════════════════════════════════════════════════

ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_LARGE   = 48


# ══════════════════════════════════════════════════════════
# stylesheet الجداول الموحد
# ══════════════════════════════════════════════════════════

def _table_stylesheet(variant: str = "normal") -> str:
    base   = get_font_size()
    c      = _C

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
        QHeaderView::section {{
            cursor: col-resize;
        }}
    """


# ══════════════════════════════════════════════════════════
# دالة بناء الجدول الأساسية
# ══════════════════════════════════════════════════════════

def _build_table(columns: list,
                 stretch_col: int = -1,
                 col_widths: dict = None,
                 variant: str = "normal",
                 max_height: int = None,
                 min_height: int = None,
                 alternating: bool = True,
                 row_height: int = None,
                 fixed_width: bool = False) -> QTableWidget:
    """دالة بناء داخلية مشتركة."""
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

    # ✅ تفعيل تحريك الأعمدة بالماوس
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

    # ── عرض الأعمدة ──
    # ✅ Interactive بدل Fixed/ResizeToContents — المستخدم يقدر يحرك العرض
    if col_widths:
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
                w = col_widths.get(i, 100)
                table.setColumnWidth(i, w)
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

    # ✅ scroll أفقي مرئي لما الأعمدة تكبر عن الجدول
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    if max_height:
        table.setMaximumHeight(max_height)
    if min_height:
        table.setMinimumHeight(min_height)

    return table


# ══════════════════════════════════════════════════════════
# make_detail_table — جدول تفاصيل داخل الصفحات
# ══════════════════════════════════════════════════════════

def make_detail_table(columns: list,
                      stretch_col: int = -1,
                      col_widths: dict = None,
                      max_height: int = None,
                      min_height: int = 100,
                      row_height: int = ROW_HEIGHT_NORMAL) -> QTableWidget:
    """
    جدول تفاصيل موحد — للاستخدام داخل صفحات التفاصيل.
    الأعمدة Interactive — المستخدم يقدر يحرك عرضها.
    stretch_col يتمدد ليملأ الباقي.
    """
    return _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        max_height=max_height, min_height=min_height,
        row_height=row_height
    )


# ══════════════════════════════════════════════════════════
# make_compact_table — جدول صغير
# ══════════════════════════════════════════════════════════

def make_compact_table(columns: list,
                       stretch_col: int = -1,
                       col_widths: dict = None,
                       max_height: int = 200) -> QTableWidget:
    """جدول صغير للـ sidebars والبطاقات والـ dialogs."""
    return _build_table(
        columns, stretch_col, col_widths,
        variant="compact",
        max_height=max_height,
        row_height=ROW_HEIGHT_COMPACT
    )


# ══════════════════════════════════════════════════════════
# make_list_table — جدول قائمة رئيسية
# ══════════════════════════════════════════════════════════

def make_list_table(columns: list,
                    stretch_col: int = -1,
                    col_widths: dict = None) -> QTableWidget:
    """
    جدول قائمة رئيسية (يسار الـ splitter).
    ✅ الأعمدة Interactive — المستخدم يقدر يحرك عرضها.
    ✅ الـ splitter يتحرك بحرية.
    """
    table = _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        row_height=ROW_HEIGHT_LARGE
    )
    table.setStyleSheet(table.styleSheet() + """
        QTableWidget {
            border: none;
            border-radius: 0;
        }
    """)
    return table


# ══════════════════════════════════════════════════════════
# make_fixed_table — جدول بعرض ثابت بالكامل (للـ dashboards)
# ══════════════════════════════════════════════════════════

def make_fixed_table(columns: list,
                     col_widths: dict,
                     max_height: int = None,
                     min_height: int = 60,
                     row_height: int = ROW_HEIGHT_NORMAL) -> QTableWidget:
    """
    جدول بعرض ثابت بالكامل — للـ dashboards والتقارير.

    ✅ كل الأعمدة Fixed — لا يوجد stretch
    ✅ عرض الجدول = مجموع عرض الأعمدة + 4 بالضبط
    ✅ لا يتمدد مع النافذة أبداً
    """
    table = _build_table(
        columns, stretch_col=-1, col_widths=col_widths,
        variant="normal",
        max_height=max_height, min_height=min_height,
        row_height=row_height
    )

    # ✅ كل الأعمدة Fixed للـ dashboards فقط
    hh = table.horizontalHeader()
    for i in range(len(columns)):
        hh.setSectionResizeMode(i, QHeaderView.Fixed)
        if i in col_widths:
            table.setColumnWidth(i, col_widths[i])
    hh.setStretchLastSection(False)

    # ✅ عرض الجدول ثابت = مجموع الأعمدة + 4
    total_w = sum(col_widths.get(i, 80) for i in range(len(columns))) + 4
    table.setFixedWidth(total_w)
    table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

    return table


# ══════════════════════════════════════════════════════════
# أدوات الخلايا
# ══════════════════════════════════════════════════════════

def make_table_item(text: str = "",
                    user_data=None,
                    align: int = None,
                    tooltip: str = None) -> QTableWidgetItem:
    """إنشاء خلية جدول مع بيانات مخفية وتوسيط اختياري."""
    item = QTableWidgetItem(str(text) if text is not None else "")
    if user_data is not None:
        item.setData(Qt.UserRole, user_data)
    if align is not None:
        item.setTextAlignment(align | Qt.AlignVCenter)
    if tooltip:
        item.setToolTip(tooltip)
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


# ══════════════════════════════════════════════════════════
# auto_fit_columns — يضبط عرض الأعمدة تلقائياً على المحتوى
# ══════════════════════════════════════════════════════════

def auto_fit_columns(table: QTableWidget,
                     fixed_cols: list = None,
                     stretch_col: int = -1,
                     min_width: int = 40,
                     max_width: int = 300):
    """
    يضبط عرض الأعمدة تلقائياً حسب المحتوى.
    ✅ Interactive بعد الضبط — المستخدم يقدر يحرك العرض يدوياً.

    fixed_cols  : الأعمدة اللي هتتضبط عرضها (None = كل الأعمدة)
    stretch_col : العمود اللي يتمدد ليملأ المساحة الزيادة
    min_width   : الحد الأدنى لعرض أي عمود
    max_width   : الحد الأقصى لعرض أي عمود
    """
    hh = table.horizontalHeader()
    n  = table.columnCount()

    cols = fixed_cols if fixed_cols is not None else list(range(n))

    for col in cols:
        if col == stretch_col:
            continue
        # احسب العرض المثالي من المحتوى
        hh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        ideal = table.columnWidth(col)
        ideal = max(min_width, min(ideal, max_width))
        # ✅ Interactive بدل Fixed — المستخدم يقدر يحرك العرض بعدين
        hh.setSectionResizeMode(col, QHeaderView.Interactive)
        table.setColumnWidth(col, ideal)

    if 0 <= stretch_col < n:
        hh.setSectionResizeMode(stretch_col, QHeaderView.Stretch)


# ══════════════════════════════════════════════════════════
# calc_table_width — يحسب العرض الكلي المثالي للجدول
# ══════════════════════════════════════════════════════════

def calc_table_width(table: QTableWidget, extra_pad: int = 4) -> int:
    """
    يحسب العرض الكلي المثالي للجدول بناءً على عرض الأعمدة.

    extra_pad : padding إضافي (borders + scrollbar احتمالي)
    """
    total = extra_pad
    for col in range(table.columnCount()):
        total += table.columnWidth(col)
    vh = table.verticalHeader()
    if not vh.isHidden():
        total += vh.width()
    return total


# ══════════════════════════════════════════════════════════
# fit_table_width — يضبط عرض الجدول بالظبط على المحتوى
# ══════════════════════════════════════════════════════════

def fit_table_width(table: QTableWidget,
                    min_w: int = 0,
                    max_w: int = 99999,
                    extra_pad: int = 4):
    """
    يضبط عرض الجدول بالظبط على قد المحتوى.
    ✅ يستخدم setMinimumWidth بدل setFixedWidth عشان الـ splitter يقدر يتحرك.
    """
    hh = table.horizontalHeader()
    hh.resizeSections(QHeaderView.ResizeToContents)
    # بعد الحساب نرجع Interactive
    for i in range(table.columnCount()):
        if hh.sectionResizeMode(i) != QHeaderView.Stretch:
            w = table.columnWidth(i)
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            table.setColumnWidth(i, w)
    total_w = calc_table_width(table, extra_pad)
    total_w = max(min_w, min(total_w, max_w))
    table.setMinimumWidth(total_w)


# ══════════════════════════════════════════════════════════
# fit_splitter_to_table — يضبط عرض الـ splitter على الجدول
# ══════════════════════════════════════════════════════════

def fit_splitter_to_table(splitter,
                           list_index: int,
                           table: QTableWidget,
                           min_w: int = 280,
                           max_w: int = 560,
                           extra_pad: int = 4):
    """
    يضبط عرض الـ panel في الـ splitter بحيث يناسب عرض الجدول.
    ✅ بدون horizontal scroll في panel القائمة.
    """
    sizes = splitter.sizes()
    if not sizes or len(sizes) <= list_index:
        return

    ideal  = calc_table_width(table, extra_pad)
    target = max(min_w, min(ideal, max_w))
    total  = sum(sizes)

    if total <= 0:
        return

    new_sizes       = list(sizes)
    new_sizes[list_index] = target

    remaining = total - target
    other_total = sum(s for i, s in enumerate(sizes) if i != list_index)
    for i in range(len(sizes)):
        if i != list_index:
            ratio = sizes[i] / other_total if other_total > 0 else 1.0
            new_sizes[i] = max(300, int(remaining * ratio))

    splitter.setSizes(new_sizes)