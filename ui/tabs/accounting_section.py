"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

[تحديث v10]:
  - بناء التبويبات الفرعية انتقل لـ accounting_tabs_builder.py
  - هذا الملف يركز على دورة الحياة (lifecycle) فقط:
    init → verify conn → build → refresh_for_company
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel,
)
from PyQt5.QtCore import Qt

from .accounting.journal_tab   import JournalTab
from .accounting.ledger_tab    import LedgerTab
from .accounting.investors_tab import InvestorsTab

from .accounting.accounting_tabs_builder import (
    build_accounts_tabs,
    build_financial_tab,
    _INNER_TAB_STYLE,          # للـ main tabs
)


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


def _get_acc_conn():
    from db.shared.connection import get_accounting_connection
    return get_accounting_connection()


def _get_erp_conn():
    from db.shared.connection import get_connection
    return get_connection()


def _is_ready() -> bool:
    from db.companies.company_state import company_state
    return company_state.is_ready


def _current_company_id():
    from db.companies.company_state import company_state
    return company_state.company_id if company_state.is_ready else None


def _current_acc_db_path():
    cid = _current_company_id()
    if cid is None:
        return None
    try:
        from db.companies.companies_schema import get_company_db_path
        return get_company_db_path(cid, "accounting")
    except Exception:
        return None


def _verify_conn_belongs_to_company(conn, expected_company_id: int) -> bool:
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
        self._company_id = _current_company_id()
        self._initialized: dict[int, str] = {}
        self._build_attempts = 0
        self._build()

    def _init_schema_with_conn(self, acc, erp):
        if not _is_ready():
            return

        cid          = _current_company_id()
        current_path = _current_acc_db_path()
        cached_path  = self._initialized.get(cid)
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
                self._build_attempts = 0
                return

            from PyQt5.QtCore import QTimer
            attempt_num = self._build_attempts
            QTimer.singleShot(120, self._build)
            lbl = QLabel(f"⏳  جاري تهيئة قاعدة البيانات... ({attempt_num}/5)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:13px; color:#888; padding:40px;")
            root.addWidget(lbl)
            return

        self._build_attempts = 0
        self._init_schema_with_conn(acc, erp)

        main_tabs = QTabWidget()
        main_tabs.setStyleSheet(_TAB_STYLE)
        self._main_tabs = main_tabs

        # ── بناء التبويبات عبر accounting_tabs_builder ──
        main_tabs.addTab(build_accounts_tabs(acc),       "🏦  الحسابات")
        main_tabs.addTab(JournalTab(acc, erp),           "📒  قيود اليومية")
        main_tabs.addTab(LedgerTab(acc),                 "📘  دفتر الأستاذ")
        main_tabs.addTab(build_financial_tab(acc),       "📊  القوائم المالية")
        main_tabs.addTab(InvestorsTab(erp, acc),         "👥  المستثمرون")

        root.addWidget(main_tabs)

    def refresh_for_company(self):
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)