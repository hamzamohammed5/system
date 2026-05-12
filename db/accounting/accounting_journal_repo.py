"""
db/accounting_journal_repo.py
==============================
عمليات CRUD لجداول journal_entries و journal_lines.
"""

from datetime import datetime


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
# قراءة القيود
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


# ══════════════════════════════════════════════════════════
# كتابة القيود
# ══════════════════════════════════════════════════════════

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
# حسابات T (دفتر الأستاذ)
# ══════════════════════════════════════════════════════════

def fetch_t_account(conn, account_id: int) -> dict:
    from db.accounting.accounting_accounts_repo import fetch_account, get_normal_balance
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