"""
db/investors_repo.py
====================
نظام إدارة المستثمرين — ربط كامل مع القيود المحاسبية.
"""

from datetime import datetime


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


def _migrate_investors(conn):
    """تأكد من وجود الجداول وتحديثها."""
    try:
        conn.execute("SELECT 1 FROM investors LIMIT 1")
    except Exception:
        create_investors_tables(conn)
        return

    try:
        sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='investor_entries'"
        ).fetchone()
        if sql and "REFERENCES journal_" in sql["sql"]:
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
    _migrate_investors(conn)
    investors = fetch_all_investors(conn)
    result = []
    for inv in investors:
        s = calc_investor_summary(conn, inv["id"], acc_conn)
        result.append(s)
    result.sort(key=lambda x: x.get("net_investment", 0), reverse=True)
    return result