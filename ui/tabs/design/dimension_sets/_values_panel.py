"""
ui/tabs/design/dimension_sets/_values_panel.py
=====================================
لوحة إدخال قيم المقاسات — مع دعم تغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from .values_panel._sets_list_panel  import _SetsListPanel
from .values_panel._instances_table import _InstancesTable
from ui.widgets.core.events import bus
from ui.theme import _C


class _ValuesPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._build()
        bus.font_changed.connect(self._on_font_changed)

    def _on_font_changed(self, size: int):
        self._sets_list._on_font_changed(size)
        self._table._on_font_changed(size)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; }}
            QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
        """)

        self._sets_list = _SetsListPanel(self.conn)
        self._sets_list.setMinimumWidth(240)
        self._sets_list.setMaximumWidth(360)
        self._sets_list.setStyleSheet(f"background: {_C['bg_surface']}; border-right: 1px solid {_C['border']};")

        self._table = _InstancesTable(self.conn)
        self._table.setStyleSheet(f"background: {_C['bg_input']};")

        self._sets_list.set_selected.connect(self._on_set_selected)

        splitter.addWidget(self._sets_list)
        splitter.addWidget(self._table)
        splitter.setSizes([280, 720])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._sets_list._on_card_click(set_id)

    def _on_set_selected(self, set_id: int):
        self._set_id = set_id
        self._table.load_set(set_id)

    def clear(self):
        self._set_id = None
        self._table.clear()