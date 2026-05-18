"""
ui/helpers.py
=============
أدوات UI مشتركة — تستورد من widgets/shared وتُعيد تصديرها.

ملاحظة: كل التعريفات الحقيقية موجودة في widgets/shared.
         هذا الملف للتوافق مع الكود القديم فقط.
"""

from PyQt5.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QWidget,
    QTableWidget, QMessageBox,
)
from PyQt5.QtGui  import QFont, QColor
from PyQt5.QtCore import Qt

from ui.app_settings import _C, get_font_size, fs

# ── إعادة تصدير من widgets/shared ──
from ui.widgets.shared.flexible_text import WrapDelegate                    # noqa: F401
from ui.widgets.shared.table_utils import (                                  # noqa: F401
    make_list_table as make_table,
    make_table_item, color_item, bold_item, muted_item,
    auto_fit_columns, fit_splitter_to_table,
    ROW_HEIGHT_NORMAL, ROW_HEIGHT_COMPACT, ROW_HEIGHT_LARGE,
)
from ui.widgets.shared.scrollable_form import wrap_in_scroll as wrap_scroll  # noqa: F401


# ══════════════════════════════════════════════════════════
# Scroll stylesheet موحد — يُستورد من هنا في كل الملفات
# ══════════════════════════════════════════════════════════

SCROLL_SS = f"""
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

# للتوافق مع الكود القديم الذي يستخدم _SCROLL_SS
_SCROLL_SS = SCROLL_SS


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


def setup_table_columns(
    table: QTableWidget,
    widths: dict = None,
    stretch_col: int = -1,
    min_width: int = 50,
):
    from PyQt5.QtWidgets import QHeaderView
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