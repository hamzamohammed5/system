"""
ui/tabs/accounting/financial/balance_sheet_tab.py
==================================================
BalanceSheetTab — تبويب الميزانية العمومية.

إصلاحات (v3): SafeConnMixin بدل conn property يدوي.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import balance_sheet
from ui.helpers import make_table, section_label
from ui.events  import bus
from ui.tabs.accounting.helpers import _money, _stat_card
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin


class BalanceSheetTab(SafeConnMixin, QWidget):
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

        hdr = QLabel("🏛️  الميزانية العمومية")
        hdr.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#1565c0;"
            "background:#e8f4fd; border:1px solid #90caf9;"
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        cards = QHBoxLayout()
        f1, self.lbl_assets = _stat_card("إجمالي الأصول", "#1565c0")
        f2, self.lbl_liab   = _stat_card("إجمالي الخصوم", "#c62828")
        f3, self.lbl_equity = _stat_card("حقوق الملكية",  "#2e7d32")
        self.lbl_balanced   = QLabel("✅ متوازنة")
        self.lbl_balanced.setStyleSheet(
            "font-weight:bold; color:#2e7d32; font-size:12px;"
        )
        self.lbl_balanced.setAlignment(Qt.AlignCenter)
        for f in (f1, f2, f3):
            cards.addWidget(f, stretch=1)
        cards.addWidget(self.lbl_balanced)
        root.addLayout(cards)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        w1 = QWidget()
        l1 = QVBoxLayout(w1)
        l1.setContentsMargins(0, 4, 4, 0)
        l1.addWidget(section_label("🏦 الأصول"))
        self.table_assets = make_table(["الكود", "البند", "المبلغ"], stretch_col=1)
        self.table_assets.setColumnWidth(0, 60)
        self.table_assets.setColumnWidth(2, 110)
        l1.addWidget(self.table_assets)
        splitter.addWidget(w1)

        w2 = QWidget()
        l2 = QVBoxLayout(w2)
        l2.setContentsMargins(4, 4, 0, 0)
        l2.addWidget(section_label("📋 الخصوم وحقوق الملكية"))
        self.table_liab = make_table(
            ["الكود", "البند", "المبلغ", "النوع"], stretch_col=1
        )
        self.table_liab.setColumnWidth(0, 60)
        self.table_liab.setColumnWidth(2, 110)
        self.table_liab.setColumnWidth(3, 80)
        l2.addWidget(self.table_liab)
        splitter.addWidget(w2)

        root.addWidget(splitter, stretch=1)

    def _load(self):
        try:
            data = balance_sheet(self._get_safe_conn())
        except Exception as e:
            print(f"[BalanceSheetTab] _load error: {e}")
            return

        self.table_assets.setRowCount(0)
        for row in data["assets"]:
            r = self.table_assets.rowCount()
            self.table_assets.insertRow(r)
            self.table_assets.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_assets.setItem(r, 1, n)
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor("#1565c0"))
            self.table_assets.setItem(r, 2, ai)

        self.table_liab.setRowCount(0)
        for row, label, color in [
            *[(r, "خصوم",      "#c62828") for r in data["liabilities"]],
            *[(r, "رأس المال", "#2e7d32") for r in data["capital"]],
            *[(r, "مسحوبات",  "#4e342e") for r in data["drawings"]],
        ]:
            r2 = self.table_liab.rowCount()
            self.table_liab.insertRow(r2)
            self.table_liab.setItem(r2, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_liab.setItem(r2, 1, n)
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor(color))
            self.table_liab.setItem(r2, 2, ai)
            self.table_liab.setItem(r2, 3, QTableWidgetItem(label))

        ni = data["net_income"]
        if ni != 0:
            r2 = self.table_liab.rowCount()
            self.table_liab.insertRow(r2)
            self.table_liab.setItem(r2, 0, QTableWidgetItem(""))
            self.table_liab.setItem(r2, 1, QTableWidgetItem("صافي الدخل"))
            ni_item = QTableWidgetItem(f"{ni:,.2f}")
            ni_item.setForeground(QColor("#1b5e20" if ni >= 0 else "#b71c1c"))
            self.table_liab.setItem(r2, 2, ni_item)
            self.table_liab.setItem(r2, 3, QTableWidgetItem("حقوق ملكية"))

        self.lbl_assets.setText(_money(data["total_assets"]))
        self.lbl_liab.setText(_money(data["total_liab"]))
        self.lbl_equity.setText(_money(data["total_equity"]))

        diff = abs(data["total_assets"] - (data["total_liab"] + data["total_equity"]))
        if diff < 0.01:
            self.lbl_balanced.setText("✅ الميزانية متوازنة")
            self.lbl_balanced.setStyleSheet("font-weight:bold; color:#2e7d32; font-size:12px;")
        else:
            self.lbl_balanced.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_balanced.setStyleSheet("font-weight:bold; color:#c62828; font-size:12px;")