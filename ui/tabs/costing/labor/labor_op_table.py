"""
ui/tabs/costing/labor/labor_op_table.py
========================================
_LaborOpTable — جدول عمليات العمالة مع فلتر واستبدال شامل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem, QMessageBox,
)

from db.operations_repo import fetch_all_labor_ops, delete_labor_op
from ui.helpers import (
    make_table, buttons_row, section_label, confirm_delete, danger_button,
)
from ui.widgets.bulk_replace_dialog import BulkReplaceDialog
from ui.widgets.filter_bar import FilterBar
from ui.events import bus


class _LaborOpTable(QWidget):
    def __init__(self, conn, settings, form, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._settings = settings
        self._form     = form
        self._all_rows = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── عمليات العمالة المحفوظة ───"))

        self._filter = FilterBar(self.conn, scope="labor")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "اسم العملية", "التصنيف", "الوقت (دقيقة)", "التكلفة / وحدة"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 130)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit    = QPushButton("✏️  تعديل")
        btn_del     = danger_button("🗑️  حذف")
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

    def _selected_row(self):
        return self.table.currentRow()

    def _edit(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        self._form.load_for_edit(int(self.table.item(row, 0).text()))

    def _delete(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        if self._form.is_editing and self._form._editing_id == op_id:
            self._form._reset()
        if confirm_delete(self, op_name):
            delete_labor_op(self.conn, op_id)
            bus.data_changed.emit()

    def _bulk_replace(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        dlg = BulkReplaceDialog(
            conn=self.conn, child_type="labor_op",
            child_id=op_id, child_name=op_name, parent=self,
        )
        dlg.exec_()

    def _load(self):
        self._all_rows = list(fetch_all_labor_ops(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        rate = self._settings.get_hourly_rate()
        self.table.setRowCount(0)
        shown = 0
        for op in self._all_rows:
            if not self._filter.match(op["name"], op["category_id"]):
                continue
            cost = (op["minutes"] / 60.0) * rate
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(op["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(op["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(op["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{op['minutes']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{cost:.2f} جنيه"))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))