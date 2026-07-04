"""
ui/tabs/inventory/items/_items_table.py
========================================
_ItemsTable — جدول أصناف المخزن مع تعديل وحذف.
"""
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem, QMessageBox,
)
from PyQt5.QtGui import QColor

from db.inventory.inventory_repo import (
    fetch_all_inventory, fetch_inventory_item, delete_inventory_item,
)

from ui.widgets.tables.tables       import auto_fit_columns
from ui.widgets.panels.form_labels   import section_title
from ui.widgets.components.button   import make_btn
from ui.widgets.dialogs.confirm      import confirm_delete

from ui.widgets.tables.tables       import make_table

from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.constants import COL_MIN_WIDTH, INVENTORY_COL_MAX_W, INVENTORY_INPUT_MIN_H

def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(6)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row

class _ItemsTable(QWidget, WidgetMixin):
    def __init__(self, inv_conn, form, on_select, parent=None):
        super().__init__(parent)
        self.inv_conn   = inv_conn
        self._form      = form
        self._on_select = on_select
        self._init_widget_mixin(theme=False, font=False, lang=True, data=True)
        self._build()
        self._load()

    def _on_data_changed(self, *_):
        self._load()

    def _refresh_data(self, company_id=None):
        self._load()

    def _refresh_lang(self, *_):
        pass  # الأعمدة تُبنى مرة واحدة في _build

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_title(tr("inventory_items_header")))

        self.table = make_table(
            [tr("id_col"), tr("item"), tr("unit"), tr("balance"), tr("inventory_min_qty_label"),
             tr("avg_cost"), tr("total_value")],
            stretch_col=1
        )

        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self._selected_id())
        )
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton(tr("edit"))
        btn_del  = make_btn(tr("delete"), style="danger")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(INVENTORY_INPUT_MIN_H)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _selected_id(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        return int(self.table.item(row, 0).text())

    def _load(self):
        from ui.theme import _C
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
        auto_fit_columns(
        self.table,
        fixed_cols=[0, 2, 3, 4, 5, 6],
        stretch_col=1,
        min_width=COL_MIN_WIDTH,
        max_width=INVENTORY_COL_MAX_W,
    )

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
