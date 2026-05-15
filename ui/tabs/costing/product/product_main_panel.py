"""
ui/tabs/costing/product/product_main_panel.py
=======================================
_ProductMainPanel — اللوحة الرئيسية: فورم + جدول + BOM tree + تحذير.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.shared.items_repo import (
    fetch_item, delete_item,
    fetch_orphan_bom_rows, delete_orphan_bom_rows,
    cleanup_empty_products_after_orphan_fix,
)
from ui.helpers import confirm_delete
from ui.widgets.costing.component_row import ComponentRow
from ui.widgets.costing.bom_tree      import BomTree
from ui.events import bus

from .product_form  import _FormPanel
from .product_table import _ProductTable, _WarningBar

_SPLITTER_STYLE = """
    QSplitter::handle {
        background: #e0e0e0;
        border-top: 1px solid #ccc;
    }
    QSplitter::handle:hover { background: #bbdefb; }
"""


def _catalog_for_component_row(conn) -> dict:
    from db.shared.items_repo      import fetch_items_by_type
    from db.costing.operations_repo import fetch_all_labor_ops, fetch_all_machine_ops

    result: dict[str, list] = {
        "raw": [], "semi": [], "labor_op": [], "machine_op": []
    }
    for row in fetch_items_by_type(conn, "raw"):
        result["raw"].append((
            row["id"], row["name"], row["category_id"],
            row["category_name"] or None,
        ))
    for row in fetch_items_by_type(conn, "semi"):
        result["semi"].append((
            row["id"], row["name"], row["category_id"],
            row["category_name"] or None,
        ))
    for op in fetch_all_labor_ops(conn):
        result["labor_op"].append((
            op["id"], op["name"], op["category_id"],
            op["category_name"] or None,
        ))
    for op in fetch_all_machine_ops(conn):
        result["machine_op"].append((
            op["id"], op["name"], op["category_id"],
            op["category_name"] or None,
        ))
    return result


class _ProductMainPanel(QWidget):
    def __init__(self, conn, product_type: str, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self.product_type = product_type
        self._build()
        bus.data_changed.connect(self._on_data_changed)

    def _get_catalog(self):
        return _catalog_for_component_row(self.conn)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form = _FormPanel(self.conn, self.product_type, self._get_catalog)
        bus.data_changed.connect(self._refresh_form_catalog)

        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(0)

        self._warning = _WarningBar(
            on_fix=self._fix_orphans,
            on_edit=self._edit_selected
        )
        mid_layout.addWidget(self._warning)

        self._prod_table = _ProductTable(
            self.conn, self.product_type,
            on_select=self._on_product_selected,
            on_edit=self._edit_selected,
            on_delete=self._delete_product
        )
        mid_layout.addWidget(self._prod_table)

        self._bom_tree = BomTree()

        splitter.addWidget(self._form)
        splitter.addWidget(mid_widget)
        splitter.addWidget(self._bom_tree)
        splitter.setSizes([280, 220, 250])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, True)

        root.addWidget(splitter)

    def _on_data_changed(self):
        pid = self._prod_table.selected_pid()
        if pid is not None:
            self._check_orphans(pid)
            self._bom_tree.load(self.conn, pid)

    def _on_product_selected(self, pid):
        if pid is None:
            self._bom_tree.clear_tree()
            self._warning.setVisible(False)
        else:
            self._check_orphans(pid)
            self._bom_tree.load(self.conn, pid)

    def _refresh_form_catalog(self):
        new_catalog = self._get_catalog()
        layout = self._form.rows_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, ComponentRow):
                w.refresh_catalog(new_catalog)

    def _check_orphans(self, pid):
        orphans = fetch_orphan_bom_rows(self.conn, pid)
        item    = fetch_item(self.conn, pid)
        name    = item["name"] if item else f"ID {pid}"
        self._warning.show_orphans(orphans, name)

    def _fix_orphans(self):
        pid = self._prod_table.selected_pid()
        if pid is None:
            return
        orphans = fetch_orphan_bom_rows(self.conn, pid)
        orphan_names = [
            o["child_name"] or f"ID:{o['child_id']}" for o in orphans
        ]
        item = fetch_item(self.conn, pid)
        prod_name = item["name"] if item else f"ID {pid}"

        n = delete_orphan_bom_rows(self.conn, pid)
        self._warning.setVisible(False)
        self._bom_tree.load(self.conn, pid)

        auto_deleted = cleanup_empty_products_after_orphan_fix(self.conn, [pid])
        bus.data_changed.emit()

        if auto_deleted:
            self._form.reset()
            self._bom_tree.clear_tree()
            QMessageBox.information(
                self, "تم — وتم حذف المنتج",
                f"✅ تم حذف {n} مكوّن ناقص:\n"
                + "\n".join(f"  • {nm}" for nm in orphan_names)
                + f"\n\nبما أن «{prod_name}» لم يعد يحتوي على أي مكونات،\n"
                  "تم حذفه تلقائياً."
            )
        else:
            QMessageBox.information(
                self, "تم",
                f"✅ تم حذف {n} مكوّن ناقص:\n"
                + "\n".join(f"  • {nm}" for nm in orphan_names)
            )

    def _edit_selected(self, pid=None):
        if pid is None:
            pid = self._prod_table.selected_pid()
        if pid is None:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً من الجدول أولاً")
            return
        self._warning.setVisible(False)
        self._form.load_product(pid)

    def _delete_product(self, pid):
        if pid is None:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً أولاً")
            return
        item = fetch_item(self.conn, pid)
        if not item:
            return
        if confirm_delete(self, item["name"]):
            if self._form.is_editing and self._form._editing_id == pid:
                self._form.reset()
            delete_item(self.conn, pid)
            self._warning.setVisible(False)
            self._bom_tree.clear_tree()
            bus.data_changed.emit()