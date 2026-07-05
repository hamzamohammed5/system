"""
db/costing/catalog_repo.py
============================
عمليات قراءة الكتالوج (منتجات مسعّرة + عروض) من قاعدة erp.

[مضاف حديثاً] هذا الملف كان في الأصل db_fetcher منفصل داخل
ui/tabs/orders/order_form/_products_fetcher.py — نُقل إلى db/costing
لأنه ينفذ SQL خام (JOIN على items/pricing/categories/offers)،
وهذا يخالف مبدأ الطبقات:
    widgets -> tabs/UI -> services -> repos (db) -> schema
UI لا يجب أن يعرف SQL أو يفتح اتصال قاعدة بيانات بنفسه.

جدول erp المستخدمة هنا (قراءة فقط):
    items(id, name, type, category_id)
    pricing(item_id, price)
    categories(id, name, color)
    offers(id, name, discount, category_id)
    offer_items(offer_id, item_id, qty)
"""


# ══════════════════════════════════════════════════════════
# المنتجات المسعّرة
# ══════════════════════════════════════════════════════════

def fetch_priced_products(conn) -> list:
    """
    يجلب المنتجات المسعّرة (final/semi) مع تصنيفاتها وأسعارها.
    يرجع list of dict: {id, name, category_id, category_name, category_color, price, type}
    """
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


def fetch_priced_product_by_id(conn, product_id: int) -> "dict | None":
    """
    [مضاف] يجلب منتجاً مسعّراً واحداً بمعرفه (id, name, price).

    [تعديل هيكلي] نُقلت هنا من services/orders/order_service.py حيث
    كانت resolve_product_info تنفذ SQL خام مباشرة على erp_conn
    (SELECT name, price FROM items WHERE id=?)، متخطّية طبقة الـ repo
    بالكامل. الآن كل قراءة على items تمر عبر catalog_repo فقط،
    حفاظاً على مبدأ الطبقات:
        widgets -> tabs/UI -> services -> repos (db) -> schema

    يرجع dict: {id, name, price} أو None لو غير موجود.
    """
    row = conn.execute(
        "SELECT id, name, price FROM items "
        "LEFT JOIN pricing ON pricing.item_id = items.id "
        "WHERE items.id = ?",
        (product_id,)
    ).fetchone()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════
# العروض
# ══════════════════════════════════════════════════════════

def fetch_offers(conn) -> list:
    rows = conn.execute("""
        SELECT o.id, o.name, o.discount, c.name AS category_name
        FROM   offers o
        LEFT JOIN categories c ON c.id = o.category_id
        ORDER  BY o.name
    """).fetchall()
    return [dict(r) for r in rows]


def fetch_offer_lines(conn, offer_id: int) -> list:
    rows = conn.execute("""
        SELECT oi.item_id, oi.qty, i.name AS item_name, p.price
        FROM   offer_items oi
        JOIN   items i  ON i.id = oi.item_id
        LEFT JOIN pricing p ON p.item_id = oi.item_id
        WHERE  oi.offer_id = ?
    """, (offer_id,)).fetchall()
    return [dict(r) for r in rows]
