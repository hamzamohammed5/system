"""
ui/tabs/orders/dashboard/_top_cards.py
"""
from PyQt5.QtWidgets import QHBoxLayout
from ui.widgets.components.stat_card import make_stat_card_simple
from ui.widgets.core.i18n import tr
from ui.theme import _C


def build_top_cards(dashboard) -> QHBoxLayout:
    """
    يبني صف البطاقات الإحصائية العلوية ويحفظ references في dashboard.
    يرجع QHBoxLayout جاهز للإضافة.
    """
    row = QHBoxLayout()
    row.setSpacing(12)

    f1, dashboard._lbl_total = make_stat_card_simple(
        "📋", tr("order_total_count"),  color=_C['accent'])
    f2, dashboard._lbl_urgent = make_stat_card_simple(
        "🔴", tr("order_urgent_count"), color=_C['danger'])
    f3, dashboard._lbl_total_value = make_stat_card_simple(
        "💰", tr("order_total_value"),  color=_C['success'])
    f4, dashboard._lbl_total_paid = make_stat_card_simple(
        "✅", tr("order_total_paid"),   color=_C['accent'])

    for f in (f1, f2, f3, f4):
        row.addWidget(f, stretch=1)

    return row
