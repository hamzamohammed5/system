"""
db/designs/dimension_sets_repo.py
==================================
عمليات قراءة/كتابة مجموعات المقاسات وحقولها واعتمادياتها.
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
    sql = """
        SELECT f.id      AS field_id,
               f.label   AS field_label,
               f.set_id,
               ds.name   AS set_name,
               COALESCE(dc.id, -1)                 AS cat_id,
               COALESCE(dc.name, '— بدون تصنيف —') AS cat_name
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
    """يحسب القيمة التلقائية في وضع التصميم (design_dim_values) مع دعم cross-set."""
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
    """
    يرجع dict: {field_id: {"value_num": float|None, "value_text": str}}
    يشمل القيمة الرقمية والاسم المخصص لكل صف.
    """
    rows = conn.execute(
        "SELECT field_id, value_num, value_text "
        "FROM dimension_set_values WHERE set_id=?",
        (set_id,)
    ).fetchall()
    return {
        r["field_id"]: {
            "value_num":  r["value_num"],
            "value_text": r["value_text"] or "",
        }
        for r in rows
    }


def save_standalone_value(conn, set_id: int, field_id: int,
                           value_num: float = None, value_text: str = None):
    conn.execute("""
        INSERT INTO dimension_set_values (set_id, field_id, value_num, value_text)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(set_id, field_id) DO UPDATE SET
            value_num=excluded.value_num,
            value_text=excluded.value_text
    """, (set_id, field_id, value_num, value_text))
    conn.commit()


def fetch_source_set_values(conn, source_set_id: int) -> dict:
    """
    يجلب كل قيم مجموعة مقاسات محددة (المجموعة المصدر في الاعتماديات).
    يُستخدم في _ValuesPanel لعرض قيم المصدر عند إدخال قيم مجموعة مرتبطة.

    يرجع dict: {field_id: {"value_num": float|None, "value_text": str, "label": str}}
    """
    rows = conn.execute("""
        SELECT dsv.field_id, dsv.value_num, dsv.value_text,
               df.label, df.unit
        FROM   dimension_set_values dsv
        JOIN   dimension_fields df ON df.id = dsv.field_id
        WHERE  dsv.set_id = ?
    """, (source_set_id,)).fetchall()
    return {
        r["field_id"]: {
            "value_num":  r["value_num"],
            "value_text": r["value_text"] or "",
            "label":      r["label"],
            "unit":       r["unit"] or "",
        }
        for r in rows
    }


def calc_standalone_cross_auto(conn, field_id: int, current_set_id: int):
    """
    يحسب القيمة التلقائية في وضع الإدخال المستقل (dimension_set_values).

    - source_set_id = None  → المصدر نفس المجموعة الحالية
    - source_set_id != None → المصدر مجموعة مختلفة (cross-set)

    يرجع float أو None لو القيمة المصدر غير موجودة.
    """
    dep = fetch_field_dep(conn, field_id)
    if not dep:
        return None

    source_field_id = dep["source_field_id"]
    # None = نفس المجموعة → نستخدم current_set_id
    source_set_id   = dep["source_set_id"] if dep["source_set_id"] else current_set_id
    offset          = float(dep["offset"])

    val_row = conn.execute(
        "SELECT value_num FROM dimension_set_values WHERE set_id=? AND field_id=?",
        (source_set_id, source_field_id)
    ).fetchone()

    if not val_row or val_row["value_num"] is None:
        return None

    return float(val_row["value_num"]) + offset


def get_source_ref(conn, field_id: int, current_set_id: int) -> dict | None:
    """
    يجيب بيانات المصدر لعرض الـ reference label في _ValuesPanel.

    يرجع:
      {"source_val": float, "result": float, "set_name": str, "offset": float}
    أو None لو مفيش اعتمادية أو القيمة مش موجودة.
    """
    dep = fetch_field_dep(conn, field_id)
    if not dep:
        return None

    source_field_id = dep["source_field_id"]
    source_set_id   = dep["source_set_id"] if dep["source_set_id"] else current_set_id
    offset          = float(dep["offset"])

    row = conn.execute(
        "SELECT dsv.value_num, ds.name AS set_name "
        "FROM dimension_set_values dsv "
        "JOIN dimension_sets ds ON ds.id = dsv.set_id "
        "WHERE dsv.set_id=? AND dsv.field_id=?",
        (source_set_id, source_field_id)
    ).fetchone()

    if not row or row["value_num"] is None:
        return None

    src = float(row["value_num"])
    return {
        "source_val": src,
        "result":     src + offset,
        "set_name":   row["set_name"],
        "offset":     offset,
    }