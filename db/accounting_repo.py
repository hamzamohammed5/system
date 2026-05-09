"""
db/accounting_repo.py (محدَّث)
================================
عمليات قراءة/كتابة جداول الحسابات في accounting.db.
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


def fetch_account_by_code(conn, code: str):
    return conn.execute(
        "SELECT * FROM accounts WHERE code=?", (code,)
    ).fetchone()


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
    row = conn.execute("""
        SELECT COALESCE(SUM(debit)-SUM(credit), 0) AS bal
        FROM journal_lines WHERE account_id=?
    """, (account_id,)).fetchone()
    return row["bal"] if row else 0.0


def get_balances_by_type(conn) -> dict:
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
# تقرير ميزان المراجعة
# ══════════════════════════════════════════════════════════

def trial_balance(conn) -> list:
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