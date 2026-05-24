"""
ui/tabs/accounting/helpers.py
==============================
أدوات مساعدة صغيرة مشتركة بين تبويبات الحسابات.

[تحديث v2]: _stat_card تستخدم stat_card_pair من stat_row بدل كود محلي.
[تحديث v3]: _spin تستخدم spin_field من form_utils بدل تعريف محلي مكرر.
"""

from db.accounting.accounting_schema import TYPE_AR, NORMAL_BALANCE
from ui.font_utils import card_title_style, card_value_style
from ui.widgets.shared.stat_row import stat_card_pair   # ← الموحد
from ui.widgets.shared.form_utils import spin_field     # ← الموحد (بدل التعريف المحلي)


TYPE_COLORS = {
    "asset":    "#1565c0",
    "liability":"#c62828",
    "capital":  "#2e7d32",
    "revenue":  "#6a1b9a",
    "expense":  "#e65100",
    "drawings": "#4e342e",
}


def _spin(max_=999_999_999, dec=2, min_height: int = 30):
    """
    QDoubleSpinBox موحد.
    [تحديث v3]: wrapper حول spin_field للتوافق مع الكود القديم.
    """
    return spin_field(max_=float(max_), dec=dec, min_height=min_height)


def _money(val: float) -> str:
    return f"{val:,.2f}  ج"


def _stat_card(label: str, color: str = "#1565c0"):
    """
    يرجع (QFrame, QLabel_value) — بطاقة إحصائية.
    [تحديث]: يستخدم stat_card_pair الموحدة بدل كود محلي مكرر.
    """
    return stat_card_pair(label=label, color=color)