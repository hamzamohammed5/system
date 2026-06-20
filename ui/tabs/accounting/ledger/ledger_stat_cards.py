"""
ui/tabs/accounting/ledger/ledger_stat_cards.py
================================================
_StatCards — بطاقات الإحصائيات في دفتر الأستاذ.

[تحديث] يستخدم StatRow من widgets/shared بدل _card محلية.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout

from db.accounting.accounting_schema import TYPE_AR
from ui.widgets.components.stat_card import StatRow, StatItem

class _StatCards(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._row = StatRow([
            StatItem("إجمالي المدين",  "#1565c0", icon="📥", compact=True),
            StatItem("إجمالي الدائن",  "#c62828", icon="📤", compact=True),
            StatItem("الرصيد",          "#2e7d32", icon="⚖️",  compact=True),
            StatItem("عدد الحركات",    "#6a1b9a", icon="🔢", compact=True),
            StatItem("الرصيد الطبيعي", "#e65100", icon="📌", compact=True),
        ], separator=True, bg="white")

        lay.addWidget(self._row)

        # مراجع مباشرة للتوافق مع الكود القديم
        self.lbl_dr  = self._row.value_label(0)
        self.lbl_cr  = self._row.value_label(1)
        self.lbl_bal = self._row.value_label(2)
        self.lbl_cnt = self._row.value_label(3)
        self.lbl_nb  = self._row.value_label(4)

    def update(self, total_dr: float, total_cr: float,
               balance: float, count: int, normal_balance: str, acc_type: str):
        self.lbl_dr.setText(f"{total_dr:,.2f}  ج")
        self.lbl_cr.setText(f"{total_cr:,.2f}  ج")

        bal_color = "#2e7d32" if balance >= 0 else "#c62828"
        self._row.set_value(2, f"{abs(balance):,.2f}  ج", bal_color)

        self.lbl_cnt.setText(str(count))

        nb_ar    = "مدين (DR↑)" if normal_balance == "dr" else "دائن (CR↑)"
        type_ar  = TYPE_AR.get(acc_type, "")
        nb_color = "#1565c0" if normal_balance == "dr" else "#c62828"
        self._row.set_value(4, f"{nb_ar} — {type_ar}", nb_color)

    def clear(self):
        self._row.reset_all()