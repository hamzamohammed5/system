"""
db/accounting/investors_repo.py
================================
نظام إدارة المستثمرين — ربط كامل مع القيود المحاسبية.

إصلاح 30: نُقل من db/inventory/ إلى db/accounting/ لأن المستثمرين
مرتبطون بجداول journal_entries في accounting.db وليس بالمخزن.

إصلاح 31: _migrate_investors تُستدعى مرة واحدة فقط per-connection
باستخدام flag مبنية على db_path — بدل PRAGMA table_info في كل query.

إصلاح 40 (جزئي): calc_all_investors_summary تجلب كل entries دفعة واحدة
بدل query منفصلة لكل مستثمر.

تحسين 7: _get_db_path تستخدم fast path لـ ProtectedConnection
          بقراءة _path مباشرة بدل PRAGMA database_list في كل استدعاء.
          هذا يُقلّص overhead من O(PRAGMA + I/O) إلى O(1) للـ ProtectedConnection،
          مع الحفاظ على slow path للـ connections العادية.
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# Migration flag — مرة واحدة per-db-path (إصلاح 31)
# ══════════════════════════════════════════════════════════

_investors_migrated: set = set()


def _get_db_path(conn) -> str:
    """
    [تحسين 7] يستخرج مسار الـ DB من الـ connection بأكفأ طريقة ممكنة.

    Fast path — ProtectedConnection:
      يحفظ _path كـ object attribute → O(1) بدون أي I/O.
      هذا يعمل لأن ProtectedConnection يخزن المسار في __init__.

    Slow path — sqlite3.Connection العادي:
      يستخدم PRAGMA database_list → O(PRAGMA + I/O).
      يُستدعى فقط للـ connections التي لا تحتوي على _path.

    المشكلة القديمة:
      كانت كل الـ connections تمر بالـ PRAGMA في كل استدعاء
      (_migrate_investors تُستدعى من fetch_all_investors, fetch_investor,
       insert_investor, وغيرها).
    """
    # Fast path: ProtectedConnection يخزن _path كـ instance attribute
    # نستخدم object.__getattribute__ لتجنب الـ __getattr__ الـ proxy
    try:
        path = object.__getattribute__(conn, '_path')
        if path and isinstance(path, str):
            return path
    except AttributeError:
        pass

    # Slow path: sqlite3.Connection العادي أو أي connection آخر
    try:
        row = conn.execute("PRAGMA database_list").fetchone()
        return row[2] if row and len(row) > 2 else str(id(conn))
    except Exception:
        return str(id(conn))


def _migrate_investors(conn):
    """
    [إصلاح 31] تتحقق من الجداول وتُنشئها/تُحدّثها مرة واحدة فقط
    per-connection-path. الاستدعاءات التالية تعود فوراً.
    """
    path = _get_db_path(conn)
    if path in _investors_migrated:
        return

    # تحقق من وجود الجداول
    try:
        conn.execute("SELECT 1 FROM investors LIMIT 1")
    except Exception:
        create_investors_tables(conn)
        _investors_migrated.add(path)
        return

    # تحقق من شكل investor_entries — هل يحتاج migration؟
    try:
        sql_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='investor_entries'"
        ).fetchone()
        if sql_row and "REFERENCES journal_" in sql_row["sql"]:
            conn.executescript("""
                PRAGMA foreign_keys = OFF;
                CREATE TABLE IF NOT EXISTS _investor_entries_new (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    investor_id   INTEGER NOT NULL REFERENCES investors(id) ON DELETE CASCADE,
                    entry_id      INTEGER NOT NULL,
                    line_id       INTEGER NOT NULL,
                    move_type     TEXT    NOT NULL CHECK(move_type IN ('capital','drawings')),
                    amount        REAL    NOT NULL DEFAULT 0,
                    notes         TEXT,
                    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO _investor_entries_new
                    SELECT id, investor_id, entry_id, line_id, move_type, amount, notes, created_at
                    FROM investor_entries;
                DROP TABLE investor_entries;
                ALTER TABLE _investor_entries_new RENAME TO investor_entries;
                PRAGMA foreign_keys = ON;
            """)
            conn.commit()
    except Exception as e:
        print(f"[investors_repo] migration error: {e}")

    _investors_migrated.add(path)


def invalidate_investors_migration_cache(conn=None):
    """
    يُمسح الـ cache — استدعه لو احتجت إعادة فحص الـ schema.
    conn=None → يمسح كل الـ cache.
    """
    if conn is None:
        _investors_migrated.clear()
    else:
        path = _get_db_path(conn)
        _investors_migrated.discard(path)


# ══════════════════════════════════════════════════════════
# إنشاء الجداول
# ══════════════════════════════════════════════════════════

def create_investors_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS investors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            notes       TEXT,
            joined_at   TEXT    NOT NULL DEFAULT (date('now')),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS investor_entries (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_id   INTEGER NOT NULL REFERENCES investors(id) ON DELETE CASCADE,
            entry_id      INTEGER NOT NULL,
            line_id       INTEGER NOT NULL,
            move_type     TEXT    NOT NULL CHECK(move_type IN ('capital','drawings')),
            amount        REAL    NOT NULL DEFAULT 0,
            notes         TEXT,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


# ══════════════════════════════════════════════════════════
# CRUD — المستثمرون
# ══════════════════════════════════════════════════════════

def fetch_all_investors(conn) -> list:
    _migrate_investors(conn)
    return conn.execute("""
        SELECT id, name, notes, joined_at, created_at
        FROM   investors
        ORDER  BY name
    """).fetchall()


def fetch_investor(conn, investor_id: int):
    _migrate_investors(conn)
    return conn.execute(
        "SELECT * FROM investors WHERE id=?", (investor_id,)
    ).fetchone()


def insert_investor(conn, name: str, notes: str = None,
                    joined_at: str = None) -> int:
    _migrate_investors(conn)
    if not joined_at:
        joined_at = datetime.now().strftime("%Y-%m-%d")
    cur = conn.execute(
        "INSERT INTO investors (name, notes, joined_at) VALUES (?, ?, ?)",
        (name, notes or "", joined_at)
    )
    conn.commit()
    return cur.lastrowid


def update_investor(conn, investor_id: int, name: str,
                    notes: str = None, joined_at: str = None):
    _migrate_investors(conn)
    conn.execute(
        "UPDATE investors SET name=?, notes=?, joined_at=? WHERE id=?",
        (name, notes or "", joined_at, investor_id)
    )
    conn.commit()


def delete_investor(conn, investor_id: int):
    conn.execute("DELETE FROM investors WHERE id=?", (investor_id,))
    conn.commit()


def investor_exists(conn, name: str):
    _migrate_investors(conn)
    row = conn.execute(
        "SELECT id FROM investors WHERE name=?", (name,)
    ).fetchone()
    return row["id"] if row else None


# ══════════════════════════════════════════════════════════
# CRUD — ربط المستثمر بالقيود
# ══════════════════════════════════════════════════════════

def link_investor_to_line(conn, investor_id: int, entry_id: int,
                          line_id: int, move_type: str,
                          amount: float, notes: str = None) -> int:
    _migrate_investors(conn)
    cur = conn.execute("""
        INSERT INTO investor_entries
            (investor_id, entry_id, line_id, move_type, amount, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (investor_id, entry_id, line_id, move_type, amount, notes or ""))
    conn.commit()
    return cur.lastrowid


def fetch_investor_entries(conn, investor_id: int, acc_conn=None) -> list:
    """
    يجيب حركات المستثمر مع بيانات القيود من accounting.db لو موجود.
    """
    _migrate_investors(conn)

    rows = conn.execute("""
        SELECT ie.id, ie.investor_id, ie.entry_id, ie.line_id,
               ie.move_type, ie.amount, ie.notes, ie.created_at
        FROM   investor_entries ie
        WHERE  ie.investor_id = ?
        ORDER  BY ie.created_at DESC
    """, (investor_id,)).fetchall()

    result = []
    for r in rows:
        entry_id = r["entry_id"]
        line_id  = r["line_id"]
        je = jl = None

        if acc_conn:
            try:
                je = acc_conn.execute(
                    "SELECT ref_no, date, description FROM journal_entries WHERE id=?",
                    (entry_id,)
                ).fetchone()
                jl = acc_conn.execute("""
                    SELECT jl.debit, jl.credit, jl.description,
                           a.code AS account_code, a.name AS account_name,
                           a.type AS account_type
                    FROM journal_lines jl
                    JOIN accounts a ON a.id = jl.account_id
                    WHERE jl.id = ?
                """, (line_id,)).fetchone()
            except Exception:
                pass

        result.append({
            "id":           r["id"],
            "move_type":    r["move_type"],
            "amount":       r["amount"],
            "notes":        r["notes"],
            "created_at":   r["created_at"],
            "ref_no":       je["ref_no"]       if je else f"Entry#{entry_id}",
            "date":         je["date"]         if je else "—",
            "entry_desc":   je["description"]  if je else "—",
            "debit":        jl["debit"]        if jl else 0,
            "credit":       jl["credit"]       if jl else 0,
            "line_desc":    jl["description"]  if jl else "",
            "account_code": jl["account_code"] if jl else "—",
            "account_name": jl["account_name"] if jl else "—",
            "account_type": jl["account_type"] if jl else "—",
        })
    return result


def fetch_entry_investor_links(conn, entry_id: int) -> list:
    """يجيب كل المستثمرين المرتبطين بقيد معين."""
    _migrate_investors(conn)
    return conn.execute("""
        SELECT ie.*, inv.name AS investor_name
        FROM   investor_entries ie
        JOIN   investors        inv ON inv.id = ie.investor_id
        WHERE  ie.entry_id = ?
    """, (entry_id,)).fetchall()


def delete_investor_link(conn, link_id: int):
    conn.execute("DELETE FROM investor_entries WHERE id=?", (link_id,))
    conn.commit()


def delete_entry_investor_links(conn, entry_id: int):
    conn.execute("DELETE FROM investor_entries WHERE entry_id=?", (entry_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# تقارير
# ══════════════════════════════════════════════════════════

def calc_investor_summary(conn, investor_id: int, acc_conn=None) -> dict:
    _migrate_investors(conn)
    inv = fetch_investor(conn, investor_id)
    if not inv:
        return {}

    entries = fetch_investor_entries(conn, investor_id, acc_conn)
    total_capital  = sum(e["amount"] for e in entries if e["move_type"] == "capital")
    total_drawings = sum(e["amount"] for e in entries if e["move_type"] == "drawings")
    net_investment = total_capital - total_drawings

    return {
        "investor_id":    investor_id,
        "investor_name":  inv["name"],
        "joined_at":      inv["joined_at"],
        "notes":          inv["notes"],
        "total_capital":  total_capital,
        "total_drawings": total_drawings,
        "net_investment": net_investment,
        "entries":        entries,
    }


def calc_all_investors_summary(conn, acc_conn=None) -> list:
    """
    [إصلاح 40] يجلب كل investor_entries دفعة واحدة بدل query لكل مستثمر.
    يُقلّص عدد الـ queries من O(n×m) إلى O(1) + O(entries).
    """
    _migrate_investors(conn)
    investors = fetch_all_investors(conn)
    if not investors:
        return []

    # جلب كل entries دفعة واحدة
    all_entries_rows = conn.execute("""
        SELECT ie.id, ie.investor_id, ie.entry_id, ie.line_id,
               ie.move_type, ie.amount, ie.notes, ie.created_at
        FROM   investor_entries ie
        ORDER  BY ie.investor_id, ie.created_at DESC
    """).fetchall()

    # تجميع حسب investor_id
    from collections import defaultdict
    entries_by_inv: dict[int, list] = defaultdict(list)
    for row in all_entries_rows:
        entries_by_inv[row["investor_id"]].append(dict(row))

    # لو محتاجين بيانات القيود من acc_conn نجمعها دفعة واحدة
    je_cache: dict[int, dict] = {}
    jl_cache: dict[int, dict] = {}
    if acc_conn:
        all_entry_ids = list({r["entry_id"] for r in all_entries_rows})
        all_line_ids  = list({r["line_id"]  for r in all_entries_rows})

        if all_entry_ids:
            try:
                placeholders = ",".join("?" * len(all_entry_ids))
                je_rows = acc_conn.execute(
                    f"SELECT id, ref_no, date, description FROM journal_entries"
                    f" WHERE id IN ({placeholders})",
                    all_entry_ids
                ).fetchall()
                je_cache = {r["id"]: dict(r) for r in je_rows}
            except Exception:
                pass

        if all_line_ids:
            try:
                placeholders = ",".join("?" * len(all_line_ids))
                jl_rows = acc_conn.execute(
                    f"""SELECT jl.id, jl.debit, jl.credit, jl.description,
                               a.code AS account_code, a.name AS account_name,
                               a.type AS account_type
                        FROM journal_lines jl
                        JOIN accounts a ON a.id = jl.account_id
                        WHERE jl.id IN ({placeholders})""",
                    all_line_ids
                ).fetchall()
                jl_cache = {r["id"]: dict(r) for r in jl_rows}
            except Exception:
                pass

    # بناء النتائج
    result = []
    for inv in investors:
        inv_id  = inv["id"]
        raw_entries = entries_by_inv.get(inv_id, [])

        entries = []
        for r in raw_entries:
            je = je_cache.get(r["entry_id"])
            jl = jl_cache.get(r["line_id"])
            entries.append({
                "id":           r["id"],
                "move_type":    r["move_type"],
                "amount":       r["amount"],
                "notes":        r["notes"],
                "created_at":   r["created_at"],
                "ref_no":       je["ref_no"]      if je else f"Entry#{r['entry_id']}",
                "date":         je["date"]         if je else "—",
                "entry_desc":   je["description"]  if je else "—",
                "debit":        jl["debit"]        if jl else 0,
                "credit":       jl["credit"]       if jl else 0,
                "line_desc":    jl["description"]  if jl else "",
                "account_code": jl["account_code"] if jl else "—",
                "account_name": jl["account_name"] if jl else "—",
                "account_type": jl["account_type"] if jl else "—",
            })

        total_capital  = sum(e["amount"] for e in entries if e["move_type"] == "capital")
        total_drawings = sum(e["amount"] for e in entries if e["move_type"] == "drawings")

        result.append({
            "investor_id":    inv_id,
            "investor_name":  inv["name"],
            "joined_at":      inv["joined_at"],
            "notes":          inv["notes"],
            "total_capital":  total_capital,
            "total_drawings": total_drawings,
            "net_investment": total_capital - total_drawings,
            "entries":        entries,
        })

    result.sort(key=lambda x: x.get("net_investment", 0), reverse=True)
    return result