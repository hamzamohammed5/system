"""
models/costing.py  — مع دعم waste_pct (نسبة الهادر)
=================
Facade يُعيد تصدير الدوال الأساسية ويضيف calc_cost و calc_cost_breakdown.

الملفات الفعلية:
  costing_base.py → calc_worker_hourly_rate, raw_unit_price, effective_qty
  costing_ops.py  → calc_labor_op_cost, calc_machine_op_cost
"""

from models.costing_base import (
    calc_worker_hourly_rate,
    raw_unit_price,
    effective_qty,
)
from models.costing_ops import (
    calc_labor_op_cost,
    calc_machine_op_cost,
)
from db.items_repo import fetch_item, fetch_bom


# ══════════════════════════════════════════════════════════
# التكلفة الكاملة (متكررة عبر BOM)
# ══════════════════════════════════════════════════════════

def calc_cost(conn, item_id: int, _visited: set = None) -> float:
    if _visited is None:
        _visited = set()
    if item_id in _visited:
        return 0.0
    _visited.add(item_id)

    item = fetch_item(conn, item_id)
    if not item:
        return 0.0

    if item["type"] == "raw":
        return raw_unit_price(item)

    total = 0.0
    for row in fetch_bom(conn, item_id):
        child_type = row["child_type"]
        child_id   = row["child_id"]
        qty        = row["qty"]
        waste_pct  = row["waste_pct"] if "waste_pct" in row.keys() else 0.0

        eff_qty = effective_qty(qty, waste_pct)

        if child_type == "raw":
            child = fetch_item(conn, child_id)
            unit_cost = raw_unit_price(child) if child else 0.0
        elif child_type == "semi":
            unit_cost = calc_cost(conn, child_id, set(_visited))
        elif child_type == "labor_op":
            unit_cost = calc_labor_op_cost(conn, child_id)
        elif child_type == "machine_op":
            unit_cost = calc_machine_op_cost(conn, child_id)
        else:
            unit_cost = 0.0

        total += unit_cost * eff_qty

    return total


# ══════════════════════════════════════════════════════════
# تفصيل التكلفة للعرض
# ══════════════════════════════════════════════════════════

def calc_cost_breakdown(conn, item_id: int) -> dict:
    item = fetch_item(conn, item_id)
    if not item:
        return {"materials": 0, "labor": 0, "machine": 0, "total": 0}

    if item["type"] == "raw":
        p = raw_unit_price(item)
        return {"materials": p, "labor": 0, "machine": 0, "total": p}

    materials = labor = machine = 0.0

    for row in fetch_bom(conn, item_id):
        child_type = row["child_type"]
        child_id   = row["child_id"]
        qty        = row["qty"]
        waste_pct  = row["waste_pct"] if "waste_pct" in row.keys() else 0.0
        eff_qty    = effective_qty(qty, waste_pct)

        if child_type == "raw":
            child = fetch_item(conn, child_id)
            materials += (raw_unit_price(child) if child else 0.0) * eff_qty
        elif child_type == "semi":
            materials += calc_cost(conn, child_id) * eff_qty
        elif child_type == "labor_op":
            labor += calc_labor_op_cost(conn, child_id) * eff_qty
        elif child_type == "machine_op":
            machine += calc_machine_op_cost(conn, child_id) * eff_qty

    return {
        "materials": materials,
        "labor":     labor,
        "machine":   machine,
        "total":     materials + labor + machine,
    }


__all__ = [
    "calc_worker_hourly_rate",
    "raw_unit_price",
    "effective_qty",
    "calc_labor_op_cost",
    "calc_machine_op_cost",
    "calc_cost",
    "calc_cost_breakdown",
]