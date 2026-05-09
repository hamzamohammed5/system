"""
db/offers_repo.py
=================
عمليات قراءة/كتابة جداول العروض.

الجداول المطلوبة (تُضاف عبر migration):
  offers      — العرض الرئيسي
  offer_items — المنتجات داخل العرض

Schema:
  offers(id, name, margin, notes, created_at)
  offer_items(id, offer_id, item_id, qty)
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════
# Migration — يُنادى مرة من run_migrations
# ══════════════════════════════════════════════════════════

def create_offers_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS offers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            margin     REAL    NOT NULL DEFAULT 30,
            notes      TEXT,
            created_at TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS offer_items (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
            item_id  INTEGER NOT NULL REFERENCES items(id)  ON DELETE CASCADE,
            qty      REAL    NOT NULL DEFAULT 1
        );
    """)
    conn.commit()


# ══════════════════════════════════════════════════════════
# CRUD — offers
# ══════════════════════════════════════════════════════════

def fetch_all_offers(conn) -> list:
    return conn.execute("""
        SELECT id, name, margin, notes, created_at
        FROM   offers
        ORDER  BY created_at DESC
    """).fetchall()


def fetch_offer(conn, offer_id: int):
    return conn.execute(
        "SELECT id, name, margin, notes, created_at FROM offers WHERE id=?",
        (offer_id,)
    ).fetchone()


def insert_offer(conn, name: str, margin: float, notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO offers (name, margin, notes, created_at) VALUES (?, ?, ?, ?)",
        (name, margin, notes or "", datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    return cur.lastrowid


def update_offer(conn, offer_id: int, name: str, margin: float, notes: str = ""):
    conn.execute(
        "UPDATE offers SET name=?, margin=?, notes=? WHERE id=?",
        (name, margin, notes or "", offer_id)
    )
    conn.commit()


def delete_offer(conn, offer_id: int):
    conn.execute("DELETE FROM offers WHERE id=?", (offer_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# CRUD — offer_items
# ══════════════════════════════════════════════════════════

def fetch_offer_items(conn, offer_id: int) -> list:
    """
    يرجع مكونات العرض مع بيانات المنتج والتكلفة.
    """
    return conn.execute("""
        SELECT oi.id, oi.offer_id, oi.item_id, oi.qty,
               i.name  AS item_name,
               i.type  AS item_type,
               c.name  AS category_name
        FROM   offer_items oi
        JOIN   items i ON i.id = oi.item_id
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE  oi.offer_id = ?
        ORDER  BY oi.id
    """, (offer_id,)).fetchall()


def replace_offer_items(conn, offer_id: int, items: list[tuple]):
    """
    items: list of (item_id, qty)
    يحذف القديم ويكتب الجديد.
    """
    conn.execute("DELETE FROM offer_items WHERE offer_id=?", (offer_id,))
    for item_id, qty in items:
        conn.execute(
            "INSERT INTO offer_items (offer_id, item_id, qty) VALUES (?, ?, ?)",
            (offer_id, item_id, qty)
        )
    conn.commit()


# ══════════════════════════════════════════════════════════
# حساب تكلفة وسعر العرض
# ══════════════════════════════════════════════════════════

def calc_offer_cost(conn, offer_id: int) -> float:
    """مجموع (تكلفة المنتج × الكمية) لكل مكونات العرض."""
    from models.costing import calc_cost
    items = fetch_offer_items(conn, offer_id)
    return sum(calc_cost(conn, row["item_id"]) * row["qty"] for row in items)


def calc_offer_price(conn, offer_id: int) -> float:
    """التكلفة الكلية × (1 + margin/100)."""
    offer = fetch_offer(conn, offer_id)
    if not offer:
        return 0.0
    cost   = calc_offer_cost(conn, offer_id)
    margin = offer["margin"] / 100.0
    return cost * (1 + margin)


def calc_offer_summary(conn, offer_id: int) -> dict:
    """ملخص كامل للعرض."""
    offer = fetch_offer(conn, offer_id)
    if not offer:
        return {}
    from models.costing import calc_cost
    items  = fetch_offer_items(conn, offer_id)
    lines  = []
    total_cost = 0.0
    for row in items:
        unit_cost = calc_cost(conn, row["item_id"])
        line_cost = unit_cost * row["qty"]
        total_cost += line_cost
        lines.append({
            "item_id":       row["item_id"],
            "item_name":     row["item_name"],
            "item_type":     row["item_type"],
            "category_name": row["category_name"],
            "qty":           row["qty"],
            "unit_cost":     unit_cost,
            "line_cost":     line_cost,
        })
    margin      = offer["margin"] / 100.0
    total_price = total_cost * (1 + margin)
    profit      = total_price - total_cost
    return {
        "offer_id":    offer_id,
        "offer_name":  offer["name"],
        "margin":      offer["margin"],
        "notes":       offer["notes"],
        "created_at":  offer["created_at"],
        "lines":       lines,
        "total_cost":  total_cost,
        "total_price": total_price,
        "profit":      profit,
    }
