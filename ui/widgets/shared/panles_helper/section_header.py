"""
ui/widgets/shared/panles_helper/section_header.py
============================
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont, QColor

from ui.app_settings import _C, get_font_size, fs
from .make_btn import _make_btn
from .colors_and_base import _base

# ══════════════════════════════════════════════════════════
# SectionHeader
# ══════════════════════════════════════════════════════════

class SectionHeader(QWidget):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._build(title)

    def _build(self, title):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(10)

        accent = QFrame()
        accent.setFixedSize(3, 18)
        accent.setStyleSheet(
            f"background:{_C['accent']}; border-radius:2px; border:none;"
        )
        lay.addWidget(accent)

        self._lbl = QLabel(title)
        base = _base()
        self._lbl.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,+1)}pt;"
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl)
        lay.addStretch()

        self._btn_container = lay

    def set_title(self, title: str):
        self._lbl.setText(title)

    def add_button(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        btn = _make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        self._btn_container.addWidget(btn)
        return btn
