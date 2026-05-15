"""
db/design/design_repo.py
=========================
كل عمليات قاعدة بيانات التصميمات (designs.db).

الجداول:
  dim_set_categories       — تصنيفات مجموعات المقاسات
  dim_set_category_fields  — حقول القالب لكل تصنيف
  design_categories        — تصنيفات الأشكال
  dimension_sets           — مجموعات المقاسات
  dimension_fields         — حقول كل مجموعة
  shapes                   — الأشكال
  shape_dimensions         — قيم المقاسات لكل شكل
"""

import json


# ══════════════════════════════════════════════════════════
# dim_set_categories — تصنيفات مجموعات المقاسات
# ══════════════════════════════════════════════════════════

def fetch_all_dim_set_categories(conn) -> list:
    return conn.execute(
        "SELECT id, name, description, default_unit, color, icon, notes "
        "FROM dim_set_categories ORDER BY name"
    ).fetchall()


def fetch_dim_set_category(conn, cat_id: int):
    return conn.execute(
        "SELECT * FROM dim_set_categories WHERE id=?", (cat_id,)
    ).fetchone()


def insert_dim_set_category(conn, name: str, description: str = "",
                             default_unit: str = "mm", color: str = "#1565c0",
                             icon: str = "📏", notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO dim_set_categories "
        "(name, description, default_unit, color, icon, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, description or "", default_unit or "mm",
         color or "#1565c0", icon or "📏", notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_dim_set_category(conn, cat_id: int, name: str,
                             description: str = "", default_unit: str = "mm",
                             color: str = "#1565c0", icon: str = "📏",
                             notes: str = ""):
    conn.execute(
        "UPDATE dim_set_categories "
        "SET name=?, description=?, default_unit=?, color=?, icon=?, notes=? "
        "WHERE id=?",
        (name, description or "", default_unit or "mm",
         color or "#1565c0", icon or "📏", notes or "", cat_id)
    )
    conn.commit()


def delete_dim_set_category(conn, cat_id: int):
    conn.execute("DELETE FROM dim_set_categories WHERE id=?", (cat_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# dim_set_category_fields — حقول القالب
# ══════════════════════════════════════════════════════════

def fetch_category_template_fields(conn, cat_id: int) -> list:
    return conn.execute(
        "SELECT id, name, label, unit, field_type, options, required, sort_order "
        "FROM dim_set_category_fields "
        "WHERE category_id=? ORDER BY sort_order, id",
        (cat_id,)
    ).fetchall()


def insert_category_template_field(conn, cat_id: int, name: str, label: str,
                                    unit: str = "", field_type: str = "number",
                                    options: list = None, required: bool = True,
                                    sort_order: int = 0) -> int:
    opts_json = json.dumps(options, ensure_ascii=False) if options else None
    cur = conn.execute(
        "INSERT INTO dim_set_category_fields "
        "(category_id, name, label, unit, field_type, options, required, sort_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (cat_id, name, label, unit or "", field_type,
         opts_json, 1 if required else 0, sort_order)
    )
    conn.commit()
    return cur.lastrowid


def update_category_template_field(conn, field_id: int, name: str, label: str,
                                    unit: str = "", field_type: str = "number",
                                    options: list = None, required: bool = True,
                                    sort_order: int = 0):
    opts_json = json.dumps(options, ensure_ascii=False) if options else None
    conn.execute(
        "UPDATE dim_set_category_fields "
        "SET name=?, label=?, unit=?, field_type=?, options=?, required=?, sort_order=? "
        "WHERE id=?",
        (name, label, unit or "", field_type, opts_json,
         1 if required else 0, sort_order, field_id)
    )
    conn.commit()


def delete_category_template_field(conn, field_id: int):
    conn.execute("DELETE FROM dim_set_category_fields WHERE id=?", (field_id,))
    conn.commit()


def reorder_category_template_fields(conn, cat_id: int, field_ids: list):
    for i, fid in enumerate(field_ids):
        conn.execute(
            "UPDATE dim_set_category_fields SET sort_order=? "
            "WHERE id=? AND category_id=?",
            (i, fid, cat_id)
        )
    conn.commit()


def apply_category_template_to_set(conn, set_id: int, cat_id: int) -> int:
    """
    ينسخ حقول القالب من dim_set_category_fields إلى dimension_fields.
    يتجاهل الحقول المكررة (نفس الـ name).
    يرجع عدد الحقول المنسوخة.
    """
    fields = fetch_category_template_fields(conn, cat_id)
    if not fields:
        return 0

    existing = {
        r["name"] for r in conn.execute(
            "SELECT name FROM dimension_fields WHERE set_id=?", (set_id,)
        ).fetchall()
    }

    count = 0
    for f in fields:
        name = f["name"].strip() if f["name"] else ""
        if not name or name in existing:
            continue
        opts = None
        if f["options"]:
            try:
                opts = json.loads(f["options"])
            except Exception:
                opts = None
        conn.execute(
            "INSERT INTO dimension_fields "
            "(set_id, name, label, unit, field_type, options, required, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                set_id, name,
                f["label"] or name,
                f["unit"] or "",
                f["field_type"] or "number",
                json.dumps(opts, ensure_ascii=False) if opts else None,
                f["required"] if f["required"] is not None else 1,
                f["sort_order"] or 0,
            )
        )
        existing.add(name)
        count += 1

    conn.commit()
    return count


# ══════════════════════════════════════════════════════════
# design_categories — تصنيفات الأشكال
# ══════════════════════════════════════════════════════════

def fetch_all_design_categories(conn) -> list:
    return conn.execute(
        "SELECT id, name, color, icon, notes "
        "FROM design_categories ORDER BY name"
    ).fetchall()


def insert_design_category(conn, name: str, color: str = "#607d8b",
                            icon: str = "📐", notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO design_categories (name, color, icon, notes) VALUES (?, ?, ?, ?)",
        (name, color, icon, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_design_category(conn, cat_id: int, name: str,
                            color: str = "#607d8b", icon: str = "📐",
                            notes: str = ""):
    conn.execute(
        "UPDATE design_categories SET name=?, color=?, icon=?, notes=? WHERE id=?",
        (name, color, icon, notes or "", cat_id)
    )
    conn.commit()


def delete_design_category(conn, cat_id: int):
    conn.execute("DELETE FROM design_categories WHERE id=?", (cat_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# dimension_sets — مجموعات المقاسات
# ══════════════════════════════════════════════════════════

def fetch_all_dimension_sets(conn) -> list:
    return conn.execute(
        "SELECT id, name, description, unit, color, category_id "
        "FROM dimension_sets ORDER BY name"
    ).fetchall()


def fetch_dimension_set(conn, set_id: int):
    return conn.execute(
        "SELECT id, name, description, unit, color, category_id "
        "FROM dimension_sets WHERE id=?",
        (set_id,)
    ).fetchone()


def insert_dimension_set(conn, name: str, description: str = "",
                          unit: str = "mm", color: str = "#1565c0",
                          category_id: int = None) -> int:
    cur = conn.execute(
        "INSERT INTO dimension_sets (name, description, unit, color, category_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (name, description or "", unit or "mm", color or "#1565c0", category_id)
    )
    conn.commit()
    return cur.lastrowid


def update_dimension_set(conn, set_id: int, name: str, description: str = "",
                          unit: str = "mm", color: str = "#1565c0",
                          category_id: int = None):
    conn.execute(
        "UPDATE dimension_sets "
        "SET name=?, description=?, unit=?, color=?, category_id=? "
        "WHERE id=?",
        (name, description or "", unit or "mm", color or "#1565c0",
         category_id, set_id)
    )
    conn.commit()


def delete_dimension_set(conn, set_id: int):
    conn.execute("DELETE FROM dimension_sets WHERE id=?", (set_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# dimension_fields — حقول المجموعة
# ══════════════════════════════════════════════════════════

def fetch_fields_for_set(conn, set_id: int) -> list:
    return conn.execute(
        "SELECT id, set_id, name, label, unit, field_type, options, required, sort_order "
        "FROM dimension_fields WHERE set_id=? ORDER BY sort_order, id",
        (set_id,)
    ).fetchall()


def fetch_field(conn, field_id: int):
    return conn.execute(
        "SELECT id, set_id, name, label, unit, field_type, options, required, sort_order "
        "FROM dimension_fields WHERE id=?",
        (field_id,)
    ).fetchone()


def insert_dimension_field(conn, set_id: int, name: str, label: str,
                            unit: str = "", field_type: str = "number",
                            options: list = None, required: bool = True,
                            sort_order: int = 0) -> int:
    opts_json = json.dumps(options, ensure_ascii=False) if options else None
    cur = conn.execute(
        "INSERT INTO dimension_fields "
        "(set_id, name, label, unit, field_type, options, required, sort_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (set_id, name, label, unit or "", field_type,
         opts_json, 1 if required else 0, sort_order)
    )
    conn.commit()
    return cur.lastrowid


def update_dimension_field(conn, field_id: int, name: str, label: str,
                            unit: str = "", field_type: str = "number",
                            options: list = None, required: bool = True,
                            sort_order: int = 0):
    opts_json = json.dumps(options, ensure_ascii=False) if options else None
    conn.execute(
        "UPDATE dimension_fields "
        "SET name=?, label=?, unit=?, field_type=?, options=?, required=?, sort_order=? "
        "WHERE id=?",
        (name, label, unit or "", field_type, opts_json,
         1 if required else 0, sort_order, field_id)
    )
    conn.commit()


def delete_dimension_field(conn, field_id: int):
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
# shapes — الأشكال
# ══════════════════════════════════════════════════════════

def fetch_all_shapes(conn, category_id: int = None,
                     dim_set_id: int = None) -> list:
    query = """
        SELECT s.id, s.name, s.category_id, s.dim_set_id,
               s.description, s.material, s.notes,
               s.created_at, s.updated_at,
               dc.name  AS category_name,
               dc.color AS category_color,
               dc.icon  AS category_icon,
               ds.name  AS dim_set_name,
               ds.unit  AS dim_set_unit
        FROM   shapes s
        LEFT JOIN design_categories dc ON dc.id = s.category_id
        LEFT JOIN dimension_sets    ds ON ds.id = s.dim_set_id
        WHERE  1=1
    """
    params = []
    if category_id is not None:
        query += " AND s.category_id = ?"
        params.append(category_id)
    if dim_set_id is not None:
        query += " AND s.dim_set_id = ?"
        params.append(dim_set_id)
    query += " ORDER BY s.name"
    return conn.execute(query, params).fetchall()


def fetch_shape(conn, shape_id: int):
    return conn.execute("""
        SELECT s.id, s.name, s.category_id, s.dim_set_id,
               s.description, s.material, s.notes,
               s.created_at, s.updated_at,
               dc.name  AS category_name,
               dc.color AS category_color,
               dc.icon  AS category_icon,
               ds.name  AS dim_set_name,
               ds.unit  AS dim_set_unit
        FROM   shapes s
        LEFT JOIN design_categories dc ON dc.id = s.category_id
        LEFT JOIN dimension_sets    ds ON ds.id = s.dim_set_id
        WHERE  s.id = ?
    """, (shape_id,)).fetchone()


def insert_shape(conn, name: str, category_id: int = None,
                 dim_set_id: int = None, description: str = "",
                 material: str = "", notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO shapes "
        "(name, category_id, dim_set_id, description, material, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, category_id, dim_set_id,
         description or "", material or "", notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_shape(conn, shape_id: int, name: str,
                 category_id: int = None, dim_set_id: int = None,
                 description: str = "", material: str = "", notes: str = ""):
    conn.execute(
        "UPDATE shapes "
        "SET name=?, category_id=?, dim_set_id=?, "
        "    description=?, material=?, notes=?, "
        "    updated_at=datetime('now') "
        "WHERE id=?",
        (name, category_id, dim_set_id,
         description or "", material or "", notes or "", shape_id)
    )
    conn.commit()


def delete_shape(conn, shape_id: int):
    conn.execute("DELETE FROM shapes WHERE id=?", (shape_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# shape_dimensions — قيم المقاسات
# ══════════════════════════════════════════════════════════

def fetch_shape_dimensions(conn, shape_id: int) -> dict:
    """يرجع {field_id: value} للشكل."""
    rows = conn.execute(
        "SELECT field_id, value FROM shape_dimensions WHERE shape_id=?",
        (shape_id,)
    ).fetchall()
    return {r["field_id"]: r["value"] for r in rows}


def save_shape_dimensions(conn, shape_id: int, dims: dict):
    """
    يحفظ قيم المقاسات للشكل.
    dims: {field_id: value_str}
    """
    for field_id, value in dims.items():
        conn.execute(
            "INSERT INTO shape_dimensions (shape_id, field_id, value) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(shape_id, field_id) DO UPDATE SET value=excluded.value",
            (shape_id, field_id, str(value) if value is not None else "")
        )
    conn.commit()


def delete_shape_dimensions_for_set(conn, shape_id: int, set_id: int):
    """يحذف قيم المقاسات المرتبطة بمجموعة معينة."""
    conn.execute("""
        DELETE FROM shape_dimensions
        WHERE shape_id=?
          AND field_id IN (
              SELECT id FROM dimension_fields WHERE set_id=?
          )
    """, (shape_id, set_id))
    conn.commit()


def fetch_shapes_with_dimensions(conn, set_id: int,
                                  category_id: int = None) -> list:
    """
    يرجع الأشكال المرتبطة بمجموعة مقاسات معينة مع قيم مقاساتها.
    كل شكل يحتوي على:
      - كل حقول الشكل العادية
      - _dims: dict {field_id: value}
    """
    query = """
        SELECT s.id, s.name, s.category_id, s.dim_set_id,
               s.description, s.material, s.notes,
               dc.name  AS category_name,
               dc.color AS category_color,
               dc.icon  AS category_icon
        FROM   shapes s
        LEFT JOIN design_categories dc ON dc.id = s.category_id
        WHERE  s.dim_set_id = ?
    """
    params = [set_id]
    if category_id is not None:
        query += " AND s.category_id = ?"
        params.append(category_id)
    query += " ORDER BY s.name"

    shapes = conn.execute(query, params).fetchall()
    result = []
    for s in shapes:
        d = dict(s)
        d["_dims"] = fetch_shape_dimensions(conn, s["id"])
        result.append(d)
    return result