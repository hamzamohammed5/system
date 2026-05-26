"""
ui/widgets/panels/state.py
===========================
مكونات الـ Empty State الموحدة:

  EmptyState          — QFrame حالة فارغة مع أيقونة ونص وزر
  EmptyPanelState     — widget أوسع مع stretch
  set_table_empty_state   — صف رسالة داخل الجدول
  clear_table_empty_state — مسح صف الرسالة
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayou, QLabel,
    QTableWidget, QTableWidgetItem, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings import _C, fs, get_font_size


def _base() -> int:
    return get_font_size()


def _make_btn(text: str, style: str = "primary"):
    from ..components.button import make_btn
    return make_btn(text, style)


def _card_colors(color: str) -> tuple[str, str]:
    from ..core.colors import card_colors
    return card_colors(color)


# ══════════════════════════════════════════════════════════
# EmptyState
# ══════════════════════════════════════════════════════════

class EmptyState(QFrame):
    """QFrame حالة فارغة مع أيقونة ونص وزر اختياري."""

    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋", title: str = "لا توجد بيانات",
                 subtitle: str = "", action_text: str = "",
                 style: str = "dashed", color: str = "#10b981",
                 min_height: int = 80, parent=None):
        super().__init__(parent)
        self._build(icon, title, subtitle, action_text, style, color, min_height)

    def _build(self, icon, title, subtitle, action_text, style, color, min_h):
        bg, border = _card_colors(color)
        border_css = {"dashed": "dashed", "solid": "solid", "plain": "none"}.get(style, "dashed")

        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:2px {border_css} {border}; border-radius:10px;
            }}
        """)
        self.setMinimumHeight(min_h)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)
        lay.setContentsMargins(20, 16, 20, 16)

        base = _base()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"background:transparent; border:none; font-size:{fs(base,+8)}pt;"
            )
            lay.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:700; font-size:{fs(base,+1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_sub)

        if action_text:
            btn = _make_btn(action_text, "success")
            btn.setFixedWidth(140)
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)


# ══════════════════════════════════════════════════════════
# EmptyPanelState
# ══════════════════════════════════════════════════════════

class EmptyPanelState(QWidget):
    """Widget حالة فارغة للـ panels مع تمدد."""

    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋", title: str = "لا توجد بيانات",
                 subtitle: str = "", action_text: str = "",
                 color: str = "#9ca3af", parent=None):
        super().__init__(parent)
        self._build(icon, title, subtitle, action_text, color)

    def _build(self, icon, title, subtitle, action_text, color):
        self.setStyleSheet("background:transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(8)
        lay.setContentsMargins(20, 30, 20, 30)

        base = _base()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"font-size:{fs(base,+8)}pt; background:transparent; border:none;"
            )
            lay.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:700; font-size:{fs(base,+1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet(
                f"color:{_C.get('text_muted','#9ca3af')}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            lbl_sub.setWordWrap(True)
            lay.addWidget(lbl_sub)

        if action_text:
            btn = _make_btn(action_text, "primary")
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)


# ══════════════════════════════════════════════════════════
# Table empty state helpers
# ══════════════════════════════════════════════════════════

def set_table_empty_state(table: QTableWidget,
                           message: str = "لا توجد بيانات",
                           icon: str = "📋",
                           color: str = "#9ca3af"):
    """يضيف صفاً واحداً يعرض رسالة فارغة في الجدول."""
    table.setRowCount(1)
    table.setRowHeight(0, 60)

    col_count = table.columnCount()
    msg_text  = f"{icon}  {message}" if icon else message

    item = QTableWidgetItem(msg_text)
    item.setTextAlignment(Qt.AlignCenter)
    item.setForeground(QColor(color))
    f = QFont()
    f.setItalic(True)
    item.setFont(f)
    item.setFlags(Qt.ItemIsEnabled)

    table.setItem(0, 0, item)
    if col_count > 1:
        table.setSpan(0, 0, 1, col_count)


def clear_table_empty_state(table: QTableWidget):
    """يمسح صف الحالة الفارغة لو كان موجوداً."""
    if table.rowCount() == 1:
        item = table.item(0, 0)
        if item and not (item.flags() & Qt.ItemIsSelectable):
            table.setRowCount(0)
            if table.columnCount() > 1:
                table.setSpan(0, 0, 1, 1)