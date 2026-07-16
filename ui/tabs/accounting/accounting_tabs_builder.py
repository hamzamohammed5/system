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
from ui.widgets.theme.layout_styles import tab_style, apply_tab_widths, normalize_tab_widget
from ui.widgets.theme.table_styles import splitter_style
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import SPLITTER_HANDLE_W, EQUITY_TAB_SPLITTER_SIZES


# [إصلاح dark-mode] القديم: _INNER_TAB_STYLE = tab_style(size="inner")
# كان بياخد snapshot من _C وقت أول import بس ومبيتحدثش أبداً بعد كده.
# لسه محتفظين بالاسم للتوافق مع أي كود قديم بيستورده، لكن دلوقتي
# ThemedTabWidget هو المصدر الفعلي للستايل، وده بياخد القيمة الحالية
# وقت الاستدعاء مش وقت الـ import.
_INNER_TAB_STYLE = tab_style(size="inner")


class ThemedTabWidget(QTabWidget, WidgetMixin):
    """
    QTabWidget بيتابع الثيم تلقائيًا — بديل مباشر لـ QTabWidget() + setStyleSheet ثابت.

    المشكلة القديمة: _make_tab_widget() كانت بتحط setStyleSheet(tab_style(...))
    مرة واحدة بس وقت الإنشاء، من غير أي تسجيل على bus.theme_changed، فالتبويبات
    كانت بتفضل بلون الثيم اللي اتبنت فيه للأبد حتى لو الثيم اتبدّل بعد كده لايف.
    """

    def __init__(self, size: str = "inner", parent=None):
        super().__init__(parent)
        self._size = size
        self.setLayoutDirection(Qt.RightToLeft)
        normalize_tab_widget(self)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(tab_style(size=self._size))
        apply_tab_widths(self, size=self._size)

    # [حل مركزي لقص نص التبويبات] ThemedTabWidget بيتم ملؤه من بره
    # (addTab بتتنادى بعد الإنشاء في build_accounts_tabs/build_equity_tab/
    # build_financial_tab وغيرها) — فبدل ما كل موضع استخدام يفتكر يستدعي
    # apply_tab_widths() يدويًا، نعمل override هنا عشان العرض يتحسب
    # تلقائيًا مع كل إضافة تاب مهما كان مصدرها.
    def addTab(self, widget, *args, **kwargs):
        index = super().addTab(widget, *args, **kwargs)
        apply_tab_widths(self, size=self._size)
        return index

    def insertTab(self, index, widget, *args, **kwargs):
        result = super().insertTab(index, widget, *args, **kwargs)
        apply_tab_widths(self, size=self._size)
        return result


def _make_tab_widget(size: str = "inner") -> QTabWidget:
    return ThemedTabWidget(size=size)


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
    splitter.setHandleWidth(SPLITTER_HANDLE_W)
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
    splitter.setSizes(list(EQUITY_TAB_SPLITTER_SIZES))

    root.addWidget(splitter)
    return widget


def build_financial_tab(acc):
    tabs = _make_tab_widget(size="small")
    tabs.addTab(IncomeStatementTab(acc),  tr("income_statement_tab"))
    tabs.addTab(OwnersEquityTab(acc),     tr("owners_equity_tab"))
    tabs.addTab(BalanceSheetTab(acc),     tr("balance_sheet_tab"))
    tabs.addTab(TrialBalanceTab(acc),     tr("trial_balance_tab"))
    return tabs
