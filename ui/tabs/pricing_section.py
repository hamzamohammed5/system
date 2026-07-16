"""
ui/tabs/pricing_section.py
==========================
قسم "التسعير" — تبويبات داخلية:
  💰 الأسعار الأساسية
  🎁 العروض

[تحديث] توحيد القسم مع باقي الأقسام:
  - النصوص عبر tr() بدلاً من نصوص مباشرة (ar.py / en.py).
  - الألوان عبر _C من ui.theme (المصدر: ui.theme_manager).
  - الخط عبر font.py (FS_*).
  - تحديث الثيم الديناميكي عبر bus.theme_changed.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from ui.widgets.theme.layout_styles import tab_style, apply_tab_widths, normalize_tab_widget
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.font                        import FS_MD
from ui.constants                    import SECTION_HEADER_HEIGHT, SECTION_HEADER_BORDER_W, SPACING_XL
from ui.widgets.core.widget_mixin   import WidgetMixin

from .pricing.pricing_tab import PricingTab
from .pricing.offers.offers_tab  import OffersTab


class PricingSection(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=True, data=False)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ──
        self._header = QLabel(f"  {tr('nav_icon_pricing')}  {tr('nav_pricing')}")
        self._header.setFixedHeight(SECTION_HEADER_HEIGHT)
        self._refresh_style()
        layout.addWidget(self._header)

        # ── التبويبات ──
        self._tabs = QTabWidget()
        normalize_tab_widget(self._tabs)
        self._tabs.setStyleSheet(tab_style())

        self._tabs.addTab(PricingTab(), tr("pricing_tab"))
        self._tabs.addTab(OffersTab(),  tr("offers_tab"))
        apply_tab_widths(self._tabs)

        layout.addWidget(self._tabs)

    def _refresh_style(self, *_):
        self._header.setStyleSheet(f"""
            QLabel {{
                background: {_C['bg_surface']};
                border-bottom: {SECTION_HEADER_BORDER_W}px solid {_C['border']};
                font-size: {FS_MD}px;
                font-weight: bold;
                color: {_C['orange']};
                padding-right: {SPACING_XL}px;
            }}
        """)
        if hasattr(self, "_tabs"):
            self._tabs.setStyleSheet(tab_style())
            apply_tab_widths(self._tabs)

    def _refresh_lang(self, *_):
        if not hasattr(self, "_header"):
            return
        self._header.setText(f"  {tr('nav_icon_pricing')}  {tr('nav_pricing')}")
        if hasattr(self, "_tabs"):
            self._tabs.setTabText(0, tr("pricing_tab"))
            self._tabs.setTabText(1, tr("offers_tab"))
            apply_tab_widths(self._tabs)
