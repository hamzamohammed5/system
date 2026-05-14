"""
db/bom_scenarios_repo.py
=========================
عمليات قراءة/كتابة جداول السيناريوهات (bom_scenarios).

كل منتج (semi/final) ممكن يكون له أكثر من سيناريو BOM.
واحد فقط هو الـ default — بيُستخدم في الحسابات.
الباقيين للعرض والمقارنة فقط.
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# السيناريوهات
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

    old_rows = conn.execute(
        "SELECT child_type, child_id, qty, child_name, "
        "COALESCE(waste_pct,0) as waste_pct, variant_id, machine_op_row_id "
        "FROM bom WHERE scenario_id=?",
        (scenario_id,)
    ).fetchall()

    has_variant  = _col_exists(conn, "bom", "variant_id")
    has_row_id   = _col_exists(conn, "bom", "machine_op_row_id")
    has_scenario = _col_exists(conn, "bom", "scenario_id")

    for r in old_rows:
        _insert_bom_row(
            conn, sc["item_id"], r["child_type"], r["child_id"],
            r["qty"], r["child_name"], r["waste_pct"],
            r["variant_id"] if has_variant else None,
            r["machine_op_row_id"] if has_row_id else None,
            new_id if has_scenario else None,
        )
    conn.commit()
    return new_id


def _col_exists(conn, table: str, col: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == col for r in rows)


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


def _insert_bom_row(conn, parent_id: int, child_type: str, child_id: int,
                    qty: float, child_name, waste_pct: float,
                    variant_id, machine_op_row_id, scenario_id):
    """
    INSERT آمن في جدول bom — يتعامل مع وجود/غياب الأعمدة الجديدة.
    """
    has_variant  = _col_exists(conn, "bom", "variant_id")
    has_row_id   = _col_exists(conn, "bom", "machine_op_row_id")
    has_scenario = _col_exists(conn, "bom", "scenario_id")

    if has_variant and has_row_id and has_scenario:
        conn.execute(
            "INSERT INTO bom "
            "(parent_id, child_type, child_id, qty, child_name,"
            " waste_pct, variant_id, machine_op_row_id, scenario_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (parent_id, child_type, child_id, qty, child_name,
             waste_pct, variant_id, machine_op_row_id, scenario_id)
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
# BOM حسب السيناريو
# ══════════════════════════════════════════════════════════

def fetch_bom_for_scenario(conn, scenario_id: int) -> list:
    """
    صفوف BOM الخاصة بسيناريو معين — دائماً يجيب machine_op_row_id.
    """
    has_row_id = _col_exists(conn, "bom", "machine_op_row_id")
    has_variant = _col_exists(conn, "bom", "variant_id")

    if has_row_id and has_variant:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct,0) as waste_pct, "
            "variant_id, machine_op_row_id "
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


def replace_bom_for_scenario(conn, scenario_id: int, rows: list[tuple]):
    """
    rows: list of (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
    يحذف BOM القديم للسيناريو ويكتب الجديد بشكل كامل.
    """
    sc = fetch_scenario(conn, scenario_id)
    if not sc:
        return

    # احذف rows الخاصة بهذا السيناريو فقط
    conn.execute("DELETE FROM bom WHERE scenario_id=?", (scenario_id,))

    for row in rows:
        ct        = row[0]
        cid       = row[1]
        qty       = row[2]
        waste_pct = float(row[3]) if len(row) > 3 and row[3] is not None else 0.0
        vid       = row[4] if len(row) > 4 else None
        # machine_op_row_id — العنصر السادس (index 5)
        mor_id    = row[5] if len(row) > 5 else None
        name      = _resolve_name(conn, ct, cid)

        _insert_bom_row(
            conn, sc["item_id"], ct, cid, qty, name,
            waste_pct, vid, mor_id, scenario_id
        )

    conn.commit()