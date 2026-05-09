"""
db/inventory_repo.py
====================
عمليات قراءة/كتابة جداول المخزن في inventory.db.
مع ربط بالحسابات في accounting.db عند الشراء.
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
                          qty_min: float = 0, category_id: int = None,
                          account_code: str = "114",
                          costing_item_id: int = None,
                          notes: str = None) -> int:
    cur = conn.execute("""
        INSERT INTO inventory_items
            (name, unit, qty_min, category_id, account_code, costing_item_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, unit, qty_min, category_id, account_code, costing_item_id, notes))
    conn.commit()
    return cur.lastrowid


def update_inventory_item(conn, inv_id: int, name: str, unit: str,
                          qty_min: float, category_id: int = None,
                          account_code: str = "114", notes: str = None):
    conn.execute("""
        UPDATE inventory_items
        SET name=?, unit=?, qty_min=?, category_id=?, account_code=?, notes=?
        WHERE id=?
    """, (name, unit, qty_min, category_id, account_code, notes, inv_id))
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
    """آخر الحركات (كل الأصناف)."""
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
    يرجع id الحركة الجديدة.
    """
    inv = fetch_inventory_item(conn, inv_id)
    if not inv:
        raise ValueError(f"صنف المخزن {inv_id} غير موجود")

    total_cost = qty * unit_cost
    old_qty    = inv["qty_on_hand"]
    old_avg    = inv["avg_cost"]

    if move_type == "in":
        new_qty = old_qty + qty
        if new_qty > 0:
            new_avg = ((old_qty * old_avg) + total_cost) / new_qty
        else:
            new_avg = unit_cost
    elif move_type == "out":
        if qty > old_qty + 0.0001:
            raise ValueError(f"الكمية المطلوبة ({qty}) أكبر من الرصيد ({old_qty})")
        new_qty    = max(0.0, old_qty - qty)
        new_avg    = old_avg
        total_cost = qty * old_avg   # نقيّم بمتوسط التكلفة
    else:  # adjust
        new_qty    = qty
        new_avg    = old_avg
        total_cost = abs(qty - old_qty) * old_avg

    conn.execute("""
        UPDATE inventory_items SET qty_on_hand=?, avg_cost=? WHERE id=?
    """, (new_qty, new_avg, inv_id))

    cur = conn.execute("""
        INSERT INTO inventory_moves
            (inventory_id, move_type, qty, unit_cost, total_cost,
             date, ref_entry_id, ref_entry_no, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (inv_id, move_type, qty, unit_cost, total_cost,
          date, ref_entry_id, ref_entry_no, notes))
    conn.commit()
    return cur.lastrowid


# ══════════════════════════════════════════════════════════
# عملية شراء متكاملة (مخزن + قيد محاسبي)
# ══════════════════════════════════════════════════════════

def purchase_with_journal(inv_conn, acc_conn,
                           inv_id: int, qty: float, unit_cost: float,
                           date: str, payment_account_id: int,
                           notes: str = None) -> tuple:
    """
    يسجل شراء مخزن مع قيد محاسبي:
    1. يجيب بيانات الصنف من inventory.db
    2. ينشئ قيد في accounting.db (مدين: المخزون / دائن: حساب الدفع)
    3. يسجل حركة وارد في inventory.db مع ref للقيد

    يرجع (entry_id, move_id)
    """
    from db.accounting_repo import (
        insert_entry, add_entry_lines, fetch_account_by_code
    )

    inv        = fetch_inventory_item(inv_conn, inv_id)
    if not inv:
        raise ValueError(f"الصنف {inv_id} غير موجود")

    total_cost = qty * unit_cost
    inv_name   = inv["name"]
    inv_unit   = inv["unit"]

    # ── 1. القيد المحاسبي في accounting.db ──
    desc     = f"شراء {qty:.4g} {inv_unit} من «{inv_name}»"
    entry_id = insert_entry(acc_conn, date, desc,
                             entry_type="purchase", notes=notes)

    # حساب المخزون
    acc_code    = inv["account_code"] or "114"
    inv_account = fetch_account_by_code(acc_conn, acc_code)
    inv_acc_id  = inv_account["id"] if inv_account else None

    if not inv_acc_id:
        # نستخدم أي حساب أصول متداولة
        row = acc_conn.execute(
            "SELECT id FROM accounts WHERE subtype='inventory' AND is_leaf=1 LIMIT 1"
        ).fetchone()
        inv_acc_id = row["id"] if row else None

    lines = [
        {"account_id": inv_acc_id,         "debit":  total_cost, "credit": 0,          "description": desc},
        {"account_id": payment_account_id,  "debit":  0,          "credit": total_cost, "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)

    # رقم القيد للعرض
    entry_row = acc_conn.execute(
        "SELECT ref_no FROM journal_entries WHERE id=?", (entry_id,)
    ).fetchone()
    ref_no = entry_row["ref_no"] if entry_row else None

    # ── 2. حركة المخزن في inventory.db ──
    move_id = record_inventory_move(
        inv_conn, inv_id, "in", qty, unit_cost, date,
        notes=notes, ref_entry_id=entry_id, ref_entry_no=ref_no
    )

    return entry_id, move_id


def outbound_with_journal(inv_conn, acc_conn,
                           inv_id: int, qty: float, date: str,
                           cogs_account_id: int = None,
                           notes: str = None) -> tuple:
    """
    يسجل صرف مخزن مع قيد محاسبي:
    مدين: تكلفة البضاعة المباعة (COGS)
    دائن: المخزون

    يرجع (entry_id, move_id)
    """
    from db.accounting_repo import (
        insert_entry, add_entry_lines, fetch_account_by_code
    )

    inv = fetch_inventory_item(inv_conn, inv_id)
    if not inv:
        raise ValueError(f"الصنف {inv_id} غير موجود")

    unit_cost  = inv["avg_cost"]
    total_cost = qty * unit_cost
    inv_name   = inv["name"]
    inv_unit   = inv["unit"]

    desc     = f"صرف {qty:.4g} {inv_unit} من «{inv_name}»"
    entry_id = insert_entry(acc_conn, date, desc,
                             entry_type="adjustment", notes=notes)

    # حساب المخزون
    acc_code    = inv["account_code"] or "114"
    inv_account = fetch_account_by_code(acc_conn, acc_code)
    inv_acc_id  = inv_account["id"] if inv_account else None

    # حساب COGS
    if cogs_account_id is None:
        row = acc_conn.execute(
            "SELECT id FROM accounts WHERE subtype='cogs' AND is_leaf=1 LIMIT 1"
        ).fetchone()
        cogs_account_id = row["id"] if row else None

    lines = []
    if cogs_account_id:
        lines.append({"account_id": cogs_account_id, "debit": total_cost, "credit": 0, "description": desc})
    if inv_acc_id:
        lines.append({"account_id": inv_acc_id, "debit": 0, "credit": total_cost, "description": desc})

    if lines:
        add_entry_lines(acc_conn, entry_id, lines)

    entry_row = acc_conn.execute(
        "SELECT ref_no FROM journal_entries WHERE id=?", (entry_id,)
    ).fetchone()
    ref_no = entry_row["ref_no"] if entry_row else None

    move_id = record_inventory_move(
        inv_conn, inv_id, "out", qty, unit_cost, date,
        notes=notes, ref_entry_id=entry_id, ref_entry_no=ref_no
    )

    return entry_id, move_id