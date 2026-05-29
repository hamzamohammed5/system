"""
ui/tabs/costing/machine/machine_table.py
========================================
_MachineTable — جدول الماكينات مع دعم العناصر المشتركة.

[Refactor] استخدام MachineService في الحذف بدل operations_repo مباشرة.
[Fix] توحيد import confirm_delete من ui.widgets.dialogs.confirm (الموثق).
[Fix] استخدام emit_company_data_changed بدل bus.data_changed.emit()
      حسب توصية files_reference/models&services.md

يرث من SharedItemsListPanel الذي يوحّد:
  - legend العناصر المشتركة/المنشورة
  - FilterBar
  - أزرار تعديل/حذف/تعديل مشترك/نشر كمشترك
  - منطق التلوين والتحميل
"""

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox

from ui.widgets.dialogs.confirm                import confirm_delete
from ui.widgets.shared.list_panel_with_shared  import SharedItemsListPanel
from ui.tabs.companies.shared_items_mixin      import get_shared_machines
from ui.tabs.costing.shared._utils             import to_dict
from ui.widgets.core.events                    import emit_company_data_changed
from .machine_form import _MachineForm


class _MachineTable(SharedItemsListPanel):
    SHARED_TYPE      = "machine"
    TABLE_COLS       = ["ID", "الاسم", "التصنيف", "جنيه/ساعة", "جنيه/وحدة"]
    FILTER_SCOPE     = "machine"
    TABLE_TITLE      = "─── الماكينات المحفوظة ───"
    HAS_BULK_REPLACE = False

    def __init__(self, conn, form: _MachineForm, parent=None):
        self._form = form
        super().__init__(conn, parent)

    def _setup_column_widths(self, table):
        table.setColumnWidth(0, 40)
        table.setColumnWidth(2, 110)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 90)

    def _fetch_local_rows(self) -> list:
        from services.costing.machine_service import MachineService
        return [
            {
                "id":            m.id,
                "name":          m.name,
                "rate_per_hour": m.rate_per_hour,
                "rate_per_unit": m.rate_per_unit,
                "category_id":   m.category_id,
                "category_name": m.category_name,
            }
            for m in MachineService(self._live_conn()).list()
        ]

    def _get_shared_rows(self, local_rows: list) -> list:
        return get_shared_machines(local_rows)

    def _fill_table_row(self, r: int, item: dict):
        is_shared    = item.get("_is_shared", False)
        is_published = item.get("_is_published", False)
        cat_display  = item.get("category_name") or "—"

        if is_shared:
            prefix = "🔗 "
            id_text = "🔗"
        elif is_published:
            prefix = "📤 "
            id_text = "📤"
        else:
            prefix  = ""
            id_text = str(item.get("id", ""))

        id_item = QTableWidgetItem(id_text)
        id_item.setData(0x0100, item.get("id"))
        self.table.setItem(r, 0, id_item)
        self.table.setItem(r, 1, QTableWidgetItem(prefix + item.get("name", "")))
        self.table.setItem(r, 2, QTableWidgetItem(cat_display))
        self.table.setItem(r, 3, QTableWidgetItem(f"{item.get('rate_per_hour', 0):.2f}"))
        self.table.setItem(r, 4, QTableWidgetItem(f"{item.get('rate_per_unit', 0):.2f}"))

    def _edit_item(self, item_id: int):
        self._form.load_for_edit(item_id)

    def _delete_item(self, item_id: int, item_name: str):
        if self._form.is_editing and self._form._editing_id == item_id:
            self._form._reset()
        if confirm_delete(self, item_name):
            try:
                from services.costing.machine_service import MachineService
                MachineService(self._live_conn()).delete(item_id)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
            emit_company_data_changed()

    def _get_item_data_for_publish(self, row: dict) -> dict:
        return {
            "rate_per_hour": float(row.get("rate_per_hour", 0.0)),
            "rate_per_unit": float(row.get("rate_per_unit", 0.0)),
            "category_name": row.get("category_name") or None,
        }

    # ── تعديل مشترك (override لـ machine) ──

    def _on_edit_shared(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        self._edit_shared_item(item_id, self.SHARED_TYPE, self)