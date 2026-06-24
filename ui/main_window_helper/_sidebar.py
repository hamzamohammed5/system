"""
ui/main_window_helper/_sidebar.py
===================================================
[تحسين 20] refresh_all_buttons تحدّث الآن _SectionLabel أيضاً عند تغيير حجم الخط.
القديم: refresh_all_buttons تحدّث الأزرار فقط وتتجاهل الـ section labels.
الجديد: تستدعي lbl._apply_style() على كل label بعد تحديث الأزرار.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.theme import _C
from ui.widgets.core.i18n import tr

from ._section_label import _SectionLabel
from ._nav_button import _NavButton, SIDEBAR_COLLAPSED_WIDTH, SIDEBAR_EXPANDED_WIDTH
from ._toggle_button import _ToggleButton
from ui.constants import (
    NAV_BTN_H, NAV_BTN_W_OFFSET,
    SIDEBAR_COMPANY_H, SIDEBAR_TOGGLE_H, SIDEBAR_DIVIDER_H,
    SIDEBAR_SCROLL_W, SIDEBAR_SCROLL_MIN_H,
    SPACING_XS,
)


# ══════════════════════════════════════════════════════════
# _Sidebar
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
        from ..tabs.companies.company_selector import CompanySelector
        self._company_selector = CompanySelector()
        self._company_selector.setFixedHeight(SIDEBAR_COMPANY_H)
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
                background:transparent;width:{SIDEBAR_SCROLL_W}px;border-radius:1px;
            }}
            QScrollBar::handle:vertical {{
                background:{_C['sidebar_border']};border-radius:1px;min-height:{SIDEBAR_SCROLL_MIN_H}px;
            }}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0px; }}
        """)
        nav_widget = QWidget()
        nav_widget.setStyleSheet("background:transparent;")
        nav_lay = QVBoxLayout(nav_widget)
        nav_lay.setContentsMargins(8, 8, 8, 8)
        nav_lay.setSpacing(1)

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
        div.setFixedHeight(SIDEBAR_DIVIDER_H)
        div.setStyleSheet(f"background:{_C['sidebar_border']};border:none;margin:2px 4px;")
        f_lay.addWidget(div)

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