"""
ui/widgets/shared/components/card.py
=======================================
StatCard  — بطاقة إحصائية مستقلة (في detail headers).
StatusCard — بطاقة حالة بسيطة.

ملاحظة: _StatCard الخفيفة (لـ StatRow) موجودة في stat_row.py
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import fs
from ui.widgets.shared.core.settings import get_base
from ui.widgets.shared.core.colors   import card_colors


class StatCard(QFrame):
    """بطاقة إحصائية كاملة — تُستخدم في detail headers."""

    def __init__(self, icon: str = "", title: str = "",
                 value: str = "─", color: str = "#1565c0",
                 bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color   = color
        self._compact = compact
        self._build(icon, title, value, color, bg, border)

    def _build(self, icon, title, value, color, bg, border):
        _bg, _border = card_colors(color)
        if bg:     _bg     = bg
        if border: _border = border

        self.setStyleSheet(f"""
            QFrame {{
                background:{_bg}; border:1px solid {_border};
                border-radius:10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QVBoxLayout(self)
        base = get_base()

        if self._compact:
            lay.setContentsMargins(10, 8, 10, 8)
            lay.setSpacing(2)
        else:
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(0)

        self._lbl_title = QLabel(title)
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none; letter-spacing:0.2px;"
        )
        top_row.addWidget(self._lbl_title)
        top_row.addStretch()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(
                f"font-size:{fs(base, +1 if self._compact else +2)}pt;"
                "background:transparent; border:none;"
            )
            top_row.addWidget(lbl_icon)

        lay.addLayout(top_row)

        self._lbl_value = QLabel(value)
        f = QFont()
        f.setPointSize(fs(base, +1 if self._compact else +3))
        f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._lbl_value)

    def set_value(self, text: str):
        self._lbl_value.setText(text)

    def set_color(self, color: str):
        self._color = color
        base = get_base()
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )

    def value_label(self) -> QLabel:
        return self._lbl_value


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

        base = get_base()
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
            from ui.app_settings import _C
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