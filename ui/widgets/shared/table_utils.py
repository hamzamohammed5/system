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
  auto_fit_columns    — ضبط عرض الأعمدة تلقائياً حسب المحتوى
  fit_table_width     — حساب العرض المثالي للجدول (مجموع عرض الأعمدة + هيدر)
  fit_splitter_to_table — ضبط الـ splitter على عرض الجدول المثالي (مشترك)

الاستخدام:
    from ui.widgets.shared.table_utils import (
        make_detail_table, make_table_item, color_item, bold_item,
        auto_fit_columns, fit_splitter_to_table,
    )

    table = make_detail_table(["البند", "الكمية", "السعر"], stretch_col=0)

    # بعد ملء البيانات:
    auto_fit_columns(table, fixed_cols=[0, 2, 4])

    # في الـ splitter:
    fit_splitter_to_table(splitter, index=0, table=table, min_w=280, max_w=700)
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSplitter,
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

# هامش إضافي للـ splitter عند حساب العرض المثالي
_SPLITTER_PADDING = 18   # scrollbar reserve + حواف


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

    if resizable:
        hh.setSectionsMovable(False)
        hh.setSectionResizeMode(QHeaderView.Interactive)

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
    hh.setMinimumSectionSize(40)

    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    if max_height:
        table.setMaximumHeight(max_height)
    if min_height:
        table.setMinimumHeight(min_height)

    return table


# ══════════════════════════════════════════════════════════
# auto_fit_columns — ضبط الأعمدة على المحتوى
# ══════════════════════════════════════════════════════════

def auto_fit_columns(table: QTableWidget,
                     fixed_cols: list[int] = None,
                     stretch_col: int = -1,
                     min_width: int = 50,
                     max_width: int = 400):
    """
    يضبط عرض الأعمدة تلقائياً حسب المحتوى (auto-fit)،
    ثم يجعلها Interactive.

    المعاملات:
        fixed_cols  : أرقام الأعمدة للـ auto-fit (None = كلهم)
        stretch_col : العمود اللي يفضل Stretch
        min_width   : الحد الأدنى لعرض أي عمود
        max_width   : الحد الأقصى لعرض أي عمود
    """
    hh = table.horizontalHeader()
    n  = table.columnCount()

    cols_to_fit = fixed_cols if fixed_cols is not None else list(range(n))

    for col in range(n):
        if col == stretch_col:
            hh.setSectionResizeMode(col, QHeaderView.Stretch)
            continue

        if col in cols_to_fit:
            table.resizeColumnToContents(col)
            current_w = table.columnWidth(col)
            clamped = max(min_width, min(current_w, max_width))
            table.setColumnWidth(col, clamped)
            hh.setSectionResizeMode(col, QHeaderView.Interactive)
        else:
            hh.setSectionResizeMode(col, QHeaderView.Interactive)


def auto_fit_all(table: QTableWidget,
                 stretch_col: int = -1,
                 min_width: int = 50,
                 max_width: int = 400):
    """اختصار — auto-fit لكل الأعمدة ما عدا الـ stretch."""
    n = table.columnCount()
    all_cols = [i for i in range(n) if i != stretch_col]
    auto_fit_columns(table, fixed_cols=all_cols,
                     stretch_col=stretch_col,
                     min_width=min_width, max_width=max_width)


# ══════════════════════════════════════════════════════════
# fit_table_width — حساب العرض المثالي للجدول
# ══════════════════════════════════════════════════════════

def fit_table_width(table: QTableWidget,
                    extra_padding: int = _SPLITTER_PADDING) -> int:
    """
    يحسب العرض المثالي للجدول بناءً على مجموع عرض الأعمدة الفعلية.

    يُستخدم لضبط الـ splitter أو setFixedWidth تلقائياً بعد ملء البيانات.

    المعاملات:
        table         : الجدول المراد قياسه
        extra_padding : هامش إضافي (scrollbar + حواف) — افتراضي 18px

    يرجع:
        العرض الإجمالي بالـ pixels
    """
    hh    = table.horizontalHeader()
    total = extra_padding

    for col in range(table.columnCount()):
        # لو Stretch نأخذ العرض الفعلي (بعد الـ layout)
        total += table.columnWidth(col)

    # نضيف عرض الـ vertical header لو ظاهر
    vh = table.verticalHeader()
    if not vh.isHidden():
        total += vh.width()

    return total


# ══════════════════════════════════════════════════════════
# fit_splitter_to_table — ضبط الـ splitter على محتوى الجدول (مشترك)
# ══════════════════════════════════════════════════════════

def fit_splitter_to_table(splitter: QSplitter,
                          index: int,
                          table: QTableWidget,
                          min_w: int = 200,
                          max_w: int = 800,
                          extra_padding: int = _SPLITTER_PADDING):
    """
    يضبط حجم panel في الـ splitter بحيث يتناسب مع عرض الجدول بالضبط.

    يُستدعى بعد auto_fit_columns() وبعد ملء البيانات.

    المعاملات:
        splitter      : الـ QSplitter
        index         : رقم الـ panel (0 = أول panel)
        table         : الجدول المراد التناسب معه
        min_w         : الحد الأدنى لعرض الـ panel
        max_w         : الحد الأقصى
        extra_padding : هامش إضافي (toolbar + borders)

    الاستخدام:
        # بعد ملء الجدول:
        auto_fit_all(self.table)
        fit_splitter_to_table(self._splitter, 0, self.table, min_w=280)
    """
    ideal = fit_table_width(table, extra_padding=extra_padding)

    # نضيف ارتفاع الـ toolbar/filter فوق الجدول
    panel = splitter.widget(index)
    if panel:
        panel_h  = panel.sizeHint().height()
        table_h  = table.sizeHint().height()
        overhead = max(0, panel_h - table_h)   # toolbar + status bar
        _ = overhead  # not needed for width

    target = max(min_w, min(ideal, max_w))

    sizes = splitter.sizes()
    if not sizes:
        return

    total = sum(sizes)
    if total <= 0:
        return

    other_total = total - sizes[index]
    new_sizes   = list(sizes)
    new_sizes[index] = target
    # توزّع الباقي على الـ panels الأخرى بنفس النسب
    remaining = total - target
    if len(sizes) > 1 and other_total > 0:
        for i, sz in enumerate(sizes):
            if i != index:
                new_sizes[i] = max(100, int(sz / other_total * remaining))
    # تأكد المجموع = total
    diff = total - sum(new_sizes)
    if diff != 0:
        last_other = next(i for i in range(len(sizes)) if i != index)
        new_sizes[last_other] = max(100, new_sizes[last_other] + diff)

    splitter.setSizes(new_sizes)


# ══════════════════════════════════════════════════════════
# make_detail_table
# ══════════════════════════════════════════════════════════

def make_detail_table(columns: list[str],
                      stretch_col: int = -1,
                      col_widths: dict = None,
                      max_height: int = None,
                      min_height: int = 100,
                      row_height: int = ROW_HEIGHT_NORMAL,
                      resizable: bool = True) -> QTableWidget:
    return _build_table(
        columns, stretch_col, col_widths,
        variant="normal",
        max_height=max_height, min_height=min_height,
        row_height=row_height, resizable=resizable,
    )


# ══════════════════════════════════════════════════════════
# make_compact_table
# ══════════════════════════════════════════════════════════

def make_compact_table(columns: list[str],
                       stretch_col: int = -1,
                       col_widths: dict = None,
                       max_height: int = 200,
                       resizable: bool = True) -> QTableWidget:
    return _build_table(
        columns, stretch_col, col_widths,
        variant="compact",
        max_height=max_height,
        row_height=ROW_HEIGHT_COMPACT,
        resizable=resizable,
    )


# ══════════════════════════════════════════════════════════
# make_list_table
# ══════════════════════════════════════════════════════════

def make_list_table(columns: list[str],
                    stretch_col: int = -1,
                    col_widths: dict = None,
                    resizable: bool = True) -> QTableWidget:
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