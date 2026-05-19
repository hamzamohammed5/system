"""
ui/tabs/orders/dashboard/_top_cards.py
========================================
بناء بطاقات الإحصائيات العلوية في لوحة المتابعة.
"""

from PyQt5.QtWidgets import QHBoxLayout

from ui.widgets.shared.panels import make_stat_card_simple


def build_top_cards(dashboard) -> QHBoxLayout:
    """
    يبني صف البطاقات الإحصائية العلوية ويحفظ references في dashboard.
    يرجع QHBoxLayout جاهز للإضافة.
    """
    row = QHBoxLayout()
    row.setSpacing(12)

    f1, dashboard._lbl_total = make_stat_card_simple(
        "📋", "إجمالي الطلبات", color="#1565c0")
    f2, dashboard._lbl_urgent = make_stat_card_simple(
        "🔴", "عاجل", color="#ef4444")
    f3, dashboard._lbl_total_value = make_stat_card_simple(
        "💰", "إجمالي القيمة", color="#10b981")
    f4, dashboard._lbl_total_paid = make_stat_card_simple(
        "✅", "إجمالي المدفوع", color="#1565c0")

    for f in (f1, f2, f3, f4):
        row.addWidget(f, stretch=1)

    return row