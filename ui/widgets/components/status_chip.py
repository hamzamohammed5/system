"""
ui/widgets/components/status_chip.py
======================================
StatusChip + StatusCard.

مستخرج من components/stat_row.py.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors import card_colors


class StatusChip(QFrame):
    """شريحة حالة: أيقونة + اسم + عدد."""

    def __init__(self, icon: str = "", label: str = "", count: int = 0,
                 color: str = "#6b7280", bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        _bg, _bdr = card_colors(color)
        self._build(icon, label, count, color,
                    bg or _bg, border or _bdr, compact)

    def _build(self, icon, label, count, color, bg, border, compact):
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:1px solid {border};
                border-radius:8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        base = get_font_size()
        m = (10, 6, 10, 6) if compact else (12, 8, 12, 8)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(*m)
        lay.setSpacing(8)

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("background:transparent; border:none;")
            lay.addWidget(lbl_icon)

        lbl_label = QLabel(label)
        lbl_label.setStyleSheet(
            f"font-weight:600; color:{color}; background:transparent;"
            f"border:none; font-size:{fs(base,0)}pt;"
        )
        lay.addWidget(lbl_label, stretch=1)

        self._lbl_count = QLabel(str(count))
        f = QFont()
        f.setPointSize(fs(base, +1 if compact else +2))
        f.setBold(True)
        self._lbl_count.setFont(f)
        self._lbl_count.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl_count)

    def set_count(self, count: int):
        self._lbl_count.setText(str(count))

    def count(self) -> int:
        try:
            return int(self._lbl_count.text())
        except ValueError:
            return 0


class StatusCard(QFrame):
    """بطاقة حالة بسيطة — أيقونة + label + عدد كبير."""

    def __init__(self, icon: str = "", label: str = "",
                 value: str = "─", color: str = "#1565c0",
                 sub: str = "", parent=None):
        super().__init__(parent)
        _bg, _bdr = card_colors(color)
        self._build(icon, label, value, color, _bg, _bdr, sub)

    def _build(self, icon, label, value, color, bg, border, sub):
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:1px solid {border};
                border-radius:12px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        base = get_font_size()
        top  = QHBoxLayout()

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("background:transparent; border:none;")
        top.addWidget(lbl_icon)
        top.addStretch()

        self._lbl_value = QLabel(value)
        f = QFont()
        f.setPointSize(fs(base, +5))
        f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top.addWidget(self._lbl_value)
        lay.addLayout(top)

        lbl_title = QLabel(label)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:600; font-size:{fs(base,0)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

        if sub:
            lbl_sub = QLabel(sub)
            lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_sub)

    def set_value(self, text: str):
        self._lbl_value.setText(text)

    def value_label(self) -> QLabel:
        return self._lbl_value


def make_status_chip(icon: str, label: str, count: int = 0,
                     color: str = "#6b7280") -> StatusChip:
    return StatusChip(icon=icon, label=label, count=count, color=color)