"""
ui/tabs/accounting/financial_statements.py
==========================================
القوائم المالية — يجمع التبويبات الفرعية.

[تحسين v6]:
  - استيراد make_financial_tabs من panels مباشرة.
  - _rebuild أنظف مع تتبع صحيح للـ layout.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import QTimer

from .financial.trial_balance_tab    import TrialBalanceTab
from .financial.income_statement_tab import IncomeStatementTab
from .financial.owners_equity_tab    import OwnersEquityTab
from .financial.balance_sheet_tab    import BalanceSheetTab
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.events import bus
from PyQt5.QtCore import Qt
from ui.widgets.theme.layout_styles import tab_style, apply_tab_widths, normalize_tab_widget
from ui.widgets.core.i18n import tr


class FinancialStatementsTab(SafeConnMixin, QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._tabs: QTabWidget | None = None
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            QTimer.singleShot(0, self._rebuild)

    def _build(self):
        conn = self._get_safe_conn()
        self._tabs = QTabWidget()
        normalize_tab_widget(self._tabs)
        self._tabs.setLayoutDirection(Qt.RightToLeft)
        self._tabs.setStyleSheet(tab_style(size="small"))
        self._tabs.addTab(IncomeStatementTab(conn),  tr("income_statement_tab"))
        self._tabs.addTab(OwnersEquityTab(conn),     tr("owners_equity_tab"))
        self._tabs.addTab(BalanceSheetTab(conn),     tr("balance_sheet_tab"))
        self._tabs.addTab(TrialBalanceTab(conn),     tr("trial_balance_tab"))
        apply_tab_widths(self._tabs, size="small")
        self._root_layout.addWidget(self._tabs)

    def _rebuild(self):
        if self._tabs is not None:
            self._root_layout.removeWidget(self._tabs)
            self._tabs.hide()
            self._tabs.deleteLater()
            self._tabs = None
        self._build()