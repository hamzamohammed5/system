"""
db/accounting/accounting_accounts_repo.py
===============================
عمليات CRUD لجدول accounts وتصنيفاتها (account_groups).

تحسين 38: fetch_all_accounts تستخدم LEFT JOIN + GROUP BY بدل correlated subquery
لكل حساب. هذا يقلل عدد الـ queries من O(n) إلى O(1).

تحسين 3:
  _sort_groups_parents_first مُحسَّنة لتتجنب إنشاء O(3n) structures:
  النسخة القديمة: dict(r) لكل صف + id_map + result list = 3 copies.
  النسخة الجديدة: تحويل لـ dicts مرة واحدة + id_map يُشير لنفس الـ objects.
  الفرق في الذاكرة: O(n) بدل O(3n) للـ dicts.

[P-01] تقسيم fetch_all_accounts إلى دالتين:
  - fetch_all_accounts_basic()       → بدون balance (سريعة للـ dropdowns)
  - fetch_all_accounts_with_balance() → مع balance (للتقارير والقوائم المالية)
  - fetch_all_accounts()             → يُبقى للتوافق = يستدعي النسخة الكاملة
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# قراءة الحسابات
# ══════════════════════════════════════════════════════════

def fetch_all_accounts_basic(conn, acc_type: str = None):
    """
    [P-01] يجلب الحسابات بدون حساب الأرصدة — سريعة للـ dropdowns والـ combos.

    استخدمها عند:
      - ملء combo اختيار الحساب في الـ journal entry
      - عرض شجرة الحسابات بدون أرصدة
      - أي مكان يحتاج قائمة الحسابات فقط

    أسرع بكثير من fetch_all_accounts_with_balance() لأنها
    لا تحتاج JOIN مع journal_lines ولا GROUP BY.
    """
    try:
        if acc_type:
            return conn.execute("""
                SELECT a.id, a.code, a.name, a.type, a.subtype,
                       a.parent_id, a.is_leaf, a.group_id,
                       p.name AS parent_name,
                       g.name AS group_name, g.color AS group_color
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
                   g.name AS group_name, g.color AS group_color
            FROM accounts a
            LEFT JOIN accounts p ON p.id = a.parent_id
            LEFT JOIN account_groups g ON g.id = a.group_id
            ORDER BY a.code
        """).fetchall()
    except Exception as e:
        print(f"[accounting_accounts_repo] fetch_all_accounts_basic error: {e}")
        return []


def fetch_all_accounts_with_balance(conn, acc_type: str = None):
    """
    [P-01] يجلب الحسابات مع أرصدتها — للتقارير والقوائم المالية فقط.

    استخدمها عند:
      - ميزان المراجعة
      - عرض الحسابات مع أرصدتها الحالية
      - أي تقرير يحتاج balance

    أبطأ من fetch_all_accounts_basic() بسبب LEFT JOIN + GROUP BY
    مع journal_lines — تجنب استخدامها في الـ dropdowns.

    [تحسين 38] تستخدم LEFT JOIN بدل correlated subquery لكل حساب.
    """
    try:
        if acc_type:
            return conn.execute("""
                SELECT a.id, a.code, a.name, a.type, a.subtype,
                       a.parent_id, a.is_leaf, a.group_id,
                       p.name AS parent_name,
                       g.name AS group_name, g.color AS group_color,
                       COALESCE(SUM(jl.debit) - SUM(jl.credit), 0) AS balance
                FROM accounts a
                LEFT JOIN accounts p ON p.id = a.parent_id
                LEFT JOIN account_groups g ON g.id = a.group_id
                LEFT JOIN journal_lines jl ON jl.account_id = a.id
                WHERE a.type = ?
                GROUP BY a.id, a.code, a.name, a.type, a.subtype,
                         a.parent_id, a.is_leaf, a.group_id,
                         p.name, g.name, g.color
                ORDER BY a.code
            """, (acc_type,)).fetchall()

        return conn.execute("""
            SELECT a.id, a.code, a.name, a.type, a.subtype,
                   a.parent_id, a.is_leaf, a.group_id,
                   p.name AS parent_name,
                   g.name AS group_name, g.color AS group_color,
                   COALESCE(SUM(jl.debit) - SUM(jl.credit), 0) AS balance
            FROM accounts a
            LEFT JOIN accounts p ON p.id = a.parent_id
            LEFT JOIN account_groups g ON g.id = a.group_id
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            GROUP BY a.id, a.code, a.name, a.type, a.subtype,
                     a.parent_id, a.is_leaf, a.group_id,
                     p.name, g.name, g.color
            ORDER BY a.code
        """).fetchall()
    except Exception as e:
        print(f"[accounting_accounts_repo] fetch_all_accounts_with_balance error: {e}")
        return []


def fetch_all_accounts(conn, acc_type: str = None):
    """
    يجلب كل الحسابات مع أرصدتها.

    [P-01] للتوافق مع الكود القديم — يُفوَّض لـ fetch_all_accounts_with_balance.
    الكود الجديد يستخدم:
      - fetch_all_accounts_basic()       للـ dropdowns والـ combos
      - fetch_all_accounts_with_balance() للتقارير

    [تحسين 38] يستخدم LEFT JOIN بدل correlated subquery لكل حساب.
    هذا أسرع بكثير عند وجود آلاف القيود.
    """
    return fetch_all_accounts_with_balance(conn, acc_type)


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
    """
    يُرتب المجموعات بحيث يظهر الأب قبل أبنائه دائماً.

    [تحسين 3] تحسين استخدام الذاكرة:
    النسخة القديمة: تحويل كل صف لـ dict مرة لـ rows_list، ثم نسخة أخرى لـ id_map.
    النسخة الجديدة:
      - تحويل لـ dicts مرة واحدة فقط في rows_list.
      - id_map يُشير لنفس الـ dict objects (لا نسخ جديدة).
    الفرق: O(3n) dicts → O(n) dicts.
    """
    rows_list = [dict(r) for r in rows]
    id_map = {r["id"]: r for r in rows_list}

    result: list = []
    visited: set = set()

    def visit(node: dict):
        nid = node["id"]
        if nid in visited:
            return
        pid = node.get("parent_id")
        if pid and pid in id_map and pid not in visited:
            visit(id_map[pid])
        visited.add(nid)
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
    """
    Private — لا تستورد من هنا مباشرة في الكود الجديد.
    استخدمها عبر: from db.accounting.accounting_accounts_repo import _get_group_descendants
    """
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
    """
    يبني شجرة من قائمة مجموعات الحسابات.

    [تحسين 3] نفس تحسين _sort_groups_parents_first:
    id_map يُشير لنفس الـ dict objects بدل نسخ إضافية.
    """
    nodes: dict = {}
    for r in rows:
        d = r if isinstance(r, dict) else dict(r)
        nodes[d["id"]] = {
            "id":        d["id"],
            "name":      d["name"],
            "acc_type":  d.get("acc_type", ""),
            "parent_id": d.get("parent_id"),
            "color":     d.get("color", "#607d8b"),
            "children":  [],
        }

    roots: list = []
    for node in nodes.values():
        pid = node["parent_id"]
        if pid and pid in nodes:
            nodes[pid]["children"].append(node)
        else:
            roots.append(node)
    return roots
