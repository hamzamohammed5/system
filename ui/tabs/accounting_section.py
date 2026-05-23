"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

إصلاحات (v7):
  ١. إزالة _INITIALIZED_COMPANIES الـ global — استبداله بـ instance dict مرتبط
     بـ company_id + db_path لضمان إعادة التهيئة الصحيحة دايماً.
  ٢. _verify_conn_belongs_to_company أكثر أماناً عبر query مباشرة على الـ DB.
  ٣. TrialBalanceTab يتضمن داخل FinancialStatementsTab مع نفس الـ connection.
  ٤. _get_current_company_id يُستدعى فقط بعد التحقق من is_ready.
  ٥. كل الـ child widgets تأخذ company_id وقت البناء لضمان الإستقرار.
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

from .accounting.financial.trial_balance_tab    import TrialBalanceTab
from .accounting.financial.income_statement_tab import IncomeStatementTab
from .accounting.financial.owners_equity_tab    import OwnersEquityTab
from .accounting.financial.balance_sheet_tab    import BalanceSheetTab

from .accounting.investors_tab import InvestorsTab


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
    [إصلاح v7] تحقق مباشر عبر PRAGMA database_list مع fallback آمن.
    يتجنب مشاكل os.path.normcase على Windows مع المسارات النسبية.
    """
    if conn is None or expected_company_id is None:
        return False
    try:
        import os
        from db.companies.companies_schema import get_company_db_path

        # تحقق أن الـ connection حي أولاً
        conn.execute("SELECT 1").fetchone()

        # جيب مسار الـ DB الحالي من الـ connection
        row = conn.execute("PRAGMA database_list").fetchone()
        if not row:
            return False

        actual_path   = row[2] if len(row) > 2 else ""
        expected_path = get_company_db_path(expected_company_id, "accounting")

        # تطبيع المسارين قبل المقارنة
        actual_norm   = os.path.normcase(os.path.realpath(actual_path))
        expected_norm = os.path.normcase(os.path.realpath(expected_path))
        return actual_norm == expected_norm

    except Exception:
        # لو PRAGMA فشل أو الـ connection مغلق → مش صالح
        return False


class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
        self._company_id: int | None = _current_company_id()

        # [إصلاح v7] instance-level cache بدل global — مرتبط بالشركة + المسار
        # الشكل: {company_id: acc_db_path}
        self._initialized: dict[int, str] = {}

        self._build()

    @property
    def acc_conn(self):
        return _get_acc_conn()

    @property
    def erp_conn(self):
        return _get_erp_conn()

    def _init_schema(self):
        """
        يُهيئ الـ schema مرة واحدة لكل (company_id + acc_db_path).
        يضمن إعادة التهيئة لو الشركة اتحذفت وأُعيد إنشاؤها.
        """
        if not _is_ready():
            return

        cid          = _current_company_id()
        current_path = _current_acc_db_path()

        # تحقق من الـ cache — نفس الشركة ونفس المسار فقط يتخطى التهيئة
        cached_path = self._initialized.get(cid)
        if cached_path and cached_path == current_path:
            return

        # تهيئة schema الحسابات
        try:
            from db.accounting.accounting_schema import create_accounting_tables
            create_accounting_tables(self.acc_conn)
        except Exception as e:
            print(f"[AccountingTab] schema init error: {e}")

        # تهيئة schema المستثمرين
        try:
            from db.inventory.investors_repo import create_investors_tables
            create_investors_tables(self.erp_conn)
        except Exception as e:
            print(f"[AccountingTab] investors schema error: {e}")

        # سجّل التهيئة في الـ cache
        if current_path:
            self._initialized[cid] = current_path

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

        # [إصلاح v7] تحقق من صحة الـ connection — مع retry آمن
        acc = self.acc_conn
        if not _verify_conn_belongs_to_company(acc, self._company_id):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(120, self._build)
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

        # ── تبويب الحسابات ──
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

        # [إصلاح v7] القوائم المالية تشمل ميزان المراجعة داخلها
        main_tabs.addTab(self._build_financial_tab(acc), "📊  القوائم المالية")

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

    def _build_financial_tab(self, acc) -> QWidget:
        """
        [إصلاح v7] يجمع كل القوائم المالية + ميزان المراجعة
        في tabs تحت نفس الـ connection — بدل بناء TrialBalanceTab منفصل.
        """
        tabs = QTabWidget()
        tabs.setStyleSheet(_INNER_TAB_STYLE)
        tabs.addTab(IncomeStatementTab(acc), "📊 قائمة الدخل")
        tabs.addTab(OwnersEquityTab(acc),    "👑 حقوق الملكية")
        tabs.addTab(BalanceSheetTab(acc),    "🏛️ الميزانية العمومية")
        tabs.addTab(TrialBalanceTab(acc),    "⚖️ ميزان المراجعة")
        return tabs

    def refresh_for_company(self):
        """
        يُستدعى من MainWindow عند تغيير الشركة النشطة.
        [إصلاح v7] يمسح فقط الـ cache الخاص بالشركة القديمة،
        ولا يمسح كل الـ cache عشان لو رجعنا للشركة القديمة يتعرف عليها.
        """
        # لا نمسح الـ cache كله — نمسح فقط لو المسار اتغير
        # البناء نفسه سيتحقق عبر _verify_conn_belongs_to_company
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)