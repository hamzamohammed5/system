"""
ui/tabs/costing/labor/labor_op_table.py  (نسخة محدثة — مع نشر كمشترك)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem,
    QMessageBox, QLabel,
)
from PyQt5.QtGui import QColor

from db.costing.operations_repo import fetch_all_labor_ops, delete_labor_op
from ui.helpers import (
    make_table, buttons_row, section_label, confirm_delete, danger_button,
)
from ui.widgets.costing.bulk_replace.bulk_replace_dialog import BulkReplaceDialog
from ui.widgets.shared.filter_bar import FilterBar
from ...companies.shared_items_mixin import (
    get_shared_labor_ops, is_shared_id, extract_shared_id,
)
from ui.events import bus

_SHARED_COLOR = "#2e7d52"
_SHARED_BG    = "#e8f5e9"


def _to_dict(row) -> dict:
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {}


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
        root.addWidget(section_label("─── عمليات العمالة المحفوظة ───"))

        legend = QLabel("🔗 أخضر = عملية مشتركة بين الشركات")
        legend.setStyleSheet(
            f"color:{_SHARED_COLOR}; background:{_SHARED_BG};"
            "border-radius:4px; padding:3px 8px; font-size:9pt;"
        )
        root.addWidget(legend)

        self._filter = FilterBar(self._live_conn(), scope="labor")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "اسم العملية", "التصنيف", "الوقت (دقيقة)", "التكلفة / وحدة"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 130)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit        = QPushButton("✏️  تعديل")
        btn_del         = danger_button("🗑️  حذف")
        btn_replace     = QPushButton("🔄  استبدال شامل")
        btn_edit_shared = QPushButton("🔗  تعديل المشترك")
        btn_publish     = QPushButton("📤  نشر كمشترك")

        btn_replace.setStyleSheet(
            "QPushButton { background:#e65100; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#bf360c; }"
        )
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
        for btn in (btn_edit, btn_del, btn_replace, btn_edit_shared, btn_publish):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_replace.clicked.connect(self._bulk_replace)
        btn_edit_shared.clicked.connect(self._edit_shared)
        btn_publish.clicked.connect(self._publish_as_shared)
        root.addLayout(buttons_row(btn_edit, btn_del, btn_replace,
                                    btn_edit_shared, btn_publish))

    def _selected_row_data(self):
        row = self.table.currentRow()
        if row == -1:
            return None, None
        item_id   = self.table.item(row, 0).data(0x0100)
        item_name = self.table.item(row, 1).text()
        return item_id, item_name

    def _selected_op_dict(self):
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
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(
                self, "عنصر مشترك",
                "هذه عملية مشتركة — استخدم زر «تعديل المشترك»."
            )
            return
        self._form.load_for_edit(int(item_id))

    def _edit_shared(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        if not is_shared_id(item_id):
            QMessageBox.information(self, "تنبيه", "هذه عملية عادية — استخدم «تعديل».")
            return
        shared_id = extract_shared_id(item_id)
        from db.companies.companies_schema import get_central_connection, create_central_tables
        from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
        central = get_central_connection()
        create_central_tables(central)
        dlg = SharedItemsDialog(central, shared_id, parent=self)
        dlg.exec_()
        central.close()
        bus.data_changed.emit()

    def _delete(self):
        item_id, item_name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.warning(self, "عنصر مشترك", "لا يمكن حذف عملية مشتركة من هنا.")
            return
        op_id = int(item_id)
        if self._form.is_editing and self._form._editing_id == op_id:
            self._form._reset()
        if confirm_delete(self, item_name):
            try:
                delete_labor_op(self._live_conn(), op_id)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            bus.data_changed.emit()

    def _bulk_replace(self):
        item_id, item_name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(self, "تنبيه", "الاستبدال الشامل غير متاح للعناصر المشتركة.")
            return
        dlg = BulkReplaceDialog(
            conn=self._live_conn(), child_type="labor_op",
            child_id=int(item_id), child_name=item_name, parent=self,
        )
        dlg.exec_()

    def _publish_as_shared(self):
        """نشر عملية عمالة محلية كمشتركة بين الشركات."""
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عملية من الجدول أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(
                self, "مشترك بالفعل",
                "هذه العملية مشتركة بالفعل.\n"
                "استخدم «🔗 تعديل المشترك» لتعديل الربط."
            )
            return

        row = self._selected_op_dict()
        if not row:
            return

        item_data = {"minutes": float(row.get("minutes", 0.0))}

        try:
            from db.companies.companies_schema import (
                get_central_connection, create_central_tables
            )
            from db.companies.shared_items_repo import create_shared_items_tables
            from ui.tabs.companies.shared_items_manager_helper._add_shared_item_dialog import (
                PublishAsSharedDialog
            )
            central = get_central_connection()
            create_central_tables(central)
            create_shared_items_tables(central)

            dlg = PublishAsSharedDialog(
                central_conn = central,
                shared_type  = "labor_op",
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
            local_rows = [_to_dict(op) for op in fetch_all_labor_ops(conn)]
        except Exception:
            local_rows = []
        shared_rows = get_shared_labor_ops()
        self._all_rows = local_rows + shared_rows
        self._apply_filter()

    def _apply_filter(self):
        rate = self._settings.get_hourly_rate()
        self.table.setRowCount(0)
        shown = 0
        for op in self._all_rows:
            if not self._filter.match(op.get("name", ""), op.get("category_id")):
                continue
            is_shared = op.get("is_shared", False)
            minutes   = op.get("minutes", 0)
            cost      = (minutes / 60.0) * rate

            r = self.table.rowCount()
            self.table.insertRow(r)

            id_item = QTableWidgetItem("🔗" if is_shared else str(op.get("id", "")))
            id_item.setData(0x0100, op.get("id"))
            self.table.setItem(r, 0, id_item)
            self.table.setItem(r, 1, QTableWidgetItem(("🔗 " if is_shared else "") + op.get("name", "")))
            self.table.setItem(r, 2, QTableWidgetItem(op.get("category_name") or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{minutes:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{cost:.2f} جنيه"))

            if is_shared:
                for col in range(self.table.columnCount()):
                    item = self.table.item(r, col)
                    if item:
                        item.setBackground(QColor(_SHARED_BG))
                        item.setForeground(QColor(_SHARED_COLOR))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))