"""
db/offers_repo.py
=================
عمليات قراءة/كتابة جداول العروض.

المنطق:
  - سعر المنتج في العرض = سعره من جدول pricing
  - الخصم % يتطرح من مجموع الأسعار
  - الربح = سعر البيع - إجمالي التكلفة

تحسين 14: calc_offer_summary تستخدم cost cache لتجنب حساب calc_cost
مرتين لنفس المنتج عند تكراره في العرض.
"""

from datetime import datetime


def create_offers_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS offers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            discount    REAL    NOT NULL DEFAULT 0,
            notes       TEXT,
            created_at  TEXT    NOT NULL,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS offer_items (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER NOT NULL REFERENCES offers(id)  ON DELETE CASCADE,
            item_id  INTEGER NOT NULL REFERENCES items(id)   ON DELETE CASCADE,
            qty      REAL    NOT NULL DEFAULT 1
        );
    """)
    conn.commit()
    _migrate_offers_schema(conn)


def _migrate_offers_schema(conn):
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(offers)").fetchall()}
    if "discount" not in cols:
        conn.execute("ALTER TABLE offers ADD COLUMN discount REAL NOT NULL DEFAULT 0")
        conn.commit()
    if "category_id" not in cols:
        conn.execute(
            "ALTER TABLE offers ADD COLUMN category_id INTEGER "
            "REFERENCES categories(id) ON DELETE SET NULL"
        )
        conn.commit()


# ══════════════════════════════════════════════════════════
# CRUD — offers
# ══════════════════════════════════════════════════════════

def fetch_all_offers(conn) -> list:
    return conn.execute("""
        SELECT o.id, o.name, o.discount, o.notes, o.created_at,
               o.category_id,
               c.name  AS category_name,
               c.color AS category_color
        FROM   offers o
        LEFT JOIN categories c ON c.id = o.category_id
        ORDER  BY o.created_at DESC
    """).fetchall()


def fetch_offer(conn, offer_id: int):
    return conn.execute("""
        SELECT o.id, o.name, o.discount, o.notes, o.created_at,
               o.category_id,
               c.name AS category_name
        FROM   offers o
        LEFT JOIN categories c ON c.id = o.category_id
        WHERE  o.id = ?
    """, (offer_id,)).fetchone()


def insert_offer(conn, name: str, discount: float,
                 notes: str = "", category_id: int = None) -> int:
    cur = conn.execute(
        "INSERT INTO offers (name, discount, notes, created_at, category_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (name, discount, notes or "",
         datetime.now().strftime("%Y-%m-%d %H:%M"), category_id)
    )
    conn.commit()
    return cur.lastrowid


def update_offer(conn, offer_id: int, name: str, discount: float,
                 notes: str = "", category_id: int = None):
    conn.execute(
        "UPDATE offers SET name=?, discount=?, notes=?, category_id=? WHERE id=?",
        (name, discount, notes or "", category_id, offer_id)
    )
    conn.commit()


def delete_offer(conn, offer_id: int):
    conn.execute("DELETE FROM offers WHERE id=?", (offer_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# CRUD — offer_items
# ══════════════════════════════════════════════════════════

def fetch_offer_items(conn, offer_id: int) -> list:
    return conn.execute("""
        SELECT oi.id, oi.offer_id, oi.item_id, oi.qty,
               i.name AS item_name,
               i.type AS item_type,
               c.name AS category_name
        FROM   offer_items oi
        JOIN   items i ON i.id = oi.item_id
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE  oi.offer_id = ?
        ORDER  BY oi.id
    """, (offer_id,)).fetchall()


def replace_offer_items(conn, offer_id: int, items: list[tuple]):
    conn.execute("DELETE FROM offer_items WHERE offer_id=?", (offer_id,))
    for item_id, qty in items:
        conn.execute(
            "INSERT INTO offer_items (offer_id, item_id, qty) VALUES (?, ?, ?)",
            (offer_id, item_id, qty)
        )
    conn.commit()


# ══════════════════════════════════════════════════════════
# حساب ملخص العرض
# ══════════════════════════════════════════════════════════

def calc_offer_summary(conn, offer_id: int) -> dict:
    """
    listed_price = سعر التسعير × الكمية
    sell_price   = listed_price × (1 - discount/100)
    cost         = تكلفة الإنتاج × الكمية
    profit       = sell_price - cost

    [تحسين 14] تحسب تكلفة كل item_id مرة واحدة فقط باستخدام cost_cache،
    بدلاً من استدعاء calc_cost في كل iteration حتى لو تكرر المنتج.
    هذا يُقلّص عدد الـ BOM traversals من O(n) إلى O(unique items).
    """
    offer = fetch_offer(conn, offer_id)
    if not offer:
        return {}

    from models.costing import calc_cost

    items = fetch_offer_items(conn, offer_id)

    # [تحسين 14] حساب تكلفة كل item_id فريد مرة واحدة فقط
    unique_item_ids = {row["item_id"] for row in items}
    cost_cache = {item_id: calc_cost(conn, item_id) for item_id in unique_item_ids}

    lines        = []
    total_listed = 0.0
    total_cost   = 0.0

    for row in items:
        item_id   = row["item_id"]
        qty       = row["qty"]
        unit_cost = cost_cache[item_id]   # من الـ cache — لا نعيد الحساب

        pricing_row = conn.execute(
            "SELECT price FROM pricing WHERE item_id=?", (item_id,)
        ).fetchone()
        unit_price = pricing_row["price"] if pricing_row else 0.0

        line_listed = unit_price * qty
        line_cost   = unit_cost  * qty
        total_listed += line_listed
        total_cost   += line_cost

        lines.append({
            "item_id":      item_id,
            "item_name":    row["item_name"],
            "item_type":    row["item_type"],
            "category_name":row["category_name"],
            "qty":          qty,
            "unit_cost":    unit_cost,
            "unit_price":   unit_price,
            "line_cost":    line_cost,
            "line_listed":  line_listed,
            "has_pricing":  pricing_row is not None,
        })

    discount   = offer["discount"] / 100.0
    sell_price = total_listed * (1 - discount)
    profit     = sell_price - total_cost

    return {
        "offer_id":     offer_id,
        "offer_name":   offer["name"],
        "discount":     offer["discount"],
        "notes":        offer["notes"],
        "created_at":   offer["created_at"],
        "category_name":offer["category_name"],
        "lines":        lines,
        "total_listed": total_listed,
        "sell_price":   sell_price,
        "total_cost":   total_cost,
        "profit":       profit,
    }