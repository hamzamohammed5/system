"""
models/costing.py  — مع دعم كامل للعناصر المشتركة (shared items)
=================
Facade يُعيد تصدير الدوال الأساسية ويضيف calc_cost و calc_cost_breakdown.

العناصر المشتركة:
  - IDs بالشكل "shared:{n}" (string)
  - بياناتها في companies.db مباشرة
  - is_shared_id() تتحقق من الـ string prefix
  - الحسابات تقرأ من companies.db دون نسخ محلية
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


# ══════════════════════════════════════════════════════════
# حساب تكلفة العناصر المشتركة من companies.db
# ══════════════════════════════════════════════════════════

def _get_shared_data(shared_item_id: int) -> dict:
    """يجيب بيانات عنصر مشترك من companies.db."""
    try:
        import json
        from db.companies.companies_schema import get_central_connection
        central = get_central_connection()
        row = central.execute(
            "SELECT shared_type, data FROM shared_items WHERE id=?",
            (shared_item_id,)
        ).fetchone()
        central.close()
        if not row:
            return {}
        data = json.loads(row["data"]) if row["data"] else {}
        data["_shared_type"] = row["shared_type"]
        return data
    except Exception:
        return {}


def _shared_raw_unit_price(shared_item_id: int) -> float:
    """يحسب سعر وحدة الخامة المشتركة من companies.db."""
    data = _get_shared_data(shared_item_id)
    if not data:
        return 0.0
    price = float(data.get("price", 0.0))
    total_qty = data.get("total_qty")
    if total_qty and float(total_qty) > 0:
        return price / float(total_qty)
    return price


def _shared_labor_op_cost(conn, shared_item_id: int) -> float:
    """يحسب تكلفة عملية عمالة مشتركة — المعدل من erp.db الشركة."""
    data = _get_shared_data(shared_item_id)
    if not data:
        return 0.0
    minutes = float(data.get("minutes", 0.0))
    rate = calc_worker_hourly_rate(conn)
    return (minutes / 60.0) * rate


def _shared_machine_op_cost(shared_item_id: int) -> float:
    """يحسب تكلفة عملية تشغيل مشتركة."""
    data = _get_shared_data(shared_item_id)
    if not data:
        return 0.0
    mode = data.get("mode", "time")
    value = float(data.get("value", 0.0))
    if mode == "time":
        return (value / 60.0) * float(data.get("rate_per_hour", 0.0))
    else:
        return value * float(data.get("rate_per_unit", 0.0))


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
# حساب تكلفة child_id (محلي أو مشترك)
# ══════════════════════════════════════════════════════════

def _calc_child_cost(conn, child_type: str, child_id,
                     variant_id=None, machine_op_row_id=None,
                     _visited: set = None) -> float:
    """
    يحسب تكلفة وحدة من child_id سواء كان محلي أو مشترك.
    child_id يمكن أن يكون int (محلي) أو str "shared:{n}" (مشترك).
    """
    if is_shared_id(child_id):
        sid = extract_shared_id(child_id)
        if sid is None:
            return 0.0
        if child_type == "raw":
            return _shared_raw_unit_price(sid)
        elif child_type == "labor_op":
            return _shared_labor_op_cost(conn, sid)
        elif child_type == "machine_op":
            return _shared_machine_op_cost(sid)
        elif child_type == "semi":
            # نصف مصنع مشترك — نحاول نحسب تكلفته
            return _shared_raw_unit_price(sid)
        return 0.0

    # عنصر محلي
    if child_type == "raw":
        child = fetch_item(conn, child_id)
        if not child:
            return 0.0
        return _raw_cost_with_variant(conn, child, variant_id)

    elif child_type == "semi":
        return calc_cost(conn, child_id, set(_visited) if _visited else None)

    elif child_type == "labor_op":
        return calc_labor_op_cost(conn, child_id)

    elif child_type == "machine_op":
        return calc_machine_op_cost(conn, child_id, row_id=machine_op_row_id)

    return 0.0


# ══════════════════════════════════════════════════════════
# التكلفة الكاملة (متكررة عبر BOM)
# ══════════════════════════════════════════════════════════

def calc_cost(conn, item_id, _visited: set = None) -> float:
    """
    يحسب التكلفة الكاملة لمنتج أو خامة.
    يدعم:
      - العناصر المحلية (int IDs)
      - العناصر المشتركة (str "shared:{n}")
      - BOM متعدد السيناريوهات (يستخدم الـ default)
    """
    if _visited is None:
        _visited = set()

    # دعم shared items مباشرة
    if is_shared_id(item_id):
        sid = extract_shared_id(item_id)
        return _shared_raw_unit_price(sid) if sid else 0.0

    # تجنب الحلقات اللانهائية
    item_id_int = int(item_id) if not is_shared_id(item_id) else item_id
    if item_id_int in _visited:
        return 0.0
    _visited.add(item_id_int)

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

        unit_cost = _calc_child_cost(
            conn, child_type, child_id,
            variant_id=variant_id,
            machine_op_row_id=machine_op_row_id,
            _visited=_visited,
        )
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

        unit_cost = _calc_child_cost(
            conn, child_type, child_id,
            variant_id=variant_id,
            machine_op_row_id=machine_op_row_id,
        )

        if child_type in ("raw", "semi"):
            materials += unit_cost * eff_qty
        elif child_type == "labor_op":
            labor += unit_cost * eff_qty
        elif child_type == "machine_op":
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