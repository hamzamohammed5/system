"""
ui/tabs/accounting/financial/balance_sheet_tab.py
==================================================
BalanceSheetTab — تبويب الميزانية العمومية.

[إعادة هيكلة]: استبدال الهيدر والبطاقات اليدوية بـ:
  - PageHeader   بدل QLabel اليدوي
  - StatRow      بدل QHBoxLayout + _stat_card
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from services.accounting.statements_service import StatementsService
from ui.widgets.tables.tables import make_table
from ui.widgets.core.events import bus
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM
from ui.constants import (
    FINANCIAL_TAB_MARGIN_H, FINANCIAL_TAB_MARGIN_T, FINANCIAL_TAB_MARGIN_B,
    FINANCIAL_TAB_SPACING, FINANCIAL_SPLITTER_HANDLE_W, FINANCIAL_TABLE_MARGIN_INNER,
    FINANCIAL_COL_CODE_W, FINANCIAL_COL_AMOUNT_W, FINANCIAL_COL_TYPE_W,
    FINANCIAL_BTN_PAD_H, BTN_BORDER_RADIUS, INPUT_BORDER_W,
)
from ._financial_helpers import _money


class BalanceSheetTab(SafeConnMixin, QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_event)
        self._init_widget_mixin(theme=True, font=False, lang=True, data=False)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(FINANCIAL_TAB_MARGIN_H, FINANCIAL_TAB_MARGIN_T, FINANCIAL_TAB_MARGIN_H, FINANCIAL_TAB_MARGIN_B)
        root.setSpacing(FINANCIAL_TAB_SPACING)

        self._page_hdr = PageHeader(
            title=tr("balance_sheet_title"),
            icon="🏛️",
            accent=_C["acc_type_asset"],
        )
        self._btn_balanced = self._page_hdr.add_action(
            tr("balance_sheet_balanced"), style="ghost"
        )
        self._btn_balanced.setEnabled(False)
        root.addWidget(self._page_hdr)

        self._stats = StatRow([
            StatItem(tr("total_assets"),      color=_C["acc_type_asset"],    icon="🏦"),
            StatItem(tr("total_liabilities"), color=_C["acc_type_liability"], icon="📋"),
            StatItem(tr("equity_label"),      color=_C["acc_type_capital"],   icon="👑"),
        ])
        root.addWidget(self._stats)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(FINANCIAL_SPLITTER_HANDLE_W)

        w1 = QWidget()
        l1 = QVBoxLayout(w1)
        l1.setContentsMargins(0, FINANCIAL_TABLE_MARGIN_INNER, FINANCIAL_TABLE_MARGIN_INNER, 0)
        self._lbl_assets = QLabel(tr("assets_section"))
        self._refresh_lbl_style(self._lbl_assets, _C["acc_type_asset"])
        l1.addWidget(self._lbl_assets)
        self.table_assets = make_table(
            [tr("code"), tr("item_col"), tr("amount")], stretch_col=1
        )
        self.table_assets.setColumnWidth(0, FINANCIAL_COL_CODE_W)
        self.table_assets.setColumnWidth(2, FINANCIAL_COL_AMOUNT_W)
        l1.addWidget(self.table_assets)
        splitter.addWidget(w1)

        w2 = QWidget()
        l2 = QVBoxLayout(w2)
        l2.setContentsMargins(FINANCIAL_TABLE_MARGIN_INNER, FINANCIAL_TABLE_MARGIN_INNER, 0, 0)
        self._lbl_liab = QLabel(tr("liabilities_equity_section"))
        self._refresh_lbl_style(self._lbl_liab, _C["acc_type_liability"])
        l2.addWidget(self._lbl_liab)
        self.table_liab = make_table(
            [tr("code"), tr("item_col"), tr("amount"), tr("equity_type_col")], stretch_col=1
        )
        self.table_liab.setColumnWidth(0, FINANCIAL_COL_CODE_W)
        self.table_liab.setColumnWidth(2, FINANCIAL_COL_AMOUNT_W)
        self.table_liab.setColumnWidth(3, FINANCIAL_COL_TYPE_W)
        l2.addWidget(self.table_liab)
        splitter.addWidget(w2)

        root.addWidget(splitter, stretch=1)

    def _refresh_lbl_style(self, lbl: QLabel, color: str):
        lbl.setStyleSheet(
            f"font-weight:bold; color:{color}; font-size:{FS_SM}px;"
            "background:transparent; border:none;"
        )

    def _refresh_style(self, *_):
        if not hasattr(self, "_lbl_assets"):
            return
        self._refresh_lbl_style(self._lbl_assets, _C["acc_type_asset"])
        self._refresh_lbl_style(self._lbl_liab,   _C["acc_type_liability"])

    def _refresh_lang(self, *_):
        if not hasattr(self, "_lbl_assets"):
            return
        self._lbl_assets.setText(tr("assets_section"))
        self._lbl_liab.setText(tr("liabilities_equity_section"))

    def _load(self):
        try:
            data = StatementsService(self._get_safe_conn()).get_balance_sheet()
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
            ai.setForeground(QColor(_C["acc_type_asset"]))
            self.table_assets.setItem(r, 2, ai)

        self.table_liab.setRowCount(0)
        for row, label, color in [
            *[(r, tr("liabilities_label"), _C["acc_type_liability"]) for r in data["liabilities"]],
            *[(r, tr("capital_label_bs"),  _C["acc_type_capital"])   for r in data["capital"]],
            *[(r, tr("drawings_bs"),       _C["acc_type_drawings"])  for r in data["drawings"]],
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
            self.table_liab.setItem(r2, 1, QTableWidgetItem(tr("net_income_bs")))
            ni_item = QTableWidgetItem(f"{ni:,.2f}")
            ni_item.setForeground(QColor(_C["success"] if ni >= 0 else _C["danger"]))
            self.table_liab.setItem(r2, 2, ni_item)
            self.table_liab.setItem(r2, 3, QTableWidgetItem(tr("owners_equity")))

        self._stats.set_value(0, _money(data["total_assets"]))
        self._stats.set_value(1, _money(data["total_liab"]))
        self._stats.set_value(2, _money(data["total_equity"]))

        diff = abs(data["total_assets"] - (data["total_liab"] + data["total_equity"]))
        if diff < 0.01:
            self._btn_balanced.setText(tr("balance_sheet_balanced"))
            self._btn_balanced.setStyleSheet(
                f"QPushButton {{ background:{_C['success_bg']}; color:{_C['success']}}};"
                f" border:{INPUT_BORDER_W}px solid {_C['success_border']}; border-radius:{BTN_BORDER_RADIUS}px;"
                f" padding:0 {FINANCIAL_BTN_PAD_H}px; font-weight:bold; }}"
            )
        else:
            self._btn_balanced.setText(tr("balance_sheet_diff").format(diff=f"{diff:,.2f}"))
            self._btn_balanced.setStyleSheet(
                f"QPushButton {{ background:{_C['danger_bg']}; color:{_C['danger']}}};"
                f" border:{INPUT_BORDER_W}px solid {_C['danger_border']}; border-radius:{BTN_BORDER_RADIUS}px;"
                f" padding:0 {FINANCIAL_BTN_PAD_H}px; font-weight:bold; }}"
            )
