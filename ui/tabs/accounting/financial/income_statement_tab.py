"""
ui/tabs/accounting/financial/income_statement_tab.py
=====================================================
IncomeStatementTab — تبويب قائمة الدخل.

[إعادة هيكلة]: استبدال الهيدر والبطاقات اليدوية بـ:
  - PageHeader   بدل QLabel اليدوي
  - StatRow      بدل QHBoxLayout + _stat_card
  - make_table   من helpers (لا تغيير)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import income_statement
from ui.helpers import make_table, section_label
from ui.events  import bus
from ui.widgets.shared.panels import (
    PageHeader,
    StatRow, StatItem,
)
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ._financial_helpers import _money


class IncomeStatementTab(SafeConnMixin, QWidget):
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

        # ── هيدر الصفحة (بدل QLabel اليدوي) ──
        root.addWidget(PageHeader(
            title="قائمة الدخل",
            icon="📊",
            accent="#6a1b9a",
        ))

        # ── البطاقات الإحصائية (بدل QHBoxLayout + _stat_card اليدوية) ──
        self._stats = StatRow([
            StatItem("إجمالي الإيرادات",     color="#6a1b9a", icon="💹"),
            StatItem("إجمالي المصروفات",     color="#e65100", icon="📤"),
            StatItem("صافي الربح / الخسارة", color="#1b5e20", icon="📊"),
        ])
        root.addWidget(self._stats)

        # ── الجداول ──
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
        try:
            data = income_statement(self._get_safe_conn())
        except Exception as e:
            print(f"[IncomeStatementTab] _load error: {e}")
            return

        for tbl, rows, color in [
            (self.table_rev, data["revenues"], "#6a1b9a"),
            (self.table_exp, data["expenses"], "#e65100"),
        ]:
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

        # ── تحديث البطاقات عبر StatRow ──
        self._stats.set_value(0, _money(data["total_rev"]))
        self._stats.set_value(1, _money(data["total_exp"]))

        net   = data["net_income"]
        color = "#1b5e20" if net >= 0 else "#b71c1c"
        self._stats.set_value(2, _money(net), color=color)