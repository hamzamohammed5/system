"""
ui/tabs/orders/order_form/_products_fetcher.py
"""


def fetch_priced_products() -> list:
    """
    يجلب المنتجات المسعّرة من erp.db مع تصنيفاتها وأسعارها.
    يرجع list of dict: {id, name, category_id, category_name, category_color, price, type}
    """
    try:
        from db.shared.connection import get_connection
        conn = get_connection("erp")
        rows = conn.execute("""
            SELECT
                i.id, i.name, i.type, i.category_id,
                c.name  AS category_name,
                c.color AS category_color,
                p.price
            FROM   items i
            JOIN   pricing p ON p.item_id = i.id
            LEFT JOIN categories c ON c.id = i.category_id
            WHERE  i.type IN ('final', 'semi')
            ORDER  BY COALESCE(c.name, 'ω') ASC, i.name ASC
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def fetch_offers() -> list:
    try:
        from db.shared.connection import get_connection
        conn = get_connection("erp")
        rows = conn.execute("""
            SELECT o.id, o.name, o.discount, c.name AS category_name
            FROM   offers o
            LEFT JOIN categories c ON c.id = o.category_id
            ORDER  BY o.name
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def fetch_offer_lines(offer_id: int) -> list:
    try:
        from db.shared.connection import get_connection
        conn = get_connection("erp")
        rows = conn.execute("""
            SELECT oi.item_id, oi.qty, i.name AS item_name, p.price
            FROM   offer_items oi
            JOIN   items i  ON i.id = oi.item_id
            LEFT JOIN pricing p ON p.item_id = oi.item_id
            WHERE  oi.offer_id = ?
        """, (offer_id,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
