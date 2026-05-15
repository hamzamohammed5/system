"""
ui/tabs/accounting/helpers.py
==============================
أدوات مساعدة صغيرة مشتركة بين تبويبات الحسابات.
- stat cards بأحجام نسبية من حجم الخط الأساسي
"""

from PyQt5.QtWidgets import QDoubleSpinBox, QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore    import Qt

from db.accounting.accounting_schema import TYPE_AR, NORMAL_BALANCE
from ui.font_utils import card_title_style, card_value_style


TYPE_COLORS = {
    "asset":    "#1565c0",
    "liability":"#c62828",
    "capital":  "#2e7d32",
    "revenue":  "#6a1b9a",
    "expense":  "#e65100",
    "drawings": "#4e342e",
}


def _spin(max_=999_999_999, dec=2) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    return s


def _money(val: float) -> str:
    return f"{val:,.2f}  ج"


def _stat_card(label: str, color: str = "#1565c0"):
    """يرجع (QFrame, QLabel_value) — بطاقة إحصائية بأحجام نسبية."""
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: white;
            border-left: 4px solid {color};
            border-radius: 6px;
        }}
    """)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(2)

    lt = QLabel(label)
    # حجم صغير للعنوان — يأتي من الـ stylesheet العام عبر card-title
    lt.setStyleSheet(card_title_style())

    lv = QLabel("0.00  ج")
    # حجم أكبر للقيمة — نسبي
    lv.setStyleSheet(card_value_style(color))

    lay.addWidget(lt)
    lay.addWidget(lv)
    return f, lv