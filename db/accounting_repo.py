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
# القيود المحاسبية
# ══════════════════════════════════════════════════════════

def fetch_all_entries(conn, limit: int = 200):
    return conn.execute("""
        SELECT je.id, je.ref_no, je.date, je.description,
               je.type, je.status, je.notes, je.created_at,
               (SELECT COALESCE(SUM(debit),0)  FROM journal_lines WHERE entry_id=je.id) AS total_debit,
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
# ميزان المراجعة
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


# ══════════════════════════════════════════════════════════
# القوائم المالية
# ══════════════════════════════════════════════════════════

def income_statement(conn) -> dict:
    """قائمة الدخل: الإيرادات - المصروفات = صافي الربح."""
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

    total_rev = sum(r["amount"] for r in rev_rows)
    total_exp = sum(r["amount"] for r in exp_rows)
    net_income = total_rev - total_exp

    return {
        "revenues":    [dict(r) for r in rev_rows],
        "expenses":    [dict(r) for r in exp_rows],
        "total_rev":   total_rev,
        "total_exp":   total_exp,
        "net_income":  net_income,
    }


def balance_sheet(conn) -> dict:
    """الميزانية العمومية: الأصول = الخصوم + حقوق الملكية."""
    def _fetch(acc_type):
        return conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = ? AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """, (acc_type,)).fetchall()

    assets     = _fetch("asset")
    liab       = _fetch("liability")
    equity_acc = _fetch("equity")

    inc = income_statement(conn)
    net_income = inc["net_income"]

    total_assets = sum(r["amount"] for r in assets)
    total_liab   = sum(r["amount"] for r in liab)
    total_equity = sum(r["amount"] for r in equity_acc) + net_income

    return {
        "assets":        [dict(r) for r in assets],
        "liabilities":   [dict(r) for r in liab],
        "equity":        [dict(r) for r in equity_acc],
        "net_income":    net_income,
        "total_assets":  total_assets,
        "total_liab":    total_liab,
        "total_equity":  total_equity,
    }


def owners_equity_statement(conn) -> dict:
    """قائمة حقوق الملكية."""
    rows = conn.execute("""
        SELECT a.code, a.name,
               COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
        FROM accounts a
        LEFT JOIN journal_lines jl ON jl.account_id = a.id
        WHERE a.type = 'equity' AND a.is_leaf = 1
        GROUP BY a.id ORDER BY a.code
    """).fetchall()

    inc = income_statement(conn)
    net_income   = inc["net_income"]
    total_equity = sum(r["amount"] for r in rows) + net_income

    return {
        "accounts":    [dict(r) for r in rows],
        "net_income":  net_income,
        "total":       total_equity,
    }


# ══════════════════════════════════════════════════════════
# حسابات T (دفتر الأستاذ)
# ══════════════════════════════════════════════════════════

def fetch_t_account(conn, account_id: int) -> dict:
    """يرجع كل حركات حساب معين للعرض كـ T-Account."""
    acc = fetch_account(conn, account_id)
    if not acc:
        return {}

    lines = conn.execute("""
        SELECT jl.id, jl.debit, jl.credit, jl.description,
               je.ref_no, je.date, je.description AS entry_desc
        FROM journal_lines jl
        JOIN journal_entries je ON je.id = jl.entry_id
        WHERE jl.account_id = ?
        ORDER BY je.date, je.id
    """, (account_id,)).fetchall()

    total_debit  = sum(l["debit"]  for l in lines)
    total_credit = sum(l["credit"] for l in lines)
    balance      = total_debit - total_credit

    return {
        "account":       dict(acc),
        "lines":         [dict(l) for l in lines],
        "total_debit":   total_debit,
        "total_credit":  total_credit,
        "balance":       balance,
    }


# ══════════════════════════════════════════════════════════
# عملية شراء مخزن مع قيد محاسبي (للاستخدام من inventory)
# ══════════════════════════════════════════════════════════

def purchase_inventory(inv_conn, acc_conn,
                       inv_id: int, qty: float, unit_cost: float,
                       date: str, payment_account_id: int,
                       notes: str = None) -> tuple:
    """
    يسجل شراء في المخزن وينشئ قيد محاسبي.
    يرجع (entry_id, move_id).
    """
    from db.inventory_repo import fetch_inventory_item, record_inventory_move

    inv = fetch_inventory_item(inv_conn, inv_id)
    if not inv:
        raise ValueError(f"الصنف {inv_id} غير موجود")

    total_cost = qty * unit_cost
    inv_name   = inv["name"]
    inv_unit   = inv["unit"]
    acc_code   = inv.get("account_code") or "114"

    # القيد
    desc     = f"شراء {qty:.4g} {inv_unit} من «{inv_name}»"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="purchase", notes=notes)

    # حساب المخزون
    inv_account = fetch_account_by_code(acc_conn, acc_code)
    inv_acc_id  = inv_account["id"] if inv_account else None
    if not inv_acc_id:
        row = acc_conn.execute(
            "SELECT id FROM accounts WHERE subtype='inventory' AND is_leaf=1 LIMIT 1"
        ).fetchone()
        inv_acc_id = row["id"] if row else None

    lines = [
        {"account_id": inv_acc_id,        "debit": total_cost, "credit": 0,
         "description": desc},
        {"account_id": payment_account_id, "debit": 0, "credit": total_cost,
         "description": desc},
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