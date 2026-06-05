"""
ui/tabs/costing/labor_tab.py
====================================
LaborTab — التبويب الرئيسي للعمالة.

يرث من TabSectionBase للتوحيد مع RawTab و ProductTab.

[Fix A1] استبدال from ui.app_settings import _C بـ from ui.theme import _C
[Fix A6] إصلاح from ui.events import bus → from ui.widgets.core.events import bus
[Fix C4] استبدال tr() بنصوص عربية مباشرة بمفاتيح i18n صحيحة
"""

from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.base.tab_section  import TabSectionBase
from ui.widgets.managers.category import CategoryManager
from ui.widgets.core.i18n         import tr
from ui.theme                     import _C

from .labor.labor_settings import _LaborSettingsPanel
from .labor.labor_op_form  import LaborOpForm
from .labor.labor_op_table import LaborOpTable


def _splitter_style() -> str:
    """style موحد للـ QSplitter مربوط بـ _C."""
    return f"""
        QSplitter::handle {{
            background: {_C['border']};
            border-top: 1px solid {_C['border_med']};
        }}
        QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
        QSplitter::handle:pressed {{ background: {_C['accent']}; }}
    """


class _LaborOpsTab(QWidget):
    def __init__(self, conn, settings, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_splitter_style())

        self._form  = LaborOpForm(conn, settings)
        self._table = LaborOpTable(conn, settings, self._form)

        splitter.addWidget(self._form)
        splitter.addWidget(self._table)
        splitter.setSizes([280, 400])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


class LaborTab(TabSectionBase):
    """
    التبويب الرئيسي للعمالة — يرث من TabSectionBase للتوحيد البصري.
    """

    def _build_tabs(self, tabs: QTabWidget):
        self._settings = _LaborSettingsPanel(self.conn)

        tabs.addTab(self._settings,
                    f"⚙️  {tr('labor_settings')}")
        tabs.addTab(_LaborOpsTab(self.conn, self._settings),
                    f"📋  {tr('labor_operations')}")
        tabs.addTab(CategoryManager(self.conn, scope="labor"),
                    f"🏷️  {tr('categories_tab')}")