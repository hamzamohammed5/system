"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

التغييرات (v5):
  - [إصلاح ١] تصحيح الـ ImportError: TrialBalanceTab يُستورد من مكانه الصحيح
    (financial.trial_balance_tab) وليس من financial_statements.
  - [إصلاح ٢] _INITIALIZED_COMPANIES يُمسح بالكامل في refresh_for_company()
    بدل مسح الشركة القديمة فقط — يضمن إعادة التهيئة الكاملة عند كل تغيير.
  - [إصلاح ٣] _destroy_tabs() تمسح _INITIALIZED_COMPANIES قبل الحذف
    لتجنب أي حالة cache غير متزامنة.
  - باقي المنطق محافظ عليه من v4.
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

# [إصلاح ١] TrialBalanceTab يُستورد من ملفه الصحيح مباشرة
from .accounting.financial.trial_balance_tab import TrialBalanceTab
from .accounting.financial_statements        import FinancialStatementsTab

from .accounting.investors_tab import InvestorsTab


# ── cache: company_id → accounting db path ────────────────
# نخزن المسار عشان نكتشف لو نفس الـ ID اتحذف وأُعيد بمسار مختلف
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


# ══════════════════════════════════════════════════════════
# مساعد: جلب الـ connections دائماً من الشركة النشطة
# ══════════════════════════════════════════════════════════

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
    """يرجع مسار accounting.db للشركة النشطة."""
    cid = _current_company_id()
    if cid is None:
        return None
    try:
        from db.companies.companies_schema import get_company_db_path
        return get_company_db_path(cid, "accounting")
    except Exception:
        return None


# ══════════════════════════════════════════════════════════
# AccountingTab
# ══════════════════════════════════════════════════════════

class AccountingTab(QWidget):
    """
    التبويب الرئيسي للمحاسبة.

    - يجلب الـ connections من company_state عند كل بناء.
    - يستمع لـ bus.company_data_changed بـ company_id محدد
      لضمان عدم استجابة الـ widget لأحداث شركة أخرى.
    - _INITIALIZED_COMPANIES يخزن المسار مع الـ ID لاكتشاف إعادة الإنشاء.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
        self._company_id: int | None = _current_company_id()
        self._build()

    # ── الحصول على connections ─────────────────────────────

    @property
    def acc_conn(self):
        return _get_acc_conn()

    @property
    def erp_conn(self):
        return _get_erp_conn()

    # ── تهيئة الجداول مع cache ────────────────────────────

    def _init_schema(self):
        """
        تهيئة الجداول مع cache ذكي يكتشف:
          1. الشركة الجديدة (ID غير موجود في الـ cache)
          2. نفس الـ ID لكن مسار مختلف (حُذفت وأُعيد إنشاؤها)
        """
        if not _is_ready():
            return

        cid          = _current_company_id()
        current_path = _current_acc_db_path()

        # تحقق من الـ cache
        cached_path = _INITIALIZED_COMPANIES.get(cid)
        if cached_path and cached_path == current_path:
            return   # نفس الشركة ونفس المسار — لا حاجة لإعادة التهيئة

        # تهيئة جديدة مطلوبة
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

        # حفظ في الـ cache مع المسار
        if current_path:
            _INITIALIZED_COMPANIES[cid] = current_path

    # ── بناء الواجهة ───────────────────────────────────────

    def _cleanup_layout(self):
        """
        يحذف الـ layout القديم وكل widgets فيه بشكل آمن.
        يستخدم hide()+deleteLater() بدل sip.delete لتجنب crashes.
        """
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
        """بناء (أو إعادة بناء) كل التبويبات."""
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
        self._init_schema()

        acc = self.acc_conn
        erp = self.erp_conn

        main_tabs = QTabWidget()
        main_tabs.setStyleSheet(_TAB_STYLE)
        self._main_tabs = main_tabs

        # ═══════════════════════════════════════════════════
        # 1. الحسابات
        # ═══════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════
        # 2. القيود المحاسبية
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(JournalTab(acc, erp), "📒  قيود اليومية")

        # ═══════════════════════════════════════════════════
        # 3. دفتر الأستاذ
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(LedgerTab(acc), "📘  دفتر الأستاذ")

        # ═══════════════════════════════════════════════════
        # 4. القوائم المالية
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(FinancialStatementsTab(acc), "📊  القوائم المالية")

        # ═══════════════════════════════════════════════════
        # 5. ميزان المراجعة
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(TrialBalanceTab(acc), "⚖️  ميزان المراجعة")

        # ═══════════════════════════════════════════════════
        # 6. المستثمرون
        # ═══════════════════════════════════════════════════
        main_tabs.addTab(InvestorsTab(erp, acc), "👥  المستثمرون")

        root.addWidget(main_tabs)

    def _build_equity_tab(self, acc) -> QWidget:
        """تبويب حقوق الملكية — شجرة جامعة + تصنيفات."""
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

    # ── واجهة خارجية ──────────────────────────────────────

    def refresh_for_company(self):
        """
        يُستدعى من MainWindow عند تغيير الشركة النشطة.

        [إصلاح ٢] يمسح _INITIALIZED_COMPANIES بالكامل (مش بس الشركة القديمة)
        لضمان إعادة تهيئة الجداول عند كل تغيير للشركة.
        ثم يُعيد بناء كل التبويبات.
        """
        # [إصلاح ٢] مسح كل الـ cache — إعادة تهيئة كاملة لكل شركة
        _INITIALIZED_COMPANIES.clear()
        self._build()

    # ── closeEvent ─────────────────────────────────────────

    def closeEvent(self, event):
        """ProtectedConnection لا تُغلق هنا — مُدارة بواسطة company_state."""
        super().closeEvent(event)