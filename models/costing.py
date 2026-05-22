"""
models/costing.py  — مع دعم waste_pct و variant_id و machine_op_row_id والعناصر المشتركة
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
from db.shared.items_repo import fetch_item, fetch_bom, is_shared_id, extract_shared_id


def _get_variant_id(row) -> int | None:
    try:
        return row["variant_id"]
    except (IndexError, KeyError):
        return None


def _get_machine_op_row_id(row) -> int | None:
    try:
        return row["machine_op_row_id"]
    except (IndexError, KeyError):
        return None


def _raw_cost_with_variant(conn, item_row, variant_id: int | None) -> float:
    if variant_id is not None:
        var_row = conn.execute(
            "SELECT pieces FROM raw_variants WHERE id=?", (variant_id,)
        ).fetchone()
        if var_row and float(var_row["pieces"]) > 0:
            return float(item_row["price"]) / float(var_row["pieces"])
    return raw_unit_price(item_row)


def _shared_raw_unit_price(shared_item_id: int) -> float:
    """يحسب سعر وحدة الخامة المشتركة من companies.db."""
    try:
        import json
        from db.companies.companies_schema import get_central_connection
        central = get_central_connection()
        row = central.execute(
            "SELECT data FROM shared_items WHERE id=?", (shared_item_id,)
        ).fetchone()
        central.close()
        if not row:
            return 0.0
        data = json.loads(row["data"]) if row["data"] else {}
        price     = float(data.get("price", 0.0))
        total_qty = data.get("total_qty")
        if total_qty and float(total_qty) > 0:
            return price / float(total_qty)
        return price
    except Exception:
        return 0.0


def _shared_labor_op_cost(conn, shared_item_id: int) -> float:
    """يحسب تكلفة عملية عمالة مشتركة."""
    try:
        import json
        from db.companies.companies_schema import get_central_connection
        central = get_central_connection()
        row = central.execute(
            "SELECT data FROM shared_items WHERE id=? AND shared_type='labor_op'",
            (shared_item_id,)
        ).fetchone()
        central.close()
        if not row:
            return 0.0
        data = json.loads(row["data"]) if row["data"] else {}
        minutes = float(data.get("minutes", 0.0))
        return (minutes / 60.0) * calc_worker_hourly_rate(conn)
    except Exception:
        return 0.0


def _shared_machine_op_cost(shared_item_id: int) -> float:
    """يحسب تكلفة عملية تشغيل مشتركة."""
    try:
        import json
        from db.companies.companies_schema import get_central_connection
        central = get_central_connection()
        row = central.execute(
            "SELECT data FROM shared_items WHERE id=? AND shared_type='machine_op'",
            (shared_item_id,)
        ).fetchone()
        central.close()
        if not row:
            return 0.0
        data = json.loads(row["data"]) if row["data"] else {}
        mode  = data.get("mode", "time")
        value = float(data.get("value", 0.0))
        if mode == "time":
            return (value / 60.0) * float(data.get("rate_per_hour", 0.0))
        else:
            return value * float(data.get("rate_per_unit", 0.0))
    except Exception:
        return 0.0


# ══════════════════════════════════════════════════════════
# جلب BOM من الـ default scenario مع machine_op_row_id
# ══════════════════════════════════════════════════════════

def _fetch_bom_default(conn, item_id: int) -> list:
    """
    يجيب BOM من الـ default scenario مع كل الأعمدة.
    Fallback: لو مفيش scenarios → يرجع للـ fetch_bom القديم مع NULL لـ machine_op_row_id.
    """
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
            has_row_id  = _col_exists(conn, "bom", "machine_op_row_id")
            has_variant = _col_exists(conn, "bom", "variant_id")

            if has_row_id and has_variant:
                rows = conn.execute(
                    "SELECT child_type, child_id, qty, "
                    "COALESCE(waste_pct,0) as waste_pct, "
                    "variant_id, machine_op_row_id "
                    "FROM bom WHERE scenario_id=? ORDER BY id",
                    (sc["id"],)
                ).fetchall()
            elif has_variant:
                rows = conn.execute(
                    "SELECT child_type, child_id, qty, "
                    "COALESCE(waste_pct,0) as waste_pct, "
                    "variant_id, NULL as machine_op_row_id "
                    "FROM bom WHERE scenario_id=? ORDER BY id",
                    (sc["id"],)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT child_type, child_id, qty, "
                    "COALESCE(waste_pct,0) as waste_pct, "
                    "NULL as variant_id, NULL as machine_op_row_id "
                    "FROM bom WHERE scenario_id=? ORDER BY id",
                    (sc["id"],)
                ).fetchall()

            if rows:
                return rows
    except Exception:
        pass

    return _fetch_bom_fallback(conn, item_id)


def _fetch_bom_fallback(conn, item_id: int) -> list:
    try:
        has_row_id  = _col_exists(conn, "bom", "machine_op_row_id")
        has_variant = _col_exists(conn, "bom", "variant_id")

        if has_row_id and has_variant:
            return conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct,0) as waste_pct, "
                "variant_id, machine_op_row_id "
                "FROM bom WHERE parent_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
        elif has_variant:
            return conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct,0) as waste_pct, "
                "variant_id, NULL as machine_op_row_id "
                "FROM bom WHERE parent_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
        else:
            return conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct,0) as waste_pct, "
                "NULL as variant_id, NULL as machine_op_row_id "
                "FROM bom WHERE parent_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
    except Exception:
        return fetch_bom(conn, item_id)


def _col_exists(conn, table: str, col: str) -> bool:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == col for r in rows)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════
# التكلفة الكاملة (متكررة عبر BOM)
# ══════════════════════════════════════════════════════════

def calc_cost(conn, item_id: int, _visited: set = None) -> float:
    if _visited is None:
        _visited = set()

    # دعم shared items
    if is_shared_id(item_id):
        sid = extract_shared_id(item_id)
        return _shared_raw_unit_price(sid) if sid else 0.0

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
        child_type        = row["child_type"]
        child_id          = row["child_id"]
        qty               = row["qty"]
        waste_pct         = row["waste_pct"] if "waste_pct" in row.keys() else 0.0
        variant_id        = _get_variant_id(row)
        machine_op_row_id = _get_machine_op_row_id(row)
        eff_qty           = effective_qty(qty, waste_pct)

        if child_type == "raw":
            # دعم shared raw
            if is_shared_id(child_id):
                sid = extract_shared_id(child_id)
                unit_cost = _shared_raw_unit_price(sid) if sid else 0.0
            else:
                child = fetch_item(conn, child_id)
                unit_cost = _raw_cost_with_variant(conn, child, variant_id) if child else 0.0
        elif child_type == "semi":
            unit_cost = calc_cost(conn, child_id, set(_visited))
        elif child_type == "labor_op":
            if is_shared_id(child_id):
                sid = extract_shared_id(child_id)
                unit_cost = _shared_labor_op_cost(conn, sid) if sid else 0.0
            else:
                unit_cost = calc_labor_op_cost(conn, child_id)
        elif child_type == "machine_op":
            if is_shared_id(child_id):
                sid = extract_shared_id(child_id)
                unit_cost = _shared_machine_op_cost(sid) if sid else 0.0
            else:
                unit_cost = calc_machine_op_cost(conn, child_id, row_id=machine_op_row_id)
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

    for row in _fetch_bom_default(conn, item_id):
        child_type        = row["child_type"]
        child_id          = row["child_id"]
        qty               = row["qty"]
        waste_pct         = row["waste_pct"] if "waste_pct" in row.keys() else 0.0
        variant_id        = _get_variant_id(row)
        machine_op_row_id = _get_machine_op_row_id(row)
        eff_qty           = effective_qty(qty, waste_pct)

        if child_type == "raw":
            if is_shared_id(child_id):
                sid = extract_shared_id(child_id)
                unit_cost = _shared_raw_unit_price(sid) if sid else 0.0
            else:
                child = fetch_item(conn, child_id)
                unit_cost = _raw_cost_with_variant(conn, child, variant_id) if child else 0.0
            materials += unit_cost * eff_qty
        elif child_type == "semi":
            materials += calc_cost(conn, child_id) * eff_qty
        elif child_type == "labor_op":
            if is_shared_id(child_id):
                sid = extract_shared_id(child_id)
                unit_cost = _shared_labor_op_cost(conn, sid) if sid else 0.0
            else:
                unit_cost = calc_labor_op_cost(conn, child_id)
            labor += unit_cost * eff_qty
        elif child_type == "machine_op":
            if is_shared_id(child_id):
                sid = extract_shared_id(child_id)
                unit_cost = _shared_machine_op_cost(sid) if sid else 0.0
            else:
                unit_cost = calc_machine_op_cost(conn, child_id, row_id=machine_op_row_id)
            machine += unit_cost * eff_qty

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