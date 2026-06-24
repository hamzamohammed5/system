"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

[تحديث v11]:
  - منطق التحقق من الـ conn انتقل لـ accounting/_conn_guard.py.
  - بناء التبويبات عبر accounting_tabs_builder.py (كما كان).
  - هذا الملف يركز على دورة الحياة (lifecycle) فقط.

[تحديث v12]:
  - استبدال _TAB_STYLE المحلي بـ tab_style() الموحّد من ui.widgets.theme.layout_styles.
  - كل النصوص عبر tr() (ar.py / en.py) — لا نص مباشر.
  - كل الألوان عبر _C من ui.theme (المصدر: ui.theme_manager).
  - كل أحجام الخط عبر font.py (FS_*).
  - تحديث الثيم الديناميكي عبر bus.theme_changed.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel,
)
from PyQt5.QtCore import Qt

from ui.widgets.theme.layout_styles import tab_style
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.font                        import FS_BASE, FS_MD
from ui.widgets.core.widget_mixin   import WidgetMixin

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


class AccountingTab(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
        self._company_id = get_current_company_id()
        self._initialized: dict[int, str] = {}
        self._build_attempts = 0
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)

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
        self._main_tabs = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        if not is_ready():
            lbl = QLabel(tr("accounting_no_company_msg"))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"font-size:{FS_MD}px; color:{_C['text_muted']}; padding:40px;")
            root.addWidget(lbl)
            return

        self._company_id = get_current_company_id()

        try:
            acc = get_acc_conn()
            erp = get_erp_conn()
        except Exception as e:
            lbl = QLabel(tr("conn_error_msg", error=e))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"font-size:{FS_BASE}px; color:{_C['danger']}; padding:40px;"
                f"background:{_C['danger_bg']}; border-radius:8px; margin:20px;"
            )
            root.addWidget(lbl)
            return

        if not verify_conn_belongs_to_company(acc, self._company_id):
            if self._build_attempts >= 5:
                lbl = QLabel(tr("init_failed_msg"))
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    f"font-size:{FS_BASE}px; color:{_C['danger']}; padding:40px;"
                    f"background:{_C['danger_bg']}; border-radius:8px; margin:20px;"
                )
                root.addWidget(lbl)
                self._build_attempts = 0
                return

            from PyQt5.QtCore import QTimer
            attempt_num = self._build_attempts
            QTimer.singleShot(120, self._build)
            lbl = QLabel(tr("loading_db_msg", attempt=attempt_num, max=5))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"font-size:{FS_BASE}px; color:{_C['text_muted']}; padding:40px;")
            root.addWidget(lbl)
            return

        self._build_attempts = 0
        init_schemas(acc, erp, self._initialized)

        main_tabs = QTabWidget()
        main_tabs.setStyleSheet(tab_style())
        self._main_tabs = main_tabs

        main_tabs.addTab(build_accounts_tabs(acc),  tr("accounts_tab"))
        main_tabs.addTab(JournalTab(acc, erp),       tr("journal_tab"))
        main_tabs.addTab(LedgerTab(acc),             tr("ledger_tab"))
        main_tabs.addTab(build_financial_tab(acc),   tr("financial_tab"))
        main_tabs.addTab(InvestorsTab(erp, acc),     tr("investors_tab"))

        root.addWidget(main_tabs)

    def _refresh_style(self, *_):
        if self._main_tabs is not None:
            self._main_tabs.setStyleSheet(tab_style())

    def refresh_for_company(self):
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)