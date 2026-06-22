"""
ui/widgets/panels/state.py
===========================
EmptyState + EmptyPanelState + table empty state helpers.

التغييرات:
  - [إصلاح imports] استبدال relative imports بـ absolute imports
  - [i18n/themes] EmptyState تحفظ reference للـ title label للتحديث المباشر.
  - [تحسين 6 محفوظ] get_font_size() تُستدعى مرة واحدة.
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont

from ui.font  import fs, get_font_size
from ui.theme import _C
from ..core.colors import card_colors, status_colors
from ui.constants import EMPTY_STATE_DEFAULT_MIN_H
from ui.widgets.core.widget_mixin import WidgetMixin


# ══════════════════════════════════════════════════════════
# EmptyState
# ══════════════════════════════════════════════════════════

class EmptyState(QFrame, WidgetMixin):
    """
    QFrame حالة فارغة مع أيقونة ونص وزر اختياري.

    [i18n/themes] يحفظ reference للـ title label في _lbl_title.
    """

    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋", title: str = "",
                 subtitle: str = "", action_text: str = "",
                 style: str = "dashed", color: str = None,
                 min_height: int = EMPTY_STATE_DEFAULT_MIN_H,
                 expandable: bool = False,
                 parent=None):
        super().__init__(parent)
        self._expandable = expandable
        self._lbl_title  = None
        self._lbl_icon   = None
        self._lbl_sub    = None
        self._icon       = icon
        self._color_arg  = color
        self._style      = style
        self._min_h      = min_height
        self._subtitle   = subtitle
        self._action_text = action_text
        _color = color or _C['text_muted']
        from ui.widgets.core.i18n import tr
        _title = title or tr('no_data')
        self._title_text = title
        self._build(icon, _title, subtitle, action_text, style, _color, min_height)
        self._init_widget_mixin(theme=True, font=True, lang=True, data=False)

    def _build(self, icon, title, subtitle, action_text, style, color, min_h):
        bg, border = card_colors(color)
        border_css = {"dashed": "dashed", "solid": "solid", "plain": "none"}.get(
            style, "dashed"
        )

        from ui.constants import EMPTY_STATE_BORDER_RADIUS
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:2px {border_css} {border};
                border-radius:{EMPTY_STATE_BORDER_RADIUS}px;
            }}
        """)
        self.setMinimumHeight(min_h)

        if self._expandable:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        from ui.constants import (
            EMPTY_STATE_SPACING, EMPTY_STATE_SPACING_EXPANDED,
            EMPTY_STATE_MARGIN_H, EMPTY_STATE_MARGIN_V, EMPTY_STATE_MARGIN_V_EXPANDED,
        )
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(EMPTY_STATE_SPACING if not self._expandable else EMPTY_STATE_SPACING_EXPANDED)
        lay.setContentsMargins(
            EMPTY_STATE_MARGIN_H,
            EMPTY_STATE_MARGIN_V if not self._expandable else EMPTY_STATE_MARGIN_V_EXPANDED,
            EMPTY_STATE_MARGIN_H,
            EMPTY_STATE_MARGIN_V if not self._expandable else EMPTY_STATE_MARGIN_V_EXPANDED,
        )

        base = get_font_size()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"background:transparent; border:none; font-size:{fs(base, +8)}pt;"
            )
            lay.addWidget(lbl_icon)
            self._lbl_icon = lbl_icon

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:700; font-size:{fs(base, +1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

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
            self._lbl_sub = lbl_sub

        if action_text:
            from ..components.button import make_btn
            from ui.constants import EMPTY_STATE_ACTION_BTN_W
            btn_style = "primary" if self._expandable else "success"
            btn = make_btn(action_text, btn_style)
            if not self._expandable:
                btn.setFixedWidth(EMPTY_STATE_ACTION_BTN_W)
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)

    def _refresh_style(self, *_):
        from ui.constants import EMPTY_STATE_BORDER_RADIUS
        color = self._color_arg or _C['text_muted']
        bg, border = card_colors(color)
        border_css = {"dashed": "dashed", "solid": "solid", "plain": "none"}.get(
            self._style, "dashed"
        )
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:2px {border_css} {border};
                border-radius:{EMPTY_STATE_BORDER_RADIUS}px;
            }}
        """)
        base = get_font_size()
        if self._lbl_icon is not None:
            self._lbl_icon.setStyleSheet(
                f"background:transparent; border:none; font-size:{fs(base, +8)}pt;"
            )
        if self._lbl_title is not None:
            self._lbl_title.setStyleSheet(
                f"color:{color}; font-weight:700; font-size:{fs(base, +1)}pt;"
                "background:transparent; border:none;"
            )
        if self._lbl_sub is not None:
            self._lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt;"
                "background:transparent; border:none;"
            )

    def _refresh_lang(self, *_):
        if self._lbl_title is not None and not self._title_text:
            from ui.widgets.core.i18n import tr
            self._lbl_title.setText(tr('no_data'))

    def set_title(self, text: str):
        if self._lbl_title is not None:
            self._lbl_title.setText(text)

    def title(self) -> str:
        if self._lbl_title is not None:
            return self._lbl_title.text()
        return ""


# ── alias للتوافق مع الكود القديم ─────────────────────────

def EmptyPanelState(icon: str = "📋", title: str = "",
                    subtitle: str = "", action_text: str = "",
                    color: str = None, parent=None) -> EmptyState:
    """Alias لـ EmptyState(expandable=True). محفوظ للتوافق."""
    from ui.widgets.core.i18n import tr
    return EmptyState(
        icon=icon, title=title or tr('no_data'), subtitle=subtitle,
        action_text=action_text,
        color=color or _C['text_muted'],
        style="plain", expandable=True, parent=parent,
    )


# ══════════════════════════════════════════════════════════
# Table empty state helpers
# ══════════════════════════════════════════════════════════

def set_table_empty_state(table: QTableWidget,
                           message: str = "",
                           icon: str = "📋",
                           color: str = None):
    """يضيف صفاً واحداً يعرض رسالة فارغة في الجدول."""
    from ui.widgets.core.i18n import tr
    _color = color or _C['text_muted']
    _message = message or tr('no_data')
    from ui.constants import EMPTY_STATE_TABLE_ROW_H
    table.setRowCount(1)
    table.setRowHeight(0, EMPTY_STATE_TABLE_ROW_H)

    col_count = table.columnCount()
    msg_text  = f"{icon}  {_message}" if icon else _message

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