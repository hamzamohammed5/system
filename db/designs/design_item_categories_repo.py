"""
db/designs/design_item_categories_repo.py
==========================================
عمليات CRUD لجدول design_item_categories —
تصنيفات التصميمات المستقلة (منفصلة عن تصنيفات مجموعات المقاسات).
"""


# ══════════════════════════════════════════════════════════
# جلب
# ══════════════════════════════════════════════════════════

def fetch_all_item_categories(conn) -> list:
    return conn.execute("""
        SELECT c.id, c.name, c.color, c.parent_id, c.notes,
               p.name AS parent_name
        FROM   design_item_categories c
        LEFT JOIN design_item_categories p ON p.id = c.parent_id
        ORDER  BY c.parent_id NULLS FIRST, c.name
    """).fetchall()


def fetch_item_category(conn, cat_id: int):
    return conn.execute(
        "SELECT id, name, color, parent_id, notes "
        "FROM design_item_categories WHERE id=?",
        (cat_id,)
    ).fetchone()


def fetch_item_category_descendants(conn, cat_id: int) -> list[int]:
    result, queue = set(), [cat_id]
    while queue:
        cur = queue.pop()
        if cur in result:
            continue
        result.add(cur)
        children = conn.execute(
            "SELECT id FROM design_item_categories WHERE parent_id=?", (cur,)
        ).fetchall()
        queue.extend(r["id"] for r in children)
    return list(result)


# ══════════════════════════════════════════════════════════
# إضافة / تعديل / حذف
# ══════════════════════════════════════════════════════════

def insert_item_category(conn, name: str, color: str = "#7c3aed",
                          parent_id: int = None, notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO design_item_categories (name, color, parent_id, notes) "
        "VALUES (?, ?, ?, ?)",
        (name, color or "#7c3aed", parent_id, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_item_category(conn, cat_id: int, name: str,
                          color: str, parent_id: int = None, notes: str = ""):
    # منع الحلقات
    if parent_id is not None:
        desc = fetch_item_category_descendants(conn, cat_id)
        if parent_id in desc:
            raise ValueError("لا يمكن جعل تصنيف فرعياً لأحد أبنائه")
    conn.execute(
        "UPDATE design_item_categories "
        "SET name=?, color=?, parent_id=?, notes=? WHERE id=?",
        (name, color or "#7c3aed", parent_id, notes or "", cat_id)
    )
    conn.commit()


def delete_item_category(conn, cat_id: int):
    conn.execute(
        "DELETE FROM design_item_categories WHERE id=?", (cat_id,)
    )
    conn.commit()


# ══════════════════════════════════════════════════════════
# بناء الشجرة
# ══════════════════════════════════════════════════════════

def build_item_category_tree(rows) -> list[dict]:
    nodes = {
        r["id"]: {
            "id":        r["id"],
            "name":      r["name"],
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


# ══════════════════════════════════════════════════════════
# عداد التصميمات لكل تصنيف
# ══════════════════════════════════════════════════════════

def count_designs_per_category(conn) -> dict[int, int]:
    """يرجع {category_id: count} للتصميمات المباشرة فقط."""
    try:
        rows = conn.execute(
            "SELECT item_category_id, COUNT(*) as cnt "
            "FROM designs WHERE item_category_id IS NOT NULL "
            "GROUP BY item_category_id"
        ).fetchall()
        return {r["item_category_id"]: r["cnt"] for r in rows}
    except Exception:
        return {}