"""
db/accounting_repo.py
======================
عمليات قراءة/كتابة جداول الحسابات في accounting.db.
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# شجرة الحسابات
# ══════════════════════════════════════════════════════════

def fetch_all_accounts(conn, acc_type: str = None):
    try:
        if acc_type:
            return conn.execute("""
                SELECT a.id, a.code, a.name, a.type, a.subtype,
                       a.parent_id, a.is_leaf, a.group_id,
                       p.name AS parent_name,
                       g.name AS group_name, g.color AS group_color,
                       (SELECT COALESCE(SUM(jl.debit)-SUM(jl.credit),0)
                        FROM journal_lines jl WHERE jl.account_id = a.id) AS balance
                FROM accounts a
                LEFT JOIN accounts p ON p.id = a.parent_id
                LEFT JOIN account_groups g ON g.id = a.group_id
                WHERE a.type = ?
                ORDER BY a.code
            """, (acc_type,)).fetchall()
        return conn.execute("""
            SELECT a.id, a.code, a.name, a.type, a.subtype,
                   a.parent_id, a.is_leaf, a.group_id,
                   p.name AS parent_name,
                   g.name AS group_name, g.color AS group_color,
                   (SELECT COALESCE(SUM(jl.debit)-SUM(jl.credit),0)
                    FROM journal_lines jl WHERE jl.account_id = a.id) AS balance
            FROM accounts a
            LEFT JOIN accounts p ON p.id = a.parent_id
            LEFT JOIN account_groups g ON g.id = a.group_id
            ORDER BY a.code
        """).fetchall()
    except Exception as e:
        print(f"[accounting_repo] fetch_all_accounts error: {e}")
        return []


def fetch_account(conn, account_id: int):
    try:
        return conn.execute("""
            SELECT a.*, p.name AS parent_name,
                   g.name AS group_name, g.color AS group_color
            FROM accounts a
            LEFT JOIN accounts p ON p.id = a.parent_id
            LEFT JOIN account_groups g ON g.id = a.group_id
            WHERE a.id = ?
        """, (account_id,)).fetchone()
    except Exception:
        return None


def fetch_account_by_code(conn, code: str):
    try:
        return conn.execute(
            "SELECT * FROM accounts WHERE code=?", (code,)
        ).fetchone()
    except Exception:
        return None


def fetch_leaf_accounts(conn, acc_type: str = None):
    """الحسابات النهائية فقط (قابلة للترحيل)."""
    try:
        if acc_type:
            return conn.execute("""
                SELECT id, code, name, type,
                       COALESCE(subtype, '') AS subtype,
                       group_id
                FROM accounts WHERE is_leaf=1 AND type=?
                ORDER BY code
            """, (acc_type,)).fetchall()
        return conn.execute("""
            SELECT id, code, name, type,
                   COALESCE(subtype, '') AS subtype,
                   group_id
            FROM accounts WHERE is_leaf=1
            ORDER BY code
        """).fetchall()
    except Exception as e:
        print(f"[accounting_repo] fetch_leaf_accounts error: {e}")
        return []


def insert_account(conn, code: str, name: str, acc_type: str,
                   parent_id: int = None, group_id: int = None,
                   subtype: str = None, notes: str = None) -> int:
    if parent_id:
        conn.execute("UPDATE accounts SET is_leaf=0 WHERE id=?", (parent_id,))
    cur = conn.execute("""
        INSERT INTO accounts (code, name, type, subtype, parent_id, is_leaf, group_id, notes)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
    """, (code, name, acc_type, subtype, parent_id, group_id, notes))
    conn.commit()
    return cur.lastrowid


def update_account(conn, account_id: int, name: str,
                   group_id: int = None, notes: str = None):
    conn.execute(
        "UPDATE accounts SET name=?, group_id=?, notes=? WHERE id=?",
        (name, group_id, notes, account_id)
    )
    conn.commit()


def delete_account(conn, account_id: int):
    conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    conn.commit()


def get_account_balance(conn, account_id: int) -> float:
    try:
        row = conn.execute("""
            SELECT COALESCE(SUM(debit)-SUM(credit), 0) AS bal
            FROM journal_lines WHERE account_id=?
        """, (account_id,)).fetchone()
        return row["bal"] if row else 0.0
    except Exception:
        return 0.0


def get_account_natural_balance(conn, account_id: int) -> float:
    acc = fetch_account(conn, account_id)
    if not acc:
        return 0.0
    bal = get_account_balance(conn, account_id)
    nb  = get_normal_balance(acc["type"])
    return bal if nb == "dr" else -bal


def get_normal_balance(acc_type: str) -> str:
    return "dr" if acc_type in ("asset", "expense", "drawings") else "cr"


def calc_signed_amount(acc_type: str, increase: bool, amount: float) -> tuple:
    nb = get_normal_balance(acc_type)
    if nb == "dr":
        return (amount, 0.0) if increase else (0.0, amount)
    else:
        return (0.0, amount) if increase else (amount, 0.0)


def get_balances_by_type(conn) -> dict:
    try:
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
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════
# تصنيفات الحسابات (account_groups)
# ══════════════════════════════════════════════════════════

def fetch_all_groups(conn, acc_type: str = None):
    """
    يرجع كل التصنيفات — بدون NULLS FIRST للتوافق مع SQLite القديم.
    """
    try:
        if acc_type:
            rows = conn.execute("""
                SELECT id, name, acc_type, parent_id,
                       COALESCE(color, '#607d8b') AS color,
                       COALESCE(notes, '') AS notes
                FROM account_groups
                WHERE acc_type=?
                ORDER BY name
            """, (acc_type,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, name, acc_type, parent_id,
                       COALESCE(color, '#607d8b') AS color,
                       COALESCE(notes, '') AS notes
                FROM account_groups
                ORDER BY acc_type, name
            """).fetchall()
        # ترتيب الآباء قبل الأبناء يدوياً
        return _sort_groups_parents_first(rows)
    except Exception as e:
        print(f"[accounting_repo] fetch_all_groups error: {e}")
        return []


def _sort_groups_parents_first(rows) -> list:
    """يرتب الصفوف بحيث الآباء يجيوا قبل أبناءهم."""
    rows_list = [dict(r) for r in rows]
    id_map = {r["id"]: r for r in rows_list}
    result = []
    visited = set()

    def visit(node):
        if node["id"] in visited:
            return
        pid = node.get("parent_id")
        if pid and pid in id_map and pid not in visited:
            visit(id_map[pid])
        visited.add(node["id"])
        result.append(node)

    for r in rows_list:
        visit(r)
    return result


def fetch_group(conn, group_id: int):
    try:
        return conn.execute(
            "SELECT * FROM account_groups WHERE id=?", (group_id,)
        ).fetchone()
    except Exception:
        return None


def insert_group(conn, name: str, acc_type: str,
                 parent_id: int = None, color: str = "#607d8b") -> int:
    cur = conn.execute(
        "INSERT INTO account_groups (name, acc_type, parent_id, color) VALUES (?, ?, ?, ?)",
        (name, acc_type, parent_id, color)
    )
    conn.commit()
    return cur.lastrowid


def update_group(conn, group_id: int, name: str,
                 parent_id: int = None, color: str = "#607d8b"):
    conn.execute(
        "UPDATE account_groups SET name=?, parent_id=?, color=? WHERE id=?",
        (name, parent_id, color, group_id)
    )
    conn.commit()


def delete_group(conn, group_id: int):
    conn.execute("UPDATE accounts SET group_id=NULL WHERE group_id=?", (group_id,))
    conn.execute("DELETE FROM account_groups WHERE id=?", (group_id,))
    conn.commit()


def _get_group_descendants(conn, group_id: int) -> set:
    result = set()
    queue  = [group_id]
    while queue:
        current = queue.pop()
        if current in result:
            continue
        result.add(current)
        try:
            children = conn.execute(
                "SELECT id FROM account_groups WHERE parent_id=?", (current,)
            ).fetchall()
            queue.extend(r["id"] for r in children)
        except Exception:
            break
    return result


def build_group_tree(rows) -> list:
    nodes = {}
    for r in rows:
        if isinstance(r, dict):
            d = r
        else:
            d = dict(r)
        nodes[d["id"]] = {
            "id":       d["id"],
            "name":     d["name"],
            "acc_type": d.get("acc_type", ""),
            "parent_id":d.get("parent_id"),
            "color":    d.get("color", "#607d8b"),
            "children": [],
        }
    roots = []
    for node in nodes.values():
        pid = node["parent_id"]
        if pid and pid in nodes:
            nodes[pid]["children"].append(node)
        else:
            roots.append(node)
    return roots


# ══════════════════════════════════════════════════════════
# رقم القيد التلقائي
# ══════════════════════════════════════════════════════════

def next_ref_no(conn) -> str:
    try:
        row = conn.execute(
            "SELECT MAX(CAST(SUBSTR(ref_no,4) AS INTEGER)) AS mx FROM journal_entries"
        ).fetchone()
        n = (row["mx"] or 0) + 1
    except Exception:
        n = 1
    return f"JE-{n:05d}"


# ══════════════════════════════════════════════════════════
# القيود المحاسبية
# ══════════════════════════════════════════════════════════

def fetch_all_entries(conn, limit: int = 200):
    try:
        return conn.execute("""
            SELECT je.id, je.ref_no, je.date, je.description,
                   je.type, je.status, je.notes, je.created_at,
                   (SELECT COALESCE(SUM(debit),0)  FROM journal_lines WHERE entry_id=je.id) AS total_debit,
                   (SELECT COALESCE(SUM(credit),0) FROM journal_lines WHERE entry_id=je.id) AS total_credit
            FROM journal_entries je
            ORDER BY je.date DESC, je.id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    except Exception:
        return []


def fetch_entry(conn, entry_id: int):
    try:
        return conn.execute(
            "SELECT * FROM journal_entries WHERE id=?", (entry_id,)
        ).fetchone()
    except Exception:
        return None


def fetch_entry_lines(conn, entry_id: int):
    try:
        return conn.execute("""
            SELECT jl.id, jl.account_id, jl.debit, jl.credit, jl.description,
                   a.code AS account_code, a.name AS account_name, a.type AS account_type
            FROM journal_lines jl
            JOIN accounts a ON a.id = jl.account_id
            WHERE jl.entry_id = ?
            ORDER BY jl.id
        """, (entry_id,)).fetchall()
    except Exception:
        return []


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


def add_entry_lines(conn, entry_id: int, lines: list):
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


def validate_entry_balance(lines: list) -> bool:
    total_d = sum(l.get("debit", 0) for l in lines)
    total_c = sum(l.get("credit", 0) for l in lines)
    return abs(total_d - total_c) < 0.001


# ══════════════════════════════════════════════════════════
# ميزان المراجعة
# ══════════════════════════════════════════════════════════

def trial_balance(conn) -> list:
    try:
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
    except Exception:
        return []


# ══════════════════════════════════════════════════════════
# القوائم المالية
# ══════════════════════════════════════════════════════════

def income_statement(conn) -> dict:
    try:
        rev_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.credit)-SUM(jl.debit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'revenue' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()

        exp_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'expense' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()
    except Exception:
        rev_rows, exp_rows = [], []

    total_rev  = sum(r["amount"] for r in rev_rows)
    total_exp  = sum(r["amount"] for r in exp_rows)
    net_income = total_rev - total_exp

    return {
        "revenues":   [dict(r) for r in rev_rows],
        "expenses":   [dict(r) for r in exp_rows],
        "total_rev":  total_rev,
        "total_exp":  total_exp,
        "net_income": net_income,
    }


def balance_sheet(conn) -> dict:
    def _fetch(acc_type):
        try:
            return conn.execute("""
                SELECT a.code, a.name,
                       COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
                FROM accounts a
                LEFT JOIN journal_lines jl ON jl.account_id = a.id
                WHERE a.type = ? AND a.is_leaf = 1
                GROUP BY a.id ORDER BY a.code
            """, (acc_type,)).fetchall()
        except Exception:
            return []

    assets   = _fetch("asset")
    liab     = _fetch("liability")
    capital  = _fetch("capital")
    drawings = _fetch("drawings")

    inc        = income_statement(conn)
    net_income = inc["net_income"]

    total_assets  = sum(r["amount"] for r in assets)
    total_liab    = sum(r["amount"] for r in liab)
    total_capital = sum(r["amount"] for r in capital)
    total_draw    = sum(r["amount"] for r in drawings)
    total_equity  = total_capital - total_draw + net_income

    return {
        "assets":        [dict(r) for r in assets],
        "liabilities":   [dict(r) for r in liab],
        "capital":       [dict(r) for r in capital],
        "drawings":      [dict(r) for r in drawings],
        "net_income":    net_income,
        "total_assets":  total_assets,
        "total_liab":    total_liab,
        "total_equity":  total_equity,
    }


def owners_equity_statement(conn) -> dict:
    try:
        capital_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.credit)-SUM(jl.debit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'capital' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()

        drawings_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'drawings' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()
    except Exception:
        capital_rows, drawings_rows = [], []

    inc           = income_statement(conn)
    net_income    = inc["net_income"]
    total_capital = sum(r["amount"] for r in capital_rows)
    total_draw    = sum(r["amount"] for r in drawings_rows)
    total_equity  = total_capital - total_draw + net_income

    return {
        "capital_accounts":  [dict(r) for r in capital_rows],
        "drawings_accounts": [dict(r) for r in drawings_rows],
        "net_income":        net_income,
        "total_capital":     total_capital,
        "total_drawings":    total_draw,
        "total_equity":      total_equity,
    }


# ══════════════════════════════════════════════════════════
# حسابات T (دفتر الأستاذ)
# ══════════════════════════════════════════════════════════

def fetch_t_account(conn, account_id: int) -> dict:
    acc = fetch_account(conn, account_id)
    if not acc:
        return {}

    try:
        lines = conn.execute("""
            SELECT jl.id, jl.debit, jl.credit, jl.description,
                   je.ref_no, je.date, je.description AS entry_desc
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.entry_id
            WHERE jl.account_id = ?
            ORDER BY je.date, je.id
        """, (account_id,)).fetchall()
    except Exception:
        lines = []

    total_debit  = sum(l["debit"]  for l in lines)
    total_credit = sum(l["credit"] for l in lines)
    balance      = total_debit - total_credit
    nb           = get_normal_balance(acc["type"])

    return {
        "account":        dict(acc),
        "lines":          [dict(l) for l in lines],
        "total_debit":    total_debit,
        "total_credit":   total_credit,
        "balance":        balance,
        "normal_balance": nb,
    }


# ══════════════════════════════════════════════════════════
# عملية شراء مخزن مع قيد محاسبي
# ══════════════════════════════════════════════════════════

def purchase_inventory(inv_conn, acc_conn,
                       inv_id: int, qty: float, unit_cost: float,
                       date: str, payment_account_id: int,
                       notes: str = None) -> tuple:
    from db.inventory_repo import fetch_inventory_item, record_inventory_move

    inv = fetch_inventory_item(inv_conn, inv_id)
    if not inv:
        raise ValueError(f"الصنف {inv_id} غير موجود")

    total_cost = qty * unit_cost
    inv_name   = inv["name"]
    inv_unit   = inv["unit"]
    acc_code   = inv.get("account_code") or "114"

    desc     = f"شراء {qty:.4g} {inv_unit} من «{inv_name}»"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="purchase", notes=notes)

    inv_account = fetch_account_by_code(acc_conn, acc_code)
    inv_acc_id  = inv_account["id"] if inv_account else None
    if not inv_acc_id:
        row = acc_conn.execute(
            "SELECT id FROM accounts WHERE subtype='inventory' AND is_leaf=1 LIMIT 1"
        ).fetchone()
        inv_acc_id = row["id"] if row else None

    lines = [
        {"account_id": inv_acc_id,         "debit": total_cost, "credit": 0,          "description": desc},
        {"account_id": payment_account_id,  "debit": 0,          "credit": total_cost, "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)

    entry_row = acc_conn.execute(
        "SELECT ref_no FROM journal_entries WHERE id=?", (entry_id,)
    ).fetchone()
    ref_no = entry_row["ref_no"] if entry_row else None

    move_id = record_inventory_move(
        inv_conn, inv_id, "in", qty, unit_cost, date,
        notes=notes, ref_entry_id=entry_id, ref_entry_no=ref_no
    )
    return entry_id, move_id