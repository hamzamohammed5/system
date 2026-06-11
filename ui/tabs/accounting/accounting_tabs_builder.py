"""
ui/tabs/accounting/accounting_tabs_builder.py
==============================================
_AccountingTabsBuilder — دوال بناء التبويبات الفرعية للقسم المحاسبي.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget
from PyQt5.QtCore import Qt

from .accounts_tree import AccountsTreePanel
from .group_manager import _GroupManagerPanel
from .financial.trial_balance_tab    import TrialBalanceTab
from .financial.income_statement_tab import IncomeStatementTab
from .financial.owners_equity_tab    import OwnersEquityTab
from .financial.balance_sheet_tab    import BalanceSheetTab
from ui.widgets.theme.layout_styles import tab_style
from ui.widgets.theme.table_styles import splitter_style
from ui.widgets.core.i18n import tr
from db.accounting.accounting_schema import TYPE_AR


# للتوافق مع accounting_section.py الذي يستورد _INNER_TAB_STYLE
_INNER_TAB_STYLE = tab_style(size="inner")


def _make_tab_widget(size: str = "inner") -> QTabWidget:
    tabs = QTabWidget()
    tabs.setLayoutDirection(Qt.RightToLeft)
    tabs.setStyleSheet(tab_style(size=size))
    return tabs


def build_accounts_tabs(acc):
    assets_inner = _make_tab_widget()
    assets_inner.addTab(AccountsTreePanel(acc, ["asset"], tr("assets")), tr("accounts_tab"))
    assets_inner.addTab(_GroupManagerPanel(acc, "asset"), tr("categories_tab"))

    liab_inner = _make_tab_widget()
    liab_inner.addTab(AccountsTreePanel(acc, ["liability"], tr("liabilities")), tr("accounts_tab"))
    liab_inner.addTab(_GroupManagerPanel(acc, "liability"), tr("categories_tab"))

    outer = _make_tab_widget()
    outer.addTab(assets_inner,          tr("assets_tab"))
    outer.addTab(liab_inner,            tr("liabilities_tab"))
    outer.addTab(build_equity_tab(acc), tr("equity_tab"))
    return outer


def build_equity_tab(acc) -> QWidget:
    widget   = QWidget()
    root     = QVBoxLayout(widget)
    root.setContentsMargins(0, 0, 0, 0)
    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(5)
    splitter.setStyleSheet(splitter_style())

    tree_panel = AccountsTreePanel(
        acc,
        ["capital", "drawings", "revenue", "expense"],
        tr("owners_equity")
    )
    splitter.addWidget(tree_panel)

    cat_tabs = _make_tab_widget()
    cat_tabs.addTab(_GroupManagerPanel(acc, "capital"),   tr("capital_tab"))
    cat_tabs.addTab(_GroupManagerPanel(acc, "drawings"),  tr("drawings_tab"))
    cat_tabs.addTab(_GroupManagerPanel(acc, "revenue"),   tr("revenue_tab"))
    cat_tabs.addTab(_GroupManagerPanel(acc, "expense"),   tr("expense_tab"))
    splitter.addWidget(cat_tabs)
    splitter.setSizes([600, 300])

    root.addWidget(splitter)
    return widget


def build_financial_tab(acc):
    tabs = _make_tab_widget(size="small")
    tabs.addTab(IncomeStatementTab(acc),  tr("income_statement_tab"))
    tabs.addTab(OwnersEquityTab(acc),     tr("owners_equity_tab"))
    tabs.addTab(BalanceSheetTab(acc),     tr("balance_sheet_tab"))
    tabs.addTab(TrialBalanceTab(acc),     tr("trial_balance_tab"))
    return tabs
