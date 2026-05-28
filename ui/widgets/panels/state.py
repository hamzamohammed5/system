"""
ui/widgets/panels/state.py
===========================
مكونات الـ Empty State الموحدة:

  EmptyState              — QFrame حالة فارغة مع أيقونة ونص وزر
  EmptyPanelState         — alias للتوافق مع الكود القديم
  set_table_empty_state   — صف رسالة داخل الجدول
  clear_table_empty_state — مسح صف الرسالة

[تحسين 6 محفوظ] get_font_size() تُستدعى مرة واحدة.

[i18n/themes] EmptyState تحفظ reference للـ title label (_lbl_title)
لتحديثه مباشرة عند تغيير اللغة بدون إعادة بناء الـ widget.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings        import _C, fs, get_font_size
from ..core.colors          import card_colors, status_colors


# ══════════════════════════════════════════════════════════
# EmptyState
# ══════════════════════════════════════════════════════════

class EmptyState(QFrame):
    """
    QFrame حالة فارغة مع أيقونة ونص وزر اختياري.

    expandable=True → يتمدد ليملأ المساحة.
    expandable=False (افتراضي) → حجم ثابت حسب المحتوى.

    [i18n/themes] يحفظ reference للـ title label في _lbl_title
    لتحديثه مباشرة من الخارج عند تغيير اللغة.
    """

    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋", title: str = "لا توجد بيانات",
                 subtitle: str = "", action_text: str = "",
                 style: str = "dashed", color: str = None,
                 min_height: int = 80,
                 expandable: bool = False,
                 parent=None):
        super().__init__(parent)
        self._expandable = expandable
        self._lbl_title  = None   # [i18n/themes] reference للـ title label
        _color = color or _C['text_muted']
        self._build(icon, title, subtitle, action_text, style, _color, min_height)

    def _build(self, icon, title, subtitle, action_text, style, color, min_h):
        bg, border = card_colors(color)
        border_css = {"dashed": "dashed", "solid": "solid", "plain": "none"}.get(
            style, "dashed"
        )

        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:2px {border_css} {border};
                border-radius:10px;
            }}
        """)
        self.setMinimumHeight(min_h)

        if self._expandable:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6 if not self._expandable else 8)
        lay.setContentsMargins(
            20, 16 if not self._expandable else 30,
            20, 16 if not self._expandable else 30,
        )

        # [تحسين 6] استدعاء get_font_size() مرة واحدة وتخزينها
        base = get_font_size()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"background:transparent; border:none; font-size:{fs(base, +8)}pt;"
            )
            lay.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:700; font-size:{fs(base, +1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

        # [i18n/themes] حفظ reference للـ title label
        self._lbl_title = lbl_title

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setWordWrap(True)
            lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt;"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_sub)

        if action_text:
            from ..components.button import make_btn
            btn_style = "primary" if self._expandable else "success"
            btn = make_btn(action_text, btn_style)
            if not self._expandable:
                btn.setFixedWidth(140)
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)

    def set_title(self, text: str):
        """
        [i18n/themes] يُحدّث نص العنوان مباشرة.
        يُستخدم من _on_language_changed() في الـ panels.
        """
        if self._lbl_title is not None:
            self._lbl_title.setText(text)

    def title(self) -> str:
        """يرجع النص الحالي للعنوان."""
        if self._lbl_title is not None:
            return self._lbl_title.text()
        return ""


# ── alias للتوافق مع الكود القديم ─────────────────────────

def EmptyPanelState(icon: str = "📋", title: str = "لا توجد بيانات",
                    subtitle: str = "", action_text: str = "",
                    color: str = None, parent=None) -> EmptyState:
    """Alias لـ EmptyState(expandable=True). محفوظ للتوافق مع الكود القديم."""
    return EmptyState(
        icon=icon, title=title, subtitle=subtitle,
        action_text=action_text,
        color=color or _C['text_muted'],
        style="plain", expandable=True, parent=parent,
    )


# ══════════════════════════════════════════════════════════
# Table empty state helpers
# ══════════════════════════════════════════════════════════

def set_table_empty_state(table: QTableWidget,
                           message: str = "لا توجد بيانات",
                           icon: str = "📋",
                           color: str = None):
    """يضيف صفاً واحداً يعرض رسالة فارغة في الجدول."""
    _color = color or _C['text_muted']
    table.setRowCount(1)
    table.setRowHeight(0, 60)

    col_count = table.columnCount()
    msg_text  = f"{icon}  {message}" if icon else message

    item = QTableWidgetItem(msg_text)
    item.setTextAlignment(Qt.AlignCenter)
    item.setForeground(QColor(_color))
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