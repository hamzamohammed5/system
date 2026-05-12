"""
ui/tabs/accounting/financial_statements.py
==========================================
القوائم المالية — الملف الرئيسي يجمع التبويبات الفرعية.

التقسيم الداخلي:
  financial/trial_balance_tab.py    → TrialBalanceTab
  financial/income_statement_tab.py → IncomeStatementTab
  financial/owners_equity_tab.py    → OwnersEquityTab
  financial/balance_sheet_tab.py    → BalanceSheetTab
  financial_statements.py           → FinancialStatementsTab  (هذا الملف)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from .financial.trial_balance_tab    import TrialBalanceTab       # noqa: F401
from .financial.income_statement_tab import IncomeStatementTab    # noqa: F401
from .financial.owners_equity_tab    import OwnersEquityTab       # noqa: F401
from .financial.balance_sheet_tab    import BalanceSheetTab       # noqa: F401


class FinancialStatementsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }"
        )
        tabs.addTab(IncomeStatementTab(self.conn), "📊 قائمة الدخل")
        tabs.addTab(OwnersEquityTab(self.conn),    "👑 حقوق الملكية")
        tabs.addTab(BalanceSheetTab(self.conn),    "🏛️ الميزانية العمومية")
        root.addWidget(tabs)