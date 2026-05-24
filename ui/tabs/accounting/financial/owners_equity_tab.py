"""
ui/tabs/accounting/financial/owners_equity_tab.py
==================================================
OwnersEquityTab — تبويب قائمة حقوق الملكية.

إصلاحات (v3): SafeConnMixin بدل conn property يدوي.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import owners_equity_statement
from ui.helpers import make_table, section_label
from ui.events  import bus
from ui.tabs.accounting.helpers import _money, _stat_card
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin


class OwnersEquityTab(SafeConnMixin, QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        hdr = QLabel("👑  قائمة حقوق الملكية")
        hdr.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#2e7d32;"
            "background:#f1f8e9; border:1px solid #a5d6a7;"
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        cards = QHBoxLayout()
        f1, self.lbl_cap   = _stat_card("رأس المال",          "#2e7d32")
        f2, self.lbl_ni    = _stat_card("صافي الدخل",         "#1b5e20")
        f3, self.lbl_draw  = _stat_card("المسحوبات",          "#4e342e")
        f4, self.lbl_total = _stat_card("صافي حقوق الملكية",  "#1565c0")
        for f in (f1, f2, f3, f4):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        left_w = QWidget()
        ll = QVBoxLayout(left_w)
        ll.setContentsMargins(0, 4, 4, 0)
        cr_hdr = QLabel("📈 ما يزيد حقوق الملكية (CR↑)")
        cr_hdr.setStyleSheet(
            "font-weight:bold; color:#2e7d32; font-size:11px;"
            "background:#f1f8e9; border-radius:4px; padding:4px 8px;"
        )
        ll.addWidget(cr_hdr)
        self.table_cr = make_table(["الكود", "البند", "النوع", "المبلغ"], stretch_col=1)
        self.table_cr.setColumnWidth(0, 60)
        self.table_cr.setColumnWidth(2, 80)
        self.table_cr.setColumnWidth(3, 100)
        ll.addWidget(self.table_cr)
        splitter.addWidget(left_w)

        right_w = QWidget()
        rl = QVBoxLayout(right_w)
        rl.setContentsMargins(4, 4, 0, 0)
        dr_hdr = QLabel("📉 ما ينقص حقوق الملكية (DR↑)")
        dr_hdr.setStyleSheet(
            "font-weight:bold; color:#c62828; font-size:11px;"
            "background:#fdecea; border-radius:4px; padding:4px 8px;"
        )
        rl.addWidget(dr_hdr)
        self.table_dr = make_table(["الكود", "البند", "النوع", "المبلغ"], stretch_col=1)
        self.table_dr.setColumnWidth(0, 60)
        self.table_dr.setColumnWidth(2, 80)
        self.table_dr.setColumnWidth(3, 100)
        rl.addWidget(self.table_dr)
        splitter.addWidget(right_w)

        root.addWidget(splitter, stretch=1)

        eq_frame = QFrame()
        eq_frame.setStyleSheet(
            "QFrame { background:#e8f4fd; border:1px solid #90caf9; border-radius:6px; }"
        )
        eq_lay = QHBoxLayout(eq_frame)
        eq_lay.setContentsMargins(12, 8, 12, 8)
        self.lbl_equation = QLabel("")
        self.lbl_equation.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#1565c0;"
            "background:transparent; border:none;"
        )
        eq_lay.addWidget(self.lbl_equation)
        root.addWidget(eq_frame)

    def _load(self):
        try:
            data = owners_equity_statement(self._get_safe_conn())
        except Exception as e:
            print(f"[OwnersEquityTab] _load error: {e}")
            return

        self.table_cr.setRowCount(0)
        for row in data["capital_accounts"]:
            r = self.table_cr.rowCount()
            self.table_cr.insertRow(r)
            self.table_cr.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_cr.setItem(r, 1, n)
            self.table_cr.setItem(r, 2, QTableWidgetItem("رأس المال"))
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor("#2e7d32"))
            self.table_cr.setItem(r, 3, ai)

        ni = data["net_income"]
        r  = self.table_cr.rowCount()
        self.table_cr.insertRow(r)
        self.table_cr.setItem(r, 0, QTableWidgetItem(""))
        self.table_cr.setItem(r, 1, QTableWidgetItem("صافي الدخل للفترة"))
        self.table_cr.setItem(r, 2, QTableWidgetItem("إيرادات - مصروفات"))
        ni_item = QTableWidgetItem(f"{ni:,.2f}")
        ni_item.setForeground(QColor("#1b5e20") if ni >= 0 else QColor("#b71c1c"))
        self.table_cr.setItem(r, 3, ni_item)

        self.table_dr.setRowCount(0)
        for row in data["drawings_accounts"]:
            r = self.table_dr.rowCount()
            self.table_dr.insertRow(r)
            self.table_dr.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_dr.setItem(r, 1, n)
            self.table_dr.setItem(r, 2, QTableWidgetItem("مسحوبات"))
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor("#4e342e"))
            self.table_dr.setItem(r, 3, ai)

        self.lbl_cap.setText(_money(data["total_capital"]))
        self.lbl_ni.setText(_money(ni))
        self.lbl_draw.setText(_money(data["total_drawings"]))
        total = data["total_equity"]
        self.lbl_total.setText(_money(total))
        tc = "#1565c0" if total >= 0 else "#b71c1c"
        self.lbl_total.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{tc};"
            "background:transparent; border:none;"
        )
        self.lbl_equation.setText(
            f"رأس المال  {data['total_capital']:,.2f}  +  "
            f"صافي الدخل  {ni:,.2f}  −  "
            f"المسحوبات  {data['total_drawings']:,.2f}  =  "
            f"صافي حقوق الملكية  {total:,.2f}"
        )