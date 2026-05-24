"""
ui/widgets/shared/stat_row.py
==============================
StatRow — صف بطاقات إحصائية أفقية موحد.

يحل محل الكود المكرر في:
  - ledger_stat_cards.py  (_card محلية)
  - accounting/helpers.py (_stat_card)
  - scenario_comparison_widget.py (_stat_card محلية)
  - investors/_investor_details.py (_stat_card)

الاستخدام:
    from ui.widgets.shared.stat_row import StatRow, StatItem

    row = StatRow([
        StatItem("📥", "إجمالي المدين",  color="#1565c0"),
        StatItem("📤", "إجمالي الدائن",  color="#c62828"),
        StatItem("⚖️", "الرصيد",          color="#2e7d32"),
    ])
    layout.addWidget(row)

    # تحديث القيم:
    row.set_value(0, "1,500.00  ج")
    row.set_value(1, "900.00  ج")
    row.set_value(2, "600.00  ج")

    # أو بـ dict:
    row.update_all({"إجمالي المدين": "1,500.00  ج", ...})
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base, _card_colors


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
# بطاقة واحدة داخلية
# ══════════════════════════════════════════════════════════

class _StatCard(QFrame):
    """
    بطاقة إحصائية واحدة — مستخدمة داخلياً من StatRow.

    الفرق عن StatCard في panles_helper/stat_card.py:
      - أبسط (بدون icon row منفصل)
      - مصممة للتضمين في صف أفقي
      - تدعم separator عمودي بين البطاقات
    """

    def __init__(self, item: StatItem, parent=None):
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

        # صف الأيقونة + العنوان
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


# ══════════════════════════════════════════════════════════
# StatRow — الصف الكامل
# ══════════════════════════════════════════════════════════

class StatRow(QWidget):
    """
    صف أفقي من البطاقات الإحصائية مع فواصل عمودية.

    المعاملات:
        items      : قائمة StatItem
        separator  : هل يظهر فاصل بين البطاقات
        compact    : حجم أصغر لكل البطاقات
        bg         : لون خلفية الحاوية (None = شفاف)
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
                sep = self._make_sep()
                lay.addWidget(sep)

    @staticmethod
    def _make_sep() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(
            f"background:{_C['border']}; border:none; margin:4px 6px;"
        )
        return sep

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
        """يرجع الـ QLabel للقيمة للتحديث المباشر."""
        if 0 <= index < len(self._cards):
            return self._cards[index].value_label()
        return QLabel()

    def reset_all(self):
        """يعيد كل القيم لـ '─'."""
        for card in self._cards:
            card.set_value("─")

    def update_all(self, values: dict):
        """
        يحدّث قيم متعددة دفعة واحدة.

        values: {label: value_text, ...}
        """
        for label, text in values.items():
            self.set_value_by_label(label, text)

    def card(self, index: int) -> _StatCard:
        """الوصول المباشر لبطاقة."""
        return self._cards[index] if 0 <= index < len(self._cards) else None


# ══════════════════════════════════════════════════════════
# دوال مساعدة للتوافق مع الكود القديم
# ══════════════════════════════════════════════════════════

def make_stat_row(*items: StatItem,
                  separator: bool = True,
                  compact: bool = False,
                  bg: str = None) -> StatRow:
    """
    دالة مساعدة لبناء StatRow بشكل سريع.

    الاستخدام:
        row = make_stat_row(
            StatItem("📥", "المدين",  "#1565c0"),
            StatItem("📤", "الدائن",  "#c62828"),
            StatItem("⚖️", "الرصيد",  "#2e7d32"),
        )
    """
    return StatRow(list(items), separator=separator, compact=compact, bg=bg)


def stat_card_pair(label: str, color: str = "#1565c0",
                   icon: str = "") -> tuple[QFrame, QLabel]:
    """
    بديل لـ _stat_card() في accounting/helpers.py و scenario_comparison_widget.py.

    يرجع (QFrame, QLabel_value) للتوافق مع الكود القديم.

    الاستخدام:
        frame, lbl = stat_card_pair("إجمالي المدين", "#1565c0", "📥")
        layout.addWidget(frame)
        lbl.setText("1,500.00  ج")
    """
    item  = StatItem(label=label, color=color, icon=icon)
    card  = _StatCard(item)
    return card, card.value_label()