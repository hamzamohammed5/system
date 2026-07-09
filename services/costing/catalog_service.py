"""
services/costing/catalog_service.py
======================================
CatalogService — ينقل منطق catalog_builder.py إلى services layer.

يبني الـ catalog المستخدم في ComponentRow ويدمج العناصر المحلية
مع المشتركة (عبر CompanyService و SharedItemsService — لا يلمس
db.companies مباشرة، لأن هذا الـ service مسؤول فقط عن db costing/shared).

يُستخدم من:
  - ui/tabs/costing/product/_catalog_provider.py
  - ui/tabs/costing/shared/catalog_builder.py  (يصبح thin wrapper)

الـ catalog شكله:
  {
    "raw":        [(id, name, category_name, price, total_qty), ...],
    "semi":       [(id, name, category_name, price, None), ...],
    "final":      [(id, name, category_name, price, None), ...],
    "labor_op":   [(id, name, category_name, minutes), ...],
    "machine_op": [(id, name, category_name, mode, machine_name), ...],
  }
"""

from __future__ import annotations
from typing import Dict, List, Any

SHARED_CATEGORY = "🔗 مشترك"


class CatalogService:
    """
    Service لبناء الـ catalog الكامل للـ ComponentRow.

    يدمج العناصر المحلية مع المشتركة لكل نوع، عبر CompanyService
    و SharedItemsService (بدل التواصل المباشر مع db.companies).

    الاستخدام:
        svc = CatalogService(conn)
        catalog = svc.build()
    """

    def __init__(self, conn):
        self.conn = conn

    # ── API رئيسي ─────────────────────────────────────────

    def build(self) -> Dict[str, List]:
        """يبني الـ catalog الكامل لكل الأنواع."""
        return {
            "raw":        self.build_raw(),
            "semi":       self.build_semi(),
            "final":      self.build_final(),
            "labor_op":   self.build_labor_ops(),
            "machine_op": self.build_machine_ops(),
        }

    def build_raw(self) -> List:
        """خامات محلية + مشتركة."""
        from db.shared.items_repo import fetch_items_by_type
        local = [
            (r["id"], r["name"], r.get("category_name") or "",
             r["price"], r.get("total_qty"))
            for r in fetch_items_by_type(self.conn, "raw")
        ]
        shared = [
            (item["id"], item["name"], SHARED_CATEGORY,
             float(item.get("price", 0.0)), item.get("total_qty"))
            for item in self._fetch_shared("raw")
        ]
        return local + shared

    def build_semi(self) -> List:
        """نصف مصنع محلي فقط."""
        from db.shared.items_repo import fetch_items_by_type
        return [
            (r["id"], r["name"], r.get("category_name") or "", 0.0, None)
            for r in fetch_items_by_type(self.conn, "semi")
        ]

    def build_final(self) -> List:
        """منتج نهائي محلي فقط."""
        from db.shared.items_repo import fetch_items_by_type
        return [
            (r["id"], r["name"], r.get("category_name") or "", 0.0, None)
            for r in fetch_items_by_type(self.conn, "final")
        ]

    def build_labor_ops(self) -> List:
        """عمليات عمالة محلية + مشتركة."""
        try:
            from db.costing.operations_repo import fetch_all_labor_ops
            local = [
                (r["id"], r["name"], r.get("category_name") or "",
                 r.get("minutes", 0.0))
                for r in fetch_all_labor_ops(self.conn)
            ]
        except Exception:
            local = []

        shared = [
            (item["id"], item["name"], SHARED_CATEGORY,
             float(item.get("minutes", 0.0)))
            for item in self._fetch_shared("labor_op")
        ]
        return local + shared

    def build_machine_ops(self) -> List:
        """عمليات تشغيل محلية + مشتركة."""
        try:
            from db.costing.operations_repo import fetch_all_machine_ops
            local = [
                (r["id"], r["name"], r.get("category_name") or "",
                 r.get("mode", "time"), r.get("machine_name", ""))
                for r in fetch_all_machine_ops(self.conn)
            ]
        except Exception:
            local = []

        shared = [
            (item["id"], item["name"], SHARED_CATEGORY,
             item.get("mode", "time"), item.get("machine_name", ""))
            for item in self._fetch_shared("machine_op")
        ]
        return local + shared

    # ── مساعد جلب المشترك ─────────────────────────────────

    def _fetch_shared(self, shared_type: str) -> List[dict]:
        """
        يجيب العناصر المشتركة للشركة النشطة عبر CompanyService
        و SharedItemsService — بدون لمس db.companies مباشرة.

        يرجع list of dicts مع id = "shared:{n}" (نفس شكل الإخراج السابق).
        """
        try:
            from services.companies.company_service import CompanyService
            if not CompanyService.is_company_ready():
                return []
            company_id = CompanyService.get_current_company_id()
            if company_id is None:
                return []

            from services.companies.shared_items_service import SharedItemsService
            conn = CompanyService.get_central_conn_and_init()
            svc  = SharedItemsService(conn)

            items = svc.list_for_company(company_id, shared_type)

            result = []
            for it in items:
                item = {"id": f"shared:{it.id}", "name": it.name}
                item.update(it.data or {})
                result.append(item)
            return result

        except Exception as e:
            import sys
            print(f"[CatalogService] _fetch_shared({shared_type}) error: {e}",
                  file=sys.stderr)
            return []