"""
ui/tabs/inventory/items/_items_tab.py
======================================
_ItemsTab — تبويب يجمع الفورم والجدول في Splitter.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ._item_form    import _ItemForm
from ._items_table  import _ItemsTable
from ui.constants import (
    INVENTORY_ITEMS_SPLITTER_HANDLE_W,
    INVENTORY_ITEMS_SPLITTER_FORM_SIZE,
    INVENTORY_ITEMS_SPLITTER_TABLE_SIZE,
    MARGIN_ZERO,
)


class _ItemsTab(QWidget):
    def __init__(self, inv_conn, acc_conn, on_select, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(INVENTORY_ITEMS_SPLITTER_HANDLE_W)

        form  = _ItemForm(inv_conn, acc_conn)
        table = _ItemsTable(inv_conn, form, on_select)

        splitter.addWidget(form)
        splitter.addWidget(table)
        splitter.setSizes([INVENTORY_ITEMS_SPLITTER_FORM_SIZE, INVENTORY_ITEMS_SPLITTER_TABLE_SIZE])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.addWidget(splitter)