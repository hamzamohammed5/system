"""
ui/tabs/accounting/helpers.py
==============================
أدوات مساعدة صغيرة مشتركة بين تبويبات الحسابات.

- stat cards بأحجام نسبية من حجم الخط الأساسي
- _spin / _money مشتركة
- TYPE_COLORS
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


def _spin(max_=999_999_999, dec=2, min_height: int = 30) -> QDoubleSpinBox:
    """
    QDoubleSpinBox موحد — يُستخدم في helpers و investors وكل تبويبات الحسابات.

    Parameters
    ----------
    max_ : الحد الأقصى للقيمة
    dec  : عدد الخانات العشرية
    min_height : الارتفاع الأدنى للعنصر
    """
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(min_height)
    return s


def _money(val: float) -> str:
    return f"{val:,.2f}  ج"


def _stat_card(label: str, color: str = "#1565c0"):
    """
    يرجع (QFrame, QLabel_value) — بطاقة إحصائية بأحجام نسبية.

    يُستخدم في:
      - accounting/helpers.py (هنا)
      - investors/_helpers.py  (يستدعي من هنا)
      - financial tabs
    """
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
    lt.setStyleSheet(card_title_style())

    lv = QLabel("0.00  ج")
    lv.setStyleSheet(card_value_style(color))

    lay.addWidget(lt)
    lay.addWidget(lv)
    return f, lv