"""
services/costing/machine_op_rows_service.py
=============================================
MachineOpRowsService — يغلّف كل عمليات machine_op_rows_repo.

يُستخدم من:
  - ui/tabs/costing/shared/machine_op_rows_editor.py
  - ui/tabs/costing/machine/machine_op_form.py  (calc_op_total_cost)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List


# ──────────────────────────────────────────────────────────
# نماذج البيانات
# ──────────────────────────────────────────────────────────

@dataclass
class OpRowResult:
    id: int
    op_id: int
    label: str
    value: float
    count: float
    sort_order: int = 0

    @classmethod
    def from_row(cls, row) -> "OpRowResult":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            id=d["id"],
            op_id=d["op_id"],
            label=d.get("label") or "",
            value=float(d["value"]),
            count=float(d["count"]),
            sort_order=int(d.get("sort_order") or 0),
        )


# ──────────────────────────────────────────────────────────
# MachineOpRowsService
# ──────────────────────────────────────────────────────────

class MachineOpRowsService:
    """
    Service لإدارة صفوف عملية التشغيل.

    الاستخدام:
        svc = MachineOpRowsService(conn)
        rows = svc.list(op_id)
        total = svc.calc_total_cost(op_id)
    """

    def __init__(self, conn):
        self.conn = conn

    # ── قراءة ─────────────────────────────────────────────

    def list(self, op_id: int) -> List[OpRowResult]:
        """يرجع كل صفوف العملية مرتبةً بـ sort_order."""
        from db.costing.machine_op_rows_repo import fetch_op_rows
        return [OpRowResult.from_row(r) for r in fetch_op_rows(self.conn, op_id)]

    def get(self, row_id: int) -> Optional[OpRowResult]:
        """يرجع صف واحد بالـ id."""
        from db.costing.machine_op_rows_repo import fetch_op_row
        row = fetch_op_row(self.conn, row_id)
        return OpRowResult.from_row(row) if row else None

    # ── كتابة ─────────────────────────────────────────────

    def add(self, op_id: int, label: str = "", value: float = 0.0,
            count: float = 1.0, sort_order: int = 0) -> int:
        """
        يضيف صف جديد للعملية.
        يرجع id الصف الجديد.
        """
        from db.costing.machine_op_rows_repo import insert_op_row
        return insert_op_row(
            self.conn, op_id,
            label=label, value=value,
            count=count, sort_order=sort_order,
        )

    def update(self, row_id: int, label: str, value: float,
               count: float, sort_order: int = 0) -> None:
        """يحدّث صف موجود."""
        from db.costing.machine_op_rows_repo import update_op_row
        update_op_row(self.conn, row_id, label, value, count, sort_order)

    def delete(self, row_id: int, op_id: int) -> bool:
        """
        يحذف صف.
        يرجع False ويرفض الحذف لو كان آخر صف في العملية.
        """
        existing = self.list(op_id)
        if len(existing) <= 1:
            return False
        from db.costing.machine_op_rows_repo import delete_op_row
        delete_op_row(self.conn, row_id)
        return True

    def replace(self, op_id: int, rows: list) -> None:
        """
        يستبدل كل صفوف العملية دفعة واحدة.
        rows: [(label, value, count), ...]
        """
        from db.costing.machine_op_rows_repo import replace_op_rows
        replace_op_rows(self.conn, op_id, rows)

    # ── حساب ──────────────────────────────────────────────

    def calc_row_cost(self, row_id: int) -> float:
        """
        يحسب تكلفة صف واحد.
        mode="time": (value/60) × rate_per_hour
        mode="unit": value × rate_per_unit
        """
        from db.costing.machine_op_rows_repo import calc_op_row_cost
        return calc_op_row_cost(self.conn, row_id)

    def calc_total_cost(self, op_id: int) -> float:
        """يحسب إجمالي تكلفة العملية (مجموع كل الصفوف)."""
        from db.costing.machine_op_rows_repo import calc_op_total_cost
        return calc_op_total_cost(self.conn, op_id)