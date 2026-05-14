"""
models/costing.py  — مع دعم waste_pct و variant_id
=================
Facade يُعيد تصدير الدوال الأساسية ويضيف calc_cost و calc_cost_breakdown.
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


def _get_variant_id(row) -> int | None:
    """يجيب variant_id من صف BOM بأمان."""
    try:
        return row["variant_id"]
    except (IndexError, KeyError):
        return None


def _raw_cost_with_variant(conn, item_row, variant_id: int | None) -> float:
    """
    تكلفة وحدة الخامة مع مراعاة الـ variant.
    الأولوية:
      1. variant محدد → سعر الخامة ÷ pieces الخاصة بالـ variant
      2. total_qty محددة → سعر ÷ total_qty  (السلوك الحالي)
      3. غير كده → السعر مباشرة
    """
    if variant_id is not None:
        var_row = conn.execute(
            "SELECT pieces FROM raw_variants WHERE id=?", (variant_id,)
        ).fetchone()
        if var_row and float(var_row["pieces"]) > 0:
            return float(item_row["price"]) / float(var_row["pieces"])
    return raw_unit_price(item_row)


# ══════════════════════════════════════════════════════════
# التكلفة الكاملة (متكررة عبر BOM)
# ══════════════════════════════════════════════════════════
def _fetch_bom_default(conn, item_id: int) -> list:
    """يجيب BOM من الـ default scenario مع machine_op_row_id."""
    try:
        sc = conn.execute(
            "SELECT id FROM bom_scenarios WHERE item_id=? AND is_default=1 LIMIT 1",
            (item_id,)
        ).fetchone()
        if not sc:
            sc = conn.execute(
                "SELECT id FROM bom_scenarios WHERE item_id=? ORDER BY id LIMIT 1",
                (item_id,)
            ).fetchone()
        if sc:
            rows = conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct,0) as waste_pct, "
                "variant_id, machine_op_row_id "
                "FROM bom WHERE scenario_id=? ORDER BY id",
                (sc["id"],)
            ).fetchall()
            if rows:
                return rows
    except Exception:
        pass
    return fetch_bom(conn, item_id)

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
    for row in _fetch_bom_default(conn, item_id):
        child_type = row["child_type"]
        child_id   = row["child_id"]
        qty        = row["qty"]
        waste_pct  = row["waste_pct"] if "waste_pct" in row.keys() else 0.0
        variant_id = _get_variant_id(row)
        eff_qty    = effective_qty(qty, waste_pct)

        # machine_op_row_id للحساب على صف محدد
        try:
            machine_op_row_id = row["machine_op_row_id"]
        except (IndexError, KeyError):
            machine_op_row_id = None

        if child_type == "raw":
            child = fetch_item(conn, child_id)
            unit_cost = _raw_cost_with_variant(conn, child, variant_id) if child else 0.0
        elif child_type == "semi":
            unit_cost = calc_cost(conn, child_id, set(_visited))
        elif child_type == "labor_op":
            unit_cost = calc_labor_op_cost(conn, child_id)
        elif child_type == "machine_op":
            unit_cost = calc_machine_op_cost(conn, child_id, row_id=machine_op_row_id)
        else:
            unit_cost = 0.0

        total += unit_cost * eff_qty

    return total

def _fetch_bom_default(conn, item_id: int) -> list:
    """
    يجيب BOM من الـ default scenario.
    Fallback: لو مفيش scenarios → يرجع للـ fetch_bom القديم.
    """
    try:
        # حاول تجيب الـ default scenario
        sc = conn.execute(
            "SELECT id FROM bom_scenarios WHERE item_id=? AND is_default=1 LIMIT 1",
            (item_id,)
        ).fetchone()
        if not sc:
            sc = conn.execute(
                "SELECT id FROM bom_scenarios WHERE item_id=? ORDER BY id LIMIT 1",
                (item_id,)
            ).fetchone()
        if sc:
            rows = conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct,0) as waste_pct, "
                "variant_id, machine_op_row_id "
                "FROM bom WHERE scenario_id=? ORDER BY id",
                (sc["id"],)
            ).fetchall()
            if rows:
                return rows
    except Exception:
        pass
    # Fallback: السلوك القديم
    return fetch_bom(conn, item_id)

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

    # ── جلب BOM من الـ default scenario ──
    bom_rows = _fetch_bom_default(conn, item_id)

    for row in bom_rows:
        child_type = row["child_type"]
        child_id   = row["child_id"]
        qty        = row["qty"]
        waste_pct  = row["waste_pct"] if "waste_pct" in row.keys() else 0.0
        variant_id = _get_variant_id(row)
        eff_qty    = effective_qty(qty, waste_pct)

        if child_type == "raw":
            child = fetch_item(conn, child_id)
            unit_cost = _raw_cost_with_variant(conn, child, variant_id) if child else 0.0
            materials += unit_cost * eff_qty
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