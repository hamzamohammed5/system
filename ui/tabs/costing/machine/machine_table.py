"""
ui/tabs/costing/machine/machine_table.py
==========================================
_MachineTable — جدول الماكينات مع دعم العناصر المشتركة + نشر كمشترك.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem,
    QMessageBox, QLabel,
)
from PyQt5.QtGui import QColor

from db.costing.operations_repo import fetch_all_machines, delete_machine
from ui.helpers import (
    make_table, buttons_row, section_label, confirm_delete, danger_button,
)
from ui.widgets.shared.filter_bar import FilterBar
from ui.tabs.companies.shared_items_mixin import (
    get_shared_machines, is_shared_id, extract_shared_id,
)
from ui.events import bus
from .machine_form import _MachineForm

_SHARED_COLOR = "#2e7d52"
_SHARED_BG    = "#e8f5e9"


def _to_dict(row) -> dict:
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {}


class _MachineTable(QWidget):
    def __init__(self, conn, form: _MachineForm, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._form     = form
        self._all_rows = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

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

        legend = QLabel("🔗 أخضر = ماكينة مشتركة بين الشركات — تعديلها يتعكس فوراً")
        legend.setStyleSheet(
            f"color:{_SHARED_COLOR}; background:{_SHARED_BG};"
            "border-radius:4px; padding:3px 8px; font-size:9pt;"
        )
        root.addWidget(legend)

        self._filter = FilterBar(self._live_conn(), scope="machine")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "جنيه/ساعة", "جنيه/وحدة"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit        = QPushButton("✏️  تعديل")
        btn_del         = danger_button("🗑️  حذف")
        btn_edit_shared = QPushButton("🔗  تعديل المشترك")
        btn_publish     = QPushButton("📤  نشر كمشترك")

        btn_edit_shared.setStyleSheet(
            f"QPushButton {{ background:{_SHARED_BG}; color:{_SHARED_COLOR};"
            "border:1px solid #a5d6a7; border-radius:4px; padding:4px 10px; font-weight:bold; }"
            f"QPushButton:hover {{ background:#c8e6c9; }}"
        )
        btn_publish.setStyleSheet(
            "QPushButton { background:#e3f2fd; color:#1565c0;"
            "border:1px solid #90caf9; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#bbdefb; }"
        )
        for btn in (btn_edit, btn_del, btn_edit_shared, btn_publish):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_edit_shared.clicked.connect(self._edit_shared)
        btn_publish.clicked.connect(self._publish_as_shared)
        root.addLayout(buttons_row(btn_edit, btn_del, btn_edit_shared, btn_publish))

    def _selected_row_data(self):
        row = self.table.currentRow()
        if row == -1:
            return None, None
        item_id   = self.table.item(row, 0).data(0x0100)
        item_name = self.table.item(row, 1).text()
        return item_id, item_name

    def _selected_machine_dict(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        item_id = self.table.item(row, 0).data(0x0100)
        for r in self._all_rows:
            if str(r.get("id")) == str(item_id):
                return r
        return None

    def _edit(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(self, "عنصر مشترك",
                                    "هذه ماكينة مشتركة — استخدم «🔗 تعديل المشترك».")
            return
        self._form.load_for_edit(int(item_id))

    def _edit_shared(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        if not is_shared_id(item_id):
            QMessageBox.information(self, "تنبيه", "هذه ماكينة عادية — استخدم «✏️ تعديل».")
            return
        shared_id = extract_shared_id(item_id)
        if shared_id is None:
            return
        from db.companies.companies_schema import get_central_connection, create_central_tables
        from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
        central = get_central_connection()
        create_central_tables(central)
        dlg = SharedItemsDialog(central, shared_id, parent=self)
        dlg.exec_()
        central.close()

    def _delete(self):
        item_id, name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.warning(self, "عنصر مشترك", "لا يمكن حذف ماكينة مشتركة من هنا.")
            return
        mid = int(item_id)
        if self._form.is_editing and self._form._editing_id == mid:
            self._form._reset()
        if confirm_delete(self, name):
            try:
                delete_machine(self._live_conn(), mid)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            bus.data_changed.emit()

    def _publish_as_shared(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة من الجدول أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(
                self, "مشترك بالفعل",
                "هذه الماكينة مشتركة بالفعل.\n"
                "استخدم «🔗 تعديل المشترك» لتعديل الربط."
            )
            return

        row = self._selected_machine_dict()
        if not row:
            return

        item_data = {
            "rate_per_hour": float(row.get("rate_per_hour", 0.0)),
            "rate_per_unit": float(row.get("rate_per_unit", 0.0)),
        }

        try:
            from db.companies.companies_schema import (
                get_central_connection, create_central_tables
            )
            from db.companies.shared_items_repo import create_shared_items_tables
            from ui.tabs.companies.shared_items_manager_helper._add_sharedItem_dialog import (
                PublishAsSharedDialog
            )
            central = get_central_connection()
            create_central_tables(central)
            create_shared_items_tables(central)

            dlg = PublishAsSharedDialog(
                central_conn = central,
                shared_type  = "machine",
                item_name    = row.get("name", ""),
                item_data    = item_data,
                parent       = self,
            )
            dlg.exec_()
            central.close()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def _load(self):
        try:
            conn = self._live_conn()
            local_rows = [_to_dict(m) for m in fetch_all_machines(conn)]
        except Exception:
            local_rows = []
        shared_rows = get_shared_machines()
        self._all_rows = local_rows + shared_rows
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        for m in self._all_rows:
            if not self._filter.match(m.get("name", ""), m.get("category_id")):
                continue
            is_shared = m.get("is_shared", False)

            r = self.table.rowCount()
            self.table.insertRow(r)

            id_item = QTableWidgetItem("🔗" if is_shared else str(m.get("id", "")))
            id_item.setData(0x0100, m.get("id"))
            self.table.setItem(r, 0, id_item)
            self.table.setItem(r, 1, QTableWidgetItem(
                ("🔗 " if is_shared else "") + m.get("name", "")
            ))
            self.table.setItem(r, 2, QTableWidgetItem(m.get("category_name") or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{m.get('rate_per_hour', 0):.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{m.get('rate_per_unit', 0):.2f}"))

            if is_shared:
                for col in range(self.table.columnCount()):
                    itm = self.table.item(r, col)
                    if itm:
                        itm.setBackground(QColor(_SHARED_BG))
                        itm.setForeground(QColor(_SHARED_COLOR))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))