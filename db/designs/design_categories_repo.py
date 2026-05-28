"""
db/designs/design_categories_repo.py
======================================
عمليات CRUD لتصنيفات مجموعات المقاسات (design_categories).

مستخرج من dimension_sets_repo.py (تحسين 46 — تقسيم الملف الضخم).

ملاحظة: هذه التصنيفات مختلفة عن design_item_categories:
  - design_categories      → تصنيفات مجموعات المقاسات (dimension_sets)
  - design_item_categories → تصنيفات التصميمات نفسها (designs)
"""


# ══════════════════════════════════════════════════════════
# جلب
# ══════════════════════════════════════════════════════════

def fetch_all_design_categories(conn) -> list:
    return conn.execute("""
        SELECT c.id, c.name, c.color, c.parent_id, c.notes,
               p.name AS parent_name
        FROM   design_categories c
        LEFT JOIN design_categories p ON p.id = c.parent_id
        ORDER  BY c.parent_id NULLS FIRST, c.name
    """).fetchall()


def fetch_design_category(conn, cat_id: int):
    return conn.execute(
        "SELECT id, name, color, parent_id, notes "
        "FROM design_categories WHERE id=?",
        (cat_id,)
    ).fetchone()


def fetch_category_descendants(conn, cat_id: int) -> list:
    """يرجع list بـ IDs كل الأبناء المتداخلين (شامل cat_id نفسه)."""
    result, queue = set(), [cat_id]
    while queue:
        cur = queue.pop()
        if cur in result:
            continue
        result.add(cur)
        children = conn.execute(
            "SELECT id FROM design_categories WHERE parent_id=?", (cur,)
        ).fetchall()
        queue.extend(r["id"] for r in children)
    return list(result)


# ══════════════════════════════════════════════════════════
# إضافة / تعديل / حذف
# ══════════════════════════════════════════════════════════

def insert_design_category(conn, name: str, color: str = "#1565c0",
                            parent_id: int = None, notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO design_categories (name, color, parent_id, notes) "
        "VALUES (?, ?, ?, ?)",
        (name, color or "#1565c0", parent_id, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_design_category(conn, cat_id: int, name: str,
                            color: str, parent_id: int = None,
                            notes: str = ""):
    conn.execute(
        "UPDATE design_categories "
        "SET name=?, color=?, parent_id=?, notes=? WHERE id=?",
        (name, color or "#1565c0", parent_id, notes or "", cat_id)
    )
    conn.commit()


def delete_design_category(conn, cat_id: int):
    conn.execute("DELETE FROM design_categories WHERE id=?", (cat_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# بناء الشجرة
# ══════════════════════════════════════════════════════════

def build_category_tree(rows) -> list:
    """
    يبني شجرة تصنيفات من قائمة صفوف DB.
    يرجع list[dict] بـ children متداخلة.
    """
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