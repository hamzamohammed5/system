"""
db/accounting_repo.py
=====================
عمليات قراءة/كتابة جداول الحسابات والمخزن.
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# الحسابات (Chart of Accounts)
# ══════════════════════════════════════════════════════════

def fetch_all_accounts(conn, acc_type: str = None):
    if acc_type:
        return conn.execute("""
            SELECT a.id, a.code, a.name, a.type, a.subtype,
                   a.parent_id, a.is_leaf,
                   p.name AS parent_name,
                   (SELECT COALESCE(SUM(jl.debit)-SUM(jl.credit),0)
                    FROM journal_lines jl WHERE jl.account_id = a.id) AS balance
            FROM accounts a
            LEFT JOIN accounts p ON p.id = a.parent_id
            WHERE a.type = ?
            ORDER BY a.code
        """, (acc_type,)).fetchall()
    return conn.execute("""
        SELECT a.id, a.code, a.name, a.type, a.subtype,
               a.parent_id, a.is_leaf,
               p.name AS parent_name,
               (SELECT COALESCE(SUM(jl.debit)-SUM(jl.credit),0)
                FROM journal_lines jl WHERE jl.account_id = a.id) AS balance
        FROM accounts a
        LEFT JOIN accounts p ON p.id = a.parent_id
        ORDER BY a.code
    """).fetchall()


def fetch_account(conn, account_id: int):
    return conn.execute("""
        SELECT a.*, p.name AS parent_name
        FROM accounts a
        LEFT JOIN accounts p ON p.id = a.parent_id
        WHERE a.id = ?
    """, (account_id,)).fetchone()


def fetch_leaf_accounts(conn, acc_type: str = None):
    """الحسابات النهائية فقط (قابلة للترحيل)."""
    if acc_type:
        return conn.execute("""
            SELECT id, code, name, type, subtype
            FROM accounts WHERE is_leaf=1 AND type=?
            ORDER BY code
        """, (acc_type,)).fetchall()
    return conn.execute("""
        SELECT id, code, name, type, subtype
        FROM accounts WHERE is_leaf=1
        ORDER BY code
    """).fetchall()


def insert_account(conn, code: str, name: str, acc_type: str,
                   subtype: str = None, parent_id: int = None,
                   notes: str = None) -> int:
    # الأب يصبح غير leaf
    if parent_id:
        conn.execute("UPDATE accounts SET is_leaf=0 WHERE id=?", (parent_id,))
    cur = conn.execute("""
        INSERT INTO accounts (code, name, type, subtype, parent_id, is_leaf, notes)
        VALUES (?, ?, ?, ?, ?, 1, ?)
    """, (code, name, acc_type, subtype, parent_id, notes))
    conn.commit()
    return cur.lastrowid


def update_account(conn, account_id: int, name: str, notes: str = None):
    conn.execute(
        "UPDATE accounts SET name=?, notes=? WHERE id=?",
        (name, notes, account_id)
    )
    conn.commit()


def delete_account(conn, account_id: int):
    conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    conn.commit()


def get_account_balance(conn, account_id: int) -> float:
    """الرصيد = مجموع المدين - مجموع الدائن."""
    row = conn.execute("""
        SELECT COALESCE(SUM(debit)-SUM(credit), 0) AS bal
        FROM journal_lines WHERE account_id=?
    """, (account_id,)).fetchone()
    return row["bal"] if row else 0.0


def get_balances_by_type(conn) -> dict:
    """ملخص الأرصدة لكل نوع حساب."""
    rows = conn.execute("""
        SELECT a.type,
               COALESCE(SUM(jl.debit),0)  AS total_debit,
               COALESCE(SUM(jl.credit),0) AS total_credit
        FROM accounts a
        LEFT JOIN journal_lines jl ON jl.account_id = a.id
        GROUP BY a.type
    """).fetchall()
    result = {}
    for r in rows:
        result[r["type"]] = {
            "debit":   r["total_debit"],
            "credit":  r["total_credit"],
            "balance": r["total_debit"] - r["total_credit"],
        }
    return result


# ══════════════════════════════════════════════════════════
# رقم القيد التلقائي
# ══════════════════════════════════════════════════════════

def next_ref_no(conn) -> str:
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(ref_no,4) AS INTEGER)) AS mx FROM journal_entries"
    ).fetchone()
    n = (row["mx"] or 0) + 1
    return f"JE-{n:05d}"


# ══════════════════════════════════════════════════════════
# القيود المحاسبية (Journal Entries)
# ══════════════════════════════════════════════════════════

def fetch_all_entries(conn, limit: int = 200):
    return conn.execute("""
        SELECT je.id, je.ref_no, je.date, je.description,
               je.type, je.status, je.notes, je.created_at,
               (SELECT COALESCE(SUM(debit),0) FROM journal_lines WHERE entry_id=je.id) AS total_debit,
               (SELECT COALESCE(SUM(credit),0) FROM journal_lines WHERE entry_id=je.id) AS total_credit
        FROM journal_entries je
        ORDER BY je.date DESC, je.id DESC
        LIMIT ?
    """, (limit,)).fetchall()


def fetch_entry(conn, entry_id: int):
    return conn.execute(
        "SELECT * FROM journal_entries WHERE id=?", (entry_id,)
    ).fetchone()


def fetch_entry_lines(conn, entry_id: int):
    return conn.execute("""
        SELECT jl.id, jl.account_id, jl.debit, jl.credit, jl.description,
               a.code AS account_code, a.name AS account_name, a.type AS account_type
        FROM journal_lines jl
        JOIN accounts a ON a.id = jl.account_id
        WHERE jl.entry_id = ?
        ORDER BY jl.id
    """, (entry_id,)).fetchall()


def insert_entry(conn, date: str, description: str,
                 entry_type: str = "manual", notes: str = None,
                 ref_id: int = None, ref_type: str = None) -> int:
    ref_no = next_ref_no(conn)
    cur = conn.execute("""
        INSERT INTO journal_entries
            (ref_no, date, description, type, status, notes, ref_id, ref_type)
        VALUES (?, ?, ?, ?, 'posted', ?, ?, ?)
    """, (ref_no, date, description, entry_type, notes, ref_id, ref_type))
    conn.commit()
    return cur.lastrowid


def add_entry_lines(conn, entry_id: int, lines: list[dict]):
    """
    lines: [{"account_id": int, "debit": float, "credit": float, "description": str}, ...]
    """
    for line in lines:
        conn.execute("""
            INSERT INTO journal_lines (entry_id, account_id, debit, credit, description)
            VALUES (?, ?, ?, ?, ?)
        """, (entry_id, line["account_id"],
              line.get("debit", 0), line.get("credit", 0),
              line.get("description", "")))
    conn.commit()


def delete_entry(conn, entry_id: int):
    conn.execute("DELETE FROM journal_entries WHERE id=?", (entry_id,))
    conn.commit()


def validate_entry_balance(lines: list[dict]) -> bool:
    """يتحقق إن مجموع المدين = مجموع الدائن."""
    total_d = sum(l.get("debit", 0) for l in lines)
    total_c = sum(l.get("credit", 0) for l in lines)
    return abs(total_d - total_c) < 0.001


# ══════════════════════════════════════════════════════════
# المخزن
# ══════════════════════════════════════════════════════════

def fetch_all_inventory(conn):
    return conn.execute("""
        SELECT inv.id, inv.name, inv.unit, inv.qty_on_hand,
               inv.qty_min, inv.avg_cost, inv.notes,
               inv.item_id, inv.account_id,
               (inv.qty_on_hand * inv.avg_cost) AS total_value,
               a.name AS account_name,
               i.name AS item_name
        FROM inventory_items inv
        LEFT JOIN accounts a ON a.id = inv.account_id
        LEFT JOIN items i    ON i.id = inv.item_id
        ORDER BY inv.name
    """).fetchall()


def fetch_inventory_item(conn, inv_id: int):
    return conn.execute(
        "SELECT * FROM inventory_items WHERE id=?", (inv_id,)
    ).fetchone()


def insert_inventory_item(conn, name: str, unit: str = "قطعة",
                          qty_min: float = 0, account_id: int = None,
                          item_id: int = None, notes: str = None) -> int:
    cur = conn.execute("""
        INSERT INTO inventory_items (name, unit, qty_min, account_id, item_id, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, unit, qty_min, account_id, item_id, notes))
    conn.commit()
    return cur.lastrowid


def update_inventory_item(conn, inv_id: int, name: str, unit: str,
                          qty_min: float, account_id: int = None, notes: str = None):
    conn.execute("""
        UPDATE inventory_items
        SET name=?, unit=?, qty_min=?, account_id=?, notes=?
        WHERE id=?
    """, (name, unit, qty_min, account_id, notes, inv_id))
    conn.commit()


def delete_inventory_item(conn, inv_id: int):
    conn.execute("DELETE FROM inventory_items WHERE id=?", (inv_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# حركات المخزن
# ══════════════════════════════════════════════════════════

def fetch_inventory_moves(conn, inv_id: int):
    return conn.execute("""
        SELECT im.*, je.ref_no
        FROM inventory_moves im
        LEFT JOIN journal_entries je ON je.id = im.ref_entry_id
        WHERE im.inventory_id = ?
        ORDER BY im.date DESC, im.id DESC
    """, (inv_id,)).fetchall()


def record_inventory_move(conn, inv_id: int, move_type: str,
                          qty: float, unit_cost: float, date: str,
                          notes: str = None, ref_entry_id: int = None) -> int:
    """
    يسجل حركة مخزن ويحدث qty_on_hand و avg_cost (WACC).
    يرجع id الحركة الجديدة.
    """
    inv = fetch_inventory_item(conn, inv_id)
    if not inv:
        raise ValueError(f"صنف المخزن {inv_id} غير موجود")

    total_cost   = qty * unit_cost
    old_qty      = inv["qty_on_hand"]
    old_avg      = inv["avg_cost"]

    if move_type == "in":
        new_qty = old_qty + qty
        # متوسط التكلفة المرجح
        if new_qty > 0:
            new_avg = ((old_qty * old_avg) + total_cost) / new_qty
        else:
            new_avg = unit_cost
    elif move_type == "out":
        if qty > old_qty:
            raise ValueError(f"الكمية المطلوبة ({qty}) أكبر من الرصيد ({old_qty})")
        new_qty = old_qty - qty
        new_avg = old_avg   # متوسط التكلفة لا يتغير عند الصرف
        total_cost = qty * old_avg   # نستخدم متوسط التكلفة للتقييم
    else:  # adjust
        new_qty = qty
        new_avg = old_avg

    conn.execute("""
        UPDATE inventory_items
        SET qty_on_hand=?, avg_cost=?
        WHERE id=?
    """, (new_qty, new_avg, inv_id))

    cur = conn.execute("""
        INSERT INTO inventory_moves
            (inventory_id, move_type, qty, unit_cost, total_cost, date, ref_entry_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (inv_id, move_type, qty, unit_cost, total_cost, date, ref_entry_id, notes))
    conn.commit()
    return cur.lastrowid


# ══════════════════════════════════════════════════════════
# عملية شراء متكاملة (مخزن + قيد محاسبي)
# ══════════════════════════════════════════════════════════

def purchase_inventory(conn, inv_id: int, qty: float, unit_cost: float,
                       date: str, payment_account_id: int,
                       notes: str = None) -> tuple[int, int]:
    """
    يسجل شراء مخزن:
    1. حركة وارد في المخزن
    2. قيد محاسبي: مدين المخزون / دائن الصندوق (أو البنك أو الموردين)

    يرجع (entry_id, move_id)
    """
    inv        = fetch_inventory_item(conn, inv_id)
    total_cost = qty * unit_cost

    # ── 1. القيد المحاسبي ──
    desc = f"شراء {qty:.4g} {inv['unit']} من «{inv['name']}»"
    entry_id = insert_entry(conn, date, desc, entry_type="purchase", notes=notes)

    # مدين: حساب المخزون
    inventory_account = inv["account_id"]
    if not inventory_account:
        # حساب المخزون الافتراضي (كود 114)
        row = conn.execute("SELECT id FROM accounts WHERE code='114'").fetchone()
        inventory_account = row["id"] if row else None

    lines = [
        {"account_id": inventory_account, "debit": total_cost,  "credit": 0,          "description": desc},
        {"account_id": payment_account_id,"debit": 0,           "credit": total_cost, "description": desc},
    ]
    add_entry_lines(conn, entry_id, lines)

    # ── 2. حركة المخزن ──
    move_id = record_inventory_move(
        conn, inv_id, "in", qty, unit_cost, date,
        notes=notes, ref_entry_id=entry_id
    )

    return entry_id, move_id


# ══════════════════════════════════════════════════════════
# تقرير ميزان المراجعة
# ══════════════════════════════════════════════════════════

def trial_balance(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT a.code, a.name, a.type,
               COALESCE(SUM(jl.debit),0)  AS total_debit,
               COALESCE(SUM(jl.credit),0) AS total_credit
        FROM accounts a
        LEFT JOIN journal_lines jl ON jl.account_id = a.id
        WHERE a.is_leaf = 1
        GROUP BY a.id
        ORDER BY a.code
    """).fetchall()
    result = []
    for r in rows:
        result.append({
            "code":         r["code"],
            "name":         r["name"],
            "type":         r["type"],
            "total_debit":  r["total_debit"],
            "total_credit": r["total_credit"],
            "balance":      r["total_debit"] - r["total_credit"],
        })
    return result