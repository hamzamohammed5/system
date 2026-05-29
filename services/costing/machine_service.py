"""
services/costing/machine_service.py
=====================================
MachineService + MachineOpService — منطق الماكينات وعمليات التشغيل بدون PyQt.
"""

from __future__ import annotations
from dataclasses import dataclass


# ── Data classes ─────────────────────────────────────────────

@dataclass
class MachineResult:
    id: int
    name: str
    rate_per_hour: float
    rate_per_unit: float
    category_id: int | None
    category_name: str | None

    @classmethod
    def from_row(cls, row) -> "MachineResult":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            id=d["id"],
            name=d["name"],
            rate_per_hour=float(d.get("rate_per_hour", 0)),
            rate_per_unit=float(d.get("rate_per_unit", 0)),
            category_id=d.get("category_id"),
            category_name=d.get("category_name"),
        )

    @property
    def mode(self) -> str:
        """يرجع "time" لو rate_per_hour > 0، وإلا "unit"."""
        return "time" if self.rate_per_hour > 0 else "unit"


@dataclass
class MachineOpResult:
    id: int
    name: str
    machine_id: int | None
    machine_name: str | None
    mode: str            # "time" | "unit"
    value: float
    category_id: int | None
    category_name: str | None

    @classmethod
    def from_row(cls, row) -> "MachineOpResult":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            id=d["id"],
            name=d["name"],
            machine_id=d.get("machine_id"),
            machine_name=d.get("machine_name"),
            mode=d.get("mode", "time"),
            value=float(d.get("value", 0)),
            category_id=d.get("category_id"),
            category_name=d.get("category_name"),
        )


# ── MachineService ───────────────────────────────────────────

class MachineService:
    """
    الاستخدام:
        svc = MachineService(conn)
        machines = svc.list()
        m = svc.get(machine_id)
        new_id = svc.add("ماكينة خياطة", rate_per_hour=50.0, rate_per_unit=0.0)
        svc.update(machine_id, ...)
        svc.delete(machine_id)
    """

    def __init__(self, conn):
        self.conn = conn

    def list(self) -> list[MachineResult]:
        from db.costing.operations_repo import fetch_all_machines
        return [MachineResult.from_row(r) for r in fetch_all_machines(self.conn)]

    def get(self, machine_id: int) -> MachineResult | None:
        from db.costing.operations_repo import fetch_machine
        row = fetch_machine(self.conn, machine_id)
        return MachineResult.from_row(row) if row else None

    def add(self, name: str, rate_per_hour: float, rate_per_unit: float,
            category_id: int | None = None) -> int:
        from db.costing.operations_repo import insert_machine
        return insert_machine(self.conn, name, rate_per_hour, rate_per_unit,
                              category_id=category_id)

    def update(self, machine_id: int, name: str,
               rate_per_hour: float, rate_per_unit: float,
               category_id: int | None = None) -> None:
        from db.costing.operations_repo import update_machine
        update_machine(self.conn, machine_id, name, rate_per_hour, rate_per_unit,
                       category_id=category_id)

    def delete(self, machine_id: int) -> None:
        from db.costing.operations_repo import delete_machine
        delete_machine(self.conn, machine_id)


# ── MachineOpService ─────────────────────────────────────────

class MachineOpService:
    """
    الاستخدام:
        svc = MachineOpService(conn)
        ops = svc.list()
        op  = svc.get(op_id)
        new_id = svc.add(machine_id, "خياطة غرزة", mode="time", value=0.0)
        svc.update(op_id, ...)
        svc.delete(op_id)
        cost = svc.calc_cost(op_id, row_id=None)
    """

    def __init__(self, conn):
        self.conn = conn

    def list(self) -> list[MachineOpResult]:
        from db.costing.operations_repo import fetch_all_machine_ops
        return [MachineOpResult.from_row(r) for r in fetch_all_machine_ops(self.conn)]

    def get(self, op_id: int) -> MachineOpResult | None:
        from db.costing.operations_repo import fetch_machine_op
        row = fetch_machine_op(self.conn, op_id)
        return MachineOpResult.from_row(row) if row else None

    def add(self, machine_id: int, name: str, mode: str, value: float,
            category_id: int | None = None) -> int:
        from db.costing.operations_repo import insert_machine_op
        return insert_machine_op(self.conn, machine_id, name, mode, value,
                                 category_id=category_id)

    def update(self, op_id: int, machine_id: int, name: str, mode: str,
               value: float, category_id: int | None = None) -> None:
        from db.costing.operations_repo import update_machine_op
        update_machine_op(self.conn, op_id, machine_id, name, mode, value,
                          category_id=category_id)

    def delete(self, op_id: int) -> None:
        from db.costing.operations_repo import delete_machine_op
        delete_machine_op(self.conn, op_id)

    def calc_cost(self, op_id: int, row_id: int | None = None) -> float:
        from models.costing_ops import calc_machine_op_cost
        return calc_machine_op_cost(self.conn, op_id, row_id=row_id)