"""
ui/widgets/shared/panles_helper/info_row.py
============================
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout,
    QLabel
)


from ui.app_settings import _C, fs
from .colors_and_base import _base

# ══════════════════════════════════════════════════════════
# InfoRow
# ══════════════════════════════════════════════════════════

class InfoRow(QWidget):
    def __init__(self, separator: str = "  ·  ", parent=None):
        super().__init__(parent)
        self._separator = separator
        self._lbl = QLabel()
        base = _base()
        self._lbl.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )
        self._lbl.setWordWrap(True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lbl)

    def set_parts(self, parts: list):
        filtered = [str(p) for p in parts if p]
        self._lbl.setText(self._separator.join(filtered) if filtered else "")

    def set_text(self, text: str):
        self._lbl.setText(text)

    def label(self) -> QLabel:
        return self._lbl
