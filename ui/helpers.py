"""
ui/helpers.py
=============
أدوات UI مشتركة — محسّنة ومتناسقة مع app_settings._C
"""

from PyQt5.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QWidget,
    QTableWidget, QHeaderView, QMessageBox,
    QAbstractItemView, QSizePolicy,
    QStyledItemDelegate, QStyle, QApplication,
)
from PyQt5.QtGui import QFont, QFontMetrics, QColor
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtWidgets import QScrollArea

from ui.app_settings import _C, get_font_size, fs


# ══════════════════════════════════════════════════════════
# WrapDelegate — عرض النص بـ word-wrap مع tooltip تلقائي
# ══════════════════════════════════════════════════════════

class WrapDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, min_row_height: int = 30, padding: int = 10):
        super().__init__(parent)
        self._min_row_height = min_row_height
        self._padding        = padding

    def paint(self, painter, option, index):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        text = index.data(Qt.DisplayRole)
        if text is None:
            text = ""
        text = str(text)

        rect = option.rect.adjusted(self._padding, 2, -self._padding, -2)

        if option.state & QStyle.State_Selected:
            painter.setPen(QColor(_C['accent_text']))
        else:
            fg = index.data(Qt.ForegroundRole)
            if fg:
                try:
                    painter.setPen(fg.color() if hasattr(fg, 'color') else fg)
                except Exception:
                    painter.setPen(QColor(_C['text_primary']))
            else:
                painter.setPen(QColor(_C['text_primary']))

        painter.setFont(option.font)
        painter.drawText(
            QRect(rect),
            Qt.AlignRight | Qt.AlignVCenter | Qt.TextWordWrap,
            text
        )
        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(Qt.DisplayRole)
        if text is None:
            text = ""
        text = str(text)

        fm        = QFontMetrics(option.font)
        col_width = option.rect.width() if option.rect.isValid() else 150
        text_width = max(col_width - self._padding * 2, 80)

        text_rect = fm.boundingRect(
            0, 0, text_width, 9999,
            Qt.AlignRight | Qt.AlignTop | Qt.TextWordWrap,
            text
        )
        height = max(self._min_row_height, text_rect.height() + 10)
        return QSize(col_width, height)


# ══════════════════════════════════════════════════════════
# مساعدات إنشاء عناصر UI
# ══════════════════════════════════════════════════════════

def bold_label(text: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setBold(True)
    lbl.setFont(f)
    return lbl


def section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("role", "section")
    f = QFont()
    f.setBold(True)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {_C['text_sec']};")
    return lbl


def danger_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{
            color: {_C['danger']};
            background: {_C['danger_bg']};
            border: 1px solid {_C['danger_border']};
            border-radius: 5px;
            padding: 3px 12px;
        }}
        QPushButton:hover {{
            background: #FCDBD9;
            border-color: {_C['danger']};
        }}
    """)
    return btn


def success_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {_C['success']};
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 5px;
            padding: 4px 16px;
        }}
        QPushButton:hover {{
            background: #236B42;
        }}
    """)
    return btn


# ══════════════════════════════════════════════════════════
# make_table — الجدول الموحد المحسّن
# ══════════════════════════════════════════════════════════

def make_table(
    columns: list,
    stretch_col: int = -1,
    min_row_height: int = 32,
) -> QTableWidget:
    base = get_font_size()

    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setWordWrap(True)
    table.setAlternatingRowColors(True)
    table.setShowGrid(True)
    table.setFrameShape(QTableWidget.NoFrame)

    # تطبيق stylesheet محسّن على الجدول
    table.setStyleSheet(f"""
        QTableWidget {{
            background: {_C['bg_input']};
            alternate-background-color: {_C['bg_surface']};
            gridline-color: {_C['border']};
            border: none;
            selection-background-color: {_C['accent_light']};
        }}
        QTableWidget::item {{
            padding: 5px 10px;
            border-bottom: 1px solid {_C['border']};
            color: {_C['text_primary']};
        }}
        QTableWidget::item:selected {{
            background: {_C['accent_light']};
            color: {_C['accent_text']};
        }}
        QTableWidget::item:hover {{
            background: {_C['bg_hover']};
        }}
        QHeaderView::section {{
            background: {_C['bg_surface_2']};
            color: {_C['text_muted']};
            font-size: {fs(base, -1)}pt;
            font-weight: 600;
            padding: 6px 10px;
            border: none;
            border-bottom: 2px solid {_C['border_med']};
            border-right: 1px solid {_C['border']};
            letter-spacing: 0.2px;
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
        QHeaderView::section:hover {{
            background: {_C['bg_hover']};
            color: {_C['text_primary']};
        }}
    """)

    hh = table.horizontalHeader()
    vh = table.verticalHeader()

    vh.setSectionResizeMode(QHeaderView.ResizeToContents)
    vh.setDefaultSectionSize(min_row_height)
    vh.setMinimumSectionSize(min_row_height)
    vh.setVisible(False)

    for i in range(len(columns)):
        if i == stretch_col:
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            hh.setSectionResizeMode(i, QHeaderView.Interactive)

    if stretch_col < 0:
        hh.setStretchLastSection(True)

    hh.setMinimumSectionSize(40)
    hh.setDefaultSectionSize(100)
    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
    hh.setHighlightSections(False)

    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    delegate = WrapDelegate(table, min_row_height=min_row_height)
    table.setItemDelegate(delegate)

    return table


def setup_table_columns(
    table: QTableWidget,
    widths: dict = None,
    stretch_col: int = -1,
    min_width: int = 50,
):
    hh = table.horizontalHeader()
    n  = table.columnCount()

    for i in range(n):
        if i == stretch_col:
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            if widths and i in widths:
                table.setColumnWidth(i, widths[i])

    hh.setMinimumSectionSize(min_width)


def buttons_row(*buttons) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(6)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


# ══════════════════════════════════════════════════════════
# EditModeMixin
# ══════════════════════════════════════════════════════════

class EditModeMixin:
    def init_edit_mode(self, add_btn, save_btn, cancel_btn, mode_label=None):
        self._em_add_btn    = add_btn
        self._em_save_btn   = save_btn
        self._em_cancel_btn = cancel_btn
        self._em_mode_label = mode_label
        self._editing_id    = None
        save_btn.setVisible(False)
        cancel_btn.setVisible(False)

    def enter_edit_mode(self, record_id: int, label_text: str = ""):
        self._editing_id = record_id
        self._em_add_btn.setVisible(False)
        self._em_save_btn.setVisible(True)
        self._em_cancel_btn.setVisible(True)
        if self._em_mode_label and label_text:
            self._em_mode_label.setText(label_text)

    def exit_edit_mode(self, default_label: str = ""):
        self._editing_id = None
        self._em_add_btn.setVisible(True)
        self._em_save_btn.setVisible(False)
        self._em_cancel_btn.setVisible(False)
        if self._em_mode_label and default_label:
            self._em_mode_label.setText(default_label)

    @property
    def is_editing(self) -> bool:
        return self._editing_id is not None


# ══════════════════════════════════════════════════════════
# تأكيد الحذف
# ══════════════════════════════════════════════════════════

def confirm_delete(parent, name: str) -> bool:
    return QMessageBox.question(
        parent, "تأكيد الحذف", f"هل تريد حذف «{name}»؟",
        QMessageBox.Yes | QMessageBox.No
    ) == QMessageBox.Yes


# ══════════════════════════════════════════════════════════
# Scroll wrapper موحد
# ══════════════════════════════════════════════════════════

_SCROLL_SS = f"""
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
"""


def wrap_scroll(widget, min_width: int = 0, min_height: int = 0) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(_SCROLL_SS)

    if min_width:
        scroll.setMinimumWidth(min_width)
    if min_height:
        scroll.setMinimumHeight(min_height)

    return scroll