"""
ui/tabs/costing/raw/raw_table_panel.py
=======================================
_TablePanel — جدول الخامات مع فلتر واستبدال شامل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem, QMessageBox,
)

from db.items_repo import fetch_items_by_type, delete_item
from models.costing import raw_unit_price
from ui.helpers import (
    make_table, buttons_row, section_label, confirm_delete, danger_button,
)
from ui.widgets.bulk_replace_dialog import BulkReplaceDialog
from ui.widgets.filter_bar import FilterBar
from ui.events import bus


class _TablePanel(QWidget):
    def __init__(self, conn, input_panel, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self._input_panel = input_panel
        self._all_rows    = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(12, 8, 12, 12)

        root.addWidget(section_label("─── الخامات المحفوظة ───"))

        self._filter = FilterBar(self.conn, scope="raw")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "السعر الكلي", "الكمية الكلية", "سعر الوحدة"],
            stretch_col=1,
        )
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 95)
        root.addWidget(self.table)

        btn_edit    = QPushButton("✏️  تعديل المحدد")
        btn_del     = danger_button("🗑️  حذف المحدد")
        btn_replace = QPushButton("🔄  استبدال شامل")
        btn_replace.setStyleSheet(
            "QPushButton { background:#e65100; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#bf360c; }"
        )
        for btn in (btn_edit, btn_del, btn_replace):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_replace.clicked.connect(self._bulk_replace)
        root.addLayout(buttons_row(btn_edit, btn_del, btn_replace))

    def _selected_id_and_name(self):
        row = self.table.currentRow()
        if row == -1:
            return None, None
        return (
            int(self.table.item(row, 0).text()),
            self.table.item(row, 1).text(),
        )

    def _edit(self):
        item_id, _ = self._selected_id_and_name()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة من الجدول أولاً")
            return
        self._input_panel.load_for_edit(item_id)

    def _delete(self):
        item_id, item_name = self._selected_id_and_name()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة أولاً")
            return
        if self._input_panel.is_editing and self._input_panel._editing_id == item_id:
            self._input_panel._reset()
        if confirm_delete(self, item_name):
            delete_item(self.conn, item_id)
            bus.data_changed.emit()

    def _bulk_replace(self):
        item_id, item_name = self._selected_id_and_name()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة من الجدول أولاً")
            return
        dlg = BulkReplaceDialog(
            conn=self.conn, child_type="raw",
            child_id=item_id, child_name=item_name, parent=self,
        )
        dlg.exec_()

    def _load(self):
        self._all_rows = list(fetch_items_by_type(self.conn, "raw"))
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        for row in self._all_rows:
            if not self._filter.match(row["name"], row["category_id"]):
                continue
            tq    = row["total_qty"]
            price = row["price"]
            unit  = raw_unit_price(row)
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(str(tq) if tq is not None else "—"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{unit:.4f}"))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))