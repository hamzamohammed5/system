"""
services/costing/bulk_replace_service.py
==========================================
BulkReplaceService — منطق الاستبدال الشامل بدون PyQt.

يُستدعى من BulkReplaceDialog فقط.
"""

from __future__ import annotations


class BulkReplaceService:
    """
    يطبق استبدال / تعديل كمية شامل على قائمة منتجات.

    الاستخدام:
        svc = BulkReplaceService(conn)
        updated, errors = svc.apply(
            child_type   = "raw",
            old_child_id = 5,
            new_child_id = 7,          # None لو do_replace=False
            product_rows = [           # list of (product_id, current_qty)
                (10, 2.0), (11, 1.5)
            ],
            uniform_qty  = None,       # None = يستخدم كمية كل منتج من product_rows
            do_replace   = True,
            do_qty       = True,
        )
        # updated : int   — عدد المنتجات المحدّثة بنجاح
        # errors  : list  — قائمة رسائل الخطأ (فارغة لو نجح الكل)
    """

    def __init__(self, conn):
        self.conn = conn

    def apply(
        self,
        *,
        child_type:   str,
        old_child_id: int,
        new_child_id: int | None,
        product_rows: list[tuple[int, float]],   # [(product_id, qty), ...]
        uniform_qty:  float | None = None,
        do_replace:   bool = True,
        do_qty:       bool = True,
    ) -> tuple[int, list[str]]:
        """
        يرجع (عدد_المندّثين, قائمة_أخطاء).
        """
        from db.shared.items_repo import fetch_bom, replace_bom, fetch_item

        updated = 0
        errors: list[str] = []

        for product_id, row_qty in product_rows:
            try:
                bom     = fetch_bom(self.conn, product_id)
                new_bom = []
                for child_type_b, child_id, qty, waste_pct in bom:
                    if child_type_b == child_type and child_id == old_child_id:
                        final_cid = new_child_id if do_replace else child_id
                        if uniform_qty is not None:
                            final_qty = uniform_qty
                        elif do_qty:
                            final_qty = row_qty
                        else:
                            final_qty = qty
                        new_bom.append((child_type_b, final_cid, final_qty, waste_pct))
                    else:
                        new_bom.append((child_type_b, child_id, qty, waste_pct))

                replace_bom(self.conn, product_id, new_bom)
                updated += 1

            except Exception as exc:
                item = fetch_item(self.conn, product_id)
                name = item["name"] if item else f"ID:{product_id}"
                errors.append(f"• {name}: {exc}")

        return updated, errors

    # ── مساعدات ──────────────────────────────────────────────
    #
    # [إصلاح هيكلي] كانت هذه الدوال تستورد من ui/tabs/... (كسر هيكلي:
    # service بيستدعي ui). الآن تستخدم db/costing/operations_repo.py
    # فقط، كما يجب لأي service داخل مجال costing.

    def get_element_name(self, child_type: str, child_id: int) -> str:
        """يرجع اسم عنصر BOM حسب نوعه."""
        from db.costing.operations_repo import fetch_element_name
        name = fetch_element_name(self.conn, child_type, child_id)
        return name if name else f"ID:{child_id}"

    def fetch_candidates(self, child_type: str,
                         exclude_id: int) -> list[tuple[int, str, str]]:
        """
        يرجع عناصر بديلة من نفس النوع بدون العنصر الحالي.
        list of (id, name, category_name)
        """
        from db.shared.items_repo import fetch_items_by_type
        from db.costing.operations_repo import (
            fetch_all_labor_ops, fetch_all_machine_ops,
        )

        if child_type == "raw":
            rows = fetch_items_by_type(self.conn, "raw")
        elif child_type == "labor_op":
            rows = fetch_all_labor_ops(self.conn)
        elif child_type == "machine_op":
            rows = fetch_all_machine_ops(self.conn)
        else:
            return []

        return [
            (r["id"], r["name"], r["category_name"] or "")
            for r in rows if r["id"] != exclude_id
        ]

    def fetch_affected_products(self, child_type: str,
                                child_id: int) -> list[dict]:
        """
        يرجع المنتجات المتأثرة.
        list of dicts: {id, name, type, qty, category_id, category_name, cost}
        """
        from db.costing.operations_repo import fetch_products_using_child
        from models.costing import calc_cost

        rows = fetch_products_using_child(self.conn, child_type, child_id)

        return [
            {
                "id":            r["parent_id"],
                "name":          r["name"],
                "type":          r["type"],
                "qty":           r["qty"],
                "category_id":   r["category_id"],
                "category_name": r["category_name"] or "—",
                "cost":          calc_cost(self.conn, r["parent_id"]),
            }
            for r in rows
        ]