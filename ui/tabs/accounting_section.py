"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

التغييرات:
  - الـ connections لا تُحفَظ كـ instance attributes ثابتة،
    بل تُجلَب من company_state عند كل استخدام.
  - refresh_for_company() تُعيد بناء كل التبويبات عند تغيير الشركة.
  - closeEvent لا يُغلق ProtectedConnection.
  - _is_ready() يتحقق من وجود شركة نشطة قبل أي عملية.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QSplitter,
)
from PyQt5.QtCore import Qt

# ── أجزاء الحسابات ──
from .accounting.accounts_tree        import AccountsTreePanel
from .accounting.group_manager        import _GroupManagerPanel
from .accounting.journal_tab          import JournalTab
from .accounting.ledger_tab           import LedgerTab
from .accounting.financial_statements import (
    TrialBalanceTab,
    FinancialStatementsTab,
)
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


# ══════════════════════════════════════════════════════════
# مساعد: جلب الـ connections دائماً من الشركة النشطة
# ══════════════════════════════════════════════════════════

def _get_acc_conn():
    """يرجع accounting.db connection للشركة النشطة."""
    from db.shared.connection import get_accounting_connection
    return get_accounting_connection()


def _get_erp_conn():
    """يرجع erp.db connection للشركة النشطة."""
    from db.shared.connection import get_connection
    return get_connection()


def _is_ready() -> bool:
    """هل في شركة نشطة؟"""
    from db.companies.company_state import company_state
    return company_state.is_ready


# ══════════════════════════════════════════════════════════
# AccountingTab
# ══════════════════════════════════════════════════════════

class AccountingTab(QWidget):
    """
    التبويب الرئيسي للمحاسبة.

    يَجلُب الـ connections من company_state عند كل بناء أو إعادة بناء،
    لذا تغيير الشركة لا يُبقي بيانات الشركة القديمة مرئية.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
        self._build()

    # ── الحصول على connections ─────────────────────────────

    @property
    def acc_conn(self):
        """دائماً يرجع accounting.db للشركة النشطة."""
        return _get_acc_conn()

    @property
    def erp_conn(self):
        """دائماً يرجع erp.db للشركة النشطة."""
        return _get_erp_conn()

    # ── بناء الواجهة ───────────────────────────────────────

    def _init_schema(self):
        """تهيئة الجداول لو لم تُهيَّأ بعد."""
        if not _is_ready():
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

    def _build(self):
        """بناء (أو إعادة بناء) كل التبويبات."""
        # تنظيف الـ layout القديم
        if self.layout() is not None:
            old_layout = self.layout()
            # احذف كل الـ widgets من الـ layout
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            # احذف الـ layout نفسه
            import sip
            try:
                sip.delete(old_layout)
            except Exception:
                pass

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        if not _is_ready():
            lbl = QLabel("⚠️  اختر شركة أولاً لعرض الحسابات")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                "font-size:14px; color:#888; padding:40px;"
            )
            root.addWidget(lbl)
            return

        self._init_schema()

        # نجلب الـ connections مرة واحدة لهذه الدورة من البناء
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
        main_tabs.addTab(
            JournalTab(acc, erp),
            "📒  قيود اليومية"
        )

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
        main_tabs.addTab(
            InvestorsTab(erp, acc),
            "👥  المستثمرون"
        )

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

    # ── واجهة خارجية: إعادة التهيئة عند تغيير الشركة ──────

    def refresh_for_company(self):
        """
        يُستدعى من MainWindow عند تغيير الشركة النشطة.
        يُعيد بناء كل التبويبات على الـ DB الجديد.
        """
        self._build()

    # ── closeEvent — لا نُغلق ProtectedConnection ──────────

    def closeEvent(self, event):
        """
        ProtectedConnection لا تُغلق هنا — هي مُدارة بواسطة company_state.
        """
        super().closeEvent(event)