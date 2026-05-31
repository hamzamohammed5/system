"""
ui/widgets/components/stat_card.py
=====================================
بطاقات إحصائية.

مستخرج من components/stat_row.py:
  StatItem, StatCard, _StatCard, StatRow,
  make_stat_row, stat_card_pair, make_stat_card_simple
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors   import card_colors
from ..theme.styles  import v_divider


# ══════════════════════════════════════════════════════════
# StatCard — بطاقة مستقلة كاملة
# ══════════════════════════════════════════════════════════

class StatCard(QFrame):
    """بطاقة إحصائية مستقلة — للـ detail headers."""

    def __init__(self, icon: str = "", title: str = "",
                 value: str = "─", color: str = "#1565c0",
                 bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color   = color
        self._compact = compact
        self._build(icon, title, value, color, bg, border)

    def _build(self, icon, title, value, color, bg, border):
        _bg, _bdr = card_colors(color)
        if bg:     _bg  = bg
        if border: _bdr = border

        self.setStyleSheet(f"""
            QFrame {{
                background:{_bg}; border:1px solid {_bdr};
                border-radius:10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QVBoxLayout(self)
        base = get_font_size()

        if self._compact:
            lay.setContentsMargins(10, 8, 10, 8)
            lay.setSpacing(2)
        else:
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(3)

        top = QHBoxLayout()
        self._lbl_title = QLabel(title)
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )
        top.addWidget(self._lbl_title)
        top.addStretch()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("background:transparent; border:none;")
            top.addWidget(lbl_icon)

        lay.addLayout(top)

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
        base = get_font_size()
        self._color = color
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )

    def value_label(self) -> QLabel:
        return self._lbl_value


# ══════════════════════════════════════════════════════════
# StatItem + _StatCard + StatRow
# ══════════════════════════════════════════════════════════

@dataclass
class StatItem:
    """تعريف بطاقة إحصائية واحدة."""
    label      : str
    color      : str           = "#1565c0"
    icon       : str           = ""
    value      : str           = "─"
    bg         : Optional[str] = None
    border     : Optional[str] = None
    bold_value : bool          = True
    compact    : bool          = False


class _StatCard(QFrame):
    """بطاقة إحصائية خفيفة — تُستخدم داخل StatRow فقط."""

    def __init__(self, item: StatItem, parent=None):
        super().__init__(parent)
        self._item = item
        self._lbl_value: QLabel = None  # type: ignore
        self._build()

    def _build(self):
        bg, border = card_colors(self._item.color)
        if self._item.bg:     bg     = self._item.bg
        if self._item.border: border = self._item.border

        self.setStyleSheet(f"""
            QFrame {{
                background:{bg};
                border:1px solid {border};
                border-radius:8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QVBoxLayout(self)
        base = get_font_size()

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
        f.setPointSize(fs(base, +1 if self._item.compact else +3))
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
        self._lbl_value.setStyleSheet(f"color:{c}; background:transparent; border:none;")

    def value_label(self) -> QLabel:
        return self._lbl_value


class StatRow(QWidget):
    """صف أفقي من البطاقات الإحصائية مع فواصل عمودية اختيارية."""

    def __init__(self, items: list[StatItem],
                 separator: bool = True,
                 compact: bool = False,
                 bg: str = None,
                 parent=None):
        super().__init__(parent)
        self._cards: list[_StatCard] = []
        self._items = items
        self._build(separator, compact, bg)

    def _build(self, separator: bool, compact: bool, bg: str):
        self.setStyleSheet(f"background:{bg};" if bg else "background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        for i, item in enumerate(self._items):
            if compact:
                item.compact = True
            card = _StatCard(item)
            self._cards.append(card)
            lay.addWidget(card, stretch=1)
            if separator and i < len(self._items) - 1:
                lay.addWidget(v_divider(margin_v=4))

    def set_value(self, index: int, text: str, color: str = None):
        if 0 <= index < len(self._cards):
            self._cards[index].set_value(text, color)

    def set_value_by_label(self, label: str, text: str, color: str = None):
        for i, item in enumerate(self._items):
            if item.label == label:
                self._cards[i].set_value(text, color)
                return

    def value_label(self, index: int) -> QLabel:
        if 0 <= index < len(self._cards):
            return self._cards[index].value_label()
        return QLabel()

    def reset_all(self):
        for card in self._cards:
            card.set_value("─")

    def update_all(self, values: dict):
        for label, text in values.items():
            self.set_value_by_label(label, text)

    def card(self, index: int) -> _StatCard | None:
        return self._cards[index] if 0 <= index < len(self._cards) else None


# ── دوال مساعدة ───────────────────────────────────────────

def make_stat_row(*items: StatItem,
                  separator: bool = True,
                  compact: bool = False,
                  bg: str = None) -> StatRow:
    return StatRow(list(items), separator=separator, compact=compact, bg=bg)


def stat_card_pair(label: str, color: str = "#1565c0",
                   icon: str = "") -> tuple[QFrame, QLabel]:
    item = StatItem(label=label, color=color, icon=icon)
    card = _StatCard(item)
    return card, card.value_label()


def make_stat_card_simple(label: str, value: str = "─",
                           color: str = "#1565c0",
                           icon: str = "") -> StatCard:
    return StatCard(icon=icon, title=label, value=value, color=color)