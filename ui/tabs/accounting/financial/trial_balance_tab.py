"""
ui/tabs/accounting/financial/trial_balance_tab.py
==================================================
TrialBalanceTab — تبويب ميزان المراجعة.

[إصلاح v4 — توحيد الـ UI]:
  - PageHeader بدل section_label اليدوي.
  - make_list_table من panels بدل make_table من helpers.
  - SafeConnMixin كما هو.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtGui import QColor

from db.accounting.accounting_repo import trial_balance, get_normal_balance
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.tables.tables import (
    make_list_table,
    bold_item as bold_table_item,
    colored_item as colored_table_item,
)
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_XS, FS_BASE


class TrialBalanceTab(SafeConnMixin, QWidget):
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
        root.setSpacing(8)

        # ── هيدر الصفحة (بدل section_label اليدوي) ──
        root.addWidget(PageHeader(
            title=tr("trial_balance_title"),
            icon="⚖️",
            accent=_C["acc_type_asset"],
            compact=True,
        ))

        legend = QLabel(tr("trial_balance_legend"))
        legend.setStyleSheet(
            f"font-size:{FS_XS}px; color:{_C['text_sec']}; background:{_C['journal_header_bg']};"
            f"border:1px solid {_C['journal_header_border']}; border-radius:4px; padding:4px 10px;"
        )
        root.addWidget(legend)

        self.table = make_list_table(
            columns=[
                tr("account_code_col"), tr("account_name_col"), tr("type_col"),
                tr("total_debit_col"), tr("total_credit_col"), tr("balance_col"),
            ],
            stretch_col=1,
            col_widths={0: 70, 2: 100, 3: 120, 4: 120, 5: 110},
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        totals = QFrame()
        totals.setStyleSheet(
            f"QFrame {{ background:{_C['journal_header_bg']}; border:1px solid {_C['journal_header_border']}; border-radius:6px; }}"
        )
        tl = QHBoxLayout(totals)
        tl.setContentsMargins(12, 8, 12, 8)
        self.lbl_sum_d  = QLabel(tr("sum_debit_label").format(val="0.00"))
        self.lbl_sum_c  = QLabel(tr("sum_credit_label").format(val="0.00"))
        self.lbl_status = QLabel("─")
        for lbl in (self.lbl_sum_d, self.lbl_sum_c, self.lbl_status):
            lbl.setStyleSheet(f"font-weight:bold; font-size:{FS_BASE}px;")
        tl.addWidget(self.lbl_sum_d)
        tl.addSpacing(24)
        tl.addWidget(self.lbl_sum_c)
        tl.addSpacing(24)
        tl.addWidget(self.lbl_status)
        tl.addStretch()
        root.addWidget(totals)

    def _load(self):
        try:
            rows = trial_balance(self._get_safe_conn())
        except Exception as e:
            print(f"[TrialBalanceTab] _load error: {e}")
            return

        self.table.setRowCount(0)
        sd = sc = 0.0

        from db.accounting.accounting_schema import TYPE_AR
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
            color   = (_C["journal_dr_accent"] if bal >= 0 else _C["orange"]) if nb == "dr" \
                      else (_C["journal_cr_accent"] if bal <= 0 else _C["orange"])

            bal_item = colored_table_item(
                f"{abs_bal:,.2f}", color,
                tooltip=f"{tr('dr_balance') if bal >= 0 else tr('cr_balance')}  {abs_bal:,.2f}"
            )
            self.table.setItem(r, 5, bal_item)

            sd += row["total_debit"]
            sc += row["total_credit"]

        self.lbl_sum_d.setText(tr("sum_debit_label").format(val=f"{sd:,.2f}"))
        self.lbl_sum_c.setText(tr("sum_credit_label").format(val=f"{sc:,.2f}"))
        diff = abs(sd - sc)
        if diff < 0.01:
            self.lbl_status.setText(tr("balance_balanced"))
            self.lbl_status.setStyleSheet(f"font-weight:bold; color:{_C['success']};")
        else:
            self.lbl_status.setText(tr("balance_diff").format(diff=f"{diff:,.2f}"))
            self.lbl_status.setStyleSheet(f"font-weight:bold; color:{_C['danger']};")