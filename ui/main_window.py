"""
ui/main_window.py  (نسخة multi-company)
=========================================
النافذة الرئيسية مع دعم الشركات المتعددة.

التغييرات:
  - إضافة CompanySelector في header الـ sidebar
  - عند تغيير الشركة → إعادة تهيئة كل التبويبات
  - NoCompanyScreen قبل اختيار شركة
  - زر العناصر المشتركة في footer الـ sidebar
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.app_settings  import get_font_size, _C
from ui.events        import bus

SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56
CONTENT_MIN_WIDTH       = 820
WINDOW_DEFAULT_W        = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH


# ══════════════════════════════════════════════════════════
# _SectionLabel, _NavButton, _ToggleButton
# (نفس الكود القديم — محذوف هنا اختصاراً، انسخه من main_window القديم)
# ══════════════════════════════════════════════════════════

class _SectionLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLabel {{
                color: {_C['sidebar_muted']}; font-size: 8pt;
                font-weight: 700; letter-spacing: 1.5px;
                padding: 12px 16px 4px 16px;
                background: transparent; border: none;
            }}
        """)

    def set_collapsed(self, collapsed):
        self.setVisible(not collapsed)


class _NavButton(QPushButton):
    def __init__(self, icon, label, badge="", parent=None):
        super().__init__(parent)
        self._icon = icon; self._label = label
        self._badge = badge; self._collapsed = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._build_content(); self._update_style()

    def _build_content(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignVCenter)
        self._ico_lbl = QLabel(self._icon)
        self._ico_lbl.setFixedWidth(22)
        self._ico_lbl.setAlignment(Qt.AlignCenter)
        self._ico_lbl.setStyleSheet(
            f"background:transparent;border:none;font-size:15pt;color:{_C['sidebar_text']};"
        )
        self._txt_lbl = QLabel(self._label)
        self._txt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._txt_lbl.setWordWrap(False)
        self._txt_lbl.setStyleSheet(
            f"background:transparent;border:none;color:{_C['sidebar_text']};"
        )
        self._badge_lbl = QLabel(self._badge)
        self._badge_lbl.setVisible(bool(self._badge))
        self._badge_lbl.setAlignment(Qt.AlignCenter)
        self._badge_lbl.setStyleSheet(
            "QLabel{background:#C0392B;color:#FFF;font-size:8pt;font-weight:700;"
            "padding:1px 6px;border-radius:8px;border:none;}"
        )
        lay.addWidget(self._txt_lbl, stretch=1)
        lay.addWidget(self._badge_lbl)
        lay.addWidget(self._ico_lbl)

    def set_badge(self, text):
        self._badge = text
        self._badge_lbl.setText(text)
        self._badge_lbl.setVisible(bool(text) and not self._collapsed)

    def set_collapsed(self, collapsed):
        self._collapsed = collapsed
        self._txt_lbl.setVisible(not collapsed)
        self._badge_lbl.setVisible(bool(self._badge) and not collapsed)
        if collapsed:
            self.setFixedWidth(SIDEBAR_COLLAPSED_WIDTH)
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.layout().setAlignment(Qt.AlignCenter)
        else:
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
            self.layout().setContentsMargins(10, 0, 10, 0)
            self.layout().setAlignment(Qt.AlignVCenter)

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background:{_C['sidebar_active']};border:none;
                    border-right:2px solid {_C['accent']};
                    border-radius:6px;color:{_C['sidebar_text']};
                    font-weight:600;text-align:right;padding:0px;min-height:38px;
                }}
            """)
            self._ico_lbl.setStyleSheet(
                f"background:transparent;border:none;font-size:15pt;color:{_C['accent_mid']};"
            )
            self._txt_lbl.setStyleSheet(
                f"background:transparent;border:none;color:{_C['sidebar_text']};font-weight:600;"
            )
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:transparent;border:none;border-radius:6px;
                    color:{_C['sidebar_text']};text-align:right;
                    padding:0px;min-height:38px;
                }}
                QPushButton:hover {{ background:{_C['sidebar_hover']}; }}
            """)
            self._ico_lbl.setStyleSheet(
                f"background:transparent;border:none;font-size:15pt;color:{_C['sidebar_muted']};"
            )
            self._txt_lbl.setStyleSheet(
                f"background:transparent;border:none;color:{_C['sidebar_text']};font-weight:400;"
            )

    def setChecked(self, v):
        super().setChecked(v); self._update_style()

    def refresh_sizes(self):
        base = get_font_size()
        self._ico_lbl.setStyleSheet(
            f"background:transparent;border:none;font-size:{base+4}pt;"
        )
        self._txt_lbl.setStyleSheet(
            f"background:transparent;border:none;font-size:{base}pt;"
        )
        h = base * 2 + 14
        self.setFixedHeight(max(38, h))
        if not self._collapsed:
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)


class _ToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()
        self.setStyleSheet(f"""
            QPushButton {{
                background:transparent;border:none;
                border-top:1px solid {_C['sidebar_border']};
                color:{_C['sidebar_muted']};font-size:11pt;
            }}
            QPushButton:hover {{
                background:{_C['sidebar_hover']};color:{_C['sidebar_text']};
            }}
        """)

    def _refresh(self):
        self.setText("◀" if not self._collapsed else "▶")
        self.setToolTip("طي الشريط الجانبي" if not self._collapsed else "فرد الشريط الجانبي")

    def toggle_state(self):
        self._collapsed = not self._collapsed
        self._refresh()
        return self._collapsed


# ══════════════════════════════════════════════════════════
# _Sidebar — مع CompanySelector في الأعلى
# ══════════════════════════════════════════════════════════

class _Sidebar(QFrame):
    def __init__(self, on_company_changed, parent=None):
        super().__init__(parent)
        self._on_company_changed = on_company_changed
        self._collapsed = False
        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C['sidebar_bg']};
                border-left:1px solid {_C['sidebar_border']};
            }}
        """)
        self._buttons: list        = []
        self._section_labels: list = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header: CompanySelector ──
        from .tabs.companies.company_selector import CompanySelector
        self._company_selector = CompanySelector()
        self._company_selector.setFixedHeight(46)
        self._company_selector.setStyleSheet(
            f"background:{_C['sidebar_bg']};"
            f"border-bottom:1px solid {_C['sidebar_border']};"
        )
        self._company_selector.company_changed.connect(self._on_company_changed)
        layout.addWidget(self._company_selector)

        # ── Nav Scroll ──
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        nav_scroll.setStyleSheet(f"""
            QScrollArea {{ border:none;background:transparent; }}
            QScrollBar:vertical {{
                background:transparent;width:3px;border-radius:1px;
            }}
            QScrollBar::handle:vertical {{
                background:{_C['sidebar_border']};border-radius:1px;min-height:20px;
            }}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0px; }}
        """)
        nav_widget = QWidget()
        nav_widget.setStyleSheet("background:transparent;")
        nav_lay = QVBoxLayout(nav_widget)
        nav_lay.setContentsMargins(8, 8, 8, 8)
        nav_lay.setSpacing(1)

        nav_sections = [
            ("الإنتاج", [
                ("📊", "حساب التكلفة", "costing",    ""),
                ("💰", "التسعير",       "pricing",    ""),
            ]),
            ("المالية", [
                ("🏦", "الحسابات",     "accounting", ""),
                ("📦", "المخزن",        "inventory",  ""),
            ]),
            ("العمل", [
                ("🎨", "التصميمات",    "design",     ""),
                ("📋", "الطلبات",       "orders",     ""),
            ]),
        ]

        for section_name, items in nav_sections:
            lbl = _SectionLabel(section_name)
            self._section_labels.append(lbl)
            nav_lay.addWidget(lbl)
            for icon, label, key, badge in items:
                btn = _NavButton(icon, label, badge)
                btn.setProperty("nav_key", key)
                btn.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
                btn.setFixedHeight(38)
                self._buttons.append(btn)
                nav_lay.addWidget(btn)
            nav_lay.addSpacing(4)

        nav_lay.addStretch()
        nav_scroll.setWidget(nav_widget)
        layout.addWidget(nav_scroll, stretch=1)

        # ── Footer ──
        footer = QWidget()
        footer.setStyleSheet("QWidget{background:transparent;}")
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(8, 4, 8, 4)
        f_lay.setSpacing(1)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{_C['sidebar_border']};border:none;margin:2px 4px;")
        f_lay.addWidget(div)

        # زر العناصر المشتركة
        shared_btn = _NavButton("🔗", "العناصر المشتركة")
        shared_btn.setProperty("nav_key", "shared_items")
        shared_btn.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
        shared_btn.setFixedHeight(38)
        self._buttons.append(shared_btn)
        f_lay.addWidget(shared_btn)

        btn_settings = _NavButton("⚙️", "الإعدادات")
        btn_settings.setProperty("nav_key", "settings")
        btn_settings.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
        btn_settings.setFixedHeight(38)
        self._buttons.append(btn_settings)
        f_lay.addWidget(btn_settings)

        self._toggle_btn = _ToggleButton()
        self._toggle_btn.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self._toggle_btn.clicked.connect(self._on_toggle)
        f_lay.addWidget(self._toggle_btn)

        layout.addWidget(footer)

    def _on_toggle(self):
        self._collapsed = self._toggle_btn.toggle_state()
        target = SIDEBAR_COLLAPSED_WIDTH if self._collapsed else SIDEBAR_EXPANDED_WIDTH

        self._anim_min = QPropertyAnimation(self, b"minimumWidth")
        self._anim_min.setDuration(200)
        self._anim_min.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim_min.setStartValue(self.width())
        self._anim_min.setEndValue(target)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(200)
        self._anim_max.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim_max.setStartValue(self.width())
        self._anim_max.setEndValue(target)

        self._anim_min.start()
        self._anim_max.start()

        self._company_selector.setVisible(not self._collapsed)
        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)
        for lbl in self._section_labels:
            lbl.set_collapsed(self._collapsed)
        self._toggle_btn.setFixedWidth(target)

    def refresh_all_buttons(self):
        for btn in self._buttons:
            btn.refresh_sizes()
            if self._collapsed:
                btn.set_collapsed(True)

    def get_buttons(self):
        return self._buttons

    def get_company_selector(self):
        return self._company_selector


# ══════════════════════════════════════════════════════════
# MainWindow
# ══════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app          = app
        self._tabs_built   = False

        self.setWindowTitle("ERP — نظام إدارة التكاليف")
        self.resize(WINDOW_DEFAULT_W, 820)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(SIDEBAR_COLLAPSED_WIDTH + 400, 500)

        self._build()

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

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{_C['border']};border:none;")
        sep.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(sep)

        # ── Content Scroll ──
        self._content_scroll = QScrollArea()
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content_scroll.setStyleSheet("""
            QScrollArea { border:none;background:transparent; }
            QScrollBar:horizontal {
                background:transparent;height:6px;border-radius:3px;
            }
            QScrollBar::handle:horizontal {
                background:#C8C4B8;border-radius:3px;min-width:30px;
            }
            QScrollBar::handle:horizontal:hover { background:#6B6760; }
            QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal { width:0px; }
        """)
        self._content_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ── Stack ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{_C['bg_page']};")
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.setMinimumWidth(CONTENT_MIN_WIDTH)

        # شاشة "اختر شركة"
        from .tabs.companies.no_company_screen import NoCompanyScreen
        self._no_company_screen = NoCompanyScreen()
        self._no_company_screen.open_manager.connect(
            lambda: self._sidebar.get_company_selector()._open_manager()
        )
        self._stack.addWidget(self._no_company_screen)  # index 0

        self._content_scroll.setWidget(self._stack)
        main_layout.addWidget(self._content_scroll, stretch=1)

        # ربط أزرار الـ sidebar
        for btn in self._sidebar.get_buttons():
            btn.clicked.connect(lambda checked, b=btn: self._on_nav(b))

        # لو في شركة نشطة مسبقاً — ابنِ التبويبات
        from db.companies.company_state import company_state
        if company_state.is_ready:
            self._build_tabs()

    def _build_tabs(self):
        """بناء تبويبات الشركة النشطة."""
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

        # انتقل للتبويب الأول
        self._stack.setCurrentIndex(1)
        self._sidebar.get_buttons()[0].setChecked(True)
        self._tabs_built = True

    def _destroy_tabs(self):
        """حذف تبويبات الشركة القديمة."""
        # احتفظ بـ index 0 (no_company_screen)
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            try:
                w.close()
                w.deleteLater()
            except Exception:
                pass
        self._tabs_built = False

    def _on_company_changed(self, company_id: int):
        """عند تغيير الشركة — أعد بناء التبويبات."""
        from db.companies.company_state import company_state
        from db.companies.companies_repo import fetch_company
        from db.companies.companies_schema import get_central_connection

        # حدّث عنوان النافذة
        self.setWindowTitle(f"ERP — {company_state.company_name}")

        # أعد بناء التبويبات
        self._build_tabs()

        # أطلق bus.data_changed لتحديث أي widget مشترك
        bus.data_changed.emit()

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
            from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
            SharedItemsDialog(parent=self).exec_()
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