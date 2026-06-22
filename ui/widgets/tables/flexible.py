"""
ui/widgets/tables/flexible.py
==============================
Delegates وأدوات word-wrap للجداول.

[Refactor V3 — المرحلة 3] refresh_tooltips تُستورد من utils/tooltip
بدل تعريف مكرر هنا.

[إصلاح] حذف re-export لـ refresh_tooltips — كل من يحتاجها يستورد مباشرة:
    from ui.widgets.utils.tooltip import refresh_tooltips
"""
from PyQt5.QtWidgets import (
    QStyledItemDelegate, QStyle, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem,
)
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui  import QFontMetrics, QPainter, QTextOption

from ui.constants import (
    COL_MIN_WIDTH,
    FLEX_WRAP_MIN_ROW_H, FLEX_WRAP_PADDING,
    FLEX_DEFAULT_COL_WIDTH, FLEX_TABLE_MIN_ROW_H,
    FLEX_ROW_HEIGHT_PAD,
)


class WrapDelegate(QStyledItemDelegate):
    """Delegate يعمل word-wrap في خلايا الجدول."""

    def __init__(self, parent=None, min_row_height: int = FLEX_WRAP_MIN_ROW_H, padding: int = FLEX_WRAP_PADDING):
        super().__init__(parent)
        self._min_h  = min_row_height
        self._pad    = padding

    def paint(self, painter: QPainter, option, index):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        text = str(index.data(Qt.DisplayRole) or "")
        rect = option.rect.adjusted(self._pad, 2, -self._pad, -2)

        text_opt = QTextOption()
        text_opt.setWrapMode(QTextOption.WordWrap)
        text_opt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            fg = index.data(Qt.ForegroundRole)
            try:
                painter.setPen(fg.color() if (fg and hasattr(fg, 'color')) else
                               option.palette.text().color())
            except Exception:
                painter.setPen(option.palette.text().color())

        painter.setFont(option.font)
        painter.drawText(QRect(rect), Qt.AlignRight | Qt.AlignVCenter | Qt.TextWordWrap, text)
        painter.restore()

    def sizeHint(self, option, index):
        text = str(index.data(Qt.DisplayRole) or "")
        view = option.widget
        if view and hasattr(view, 'columnWidth'):
            col_width = view.columnWidth(index.column())
        elif option.rect.isValid():
            col_width = option.rect.width()
        else:
            col_width = FLEX_DEFAULT_COL_WIDTH

        text_width = max(col_width - self._pad * 2, COL_MIN_WIDTH)
        fm = QFontMetrics(option.font)
        text_rect = fm.boundingRect(0, 0, text_width, 9999,
                                    Qt.AlignRight | Qt.AlignTop | Qt.TextWordWrap, text)
        return QSize(col_width, max(self._min_h, text_rect.height() + FLEX_ROW_HEIGHT_PAD))


class AutoTooltipDelegate(QStyledItemDelegate):
    """Delegate يضيف tooltip تلقائي بالنص الكامل."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        text = index.data(Qt.DisplayRole)
        if text:
            option.text = str(text)


class FlexItem(QTableWidgetItem):
    """QTableWidgetItem مع tooltip تلقائي."""

    def __init__(self, text: str = "", tooltip: str = None):
        super().__init__(text)
        self.setToolTip(tooltip if tooltip is not None else text)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)


def set_flexible_columns(table: QTableWidget, wrap_cols: list = None,
                         min_row_height: int = FLEX_TABLE_MIN_ROW_H):
    table.setWordWrap(True)
    table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    delegate = WrapDelegate(table, min_row_height=min_row_height)
    if wrap_cols is None:
        table.setItemDelegate(delegate)
    else:
        for col in wrap_cols:
            table.setItemDelegateForColumn(col, delegate)
        tip = AutoTooltipDelegate(table)
        for col in set(range(table.columnCount())) - set(wrap_cols):
            table.setItemDelegateForColumn(col, tip)


def make_flexible_table(columns: list, stretch_col: int = -1,
                        wrap_cols: list = None,
                        min_row_height: int = FLEX_TABLE_MIN_ROW_H) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setWordWrap(True)

    hh = table.horizontalHeader()
    vh = table.verticalHeader()
    vh.setSectionResizeMode(QHeaderView.ResizeToContents)
    vh.setDefaultSectionSize(min_row_height)
    vh.setMinimumSectionSize(min_row_height)

    for i in range(len(columns)):
        if i == stretch_col:
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
    if stretch_col < 0:
        hh.setStretchLastSection(True)

    hh.setMinimumSectionSize(COL_MIN_WIDTH)
    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    set_flexible_columns(table, wrap_cols=wrap_cols, min_row_height=min_row_height)
    return table


class FlexibleTreeWidget(QTreeWidget):
    """QTreeWidget مع word-wrap وtooltip تلقائي."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setUniformRowHeights(False)
        self._wrap_delegate = WrapDelegate(self, min_row_height=FLEX_WRAP_MIN_ROW_H)

    def setWrapColumn(self, col: int):
        self.setItemDelegateForColumn(col, self._wrap_delegate)

    def addFlexibleItem(self, parent_item, texts: list,
                        tooltips: list = None) -> QTreeWidgetItem:
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