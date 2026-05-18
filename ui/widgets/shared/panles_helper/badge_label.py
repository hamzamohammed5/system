"""
ui/widgets/shared/panles_helper/badge_label.py
============================
"""

from PyQt5.QtWidgets import (
    QLabel
)
from PyQt5.QtCore import Qt

from ui.app_settings import fs
from .colors_and_base import _base

# ══════════════════════════════════════════════════════════
# BadgeLabel
# ══════════════════════════════════════════════════════════

class BadgeLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._apply_base_style()

    def _apply_base_style(self, text_color="#555", bg="#f5f5f5", border="#e0e0e0"):
        base = _base()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,-1)}pt;"
            f"padding:3px 12px; border-radius:20px;"
            f"color:{text_color}; background:{bg}; border:1.5px solid {border};"
        )

    def set_badge(self, text: str, text_color: str = "#555",
                  bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        self.setText(text)
        self._apply_base_style(text_color, bg, border)

    def clear_badge(self):
        self.setText("")
        self._apply_base_style()

