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

    card1 = make_stat_card_simple(tr("order_total_count"),  color=_C['accent'], icon="📋")
    card2 = make_stat_card_simple(tr("order_urgent_count"), color=_C['danger'], icon="🔴")
    card3 = make_stat_card_simple(tr("order_total_value"),  color=_C['success'], icon="💰")
    card4 = make_stat_card_simple(tr("order_total_paid"),   color=_C['accent'], icon="✅")
    dashboard._lbl_total       = card1.value_label()
    dashboard._lbl_urgent      = card2.value_label()
    dashboard._lbl_total_value = card3.value_label()
    dashboard._lbl_total_paid  = card4.value_label()

    for card in (card1, card2, card3, card4):
        row.addWidget(card, stretch=1)

    return row
