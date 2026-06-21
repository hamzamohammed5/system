"""
ui/tabs/accounting/ledger/ledger_stat_cards.py
================================================
_StatCards — بطاقات الإحصائيات في دفتر الأستاذ.

[تحديث] يستخدم StatRow من widgets/shared بدل _card محلية.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout

from db.accounting.accounting_schema import TYPE_AR
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.core.i18n import tr
from ui.theme import _C

class _StatCards(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border_med']};
                border-radius: 8px;
            }}
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._row = StatRow([
            StatItem(tr("total_debit"),  _C["acc_type_asset"],     icon="📥", compact=True),
            StatItem(tr("total_credit"), _C["acc_type_liability"], icon="📤", compact=True),
            StatItem(tr("balance"),      _C["acc_type_capital"],   icon="⚖️",  compact=True),
            StatItem(tr("ledger_movements_count"),     _C["acc_type_revenue"], icon="🔢", compact=True),
            StatItem(tr("ledger_normal_balance_card"), _C["acc_type_expense"], icon="📌", compact=True),
        ], separator=True, bg=_C["bg_surface"])

        lay.addWidget(self._row)

        # مراجع مباشرة للتوافق مع الكود القديم
        self.lbl_dr  = self._row.value_label(0)
        self.lbl_cr  = self._row.value_label(1)
        self.lbl_bal = self._row.value_label(2)
        self.lbl_cnt = self._row.value_label(3)
        self.lbl_nb  = self._row.value_label(4)

    def update(self, total_dr: float, total_cr: float,
               balance: float, count: int, normal_balance: str, acc_type: str):
        currency = tr("currency_sym")
        self.lbl_dr.setText(f"{total_dr:,.2f}  {currency}")
        self.lbl_cr.setText(f"{total_cr:,.2f}  {currency}")

        bal_color = _C["acc_type_capital"] if balance >= 0 else _C["acc_type_liability"]
        self._row.set_value(2, f"{abs(balance):,.2f}  {currency}", bal_color)

        self.lbl_cnt.setText(str(count))

        nb_ar    = tr("ledger_card_nb_dr") if normal_balance == "dr" else tr("ledger_card_nb_cr")
        type_ar  = TYPE_AR.get(acc_type, "")
        nb_color = _C["acc_type_asset"] if normal_balance == "dr" else _C["acc_type_liability"]
        self._row.set_value(4, f"{nb_ar} — {type_ar}", nb_color)

    def clear(self):
        self._row.reset_all()