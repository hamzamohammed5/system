"""
ui/widgets/components/badge.py
================================
BadgeLabel — شارة نصية ملونة.

مستخرج من components/stat_row.py.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    BADGE_LABEL_PAD_V, BADGE_LABEL_PAD_H,
    BADGE_LABEL_BORDER_RADIUS, BADGE_LABEL_BORDER_W,
)


class BadgeLabel(QLabel, WidgetMixin):
    """شارة نصية ملونة."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        # None = استخدم الافتراضي من _C عند كل رسم (يتحدث مع الثيم تلقائياً)
        self._fg     = None
        self._bg     = None
        self._border = None
        self._init_widget_mixin(theme=True, font=True)
        self._refresh_style()

    def _refresh_style(self, *_):
        fg     = self._fg     or _C["text_sec"]
        bg     = self._bg     or _C["bg_surface_2"]
        border = self._border or _C["border"]
        self._apply(fg, bg, border)

    def _apply(self, fg: str, bg: str, border: str):
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,-1)}pt;"
            f"padding:{BADGE_LABEL_PAD_V}px {BADGE_LABEL_PAD_H}px;"
            f"border-radius:{BADGE_LABEL_BORDER_RADIUS}px;"
            f"color:{fg}; background:{bg}; border:{BADGE_LABEL_BORDER_W}px solid {border};"
        )

    def set_badge(self, text: str, text_color: str = None,
                  bg: str = None, border: str = None):
        self.setText(text)
        # None = fallback لـ _C عند _refresh_style
        self._fg     = text_color
        self._bg     = bg
        self._border = border
        fg     = self._fg     or _C["text_sec"]
        bg_    = self._bg     or _C["bg_surface_2"]
        border_= self._border or _C["border"]
        self._apply(fg, bg_, border_)

    def clear_badge(self):
        self.setText("")
        self._fg     = None
        self._bg     = None
        self._border = None
        self._apply(_C["text_sec"], _C["bg_surface_2"], _C["border"])