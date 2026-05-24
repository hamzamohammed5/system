"""
ui/tabs/costing/costing_section.py
==========================
قسم "حساب التكلفة" — تبويبات داخلية:
  📦 الخامات | 🔧 نصف مصنع | 🏭 منتج نهائي | 👷 العمالة | ⚙️ التشغيل

التحسينات:
  - يستخدم _tab_stylesheet() من tab_section_base بدل تعريف _TAB_STYLE محلياً
  - يستخدم QLabel موحد للهيدر بدل ستايل مكرر
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore import Qt

from ui.widgets.shared.tab_section_base import _tab_stylesheet

from .costing.raw_tab     import RawTab
from .costing.product_tab import ProductTab
from .costing.labor_tab   import LaborTab
from .costing.machine_tab import MachineTab

from ui.app_settings import _C


class CostingSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ──
        header = QLabel("  📊  حساب التكلفة")
        header.setFixedHeight(42)
        header.setStyleSheet(f"""
            QLabel {{
                background: {_C['bg_surface']};
                border-bottom: 1px solid {_C['border']};
                font-size: 14px;
                font-weight: bold;
                color: {_C['accent']};
                padding-right: 16px;
            }}
        """)
        layout.addWidget(header)

        # ── التبويبات ──
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)

        # استخدام _tab_stylesheet() من tab_section_base بدل تعريف ستايل جديد
        self._tabs.setStyleSheet(_tab_stylesheet())

        # السماح للتبويبات بالتمرير عند الضيق
        self._tabs.setUsesScrollButtons(True)
        self._tabs.setElideMode(Qt.ElideNone)
        tab_bar = self._tabs.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setDrawBase(True)

        self._tabs.addTab(RawTab(),            "📦  الخامات")
        self._tabs.addTab(ProductTab("semi"),  "🔧  نصف مصنع")
        self._tabs.addTab(ProductTab("final"), "🏭  منتج نهائي")
        self._tabs.addTab(LaborTab(),          "👷  العمالة")
        self._tabs.addTab(MachineTab(),        "⚙️  التشغيل")

        layout.addWidget(self._tabs)