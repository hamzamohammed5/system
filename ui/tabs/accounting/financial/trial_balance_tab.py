"""
ui/tabs/accounting/financial/trial_balance_tab.py
==================================================
TrialBalanceTab — تبويب ميزان المراجعة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtGui import QColor

from db.accounting_repo import trial_balance, get_normal_balance
from ui.helpers import make_table, section_label
from ui.events  import bus


class TrialBalanceTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)
        root.addWidget(section_label("── ميزان المراجعة ──"))

        legend = QLabel(
            "  🔵 مدين (الرصيد الطبيعي DR)     🔴 دائن (الرصيد الطبيعي CR)   "
            " — القيمة تُعرض دائماً موجبة"
        )
        legend.setStyleSheet(
            "font-size:10px; color:#555; background:#f0f4ff;"
            "border:1px solid #c5cae9; border-radius:4px; padding:4px 10px;"
        )
        root.addWidget(legend)

        self.table = make_table(
            ["الكود", "اسم الحساب", "النوع", "مجموع المدين", "مجموع الدائن", "الرصيد"],
            stretch_col=1,
        )
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 110)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        totals = QFrame()
        totals.setStyleSheet(
            "QFrame { background:#f0f4ff; border:1px solid #c5cae9; border-radius:6px; }"
        )
        tl = QHBoxLayout(totals)
        tl.setContentsMargins(12, 8, 12, 8)
        self.lbl_sum_d  = QLabel("مجموع المدين: 0.00")
        self.lbl_sum_c  = QLabel("مجموع الدائن: 0.00")
        self.lbl_status = QLabel("─")
        for lbl in (self.lbl_sum_d, self.lbl_sum_c, self.lbl_status):
            lbl.setStyleSheet("font-weight:bold; font-size:12px;")
        tl.addWidget(self.lbl_sum_d)
        tl.addSpacing(24)
        tl.addWidget(self.lbl_sum_c)
        tl.addSpacing(24)
        tl.addWidget(self.lbl_status)
        tl.addStretch()
        root.addWidget(totals)

    def _load(self):
        rows = trial_balance(self.conn)
        self.table.setRowCount(0)
        sd = sc = 0.0

        from db.accounting_schema import TYPE_AR
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            self.table.setItem(r, 0, QTableWidgetItem(row["code"]))
            ni = QTableWidgetItem(row["name"])
            ni.setToolTip(row["name"])
            self.table.setItem(r, 1, ni)
            self.table.setItem(r, 2, QTableWidgetItem(
                TYPE_AR.get(row["type"], row["type"])
            ))
            self.table.setItem(r, 3, QTableWidgetItem(f"{row['total_debit']:,.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{row['total_credit']:,.2f}"))

            bal     = row["balance"]
            abs_bal = abs(bal)
            nb      = get_normal_balance(row["type"])

            if nb == "dr":
                color = "#1565c0" if bal >= 0 else "#e65100"
            else:
                color = "#c62828" if bal <= 0 else "#e65100"

            bal_item = QTableWidgetItem(f"{abs_bal:,.2f}")
            bal_item.setForeground(QColor(color))
            bal_item.setToolTip(f"{'مدين' if bal >= 0 else 'دائن'}  {abs_bal:,.2f}")
            self.table.setItem(r, 5, bal_item)

            sd += row["total_debit"]
            sc += row["total_credit"]

        self.lbl_sum_d.setText(f"مجموع المدين: {sd:,.2f}")
        self.lbl_sum_c.setText(f"مجموع الدائن: {sc:,.2f}")
        diff = abs(sd - sc)
        if diff < 0.01:
            self.lbl_status.setText("✅ الميزان متوازن")
            self.lbl_status.setStyleSheet("font-weight:bold; color:#2e7d32;")
        else:
            self.lbl_status.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_status.setStyleSheet("font-weight:bold; color:#c62828;")