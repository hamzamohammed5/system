"""
ui/widgets/components/stat_card.py
=====================================
بطاقات إحصائية.

مستخرج من components/stat_row.py:
  StatItem, StatCard, _StatCard, StatRow,
  make_stat_row, stat_card_pair, make_stat_card_simple
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors   import card_colors
from ..theme.builders import v_divider
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    MARGIN_ZERO,
    STAT_CARD_MARGIN_COMPACT, STAT_CARD_MARGIN_NORMAL,
    STAT_CARD_SPACING_COMPACT, STAT_CARD_SPACING_NORMAL,
    STAT_CARD_BORDER_RADIUS,
    STAT_INNER_MARGIN_COMPACT, STAT_INNER_MARGIN_NORMAL,
    STAT_INNER_TOP_SPACING, STAT_INNER_BORDER_RADIUS,
)

# ══════════════════════════════════════════════════════════
# StatCard — بطاقة مستقلة كاملة
# ══════════════════════════════════════════════════════════

class StatCard(QFrame, WidgetMixin):
    """بطاقة إحصائية مستقلة — للـ detail headers."""

    def __init__(self, icon: str = "", title: str = "",
                 value: str = "─", color: str = None,
                 bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._custom_color = color
        self._color   = color or _C["blue"]
        self._custom_bg     = bg
        self._custom_border = border
        self._compact = compact
        self._title   = title
        self._icon    = icon
        self._build(icon, title, value)
        self._init_widget_mixin(theme=True, font=True)
        self._refresh_style()

    def _build(self, icon, title, value):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)

        if self._compact:
            lay.setContentsMargins(*STAT_CARD_MARGIN_COMPACT)
            lay.setSpacing(STAT_CARD_SPACING_COMPACT)
        else:
            lay.setContentsMargins(*STAT_CARD_MARGIN_NORMAL)
            lay.setSpacing(STAT_CARD_SPACING_NORMAL)

        top = QHBoxLayout()
        self._lbl_title = QLabel(title)
        top.addWidget(self._lbl_title)
        top.addStretch()

        self._lbl_icon = None
        if icon:
            self._lbl_icon = QLabel(icon)
            self._lbl_icon.setStyleSheet("background:transparent; border:none;")
            top.addWidget(self._lbl_icon)

        lay.addLayout(top)

        self._lbl_value = QLabel(value)
        self._lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._lbl_value)

    def _refresh_style(self, *_):
        if self._custom_color is None:
            self._color = _C["blue"]
        _bg, _bdr = card_colors(self._color)
        if self._custom_bg:     _bg  = self._custom_bg
        if self._custom_border: _bdr = self._custom_border

        self.setStyleSheet(f"""
            QFrame {{
                background:{_bg}; border:1px solid {_bdr};
                border-radius:{STAT_CARD_BORDER_RADIUS}px;
            }}
        """)

        base = get_font_size()

        self._lbl_title.setStyleSheet(
            f"color:{self._color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )

        f = QFont()
        f.setPointSize(fs(base, +1 if self._compact else +3))
        f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{self._color}; background:transparent; border:none;"
        )

    def set_value(self, text: str):
        self._lbl_value.setText(text)

    def set_color(self, color: str):
        self._custom_color = color
        self._color = color
        self._refresh_style()

    def value_label(self) -> QLabel:
        return self._lbl_value


# ══════════════════════════════════════════════════════════
# StatItem + _StatCard + StatRow
# ══════════════════════════════════════════════════════════

@dataclass
class StatItem:
    """تعريف بطاقة إحصائية واحدة."""
    label      : str
    color      : str           = field(default_factory=lambda: _C["blue"])
    icon       : str           = ""
    value      : str           = "─"
    bg         : Optional[str] = None
    border     : Optional[str] = None
    bold_value : bool          = True
    compact    : bool          = False


class _StatCard(QFrame, WidgetMixin):
    """بطاقة إحصائية خفيفة — تُستخدم داخل StatRow فقط."""

    def __init__(self, item: StatItem, parent=None):
        super().__init__(parent)
        self._item = item
        self._current_color = item.color
        self._lbl_value: QLabel = None  # type: ignore
        self._build()
        self._init_widget_mixin(theme=True, font=True)
        self._refresh_style()

    def _build(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)

        if self._item.compact:
            lay.setContentsMargins(*STAT_INNER_MARGIN_COMPACT)
            lay.setSpacing(STAT_CARD_SPACING_COMPACT)
        else:
            lay.setContentsMargins(*STAT_INNER_MARGIN_NORMAL)
            lay.setSpacing(STAT_CARD_SPACING_NORMAL)

        top = QHBoxLayout()
        top.setSpacing(STAT_INNER_TOP_SPACING)

        self._lbl_icon = None
        if self._item.icon:
            self._lbl_icon = QLabel(self._item.icon)
            self._lbl_icon.setStyleSheet("background:transparent; border:none;")
            top.addWidget(self._lbl_icon)

        self._lbl_label = QLabel(self._item.label)
        self._lbl_label.setWordWrap(True)
        top.addWidget(self._lbl_label, stretch=1)
        lay.addLayout(top)

        self._lbl_value = QLabel(self._item.value)
        self._lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._lbl_value)

    def _refresh_style(self, *_):
        bg, border = card_colors(self._item.color)
        if self._item.bg:     bg     = self._item.bg
        if self._item.border: border = self._item.border

        self.setStyleSheet(f"""
            QFrame {{
                background:{bg};
                border:1px solid {border};
                border-radius:{STAT_INNER_BORDER_RADIUS}px;
            }}
        """)

        base = get_font_size()

        self._lbl_label.setStyleSheet(
            f"color:{self._item.color}; font-size:{fs(base,-2)}pt; font-weight:600;"
            "background:transparent; border:none; letter-spacing:0.1px;"
        )

        f = QFont()
        f.setPointSize(fs(base, +1 if self._item.compact else +3))
        if self._item.bold_value:
            f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{self._current_color}; background:transparent; border:none;"
        )

    def set_value(self, text: str, color: str = None):
        self._lbl_value.setText(text)
        self._current_color = color or self._item.color
        self._lbl_value.setStyleSheet(
            f"color:{self._current_color}; background:transparent; border:none;"
        )

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
        lay.setContentsMargins(*MARGIN_ZERO)
        lay.setSpacing(0)

        for i, item in enumerate(self._items):
            if compact:
                item.compact = True
            card = _StatCard(item)
            self._cards.append(card)
            lay.addWidget(card, stretch=1)
            if separator and i < len(self._items) - 1:
                lay.addWidget(v_divider(margin_v=STAT_INNER_TOP_SPACING))

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


def stat_card_pair(label: str, color: str = None,
                   icon: str = "") -> tuple[QFrame, QLabel]:
    item = StatItem(label=label, color=color or _C["blue"], icon=icon)
    card = _StatCard(item)
    return card, card.value_label()


def make_stat_card_simple(label: str, value: str = "─",
                           color: str = None,
                           icon: str = "") -> StatCard:
    return StatCard(icon=icon, title=label, value=value, color=color or _C["blue"])