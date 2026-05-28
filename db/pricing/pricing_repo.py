"""
db/pricing_repo.py
==================
عمليات قراءة/كتابة جدول pricing.
كل منتج نهائي ممكن يكون له سعر = margin × cost

تحسين 23: upsert_pricing يتحقق من نوع المنتج قبل الحفظ.
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
    """
    حفظ أو تحديث سعر منتج.

    [تحسين 23] يتحقق أن المنتج موجود ونوعه 'final' قبل الحفظ.
    التسعير مخصص للمنتجات النهائية فقط — الخامات والنصف مصنع لا تُسعَّر هنا.
    """
    item = conn.execute(
        "SELECT type FROM items WHERE id=?", (item_id,)
    ).fetchone()
    if not item:
        raise ValueError(f"المنتج رقم {item_id} غير موجود")
    if item["type"] != "final":
        raise ValueError(
            f"التسعير متاح للمنتجات النهائية فقط "
            f"(المنتج رقم {item_id} نوعه '{item['type']}')"
        )

    conn.execute("""
        INSERT INTO pricing (item_id, margin, price)
        VALUES (?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET margin=excluded.margin, price=excluded.price
    """, (item_id, margin, price))
    conn.commit()


def delete_pricing(conn, item_id: int):
    conn.execute("DELETE FROM pricing WHERE item_id=?", (item_id,))
    conn.commit()