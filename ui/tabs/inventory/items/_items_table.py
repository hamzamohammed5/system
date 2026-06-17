"""
ui/tabs/inventory/items/_items_table.py
========================================
_ItemsTable — جدول أصناف المخزن مع تعديل وحذف.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem, QMessageBox,
)
from PyQt5.QtGui import QColor

from db.inventory.inventory_repo import (
    fetch_all_inventory, fetch_inventory_item, delete_inventory_item,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.theme import _C


class _ItemsTable(QWidget, BusConnectedMixin):
    def __init__(self, inv_conn, form, on_select, parent=None):
        super().__init__(parent)
        self.inv_conn   = inv_conn
        self._form      = form
        self._on_select = on_select
        self._build()
        self._load()
        self._connect_bus(data=True)

    def _on_data_changed(self):
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label(tr("inventory_items_header")))

        self.table = make_table(
            [tr("id_col"), tr("item"), tr("unit"), tr("balance"), tr("inventory_min_qty_label"),
             tr("avg_cost"), tr("total_value")],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 40, 2: 70, 3: 80, 4: 80, 5: 110, 6: 110},
            stretch_col=1
        )
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self._selected_id())
        )
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton(f"✏️  {tr('edit')}")
        btn_del  = danger_button(f"🗑️  {tr('delete')}")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _selected_id(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        return int(self.table.item(row, 0).text())

    def _load(self):
        rows = fetch_all_inventory(self.inv_conn)
        self.table.setRowCount(0)
        for inv in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(inv["id"])))
            name_item = QTableWidgetItem(inv["name"])
            name_item.setToolTip(inv["name"])
            self.table.setItem(r, 1, name_item)
            self.table.setItem(r, 2, QTableWidgetItem(inv["unit"]))

            qty_item = QTableWidgetItem(f"{inv['qty_on_hand']:,.4g}")
            if inv["qty_on_hand"] <= inv["qty_min"]:
                qty_item.setForeground(QColor(_C["stock_critical_fg"]))
                qty_item.setToolTip(tr("inventory_below_min_tooltip").format(min=f"{inv['qty_min']:,.4g}"))
            self.table.setItem(r, 3, qty_item)

            self.table.setItem(r, 4, QTableWidgetItem(f"{inv['qty_min']:,.4g}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{inv['avg_cost']:,.4f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{inv['total_value']:,.2f}"))

    def _edit(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, tr("warning"), tr("inventory_select_item"))
            return
        self._form.load_for_edit(inv_id)

    def _delete(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, tr("warning"), tr("inventory_select_item"))
            return
        inv = fetch_inventory_item(self.inv_conn, inv_id)
        if confirm_delete(self, inv["name"]):
            delete_inventory_item(self.inv_conn, inv_id)
            emit_company_data_changed()

    def closeEvent(self, event):
        self._disconnect_bus()
        super().closeEvent(event)
