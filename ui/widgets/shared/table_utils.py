"""
ui/widgets/shared/table_utils.py
================================
أدوات موحدة لإنشاء وإدارة الجداول في كل أقسام التطبيق.

الدوال:
  make_orders_table   — جدول طلبات موحد
  make_detail_table   — جدول تفاصيل موحد (بنود، سجل، ...)
  make_compact_table  — جدول صغير للـ sidebars والبطاقات
  apply_row_height    — تعيين ارتفاع موحد للصفوف
  set_item_center     — توسيط محتوى خلية
  color_item          — تلوين خلية
  bold_item           — تغليظ خلية
  make_table_item     — إنشاء خلية مع بيانات مخفية وتوسيط اختياري
  auto_fit_columns    — ضبط عرض الأعمدة تلقائياً حسب المحتوى (NEW)

الاستخدام:
    from ui.widgets.shared.table_utils import (
        make_detail_table, make_table_item, color_item, bold_item,
        auto_fit_columns,
    )

    table = make_detail_table(["البند", "الكمية", "السعر"], stretch_col=0)
    item = make_table_item("محصول أ", user_data=42)
    bold_item(item)
    table.setItem(0, 0, item)

    # بعد ملء البيانات:
    auto_fit_columns(table, fixed_cols=[0, 2, 4])
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings import _C, get_font_size, fs


# ══════════════════════════════════════════════════════════
# ثابت الارتفاع الموحد
# ══════════════════════════════════════════════════════════

ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_LARGE   = 48


# ══════════════════════════════════════════════════════════
# stylesheet الجداول الموحد
# ══════════════════════════════════════════════════════════

def _table_stylesheet(variant: str = "normal") -> str:
    """يبني stylesheet الجدول حسب الـ variant."""
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
        QHeaderView::section:pressed {{
            background: {c['bg_active']};
        }}
    """


# ══════════════════════════════════════════════════════════
# دالة بناء الجدول الأساسية
# ══════════════════════════════════════════════════════════

def _build_table(columns: list[str],
                 stretch_col: int = -1,
                 col_widths: dict = None,
                 variant: str = "normal",
                 max_height: int = None,
                 min_height: int = None,
                 alternating: bool = True,
                 row_height: int = None,
                 resizable: bool = True) -> QTableWidget:
    """
    دالة بناء داخلية مشتركة.

    resizable: لو True، كل الأعمدة (غير الـ Stretch وغير الـ Fixed)
               تكون Interactive → المستخدم يسحبها بالماوس.
    """
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

    # السماح بسحب فواصل الأعمدة
    if resizable:
        hh.setSectionsMovable(False)       # لا نسمح بإعادة ترتيب الأعمدة
        hh.setSectionResizeMode(QHeaderView.Interactive)  # baseline

    # ارتفاع الصف الافتراضي
    _row_h = row_height or (
        ROW_HEIGHT_COMPACT if variant == "compact"
        else ROW_HEIGHT_LARGE if variant == "large"
        else ROW_HEIGHT_NORMAL
    )
    vh.setDefaultSectionSize(_row_h)
    vh.setMinimumSectionSize(_row_h - 4)
    vh.setSectionResizeMode(QHeaderView.Fixed)

    # عرض الأعمدة
    if col_widths:
        for i in range(len(columns)):
            if i in col_widths:
                hh.setSectionResizeMode(i, QHeaderView.Fixed)
                table.setColumnWidth(i, col_widths[i])
            elif i == stretch_col or (stretch_col < 0 and i == len(columns) - 1):
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                # Interactive → قابل للسحب
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
    hh.setMinimumSectionSize(40)

    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    if max_height:
        table.setMaximumHeight(max_height)
    if min_height:
        table.setMinimumHeight(min_height)

    return table


# ══════════════════════════════════════════════════════════
# auto_fit_columns — الدالة الجديدة
# ══════════════════════════════════════════════════════════

def auto_fit_columns(table: QTableWidget,
                     fixed_cols: list[int] = None,
                     stretch_col: int = -1,
                     min_width: int = 50,
                     max_width: int = 400):
    """
    يضبط عرض الأعمدة تلقائياً حسب المحتوى (auto-fit)،
    ثم يجعلها Interactive بحيث المستخدم يقدر يسحبها.

    المعاملات:
        fixed_cols  : أرقام الأعمدة اللي تتعمل auto-fit (None = كلهم)
        stretch_col : العمود اللي يفضل Stretch (مش بيتعمله auto-fit)
        min_width   : الحد الأدنى لعرض أي عمود بعد auto-fit
        max_width   : الحد الأقصى لعرض أي عمود بعد auto-fit

    الاستخدام:
        # بعد ملء الجدول بالبيانات:
        auto_fit_columns(self.table, fixed_cols=[0, 2, 3, 4])
        # العمود 1 (العميل) هيفضل Stretch لأنه مش في fixed_cols
    """
    hh = table.horizontalHeader()
    n  = table.columnCount()

    cols_to_fit = fixed_cols if fixed_cols is not None else list(range(n))

    for col in range(n):
        if col == stretch_col:
            hh.setSectionResizeMode(col, QHeaderView.Stretch)
            continue

        if col in cols_to_fit:
            # احسب أوسع خلية في هذا العمود (هيدر + بيانات)
            table.resizeColumnToContents(col)
            current_w = table.columnWidth(col)
            # طبّق الحدود
            clamped = max(min_width, min(current_w, max_width))
            table.setColumnWidth(col, clamped)
            # Interactive → المستخدم يقدر يسحب بعد الـ auto-fit
            hh.setSectionResizeMode(col, QHeaderView.Interactive)
        else:
            # أعمدة مش في القائمة → Interactive بدون auto-fit
            hh.setSectionResizeMode(col, QHeaderView.Interactive)


def auto_fit_all(table: QTableWidget,
                 stretch_col: int = -1,
                 min_width: int = 50,
                 max_width: int = 400):
    """
    اختصار — auto-fit لكل الأعمدة ما عدا الـ stretch.
    """
    n = table.columnCount()
    all_cols = [i for i in range(n) if i != stretch_col]
    auto_fit_columns(table, fixed_cols=all_cols,
                     stretch_col=stretch_col,
                     min_width=min_width, max_width=max_width)


# ══════════════════════════════════════════════════════════
# make_detail_table — جدول تفاصيل داخل الصفحات
# ══════════════════════════════════════════════════════════

def make_detail_table(columns: list[str],
                      stretch_col: int = -1,
                      col_widths: dict = None,
                      max_height: int = None,
                      min_height: int = 100,
                      row_height: int = ROW_HEIGHT_NORMAL,
                      resizable: bool = True) -> QTableWidget:
    """
    جدول تفاصيل موحد — للاستخدام داخل صفحات التفاصيل.

    columns     : أسماء الأعمدة
    stretch_col : العمود اللي يتمدد أفقياً (-1 = الأخير)
    col_widths  : {col_index: width_px} للأعمدة ذات العرض الثابت
    max_height  : الحد الأقصى للارتفاع (None = بلا حد)
    min_height  : الحد الأدنى للارتفاع
    resizable   : السماح بسحب عرض الأعمدة (افتراضي True)
    """
    return _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        max_height=max_height, min_height=min_height,
        row_height=row_height, resizable=resizable,
    )


# ══════════════════════════════════════════════════════════
# make_compact_table — جدول صغير
# ══════════════════════════════════════════════════════════

def make_compact_table(columns: list[str],
                       stretch_col: int = -1,
                       col_widths: dict = None,
                       max_height: int = 200,
                       resizable: bool = True) -> QTableWidget:
    """جدول صغير للـ sidebars والبطاقات والـ dialogs."""
    return _build_table(
        columns, stretch_col, col_widths,
        variant="compact",
        max_height=max_height,
        row_height=ROW_HEIGHT_COMPACT,
        resizable=resizable,
    )


# ══════════════════════════════════════════════════════════
# make_list_table — جدول قائمة رئيسية
# ══════════════════════════════════════════════════════════

def make_list_table(columns: list[str],
                    stretch_col: int = -1,
                    col_widths: dict = None,
                    resizable: bool = True) -> QTableWidget:
    """جدول قائمة رئيسية (يسار الـ splitter)."""
    table = _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        row_height=ROW_HEIGHT_LARGE,
        resizable=resizable,
    )
    table.setStyleSheet(table.styleSheet() + """
        QTableWidget {
            border: none;
            border-radius: 0;
        }
    """)
    return table


# ══════════════════════════════════════════════════════════
# أدوات الخلايا
# ══════════════════════════════════════════════════════════

def make_table_item(text: str = "",
                    user_data=None,
                    align: int = None,
                    tooltip: str = None) -> QTableWidgetItem:
    """
    إنشاء خلية جدول مع بيانات مخفية وتوسيط اختياري.

    align: Qt.AlignCenter | Qt.AlignRight | Qt.AlignLeft | None (الافتراضي)
    """
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