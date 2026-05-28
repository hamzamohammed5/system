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

from ui.app_settings  import _C

from ._section_label import _SectionLabel
from ._nav_button import _NavButton, SIDEBAR_COLLAPSED_WIDTH, SIDEBAR_EXPANDED_WIDTH
from ._toggle_button import _ToggleButton


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