"""
ui/tabs/accounting_tab.py  — نسخة مصححة
==========================================
التغييرات:
  1. إزالة التداخل في التبويبات (nested QTabWidget مكثف)
  2. دمج نظام المستثمرين مع ربطه بـ accounting.db و erp.db
  3. تبويبات واضحة ومرتبة بدون تكرار
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QSplitter,
)
from PyQt5.QtCore import Qt

from db.connection import get_connection, get_accounting_connection

# ── أجزاء الحسابات ──
from ui.tabs.accounting.accounts_tree        import AccountsTreePanel
from ui.tabs.accounting.group_manager        import _GroupManagerPanel
from ui.tabs.accounting.journal_tab          import JournalTab
from ui.tabs.accounting.ledger_tab           import LedgerTab
from ui.tabs.accounting.financial_statements import (
    TrialBalanceTab,
    FinancialStatementsTab,
)
# ── المستثمرون ──
from ui.tabs.accounting.investors_tab import InvestorsTab


_TAB_STYLE = """
    QTabWidget::pane {
        border: none;
        background: #f9f9f9;
    }
    QTabBar::tab {
        background: #f0f0f0;
        border: 1px solid #ddd;
        border-bottom: none;
        padding: 8px 16px;
        margin-left: 2px;
        font-size: 11px;
        color: #555;
    }
    QTabBar::tab:selected {
        background: #ffffff;
        color: #1565c0;
        font-weight: bold;
        border-top: 2px solid #1565c0;
    }
    QTabBar::tab:hover:!selected {
        background: #e8f0fe;
        color: #1565c0;
    }
"""

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
    """ينشئ QTabWidget داخلي بالستايل المناسب."""
    tabs = QTabWidget()
    tabs.setStyleSheet(_INNER_TAB_STYLE)
    for label, widget in tab_defs:
        tabs.addTab(widget, label)
    return tabs


class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.acc_conn = get_accounting_connection()
        self.erp_conn = get_connection()          # لنظام المستثمرين
        self._init_schema()
        self._build()

    def _init_schema(self):
        try:
            from db.accounting_schema import create_accounting_tables
            create_accounting_tables(self.acc_conn)
        except Exception as e:
            print(f"[AccountingTab] schema init error: {e}")
        try:
            from db.investors_repo import create_investors_tables
            create_investors_tables(self.erp_conn)
        except Exception as e:
            print(f"[AccountingTab] investors schema error: {e}")

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        main_tabs = QTabWidget()
        main_tabs.setStyleSheet(_TAB_STYLE)

        # ═══════════════════════════════════════════════════
        # 1. الحسابات — شجرة الحسابات + التصنيفات
        # ═══════════════════════════════════════════════════
        accounts_tabs = _make_inner_tabs(
            ("🏦  الأصول",
             _make_inner_tabs(
                 ("📊 الحسابات",     AccountsTreePanel(self.acc_conn, ["asset"], "الأصول")),
                 ("🏷️ التصنيفات",   _GroupManagerPanel(self.acc_conn, "asset")),
             )),
            ("📋  الخصوم",
             _make_inner_tabs(
                 ("📊 الحسابات",     AccountsTreePanel(self.acc_conn, ["liability"], "الخصوم")),
                 ("🏷️ التصنيفات",   _GroupManagerPanel(self.acc_conn, "liability")),
             )),
            ("👑  حقوق الملكية",
             self._build_equity_tab()),
        )
        main_tabs.addTab(accounts_tabs, "🏦  الحسابات")

        # ═══════════════════════════════════════════════════
        # 2. القيود المحاسبية
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(JournalTab(self.acc_conn), "📒  قيود اليومية")

        # ═══════════════════════════════════════════════════
        # 3. دفتر الأستاذ
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(LedgerTab(self.acc_conn), "📘  دفتر الأستاذ")

        # ═══════════════════════════════════════════════════
        # 4. القوائم المالية
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(FinancialStatementsTab(self.acc_conn), "📊  القوائم المالية")

        # ═══════════════════════════════════════════════════
        # 5. ميزان المراجعة
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(TrialBalanceTab(self.acc_conn), "⚖️  ميزان المراجعة")

        # ═══════════════════════════════════════════════════
        # 6. المستثمرون — مرتبط بـ erp.db + accounting.db
        # ═══════════════════════════════════════════════════
        investors_widget = InvestorsTab(self.erp_conn, self.acc_conn)
        main_tabs.addTab(investors_widget, "👥  المستثمرون")

        root.addWidget(main_tabs)

    def _build_equity_tab(self) -> QWidget:
        """
        تبويب حقوق الملكية: يجمع الحسابات (رأس مال، مسحوبات، إيرادات، مصروفات)
        + التصنيفات لكل نوع.
        """
        widget = QWidget()
        root   = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        # شجرة الحسابات (كل أنواع الملكية معاً)
        tree_panel = AccountsTreePanel(
            self.acc_conn,
            ["capital", "drawings", "revenue", "expense"],
            "حقوق الملكية والإيرادات والمصروفات"
        )
        splitter.addWidget(tree_panel)

        # التصنيفات لكل نوع في تبويبات داخلية مدمجة
        cat_tabs = _make_inner_tabs(
            ("رأس المال",   _GroupManagerPanel(self.acc_conn, "capital")),
            ("المسحوبات",  _GroupManagerPanel(self.acc_conn, "drawings")),
            ("الإيرادات",  _GroupManagerPanel(self.acc_conn, "revenue")),
            ("المصروفات",  _GroupManagerPanel(self.acc_conn, "expense")),
        )
        splitter.addWidget(cat_tabs)
        splitter.setSizes([600, 300])

        root.addWidget(splitter)
        return widget

    def closeEvent(self, event):
        try:
            self.acc_conn.close()
        except Exception:
            pass
        try:
            self.erp_conn.close()
        except Exception:
            pass
        super().closeEvent(event)