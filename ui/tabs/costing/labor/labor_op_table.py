"""
ui/tabs/costing/labor/labor_op_table.py
========================================
_LaborOpTable — جدول عمليات العمالة مع دعم العناصر المشتركة.

يرث من SharedItemsListPanel الذي يوحّد:
  - legend العناصر المشتركة/المنشورة
  - FilterBar
  - أزرار تعديل/حذف/استبدال شامل/تعديل مشترك/نشر كمشترك
  - منطق التلوين والتحميل

إصلاحات:
1. _load تمرر local_rows لـ get_shared_labor_ops (منع التكرار)
2. category_name يُعرض الحقيقي (أو "—")
3. علامة 📤 على العمليات المحلية المنشورة كمشتركة
"""

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox

from db.costing.operations_repo import fetch_all_labor_ops, delete_labor_op
from ui.helpers import confirm_delete
from ui.widgets.shared.list_panel_with_shared import SharedItemsListPanel
from ui.tabs.companies.shared_items_mixin import get_shared_labor_ops
from ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog import BulkReplaceDialog


def _to_dict(row) -> dict:
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {}


class _LaborOpTable(SharedItemsListPanel):
    SHARED_TYPE      = "labor_op"
    TABLE_COLS       = ["ID", "اسم العملية", "التصنيف", "الوقت (دقيقة)", "التكلفة / وحدة"]
    FILTER_SCOPE     = "labor"
    TABLE_TITLE      = "─── عمليات العمالة المحفوظة ───"
    HAS_BULK_REPLACE = True

    def __init__(self, conn, settings, form, parent=None):
        self._settings = settings
        self._form     = form
        super().__init__(conn, parent)

    def _setup_column_widths(self, table):
        table.setColumnWidth(0, 40)
        table.setColumnWidth(2, 110)
        table.setColumnWidth(3, 110)
        table.setColumnWidth(4, 130)

    def _fetch_local_rows(self) -> list:
        return [_to_dict(op) for op in fetch_all_labor_ops(self._live_conn())]

    def _get_shared_rows(self, local_rows: list) -> list:
        return get_shared_labor_ops(local_rows)

    def _fill_table_row(self, r: int, item: dict):
        is_shared    = item.get("_is_shared", False)
        is_published = item.get("_is_published", False)
        rate         = self._settings.get_hourly_rate()
        minutes      = item.get("minutes", 0)
        cost         = (minutes / 60.0) * rate
        cat_display  = item.get("category_name") or "—"

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
        self.table.setItem(r, 3, QTableWidgetItem(f"{minutes:.2f}"))
        self.table.setItem(r, 4, QTableWidgetItem(f"{cost:.2f} جنيه"))

    def _edit_item(self, item_id: int):
        self._form.load_for_edit(item_id)

    def _delete_item(self, item_id: int, item_name: str):
        if self._form.is_editing and self._form._editing_id == item_id:
            self._form._reset()
        if confirm_delete(self, item_name):
            try:
                delete_labor_op(self._live_conn(), item_id)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            from ui.events import bus
            bus.data_changed.emit()

    def _bulk_replace_item(self, item_id: int, item_name: str):
        dlg = BulkReplaceDialog(
            conn=self._live_conn(), child_type="labor_op",
            child_id=item_id, child_name=item_name, parent=self,
        )
        dlg.exec_()

    def _get_item_data_for_publish(self, row: dict) -> dict:
        return {
            "minutes":       float(row.get("minutes", 0.0)),
            "category_name": row.get("category_name") or None,
        }
