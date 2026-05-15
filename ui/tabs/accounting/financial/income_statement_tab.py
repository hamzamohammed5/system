"""
ui/tabs/accounting/financial/income_statement_tab.py
=====================================================
IncomeStatementTab — تبويب قائمة الدخل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import income_statement
from ui.helpers import make_table, section_label
from ui.events  import bus
from ui.tabs.accounting.helpers import _money, _stat_card


class IncomeStatementTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        hdr = QLabel("📊  قائمة الدخل")
        hdr.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#6a1b9a;"
            "background:#f3e5f5; border:1px solid #ce93d8;"
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        cards = QHBoxLayout()
        f1, self.lbl_rev = _stat_card("إجمالي الإيرادات",     "#6a1b9a")
        f2, self.lbl_exp = _stat_card("إجمالي المصروفات",     "#e65100")
        f3, self.lbl_net = _stat_card("صافي الربح / الخسارة", "#1b5e20")
        for f in (f1, f2, f3):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        for attr_name, title in [
            ("table_rev", "💹 الإيرادات"),
            ("table_exp", "📤 المصروفات"),
        ]:
            w  = QWidget()
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 4, 4, 0)
            wl.addWidget(section_label(title))
            tbl = make_table(["الكود", "البند", "المبلغ"], stretch_col=1)
            tbl.setColumnWidth(0, 60)
            tbl.setColumnWidth(2, 110)
            setattr(self, attr_name, tbl)
            wl.addWidget(tbl)
            splitter.addWidget(w)

        root.addWidget(splitter, stretch=1)

    def _load(self):
        data = income_statement(self.conn)
        colors = {"table_rev": "#6a1b9a", "table_exp": "#e65100"}
        row_data = [
            (self.table_rev, data["revenues"], "#6a1b9a"),
            (self.table_exp, data["expenses"], "#e65100"),
        ]
        for tbl, rows, color in row_data:
            tbl.setRowCount(0)
            for row in rows:
                r = tbl.rowCount()
                tbl.insertRow(r)
                tbl.setItem(r, 0, QTableWidgetItem(row["code"]))
                n = QTableWidgetItem(row["name"])
                n.setToolTip(row["name"])
                tbl.setItem(r, 1, n)
                ai = QTableWidgetItem(f"{row['amount']:,.2f}")
                ai.setForeground(QColor(color))
                tbl.setItem(r, 2, ai)

        self.lbl_rev.setText(_money(data["total_rev"]))
        self.lbl_exp.setText(_money(data["total_exp"]))
        net   = data["net_income"]
        color = "#1b5e20" if net >= 0 else "#b71c1c"
        self.lbl_net.setText(_money(net))
        self.lbl_net.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )