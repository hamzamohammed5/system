"""
models/costing_ops.py
======================
تكلفة عمليات العمالة والتشغيل.

عمليات التشغيل: التكلفة تُحسب من صفوف machine_op_rows (مجموع الصفوف).
لو مفيش صفوف → fallback على value في machine_ops (السلوك القديم).
"""

from db.costing.operations_repo  import fetch_labor_op, fetch_machine_op
from models.costing_base import calc_worker_hourly_rate


def calc_labor_op_cost(conn, op_id: int) -> float:
    """تكلفة عملية عمالة واحدة بالجنيه."""
    op = fetch_labor_op(conn, op_id)
    if not op:
        return 0.0
    return (op["minutes"] / 60.0) * calc_worker_hourly_rate(conn)


def calc_machine_op_cost(conn, op_id: int, row_id: int = None) -> float:
    """
    تكلفة عملية تشغيل.
    لو row_id محدد → تكلفة ذلك الصف فقط.
    لو مش محدد → مجموع كل الصفوف (السلوك القديم).
    """
    op = fetch_machine_op(conn, op_id)
    if not op:
        return 0.0

    try:
        from db.costing.machine_op_rows_repo import calc_op_total_cost, calc_op_row_cost, fetch_op_rows
        rows = fetch_op_rows(conn, op_id)
        if rows:
            if row_id is not None:
                # صف محدد فقط
                return calc_op_row_cost(conn, row_id)
            else:
                # كل الصفوف
                return calc_op_total_cost(conn, op_id)
    except Exception:
        pass

    # Fallback
    if op["mode"] == "time":
        return (op["value"] / 60.0) * op["rate_per_hour"]
    return op["value"] * op["rate_per_unit"]
