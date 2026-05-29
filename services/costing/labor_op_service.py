"""
services/costing/labor_op_service.py
======================================
LaborOpService — منطق عمليات العمالة بدون PyQt.

يُغلّف كل استدعاءات db/costing/operations_repo الخاصة بالعمالة.
"""

from __future__ import annotations
from dataclasses import dataclass


# ── Data classes ─────────────────────────────────────────────

@dataclass
class LaborOpResult:
    id: int
    name: str
    minutes: float
    category_id: int | None
    category_name: str | None

    @classmethod
    def from_row(cls, row) -> "LaborOpResult":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            id=d["id"],
            name=d["name"],
            minutes=float(d.get("minutes", 0)),
            category_id=d.get("category_id"),
            category_name=d.get("category_name"),
        )


# ── Service ──────────────────────────────────────────────────

class LaborOpService:
    """
    الاستخدام:
        svc = LaborOpService(conn)
        ops = svc.list()
        op  = svc.get(op_id)
        new_id = svc.add("خياطة", minutes=15.0, category_id=2)
        svc.update(op_id, "خياطة", minutes=20.0)
        svc.delete(op_id)
        cost = svc.calc_cost(op_id)
    """

    def __init__(self, conn):
        self.conn = conn

    # ── قراءة ────────────────────────────────────────────────

    def list(self) -> list[LaborOpResult]:
        from db.costing.operations_repo import fetch_all_labor_ops
        return [LaborOpResult.from_row(r) for r in fetch_all_labor_ops(self.conn)]

    def get(self, op_id: int) -> LaborOpResult | None:
        from db.costing.operations_repo import fetch_labor_op
        row = fetch_labor_op(self.conn, op_id)
        return LaborOpResult.from_row(row) if row else None

    # ── كتابة ────────────────────────────────────────────────

    def add(self, name: str, minutes: float,
            category_id: int | None = None) -> int:
        from db.costing.operations_repo import insert_labor_op
        return insert_labor_op(self.conn, name, minutes,
                               category_id=category_id)

    def update(self, op_id: int, name: str, minutes: float,
               category_id: int | None = None) -> None:
        from db.costing.operations_repo import update_labor_op
        update_labor_op(self.conn, op_id, name, minutes,
                        category_id=category_id)

    def delete(self, op_id: int) -> None:
        from db.costing.operations_repo import delete_labor_op
        delete_labor_op(self.conn, op_id)

    # ── حساب ─────────────────────────────────────────────────

    def calc_cost(self, op_id: int) -> float:
        from models.costing_ops import calc_labor_op_cost
        return calc_labor_op_cost(self.conn, op_id)