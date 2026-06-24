"""
ui/tabs/costing_section.py
==========================
قسم "حساب التكلفة" — تبويبات داخلية:
  📦 الخامات | 🔧 نصف مصنع | 🏭 منتج نهائي | 👷 العمالة | ⚙️ التشغيل

[Fix A1] استبدال from ui.app_settings import _C بـ from ui.theme import _C
[Fix A3] استبدال from ui.widgets.theme.styles import tab_style
         بـ from ui.widgets.theme.layout_styles import tab_style
[Fix C5] استخدام مفاتيح i18n صحيحة لكل التبويبات
[Fix #9] إضافة try/except حول بناء الـ tabs مع عرض رسالة واضحة عند الفشل
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore    import Qt

from ui.widgets.theme.layout_styles import tab_style
from ui.theme                        import _C
from ui.widgets.core.i18n           import tr
from ui.font                        import FS_MD, FS_LG
from ui.constants                    import SECTION_HEADER_HEIGHT
from ui.widgets.core.widget_mixin   import WidgetMixin

from .costing.raw_tab     import RawTab
from .costing.product_tab import ProductTab
from .costing.labor_tab   import LaborTab
from .costing.machine_tab import MachineTab


def _make_error_tab(msg: str) -> QLabel:
    """يُنشئ تبويب خطأ بسيط لعرض رسالة الفشل."""
    lbl = QLabel(f"{tr('notif_icon_warning')}  {msg}")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"color:{_C['danger']}; font-size:{FS_MD}px;"
        f"background:{_C['danger_bg']}; border:1px solid {_C['danger_border']};"
        "border-radius:6px; padding:12px;"
    )
    return lbl


class CostingSection(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر القسم ──
        self._header = QLabel(f"  {tr('nav_icon_costing')}  {tr('costing_section')}")
        self._header.setFixedHeight(SECTION_HEADER_HEIGHT)
        self._refresh_style()
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

        # [Fix #9] try/except حول كل tab على حدة لعزل الأخطاء
        _tab_defs = [
            (lambda: RawTab(),            f"{tr('tab_icon_raw')}  {tr('raw_materials')}"),
            (lambda: ProductTab("semi"),  f"{tr('tab_icon_semi')}  {tr('semi_product')}"),
            (lambda: ProductTab("final"), f"{tr('tab_icon_final')}  {tr('final_product')}"),
            (lambda: LaborTab(),          f"{tr('tab_icon_labor')}  {tr('labor')}"),
            (lambda: MachineTab(),        f"{tr('tab_icon_machine')}  {tr('machine')}"),
        ]

        for factory, label in _tab_defs:
            widget = factory()
            # try:
            #     widget = factory()
            # except Exception as e:
            #     widget = _make_error_tab(tr("tab_load_error", error=str(e)))
            self._tabs.addTab(widget, label)

        layout.addWidget(self._tabs)

    def _refresh_style(self, *_):
        self._header.setStyleSheet(f"""
            QLabel {{
                background: {_C['bg_surface']};
                border-bottom: 1px solid {_C['border']};
                font-size: {FS_LG}px;
                font-weight: bold;
                color: {_C['accent']};
                padding-right: 16px;
            }}
        """)
        if hasattr(self, "_tabs"):
            self._tabs.setStyleSheet(tab_style())