"""
ui/main_window_helper/_sidebar.py
===================================================
[تحسين 20] refresh_all_buttons تحدّث الآن _SectionLabel أيضاً عند تغيير حجم الخط.
القديم: refresh_all_buttons تحدّث الأزرار فقط وتتجاهل الـ section labels.
الجديد: تستدعي lbl._apply_style() على كل label بعد تحديث الأزرار.
[Refactor V4] تحويل _Sidebar إلى WidgetMixin لتحديث stylesheet تلقائياً عند تغيير الثيم.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin

from ._section_label import _SectionLabel
from ._nav_button import _NavButton
from ._toggle_button import _ToggleButton
from ui.constants import (
    NAV_BTN_H, NAV_BTN_W_OFFSET,
    SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_COMPANY_H, SIDEBAR_DIVIDER_H,
    SIDEBAR_SCROLL_W, SIDEBAR_SCROLL_MIN_H,
    SPACING_XS,
    SIDEBAR_NAV_MARGIN, SIDEBAR_NAV_SPACING,
    SIDEBAR_FOOTER_MARGIN_H, SIDEBAR_FOOTER_MARGIN_V, SIDEBAR_FOOTER_SPACING,
    SIDEBAR_DIV_MARGIN_V, SIDEBAR_DIV_MARGIN_H,
    SIDEBAR_ANIM_DURATION,
    SIDEBAR_SCROLL_RADIUS, SIDEBAR_BORDER_W,
)


# ══════════════════════════════════════════════════════════
# _Sidebar
# ══════════════════════════════════════════════════════════

class _Sidebar(QFrame, WidgetMixin):
    def __init__(self, on_company_changed, parent=None):
        super().__init__(parent)
        self._on_company_changed = on_company_changed
        self._collapsed = False
        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._buttons: list        = []
        self._section_labels: list = []
        self._build()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C['sidebar_bg']};
                border-left:{SIDEBAR_BORDER_W}px solid {_C['sidebar_border']};
            }}
        """)
        if hasattr(self, '_company_selector'):
            self._company_selector.setStyleSheet(
                f"background:{_C['sidebar_bg']};"
                f"border-bottom:{SIDEBAR_BORDER_W}px solid {_C['sidebar_border']};"
            )
        if hasattr(self, '_nav_scroll'):
            self._nav_scroll.setStyleSheet(f"""
                QScrollArea {{ border:none;background:transparent; }}
                QScrollBar:vertical {{
                    background:transparent;width:{SIDEBAR_SCROLL_W}px;border-radius:{SIDEBAR_SCROLL_RADIUS}px;
                }}
                QScrollBar::handle:vertical {{
                    background:{_C['sidebar_border']};border-radius:{SIDEBAR_SCROLL_RADIUS}px;min-height:{SIDEBAR_SCROLL_MIN_H}px;
                }}
                QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0px; }}
            """)
        if hasattr(self, '_div'):
            self._div.setStyleSheet(
                f"background:{_C['sidebar_border']};border:none;"
                f"margin:{SIDEBAR_DIV_MARGIN_V}px {SIDEBAR_DIV_MARGIN_H}px;"
            )

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header: CompanySelector ──
        from ..tabs.companies.company_selector import CompanySelector
        self._company_selector = CompanySelector()
        self._company_selector.setFixedHeight(SIDEBAR_COMPANY_H)
        self._company_selector.company_changed.connect(self._on_company_changed)
        layout.addWidget(self._company_selector)

        # ── Nav Scroll ──
        self._nav_scroll = QScrollArea()
        self._nav_scroll.setWidgetResizable(True)
        self._nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        nav_widget = QWidget()
        nav_widget.setStyleSheet("background:transparent;")
        nav_lay = QVBoxLayout(nav_widget)
        nav_lay.setContentsMargins(SIDEBAR_NAV_MARGIN, SIDEBAR_NAV_MARGIN, SIDEBAR_NAV_MARGIN, SIDEBAR_NAV_MARGIN)
        nav_lay.setSpacing(SIDEBAR_NAV_SPACING)

        nav_sections = [
            (tr("nav_section_production"), [
                (tr("nav_icon_costing"),    tr("nav_costing"),    "costing",    ""),
                (tr("nav_icon_pricing"),    tr("nav_pricing"),    "pricing",    ""),
            ]),
            (tr("nav_section_finance"), [
                (tr("nav_icon_accounting"), tr("nav_accounting"), "accounting", ""),
                (tr("nav_icon_inventory"),  tr("nav_inventory"),  "inventory",  ""),
            ]),
            (tr("nav_section_work"), [
                (tr("nav_icon_design"),     tr("nav_design"),     "design",     ""),
                (tr("nav_icon_orders"),     tr("nav_orders"),     "orders",     ""),
            ]),
        ]

        for section_name, items in nav_sections:
            lbl = _SectionLabel(section_name)
            self._section_labels.append(lbl)
            nav_lay.addWidget(lbl)
            for icon, label, key, badge in items:
                btn = _NavButton(icon, label, badge)
                btn.setProperty("nav_key", key)
                btn.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - NAV_BTN_W_OFFSET)
                btn.setFixedHeight(NAV_BTN_H)
                self._buttons.append(btn)
                nav_lay.addWidget(btn)
        nav_lay.addSpacing(SPACING_XS)

        nav_lay.addStretch()
        self._nav_scroll.setWidget(nav_widget)
        layout.addWidget(self._nav_scroll, stretch=1)

        # ── Footer ──
        footer = QWidget()
        footer.setStyleSheet("QWidget{background:transparent;}")
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(SIDEBAR_FOOTER_MARGIN_H, SIDEBAR_FOOTER_MARGIN_V, SIDEBAR_FOOTER_MARGIN_H, SIDEBAR_FOOTER_MARGIN_V)
        f_lay.setSpacing(SIDEBAR_FOOTER_SPACING)

        self._div = QFrame()
        self._div.setFrameShape(QFrame.HLine)
        self._div.setFixedHeight(SIDEBAR_DIVIDER_H)
        f_lay.addWidget(self._div)

        shared_btn = _NavButton(tr("nav_icon_shared"), tr("nav_shared"))
        shared_btn.setProperty("nav_key", "shared_items")
        shared_btn.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - NAV_BTN_W_OFFSET)
        shared_btn.setFixedHeight(NAV_BTN_H)
        self._buttons.append(shared_btn)
        f_lay.addWidget(shared_btn)

        btn_settings = _NavButton(tr("nav_icon_settings"), tr("nav_settings"))
        btn_settings.setProperty("nav_key", "settings")
        btn_settings.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - NAV_BTN_W_OFFSET)
        btn_settings.setFixedHeight(NAV_BTN_H)
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
        self._anim_min.setDuration(SIDEBAR_ANIM_DURATION)
        self._anim_min.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim_min.setStartValue(self.width())
        self._anim_min.setEndValue(target)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(SIDEBAR_ANIM_DURATION)
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
        """
        يحدّث أحجام كل الأزرار والـ section labels.

        [تحسين 20] يستدعي _apply_style() على كل _SectionLabel بعد تحديث الأزرار،
        بدلاً من تجاهلها (وهو ما كان يحدث من قبل). هذا يضمن أن الـ section labels
        تتحدث عند تغيير حجم الخط من الإعدادات، مثلها مثل الأزرار تماماً.
        """
        for btn in self._buttons:
            btn.refresh_sizes()
            if self._collapsed:
                btn.set_collapsed(True)

        # [تحسين 20] تحديث section labels بعد الأزرار
        for lbl in self._section_labels:
            lbl._apply_style()

    def get_buttons(self):
        return self._buttons

    def get_company_selector(self):
        return self._company_selector
