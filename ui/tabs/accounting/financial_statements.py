"""
ui/tabs/accounting/financial_statements.py
==========================================
القوائم المالية — يجمع التبويبات الفرعية.

[تحسين v7]:
  - RebuildMixin لتوحيد نمط _rebuild.
  - make_financial_tabs من panels مباشرة.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer

from .financial.trial_balance_tab    import TrialBalanceTab
from .financial.income_statement_tab import IncomeStatementTab
from .financial.owners_equity_tab    import OwnersEquityTab
from .financial.balance_sheet_tab    import BalanceSheetTab
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.rebuild_mixin import RebuildMixin
from ui.widgets.shared.panels import make_financial_tabs
from ui.events import bus


class FinancialStatementsTab(SafeConnMixin, RebuildMixin, QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._current_widget = None
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            QTimer.singleShot(0, self._rebuild)

    def _build_widget(self):
        conn = self._get_safe_conn()
        return make_financial_tabs(
            ("📊 قائمة الدخل",        IncomeStatementTab(conn)),
            ("👑 حقوق الملكية",       OwnersEquityTab(conn)),
            ("🏛️ الميزانية العمومية", BalanceSheetTab(conn)),
            ("⚖️ ميزان المراجعة",    TrialBalanceTab(conn)),
        )

    def _build(self):
        self._replace_widget(self._build_widget())

    def _rebuild(self):
        self._build()