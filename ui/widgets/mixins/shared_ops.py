"""
ui/widgets/mixins/shared_ops.py
==========================================
SharedOpsMixin — منطق النشر والتعديل المشترك.
نسخة محدّثة تستخدم emit_company_data_changed بدل bus.data_changed.

  [FIX] _publish_item: إضافة emit_company_data_changed() بعد نجاح النشر.
        القديم: كانت _edit_shared_item و _edit_published_item تُطلقان الإشعار
                لكن _publish_item كانت تنتهي صامتةً → الـ UI لا يتحدث بعد النشر.
        الجديد: emit_company_data_changed() تُستدعى في نهاية _publish_item أيضاً.

  [إصلاح هيكلة] استبدال imports مباشرة من db.companies.* بـ
        CompanyService و SharedItemsService.
        القديم: from db.companies.companies_schema import get_central_connection, create_central_tables
                from db.companies.shared_items_repo import create_shared_items_tables
                central.execute("SELECT id FROM shared_items WHERE ...")  # SQL خام
        الجديد: كل الاستدعاءات عبر CompanyService / SharedItemsService — المسار الصحيح:
                widget → service → repo (db/)
        - CompanyService.get_central_conn_and_init() بدل get_central_connection + create_central_tables
        - SharedItemsService(central) ينشئ جداول shared_items تلقائياً في __init__
        - SharedItemsService.list_items(shared_type) بدل استعلام SQL خام للبحث بالاسم
"""
import logging

from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr

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
            msg_info(parent, tr("warning"), tr("shared_item_not_shared_use_edit"))
            return

        shared_id = self._extract_shared_id(item_id)
        if shared_id is None:
            return

        try:
            from services.companies.company_service import CompanyService
            from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
            central = CompanyService.get_central_conn_and_init()
            SharedItemsDialog(central, shared_id, parent=parent).exec_()
            central.close()
            emit_company_data_changed()
        except Exception as e:
            msg_warning(parent, tr("error"), str(e))

    def _edit_published_item(self, row: dict, shared_type: str, parent=None):
        from ..dialogs.message import msg_warning
        parent = parent or self
        try:
            from services.companies.company_service import CompanyService
            from services.companies.shared_items_service import SharedItemsService
            from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
            central = CompanyService.get_central_conn_and_init()
            svc = SharedItemsService(central)
            match_name = str(row.get("name", "")).strip().lower()
            shared_row = next(
                (it for it in svc.list_items(shared_type)
                 if it.name.strip().lower() == match_name),
                None,
            )
            if shared_row:
                SharedItemsDialog(central, shared_row.id, parent=parent).exec_()
            central.close()
            emit_company_data_changed()
        except Exception as e:
            msg_warning(parent, tr("error"), str(e))

    def _publish_item(self, row: dict, shared_type: str,
                      item_data: dict, parent=None):
        from ..dialogs.message import msg_warning
        parent = parent or self

        if self._is_published(row):
            self._edit_published_item(row, shared_type, parent)
            return

        try:
            from services.companies.company_service import CompanyService
            from services.companies.shared_items_service import SharedItemsService
            from ui.tabs.companies.shared_items_manager_helper._add_shared_item_dialog import (
                PublishAsSharedDialog
            )
            central = CompanyService.get_central_conn_and_init()
            # [FIX] SharedItemsService.__init__ ينشئ جداول shared_items تلقائياً
            SharedItemsService(central)
            PublishAsSharedDialog(
                central_conn=central,
                shared_type=shared_type,
                item_name=row.get("name", ""),
                item_data=item_data,
                parent=parent,
            ).exec_()
            central.close()
            # [FIX] إطلاق الإشعار بعد النشر حتى يتحدث الـ UI
            # كان مفقوداً — _edit_shared_item و_edit_published_item كانا يُطلقانه
            # لكن _publish_item كانت تنتهي صامتةً
            emit_company_data_changed()
        except Exception as e:
            msg_warning(parent, tr("error"), str(e))
