"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

[تحديث v11]:
  - منطق التحقق من الـ conn انتقل لـ accounting/_conn_guard.py.
  - بناء التبويبات عبر accounting_tabs_builder.py (كما كان).
  - هذا الملف يركز على دورة الحياة (lifecycle) فقط.
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
    _INNER_TAB_STYLE,
)
from .accounting._conn_guard import (
    is_ready,
    get_current_company_id,
    get_acc_conn,
    get_erp_conn,
    verify_conn_belongs_to_company,
    init_schemas,
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


class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
        self._company_id = get_current_company_id()
        self._initialized: dict[int, str] = {}
        self._build_attempts = 0
        self._build()

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

        if not is_ready():
            lbl = QLabel("⚠️  اختر شركة أولاً لعرض الحسابات")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:14px; color:#888; padding:40px;")
            root.addWidget(lbl)
            return

        self._company_id = get_current_company_id()

        try:
            acc = get_acc_conn()
            erp = get_erp_conn()
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

        if not verify_conn_belongs_to_company(acc, self._company_id):
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
        init_schemas(acc, erp, self._initialized)

        main_tabs = QTabWidget()
        main_tabs.setStyleSheet(_TAB_STYLE)
        self._main_tabs = main_tabs

        main_tabs.addTab(build_accounts_tabs(acc),  "🏦  الحسابات")
        main_tabs.addTab(JournalTab(acc, erp),       "📒  قيود اليومية")
        main_tabs.addTab(LedgerTab(acc),             "📘  دفتر الأستاذ")
        main_tabs.addTab(build_financial_tab(acc),   "📊  القوائم المالية")
        main_tabs.addTab(InvestorsTab(erp, acc),     "👥  المستثمرون")

        root.addWidget(main_tabs)

    def refresh_for_company(self):
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)