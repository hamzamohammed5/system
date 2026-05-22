"""
ui/tabs/costing/machine/machine_table.py
=========================================
_MachineTable — جدول الماكينات مع فلتر.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem, QMessageBox,
)

from db.costing.operations_repo import fetch_all_machines, delete_machine
from ui.helpers import (
    make_table, buttons_row, section_label, confirm_delete, danger_button,
)
from ui.widgets.shared.filter_bar import FilterBar
from ui.events import bus
from .machine_form import _MachineForm


class _MachineTable(QWidget):
    def __init__(self, conn, form: _MachineForm, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._form     = form
        self._all_rows = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    # ── connection صالح دايماً ────────────────────────────

    def _live_conn(self):
        if self.conn is not None:
            try:
                self.conn.execute("SELECT 1")
                return self.conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── الماكينات المحفوظة ───"))

        self._filter = FilterBar(self._live_conn(), scope="machine")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "جنيه/ساعة", "جنيه/وحدة"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        self._form.load_for_edit(int(self.table.item(row, 0).text()))

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        mid  = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        if self._form.is_editing and self._form._editing_id == mid:
            self._form._reset()
        if confirm_delete(self, name):
            try:
                delete_machine(self._live_conn(), mid)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            bus.data_changed.emit()

    def _load(self):
        try:
            conn = self._live_conn()
            self._all_rows = list(fetch_all_machines(conn))
        except Exception:
            self._all_rows = []
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        for m in self._all_rows:
            if not self._filter.match(m["name"], m["category_id"]):
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(m["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(m["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(m["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{m['rate_per_hour']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{m['rate_per_unit']:.2f}"))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))