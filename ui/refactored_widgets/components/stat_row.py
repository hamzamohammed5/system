"""
ui/widgets/components/stat_row.py
=============================================
StatItem  — dataclass لتعريف بطاقة إحصائية.
_StatCard — بطاقة خفيفة مضمّنة (للاستخدام الداخلي فقط).
StatRow   — صف أفقي من البطاقات مع فواصل.

الاستخدام:
    row = StatRow([
        StatItem("المبيعات", color="#1565c0", value="150"),
        StatItem("الأرباح",  color="#2e7d32", value="40,000 ج"),
    ])
    row.set_value(0, "200")
    row.set_value_by_label("الأرباح", "50,000 ج", color="#2e7d32")
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont

from ui.app_settings import fs
from ..core.settings import get_base
from ..core.colors   import card_colors
from ..theme.builders import v_divider


# ══════════════════════════════════════════════════════════
# DataClass
# ══════════════════════════════════════════════════════════

@dataclass
class StatItem:
    """تعريف بطاقة إحصائية واحدة."""
    label      : str
    color      : str            = "#1565c0"
    icon       : str            = ""
    value      : str            = "─"
    bg         : Optional[str]  = None
    border     : Optional[str]  = None
    bold_value : bool           = True
    compact    : bool           = False


# ══════════════════════════════════════════════════════════
# _StatCard — بطاقة خفيفة (داخلية)
# ══════════════════════════════════════════════════════════

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
        base = get_base()

        if self._item.compact:
            lay.setContentsMargins(10, 6, 10, 6)
            lay.setSpacing(2)
        else:
            lay.setContentsMargins(14, 10, 14, 10)
            lay.setSpacing(3)

        # صف العنوان + أيقونة
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

        # القيمة
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


# ══════════════════════════════════════════════════════════
# StatRow
# ══════════════════════════════════════════════════════════

class StatRow(QWidget):
    """
    صف أفقي من البطاقات الإحصائية مع فواصل عمودية اختيارية.

    الاستخدام:
        row = StatRow([
            StatItem("المبيعات", color="#1565c0", value="150"),
            StatItem("الأرباح",  color="#2e7d32", value="40,000 ج"),
        ])
        layout.addWidget(row)
        row.set_value(0, "200")
    """

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

    # ── API ──────────────────────────────────────────────

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
    """يبني بطاقة مع label مرجع للتحديث السريع."""
    item = StatItem(label=label, color=color, icon=icon)
    card = _StatCard(item)
    return card, card.value_label()