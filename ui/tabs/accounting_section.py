"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

[تحديث v12]:
  - _TAB_STYLE حُذف — يستخدم get_tab_style() من theme مباشرة.
  - _build_tabs موحدة مع make_tabs من tab_builder.

[تحديث v13]:
  - حذف الاستيراد المكرر لـ get_tab_style (كان يُستورد من panels ثم يُستبدل من theme).
  - استخدام _state_widgets بدل بناء QLabel الأخطاء يدوياً.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
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
from .accounting._state_widgets import (
    make_no_company_widget,
    make_conn_error_widget,
    make_init_failed_widget,
    make_loading_widget,
)
from ui.widgets.shared.panels import make_tabs
from ui.widgets.shared.panles_helper.theme import get_tab_style  # noqa: F401


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
            root.addWidget(make_no_company_widget())
            return

        self._company_id = get_current_company_id()

        try:
            acc = get_acc_conn()
            erp = get_erp_conn()
        except Exception as e:
            root.addWidget(make_conn_error_widget(e))
            return

        if not verify_conn_belongs_to_company(acc, self._company_id):
            if self._build_attempts >= 5:
                root.addWidget(make_init_failed_widget())
                self._build_attempts = 0
                return

            QTimer.singleShot(120, self._build)
            root.addWidget(make_loading_widget(self._build_attempts))
            return

        self._build_attempts = 0
        init_schemas(acc, erp, self._initialized)

        main_tabs = make_tabs(
            ("🏦  الحسابات",        build_accounts_tabs(acc)),
            ("📒  قيود اليومية",    JournalTab(acc, erp)),
            ("📘  دفتر الأستاذ",    LedgerTab(acc)),
            ("📊  القوائم المالية", build_financial_tab(acc)),
            ("👥  المستثمرون",      InvestorsTab(erp, acc)),
            style="main",
        )
        self._main_tabs = main_tabs
        root.addWidget(main_tabs)

    def refresh_for_company(self):
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)