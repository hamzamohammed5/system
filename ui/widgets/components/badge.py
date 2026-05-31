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


class BadgeLabel(QLabel):
    """شارة نصية ملونة."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._apply(_C["text_sec"], _C["bg_surface_2"], _C["border"])

    def _apply(self, fg: str, bg: str, border: str):
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,-1)}pt;"
            f"padding:3px 12px; border-radius:20px;"
            f"color:{fg}; background:{bg}; border:1.5px solid {border};"
        )

    def set_badge(self, text: str, text_color: str = None,
                  bg: str = None, border: str = None):
        self.setText(text)
        self._apply(
            text_color or _C["text_sec"],
            bg         or _C["bg_surface_2"],
            border     or _C["border"],
        )

    def clear_badge(self):
        self.setText("")
        self._apply(_C["text_sec"], _C["bg_surface_2"], _C["border"])