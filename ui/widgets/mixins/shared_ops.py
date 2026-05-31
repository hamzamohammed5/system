"""
ui/widgets/mixins/shared_ops.py
==========================================
SharedOpsMixin — منطق النشر والتعديل المشترك.
نسخة محدّثة تستخدم emit_company_data_changed بدل bus.data_changed.

  [FIX] _publish_item: إضافة emit_company_data_changed() بعد نجاح النشر.
        القديم: كانت _edit_shared_item و _edit_published_item تُطلقان الإشعار
                لكن _publish_item كانت تنتهي صامتةً → الـ UI لا يتحدث بعد النشر.
        الجديد: emit_company_data_changed() تُستدعى في نهاية _publish_item أيضاً.
"""
import logging

from ui.widgets.core.events import emit_company_data_changed

logger = logging.getLogger(__name__)


class SharedOpsMixin:
    """
    Mixin يوحّد منطق عمليات العناصر المشتركة.

    يفترض:
        self._published_names: set[str]
        self._all_rows: list[dict]
    """

    def _check_shared_id(self, item_id) -> bool:
        try:
            from ui.tabs.companies.shared_items_mixin import is_shared_id
            return is_shared_id(item_id)
        except Exception:
            return False

    def _extract_shared_id(self, item_id):
        try:
            from ui.tabs.companies.shared_items_mixin import extract_shared_id
            return extract_shared_id(item_id)
        except Exception:
            return None

    def _is_published(self, row: dict) -> bool:
        names = getattr(self, "_published_names", set())
        return str(row.get("name", "")).strip().lower() in names

    def _find_row_by_id(self, item_id) -> "dict | None":
        for r in getattr(self, "_all_rows", []):
            if str(r.get("id")) == str(item_id):
                return r
        return None

    def _edit_shared_item(self, item_id, shared_type: str, parent=None):
        from ..dialogs.message import msg_info, msg_warning
        parent = parent or self

        if not self._check_shared_id(item_id):
            row = self._find_row_by_id(item_id)
            if row and self._is_published(row):
                self._edit_published_item(row, shared_type, parent)
                return
            msg_info(parent, "تنبيه", "هذا عنصر عادي — استخدم «✏️ تعديل».")
            return

        shared_id = self._extract_shared_id(item_id)
        if shared_id is None:
            return

        try:
            from db.companies.companies_schema import (
                get_central_connection, create_central_tables
            )
            from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
            central = get_central_connection()
            create_central_tables(central)
            SharedItemsDialog(central, shared_id, parent=parent).exec_()
            central.close()
            emit_company_data_changed()
        except Exception as e:
            msg_warning(parent, "خطأ", str(e))

    def _edit_published_item(self, row: dict, shared_type: str, parent=None):
        from ..dialogs.message import msg_warning
        parent = parent or self
        try:
            from db.companies.companies_schema import (
                get_central_connection, create_central_tables
            )
            from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
            central = get_central_connection()
            create_central_tables(central)
            shared_row = central.execute(
                "SELECT id FROM shared_items WHERE name=? AND shared_type=? LIMIT 1",
                (row.get("name", ""), shared_type)
            ).fetchone()
            if shared_row:
                SharedItemsDialog(central, shared_row["id"], parent=parent).exec_()
            central.close()
            emit_company_data_changed()
        except Exception as e:
            msg_warning(parent, "خطأ", str(e))

    def _publish_item(self, row: dict, shared_type: str,
                      item_data: dict, parent=None):
        from ..dialogs.message import msg_warning
        parent = parent or self

        if self._is_published(row):
            self._edit_published_item(row, shared_type, parent)
            return

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
            PublishAsSharedDialog(
                central_conn=central,
                shared_type=shared_type,
                item_name=row.get("name", ""),
                item_data=item_data,
                parent=parent,
            ).exec_()
            central.close()
            # [FIX] إطلاق الإشعار بعد النشر حتى يتحدث الـ UI
            emit_company_data_changed()
        except Exception as e:
            msg_warning(parent, "خطأ", str(e))