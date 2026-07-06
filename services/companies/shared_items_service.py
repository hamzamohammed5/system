"""
services/companies/shared_items_service.py
============================================
SharedItemsService — الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات
لكل عمليات العناصر المشتركة بين الشركات (companies.db → shared_items).

المسؤولية:
  - CRUD للعناصر المشتركة عبر db.companies.shared_items_repo
  - نشر عنصر من شركة كعنصر مشترك، وربطه/فك ربطه بشركات أخرى
    عبر db.companies.companies_repo (الدوال المخصصة لهذا الغرض)

لماذا service وليس تواصل مباشر؟
  يحقق هذا الملف الهيكلة المطلوبة:
    ui/tabs/...  →  SharedItemsService  →  shared_items_repo / companies_repo
                 →  companies_schema  →  DB
  طبقة الـ UI (tabs/, widgets/) لا تستدعي db.companies مباشرة أبداً.

الاستخدام:
    from services.companies.shared_items_service import SharedItemsService
    from services.companies.company_service import CompanyService

    conn = CompanyService.get_central_conn_and_init()
    svc  = SharedItemsService(conn)
    items = svc.list_items(shared_type="raw")
"""

from __future__ import annotations
import logging
from dataclasses import dataclass

from db.companies.shared_items_repo import (
    create_shared_items_tables,
    fetch_all_shared_items,
    fetch_shared_item,
    insert_shared_item,
    update_shared_item,
    fetch_linked_companies,
    fetch_shared_items_for_company,
    is_company_linked,
    set_linked_companies,
    get_item_data,
    get_item_as_raw,
    get_item_as_machine,
    get_item_as_labor_op,
)
from db.companies.companies_repo import (
    publish_item_as_shared,
    link_shared_item_to_company,
    unlink_shared_item as _repo_unlink_shared_item,
    delete_shared_item as _repo_delete_shared_item_cascade,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class SharedItemResult:
    id          : int
    name        : str
    shared_type : str
    data        : dict
    updated_at  : str


# ══════════════════════════════════════════════════════════
# SharedItemsService
# ══════════════════════════════════════════════════════════

class SharedItemsService:
    """
    Business Logic للعناصر المشتركة بين الشركات.

    الاستخدام:
        conn = CompanyService.get_central_conn_and_init()
        svc  = SharedItemsService(conn)
    """

    _VALID_TYPES = ("raw", "machine", "labor_op", "machine_op")

    def __init__(self, conn):
        self._conn = conn
        create_shared_items_tables(self._conn)

    # ────────────────────────────────────────────────────
    # Validation
    # ────────────────────────────────────────────────────

    def validate(self, name: str, shared_type: str) -> "str | None":
        if not name.strip():
            return "اسم العنصر مطلوب"
        if shared_type not in self._VALID_TYPES:
            return f"نوع العنصر المشترك غير صالح: {shared_type}"
        return None

    # ────────────────────────────────────────────────────
    # Read — عناصر مشتركة
    # ────────────────────────────────────────────────────

    def list_items(self, shared_type: str = None) -> list[SharedItemResult]:
        rows = fetch_all_shared_items(self._conn, shared_type)
        return [self._to_result(r) for r in rows]

    def get_item(self, item_id: int) -> "SharedItemResult | None":
        row = fetch_shared_item(self._conn, item_id)
        if not row:
            return None
        return self._to_result(row)

    def get_item_data(self, item_id: int) -> dict:
        return get_item_data(self._conn, item_id)

    def get_item_as_raw(self, item_id: int) -> "dict | None":
        return get_item_as_raw(self._conn, item_id)

    def get_item_as_machine(self, item_id: int) -> "dict | None":
        return get_item_as_machine(self._conn, item_id)

    def get_item_as_labor_op(self, item_id: int) -> "dict | None":
        return get_item_as_labor_op(self._conn, item_id)

    def _to_result(self, row) -> SharedItemResult:
        return SharedItemResult(
            id          = row["id"],
            name        = row["name"],
            shared_type = row["shared_type"],
            data        = get_item_data(self._conn, row["id"]),
            updated_at  = row["updated_at"],
        )

    # ────────────────────────────────────────────────────
    # Write — عناصر مشتركة
    # ────────────────────────────────────────────────────

    def add_item(self, name: str, shared_type: str, data: dict = None) -> int:
        err = self.validate(name, shared_type)
        if err:
            raise ValueError(err)
        return insert_shared_item(self._conn, name.strip(), shared_type, data)

    def update_item(self, item_id: int, name: str, data: dict) -> None:
        if not name.strip():
            raise ValueError("اسم العنصر مطلوب")
        update_shared_item(self._conn, item_id, name.strip(), data)

    def delete_item(self, item_id: int) -> None:
        """حذف العنصر المشترك وكل روابطه (cascade عبر FK)."""
        _repo_delete_shared_item_cascade(self._conn, item_id)

    # ────────────────────────────────────────────────────
    # نشر وربط بين الشركات
    # ────────────────────────────────────────────────────

    def publish_from_company(self, source_company_id: int,
                              source_item_id: int, shared_type: str,
                              name: str, notes: str = "") -> int:
        """
        ينشر عنصر من شركة كعنصر مشترك (أو يربط بعنصر موجود بنفس الاسم).
        """
        err = self.validate(name, shared_type)
        if err:
            raise ValueError(err)
        return publish_item_as_shared(
            self._conn, source_company_id, source_item_id,
            shared_type, name.strip(), notes,
        )

    def link_to_company(self, shared_item_id: int, company_id: int) -> int:
        return link_shared_item_to_company(
            self._conn, self._conn, shared_item_id, company_id
        )

    def unlink_from_company(self, shared_item_id: int, company_id: int) -> None:
        _repo_unlink_shared_item(self._conn, shared_item_id, company_id)

    def is_linked(self, shared_item_id: int, company_id: int) -> bool:
        return is_company_linked(self._conn, shared_item_id, company_id)

    def set_linked_companies(self, shared_item_id: int,
                              company_ids: list) -> None:
        set_linked_companies(self._conn, shared_item_id, company_ids)

    def list_linked_companies(self, shared_item_id: int) -> list:
        return fetch_linked_companies(self._conn, shared_item_id)

    def list_for_company(self, company_id: int,
                          shared_type: str = None) -> list[SharedItemResult]:
        rows = fetch_shared_items_for_company(self._conn, company_id, shared_type)
        return [self._to_result(r) for r in rows]
