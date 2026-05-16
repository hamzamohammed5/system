"""
db/designs/dimension_sets_repo.py
==================================
عمليات قراءة/كتابة مجموعات المقاسات وحقولها واعتمادياتها.

ملاحظة: عمود source_set_id يُضاف في create_designs_tables (design_schema.py).
"""


# ══════════════════════════════════════════════════════════
# تصنيفات التصميمات
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
        "SELECT id, name, color, parent_id, notes FROM design_categories WHERE id=?",
        (cat_id,)
    ).fetchone()


def insert_design_category(conn, name: str, color: str = "#1565c0",
                            parent_id: int = None, notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO design_categories (name, color, parent_id, notes) VALUES (?, ?, ?, ?)",
        (name, color, parent_id, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_design_category(conn, cat_id: int, name: str,
                            color: str, parent_id: int = None, notes: str = ""):
    conn.execute(
        "UPDATE design_categories SET name=?, color=?, parent_id=?, notes=? WHERE id=?",
        (name, color, parent_id, notes or "", cat_id)
    )
    conn.commit()


def delete_design_category(conn, cat_id: int):
    conn.execute("DELETE FROM design_categories WHERE id=?", (cat_id,))
    conn.commit()


def build_category_tree(rows) -> list:
    nodes = {
        r["id"]: {
            "id": r["id"], "name": r["name"],
            "color": r["color"], "parent_id": r["parent_id"],
            "children": [],
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


def fetch_category_descendants(conn, cat_id: int) -> list:
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
# مجموعات المقاسات
# ══════════════════════════════════════════════════════════

def fetch_all_dimension_sets(conn) -> list:
    return conn.execute("""
        SELECT ds.id, ds.name, ds.category_id, ds.default_unit, ds.notes,
               dc.name AS category_name
        FROM   dimension_sets ds
        LEFT JOIN design_categories dc ON dc.id = ds.category_id
        ORDER  BY ds.name
    """).fetchall()


def fetch_dimension_set(conn, set_id: int):
    return conn.execute("""
        SELECT ds.id, ds.name, ds.category_id, ds.default_unit, ds.notes,
               dc.name AS category_name
        FROM   dimension_sets ds
        LEFT JOIN design_categories dc ON dc.id = ds.category_id
        WHERE  ds.id = ?
    """, (set_id,)).fetchone()


def insert_dimension_set(conn, name: str, category_id: int = None,
                          default_unit: str = "cm", notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO dimension_sets (name, category_id, default_unit, notes) VALUES (?, ?, ?, ?)",
        (name, category_id, default_unit or "cm", notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_dimension_set(conn, set_id: int, name: str,
                          category_id: int = None, default_unit: str = "cm",
                          notes: str = ""):
    conn.execute(
        "UPDATE dimension_sets SET name=?, category_id=?, default_unit=?, notes=? WHERE id=?",
        (name, category_id, default_unit or "cm", notes or "", set_id)
    )
    conn.commit()


def delete_dimension_set(conn, set_id: int):
    conn.execute("DELETE FROM dimension_sets WHERE id=?", (set_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# حقول المجموعة
# ══════════════════════════════════════════════════════════

def fetch_fields_for_set(conn, set_id: int) -> list:
    """كل حقول مجموعة مقاسات مع معلومات الاعتمادية إن وجدت."""
    return conn.execute("""
        SELECT f.id, f.set_id, f.name, f.label, f.unit,
               f.field_type, f.required, f.sort_order,
               dep.source_field_id, dep.source_set_id,
               dep.offset AS dep_offset,
               sf.label AS source_label,
               ss.name  AS source_set_name
        FROM   dimension_fields f
        LEFT JOIN dimension_field_deps dep ON dep.field_id = f.id
        LEFT JOIN dimension_fields sf ON sf.id = dep.source_field_id
        LEFT JOIN dimension_sets   ss ON ss.id = dep.source_set_id
        WHERE  f.set_id = ?
        ORDER  BY f.sort_order, f.id
    """, (set_id,)).fetchall()


def fetch_all_fields_for_combo(conn, exclude_field_id: int = None) -> list:
    """
    كل الحقول الرقمية من كل المجموعات مرتبة بالتصنيف ثم المجموعة.
    كل صف: field_id, field_label, set_id, set_name, cat_id, cat_name
    """
    sql = """
        SELECT f.id      AS field_id,
               f.label   AS field_label,
               f.set_id,
               ds.name   AS set_name,
               COALESCE(dc.id, -1)                       AS cat_id,
               COALESCE(dc.name, '— بدون تصنيف —')       AS cat_name
        FROM   dimension_fields f
        JOIN   dimension_sets ds ON ds.id = f.set_id
        LEFT JOIN design_categories dc ON dc.id = ds.category_id
        WHERE  f.field_type = 'number'
    """
    params = []
    if exclude_field_id is not None:
        sql += " AND f.id != ?"
        params.append(exclude_field_id)
    sql += " ORDER BY cat_name, ds.name, f.sort_order, f.id"
    return conn.execute(sql, params).fetchall()


def fetch_field(conn, field_id: int):
    return conn.execute(
        "SELECT id, set_id, name, label, unit, field_type, required, sort_order "
        "FROM dimension_fields WHERE id=?", (field_id,)
    ).fetchone()


def insert_field(conn, set_id: int, name: str, label: str,
                 unit: str = "cm", field_type: str = "number",
                 required: bool = True, sort_order: int = 0) -> int:
    cur = conn.execute(
        """INSERT INTO dimension_fields
           (set_id, name, label, unit, field_type, required, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (set_id, name, label, unit or "cm",
         field_type or "number", 1 if required else 0, sort_order)
    )
    conn.commit()
    return cur.lastrowid


def update_field(conn, field_id: int, name: str, label: str,
                 unit: str = "cm", field_type: str = "number",
                 required: bool = True, sort_order: int = 0):
    conn.execute(
        """UPDATE dimension_fields
           SET name=?, label=?, unit=?, field_type=?, required=?, sort_order=?
           WHERE id=?""",
        (name, label, unit or "cm", field_type or "number",
         1 if required else 0, sort_order, field_id)
    )
    conn.commit()


def delete_field(conn, field_id: int):
    conn.execute("DELETE FROM dimension_fields WHERE id=?", (field_id,))
    conn.commit()


def reorder_fields(conn, set_id: int, field_ids: list):
    for i, fid in enumerate(field_ids):
        conn.execute(
            "UPDATE dimension_fields SET sort_order=? WHERE id=? AND set_id=?",
            (i, fid, set_id)
        )
    conn.commit()


# ══════════════════════════════════════════════════════════
# اعتماديات الحقول (مع دعم cross-set)
# ══════════════════════════════════════════════════════════

def fetch_field_dep(conn, field_id: int):
    return conn.execute(
        "SELECT id, field_id, source_field_id, source_set_id, offset, notes "
        "FROM dimension_field_deps WHERE field_id=?",
        (field_id,)
    ).fetchone()


def set_field_dep(conn, field_id: int, source_field_id: int,
                  offset: float = 0.0, notes: str = "",
                  source_set_id: int = None):
    conn.execute("DELETE FROM dimension_field_deps WHERE field_id=?", (field_id,))
    conn.execute(
        "INSERT INTO dimension_field_deps "
        "(field_id, source_field_id, source_set_id, offset, notes)"
        " VALUES (?, ?, ?, ?, ?)",
        (field_id, source_field_id, source_set_id, offset, notes or "")
    )
    conn.commit()


def remove_field_dep(conn, field_id: int):
    conn.execute("DELETE FROM dimension_field_deps WHERE field_id=?", (field_id,))
    conn.commit()


def calc_auto_value(conn, field_id: int, link_id: int):
    """يحسب القيمة التلقائية مع دعم cross-set."""
    dep = fetch_field_dep(conn, field_id)
    if not dep:
        return None

    source_field_id = dep["source_field_id"]
    source_set_id   = dep["source_set_id"]
    offset          = float(dep["offset"])

    if source_set_id is None:
        source_link_id = link_id
    else:
        link_row = conn.execute(
            "SELECT design_id FROM design_dimensions WHERE id=?", (link_id,)
        ).fetchone()
        if not link_row:
            return None
        src_link_row = conn.execute(
            "SELECT id FROM design_dimensions WHERE design_id=? AND set_id=? LIMIT 1",
            (link_row["design_id"], source_set_id)
        ).fetchone()
        if not src_link_row:
            return None
        source_link_id = src_link_row["id"]

    val_row = conn.execute(
        "SELECT value_num FROM design_dim_values WHERE link_id=? AND field_id=?",
        (source_link_id, source_field_id)
    ).fetchone()

    if not val_row or val_row["value_num"] is None:
        return None

    return float(val_row["value_num"]) + offset


# ══════════════════════════════════════════════════════════
# قيم المجموعة المستقلة (للإدخال المباشر بدون تصميم)
# ══════════════════════════════════════════════════════════

def fetch_standalone_values(conn, set_id: int) -> dict:
    rows = conn.execute(
        "SELECT field_id, value_num FROM dimension_set_values WHERE set_id=?",
        (set_id,)
    ).fetchall()
    return {r["field_id"]: r["value_num"] for r in rows}


def save_standalone_value(conn, set_id: int, field_id: int, value_num: float = None):
    conn.execute("""
        INSERT INTO dimension_set_values (set_id, field_id, value_num)
        VALUES (?, ?, ?)
        ON CONFLICT(set_id, field_id) DO UPDATE SET value_num=excluded.value_num
    """, (set_id, field_id, value_num))
    conn.commit()


def calc_standalone_cross_auto(conn, field_id: int, current_set_id: int):
    """يحسب القيمة التلقائية في وضع الإدخال المستقل عبر dimension_set_values."""
    dep = fetch_field_dep(conn, field_id)
    if not dep:
        return None

    source_field_id = dep["source_field_id"]
    source_set_id   = dep["source_set_id"] if dep["source_set_id"] else current_set_id
    offset          = float(dep["offset"])

    val_row = conn.execute(
        "SELECT value_num FROM dimension_set_values WHERE set_id=? AND field_id=?",
        (source_set_id, source_field_id)
    ).fetchone()

    if not val_row or val_row["value_num"] is None:
        return None

    return float(val_row["value_num"]) + offset