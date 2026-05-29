"""
models/costing.py  — مع دعم كامل للعناصر المشتركة (shared items)
=================
Facade يُعيد تصدير الدوال الأساسية ويضيف calc_cost و calc_cost_breakdown.

العناصر المشتركة:
  - IDs بالشكل "shared:{n}" (string)
  - بياناتها في companies.db مباشرة
  - is_shared_id() تتحقق من الـ string prefix
  - الحسابات تقرأ من companies.db دون نسخ محلية

[C-01 / E-01] إضافة calc_product_cost(conn, product_id, scenario_id=None)
  - يدعم scenario_id محدد أو يرجع للـ default
  - يرجع (total_cost, breakdown) كـ tuple
  - يُستخدم من ProductService.calculate_cost

[P-02] _get_shared_data يستخدم _get_central_conn_cached من items_repo
  بدل فتح/غلق central connection في كل استدعاء.

[P-02b] calc_cost يقبل central_conn اختياري:
  المشكلة: offers_repo.calc_offer_summary تستدعي calc_cost لكل منتج.
  كل منتج قد يحتوي خامات مشتركة تستدعي _get_shared_data.
  رغم أن _get_shared_data يستخدم _get_central_conn_cached (module cache)،
  إلا أن تمرير central_conn صريح يُمكِّن الـ caller من استخدام
  connection منفصل (مفيد في الـ unit tests والـ multi-company scenarios).

  الـ API:
    calc_cost(conn, item_id)                          → كالمعتاد
    calc_cost(conn, item_id, central_conn=my_conn)    → يستخدم my_conn للـ shared data

  الـ central_conn parameter لا يُستخدم مباشرة في calc_cost نفسها —
  بل يُمرَّر لـ _calc_child_cost التي تمرره لـ _get_shared_data عبر
  thread-local override. هذا يحافظ على الـ API الداخلي بدون تغيير.

  Implementation note:
    نستخدم _central_conn_override: dict = {} كـ thread-local store بسيط.
    لأن التطبيق single-threaded (PyQt main thread)، هذا كافٍ وآمن.
    في بيئة multi-threaded حقيقية يُستبدل بـ threading.local().
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
from db.shared.items_repo import (
    fetch_item,
    fetch_bom,
    is_shared_id,
    extract_shared_id,
    _get_central_conn_cached,   # [P-02] cached connection بدل فتح/غلق متكرر
)


# [P-02b] override store للـ central_conn الممرر من الـ caller
# single-threaded safe — كافٍ للتطبيق الحالي
_central_conn_override: dict = {"conn": None}


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
    """
    يجيب بيانات عنصر مشترك من companies.db.

    [P-02] يستخدم _get_central_conn_cached() بدل get_central_connection()
    لتجنب فتح/غلق connection في كل استدعاء.

    [P-02b] لو في _central_conn_override نشط (من calc_cost مع central_conn)،
    يستخدمه أولاً — fallback للـ cache العادي.
    """
    try:
        from db.shared.json_utils import decode_json

        # [P-02b] استخدم الـ override لو موجود
        override = _central_conn_override.get("conn")
        central  = override if override is not None else _get_central_conn_cached()

        row = central.execute(
            "SELECT shared_type, data FROM shared_items WHERE id=?",
            (shared_item_id,)
        ).fetchone()
        if not row:
            return {}
        data = decode_json(row["data"])
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
# جلب BOM — بدعم scenario_id صريح أو الـ default
# ══════════════════════════════════════════════════════════

def _col_exists(conn, table: str, col: str) -> bool:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == col for r in rows)
    except Exception:
        return False


def _fetch_bom_for_scenario_id(conn, scenario_id: int) -> list:
    """
    يجيب BOM من scenario_id صريح.
    يتعامل مع وجود/غياب أعمدة variant_id و machine_op_row_id.
    """
    has_row_id  = _col_exists(conn, "bom", "machine_op_row_id")
    has_variant = _col_exists(conn, "bom", "variant_id")

    if has_row_id and has_variant:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct, 0) AS waste_pct, "
            "variant_id, machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()
    elif has_variant:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct, 0) AS waste_pct, "
            "variant_id, NULL AS machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()
    elif has_row_id:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct, 0) AS waste_pct, "
            "NULL AS variant_id, machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()
    else:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct, 0) AS waste_pct, "
            "NULL AS variant_id, NULL AS machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()


def _fetch_bom_default(conn, item_id: int) -> list:
    """
    يجيب BOM من الـ default scenario مع كل الأعمدة.
    Fallback: لو مفيش scenarios → يرجع للـ fetch_bom القديم.
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
            rows = _fetch_bom_for_scenario_id(conn, sc["id"])
            if rows:
                return rows
    except Exception:
        pass

    return _fetch_bom_fallback(conn, item_id)


def _fetch_bom_by_scenario(conn, item_id: int,
                            scenario_id: int | None) -> list:
    """
    [C-01 / E-01] يجيب BOM بناءً على scenario_id.
    - scenario_id محدد  → يجلب BOM ذلك السيناريو مباشرة
    - scenario_id=None  → يرجع للـ default (_fetch_bom_default)
    """
    if scenario_id is not None:
        try:
            sc = conn.execute(
                "SELECT id FROM bom_scenarios WHERE id=? AND item_id=? LIMIT 1",
                (scenario_id, item_id)
            ).fetchone()
            if sc:
                rows = _fetch_bom_for_scenario_id(conn, scenario_id)
                return rows
        except Exception:
            pass
    return _fetch_bom_default(conn, item_id)


def _fetch_bom_fallback(conn, item_id: int) -> list:
    try:
        has_row_id  = _col_exists(conn, "bom", "machine_op_row_id")
        has_variant = _col_exists(conn, "bom", "variant_id")

        if has_row_id and has_variant:
            return conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct, 0) AS waste_pct, "
                "variant_id, machine_op_row_id "
                "FROM bom WHERE parent_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
        elif has_variant:
            return conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct, 0) AS waste_pct, "
                "variant_id, NULL AS machine_op_row_id "
                "FROM bom WHERE parent_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
        else:
            return conn.execute(
                "SELECT child_type, child_id, qty, "
                "COALESCE(waste_pct, 0) AS waste_pct, "
                "NULL AS variant_id, NULL AS machine_op_row_id "
                "FROM bom WHERE parent_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
    except Exception:
        return fetch_bom(conn, item_id)


# ══════════════════════════════════════════════════════════
# حساب تكلفة child_id (محلي أو مشترك)
# ══════════════════════════════════════════════════════════

def _calc_child_cost(conn, child_type: str, child_id,
                     variant_id=None, machine_op_row_id=None,
                     _visited: set = None) -> float:
    """
    يحسب تكلفة وحدة من child_id سواء كان محلي أو مشترك.
    child_id يمكن أن يكون int (محلي) أو str "shared:{n}" (مشترك).

    يستخدم _central_conn_override تلقائياً لو كان نشطاً.
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
# calc_cost — التكلفة الكاملة (default scenario)
# ══════════════════════════════════════════════════════════

def calc_cost(conn, item_id, _visited: set = None,
              central_conn=None) -> float:
    """
    يحسب التكلفة الكاملة لمنتج أو خامة باستخدام الـ default scenario.

    Parameters:
        conn         : erp connection للشركة النشطة
        item_id      : ID المنتج (int محلي أو str "shared:{n}")
        _visited     : internal — لمنع الحلقات اللانهائية
        central_conn : [P-02b] connection اختياري لـ companies.db.
                       None = يستخدم _get_central_conn_cached() (الافتراضي).
                       قيمة = يُمرَّر هذا الـ connection لكل استدعاءات
                       _get_shared_data في هذه العملية الحسابية.
                       مفيد في:
                         - offers_repo: connection واحد لكل العرض
                         - unit tests: connection مُتحكَّم فيه
                         - multi-company: connection صريح للشركة الصح

    يدعم:
      - العناصر المحلية (int IDs)
      - العناصر المشتركة (str "shared:{n}")
      - BOM متعدد السيناريوهات (يستخدم الـ default)

    للحساب بسيناريو محدد استخدم calc_product_cost.
    """
    # [P-02b] ضبط الـ override للـ central connection
    _prev_override = _central_conn_override.get("conn")
    if central_conn is not None:
        _central_conn_override["conn"] = central_conn

    try:
        return _calc_cost_impl(conn, item_id, _visited)
    finally:
        # استعادة الـ override السابق دائماً (حتى عند الخطأ)
        _central_conn_override["conn"] = _prev_override


def _calc_cost_impl(conn, item_id, _visited: set = None) -> float:
    """
    التنفيذ الفعلي لـ calc_cost — بدون إدارة الـ central_conn override.
    يُستدعى من calc_cost بعد ضبط الـ override.
    """
    if _visited is None:
        _visited = set()

    if is_shared_id(item_id):
        sid = extract_shared_id(item_id)
        return _shared_raw_unit_price(sid) if sid else 0.0

    item_id_int = int(item_id)
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
# calc_product_cost — [C-01 / E-01] مع دعم scenario_id
# ══════════════════════════════════════════════════════════

def calc_product_cost(conn, product_id: int,
                      scenario_id: int | None = None,
                      central_conn=None) -> tuple[float, dict]:
    """
    [C-01 / E-01] يحسب تكلفة المنتج مع تفاصيل التكاليف.

    Parameters:
        conn         : erp connection للشركة النشطة
        product_id   : ID المنتج (semi أو final)
        scenario_id  : ID السيناريو (None = default)
        central_conn : [P-02b] connection اختياري لـ companies.db

    Returns:
        (total_cost: float, breakdown: dict)
        breakdown = {
            "raw":     float,
            "labor":   float,
            "machine": float,
            "semi":    float,
            "total":   float,
        }
    """
    # [P-02b] ضبط الـ override
    _prev_override = _central_conn_override.get("conn")
    if central_conn is not None:
        _central_conn_override["conn"] = central_conn

    try:
        return _calc_product_cost_impl(conn, product_id, scenario_id)
    finally:
        _central_conn_override["conn"] = _prev_override


def _calc_product_cost_impl(conn, product_id: int,
                             scenario_id: int | None) -> tuple[float, dict]:
    """التنفيذ الفعلي لـ calc_product_cost."""
    item = fetch_item(conn, product_id)
    if not item:
        empty = {"raw": 0.0, "labor": 0.0, "machine": 0.0, "semi": 0.0, "total": 0.0}
        return 0.0, empty

    if item["type"] == "raw":
        price = raw_unit_price(item)
        breakdown = {
            "raw":     price,
            "labor":   0.0,
            "machine": 0.0,
            "semi":    0.0,
            "total":   price,
        }
        return price, breakdown

    raw_cost     = 0.0
    labor_cost   = 0.0
    machine_cost = 0.0
    semi_cost    = 0.0

    bom_rows = _fetch_bom_by_scenario(conn, product_id, scenario_id)
    visited  = {int(product_id)}

    for row in bom_rows:
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
            _visited=visited,
        )
        line_cost = unit_cost * eff_qty

        if child_type == "raw":
            raw_cost += line_cost
        elif child_type == "labor_op":
            labor_cost += line_cost
        elif child_type == "machine_op":
            machine_cost += line_cost
        elif child_type == "semi":
            semi_cost += line_cost

    total = raw_cost + labor_cost + machine_cost + semi_cost
    breakdown = {
        "raw":     raw_cost,
        "labor":   labor_cost,
        "machine": machine_cost,
        "semi":    semi_cost,
        "total":   total,
    }
    return total, breakdown


# ══════════════════════════════════════════════════════════
# calc_cost_breakdown — تفصيل التكلفة (للعرض)
# ══════════════════════════════════════════════════════════

def calc_cost_breakdown(conn, item_id: int,
                        central_conn=None) -> dict:
    """
    يحسب تفاصيل التكلفة باستخدام الـ default scenario.
    يرجع dict بـ materials/labor/machine/total (للتوافق مع الكود القديم).

    [P-02b] يقبل central_conn اختياري — نفس منطق calc_cost.

    للحصول على breakdown بـ 4 categories استخدم:
        total, breakdown = calc_product_cost(conn, item_id)
    """
    _prev_override = _central_conn_override.get("conn")
    if central_conn is not None:
        _central_conn_override["conn"] = central_conn

    try:
        return _calc_cost_breakdown_impl(conn, item_id)
    finally:
        _central_conn_override["conn"] = _prev_override


def _calc_cost_breakdown_impl(conn, item_id: int) -> dict:
    """التنفيذ الفعلي لـ calc_cost_breakdown."""
    item = fetch_item(conn, item_id)
    if not item:
        return {"materials": 0.0, "labor": 0.0, "machine": 0.0, "total": 0.0}

    if item["type"] == "raw":
        p = raw_unit_price(item)
        return {"materials": p, "labor": 0.0, "machine": 0.0, "total": p}

    materials = 0.0
    labor     = 0.0
    machine   = 0.0

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
    # re-exports من costing_base
    "calc_worker_hourly_rate",
    "raw_unit_price",
    "effective_qty",
    # re-exports من costing_ops
    "calc_labor_op_cost",
    "calc_machine_op_cost",
    # دوال هذا الملف
    "calc_cost",
    "calc_product_cost",       # [C-01 / E-01]
    "calc_cost_breakdown",
]