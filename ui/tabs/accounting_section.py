"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

إصلاحات (v9):
  ١. حذف acc_conn و erp_conn properties — كانوا يفتحون connection جديد في كل call.
  ٢. _build() تجيب acc و erp مرة واحدة وتمررهم صريح لكل الدوال.
  ٣. _init_schema استُبدلت بـ _init_schema_with_conn(acc, erp) تستقبل conn صريح.
  ٤. _build_equity_tab و _build_financial_tab يستقبلان acc صريح (كانوا كذلك).
  ٥. باقي الإصلاحات من v8 محافظ عليها.
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
    """تحقق مباشر عبر PRAGMA database_list مع fallback آمن."""
    if conn is None or expected_company_id is None:
        return False
    try:
        import os
        from db.companies.companies_schema import get_company_db_path

        conn.execute("SELECT 1").fetchone()

        row = conn.execute("PRAGMA database_list").fetchone()
        if not row:
            return False

        actual_path   = row[2] if len(row) > 2 else ""
        expected_path = get_company_db_path(expected_company_id, "accounting")

        actual_norm   = os.path.normcase(os.path.realpath(actual_path))
        expected_norm = os.path.normcase(os.path.realpath(expected_path))
        return actual_norm == expected_norm

    except Exception:
        return False


class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
        self._company_id: int | None = _current_company_id()
        self._initialized: dict[int, str] = {}
        self._build_attempts = 0
        self._build()

    # ── تمت إزالة acc_conn و erp_conn properties ──────────────────────────
    # كانتا تفتحان connection جديد في كل call عبر _get_acc_conn()/_get_erp_conn()
    # الآن يُجلب acc و erp مرة واحدة في _build() ويُمرران صريحاً لكل الدوال.

    def _init_schema_with_conn(self, acc, erp):
        """
        تهيئة Schema باستخدام conn مُمرر صريحاً.
        استبدلت _init_schema() التي كانت تستخدم self.acc_conn property.
        """
        if not _is_ready():
            return

        cid          = _current_company_id()
        current_path = _current_acc_db_path()

        cached_path = self._initialized.get(cid)
        if cached_path and cached_path == current_path:
            return

        try:
            from db.accounting.accounting_schema import create_accounting_tables
            create_accounting_tables(acc)
        except Exception as e:
            print(f"[AccountingTab] schema init error: {e}")

        try:
            from db.inventory.investors_repo import create_investors_tables
            create_investors_tables(erp)
        except Exception as e:
            print(f"[AccountingTab] investors schema error: {e}")

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
        self._build_attempts += 1

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        if not _is_ready():
            lbl = QLabel("⚠️  اختر شركة أولاً لعرض الحسابات")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:14px; color:#888; padding:40px;")
            root.addWidget(lbl)
            return

        self._company_id = _current_company_id()

        # ── الإصلاح الجوهري: جيب acc و erp مرة واحدة فقط في _build ──────
        # بدل properties كانت تفتح connection جديد في كل call
        try:
            acc = _get_acc_conn()
            erp = _get_erp_conn()
        except Exception as e:
            lbl = QLabel(f"❌  خطأ في الاتصال بقاعدة البيانات:\n{e}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                "font-size:13px; color:#c62828; padding:40px;"
                "background:#fdecea; border-radius:8px; margin:20px;"
            )
            root.addWidget(lbl)
            return

        if not _verify_conn_belongs_to_company(acc, self._company_id):
            # حد أقصى 5 محاولات (5 × 120ms = 600ms)
            if self._build_attempts >= 5:
                lbl = QLabel(
                    "❌  تعذّر تهيئة قاعدة بيانات المحاسبة\n"
                    "جرّب إعادة تشغيل البرنامج أو تحديد الشركة مجدداً"
                )
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    "font-size:13px; color:#c62828; padding:40px;"
                    "background:#fdecea; border-radius:8px; margin:20px;"
                )
                root.addWidget(lbl)
                self._build_attempts = 0    # reset للمحاولة القادمة
                return

            from PyQt5.QtCore import QTimer
            attempt_num = self._build_attempts
            QTimer.singleShot(120, self._build)
            lbl = QLabel(
                f"⏳  جاري تهيئة قاعدة البيانات... ({attempt_num}/5)"
            )
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:13px; color:#888; padding:40px;")
            root.addWidget(lbl)
            return

        # نجح التحقق — أعد العداد
        self._build_attempts = 0

        # ── تهيئة Schema بتمرير acc و erp صريحاً ─────────────────────────
        self._init_schema_with_conn(acc, erp)

        main_tabs = QTabWidget()
        main_tabs.setStyleSheet(_TAB_STYLE)
        self._main_tabs = main_tabs

        # ── تبويب الحسابات ─────────────────────────────────────────────────
        # acc يُمرر صريحاً لكل widget — لا properties، لا connections مخفية
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
        main_tabs.addTab(accounts_tabs,                   "🏦  الحسابات")
        main_tabs.addTab(JournalTab(acc, erp),            "📒  قيود اليومية")
        main_tabs.addTab(LedgerTab(acc),                  "📘  دفتر الأستاذ")
        main_tabs.addTab(self._build_financial_tab(acc),  "📊  القوائم المالية")
        main_tabs.addTab(InvestorsTab(erp, acc),          "👥  المستثمرون")

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
        tabs = QTabWidget()
        tabs.setStyleSheet(_INNER_TAB_STYLE)
        tabs.addTab(IncomeStatementTab(acc), "📊 قائمة الدخل")
        tabs.addTab(OwnersEquityTab(acc),    "👑 حقوق الملكية")
        tabs.addTab(BalanceSheetTab(acc),    "🏛️ الميزانية العمومية")
        tabs.addTab(TrialBalanceTab(acc),    "⚖️ ميزان المراجعة")
        return tabs

    def refresh_for_company(self):
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)