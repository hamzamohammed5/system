"""
db/bom_scenarios_repo.py  (نسخة مصلوحة - إصلاح _bom_cols_cache)
=========================
الإصلاحات:
1. إزالة _bom_cols_cache العالمي الخطير - كان يُسبب المشكلة الجذرية
   لو اتحسب قبل ما migration يشتغل، كان بيحفظ قائمة أعمدة ناقصة
   وكل الـ calls التالية كانت تعتقد إن machine_op_row_id مش موجود
2. _get_bom_cols الآن بتعمل PRAGMA في كل call (أبطأ قليلاً لكن صح دايماً)
3. machine_op_row_id بيتحفظ ويتقرأ صح في كل الحالات
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# مساعدات الأعمدة — بدون cache عشان تكون دايماً محدثة
# ══════════════════════════════════════════════════════════

def _get_bom_cols(conn) -> set:
    """
    يجيب أعمدة جدول bom.
    ⚠️ لا نستخدم cache عشان لو migration اشتغل بعد أول call
    نضمن إننا نشوف الأعمدة الجديدة.
    """
    try:
        return {
            r["name"]
            for r in conn.execute("PRAGMA table_info(bom)").fetchall()
        }
    except Exception:
        return set()


def _col_exists(conn, table: str, col: str) -> bool:
    if table == "bom":
        return col in _get_bom_cols(conn)
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == col for r in rows)
    except Exception:
        return False


def _resolve_name(conn, child_type: str, child_id: int):
    if child_type in ("raw", "semi"):
        row = conn.execute("SELECT name FROM items WHERE id=?", (child_id,)).fetchone()
    elif child_type == "labor_op":
        row = conn.execute("SELECT name FROM labor_ops WHERE id=?", (child_id,)).fetchone()
    elif child_type == "machine_op":
        row = conn.execute("SELECT name FROM machine_ops WHERE id=?", (child_id,)).fetchone()
    else:
        return None
    return row["name"] if row else None


# ══════════════════════════════════════════════════════════
# السيناريوهات — CRUD
# ══════════════════════════════════════════════════════════

def fetch_scenarios(conn, item_id: int) -> list:
    """كل السيناريوهات لمنتج معين."""
    return conn.execute(
        "SELECT id, item_id, name, is_default, notes, created_at "
        "FROM bom_scenarios WHERE item_id=? ORDER BY id",
        (item_id,)
    ).fetchall()


def fetch_scenario(conn, scenario_id: int):
    return conn.execute(
        "SELECT id, item_id, name, is_default, notes, created_at "
        "FROM bom_scenarios WHERE id=?",
        (scenario_id,)
    ).fetchone()


def fetch_default_scenario(conn, item_id: int):
    """يرجع السيناريو الـ default — لو مفيش يرجع أول سيناريو."""
    row = conn.execute(
        "SELECT id, item_id, name, is_default, notes "
        "FROM bom_scenarios WHERE item_id=? AND is_default=1 LIMIT 1",
        (item_id,)
    ).fetchone()
    if not row:
        row = conn.execute(
            "SELECT id, item_id, name, is_default, notes "
            "FROM bom_scenarios WHERE item_id=? ORDER BY id LIMIT 1",
            (item_id,)
        ).fetchone()
    return row


def insert_scenario(conn, item_id: int, name: str,
                    is_default: bool = False, notes: str = "") -> int:
    if is_default:
        conn.execute(
            "UPDATE bom_scenarios SET is_default=0 WHERE item_id=?",
            (item_id,)
        )
    cur = conn.execute(
        "INSERT INTO bom_scenarios (item_id, name, is_default, notes) VALUES (?, ?, ?, ?)",
        (item_id, name, 1 if is_default else 0, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_scenario(conn, scenario_id: int, name: str, notes: str = ""):
    conn.execute(
        "UPDATE bom_scenarios SET name=?, notes=? WHERE id=?",
        (name, notes or "", scenario_id)
    )
    conn.commit()


def set_default_scenario(conn, scenario_id: int):
    sc = fetch_scenario(conn, scenario_id)
    if not sc:
        return
    conn.execute(
        "UPDATE bom_scenarios SET is_default=0 WHERE item_id=?",
        (sc["item_id"],)
    )
    conn.execute(
        "UPDATE bom_scenarios SET is_default=1 WHERE id=?",
        (scenario_id,)
    )
    conn.commit()


def delete_scenario(conn, scenario_id: int) -> bool:
    sc = fetch_scenario(conn, scenario_id)
    if not sc:
        return False
    count = conn.execute(
        "SELECT COUNT(*) as c FROM bom_scenarios WHERE item_id=?",
        (sc["item_id"],)
    ).fetchone()["c"]
    if count <= 1:
        return False
    conn.execute("DELETE FROM bom WHERE scenario_id=?", (scenario_id,))
    conn.execute("DELETE FROM bom_scenarios WHERE id=?", (scenario_id,))
    conn.commit()
    if sc["is_default"]:
        first = conn.execute(
            "SELECT id FROM bom_scenarios WHERE item_id=? ORDER BY id LIMIT 1",
            (sc["item_id"],)
        ).fetchone()
        if first:
            conn.execute(
                "UPDATE bom_scenarios SET is_default=1 WHERE id=?",
                (first["id"],)
            )
            conn.commit()
    return True


def clone_scenario(conn, scenario_id: int, new_name: str) -> int:
    sc = fetch_scenario(conn, scenario_id)
    if not sc:
        raise ValueError("السيناريو غير موجود")

    new_id = insert_scenario(
        conn, sc["item_id"], new_name, is_default=False, notes=sc["notes"] or ""
    )

    old_rows = fetch_bom_for_scenario(conn, scenario_id)
    for r in old_rows:
        _insert_bom_row(
            conn, sc["item_id"],
            r["child_type"], r["child_id"], r["qty"], None,
            float(r["waste_pct"]) if r["waste_pct"] is not None else 0.0,
            r["variant_id"]        if "variant_id"        in r.keys() else None,
            r["machine_op_row_id"] if "machine_op_row_id" in r.keys() else None,
            new_id,
        )
    conn.commit()
    return new_id


# ══════════════════════════════════════════════════════════
# _insert_bom_row
# ══════════════════════════════════════════════════════════

def _insert_bom_row(conn, parent_id: int, child_type: str, child_id: int,
                    qty: float, child_name, waste_pct: float,
                    variant_id, machine_op_row_id, scenario_id):
    """
    INSERT آمن في جدول bom — يتعامل مع وجود/غياب الأعمدة.
    يحفظ machine_op_row_id في كل الحالات اللي بيكون فيها العمود موجود.
    """
    # ⚠️ لا نستخدم cache هنا - نجيب الأعمدة الفعلية في كل مرة
    cols = _get_bom_cols(conn)
    has_variant  = "variant_id"        in cols
    has_row_id   = "machine_op_row_id" in cols
    has_scenario = "scenario_id"       in cols

    if child_name is None:
        child_name = _resolve_name(conn, child_type, child_id)

    # الحالة الكاملة (الأكثر شيوعاً بعد run_migrations_v2)
    if has_variant and has_row_id and has_scenario:
        conn.execute(
            "INSERT INTO bom "
            "(parent_id, child_type, child_id, qty, child_name,"
            " waste_pct, variant_id, machine_op_row_id, scenario_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (parent_id, child_type, child_id, qty, child_name,
             waste_pct, variant_id, machine_op_row_id, scenario_id)
        )
    elif has_row_id and has_scenario:
        conn.execute(
            "INSERT INTO bom "
            "(parent_id, child_type, child_id, qty, child_name,"
            " waste_pct, machine_op_row_id, scenario_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (parent_id, child_type, child_id, qty, child_name,
             waste_pct, machine_op_row_id, scenario_id)
        )
    elif has_variant and has_scenario:
        conn.execute(
            "INSERT INTO bom "
            "(parent_id, child_type, child_id, qty, child_name,"
            " waste_pct, variant_id, scenario_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (parent_id, child_type, child_id, qty, child_name,
             waste_pct, variant_id, scenario_id)
        )
    elif has_row_id:
        conn.execute(
            "INSERT INTO bom "
            "(parent_id, child_type, child_id, qty, child_name,"
            " waste_pct, machine_op_row_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (parent_id, child_type, child_id, qty, child_name,
             waste_pct, machine_op_row_id)
        )
    elif has_scenario:
        conn.execute(
            "INSERT INTO bom "
            "(parent_id, child_type, child_id, qty, child_name,"
            " waste_pct, scenario_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (parent_id, child_type, child_id, qty, child_name,
             waste_pct, scenario_id)
        )
    else:
        conn.execute(
            "INSERT INTO bom "
            "(parent_id, child_type, child_id, qty, child_name, waste_pct)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (parent_id, child_type, child_id, qty, child_name, waste_pct)
        )


# ══════════════════════════════════════════════════════════
# fetch_bom_for_scenario
# ══════════════════════════════════════════════════════════

def fetch_bom_for_scenario(conn, scenario_id: int) -> list:
    """
    يجيب صفوف BOM لسيناريو محدد.
    دايماً بيرجع machine_op_row_id (NULL لو العمود مش موجود).
    ⚠️ لا نستخدم cache - نتحقق من الأعمدة الفعلية في كل مرة.
    """
    # نجيب الأعمدة الفعلية الآن (بدون cache)
    cols = _get_bom_cols(conn)
    has_row_id  = "machine_op_row_id" in cols
    has_variant = "variant_id"        in cols

    if has_row_id and has_variant:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct,0) as waste_pct, "
            "variant_id, machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()
    elif has_row_id:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct,0) as waste_pct, "
            "NULL as variant_id, machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()
    elif has_variant:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct,0) as waste_pct, "
            "variant_id, NULL as machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()
    else:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct,0) as waste_pct, "
            "NULL as variant_id, NULL as machine_op_row_id "
            "FROM bom WHERE scenario_id=? ORDER BY id",
            (scenario_id,)
        ).fetchall()


# ══════════════════════════════════════════════════════════
# replace_bom_for_scenario
# ══════════════════════════════════════════════════════════

def replace_bom_for_scenario(conn, scenario_id: int, rows):
    """
    rows: list/tuple of:
      (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)

    يضمن حفظ machine_op_row_id صح.
    """
    sc = fetch_scenario(conn, scenario_id)
    if not sc:
        return

    conn.execute("DELETE FROM bom WHERE scenario_id=?", (scenario_id,))

    for row in rows:
        ct        = row[0]
        cid       = row[1]
        qty       = row[2]
        waste_pct = float(row[3]) if len(row) > 3 and row[3] is not None else 0.0
        vid       = row[4] if len(row) > 4 else None
        # machine_op_row_id هو العنصر السادس (index 5)
        mor_id    = row[5] if len(row) > 5 else None

        _insert_bom_row(
            conn, sc["item_id"], ct, cid, qty, None,
            waste_pct, vid, mor_id, scenario_id
        )

    conn.commit()