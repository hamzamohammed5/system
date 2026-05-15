"""
db/items_repo.py  (مع دعم variant_id في BOM)
================
"""


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


def fetch_item(conn, item_id: int):
    return conn.execute("""
        SELECT i.id, i.name, i.type, i.price, i.total_qty,
               i.category_id,
               c.name AS category_name
        FROM   items i
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE  i.id = ?
    """, (item_id,)).fetchone()


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
# BOM — مع waste_pct و variant_id
# ══════════════════════════════════════════════════════════

def _resolve_name(conn, child_type: str, child_id: int) -> str | None:
    if child_type in ("raw", "semi"):
        row = conn.execute(
            "SELECT name FROM items WHERE id=?", (child_id,)
        ).fetchone()
    elif child_type == "labor_op":
        row = conn.execute(
            "SELECT name FROM labor_ops WHERE id=?", (child_id,)
        ).fetchone()
    elif child_type == "machine_op":
        row = conn.execute(
            "SELECT name FROM machine_ops WHERE id=?", (child_id,)
        ).fetchone()
    else:
        return None
    return row["name"] if row else None


def fetch_bom(conn, parent_id: int):
    """
    يرجع صفوف BOM مع waste_pct و variant_id.
    كل صف: (child_type, child_id, qty, waste_pct, variant_id)
    """
    # تحقق من وجود عمود variant_id
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(bom)").fetchall()}
    if "variant_id" in cols:
        return conn.execute(
            "SELECT child_type, child_id, qty, "
            "COALESCE(waste_pct, 0) as waste_pct, "
            "variant_id "
            "FROM bom WHERE parent_id=? ORDER BY id",
            (parent_id,)
        ).fetchall()
    else:
        # fallback بدون variant_id
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
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(bom)").fetchall()}
    if "variant_id" in cols:
        conn.execute(
            """INSERT INTO bom
               (parent_id, child_type, child_id, qty, child_name, waste_pct, variant_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (parent_id, child_type, child_id, qty, name,
             waste_pct or 0.0, variant_id)
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
    """
    rows: list of (child_type, child_id, qty, waste_pct) or
          (child_type, child_id, qty, waste_pct, variant_id)
    """
    conn.execute("DELETE FROM bom WHERE parent_id=?", (parent_id,))
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(bom)").fetchall()}
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
            exists = conn.execute(
                "SELECT 1 FROM items WHERE id=?", (cid,)
            ).fetchone()
        elif ct == "labor_op":
            exists = conn.execute(
                "SELECT 1 FROM labor_ops WHERE id=?", (cid,)
            ).fetchone()
        elif ct == "machine_op":
            exists = conn.execute(
                "SELECT 1 FROM machine_ops WHERE id=?", (cid,)
            ).fetchone()
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


def update_item_category(conn, item_id: int, category_id: int | None):
    conn.execute(
        "UPDATE items SET category_id=? WHERE id=?",
        (category_id, item_id)
    )
    conn.commit()