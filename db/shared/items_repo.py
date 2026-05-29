"""
db/shared/items_repo.py
========================
تحسين 11: fetch_shared_for_types() batch query بدل connection لكل نوع.
إصلاح 33: استبدال json.loads/dumps المباشر بـ decode_json من json_utils.
تحسين 8:  _get_central_conn_cached() تُعيد connection مشترك بدل فتح
           connection جديد في كل استدعاء لـ fetch_shared_for_types.
           الـ central DB للقراءة فقط (shared_items) — آمن للمشاركة.
           الـ cache مرتبط بالـ company_id النشط ويُبطَل عند تغييره.

[A-02] is_shared_id و extract_shared_id هنا هي المصدر الوحيد الموثوق.
       الملفات الأخرى (shared_items_bridge.py) تُعيد تصديرهما من هنا.
"""

import logging
from db.shared.json_utils import decode_json

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# Central Connection Cache
# ══════════════════════════════════════════════════════════

_central_conn_cache: dict = {
    "conn":       None,
    "company_id": None,
}


def _get_central_conn_cached():
    """
    [تحسين 8] يرجع central connection مشترك (cached).

    المشكلة القديمة: كل استدعاء لـ fetch_shared_for_types يفتح central
    connection جديد، ينفذ query، ثم يُغلقه. مع panels كثيرة تُحدِّث
    نفسها عند كل data_changed، هذا يُنشئ عشرات الـ connections/ثانية.

    الحل الجديد:
      - connection واحد مشترك مرتبط بالـ company_id الحالي.
      - لو تغير company_id أو مات الـ connection → ينشئ واحد جديد.
      - read-only لجدول shared_items → آمن للمشاركة بين القراءات.

    ملاحظة: هذا الـ cache module-level (process-global) — مقبول لأن:
      1. الـ central DB للقراءة فقط هنا.
      2. التطبيق single-threaded (PyQt main thread).
      3. الـ invalidate يحدث عند تغيير الشركة.
    """
    from db.companies.company_state import company_state

    try:
        current_cid = company_state.company_id if company_state.is_ready else None
    except Exception:
        current_cid = None

    cached_conn = _central_conn_cache["conn"]
    cached_cid  = _central_conn_cache["company_id"]

    # تحقق من أن الـ cache صالح
    if (cached_conn is not None and
            cached_cid == current_cid):
        try:
            cached_conn.execute("SELECT 1")
            return cached_conn
        except Exception:
            pass  # الـ connection مات — ننشئ واحد جديد

    # أنشئ connection جديد
    from db.companies.companies_schema import get_central_connection
    new_conn = get_central_connection()
    _central_conn_cache["conn"]       = new_conn
    _central_conn_cache["company_id"] = current_cid
    return new_conn


def invalidate_central_conn_cache():
    """
    [تحسين 8] يُبطل الـ central connection cache.
    استدعه عند تغيير الشركة النشطة.

    يُستدعى تلقائياً من company_state عند تغيير الشركة
    (أضف الاستدعاء هناك إذا لم يكن موجوداً).
    """
    old_conn = _central_conn_cache.get("conn")
    if old_conn is not None:
        try:
            old_conn.close()
        except Exception:
            pass
    _central_conn_cache["conn"]       = None
    _central_conn_cache["company_id"] = None


# ══════════════════════════════════════════════════════════
# BOM columns cache
# ══════════════════════════════════════════════════════════

_bom_cols_cache: dict[str, set] = {}


def _get_bom_cols(conn) -> set:
    try:
        path = conn.execute("PRAGMA database_list").fetchone()[2]
    except Exception:
        path = str(id(conn))

    if path not in _bom_cols_cache:
        _bom_cols_cache[path] = {
            r["name"] for r in conn.execute("PRAGMA table_info(bom)").fetchall()
        }
    return _bom_cols_cache[path]


def invalidate_bom_cols_cache(conn=None):
    if conn is None:
        _bom_cols_cache.clear()
    else:
        try:
            path = conn.execute("PRAGMA database_list").fetchone()[2]
        except Exception:
            path = str(id(conn))
        _bom_cols_cache.pop(path, None)


# ══════════════════════════════════════════════════════════
# Shared ID Utilities — [A-02] المصدر الوحيد لهذه الدوال
# ══════════════════════════════════════════════════════════

def is_shared_id(item_id) -> bool:
    """
    يتحقق هل الـ ID يُشير لعنصر مشترك.
    العناصر المشتركة تبدأ بـ "shared:" مثل "shared:42".

    [A-02] هذا هو التعريف الوحيد — الملفات الأخرى تستورد من هنا.
    """
    return isinstance(item_id, str) and str(item_id).startswith("shared:")


def extract_shared_id(item_id) -> "int | None":
    """
    يستخرج الـ integer ID من "shared:42" → 42.
    يرجع None لو الصيغة غير صحيحة.

    [A-02] هذا هو التعريف الوحيد — الملفات الأخرى تستورد من هنا.
    """
    if is_shared_id(item_id):
        try:
            return int(str(item_id).split(":")[1])
        except Exception:
            return None
    return None


# ══════════════════════════════════════════════════════════
# Items
# ══════════════════════════════════════════════════════════

def fetch_all_items(conn):
    return conn.execute(
        "SELECT id, name, type, price, total_qty FROM items ORDER BY name"
    ).fetchall()


def fetch_items_by_type(conn, item_type: str):
    return conn.execute("""
        SELECT i.id, i.name, i.price, i.total_qty,
               i.category_id,
               c.name AS category_name
        FROM   items i
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE  i.type = ?
        ORDER  BY i.name
    """, (item_type,)).fetchall()


def fetch_items_by_type_with_shared(conn, item_type: str,
                                     company_id: int = None) -> list:
    local = [dict(r) for r in fetch_items_by_type(conn, item_type)]
    for item in local:
        item["is_shared"]      = False
        item["shared_item_id"] = None

    shared = _fetch_shared_for_type(item_type, company_id)
    return local + shared


def _fetch_shared_for_type(item_type: str, company_id: int = None) -> list:
    try:
        result = fetch_shared_for_types(company_id=company_id, types=[item_type])
        return result.get(item_type, [])
    except Exception as e:
        logger.warning("[items_repo] _fetch_shared_for_type error: %s", e)
        return []


def fetch_shared_for_types(company_id: int = None,
                            types: list = None) -> dict:
    """
    [تحسين 11] يجيب العناصر المشتركة لأكثر من نوع في connection واحد.
    [تحسين 8]  يستخدم _get_central_conn_cached() بدل فتح connection جديد.

    التغيير:
      القديم: get_central_connection() + central.close() في كل استدعاء.
      الجديد: connection مشترك من الـ cache — لا فتح/إغلاق متكرر.

    ملاحظة: لا نُغلق الـ connection هنا لأنه من الـ cache.
    الإغلاق يحدث فقط في invalidate_central_conn_cache().
    """
    if not types:
        return {}

    result = {t: [] for t in types}

    try:
        if company_id is None:
            from db.companies.company_state import company_state
            if not company_state.is_ready:
                return result
            company_id = company_state.company_id

        # [تحسين 8] connection مشترك من الـ cache
        central = _get_central_conn_cached()

        placeholders = ",".join("?" * len(types))
        rows = central.execute(f"""
            SELECT s.id, s.name, s.shared_type, s.data, s.updated_at
            FROM company_shared_links lnk
            JOIN shared_items s ON s.id = lnk.shared_item_id
            WHERE lnk.company_id = ?
              AND s.shared_type IN ({placeholders})
            ORDER BY s.shared_type, s.name
        """, [company_id] + list(types)).fetchall()

        for row in rows:
            item = _shared_row_to_item(row, row["shared_type"])
            if row["shared_type"] in result:
                result[row["shared_type"]].append(item)

    except Exception as e:
        logger.warning("[items_repo] fetch_shared_for_types error: %s", e)
        # لو الـ cache تلف → نُبطله للمحاولة القادمة
        _central_conn_cache["conn"] = None

    return result


def _shared_row_to_item(row, item_type: str) -> dict:
    """
    يحول صف shared_items إلى dict يشبه صف items.
    [إصلاح 33] يستخدم decode_json من json_utils بدل json.loads المحلي.
    """
    data = decode_json(row["data"])

    base = {
        "id":             f"shared:{row['id']}",
        "shared_item_id": row["id"],
        "name":           row["name"],
        "type":           item_type,
        "category_id":    None,
        "category_name":  "🔗 مشترك",
        "is_shared":      True,
        "total_qty":      None,
    }

    if item_type == "raw":
        base["price"]     = float(data.get("price", 0.0))
        base["total_qty"] = data.get("total_qty")
    elif item_type == "machine":
        base["rate_per_hour"] = float(data.get("rate_per_hour", 0.0))
        base["rate_per_unit"] = float(data.get("rate_per_unit", 0.0))
        base["price"] = 0.0
    elif item_type == "labor_op":
        base["minutes"] = float(data.get("minutes", 0.0))
        base["price"] = 0.0
    elif item_type == "machine_op":
        base["mode"]          = data.get("mode", "time")
        base["value"]         = float(data.get("value", 0.0))
        base["machine_name"]  = data.get("machine_name", "")
        base["rate_per_hour"] = float(data.get("rate_per_hour", 0.0))
        base["rate_per_unit"] = float(data.get("rate_per_unit", 0.0))
        base["price"] = 0.0
    else:
        base["price"] = 0.0

    return base


def fetch_item(conn, item_id):
    if is_shared_id(item_id):
        shared_id = extract_shared_id(item_id)
        if shared_id is None:
            return None
        return _fetch_shared_item_as_row(shared_id)

    return conn.execute("""
        SELECT i.id, i.name, i.type, i.price, i.total_qty,
               i.category_id,
               c.name AS category_name
        FROM   items i
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE  i.id = ?
    """, (item_id,)).fetchone()


def _fetch_shared_item_as_row(shared_item_id: int):
    try:
        # [تحسين 8] نستخدم الـ cached connection هنا أيضاً
        central = _get_central_conn_cached()
        row = central.execute(
            "SELECT id, name, shared_type, data FROM shared_items WHERE id=?",
            (shared_item_id,)
        ).fetchone()

        if not row:
            return None

        data = decode_json(row["data"])

        return _SharedItemRow(
            id=f"shared:{row['id']}",
            name=row["name"],
            type=row["shared_type"],
            price=float(data.get("price", 0.0)),
            total_qty=data.get("total_qty"),
            category_id=None,
            category_name="🔗 مشترك",
            is_shared=True,
            shared_item_id=row["id"],
            data=data,
        )
    except Exception as e:
        logger.warning("[items_repo] _fetch_shared_item_as_row error: %s", e)
        _central_conn_cache["conn"] = None
        return None


class _SharedItemRow:
    """يحاكي sqlite3.Row للعناصر المشتركة."""

    def __init__(self, **kwargs):
        self._data = kwargs

    def __getitem__(self, key):
        return self._data.get(key)

    def __getattr__(self, key):
        if key.startswith("_"):
            raise AttributeError(key)
        val = self._data.get(key)
        if val is None and key not in self._data:
            logger.debug(
                "_SharedItemRow: unknown attribute '%s' — check caller", key
            )
        return val

    def keys(self):
        return self._data.keys()

    def get(self, key, default=None):
        return self._data.get(key, default)


def insert_item(conn, name: str, item_type: str, price: float = 0,
                category_id: int = None, total_qty: float = None) -> int:
    cur = conn.execute(
        "INSERT INTO items (name, type, price, category_id, total_qty) VALUES (?, ?, ?, ?, ?)",
        (name, item_type, price, category_id, total_qty)
    )
    conn.commit()
    return cur.lastrowid


def update_item(conn, item_id: int, name: str, price: float,
                category_id: int = None, total_qty: float = None):
    conn.execute(
        "UPDATE items SET name=?, price=?, category_id=?, total_qty=? WHERE id=?",
        (name, price, category_id, total_qty, item_id)
    )
    conn.commit()


def delete_item(conn, item_id: int):
    conn.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# BOM
# ══════════════════════════════════════════════════════════

def _resolve_name(conn, child_type: str, child_id: int) -> "str | None":
    if child_type in ("raw", "semi"):
        row = conn.execute("SELECT name FROM items WHERE id=?", (child_id,)).fetchone()
    elif child_type == "labor_op":
        row = conn.execute("SELECT name FROM labor_ops WHERE id=?", (child_id,)).fetchone()
    elif child_type == "machine_op":
        row = conn.execute("SELECT name FROM machine_ops WHERE id=?", (child_id,)).fetchone()
    else:
        return None
    return row["name"] if row else None


def fetch_bom(conn, parent_id: int):
    cols = _get_bom_cols(conn)
    if "variant_id" in cols:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct, 0) as waste_pct, "
            "variant_id "
            "FROM bom WHERE parent_id=? ORDER BY id",
            (parent_id,)
        ).fetchall()
    else:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct, 0) as waste_pct "
            "FROM bom WHERE parent_id=? ORDER BY id",
            (parent_id,)
        ).fetchall()


def insert_bom_row(conn, parent_id: int, child_type: str, child_id: int,
                   qty: float, waste_pct: float = 0.0,
                   variant_id: int = None):
    name = _resolve_name(conn, child_type, child_id)
    cols = _get_bom_cols(conn)
    if "variant_id" in cols:
        conn.execute(
            """INSERT INTO bom
               (parent_id, child_type, child_id, qty, child_name, waste_pct, variant_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (parent_id, child_type, child_id, qty, name, waste_pct or 0.0, variant_id)
        )
    else:
        conn.execute(
            """INSERT INTO bom (parent_id, child_type, child_id, qty, child_name, waste_pct)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (parent_id, child_type, child_id, qty, name, waste_pct or 0.0)
        )
    conn.commit()


def delete_bom_row(conn, parent_id: int, child_type: str, child_id: int):
    conn.execute(
        "DELETE FROM bom WHERE parent_id=? AND child_type=? AND child_id=?",
        (parent_id, child_type, child_id)
    )
    conn.commit()


def replace_bom(conn, parent_id: int, rows: list[tuple]):
    conn.execute("DELETE FROM bom WHERE parent_id=?", (parent_id,))
    cols = _get_bom_cols(conn)
    has_variant = "variant_id" in cols

    for row in rows:
        ct, cid, qty = row[0], row[1], row[2]
        waste_pct  = float(row[3]) if len(row) > 3 and row[3] is not None else 0.0
        variant_id = int(row[4]) if len(row) > 4 and row[4] is not None else None
        name = _resolve_name(conn, ct, cid)

        if has_variant:
            conn.execute(
                """INSERT INTO bom
                   (parent_id, child_type, child_id, qty, child_name, waste_pct, variant_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (parent_id, ct, cid, qty, name, waste_pct, variant_id)
            )
        else:
            conn.execute(
                """INSERT INTO bom (parent_id, child_type, child_id, qty, child_name, waste_pct)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (parent_id, ct, cid, qty, name, waste_pct)
            )
    conn.commit()


# ══════════════════════════════════════════════════════════
# Orphans
# ══════════════════════════════════════════════════════════

def fetch_orphan_bom_rows(conn, parent_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT child_type, child_id, child_name, qty, "
        "COALESCE(waste_pct,0) as waste_pct "
        "FROM bom WHERE parent_id=?",
        (parent_id,)
    ).fetchall()

    orphans = []
    for row in rows:
        ct  = row["child_type"]
        cid = row["child_id"]

        if ct in ("raw", "semi"):
            exists = conn.execute("SELECT 1 FROM items WHERE id=?", (cid,)).fetchone()
        elif ct == "labor_op":
            exists = conn.execute("SELECT 1 FROM labor_ops WHERE id=?", (cid,)).fetchone()
        elif ct == "machine_op":
            exists = conn.execute("SELECT 1 FROM machine_ops WHERE id=?", (cid,)).fetchone()
        else:
            exists = True

        if not exists:
            orphans.append({
                "child_type": ct,
                "child_id":   cid,
                "child_name": row["child_name"],
                "qty":        row["qty"],
                "waste_pct":  row["waste_pct"],
            })
    return orphans


def delete_orphan_bom_rows(conn, parent_id: int) -> int:
    orphans = fetch_orphan_bom_rows(conn, parent_id)
    for o in orphans:
        conn.execute(
            "DELETE FROM bom WHERE parent_id=? AND child_type=? AND child_id=?",
            (parent_id, o["child_type"], o["child_id"])
        )
    conn.commit()
    return len(orphans)


def fetch_products_with_orphan(conn, child_type: str, child_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT DISTINCT parent_id FROM bom WHERE child_type=? AND child_id=?",
        (child_type, child_id)
    ).fetchall()
    return [r["parent_id"] for r in rows]


def cleanup_empty_products_after_orphan_fix(conn, parent_ids: list[int]) -> list[int]:
    deleted = []
    for pid in parent_ids:
        remaining = conn.execute(
            "SELECT COUNT(*) as cnt FROM bom WHERE parent_id=?", (pid,)
        ).fetchone()["cnt"]

        if remaining == 0:
            item = conn.execute(
                "SELECT id FROM items WHERE id=? AND type IN ('semi','final')",
                (pid,)
            ).fetchone()
            if item:
                conn.execute("DELETE FROM items WHERE id=?", (pid,))
                deleted.append(pid)

    conn.commit()
    return deleted


def update_item_category(conn, item_id: int, category_id: "int | None"):
    conn.execute(
        "UPDATE items SET category_id=? WHERE id=?",
        (category_id, item_id)
    )
    conn.commit()
