"""
ui/main_window.py  (نسخة multi-company — مُصلَحة v7)
=====================================================
التغييرات عن v6:
  - scrollbar الـ content_scroll يستخدم _C بدل hardcoded hex
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QFrame,
    QScrollArea, QSizePolicy, QApplication,
)
from PyQt5.QtCore import Qt

from ui.app_settings  import _C
from ui.events        import bus
from .main_window_helper._sidebar import _Sidebar

from .main_window_helper._nav_button import (
    WINDOW_DEFAULT_W,
    SIDEBAR_COLLAPSED_WIDTH, CONTENT_MIN_WIDTH,
)


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
        # يستخدم _C بدل hardcoded hex
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
        if self._tabs_built:
            self._destroy_tabs()

        from ui.tabs.costing_section    import CostingSection
        from ui.tabs.pricing_section    import PricingSection
        from ui.tabs.accounting_section import AccountingTab
        from ui.tabs.inventory_section  import InventoryTab
        from ui.tabs.design_section     import DesignSection
        from ui.tabs.orders_section     import OrdersSection

        self._costing    = CostingSection()
        self._pricing    = PricingSection()
        self._accounting = AccountingTab()
        self._inventory  = InventoryTab()
        self._design     = DesignSection()
        self._orders     = OrdersSection()

        for w in [self._costing, self._pricing, self._accounting,
                  self._inventory, self._design, self._orders]:
            self._stack.addWidget(w)

        self._stack.setCurrentIndex(1)
        self._sidebar.get_buttons()[0].setChecked(True)
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
            print(f"[MainWindow] refresh_connections warning: {e}")

        self._accounting = None
        self._tabs_built = False

    def _refresh_tabs(self):
        self._build_tabs()

    # ──────────────────────────────────────────────────────
    # أحداث
    # ──────────────────────────────────────────────────────

    def _on_company_changed(self, company_id: int):
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
            self._stack.setCurrentIndex(index_map[key])

    def _open_shared_items(self):
        from db.companies.companies_schema import get_central_connection, create_central_tables
        from db.companies.shared_items_repo import create_shared_items_tables
        from ui.tabs.companies.shared_items_manager import SharedItemsManagerDialog

        central = get_central_connection()
        create_central_tables(central)
        create_shared_items_tables(central)

        dlg = SharedItemsManagerDialog(central, parent=self)
        dlg.items_changed.connect(lambda: bus.data_changed.emit())
        dlg.exec_()
        central.close()