"""
db/accounting_accounts_repo.py
===============================
عمليات CRUD لجدول accounts وتصنيفاتها (account_groups).
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# مساعد داخلي
# ══════════════════════════════════════════════════════════

def _balance_subquery(conn) -> str:
    try:
        conn.execute("SELECT 1 FROM journal_lines LIMIT 1")
        return """(SELECT COALESCE(SUM(jl.debit)-SUM(jl.credit),0)
                   FROM journal_lines jl WHERE jl.account_id = a.id)"""
    except Exception:
        return "0"


# ══════════════════════════════════════════════════════════
# قراءة الحسابات
# ══════════════════════════════════════════════════════════

def fetch_all_accounts(conn, acc_type: str = None):
    try:
        bal_sq = _balance_subquery(conn)
        if acc_type:
            return conn.execute(f"""
                SELECT a.id, a.code, a.name, a.type, a.subtype,
                       a.parent_id, a.is_leaf, a.group_id,
                       p.name AS parent_name,
                       g.name AS group_name, g.color AS group_color,
                       {bal_sq} AS balance
                FROM accounts a
                LEFT JOIN accounts p ON p.id = a.parent_id
                LEFT JOIN account_groups g ON g.id = a.group_id
                WHERE a.type = ?
                ORDER BY a.code
            """, (acc_type,)).fetchall()
        return conn.execute(f"""
            SELECT a.id, a.code, a.name, a.type, a.subtype,
                   a.parent_id, a.is_leaf, a.group_id,
                   p.name AS parent_name,
                   g.name AS group_name, g.color AS group_color,
                   {bal_sq} AS balance
            FROM accounts a
            LEFT JOIN accounts p ON p.id = a.parent_id
            LEFT JOIN account_groups g ON g.id = a.group_id
            ORDER BY a.code
        """).fetchall()
    except Exception as e:
        print(f"[accounting_accounts_repo] fetch_all_accounts error: {e}")
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
        print(f"[accounting_accounts_repo] fetch_leaf_accounts error: {e}")
        return []


# ══════════════════════════════════════════════════════════
# كتابة الحسابات
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# أرصدة الحسابات
# ══════════════════════════════════════════════════════════

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
        return _sort_groups_parents_first(rows)
    except Exception as e:
        print(f"[accounting_accounts_repo] fetch_all_groups error: {e}")
        return []


def _sort_groups_parents_first(rows) -> list:
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