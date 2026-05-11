"""
models/costing.py  — مع دعم waste_pct (نسبة الهادر)
=================
المعادلة:
  الكمية الفعلية = qty × (1 + waste_pct / 100)
  مثال: qty=10م، waste_pct=10% → الفعلي = 10 × 1.10 = 11م
"""

from db.items_repo      import fetch_item, fetch_bom
from db.operations_repo import fetch_labor_op, fetch_machine_op
from db.settings_repo   import get_setting


# ══════════════════════════════════════════════════════════
# أجر العامل بالساعة
# ══════════════════════════════════════════════════════════

def calc_worker_hourly_rate(conn) -> float:
    salary   = get_setting(conn, "monthly_salary",    3000.0)
    w_days   = get_setting(conn, "working_days",        25.0)
    h_days   = get_setting(conn, "holiday_days",         4.0)
    h_per_d  = get_setting(conn, "working_hours_day",    8.0)
    overhead = get_setting(conn, "overhead_factor",      1.10)
    net_hours = max(w_days - h_days, 1) * max(h_per_d, 1)
    return (salary / net_hours) * overhead if net_hours else 0.0


# ══════════════════════════════════════════════════════════
# تكلفة عملية واحدة
# ══════════════════════════════════════════════════════════

def calc_labor_op_cost(conn, op_id: int) -> float:
    op = fetch_labor_op(conn, op_id)
    if not op:
        return 0.0
    return (op["minutes"] / 60.0) * calc_worker_hourly_rate(conn)


def calc_machine_op_cost(conn, op_id: int) -> float:
    op = fetch_machine_op(conn, op_id)
    if not op:
        return 0.0
    if op["mode"] == "time":
        return (op["value"] / 60.0) * op["rate_per_hour"]
    return op["value"] * op["rate_per_unit"]


# ══════════════════════════════════════════════════════════
# سعر وحدة الخامة
# ══════════════════════════════════════════════════════════

def raw_unit_price(item_row) -> float:
    """
    يحسب سعر الوحدة الواحدة من الخامة.
    لو total_qty محددة وأكبر من صفر:
        unit_price = price / total_qty
    غير كده:
        unit_price = price
    """
    price     = float(item_row["price"])
    total_qty = item_row["total_qty"]
    if total_qty and float(total_qty) > 0:
        return price / float(total_qty)
    return price


# ══════════════════════════════════════════════════════════
# حساب الكمية الفعلية مع الهادر
# ══════════════════════════════════════════════════════════

def effective_qty(qty: float, waste_pct: float) -> float:
    """
    الكمية الفعلية = qty × (1 + waste_pct / 100)
    مثال: qty=10، waste_pct=10 → 10 × 1.10 = 11
    """
    if waste_pct and waste_pct > 0:
        return qty * (1.0 + waste_pct / 100.0)
    return qty


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

        # الكمية الفعلية بعد الهادر
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