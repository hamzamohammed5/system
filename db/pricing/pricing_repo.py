"""
db/pricing_repo.py
==================
عمليات قراءة/كتابة جدول pricing.
كل منتج نهائي ممكن يكون له سعر = margin × cost
"""


def fetch_all_pricing(conn):
    """
    يرجع كل المنتجات النهائية مع بيانات التسعير (لو موجودة).
    """
    return conn.execute("""
        SELECT
            i.id,
            i.name,
            i.category_id,
            c.name  AS category_name,
            c.color AS category_color,
            p.id    AS pricing_id,
            p.margin,
            p.price
        FROM items i
        LEFT JOIN pricing  p ON p.item_id = i.id
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE i.type = 'final'
        ORDER BY i.name
    """).fetchall()


def fetch_pricing(conn, item_id: int):
    return conn.execute(
        "SELECT id, item_id, margin, price FROM pricing WHERE item_id=?",
        (item_id,)
    ).fetchone()


def upsert_pricing(conn, item_id: int, margin: float, price: float):
    """حفظ أو تحديث سعر منتج."""
    conn.execute("""
        INSERT INTO pricing (item_id, margin, price)
        VALUES (?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET margin=excluded.margin, price=excluded.price
    """, (item_id, margin, price))
    conn.commit()


def delete_pricing(conn, item_id: int):
    conn.execute("DELETE FROM pricing WHERE item_id=?", (item_id,))
    conn.commit()
