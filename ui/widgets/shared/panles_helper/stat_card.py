"""
ui/widgets/shared/panles_helper/stat_card.py
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.app_settings import fs
from .colors_and_base import _card_colors, _base


class StatCard(QFrame):
    def __init__(self, icon: str = "", title: str = "",
                 value: str = "─", color: str = "#1565c0",
                 bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color   = color
        self._compact = compact
        self._build(icon, title, value, color, bg, border)

    def _build(self, icon, title, value, color, bg, border):
        _bg, _border = _card_colors(color)
        if bg:     _bg = bg
        if border: _border = border

        self.setStyleSheet(f"""
            QFrame {{
                background: {_bg};
                border: 1px solid {_border};
                border-radius: 10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QVBoxLayout(self)
        base = _base()

        if self._compact:
            lay.setContentsMargins(10, 8, 10, 8)
            lay.setSpacing(2)
        else:
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(0)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none; letter-spacing:0.2px;"
        )
        top_row.addWidget(lbl_title)
        top_row.addStretch()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(
                f"font-size:{fs(base,+1) if self._compact else fs(base,+2)}pt;"
                "background:transparent; border:none;"
            )
            top_row.addWidget(lbl_icon)

        lay.addLayout(top_row)

        self._lbl_value = QLabel(value)
        f = QFont()
        f.setPointSize(fs(base, +1) if self._compact else fs(base, +3))
        f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._lbl_value)

        self._lbl_title = lbl_title

    def set_value(self, text: str):
        self._lbl_value.setText(text)

    def set_color(self, color: str):
        self._color = color
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(_base(),-1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )

    def value_label(self) -> QLabel:
        return self._lbl_value