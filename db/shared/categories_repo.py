"""
db/categories_repo.py
=====================
عمليات قراءة/كتابة جدول categories — مع دعم التصنيفات الفرعية (شجرة).
"""

SCOPES = {
    "all":     "الكل",
    "raw":     "الخامات",
    "semi":    "نصف مصنع",
    "final":   "منتج نهائي",
    "labor":   "العمالة",
    "machine": "التشغيل",
    "pricing": "التسعير",
}

PRESET_COLORS = [
    "#e53935", "#d81b60", "#8e24aa", "#1e88e5",
    "#00897b", "#43a047", "#f4511e", "#6d4c41",
    "#546e7a", "#1565c0",
]


def fetch_all_categories(conn, scope: str = None):
    """كل التصنيفات مع اسم الأب — مفلترة بالـ scope لو محدد."""
    if scope:
        return conn.execute("""
            SELECT c.id, c.name, c.scope, c.color, c.parent_id,
                   p.name AS parent_name
            FROM   categories c
            LEFT JOIN categories p ON p.id = c.parent_id
            WHERE  c.scope = 'all' OR c.scope = ?
            ORDER  BY c.parent_id NULLS FIRST, c.name
        """, (scope,)).fetchall()
    return conn.execute("""
        SELECT c.id, c.name, c.scope, c.color, c.parent_id,
               p.name AS parent_name
        FROM   categories c
        LEFT JOIN categories p ON p.id = c.parent_id
        ORDER  BY c.scope, c.parent_id NULLS FIRST, c.name
    """).fetchall()


def fetch_category(conn, cat_id: int):
    return conn.execute(
        "SELECT id, name, scope, color, parent_id FROM categories WHERE id=?",
        (cat_id,)
    ).fetchone()


def fetch_descendants(conn, cat_id: int) -> list[int]:
    """
    يرجع IDs كل الأبناء والأحفاد (recursive) لتصنيف معين.
    يشمل الـ cat_id نفسه.
    """
    result = set()
    queue  = [cat_id]
    while queue:
        current = queue.pop()
        if current in result:
            continue
        result.add(current)
        children = conn.execute(
            "SELECT id FROM categories WHERE parent_id=?", (current,)
        ).fetchall()
        queue.extend(r["id"] for r in children)
    return list(result)


def insert_category(conn, name: str, scope: str = "all",
                    color: str = "#607d8b", parent_id: int = None) -> int:
    cur = conn.execute(
        "INSERT INTO categories (name, scope, color, parent_id) VALUES (?, ?, ?, ?)",
        (name, scope, color, parent_id)
    )
    conn.commit()
    return cur.lastrowid


def update_category(conn, cat_id: int, name: str, scope: str,
                    color: str, parent_id: int = None):
    # منع التصنيف من أن يكون أبًا لنفسه أو لأحد أسلافه
    if parent_id is not None:
        descendants = fetch_descendants(conn, cat_id)
        if parent_id in descendants:
            raise ValueError("لا يمكن جعل تصنيف فرعياً لأحد أبنائه")
    conn.execute(
        "UPDATE categories SET name=?, scope=?, color=?, parent_id=? WHERE id=?",
        (name, scope, color, parent_id, cat_id)
    )
    conn.commit()


def delete_category(conn, cat_id: int):
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()


def count_category_items(conn, cat_id: int) -> dict:
    """كام عنصر في كل جدول بيستخدم التصنيف ده أو أي فرع منه."""
    ids      = fetch_descendants(conn, cat_id)
    placeholders = ",".join("?" * len(ids))
    results  = {}
    for table, label in [
        ("items",       "عناصر"),
        ("labor_ops",   "عمليات عمالة"),
        ("machine_ops", "عمليات تشغيل"),
        ("machines",    "ماكينات"),
    ]:
        row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM {table} "
            f"WHERE category_id IN ({placeholders})", ids
        ).fetchone()
        results[label] = row["cnt"] if row else 0
    return results


def build_tree(rows) -> list[dict]:
    """
    يحوّل قايمة flat من التصنيفات لشجرة متداخلة.
    كل node: {id, name, scope, color, parent_id, children: [...]}
    """
    nodes = {
        r["id"]: {
            "id":        r["id"],
            "name":      r["name"],
            "scope":     r["scope"],
            "color":     r["color"],
            "parent_id": r["parent_id"],
            "children":  [],
        }
        for r in rows
    }
    roots = []
    for node in nodes.values():
        pid = node["parent_id"]
        if pid and pid in nodes:
            nodes[pid]["children"].append(node)
        else:
            roots.append(node)
    return roots