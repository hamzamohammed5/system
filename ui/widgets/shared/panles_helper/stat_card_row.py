"""
ui/widgets/shared/panles_helper/stat_card_row.py
=================================================
_StatCard داخلية لـ StatRow — مفصولة لتسهيل الصيانة.

[ملاحظة]: هذه _StatCard مختلفة عن StatCard في stat_card.py:
  - StatCard : بطاقة مستقلة كاملة (في detail headers)
  - _StatCard : بطاقة خفيفة مضمّنة جوه StatRow فقط

لا تستورد مباشرة — تُستخدم من stat_row.py فقط.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import fs
from .colors_and_base import _base, _card_colors


class _StatCard(QFrame):
    """بطاقة إحصائية خفيفة مُضمَّنة جوه StatRow."""

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._item = item
        self._build()

    def _build(self):
        bg, border = _card_colors(self._item.color)
        if self._item.bg:
            bg = self._item.bg
        if self._item.border:
            border = self._item.border

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        base = _base()

        if self._item.compact:
            lay.setContentsMargins(10, 6, 10, 6)
            lay.setSpacing(2)
        else:
            lay.setContentsMargins(14, 10, 14, 10)
            lay.setSpacing(3)

        top = QHBoxLayout()
        top.setSpacing(4)

        if self._item.icon:
            lbl_icon = QLabel(self._item.icon)
            lbl_icon.setStyleSheet("background:transparent; border:none;")
            top.addWidget(lbl_icon)

        lbl_label = QLabel(self._item.label)
        lbl_label.setStyleSheet(
            f"color:{self._item.color}; font-size:{fs(base,-2)}pt; font-weight:600;"
            "background:transparent; border:none; letter-spacing:0.1px;"
        )
        lbl_label.setWordWrap(True)
        top.addWidget(lbl_label, stretch=1)
        lay.addLayout(top)

        self._lbl_value = QLabel(self._item.value)
        f = QFont()
        sz = fs(base, +1) if self._item.compact else fs(base, +3)
        f.setPointSize(sz)
        if self._item.bold_value:
            f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{self._item.color}; background:transparent; border:none;"
        )
        self._lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._lbl_value)

    def set_value(self, text: str, color: str = None):
        self._lbl_value.setText(text)
        c = color or self._item.color
        self._lbl_value.setStyleSheet(
            f"color:{c}; background:transparent; border:none;"
        )

    def value_label(self) -> QLabel:
        return self._lbl_value