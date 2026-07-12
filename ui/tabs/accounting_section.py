"""
ui/tabs/accounting_section.py
==============================
النافذة المحاسبية الرئيسية — مع دعم كامل لتعدد الشركات.

[تحديث v13] — إصلاح هيكلة:
  - حُذف _conn_guard.py بالكامل. كان يُعيد تنفيذ منطق موجود فعلاً
    وموثوق في db.companies.company_state (path_matches/_get_conn)
    وفي db.companies.companies_repo._init_company_databases().
  - الاتصالات تُجلب الآن من company_state مباشرة (public API):
        company_state.get_erp_conn()
        company_state.get_accounting_conn()
    بدل db.shared.connection (طبقة وسيطة لا تضمن نفس صحة الـ conn
    التي يضمنها company_state._get_conn() داخلياً).
  - لا حاجة لـ verify_conn_belongs_to_company: company_state يغلق
    ويعيد فتح أي connection لا يطابق مسار الشركة النشطة تلقائياً
    (موثّق في _get_conn — path_matches() + real_close() عند الاختلاف).
    السيناريو الذي كان _conn_guard يتحقق منه دفاعيًا غير ممكن الحدوث
    أصلًا عند الاستخدام الصحيح للـ public API.
  - لا حاجة لتهيئة schemas هنا: تتم مرة واحدة في
    companies_repo._init_company_databases() عند إنشاء الشركة.
  - لا حاجة لـ retry loop عبر QTimer: MainWindow._on_company_changed()
    يستدعي _build_tabs() بالكامل عند كل تغيير شركة (راجع ui_root.md)،
    فهذا الـ tab يُعاد بناؤه من جديد تلقائيًا وليس مسؤولًا عن انتظار
    جاهزية الاتصال بنفسه.

[تحديث v12] (محفوظ):
  - tab_style() الموحّد من ui.widgets.theme.layout_styles.
  - كل النصوص عبر tr() — لا نص مباشر.
  - كل الألوان عبر _C من ui.theme.
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
from ui.constants                    import (
    ACCOUNTING_TAB_MSG_PAD, ACCOUNTING_TAB_ERR_RADIUS, ACCOUNTING_TAB_ERR_MARGIN,
)
from ui.widgets.core.widget_mixin   import WidgetMixin

from .accounting.journal_tab   import JournalTab
from .accounting.ledger_tab    import LedgerTab
from .accounting.investors_tab import InvestorsTab

from .accounting.accounting_tabs_builder import (
    build_accounts_tabs,
    build_financial_tab,
    ThemedTabWidget,
    _INNER_TAB_STYLE,
)


class AccountingTab(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_tabs: QTabWidget | None = None
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
        self._main_tabs = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        from services.companies.company_service import CompanyService

        if not CompanyService.is_company_ready():
            lbl = QLabel(tr("accounting_no_company_msg"))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"font-size:{FS_MD}px; color:{_C['text_muted']}; padding:{ACCOUNTING_TAB_MSG_PAD}px;")
            root.addWidget(lbl)
            return

        try:
            acc = CompanyService.get_active_accounting_conn()
            erp = CompanyService.get_active_erp_conn()
            if acc is None or erp is None:
                raise RuntimeError(tr("conn_error_msg", error=""))
        except Exception as e:
            lbl = QLabel(tr("conn_error_msg", error=e))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"font-size:{FS_BASE}px; color:{_C['danger']}; padding:{ACCOUNTING_TAB_MSG_PAD}px;"
                f"background:{_C['danger_bg']}; border-radius:{ACCOUNTING_TAB_ERR_RADIUS}px; margin:{ACCOUNTING_TAB_ERR_MARGIN}px;"
            )
            root.addWidget(lbl)
            return

        # [إصلاح dark-mode] القديم: QTabWidget() + setStyleSheet(tab_style()) ثابت.
        # ThemedTabWidget بيسجل نفسه على bus.theme_changed تلقائيًا عبر
        # WidgetMixin، فمش محتاجين نعتمد بس على _refresh_style اليدوية هنا
        # في الأب — ده بيضمن التلوين حتى لو AccountingTab._refresh_style
        # اتأخرت أو الترتيب اختلف.
        main_tabs = ThemedTabWidget(size="normal")
        self._main_tabs = main_tabs

        main_tabs.addTab(build_accounts_tabs(acc),  tr("accounts_tab"))
        main_tabs.addTab(JournalTab(acc, erp),       tr("journal_tab"))
        main_tabs.addTab(LedgerTab(acc),             tr("ledger_tab"))
        main_tabs.addTab(build_financial_tab(acc),   tr("financial_tab"))
        main_tabs.addTab(InvestorsTab(erp, acc),     tr("investors_tab"))

        root.addWidget(main_tabs)

    def _refresh_style(self, *_):
        # [حماية إضافية] main_tabs بقى ThemedTabWidget ومسجل لوحده على
        # bus.theme_changed، فمن المفروض يتلوّن تلقائيًا. الاستدعاء هنا
        # طبقة أمان إضافية بس (نفس فلسفة _AccountForm._refresh_style) —
        # لا يضر لو اتنفذ مرتين.
        if self._main_tabs is not None and hasattr(self._main_tabs, "_refresh_style"):
            self._main_tabs._refresh_style()

    def refresh_for_company(self):
        self._build()

    def closeEvent(self, event):
        super().closeEvent(event)
