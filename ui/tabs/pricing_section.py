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

from ui.widgets.theme.layout_styles import tab_style
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.widgets.core.events         import bus
from ui.font                        import FS_MD

from .pricing.pricing_tab import PricingTab
from .pricing.offers import OffersTab


class PricingSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        bus.theme_changed.connect(self._apply_theme)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ──
        self._header = QLabel(f"  💰  {tr('nav_pricing')}")
        self._header.setFixedHeight(42)
        self._apply_theme()
        layout.addWidget(self._header)

        # ── التبويبات ──
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setStyleSheet(tab_style())

        self._tabs.addTab(PricingTab(), tr("pricing_tab"))
        self._tabs.addTab(OffersTab(),  tr("offers_tab"))

        layout.addWidget(self._tabs)

    def _apply_theme(self, _=None):
        self._header.setStyleSheet(f"""
            QLabel {{
                background: {_C['bg_surface']};
                border-bottom: 1px solid {_C['border']};
                font-size: {FS_MD}px;
                font-weight: bold;
                color: {_C['orange']};
                padding-right: 16px;
            }}
        """)
        if hasattr(self, "_tabs"):
            self._tabs.setStyleSheet(tab_style())