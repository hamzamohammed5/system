"""
ui/tabs/accounting/financial_statements.py
==========================================
القوائم المالية — الملف الرئيسي يجمع التبويبات الفرعية.

[تحديث v4]:
  - استخدام make_financial_tabs من tab_builder المشترك.
  - باقي المنطق (SafeConnMixin, rebuild) كما هو.

التقسيم الداخلي:
  financial/trial_balance_tab.py    → TrialBalanceTab
  financial/income_statement_tab.py → IncomeStatementTab
  financial/owners_equity_tab.py    → OwnersEquityTab
  financial/balance_sheet_tab.py    → BalanceSheetTab
  financial_statements.py           → FinancialStatementsTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import QTimer

from .financial.trial_balance_tab    import TrialBalanceTab       # noqa: F401
from .financial.income_statement_tab import IncomeStatementTab    # noqa: F401
from .financial.owners_equity_tab    import OwnersEquityTab       # noqa: F401
from .financial.balance_sheet_tab    import BalanceSheetTab       # noqa: F401
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.tab_builder    import make_financial_tabs
from ui.events import bus


class FinancialStatementsTab(SafeConnMixin, QWidget):
    """
    يجمع كل القوائم المالية في تبويبات تحت نفس الـ connection.

    [تحديث v4]:
      - make_financial_tabs من tab_builder بدل بناء QTabWidget يدوي.
      - باقي المنطق كما هو.
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._tabs: QTabWidget | None = None
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            QTimer.singleShot(0, self._rebuild)

    def _build(self):
        """ينشئ tabs بـ conn حي من _get_safe_conn()."""
        conn = self._get_safe_conn()
        tabs = make_financial_tabs(
            ("📊 قائمة الدخل",        IncomeStatementTab(conn)),
            ("👑 حقوق الملكية",       OwnersEquityTab(conn)),
            ("🏛️ الميزانية العمومية", BalanceSheetTab(conn)),
            ("⚖️ ميزان المراجعة",    TrialBalanceTab(conn)),
        )
        self._tabs = tabs
        self._root_layout.addWidget(tabs)

    def _rebuild(self):
        """يحذف الـ tabs القديمة وينشئ جديدة بـ conn للشركة النشطة."""
        if self._tabs is not None:
            self._root_layout.removeWidget(self._tabs)
            self._tabs.hide()
            self._tabs.deleteLater()
            self._tabs = None
        self._build()