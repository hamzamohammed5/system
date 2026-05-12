"""
ui/tabs/inventory/items/_items_tab.py
======================================
_ItemsTab — تبويب يجمع الفورم والجدول في Splitter.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ._item_form    import _ItemForm
from ._items_table  import _ItemsTable


class _ItemsTab(QWidget):
    def __init__(self, inv_conn, acc_conn, on_select, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        form  = _ItemForm(inv_conn, acc_conn)
        table = _ItemsTable(inv_conn, form, on_select)

        splitter.addWidget(form)
        splitter.addWidget(table)
        splitter.setSizes([320, 580])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)