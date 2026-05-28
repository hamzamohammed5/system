"""
db/inventory/inventory_repo.py
===================
تحسين 20: record_inventory_move يتحقق من qty سالبة في adjust.
"""

# ══════════════════════════════════════════════════════════
# تصنيفات المخزن
# ══════════════════════════════════════════════════════════

def fetch_all_inv_categories(conn):
    return conn.execute(
        "SELECT id, name, color, notes FROM inventory_categories ORDER BY name"
    ).fetchall()


def insert_inv_category(conn, name: str, color: str = "#607d8b",
                         notes: str = None) -> int:
    cur = conn.execute(
        "INSERT INTO inventory_categories (name, color, notes) VALUES (?, ?, ?)",
        (name, color, notes)
    )
    conn.commit()
    return cur.lastrowid


def delete_inv_category(conn, cat_id: int):
    conn.execute("DELETE FROM inventory_categories WHERE id=?", (cat_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# أصناف المخزن
# ══════════════════════════════════════════════════════════

def fetch_all_inventory(conn):
    return conn.execute("""
        SELECT inv.id, inv.name, inv.unit, inv.qty_on_hand,
               inv.qty_min, inv.avg_cost, inv.notes,
               inv.costing_item_id, inv.account_code,
               inv.category_id,
               (inv.qty_on_hand * inv.avg_cost) AS total_value,
               c.name AS category_name, c.color AS category_color
        FROM inventory_items inv
        LEFT JOIN inventory_categories c ON c.id = inv.category_id
        ORDER BY inv.name
    """).fetchall()


def fetch_inventory_item(conn, inv_id: int):
    return conn.execute(
        "SELECT * FROM inventory_items WHERE id=?", (inv_id,)
    ).fetchone()


def insert_inventory_item(conn, name: str, unit: str = "قطعة",
                          qty_min: float = 0,
                          account_code: str = "114",
                          category_id: int = None,
                          costing_item_id: int = None,
                          notes: str = None) -> int:
    cur = conn.execute("""
        INSERT INTO inventory_items
            (name, unit, qty_min, account_code, category_id, costing_item_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, unit, qty_min, account_code, category_id, costing_item_id, notes))
    conn.commit()
    return cur.lastrowid


def update_inventory_item(conn, inv_id: int, name: str, unit: str,
                          qty_min: float,
                          account_code: str = "114",
                          category_id: int = None,
                          notes: str = None):
    conn.execute("""
        UPDATE inventory_items
        SET name=?, unit=?, qty_min=?, account_code=?, category_id=?, notes=?
        WHERE id=?
    """, (name, unit, qty_min, account_code, category_id, notes, inv_id))
    conn.commit()


def delete_inventory_item(conn, inv_id: int):
    conn.execute("DELETE FROM inventory_items WHERE id=?", (inv_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# حركات المخزن
# ══════════════════════════════════════════════════════════

def fetch_inventory_moves(conn, inv_id: int):
    return conn.execute("""
        SELECT id, inventory_id, move_type, qty, unit_cost, total_cost,
               date, ref_entry_id, ref_entry_no, notes, created_at
        FROM inventory_moves
        WHERE inventory_id = ?
        ORDER BY date DESC, id DESC
    """, (inv_id,)).fetchall()


def fetch_recent_moves(conn, move_type: str = None, limit: int = 100):
    if move_type:
        return conn.execute("""
            SELECT im.*, inv.name AS item_name, inv.unit
            FROM inventory_moves im
            JOIN inventory_items inv ON inv.id = im.inventory_id
            WHERE im.move_type = ?
            ORDER BY im.date DESC, im.id DESC
            LIMIT ?
        """, (move_type, limit)).fetchall()
    return conn.execute("""
        SELECT im.*, inv.name AS item_name, inv.unit
        FROM inventory_moves im
        JOIN inventory_items inv ON inv.id = im.inventory_id
        ORDER BY im.date DESC, im.id DESC
        LIMIT ?
    """, (limit,)).fetchall()


def record_inventory_move(conn, inv_id: int, move_type: str,
                           qty: float, unit_cost: float, date: str,
                           notes: str = None,
                           ref_entry_id: int = None,
                           ref_entry_no: str = None) -> int:
    """
    يسجل حركة مخزن ويحدث qty_on_hand و avg_cost (WACC).

    [تحسين 20] يتحقق من qty سالبة في حالة adjust.
    """
    inv = fetch_inventory_item(conn, inv_id)
    if not inv:
        raise ValueError(f"صنف المخزن {inv_id} غير موجود")

    old_qty  = inv["qty_on_hand"]
    old_avg  = inv["avg_cost"]

    if move_type == "in":
        total_cost = qty * unit_cost
        new_qty = old_qty + qty
        new_avg = ((old_qty * old_avg) + total_cost) / new_qty if new_qty > 0 else unit_cost
    elif move_type == "out":
        if qty > old_qty + 0.0001:
            raise ValueError(f"الكمية المطلوبة ({qty:,.4g}) أكبر من الرصيد ({old_qty:,.4g})")
        new_qty    = max(0.0, old_qty - qty)
        new_avg    = old_avg
        total_cost = qty * old_avg
        unit_cost  = old_avg
    else:  # adjust
        # [تحسين 20] تحقق من الكمية السالبة
        if qty < 0:
            raise ValueError(
                f"كمية التسوية ({qty:,.4g}) لا يمكن أن تكون سالبة. "
                f"للتعديل لكمية أقل استخدم حركة صادر بدلاً من ذلك."
            )
        new_qty    = qty
        new_avg    = old_avg
        total_cost = abs(qty - old_qty) * old_avg

    conn.execute(
        "UPDATE inventory_items SET qty_on_hand=?, avg_cost=? WHERE id=?",
        (new_qty, new_avg, inv_id)
    )

    cur = conn.execute("""
        INSERT INTO inventory_moves
            (inventory_id, move_type, qty, unit_cost, total_cost,
             date, ref_entry_id, ref_entry_no, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (inv_id, move_type, qty, unit_cost, total_cost,
          date, ref_entry_id, ref_entry_no, notes))
    conn.commit()
    return cur.lastrowid