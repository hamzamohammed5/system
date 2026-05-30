"""
ui/main_window.py  (نسخة multi-company — مُصلَحة v11)
=====================================================
التغييرات عن v10:
  - [إصلاح A] _build_tabs: استخدام sections حقيقية بدل placeholders.
    كل section يرث من TabSectionBase ويُبنى من conn الخاص بالشركة النشطة.
    لو section لم يُنشأ بعد (import يفشل) يُعرض placeholder مؤقت مع
    رسالة خطأ واضحة بدل صمت.

  - [إصلاح B] _destroy_tabs: يستدعي company_state.refresh_connections()
    بعد إزالة tabs لضمان تحديث الـ connections.

  - [محفوظ] _on_company_changed يستدعي AppState.invalidate() لمسح font_size cache.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QFrame, QLabel,
    QScrollArea, QSizePolicy, QApplication,
)
from PyQt5.QtCore import Qt
import logging

from ui.app_settings  import _C, fs, get_font_size
from ui.events        import bus
from ui.widgets.core.events import emit_company_data_changed
from .main_window_helper._sidebar import _Sidebar

from .main_window_helper._nav_button import (
    WINDOW_DEFAULT_W,
    SIDEBAR_COLLAPSED_WIDTH, CONTENT_MIN_WIDTH,
)

logger = logging.getLogger(__name__)


def _make_placeholder_tab(section_name: str, error: str = "") -> QWidget:
    """
    Placeholder مؤقت لـ section لم يُبنَ بعد أو فشل import.
    يعرض رسالة واضحة للمطور.
    """
    w = QWidget()
    w.setStyleSheet(f"background:{_C['bg_page']};")
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

    lbl_title = QLabel(f"قسم {section_name}")
    lbl_title.setAlignment(Qt.AlignCenter)
    lbl_title.setStyleSheet(
        f"font-size:{fs(base, +2)}pt; font-weight:bold;"
        f"color:{_C['text_primary']}; background:transparent; border:none;"
    )
    lay.addWidget(lbl_title)

    msg = error if error else "قيد التطوير"
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
    try:
        return builder_fn()
    except ImportError as e:
        logger.warning("_try_build_section: import فشل لـ %s: %s", section_name, e)
        return _make_placeholder_tab(section_name, f"ImportError: {e}")
    except Exception as e:
        logger.error("_try_build_section: فشل بناء %s: %s", section_name, e)
        return _make_placeholder_tab(section_name, f"خطأ: {e}")


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app          = app
        self._tabs_built   = False
        self._accounting   = None

        self.setWindowTitle("ERP — نظام إدارة التكاليف")
        self.resize(WINDOW_DEFAULT_W, 820)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(SIDEBAR_COLLAPSED_WIDTH + 400, 500)

        self._build()

    # ──────────────────────────────────────────────────────
    # بناء الهيكل الأساسي
    # ──────────────────────────────────────────────────────

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._sidebar = _Sidebar(on_company_changed=self._on_company_changed)
        self._sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self._sidebar)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{_C['border']};border:none;")
        sep.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(sep)

        self._content_scroll = QScrollArea()
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content_scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:transparent; }}
            QScrollBar:horizontal {{
                background:transparent; height:6px; border-radius:3px;
            }}
            QScrollBar::handle:horizontal {{
                background:{_C['border_med']}; border-radius:3px; min-width:30px;
            }}
            QScrollBar::handle:horizontal:hover {{ background:{_C['border_strong']}; }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{ width:0px; }}
        """)
        self._content_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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

        for btn in self._sidebar.get_buttons():
            btn.clicked.connect(lambda checked, b=btn: self._on_nav(b))

        from db.companies.company_state import company_state
        if company_state.is_ready:
            self._build_tabs()

    # ──────────────────────────────────────────────────────
    # بناء وتدمير التبويبات
    # ──────────────────────────────────────────────────────

    def _build_tabs(self):
        """
        يبني tabs الـ sections الحقيقية.

        كل section يُبنى باستخدام _try_build_section() لعزل أي import errors.
        الترتيب والـ index يجب أن يتطابقا مع index_map في _on_nav().

        index 1 → costing
        index 2 → pricing
        index 3 → accounting
        index 4 → inventory
        index 5 → design
        index 6 → orders
        """
        if self._tabs_built:
            self._destroy_tabs()

        # جلب الـ connection من company_state لتمريره للـ sections
        try:
            from db.companies.company_state import company_state
            conn = company_state.get_erp_conn()
        except Exception as e:
            logger.error("_build_tabs: تعذر الحصول على conn: %s", e)
            conn = None

        # ── بناء كل section بشكل آمن ──────────────────────

        # index 1: Costing
        def _build_costing():
            from ui.tabs.costing_section import CostingSection
            return CostingSection(conn_fn=lambda: conn)

        # index 2: Pricing
        def _build_pricing():
            from ui.tabs.pricing_section import PricingSection
            return PricingSection(conn_fn=lambda: conn)

        # index 3: Accounting
        def _build_accounting():
            from ui.tabs.accounting_section import AccountingTab
            return AccountingTab(conn_fn=lambda: conn)

        # index 4: Inventory
        def _build_inventory():
            from ui.tabs.inventory_section import InventoryTab
            return InventoryTab(conn_fn=lambda: conn)

        # index 5: Design
        def _build_design():
            from ui.tabs.design_section import DesignSection
            return DesignSection(conn_fn=lambda: conn)

        # index 6: Orders
        def _build_orders():
            from ui.tabs.orders_section import OrdersSection
            return OrdersSection(conn_fn=lambda: conn)

        _builders = [
            (_build_costing,    "حساب التكلفة"),
            (_build_pricing,    "التسعير"),
            (_build_accounting, "الحسابات"),
            (_build_inventory,  "المخزن"),
            (_build_design,     "التصميمات"),
            (_build_orders,     "الطلبات"),
        ]

        for builder_fn, name in _builders:
            w = _try_build_section(builder_fn, name)
            self._stack.addWidget(w)

        # الانتقال لأول tab حقيقية (index 1)
        if self._stack.count() > 1:
            self._stack.setCurrentIndex(1)
            btns = self._sidebar.get_buttons()
            if btns:
                btns[0].setChecked(True)

        self._tabs_built = True

    def _destroy_tabs(self):
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
            logger.warning("_destroy_tabs: refresh_connections: %s", e)

        self._accounting = None
        self._tabs_built = False

    def _refresh_tabs(self):
        self._build_tabs()

    # ──────────────────────────────────────────────────────
    # أحداث
    # ──────────────────────────────────────────────────────

    def _on_company_changed(self, company_id: int):
        # مسح font_size cache — كل شركة ممكن يكون ليها إعداد مختلف
        from ui.app_state import AppState
        AppState.invalidate()

        from db.companies.company_state import company_state
        self.setWindowTitle(f"ERP — {company_state.company_name}")
        self._refresh_tabs()
        bus.company_data_changed.emit(company_id)

    def _on_nav(self, clicked_btn):
        for btn in self._sidebar.get_buttons():
            if btn is not clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)

        key = clicked_btn.property("nav_key")

        if key == "settings":
            clicked_btn.setChecked(False)
            from ui.settings_dialog import SettingsDialog
            SettingsDialog(self._app, parent=self).exec_()
            self._sidebar.refresh_all_buttons()
            return

        if key == "shared_items":
            clicked_btn.setChecked(False)
            self._open_shared_items()
            return

        if not self._tabs_built:
            self._stack.setCurrentIndex(0)
            return

        index_map = {
            "costing":    1,
            "pricing":    2,
            "accounting": 3,
            "inventory":  4,
            "design":     5,
            "orders":     6,
        }
        if key in index_map:
            idx = index_map[key]
            if idx < self._stack.count():
                self._stack.setCurrentIndex(idx)

    def _open_shared_items(self):
        from db.companies.companies_schema import get_central_connection, create_central_tables
        from db.companies.shared_items_repo import create_shared_items_tables
        from ui.tabs.companies.shared_items_manager import SharedItemsManagerDialog

        central = get_central_connection()
        create_central_tables(central)
        create_shared_items_tables(central)

        dlg = SharedItemsManagerDialog(central, parent=self)
        dlg.items_changed.connect(emit_company_data_changed)
        dlg.exec_()
        central.close()