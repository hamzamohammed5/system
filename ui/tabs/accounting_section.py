"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

التغييرات (v6):
  - [إصلاح ١] نفس إصلاحات v5 محافظ عليها.
  - [إصلاح ٢ جديد] _build() تتحقق من صحة الـ connection قبل بناء الـ widgets
    لتجنب استخدام connection من شركة قديمة لو company_state تأخر.
  - [إصلاح ٣ جديد] _INITIALIZED_COMPANIES يُمسح دائماً في refresh_for_company()
    قبل أي عملية.
  - [إصلاح ٤ جديد] نضيف _conn_company_id snapshot للتحقق من أن الـ conn
    اللي بنستخدمه فعلاً ينتمي للشركة الحالية.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QSplitter,
)
from PyQt5.QtCore import Qt

from .accounting.accounts_tree        import AccountsTreePanel
from .accounting.group_manager        import _GroupManagerPanel
from .accounting.journal_tab          import JournalTab
from .accounting.ledger_tab           import LedgerTab

from .accounting.financial.trial_balance_tab import TrialBalanceTab
from .accounting.financial_statements        import FinancialStatementsTab

from .accounting.investors_tab import InvestorsTab


_INITIALIZED_COMPANIES: dict[int, str] = {}


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
    tabs = QTabWidget()
    tabs.setStyleSheet(_INNER_TAB_STYLE)
    for label, widget in tab_defs:
        tabs.addTab(widget, label)
    return tabs


def _get_acc_conn():
    from db.shared.connection import get_accounting_connection
    return get_accounting_connection()


def _get_erp_conn():
    from db.shared.connection import get_connection
    return get_connection()


def _is_ready() -> bool:
    from db.companies.company_state import company_state
    return company_state.is_ready


def _current_company_id() -> int | None:
    from db.companies.company_state import company_state
    return company_state.company_id if company_state.is_ready else None


def _current_acc_db_path() -> str | None:
    cid = _current_company_id()
    if cid is None:
        return None
    try:
        from db.companies.companies_schema import get_company_db_path
        return get_company_db_path(cid, "accounting")
    except Exception:
        return None


def _verify_conn_belongs_to_company(conn, expected_company_id: int) -> bool:
    """
    [إصلاح جديد] يتحقق أن الـ connection اللي بنستخدمه
    فعلاً ينتمي للشركة المطلوبة وليس لشركة قديمة.

    يعمل بقراءة مسار الـ DB من الـ connection نفسه
    ومقارنته بالمسار المتوقع للشركة الحالية.
    """
    if conn is None or expected_company_id is None:
        return False
    try:
        from db.companies.companies_schema import get_company_db_path
        expected_path = get_company_db_path(expected_company_id, "accounting")
        # نجرب نقرأ صف واحد — لو فشل الـ conn مش صالح
        conn.execute("SELECT 1").fetchone()

        # نتحقق من اسم الـ DB عبر PRAGMA
        row = conn.execute("PRAGMA database_list").fetchone()
        if row:
            actual_path = row[2] if len(row) > 2 else ""
            # مقارنة المسار بدون حساسية الحالة (Windows)
            import os
            return os.path.normcase(actual_path) == os.path.normcase(expected_path)
    except Exception:
        pass
    return False


class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
        self._company_id: int | None = _current_company_id()
        self._build()

    @property
    def acc_conn(self):
        return _get_acc_conn()

    @property
    def erp_conn(self):
        return _get_erp_conn()

    def _init_schema(self):
        if not _is_ready():
            return

        cid          = _current_company_id()
        current_path = _current_acc_db_path()

        cached_path = _INITIALIZED_COMPANIES.get(cid)
        if cached_path and cached_path == current_path:
            return

        try:
            from db.accounting.accounting_schema import create_accounting_tables
            create_accounting_tables(self.acc_conn)
        except Exception as e:
            print(f"[AccountingTab] schema init error: {e}")

        try:
            from db.inventory.investors_repo import create_investors_tables
            create_investors_tables(self.erp_conn)
        except Exception as e:
            print(f"[AccountingTab] investors schema error: {e}")

        if current_path:
            _INITIALIZED_COMPANIES[cid] = current_path

    def _cleanup_layout(self):
        old_layout = self.layout()
        if old_layout is None:
            return

        while old_layout.count():
            item = old_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.deleteLater()

        dummy = QWidget()
        dummy.setLayout(old_layout)
        dummy.deleteLater()

    def _build(self):
        self._cleanup_layout()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        if not _is_ready():
            lbl = QLabel("⚠️  اختر شركة أولاً لعرض الحسابات")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:14px; color:#888; padding:40px;")
            root.addWidget(lbl)
            return

        self._company_id = _current_company_id()

        # [إصلاح جديد] تحقق من صحة الـ connection قبل البناء
        acc = self.acc_conn
        if not _verify_conn_belongs_to_company(acc, self._company_id):
            # الـ connection لسه بيتجهز — انتظر وحاول مرة ثانية
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self._build)
            lbl = QLabel("⏳  جاري تهيئة قاعدة البيانات...")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:13px; color:#888; padding:40px;")
            root.addWidget(lbl)
            return

        self._init_schema()

        erp = self.erp_conn

        main_tabs = QTabWidget()
        main_tabs.setStyleSheet(_TAB_STYLE)
        self._main_tabs = main_tabs

        accounts_tabs = _make_inner_tabs(
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
             self._build_equity_tab(acc)),
        )
        main_tabs.addTab(accounts_tabs, "🏦  الحسابات")
        main_tabs.addTab(JournalTab(acc, erp), "📒  قيود اليومية")
        main_tabs.addTab(LedgerTab(acc), "📘  دفتر الأستاذ")
        main_tabs.addTab(FinancialStatementsTab(acc), "📊  القوائم المالية")
        main_tabs.addTab(TrialBalanceTab(acc), "⚖️  ميزان المراجعة")
        main_tabs.addTab(InvestorsTab(erp, acc), "👥  المستثمرون")

        root.addWidget(main_tabs)

    def _build_equity_tab(self, acc) -> QWidget:
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

    def refresh_for_company(self):
        """
        يُستدعى من MainWindow عند تغيير الشركة النشطة.
        يمسح الـ cache بالكامل ويُعيد بناء كل التبويبات.
        """
        _INITIALIZED_COMPANIES.clear()
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)