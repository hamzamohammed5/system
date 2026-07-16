"""
ui/tabs/costing/labor/labor_op_table.py
=========================================
LaborOpTable — جدول عمليات العمالة.

يرث من SharedItemsListPanel (النمط الموجود والجيد).
[Refactor] استخدام LaborOpService بدل repo مباشر في _fetch_local_rows.
[Refactor] استخدام confirm_delete من ui.widgets.dialogs.confirm (الموثق).
"""

from PyQt5.QtWidgets import QMessageBox

from ui.widgets.dialogs.confirm                            import confirm_delete
from ui.widgets.shared.list_panel_with_shared              import SharedItemsListPanel
from ui.tabs.companies.shared_items_mixin                  import get_shared_labor_ops
from ui.tabs.costing.shared._utils                         import to_dict
from ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog import BulkReplaceDialog
from ui.widgets.core.events                                import emit_company_data_changed
from ui.widgets.core.i18n                                  import tr
from ui.widgets.tables.tables                              import make_item
from ui.constants import (
    LABOR_TABLE_COL0_W, LABOR_TABLE_COL2_W,
    LABOR_TABLE_COL3_W, LABOR_TABLE_COL4_W,
)


class LaborOpTable(SharedItemsListPanel):
    SHARED_TYPE      = "labor_op"
    TABLE_COLS       = [tr("id_col"), tr("op_name"), tr("category"),
                        tr("labor_time_lbl"), tr("cost_per_unit_col")]
    FILTER_SCOPE     = "labor"
    TABLE_TITLE      = tr("labor_op_table_title")
    HAS_BULK_REPLACE = True

    def __init__(self, conn, settings, form, parent=None):
        self._settings = settings
        self._form     = form
        super().__init__(conn, parent)

    def _setup_column_widths(self, table):
        table.setColumnWidth(0, LABOR_TABLE_COL0_W)
        table.setColumnWidth(2, LABOR_TABLE_COL2_W)
        table.setColumnWidth(3, LABOR_TABLE_COL3_W)
        table.setColumnWidth(4, LABOR_TABLE_COL4_W)

    def _fetch_local_rows(self) -> list:
        from services.costing.labor_op_service import LaborOpService
        return [
            {
                "id":            r.id,
                "name":          r.name,
                "minutes":       r.minutes,
                "category_id":   r.category_id,
                "category_name": r.category_name,
            }
            for r in LaborOpService(self._live_conn()).list()
        ]

    def _get_shared_rows(self, local_rows: list) -> list:
        return get_shared_labor_ops(local_rows)

    def _fill_table_row(self, r: int, item: dict):
        is_shared    = item.get("_is_shared", False)
        is_published = item.get("_is_published", False)
        rate         = self._settings.get_hourly_rate()
        minutes      = item.get("minutes", 0)
        cost         = (minutes / 60.0) * rate
        cat_display  = item.get("category_name") or tr("dash")

        if is_shared:
            prefix  = tr("table_shared_prefix")
            id_text = tr("table_shared_icon")
        elif is_published:
            prefix  = tr("table_published_prefix")
            id_text = tr("table_published_icon")
        else:
            prefix  = ""
            id_text = str(item.get("id", ""))

        self.table.setItem(r, 0, make_item(id_text, user_data=item.get("id")))
        self.table.setItem(r, 1, make_item(prefix + item.get("name", "")))
        self.table.setItem(r, 2, make_item(cat_display))
        self.table.setItem(r, 3, make_item(f"{minutes:.2f}"))
        self.table.setItem(r, 4, make_item(f"{cost:.2f} {tr('currency_abbr')}"))

    def _edit_item(self, item_id: int):
        self._form.load_for_edit(item_id)

    def _delete_item(self, item_id: int, item_name: str):
        if (getattr(self._form, "is_editing", False) and
                getattr(self._form, "_editing_id", None) == item_id):
            self._form._reset()
        if confirm_delete(self, item_name):
            try:
                from services.costing.labor_op_service import LaborOpService
                LaborOpService(self._live_conn()).delete(item_id)
            except Exception as e:
                QMessageBox.warning(self, tr("error"), str(e))
                return
            emit_company_data_changed()

    def _bulk_replace_item(self, item_id: int, item_name: str):
        BulkReplaceDialog(
            conn=self._live_conn(), child_type="labor_op",
            child_id=item_id, child_name=item_name, parent=self,
        ).exec_()

    def _get_item_data_for_publish(self, row: dict) -> dict:
        return {
            "minutes":       float(row.get("minutes", 0.0)),
            "category_name": row.get("category_name") or None,
        }