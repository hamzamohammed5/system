"""
ui/tabs/accounting/ledger/ledger_stat_cards.py
================================================
_StatCards — بطاقات الإحصائيات في دفتر الأستاذ.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QWidget, QLabel,
)
from PyQt5.QtCore import Qt

from db.accounting_schema import TYPE_AR


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
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(0)

        def _card(icon, label, color):
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            wl = QVBoxLayout(w)
            wl.setContentsMargins(12, 4, 12, 4)
            wl.setSpacing(2)
            lbl_t = QLabel(f"{icon}  {label}")
            lbl_t.setStyleSheet(
                "font-size:10px; color:#888; background:transparent; border:none;"
            )
            lbl_v = QLabel("─")
            lbl_v.setStyleSheet(
                f"font-size:14px; font-weight:bold; color:{color};"
                "background:transparent; border:none;"
            )
            wl.addWidget(lbl_t)
            wl.addWidget(lbl_v)
            return w, lbl_v

        def _sep():
            s = QFrame()
            s.setFrameShape(QFrame.VLine)
            s.setStyleSheet("color:#e0e0e0; background:#e0e0e0;")
            s.setFixedWidth(1)
            return s

        w1, self.lbl_dr   = _card("📥", "إجمالي المدين",   "#1565c0")
        w2, self.lbl_cr   = _card("📤", "إجمالي الدائن",   "#c62828")
        w3, self.lbl_bal  = _card("⚖️", "الرصيد",           "#2e7d32")
        w4, self.lbl_cnt  = _card("🔢", "عدد الحركات",      "#6a1b9a")
        w5, self.lbl_nb   = _card("📌", "الرصيد الطبيعي",   "#e65100")

        for i, w in enumerate([w1, _sep(), w2, _sep(), w3, _sep(), w4, _sep(), w5]):
            if isinstance(w, QFrame):
                lay.addWidget(w)
            else:
                lay.addWidget(w, stretch=1)

    def update(self, total_dr: float, total_cr: float,
               balance: float, count: int, normal_balance: str, acc_type: str):
        self.lbl_dr.setText(f"{total_dr:,.2f}  ج")
        self.lbl_cr.setText(f"{total_cr:,.2f}  ج")

        bal_color = "#2e7d32" if balance >= 0 else "#c62828"
        self.lbl_bal.setText(f"{abs(balance):,.2f}  ج")
        self.lbl_bal.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{bal_color};"
            "background:transparent; border:none;"
        )

        self.lbl_cnt.setText(str(count))

        nb_ar    = "مدين (DR↑)" if normal_balance == "dr" else "دائن (CR↑)"
        type_ar  = TYPE_AR.get(acc_type, "")
        nb_color = "#1565c0" if normal_balance == "dr" else "#c62828"
        self.lbl_nb.setText(f"{nb_ar} — {type_ar}")
        self.lbl_nb.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{nb_color};"
            "background:transparent; border:none;"
        )

    def clear(self):
        for lbl in (self.lbl_dr, self.lbl_cr, self.lbl_bal, self.lbl_cnt, self.lbl_nb):
            lbl.setText("─")