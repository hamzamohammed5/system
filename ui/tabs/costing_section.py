"""
ui/tabs/costing_section.py
==========================
قسم "حساب التكلفة" — تبويبات داخلية:
  📦 الخامات | 🔧 نصف مصنع | 🏭 منتج نهائي | 👷 العمالة | ⚙️ التشغيل

[Refactor] استخدام _C و tr() بدل الألوان والنصوص المدمجة.
استخدام tab_style من ui.widgets.theme.styles (الموثق في files_reference).
ربط bus.theme_changed لتحديث الـ stylesheet عند تغيير الثيم.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore    import Qt

from ui.widgets.theme.styles import tab_style
from ui.app_settings         import _C
from ui.widgets.core.i18n    import tr
from ui.events               import bus

from .costing.raw_tab     import RawTab
from .costing.product_tab import ProductTab
from .costing.labor_tab   import LaborTab
from .costing.machine_tab import MachineTab


class CostingSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        bus.theme_changed.connect(self._apply_theme)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ──
        self._header = QLabel(f"  📊  {tr('costing_section')}")
        self._header.setFixedHeight(42)
        self._apply_theme()
        layout.addWidget(self._header)

        # ── التبويبات ──
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setStyleSheet(tab_style())
        self._tabs.setUsesScrollButtons(True)
        self._tabs.setElideMode(Qt.ElideNone)

        tab_bar = self._tabs.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setDrawBase(True)

        self._tabs.addTab(RawTab(),            f"📦  {tr('raw_materials')}")
        self._tabs.addTab(ProductTab("semi"),  f"🔧  {tr('semi_product')}")
        self._tabs.addTab(ProductTab("final"), f"🏭  {tr('final_product')}")
        self._tabs.addTab(LaborTab(),          f"👷  {tr('labor')}")
        self._tabs.addTab(MachineTab(),        f"⚙️  {tr('machine')}")

        layout.addWidget(self._tabs)

    def _apply_theme(self, _=None):
        self._header.setStyleSheet(f"""
            QLabel {{
                background: {_C['bg_surface']};
                border-bottom: 1px solid {_C['border']};
                font-size: 14px;
                font-weight: bold;
                color: {_C['accent']};
                padding-right: 16px;
            }}
        """)
        if hasattr(self, "_tabs"):
            self._tabs.setStyleSheet(tab_style())