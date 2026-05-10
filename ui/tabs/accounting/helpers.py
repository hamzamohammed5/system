"""
ui/tabs/accounting/helpers.py
==============================
أدوات مساعدة صغيرة مشتركة بين تبويبات الحسابات.
"""

from PyQt5.QtWidgets import QDoubleSpinBox, QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore    import Qt

from db.accounting_schema import TYPE_AR, NORMAL_BALANCE


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
    s.setMinimumHeight(30)
    return s


def _money(val: float) -> str:
    return f"{val:,.2f}  ج"


def _stat_card(label: str, color: str = "#1565c0"):
    """يرجع (QFrame, QLabel_value)."""
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{ background:white; border-left:4px solid {color}; border-radius:6px; }}
    """)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(12, 8, 12, 8)
    lt = QLabel(label)
    lt.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lv = QLabel("0.00  ج")
    lv.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        " background:transparent; border:none;"
    )
    lay.addWidget(lt)
    lay.addWidget(lv)
    return f, lv