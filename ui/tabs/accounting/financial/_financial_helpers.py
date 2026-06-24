"""
ui/tabs/accounting/financial/_financial_helpers.py
===================================================
دوال مساعدة خاصة بالتبويبات المالية.

مُنقلة من ui/tabs/accounting/helpers.py لأنها تُستخدم
فقط داخل هذا المجلد (financial/).

المتوفر:
  _money(value)  → تنسيق مبلغ مالي كـ string
"""


def _money(value: float) -> str:
    """
    يُنسق مبلغ مالي للعرض في البطاقات الإحصائية.

    مثال:
        _money(1500.5)   → "1,500.50"
        _money(-200.0)   → "-200.00"
        _money(0)        → "─"
    """
    if value == 0:
        from ui.widgets.core.i18n import tr
        return tr("amount_dash_placeholder")
    return f"{value:,.2f}"