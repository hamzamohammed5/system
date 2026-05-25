"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

[تحديث v12]:
  - _TAB_STYLE حُذف — يستخدم get_tab_style() من theme مباشرة.
  - _build_tabs موحدة مع make_tabs من tab_builder.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel,
)
from PyQt5.QtCore import Qt, QTimer

from .accounting.journal_tab   import JournalTab
from .accounting.ledger_tab    import LedgerTab
from .accounting.investors_tab import InvestorsTab

from .accounting.accounting_tabs_builder import (
    build_accounts_tabs,
    build_financial_tab,
)
from .accounting._conn_guard import (
    is_ready,
    get_current_company_id,
    get_acc_conn,
    get_erp_conn,
    verify_conn_belongs_to_company,
    init_schemas,
)
from ui.widgets.shared.panels import make_tabs, get_tab_style
from ui.widgets.shared.panles_helper.theme import get_tab_style


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

            QTimer.singleShot(120, self._build)
            lbl = QLabel(f"⏳  جاري تهيئة قاعدة البيانات... ({self._build_attempts}/5)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:13px; color:#888; padding:40px;")
            root.addWidget(lbl)
            return

        self._build_attempts = 0
        init_schemas(acc, erp, self._initialized)

        # ← يستخدم make_tabs من tab_builder بدل QTabWidget يدوي
        main_tabs = make_tabs(
            ("🏦  الحسابات",     build_accounts_tabs(acc)),
            ("📒  قيود اليومية", JournalTab(acc, erp)),
            ("📘  دفتر الأستاذ", LedgerTab(acc)),
            ("📊  القوائم المالية", build_financial_tab(acc)),
            ("👥  المستثمرون",  InvestorsTab(erp, acc)),
            style="main",
        )
        self._main_tabs = main_tabs
        root.addWidget(main_tabs)

    def refresh_for_company(self):
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)