"""
ui/widgets/shared/stat_row.py
==============================
StatRow — صف بطاقات إحصائية أفقية موحد.

[تحديث v2]:
  - _StatCard مستخرجة لـ stat_card_row.py لتسهيل الصيانة
  - StatRow._make_sep() تستخدم make_vline_sep() من divider_utils
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QLabel, QSizePolicy,
)

from ui.app_settings import _C
from ui.widgets.shared.panles_helper.stat_card_row import _StatCard  # noqa: F401 — re-exported


# ══════════════════════════════════════════════════════════
# DataClass لتعريف بطاقة واحدة
# ══════════════════════════════════════════════════════════

@dataclass
class StatItem:
    """تعريف بطاقة إحصائية واحدة."""
    label      : str
    color      : str   = "#1565c0"
    icon       : str   = ""
    value      : str   = "─"
    bg         : Optional[str] = None
    border     : Optional[str] = None
    bold_value : bool  = True
    compact    : bool  = False


# ══════════════════════════════════════════════════════════
# StatRow — الصف الكامل
# ══════════════════════════════════════════════════════════

class StatRow(QWidget):
    """
    صف أفقي من البطاقات الإحصائية مع فواصل عمودية.

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
        self._separator = separator
        self._compact = compact
        self._build(bg)

    def _build(self, bg: str):
        if bg:
            self.setStyleSheet(f"background:{bg};")
        else:
            self.setStyleSheet("background:transparent;")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        for i, item in enumerate(self._items):
            if self._compact:
                item.compact = True

            card = _StatCard(item)
            self._cards.append(card)
            lay.addWidget(card, stretch=1)

            if self._separator and i < len(self._items) - 1:
                lay.addWidget(self._make_sep())

    @staticmethod
    def _make_sep() -> QFrame:
        from ui.widgets.shared.panles_helper.divider_utils import make_vline_sep
        return make_vline_sep(margin_v=4)

    # ── API ───────────────────────────────────────────────

    def set_value(self, index: int, text: str, color: str = None):
        """يحدّث قيمة بطاقة بالـ index."""
        if 0 <= index < len(self._cards):
            self._cards[index].set_value(text, color)

    def set_value_by_label(self, label: str, text: str, color: str = None):
        """يحدّث قيمة بطاقة بالـ label."""
        for i, item in enumerate(self._items):
            if item.label == label:
                self._cards[i].set_value(text, color)
                return

    def value_label(self, index: int) -> QLabel:
        """يرجع QLabel القيمة للتحديث المباشر."""
        if 0 <= index < len(self._cards):
            return self._cards[index].value_label()
        return QLabel()

    def reset_all(self):
        """يعيد كل البطاقات لـ '─'."""
        for card in self._cards:
            card.set_value("─")

    def update_all(self, values: dict):
        """يحدّث قيم بالـ {label: value}."""
        for label, text in values.items():
            self.set_value_by_label(label, text)

    def card(self, index: int) -> _StatCard | None:
        """يرجع _StatCard بالـ index."""
        return self._cards[index] if 0 <= index < len(self._cards) else None


# ══════════════════════════════════════════════════════════
# دوال مساعدة للتوافق مع الكود القديم
# ══════════════════════════════════════════════════════════

def make_stat_row(*items: StatItem,
                  separator: bool = True,
                  compact: bool = False,
                  bg: str = None) -> StatRow:
    """دالة سريعة لبناء StatRow."""
    return StatRow(list(items), separator=separator, compact=compact, bg=bg)


def stat_card_pair(label: str, color: str = "#1565c0",
                   icon: str = "") -> tuple[QFrame, QLabel]:
    """
    يبني بطاقة + label مرجع للتحديث السريع.

    الاستخدام:
        frame, lbl = stat_card_pair("التكلفة", "#1565c0")
        layout.addWidget(frame)
        lbl.setText("250.00 ج")
    """
    item  = StatItem(label=label, color=color, icon=icon)
    card  = _StatCard(item)
    return card, card.value_label()