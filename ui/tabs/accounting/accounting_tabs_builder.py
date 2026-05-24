"""
ui/tabs/accounting/accounting_tabs_builder.py
==============================================
_AccountingTabsBuilder — دوال بناء التبويبات الفرعية للقسم المحاسبي.

[تحديث v3]:
  - استخدام make_inner_tabs و make_financial_tabs من tab_builder المشترك.
  - _INNER_TAB_STYLE محتفظ به للتوافق مع accounting_section.py فقط،
    لكن لا يُستخدم داخلياً — نستخدم make_inner_tabs بدلاً منه.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from .accounts_tree import AccountsTreePanel
from .group_manager import _GroupManagerPanel
from .financial.trial_balance_tab    import TrialBalanceTab
from .financial.income_statement_tab import IncomeStatementTab
from .financial.owners_equity_tab    import OwnersEquityTab
from .financial.balance_sheet_tab    import BalanceSheetTab
from ui.widgets.shared.tab_builder   import make_inner_tabs, make_financial_tabs
from ui.widgets.shared.panels        import get_splitter_style


# للتوافق مع accounting_section.py الذي يستورد _INNER_TAB_STYLE
# مستمد من tab_builder بدل تعريف محلي
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


def build_accounts_tabs(acc):
    """يبني تبويبات قسم الحسابات (الأصول / الخصوم / حقوق الملكية)."""
    return make_inner_tabs(
        ("🏦  الأصول",
         make_inner_tabs(
             ("📊 الحسابات",   AccountsTreePanel(acc, ["asset"], "الأصول")),
             ("🏷️ التصنيفات", _GroupManagerPanel(acc, "asset")),
         )),
        ("📋  الخصوم",
         make_inner_tabs(
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
    splitter.setStyleSheet(get_splitter_style())

    tree_panel = AccountsTreePanel(
        acc,
        ["capital", "drawings", "revenue", "expense"],
        "حقوق الملكية"
    )
    splitter.addWidget(tree_panel)

    cat_tabs = make_inner_tabs(
        ("👑 رأس المال",   _GroupManagerPanel(acc, "capital")),
        ("💸 المسحوبات",  _GroupManagerPanel(acc, "drawings")),
        ("💹 الإيرادات",  _GroupManagerPanel(acc, "revenue")),
        ("📤 المصروفات",  _GroupManagerPanel(acc, "expense")),
    )
    splitter.addWidget(cat_tabs)
    splitter.setSizes([600, 300])

    root.addWidget(splitter)
    return widget


def build_financial_tab(acc):
    """يبني تبويبات القوائم المالية."""
    return make_financial_tabs(
        ("📊 قائمة الدخل",        IncomeStatementTab(acc)),
        ("👑 حقوق الملكية",       OwnersEquityTab(acc)),
        ("🏛️ الميزانية العمومية", BalanceSheetTab(acc)),
        ("⚖️ ميزان المراجعة",    TrialBalanceTab(acc)),
    )