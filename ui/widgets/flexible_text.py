"""
ui/widgets/flexible_text.py
============================
أدوات عرض النصوص بشكل flexible في الجداول والشجر.

المشكلة: النصوص الطويلة بتتقطع في الجداول والشجر بدون إمكانية قراءتها.
الحل:
  1. WrapDelegate       — delegate بيعمل word-wrap تلقائي في خلايا الجدول
  2. AutoTooltipDelegate — tooltip تلقائي بالنص الكامل عند hover
  3. set_flexible_columns — بيطبّق word-wrap على أعمدة محددة
  4. FlexibleTreeWidget  — QTreeWidget بـ word-wrap وتوسيع تلقائي للصفوف
  5. make_flexible_table  — بديل لـ make_table بـ word-wrap كامل
"""

from PyQt5.QtWidgets import (
    QStyledItemDelegate, QStyle, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui  import QFontMetrics, QPainter, QTextOption


# ══════════════════════════════════════════════════════════
# WrapDelegate — عرض النص بـ word-wrap
# ══════════════════════════════════════════════════════════

class WrapDelegate(QStyledItemDelegate):
    """
    Delegate بيعمل word-wrap تلقائي في خلايا الجدول.
    يُستخدم مع setItemDelegateForColumn أو setItemDelegate.
    """
    def __init__(self, parent=None, min_row_height: int = 28, padding: int = 6):
        super().__init__(parent)
        self._min_row_height = min_row_height
        self._padding        = padding

    def paint(self, painter: QPainter, option, index):
        painter.save()

        # خلفية التحديد
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        # النص
        text = index.data(Qt.DisplayRole)
        if text is None:
            text = ""
        text = str(text)

        rect = option.rect.adjusted(self._padding, 2, -self._padding, -2)

        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WordWrap)
        text_option.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # لون النص
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            fg = index.data(Qt.ForegroundRole)
            if fg:
                try:
                    painter.setPen(fg.color() if hasattr(fg, 'color') else fg)
                except Exception:
                    painter.setPen(option.palette.text().color())
            else:
                painter.setPen(option.palette.text().color())

        painter.setFont(option.font)
        painter.drawText(QRect(rect), Qt.AlignRight | Qt.AlignVCenter | Qt.TextWordWrap, text)
        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(Qt.DisplayRole)
        if text is None:
            text = ""
        text = str(text)

        # حساب الارتفاع المطلوب
        fm   = QFontMetrics(option.font)
        col_width = option.rect.width() if option.rect.isValid() else 150
        text_width = col_width - self._padding * 2

        if text_width <= 0:
            text_width = 150

        # كم سطر لازم؟
        text_rect = fm.boundingRect(
            0, 0, text_width, 9999,
            Qt.AlignRight | Qt.AlignTop | Qt.TextWordWrap,
            text
        )
        height = max(self._min_row_height, text_rect.height() + 8)
        return QSize(col_width, height)


# ══════════════════════════════════════════════════════════
# AutoTooltipDelegate — tooltip تلقائي
# ══════════════════════════════════════════════════════════

class AutoTooltipDelegate(QStyledItemDelegate):
    """
    Delegate بيضيف tooltip تلقائي بالنص الكامل.
    يُستخدم مع الأعمدة اللي مش محتاجة word-wrap.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # نضيف tooltip بالنص الكامل دايمًا
        text = index.data(Qt.DisplayRole)
        if text:
            option.text = str(text)


# ══════════════════════════════════════════════════════════
# دوال مساعدة للتطبيق على الجداول
# ══════════════════════════════════════════════════════════

def set_flexible_columns(table: QTableWidget,
                         wrap_cols: list[int] = None,
                         min_row_height: int = 32):
    """
    بيطبق word-wrap على أعمدة محددة في الجدول.

    wrap_cols: قائمة أرقام الأعمدة اللي محتاج wrap، أو None لكلهم.
    """
    table.setWordWrap(True)
    table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.setTextElideMode(Qt.ElideRight)  # نهاية النص تُقطع بـ ...

    delegate = WrapDelegate(table, min_row_height=min_row_height)

    if wrap_cols is None:
        table.setItemDelegate(delegate)
    else:
        for col in wrap_cols:
            table.setItemDelegateForColumn(col, delegate)

    # tooltip تلقائي للأعمدة الباقية
    if wrap_cols is not None:
        all_cols = set(range(table.columnCount()))
        other_cols = all_cols - set(wrap_cols)
        tip_delegate = AutoTooltipDelegate(table)
        for col in other_cols:
            table.setItemDelegateForColumn(col, tip_delegate)


def apply_tooltip_to_all(table: QTableWidget):
    """
    يضيف tooltip تلقائي لكل خلية في الجدول.
    يُستدعى بعد ملء الجدول بالبيانات.
    """
    for r in range(table.rowCount()):
        for c in range(table.columnCount()):
            item = table.item(r, c)
            if item and item.text():
                item.setToolTip(item.text())


# ══════════════════════════════════════════════════════════
# make_flexible_table — بديل make_table مع word-wrap
# ══════════════════════════════════════════════════════════

def make_flexible_table(columns: list[str],
                        stretch_col: int = -1,
                        wrap_cols: list[int] = None,
                        min_row_height: int = 32) -> QTableWidget:
    """
    إنشاء جدول مع:
      - word-wrap في الأعمدة المحددة
      - tooltip تلقائي لكل الأعمدة
      - ارتفاع الصف يتمدد تلقائيًا حسب المحتوى
      - scroll أفقي ورأسي

    wrap_cols: أعمدة بتعمل wrap، None = كلهم
    stretch_col: العمود اللي يتمدد أفقيًا
    """
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setWordWrap(True)

    hh = table.horizontalHeader()
    vh = table.verticalHeader()

    # ارتفاع الصف يتمدد تلقائيًا
    vh.setSectionResizeMode(QHeaderView.ResizeToContents)
    vh.setDefaultSectionSize(min_row_height)
    vh.setMinimumSectionSize(min_row_height)

    if stretch_col >= 0:
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
    else:
        for i in range(len(columns)):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
        hh.setStretchLastSection(True)

    hh.setMinimumSectionSize(40)
    hh.setDefaultSectionSize(100)
    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)

    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    # تطبيق الـ delegate
    set_flexible_columns(table, wrap_cols=wrap_cols, min_row_height=min_row_height)

    return table


# ══════════════════════════════════════════════════════════
# FlexibleTreeWidget — QTreeWidget بـ word-wrap
# ══════════════════════════════════════════════════════════

class FlexibleTreeWidget(QTreeWidget):
    """
    QTreeWidget بـ:
      - word-wrap تلقائي في العمود الأول
      - tooltip تلقائي لكل الأعمدة
      - ارتفاع الصف يتمدد حسب المحتوى
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.ElideRight)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setUniformRowHeights(False)  # مهم لـ word-wrap
        self._wrap_delegate = WrapDelegate(self, min_row_height=28)

    def setWrapColumn(self, col: int):
        """بيطبق wrap على عمود محدد."""
        self.setItemDelegateForColumn(col, self._wrap_delegate)

    def addFlexibleItem(self, parent_item, texts: list[str],
                        tooltips: list[str] = None) -> QTreeWidgetItem:
        """
        يضيف item بـ tooltip تلقائي.
        texts: نصوص الأعمدة
        tooltips: tooltips مخصصة، أو None للنص الكامل
        """
        item = QTreeWidgetItem(texts if parent_item is None else None)
        for i, text in enumerate(texts):
            item.setText(i, text)
            tip = tooltips[i] if tooltips and i < len(tooltips) else text
            item.setToolTip(i, tip)

        if parent_item is None:
            self.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        return item


# ══════════════════════════════════════════════════════════
# دالة مساعدة لتحديث tooltip بعد ملء الجدول
# ══════════════════════════════════════════════════════════

def refresh_tooltips(table: QTableWidget):
    """
    يحدّث tooltip كل الخلايا بالنص الكامل.
    استدعها بعد إضافة صفوف جديدة للجدول.
    """
    for r in range(table.rowCount()):
        for c in range(table.columnCount()):
            item = table.item(r, c)
            if item and item.text() and not item.toolTip():
                item.setToolTip(item.text())


# ══════════════════════════════════════════════════════════
# FlexItem — QTableWidgetItem مع tooltip تلقائي
# ══════════════════════════════════════════════════════════

class FlexItem(QTableWidgetItem):
    """
    QTableWidgetItem بيضيف tooltip = النص الكامل تلقائيًا.
    استخدمه بدل QTableWidgetItem في الجداول.
    """
    def __init__(self, text: str = "", tooltip: str = None):
        super().__init__(text)
        self.setToolTip(tooltip if tooltip is not None else text)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)