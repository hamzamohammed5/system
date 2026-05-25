"""
ui/widgets/panels/cards.py
===========================
كل البطاقات الإحصائية والشارات في مكان واحد:

  BadgeLabel    — شارة نصية ملونة
  StatCard      — بطاقة إحصائية مستقلة
  StatusChip    — شريحة حالة (أيقونة + اسم + عدد)
  StatItem      — dataclass لتعريف بطاقة
  _StatCard     — بطاقة خفيفة مضمّنة في StatRow
  StatRow       — صف أفقي من البطاقات
  make_stat_card_simple / make_status_chip / make_stat_row / stat_card_pair
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs, get_font_size


def _base() -> int:
    return get_font_size()


# ── لوحة الألوان ──────────────────────────────────────────

_CARD_PALETTE: dict[str, tuple[str, str]] = {
    "#1565c0": ("#e8f0fe", "#90caf9"),
    "#0d47a1": ("#e3f2fd", "#64b5f6"),
    "#10b981": ("#ecfdf5", "#6ee7b7"),
    "#2e7d32": ("#e8f5e9", "#a5d6a7"),
    "#065f46": ("#ecfdf5", "#a7f3d0"),
    "#15803d": ("#f0fdf4", "#86efac"),
    "#ef4444": ("#fef2f2", "#fca5a5"),
    "#dc2626": ("#fef2f2", "#fca5a5"),
    "#c62828": ("#ffebee", "#ef9a9a"),
    "#f59e0b": ("#fffbeb", "#fcd34d"),
    "#e65100": ("#fff3e0", "#ffcc80"),
    "#6b7280": ("#f9fafb", "#d1d5db"),
    "#9ca3af": ("#f9fafb", "#e5e7eb"),
    "#8b5cf6": ("#f5f3ff", "#c4b5fd"),
    "#6a1b9a": ("#f3e5f5", "#ce93d8"),
    "#db2777": ("#fdf2f8", "#f9a8d4"),
}
_FALLBACK = ("#f5f5f5", "#e0e0e0")


def card_colors(color: str) -> tuple[str, str]:
    return _CARD_PALETTE.get(color, _FALLBACK)


# ══════════════════════════════════════════════════════════
# BadgeLabel
# ══════════════════════════════════════════════════════════

class BadgeLabel(QLabel):
    """شارة نصية ملونة."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._apply("#555", "#f5f5f5", "#e0e0e0")

    def _apply(self, fg: str, bg: str, border: str):
        base = _base()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,-1)}pt;"
            f"padding:3px 12px; border-radius:20px;"
            f"color:{fg}; background:{bg}; border:1.5px solid {border};"
        )

    def set_badge(self, text: str, text_color: str = "#555",
                  bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        self.setText(text)
        self._apply(text_color, bg, border)

    def clear_badge(self):
        self.setText("")
        self._apply("#555", "#f5f5f5", "#e0e0e0")


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
        base = _base()

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
        base = _base()
        self._color = color
        self._lbl_value.setStyleSheet(f"color:{color}; background:transparent; border:none;")
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )

    def value_label(self) -> QLabel:
        return self._lbl_value


# ══════════════════════════════════════════════════════════
# StatusChip
# ══════════════════════════════════════════════════════════

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
        base = _base()
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


def make_stat_card_simple(label: str, value: str = "─",
                           color: str = "#1565c0",
                           icon: str = "") -> StatCard:
    return StatCard(icon=icon, title=label, value=value, color=color)


def make_status_chip(icon: str, label: str, count: int = 0,
                     color: str = "#6b7280") -> StatusChip:
    return StatusChip(icon=icon, label=label, count=count, color=color)


# ══════════════════════════════════════════════════════════
# StatItem + _StatCard + StatRow
# ══════════════════════════════════════════════════════════

@dataclass
class StatItem:
    """تعريف بطاقة إحصائية واحدة لـ StatRow."""
    label      : str
    color      : str            = "#1565c0"
    icon       : str            = ""
    value      : str            = "─"
    bg         : Optional[str]  = None
    border     : Optional[str]  = None
    bold_value : bool           = True
    compact    : bool           = False


class _StatCard(QFrame):
    """بطاقة خفيفة مضمّنة — تُستخدم داخل StatRow فقط."""

    def __init__(self, item: StatItem, parent=None):
        super().__init__(parent)
        self._item = item
        self._build()

    def _build(self):
        bg, border = card_colors(self._item.color)
        if self._item.bg:     bg     = self._item.bg
        if self._item.border: border = self._item.border

        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:1px solid {border}; border-radius:8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QVBoxLayout(self)
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
            "background:transparent; border:none;"
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


def _v_sep(margin_v: int = 4) -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setFixedWidth(1)
    sep.setStyleSheet(
        f"background:{_C.get('border_med','#bdbdbd')}; border:none; margin:{margin_v}px 2px;"
    )
    return sep


class StatRow(QWidget):
    """صف أفقي من البطاقات الإحصائية مع فواصل اختيارية."""

    def __init__(self, items: list[StatItem], separator: bool = True,
                 compact: bool = False, bg: str = None, parent=None):
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
                lay.addWidget(_v_sep())

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


def make_stat_row(*items: StatItem, separator: bool = True,
                  compact: bool = False, bg: str = None) -> StatRow:
    return StatRow(list(items), separator=separator, compact=compact, bg=bg)


def stat_card_pair(label: str, color: str = "#1565c0",
                   icon: str = "") -> tuple[QFrame, QLabel]:
    item = StatItem(label=label, color=color, icon=icon)
    card = _StatCard(item)
    return card, card.value_label()