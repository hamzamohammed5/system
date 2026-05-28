"""
db/pricing/pricing_repo.py
==================
عمليات قراءة/كتابة جدول pricing.
كل منتج نهائي ممكن يكون له سعر = margin × cost

تحسين 23: upsert_pricing يتحقق من نوع المنتج قبل الحفظ.

تحسين 23b (pagination):
  fetch_all_pricing يدعم الآن limit/offset لتجنب تحميل آلاف
  المنتجات النهائية في الذاكرة دفعة واحدة.
  fetch_pricing_count يُعيد إجمالي العدد للـ UI pagination.
  الـ API القديم (بدون parameters) لا يزال يعمل للتوافق
  لكن يُرجع أول 500 فقط — استخدم fetch_all_pricing_paginated
  للتحكم الكامل.
"""


def fetch_all_pricing(conn, limit: int = 500, offset: int = 0):
    """
    يرجع المنتجات النهائية مع بيانات التسعير.

    [تحسين 23b] يدعم pagination عبر limit/offset.
    القيمة الافتراضية limit=500 تحمي من تحميل آلاف الصفوف بصمت.

    للحصول على الإجمالي الكامل استخدم fetch_pricing_count().
    للتحكم الكامل في الصفحات استخدم fetch_all_pricing_paginated().

    مثال في الـ UI:
        total   = fetch_pricing_count(conn)
        rows    = fetch_all_pricing(conn, limit=200, offset=0)
        if total > len(rows):
            label.setText(f"يعرض {len(rows)} من أصل {total} منتج")
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
        LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()


def fetch_pricing_count(conn) -> int:
    """
    [تحسين 23b] يرجع إجمالي عدد المنتجات النهائية.
    يُستخدم جنباً إلى جنب مع fetch_all_pricing() للـ pagination.

    مثال:
        total = fetch_pricing_count(conn)
        page  = fetch_all_pricing(conn, limit=200, offset=page_num * 200)
        label.setText(f"يعرض {len(page)} من أصل {total}")
    """
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM items WHERE type = 'final'"
        ).fetchone()
        return row["c"] if row else 0
    except Exception:
        return 0


def fetch_all_pricing_paginated(conn,
                                 limit: int = 200,
                                 offset: int = 0,
                                 category_id: int = None,
                                 search: str = None,
                                 only_priced: bool = False):
    """
    [تحسين 23b] Pagination كاملة مع فلترة.

    Parameters:
        limit       : عدد الصفوف في الصفحة
        offset      : بداية الصفحة
        category_id : فلتر على التصنيف (اختياري)
        search      : بحث في اسم المنتج (اختياري)
        only_priced : لو True → يُرجع المنتجات التي لها سعر فقط

    مثال استخدام في الـ UI:
        PAGE = 100
        total   = fetch_pricing_count(conn)
        rows    = fetch_all_pricing_paginated(conn,
                      limit=PAGE, offset=page * PAGE,
                      search=search_text)
        has_next = (page + 1) * PAGE < total
    """
    conditions = ["i.type = 'final'"]
    params = []

    if category_id is not None:
        conditions.append("i.category_id = ?")
        params.append(category_id)

    if search:
        conditions.append("i.name LIKE ?")
        params.append(f"%{search}%")

    if only_priced:
        conditions.append("p.id IS NOT NULL")

    where = "WHERE " + " AND ".join(conditions)

    return conn.execute(f"""
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
        {where}
        ORDER BY i.name
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()


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