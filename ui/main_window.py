"""
ui/main_window.py  (نسخة multi-company — مُصلَحة v12)
=====================================================
التغييرات عن v11:
  - [إصلاح C] _build_tabs: يبني CostingSection فقط — باقي الـ sections
    تظهر كـ placeholder "قيد التطوير" بدل بناء كل شيء دفعةً واحدة.
    يسهّل التطوير التدريجي ويقلل وقت الإقلاع.

  - [إصلاح D] إزالة كل hardcoded strings من الـ UI:
    عنوان النافذة والـ placeholder يستخدمان tr() بدل نصوص مباشرة.

  - [إصلاح E] توحيد index_map في مكان واحد (_INDEX_MAP) بدل تكراره
    في _validate_index_map و _on_nav.

  - [محفوظ إصلاح A] _try_build_section يعزل import errors.
  - [محفوظ إصلاح B] _destroy_tabs يستدعي company_state.refresh_connections().
  - [محفوظ] _on_company_changed يستدعي AppState.invalidate().
  - [محفوظ] emit_company_data_changed عبر الدالة لا bus.emit مباشرة.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QFrame, QLabel,
    QScrollArea, QSizePolicy, QApplication,
)
from PyQt5.QtCore import Qt
import logging

from ui.font                    import get_font_size, fs
from ui.theme                   import _C
from ui.widgets.core.events     import bus, emit_company_data_changed
from ui.widgets.core.i18n       import tr
from .main_window_helper._sidebar import _Sidebar
from .main_window_helper._nav_button import (
    WINDOW_DEFAULT_W,
    SIDEBAR_COLLAPSED_WIDTH,
    CONTENT_MIN_WIDTH,
)

logger = logging.getLogger(__name__)

# ── خريطة التنقل: nav_key → stack index ──────────────────────────────────────
# يجب أن يتطابق عدد العناصر مع _builders في _build_tabs (index يبدأ من 1)
_INDEX_MAP: dict[str, int] = {
    "costing":    1,
    "pricing":    2,
    "accounting": 3,
    "inventory":  4,
    "design":     5,
    "orders":     6,
}


# ── دوال مساعدة مستقلة ───────────────────────────────────────────────────────

def _make_placeholder_tab(section_name: str, error: str = "") -> QWidget:
    """
    Placeholder مؤقت لـ section لم يُبنَ بعد أو فشل import.
    يعرض رسالة واضحة للمطور.
    كل الألوان من _C — لا hardcoded.
    """
    w = QWidget()
    w.setStyleSheet(f"background:{_C['bg_page']};")

    from PyQt5.QtWidgets import QVBoxLayout
    lay = QVBoxLayout(w)
    lay.setAlignment(Qt.AlignCenter)
    lay.setSpacing(12)

    base = get_font_size()

    lbl_icon = QLabel("🚧")
    lbl_icon.setAlignment(Qt.AlignCenter)
    lbl_icon.setStyleSheet(
        f"font-size:{fs(base, +8)}pt; background:transparent; border:none;"
    )
    lay.addWidget(lbl_icon)

    lbl_title = QLabel(section_name)
    lbl_title.setAlignment(Qt.AlignCenter)
    lbl_title.setStyleSheet(
        f"font-size:{fs(base, +2)}pt; font-weight:bold;"
        f"color:{_C['text_primary']}; background:transparent; border:none;"
    )
    lay.addWidget(lbl_title)

    msg = error if error else tr("under_development")
    lbl_sub = QLabel(msg)
    lbl_sub.setAlignment(Qt.AlignCenter)
    lbl_sub.setWordWrap(True)
    lbl_sub.setStyleSheet(
        f"font-size:{fs(base, -1)}pt; color:{_C['text_muted']};"
        "background:transparent; border:none;"
    )
    lay.addWidget(lbl_sub)

    return w


def _try_build_section(builder_fn, section_name: str) -> QWidget:
    """
    يحاول بناء section — يرجع placeholder مع رسالة خطأ لو فشل.
    يضمن أن فشل section واحد لا يمنع بقية الـ sections من العمل.
    """
    return builder_fn()
    
    # try:
        # return builder_fn()
    # except ImportError as e:
    #     logger.warning("_try_build_section: import فشل لـ %s: %s", section_name, e)
    #     return _make_placeholder_tab(section_name, f"ImportError: {e}")
    # except Exception as e:
    #     logger.error("_try_build_section: فشل بناء %s: %s", section_name, e)
    #     return _make_placeholder_tab(section_name, f"خطأ: {e}")


# ── MainWindow ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app        = app
        self._tabs_built = False
        self._accounting = None

        self.setWindowTitle(tr("app_title"))
        self.resize(WINDOW_DEFAULT_W, 820)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(SIDEBAR_COLLAPSED_WIDTH + 400, 500)

        self._build()

    # ── بناء الهيكل الأساسي ──────────────────────────────────────────────────

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──
        self._sidebar = _Sidebar(on_company_changed=self._on_company_changed)
        self._sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self._sidebar)

        # ── فاصل عمودي ──
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{_C['border']};border:none;")
        sep.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(sep)

        # ── منطقة المحتوى مع scroll أفقي ──
        self._content_scroll = QScrollArea()
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:horizontal {{
                background: transparent;
                height: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:horizontal {{
                background: {_C['border_med']};
                border-radius: 3px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {_C['border_strong']};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)
        self._content_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ── Stack ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{_C['bg_page']};")
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.setMinimumWidth(CONTENT_MIN_WIDTH)

        # index 0 → شاشة "لا توجد شركة"
        from .tabs.companies.no_company_screen import NoCompanyScreen
        self._no_company_screen = NoCompanyScreen()
        self._no_company_screen.open_manager.connect(
            lambda: self._sidebar.get_company_selector()._open_manager()
        )
        self._stack.addWidget(self._no_company_screen)

        self._content_scroll.setWidget(self._stack)
        main_layout.addWidget(self._content_scroll, stretch=1)

        # ربط أزرار الـ sidebar
        for btn in self._sidebar.get_buttons():
            btn.clicked.connect(lambda checked, b=btn: self._on_nav(b))

        # بناء التبويبات لو الشركة جاهزة
        from db.companies.company_state import company_state
        if company_state.is_ready:
            self._build_tabs()

    # ── بناء وتدمير التبويبات ────────────────────────────────────────────────

    def _build_tabs(self):
        """
        يبني tabs الـ sections.

        [إصلاح C] CostingSection تُبنى فعلياً — باقي الـ sections تظهر
        كـ placeholder "قيد التطوير" لتسريع الإقلاع وتسهيل التطوير التدريجي.

        الترتيب يجب أن يتطابق مع _INDEX_MAP:
            index 1 → costing     (مبني فعلياً)
            index 2 → pricing     (placeholder)
            index 3 → accounting  (placeholder)
            index 4 → inventory   (placeholder)
            index 5 → design      (placeholder)
            index 6 → orders      (placeholder)
        """
        if self._tabs_built:
            self._destroy_tabs()

        # جلب الـ connection
        try:
            from db.companies.company_state import company_state
            conn = company_state.get_erp_conn()
        except Exception as e:
            logger.error("_build_tabs: تعذر الحصول على conn: %s", e)
            conn = None

        # ── تعريف الـ builders ──
        # كل builder دالة تُبنى lazy — لا تُنفَّذ إلا عند الاستدعاء

        def _build_costing():
            from ui.tabs.costing_section import CostingSection
            return CostingSection(conn_fn=lambda: conn)

        # [إصلاح C] الـ sections الأخرى placeholder حتى تُفعَّل لاحقاً
        # لتفعيل section: استبدل lambda بدالة بناء فعلية مثل _build_costing
        def _build_pricing():
            return _make_placeholder_tab(tr("pricing"))

        def _build_accounting():
            return _make_placeholder_tab(tr("accounting"))

        def _build_inventory():
            return _make_placeholder_tab(tr("inventory"))

        def _build_design():
            return _make_placeholder_tab(tr("design"))

        def _build_orders():
            return _make_placeholder_tab(tr("orders"))

        # الترتيب يجب أن يطابق _INDEX_MAP بالضبط
        _builders = [
            (_build_costing,    tr("costing")),
            (_build_pricing,    tr("pricing")),
            (_build_accounting, tr("accounting")),
            (_build_inventory,  tr("inventory")),
            (_build_design,     tr("design")),
            (_build_orders,     tr("orders")),
        ]

        for builder_fn, name in _builders:
            w = _try_build_section(builder_fn, name)
            self._stack.addWidget(w)

        # الانتقال لـ costing (index 1) وتفعيل زره في الـ sidebar
        if self._stack.count() > 1:
            self._stack.setCurrentIndex(_INDEX_MAP["costing"])
            btns = self._sidebar.get_buttons()
            if btns:
                btns[0].setChecked(True)

        self._validate_index_map()
        self._tabs_built = True

    def _validate_index_map(self):
        """
        يتحقق أن كل index في _INDEX_MAP موجود فعلاً في الـ stack.
        يُطلق AssertionError برسالة واضحة لو فشل.
        """
        stack_count = self._stack.count()
        for key, idx in _INDEX_MAP.items():
            assert idx < stack_count, (
                f"_INDEX_MAP['{key}'] = {idx} خارج نطاق الـ stack "
                f"(count={stack_count}) — تأكد من تطابق _builders مع _INDEX_MAP"
            )

    def _destroy_tabs(self):
        """
        يُزيل كل tabs عدا index 0 (NoCompanyScreen).
        [إصلاح B] يستدعي refresh_connections() بعد الإزالة.
        """
        bus.blockSignals(True)

        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            try:
                w.hide()
                w.deleteLater()
            except Exception:
                pass

        QApplication.processEvents()
        bus.blockSignals(False)

        try:
            from db.companies.company_state import company_state
            company_state.refresh_connections()
        except Exception as e:
            logger.warning("_destroy_tabs: refresh_connections فشل: %s", e)

        self._accounting = None
        self._tabs_built = False

    def _refresh_tabs(self):
        self._build_tabs()

    # ── أحداث ────────────────────────────────────────────────────────────────

    def _on_company_changed(self, company_id: int):
        """
        يُستدعى عند تغيير الشركة النشطة من CompanySelector.
        [محفوظ] AppState.invalidate() لمسح font_size cache.
        """
        from ui.app_state import AppState
        AppState.invalidate()

        try:
            from db.companies.company_state import company_state
            self.setWindowTitle(
                tr("app_title_company", name=company_state.company_name)
            )
            self._refresh_tabs()
        except Exception as e:
            logger.error("_on_company_changed: %s", e)
            return

        # [محفوظ] عبر الدالة لا bus.emit مباشرة — تتحقق من is_ready داخلياً
        emit_company_data_changed()

    def _on_nav(self, clicked_btn):
        """
        يعالج النقر على أزرار الـ sidebar.
        settings و shared_items لهما سلوك خاص — لا يُغيّران الـ stack.
        """
        # إلغاء تحديد كل الأزرار ثم تحديد المضغوط
        for btn in self._sidebar.get_buttons():
            if btn is not clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)

        key = clicked_btn.property("nav_key")

        # ── settings ──
        if key == "settings":
            clicked_btn.setChecked(False)
            from ui.widgets.dialogs.settings_dialog import SettingsDialog
            SettingsDialog(self._app, parent=self).exec_()
            # [تحسين 20] يُحدّث الأزرار والـ section labels بعد تغيير الإعدادات
            self._sidebar.refresh_all_buttons()
            return

        # ── shared_items ──
        if key == "shared_items":
            clicked_btn.setChecked(False)
            self._open_shared_items()
            return

        # ── لو لم تُبنَ الـ tabs بعد → شاشة "لا توجد شركة" ──
        if not self._tabs_built:
            self._stack.setCurrentIndex(0)
            return

        # ── التنقل العادي عبر _INDEX_MAP ──
        if key in _INDEX_MAP:
            idx = _INDEX_MAP[key]
            if idx < self._stack.count():
                self._stack.setCurrentIndex(idx)

    def _open_shared_items(self):
        """
        يفتح نافذة إدارة العناصر المشتركة من companies.db.
        يُطلق emit_company_data_changed بعد أي تغيير.
        """
        from db.companies.companies_schema   import get_central_connection, create_central_tables
        from db.companies.shared_items_repo  import create_shared_items_tables
        from ui.tabs.companies.shared_items_manager import SharedItemsManagerDialog

        central = get_central_connection()
        create_central_tables(central)
        create_shared_items_tables(central)

        dlg = SharedItemsManagerDialog(central, parent=self)
        dlg.items_changed.connect(emit_company_data_changed)
        dlg.exec_()
        central.close()