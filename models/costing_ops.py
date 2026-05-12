"""
models/costing_ops.py
======================
تكلفة عمليات العمالة والتشغيل.
"""

from db.operations_repo  import fetch_labor_op, fetch_machine_op
from models.costing_base import calc_worker_hourly_rate


def calc_labor_op_cost(conn, op_id: int) -> float:
    """تكلفة عملية عمالة واحدة بالجنيه."""
    op = fetch_labor_op(conn, op_id)
    if not op:
        return 0.0
    return (op["minutes"] / 60.0) * calc_worker_hourly_rate(conn)


def calc_machine_op_cost(conn, op_id: int) -> float:
    """تكلفة عملية تشغيل واحدة بالجنيه."""
    op = fetch_machine_op(conn, op_id)
    if not op:
        return 0.0
    if op["mode"] == "time":
        return (op["value"] / 60.0) * op["rate_per_hour"]
    return op["value"] * op["rate_per_unit"]