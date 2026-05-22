"""
ui/helpers.py
=============
أدوات UI مشتركة — تستورد من widgets/shared وتُعيد تصديرها.

الإصلاح: make_detail_scroll / set_detail_content
  - الـ scroll بيقبل horizontal + vertical
  - الـ inner container عنده setMinimumWidth
  عشان لما النافذة تضيق يظهر scrollbar أفقي يشمل كل حاجة.

live_conn:
  - يرجع connection صالح دايماً
  - لو stored_conn صالح → يستخدمه
  - لو لا → يجيب connection جديد من company_state
"""

from PyQt5.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QWidget,
    QTableWidget, QMessageBox, QScrollArea,
)
from PyQt5.QtGui  import QFont, QColor
from PyQt5.QtCore import Qt

from ui.app_settings import _C, get_font_size, fs

from ui.widgets.shared.flexible_text import WrapDelegate                    # noqa: F401
from ui.widgets.shared.table_utils import (                                  # noqa: F401
    make_list_table as make_table,
    make_table_item, color_item, bold_item, muted_item,
    auto_fit_columns, fit_splitter_to_table,
    ROW_HEIGHT_NORMAL, ROW_HEIGHT_COMPACT, ROW_HEIGHT_LARGE,
)
from ui.widgets.shared.scrollable_form import wrap_in_scroll as wrap_scroll  # noqa: F401

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

_SCROLL_SS = SCROLL_SS


# ══════════════════════════════════════════════════════════
# live_conn — connection صالح دايماً
# ══════════════════════════════════════════════════════════

def live_conn(stored_conn=None, db: str = "erp"):
    """
    يرجع connection صالح دايماً.

    - لو stored_conn مش None وصالح → يستخدمه كما هو.
    - لو stored_conn None أو مغلق أو فشل → يجيب connection
      جديد من company_state.

    الاستخدام:
        conn = live_conn(self.conn)
        rows = fetch_all_categories(conn, self.scope)
    """
    if stored_conn is not None:
        try:
            stored_conn.execute("SELECT 1")
            return stored_conn
        except Exception:
            pass
    from db.companies.company_state import company_state
    return company_state._get_conn(db)


def make_detail_scroll(min_content_width: int = 520) -> QScrollArea:
    """
    QScrollArea للـ detail panels مع horizontal scroll حقيقي.

    المهم: بعد ما تعمل make_detail_scroll، استخدم set_detail_content()
    لوضع المحتوى جواه — هو بيضبط setMinimumWidth على الـ content
    عشان الـ horizontal scroll يظهر فعلاً لما النافذة تضيق.
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(SCROLL_SS)
    scroll._min_content_width = min_content_width
    return scroll


def set_detail_content(scroll: QScrollArea, content: QWidget,
                       bg: str = "#f8f9fb"):
    """
    يضع الـ content جوا الـ scroll مع ضبط minimum width
    عشان الـ horizontal scroll يظهر لما المحتوى أعرض من الـ panel.
    """
    min_w = getattr(scroll, '_min_content_width', 520)
    content.setStyleSheet(f"background:{bg};")
    content.setMinimumWidth(min_w)
    scroll.setWidget(content)


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


def confirm_delete(parent, name: str) -> bool:
    return QMessageBox.question(
        parent, "تأكيد الحذف", f"هل تريد حذف «{name}»؟",
        QMessageBox.Yes | QMessageBox.No
    ) == QMessageBox.Yes