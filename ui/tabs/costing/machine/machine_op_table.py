"""
ui/tabs/costing/machine/machine_op_table.py
============================================
_MachineOpTable — جدول عمليات التشغيل مع دعم العناصر المشتركة.

يرث من SharedItemsListPanel الذي يوحّد:
  - legend العناصر المشتركة/المنشورة
  - FilterBar
  - أزرار تعديل/حذف/استبدال شامل/تعديل مشترك/نشر كمشترك
  - منطق التلوين والتحميل

[M3] إصلاحات:
  - حذف _to_dict() المحلية → استخدام to_dict من _utils
  - استخدام emit_company_data_changed() بدل bus.data_changed.emit()
"""

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox

from db.costing.operations_repo import fetch_all_machine_ops, delete_machine_op
from models.costing import calc_machine_op_cost
from ui.helpers import confirm_delete
from ui.widgets.shared.list_panel_with_shared import SharedItemsListPanel
from ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog import BulkReplaceDialog
from ui.tabs.costing.shared._utils import to_dict
from ui.widgets.core.events import emit_company_data_changed
from .machine_op_form import _MachineOpForm


class _MachineOpTable(SharedItemsListPanel):
    SHARED_TYPE      = "machine_op"
    TABLE_COLS       = ["ID", "اسم العملية", "التصنيف", "الماكينة", "الوضع", "القيمة", "التكلفة"]
    FILTER_SCOPE     = "machine"
    TABLE_TITLE      = "─── عمليات التشغيل المحفوظة ───"
    HAS_BULK_REPLACE = True

    def __init__(self, conn, form: _MachineOpForm, parent=None):
        self._form = form
        super().__init__(conn, parent)

    def _setup_column_widths(self, table):
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 140)
        table.setColumnWidth(2, 100)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 70)
        table.setColumnWidth(5, 70)
        table.setColumnWidth(6, 110)
        table.setAlternatingRowColors(True)

    def _fetch_local_rows(self) -> list:
        return [to_dict(op) for op in fetch_all_machine_ops(self._live_conn())]

    def _get_shared_rows(self, local_rows: list) -> list:
        try:
            from ui.tabs.companies.shared_items_mixin import get_shared_machine_ops
            return get_shared_machine_ops(local_rows)
        except Exception:
            return []

    def _fill_table_row(self, r: int, item: dict):
        is_shared    = item.get("_is_shared", False)
        is_published = item.get("_is_published", False)

        mode_ar     = "وقت" if item.get("mode") == "time" else "وحدة"
        cat_display = item.get("category_name") or "—"

        try:
            conn  = self._live_conn()
            cost  = calc_machine_op_cost(conn, item.get("id")) if not is_shared else 0.0
        except Exception:
            cost = 0.0

        if is_shared:
            prefix  = "🔗 "
            id_text = "🔗"
        elif is_published:
            prefix  = "📤 "
            id_text = "📤"
        else:
            prefix  = ""
            id_text = str(item.get("id", ""))

        id_item = QTableWidgetItem(id_text)
        id_item.setData(0x0100, item.get("id"))
        self.table.setItem(r, 0, id_item)
        self.table.setItem(r, 1, QTableWidgetItem(prefix + item.get("name", "")))
        self.table.setItem(r, 2, QTableWidgetItem(cat_display))
        self.table.setItem(r, 3, QTableWidgetItem(item.get("machine_name", "—")))
        self.table.setItem(r, 4, QTableWidgetItem(mode_ar))
        self.table.setItem(r, 5, QTableWidgetItem(f"{item.get('value', 0):.4f}"))
        self.table.setItem(r, 6, QTableWidgetItem(f"{cost:.2f} جنيه"))

    def _edit_item(self, item_id: int):
        self._form.load_for_edit(item_id)

    def _delete_item(self, item_id: int, item_name: str):
        if self._form.is_editing and self._form._editing_id == item_id:
            self._form._reset()
        if confirm_delete(self, item_name):
            try:
                delete_machine_op(self._live_conn(), item_id)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            emit_company_data_changed()

    def _bulk_replace_item(self, item_id: int, item_name: str):
        dlg = BulkReplaceDialog(
            conn=self._live_conn(), child_type="machine_op",
            child_id=item_id, child_name=item_name, parent=self,
        )
        dlg.exec_()

    def _get_item_data_for_publish(self, row: dict) -> dict:
        return {
            "mode":          row.get("mode", "time"),
            "value":         float(row.get("value", 0.0)),
            "machine_name":  row.get("machine_name") or None,
            "category_name": row.get("category_name") or None,
        }