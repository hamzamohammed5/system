"""
ui/tabs/costing/machine/machine_op_table.py
============================================
_MachineOpTable — جدول عمليات التشغيل مع فلتر واستبدال شامل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem, QMessageBox,
)

from db.costing.operations_repo import fetch_all_machine_ops, delete_machine_op
from models.costing import calc_machine_op_cost
from ui.helpers import (
    make_table, buttons_row, section_label, confirm_delete, danger_button,
)
from ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog import BulkReplaceDialog
from ui.widgets.shared.filter_bar import FilterBar
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.events import bus
from .machine_op_form import _MachineOpForm


class _MachineOpTable(QWidget, LiveConnMixin):
    def __init__(self, conn, form: _MachineOpForm, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._form     = form
        self._all_rows = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── عمليات التشغيل المحفوظة ───"))

        self._filter = FilterBar(self._live_conn(), scope="machine")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "اسم العملية", "التصنيف", "الماكينة", "الوضع", "القيمة", "التكلفة"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 110)
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

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        self._form.load_for_edit(int(self.table.item(row, 0).text()))

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        if self._form.is_editing and self._form._editing_id == op_id:
            self._form._reset()
        if confirm_delete(self, op_name):
            try:
                delete_machine_op(self._live_conn(), op_id)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            bus.data_changed.emit()

    def _bulk_replace(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        dlg = BulkReplaceDialog(
            conn=self._live_conn(), child_type="machine_op",
            child_id=op_id, child_name=op_name, parent=self,
        )
        dlg.exec_()

    def _load(self):
        try:
            conn = self._live_conn()
            self._all_rows = list(fetch_all_machine_ops(conn))
        except Exception:
            self._all_rows = []
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        try:
            conn = self._live_conn()
        except Exception:
            self._filter.set_count(0, 0)
            return
        for op in self._all_rows:
            if not self._filter.match(op["name"], op["category_id"]):
                continue
            cost    = calc_machine_op_cost(conn, op["id"])
            mode_ar = "وقت" if op["mode"] == "time" else "وحدة"
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(op["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(op["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(op["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(op["machine_name"]))
            self.table.setItem(r, 4, QTableWidgetItem(mode_ar))
            self.table.setItem(r, 5, QTableWidgetItem(f"{op['value']:.4f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{cost:.2f} جنيه"))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))