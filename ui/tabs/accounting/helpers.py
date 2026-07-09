"""
ui/tabs/accounting/helpers.py
==============================
أدوات مساعدة صغيرة مشتركة بين تبويبات الحسابات.

[تحديث v2]: _stat_card تستخدم stat_card_pair من stat_row بدل كود محلي.
[تحديث v3]: _spin تستخدم spin_field من form_utils بدل تعريف محلي مكرر.
[تحديث v4]: _get_type_colors تقرأ من _C دائماً — لا hardcoded.
             TYPE_COLORS يُحدَّث عند كل استدعاء _get_type_colors().
"""

from ui.widgets.components.stat_card import stat_card_pair
from ui.widgets.panels.form_fields import spin_field
from ui.theme import _C
from ui.widgets.core.i18n import tr


def _get_type_colors() -> dict:
    """ألوان أنواع الحسابات — تُقرأ من _C دائماً لدعم الثيمات."""
    return {
        "asset":    _C["acc_type_asset"],
        "liability":_C["acc_type_liability"],
        "capital":  _C["acc_type_capital"],
        "revenue":  _C["acc_type_revenue"],
        "expense":  _C["acc_type_expense"],
        "drawings": _C["acc_type_drawings"],
    }


# للتوافق مع الكود الذي يستورد TYPE_COLORS مباشرة
# استخدم _get_type_colors() مباشرة في الكود الجديد
TYPE_COLORS = _get_type_colors()


def _spin(max_=999_999_999, dec=2, min_height: int = 30):
    """
    QDoubleSpinBox موحد.
    [تحديث v3]: wrapper حول spin_field للتوافق مع الكود القديم.
    """
    return spin_field(max_=float(max_), dec=dec, min_height=min_height)


def _money(val: float) -> str:
    return f"{val:,.2f}  {tr('currency_abbr')}"


def _stat_card(label: str, color: str = None):
    """
    يرجع (QFrame, QLabel_value) — بطاقة إحصائية.
    [تحديث]: يستخدم stat_card_pair الموحدة بدل كود محلي مكرر.
    """
    return stat_card_pair(label=label, color=color or _C["accent"])