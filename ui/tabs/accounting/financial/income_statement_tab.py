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
from ui.widgets.tables.tables import make_table
from ui.widgets.core.events import bus
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.core.conn import SafeConnMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM
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

        root.addWidget(PageHeader(
            title=tr("income_statement_title"),
            icon="📊",
            accent=_C["acc_type_revenue"],
        ))

        self._stats = StatRow([
            StatItem(tr("total_revenues"),  color=_C["acc_type_revenue"], icon="💹"),
            StatItem(tr("total_expenses"),  color=_C["acc_type_expense"], icon="📤"),
            StatItem(tr("net_profit_loss"), color=_C["success"],          icon="📊"),
        ])
        root.addWidget(self._stats)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        for attr_name, title, color in [
            ("table_rev", tr("revenues_section"), _C["acc_type_revenue"]),
            ("table_exp", tr("expenses_section"), _C["acc_type_expense"]),
        ]:
            w  = QWidget()
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 4, 4, 0)
            lbl = QLabel(title)
            lbl.setStyleSheet(
                f"font-weight:bold; color:{color}; font-size:{FS_SM}px;"
                "background:transparent; border:none;"
            )
            wl.addWidget(lbl)
            tbl = make_table([tr("code"), tr("item_col"), tr("amount")], stretch_col=1)
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
            (self.table_rev, data["revenues"], _C["acc_type_revenue"]),
            (self.table_exp, data["expenses"], _C["acc_type_expense"]),
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

        self._stats.set_value(0, _money(data["total_rev"]))
        self._stats.set_value(1, _money(data["total_exp"]))

        net   = data["net_income"]
        color = _C["success"] if net >= 0 else _C["danger"]
        self._stats.set_value(2, _money(net), color=color)