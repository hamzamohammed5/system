"""
ui/tabs/accounting/financial_statements.py
==========================================
القوائم المالية — الملف الرئيسي يجمع التبويبات الفرعية.

[إصلاح v3] FinancialStatementsTab أصبح يستخدم SafeConnMixin:
  - يستمع لـ bus.company_data_changed ويعيد بناء الـ tabs بـ conn حي.
  - هذا يضمن أن كل child يحصل على conn الشركة الصح عند تغيير الشركة.
  - TrialBalanceTab أُضيف هنا داخل نفس الـ connection.

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
from ui.events import bus


class FinancialStatementsTab(SafeConnMixin, QWidget):
    """
    يجمع كل القوائم المالية في تبويبات تحت نفس الـ connection.

    [إصلاح v3]:
      - SafeConnMixin يضمن _get_safe_conn() دايماً للشركة النشطة.
      - يستمع لـ bus.company_data_changed ويعيد بناء الـ tabs عند تغيير الشركة.
      - _rebuild() يحذف الـ tabs القديمة وينشئ جديدة بـ conn حي.
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
        """ينشئ QTabWidget بـ conn حي من _get_safe_conn()."""
        conn = self._get_safe_conn()
        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }"
        )
        tabs.addTab(IncomeStatementTab(conn), "📊 قائمة الدخل")
        tabs.addTab(OwnersEquityTab(conn),    "👑 حقوق الملكية")
        tabs.addTab(BalanceSheetTab(conn),    "🏛️ الميزانية العمومية")
        tabs.addTab(TrialBalanceTab(conn),    "⚖️ ميزان المراجعة")
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