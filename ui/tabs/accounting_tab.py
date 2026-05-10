"""
ui/tabs/accounting_tab.py
==========================
التبويب الرئيسي للحسابات — يجمع الأجزاء المقسمة في مجلد accounting/.

الهيكل:
  ui/tabs/accounting/
    __init__.py
    helpers.py              — TYPE_COLORS, _spin, _money, _stat_card
    account_combo.py        — _AccountCombo
    accounts_tree.py        — AccountsTreePanel
    group_manager.py        — _GroupManagerPanel
    journal_tab.py          — JournalTab, _SmartEntryLine
    ledger_tab.py           — LedgerTab
    financial_statements.py — TrialBalanceTab, IncomeStatementTab,
                              OwnersEquityTab, BalanceSheetTab,
                              FinancialStatementsTab
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore    import Qt

from db.connection import get_accounting_connection

# ── الأجزاء المقسمة ──────────────────────────────────────
from ui.tabs.accounting.accounts_tree        import AccountsTreePanel
from ui.tabs.accounting.group_manager        import _GroupManagerPanel
from ui.tabs.accounting.journal_tab          import JournalTab
from ui.tabs.accounting.ledger_tab           import LedgerTab
from ui.tabs.accounting.financial_statements import (
    TrialBalanceTab,
    FinancialStatementsTab,
)

from db.accounting_schema import TYPE_AR


class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_accounting_connection()
        self._init_schema()
        self._build()

    def _init_schema(self):
        try:
            from db.accounting_schema import create_accounting_tables
            create_accounting_tables(self.conn)
        except Exception as e:
            print(f"[AccountingTab] schema init error: {e}")

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border:none; background:#f9f9f9; }
            QTabBar::tab {
                background:#f0f0f0; border:1px solid #ddd;
                border-bottom:none; padding:8px 14px;
                margin-left:2px; font-size:11px; color:#555;
            }
            QTabBar::tab:selected {
                background:#fff; color:#1565c0;
                font-weight:bold; border-top:2px solid #1565c0;
            }
            QTabBar::tab:hover:!selected { background:#e8f0fe; color:#1565c0; }
        """)

        # ── أصول ──
        asset_tab = QTabWidget()
        asset_tab.addTab(
            AccountsTreePanel(self.conn, ["asset"], "الأصول"),
            "📊 الحسابات"
        )
        asset_tab.addTab(
            _GroupManagerPanel(self.conn, "asset"),
            "🏷️ التصنيفات"
        )
        tabs.addTab(asset_tab, "🏦 الأصول")

        # ── خصوم ──
        liab_tab = QTabWidget()
        liab_tab.addTab(
            AccountsTreePanel(self.conn, ["liability"], "الخصوم"),
            "📊 الحسابات"
        )
        liab_tab.addTab(
            _GroupManagerPanel(self.conn, "liability"),
            "🏷️ التصنيفات"
        )
        tabs.addTab(liab_tab, "📋 الخصوم")

        # ── حقوق الملكية ──
        eq_tab = QTabWidget()
        eq_tab.addTab(
            AccountsTreePanel(
                self.conn,
                ["capital", "drawings", "revenue", "expense"],
                "حقوق الملكية"
            ),
            "📊 الحسابات"
        )
        eq_groups = QTabWidget()
        eq_groups.addTab(_GroupManagerPanel(self.conn, "capital"),  "رأس المال")
        eq_groups.addTab(_GroupManagerPanel(self.conn, "drawings"), "المسحوبات")
        eq_groups.addTab(_GroupManagerPanel(self.conn, "revenue"),  "الإيرادات")
        eq_groups.addTab(_GroupManagerPanel(self.conn, "expense"),  "المصروفات")
        eq_tab.addTab(eq_groups, "🏷️ التصنيفات")
        tabs.addTab(eq_tab, "👑 حقوق الملكية")

        # ── القوائم المالية ──
        tabs.addTab(FinancialStatementsTab(self.conn), "📊 القوائم المالية")

        # ── قيود اليومية ──
        tabs.addTab(JournalTab(self.conn), "📒 قيود اليومية")

        # ── دفتر الأستاذ ──
        tabs.addTab(LedgerTab(self.conn), "📘 دفتر الأستاذ")

        # ── ميزان المراجعة ──
        tabs.addTab(TrialBalanceTab(self.conn), "⚖️ ميزان المراجعة")

        root.addWidget(tabs)

    def closeEvent(self, event):
        try:
            self.conn.close()
        except Exception:
            pass
        super().closeEvent(event)