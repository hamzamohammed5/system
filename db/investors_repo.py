"""
db/investors_repo.py
=====================
عمليات قراءة/كتابة جداول المستثمرين في accounting.db.

الجداول:
  investors          — بيانات المستثمر (الاسم، الوصف، تاريخ الانضمام)
  investor_entries   — ربط المستثمر بصفوف القيود (journal_lines)
                       كل صف قيد يُنسب لمستثمر معين (capital أو drawings)

المنطق:
  صافي استثمار المستثمر = مجموع Capital - مجموع Drawings
  Capital  = صفوف CR على حسابات capital مرتبطة بالمستثمر
  Drawings = صفوف DR على حسابات drawings مرتبطة بالمستثمر
"""

from datetime import datetime


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
            entry_id      INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
            line_id       INTEGER NOT NULL REFERENCES journal_lines(id) ON DELETE CASCADE,
            move_type     TEXT    NOT NULL CHECK(move_type IN ('capital','drawings')),
            amount        REAL    NOT NULL DEFAULT 0,
            notes         TEXT,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


def _migrate_investors(conn):
    """تأكد من وجود الجداول عند أي استدعاء."""
    try:
        conn.execute("SELECT 1 FROM investors LIMIT 1")
    except Exception:
        create_investors_tables(conn)


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


def investor_exists(conn, name: str) -> int | None:
    """يرجع id المستثمر لو موجود، أو None."""
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
    """يربط مستثمر بصف قيد محدد."""
    _migrate_investors(conn)
    cur = conn.execute("""
        INSERT INTO investor_entries
            (investor_id, entry_id, line_id, move_type, amount, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (investor_id, entry_id, line_id, move_type, amount, notes or ""))
    conn.commit()
    return cur.lastrowid


def fetch_investor_entries(conn, investor_id: int) -> list:
    """كل القيود المرتبطة بمستثمر معين."""
    _migrate_investors(conn)
    return conn.execute("""
        SELECT ie.id, ie.move_type, ie.amount, ie.notes, ie.created_at,
               je.ref_no, je.date, je.description AS entry_desc,
               jl.debit, jl.credit, jl.description AS line_desc,
               a.code AS account_code, a.name AS account_name, a.type AS account_type
        FROM   investor_entries ie
        JOIN   journal_entries  je ON je.id = ie.entry_id
        JOIN   journal_lines    jl ON jl.id = ie.line_id
        JOIN   accounts         a  ON a.id  = jl.account_id
        WHERE  ie.investor_id = ?
        ORDER  BY je.date DESC, je.id DESC
    """, (investor_id,)).fetchall()


def fetch_entry_investor_links(conn, entry_id: int) -> list:
    """كل الروابط لقيد معين."""
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
    """يحذف كل روابط قيد معين."""
    conn.execute("DELETE FROM investor_entries WHERE entry_id=?", (entry_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# تقرير المستثمر
# ══════════════════════════════════════════════════════════

def calc_investor_summary(conn, investor_id: int) -> dict:
    """
    يحسب ملخص استثمار مستثمر واحد.

    Returns:
        total_capital  : إجمالي ما دفعه كـ capital
        total_drawings : إجمالي المسحوبات
        net_investment : total_capital - total_drawings
        entries        : قائمة الحركات مفصلة
    """
    _migrate_investors(conn)
    inv = fetch_investor(conn, investor_id)
    if not inv:
        return {}

    entries = fetch_investor_entries(conn, investor_id)

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
        "entries":        [dict(e) for e in entries],
    }


def calc_all_investors_summary(conn) -> list:
    """ملخص جميع المستثمرين مرتبين بالاستثمار الصافي تنازلياً."""
    _migrate_investors(conn)
    investors = fetch_all_investors(conn)
    result = []
    for inv in investors:
        s = calc_investor_summary(conn, inv["id"])
        result.append(s)
    result.sort(key=lambda x: x.get("net_investment", 0), reverse=True)
    return result