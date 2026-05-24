"""
ui/tabs/accounting/accounting_tabs_builder.py
==============================================
_AccountingTabsBuilder — دوال بناء التبويبات الفرعية للقسم المحاسبي.

مُستخرج من accounting_section.py لتقليل حجمه.
يُستدعى فقط من AccountingTab._build().

دوال:
  build_accounts_tabs(acc)    → QTabWidget تبويبات الحسابات
  build_equity_tab(acc)       → QWidget تبويب حقوق الملكية
  build_financial_tab(acc)    → QTabWidget القوائم المالية
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QSplitter
from PyQt5.QtCore import Qt

from .accounts_tree import AccountsTreePanel
from .group_manager import _GroupManagerPanel
from .financial.trial_balance_tab    import TrialBalanceTab
from .financial.income_statement_tab import IncomeStatementTab
from .financial.owners_equity_tab    import OwnersEquityTab
from .financial.balance_sheet_tab    import BalanceSheetTab


_INNER_TAB_STYLE = """
    QTabWidget::pane { border: none; background: #fafafa; }
    QTabBar::tab {
        background: #f5f5f5;
        border: 1px solid #e0e0e0;
        border-bottom: none;
        padding: 6px 12px;
        font-size: 10px;
        color: #666;
    }
    QTabBar::tab:selected {
        background: white;
        color: #1565c0;
        font-weight: bold;
        border-top: 2px solid #1565c0;
    }
    QTabBar::tab:hover:!selected { background: #eeeeee; }
"""


def _make_inner_tabs(*tab_defs) -> QTabWidget:
    """يبني QTabWidget داخلي بـ style موحد."""
    tabs = QTabWidget()
    tabs.setStyleSheet(_INNER_TAB_STYLE)
    for label, widget in tab_defs:
        tabs.addTab(widget, label)
    return tabs


def build_accounts_tabs(acc) -> QTabWidget:
    """يبني تبويبات قسم الحسابات (الأصول / الخصوم / حقوق الملكية)."""
    return _make_inner_tabs(
        ("🏦  الأصول",
         _make_inner_tabs(
             ("📊 الحسابات",   AccountsTreePanel(acc, ["asset"], "الأصول")),
             ("🏷️ التصنيفات", _GroupManagerPanel(acc, "asset")),
         )),
        ("📋  الخصوم",
         _make_inner_tabs(
             ("📊 الحسابات",   AccountsTreePanel(acc, ["liability"], "الخصوم")),
             ("🏷️ التصنيفات", _GroupManagerPanel(acc, "liability")),
         )),
        ("👑  حقوق الملكية",
         build_equity_tab(acc)),
    )


def build_equity_tab(acc) -> QWidget:
    """يبني تبويب حقوق الملكية مع الـ splitter."""
    widget = QWidget()
    root   = QVBoxLayout(widget)
    root.setContentsMargins(0, 0, 0, 0)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(5)
    splitter.setStyleSheet("""
        QSplitter::handle { background: #e0e0e0; }
        QSplitter::handle:hover { background: #c8e6c9; }
    """)

    tree_panel = AccountsTreePanel(
        acc,
        ["capital", "drawings", "revenue", "expense"],
        "حقوق الملكية"
    )
    splitter.addWidget(tree_panel)

    cat_tabs = _make_inner_tabs(
        ("👑 رأس المال",   _GroupManagerPanel(acc, "capital")),
        ("💸 المسحوبات",  _GroupManagerPanel(acc, "drawings")),
        ("💹 الإيرادات",  _GroupManagerPanel(acc, "revenue")),
        ("📤 المصروفات",  _GroupManagerPanel(acc, "expense")),
    )
    splitter.addWidget(cat_tabs)
    splitter.setSizes([600, 300])

    root.addWidget(splitter)
    return widget


def build_financial_tab(acc) -> QTabWidget:
    """يبني تبويبات القوائم المالية."""
    tabs = QTabWidget()
    tabs.setStyleSheet(_INNER_TAB_STYLE)
    tabs.addTab(IncomeStatementTab(acc), "📊 قائمة الدخل")
    tabs.addTab(OwnersEquityTab(acc),    "👑 حقوق الملكية")
    tabs.addTab(BalanceSheetTab(acc),    "🏛️ الميزانية العمومية")
    tabs.addTab(TrialBalanceTab(acc),    "⚖️ ميزان المراجعة")
    return tabs