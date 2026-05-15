"""
db/design_repo.py
==================
عمليات قراءة/كتابة كل جداول التصميمات.
"""

import json
from db.design.design_schema import get_design_connection


# ══════════════════════════════════════════════════════════
# تصنيفات التصميم
# ══════════════════════════════════════════════════════════

def fetch_all_design_categories(conn):
    return conn.execute(
        "SELECT id, name, color, icon, notes FROM design_categories ORDER BY name"
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
                            color: str, icon: str, notes: str = ""):
    conn.execute(
        "UPDATE design_categories SET name=?, color=?, icon=?, notes=? WHERE id=?",
        (name, color, icon, notes or "", cat_id)
    )
    conn.commit()


def delete_design_category(conn, cat_id: int):
    conn.execute("DELETE FROM design_categories WHERE id=?", (cat_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# مجموعات المقاسات
# ══════════════════════════════════════════════════════════

def fetch_all_dimension_sets(conn):
    return conn.execute(
        "SELECT id, name, description, unit, color, created_at "
        "FROM dimension_sets ORDER BY name"
    ).fetchall()


def fetch_dimension_set(conn, set_id: int):
    return conn.execute(
        "SELECT * FROM dimension_sets WHERE id=?", (set_id,)
    ).fetchone()


def insert_dimension_set(conn, name: str, description: str = "",
                          unit: str = "mm", color: str = "#1565c0") -> int:
    cur = conn.execute(
        "INSERT INTO dimension_sets (name, description, unit, color) VALUES (?, ?, ?, ?)",
        (name, description or "", unit, color)
    )
    conn.commit()
    return cur.lastrowid


def update_dimension_set(conn, set_id: int, name: str,
                          description: str = "", unit: str = "mm",
                          color: str = "#1565c0"):
    conn.execute(
        "UPDATE dimension_sets SET name=?, description=?, unit=?, color=? WHERE id=?",
        (name, description or "", unit, color, set_id)
    )
    conn.commit()


def delete_dimension_set(conn, set_id: int):
    conn.execute("DELETE FROM dimension_sets WHERE id=?", (set_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# حقول المقاسات
# ══════════════════════════════════════════════════════════

def fetch_fields_for_set(conn, set_id: int):
    return conn.execute(
        "SELECT id, set_id, name, label, unit, field_type, options, required, sort_order, notes "
        "FROM dimension_fields WHERE set_id=? ORDER BY sort_order, id",
        (set_id,)
    ).fetchall()


def fetch_field(conn, field_id: int):
    return conn.execute(
        "SELECT * FROM dimension_fields WHERE id=?", (field_id,)
    ).fetchone()


def insert_dimension_field(conn, set_id: int, name: str, label: str,
                            unit: str = "", field_type: str = "number",
                            options: list = None, required: bool = True,
                            sort_order: int = 0, notes: str = "") -> int:
    opts_json = json.dumps(options, ensure_ascii=False) if options else None
    cur = conn.execute(
        "INSERT INTO dimension_fields "
        "(set_id, name, label, unit, field_type, options, required, sort_order, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (set_id, name, label, unit, field_type,
         opts_json, 1 if required else 0, sort_order, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_dimension_field(conn, field_id: int, name: str, label: str,
                            unit: str = "", field_type: str = "number",
                            options: list = None, required: bool = True,
                            sort_order: int = 0, notes: str = ""):
    opts_json = json.dumps(options, ensure_ascii=False) if options else None
    conn.execute(
        "UPDATE dimension_fields SET name=?, label=?, unit=?, field_type=?, "
        "options=?, required=?, sort_order=?, notes=? WHERE id=?",
        (name, label, unit, field_type, opts_json,
         1 if required else 0, sort_order, notes or "", field_id)
    )
    conn.commit()


def delete_dimension_field(conn, field_id: int):
    conn.execute("DELETE FROM dimension_fields WHERE id=?", (field_id,))
    conn.commit()


def reorder_fields(conn, set_id: int, field_ids: list[int]):
    """إعادة ترتيب الحقول."""
    for i, fid in enumerate(field_ids):
        conn.execute(
            "UPDATE dimension_fields SET sort_order=? WHERE id=? AND set_id=?",
            (i, fid, set_id)
        )
    conn.commit()


# ══════════════════════════════════════════════════════════
# الأشكال
# ══════════════════════════════════════════════════════════

def fetch_all_shapes(conn, category_id: int = None, dim_set_id: int = None):
    query = """
        SELECT s.id, s.name, s.description, s.material, s.notes,
               s.category_id, s.dim_set_id, s.created_at, s.updated_at,
               c.name AS category_name, c.color AS category_color, c.icon AS category_icon,
               ds.name AS dim_set_name, ds.unit AS dim_set_unit
        FROM shapes s
        LEFT JOIN design_categories c  ON c.id  = s.category_id
        LEFT JOIN dimension_sets    ds ON ds.id = s.dim_set_id
        WHERE 1=1
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
        SELECT s.*, c.name AS category_name, c.color AS category_color,
               c.icon AS category_icon,
               ds.name AS dim_set_name, ds.unit AS dim_set_unit, ds.color AS dim_set_color
        FROM shapes s
        LEFT JOIN design_categories c  ON c.id  = s.category_id
        LEFT JOIN dimension_sets    ds ON ds.id = s.dim_set_id
        WHERE s.id = ?
    """, (shape_id,)).fetchone()


def insert_shape(conn, name: str, category_id: int = None,
                 dim_set_id: int = None, description: str = "",
                 material: str = "", notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO shapes (name, category_id, dim_set_id, description, material, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, category_id, dim_set_id, description or "",
         material or "", notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_shape(conn, shape_id: int, name: str, category_id: int = None,
                 dim_set_id: int = None, description: str = "",
                 material: str = "", notes: str = ""):
    conn.execute(
        "UPDATE shapes SET name=?, category_id=?, dim_set_id=?, "
        "description=?, material=?, notes=?, "
        "updated_at=datetime('now') WHERE id=?",
        (name, category_id, dim_set_id,
         description or "", material or "", notes or "", shape_id)
    )
    conn.commit()


def delete_shape(conn, shape_id: int):
    conn.execute("DELETE FROM shapes WHERE id=?", (shape_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# قيم المقاسات لكل شكل
# ══════════════════════════════════════════════════════════

def fetch_shape_dimensions(conn, shape_id: int) -> dict:
    """يرجع {field_id: value} للشكل."""
    rows = conn.execute(
        "SELECT field_id, value FROM shape_dimensions WHERE shape_id=?",
        (shape_id,)
    ).fetchall()
    return {r["field_id"]: r["value"] for r in rows}


def fetch_shape_dimensions_full(conn, shape_id: int) -> list:
    """يرجع بيانات كاملة مع اسم الحقل."""
    return conn.execute("""
        SELECT sd.field_id, sd.value,
               df.name, df.label, df.unit, df.field_type, df.sort_order
        FROM shape_dimensions sd
        JOIN dimension_fields df ON df.id = sd.field_id
        WHERE sd.shape_id = ?
        ORDER BY df.sort_order, df.id
    """, (shape_id,)).fetchall()


def save_shape_dimensions(conn, shape_id: int, values: dict):
    """
    يحفظ قيم المقاسات للشكل.
    values: {field_id: value_str}
    """
    for field_id, value in values.items():
        conn.execute("""
            INSERT INTO shape_dimensions (shape_id, field_id, value)
            VALUES (?, ?, ?)
            ON CONFLICT(shape_id, field_id) DO UPDATE SET value=excluded.value
        """, (shape_id, field_id, str(value) if value is not None else ""))
    conn.commit()


def delete_shape_dimensions_for_set(conn, shape_id: int, set_id: int):
    """يحذف قيم المقاسات المرتبطة بـ dimension_set معين."""
    conn.execute("""
        DELETE FROM shape_dimensions
        WHERE shape_id=?
          AND field_id IN (
              SELECT id FROM dimension_fields WHERE set_id=?
          )
    """, (shape_id, set_id))
    conn.commit()


# ══════════════════════════════════════════════════════════
# بحث وتقارير
# ══════════════════════════════════════════════════════════

def search_shapes(conn, query: str) -> list:
    """بحث بالاسم أو الوصف أو المادة."""
    q = f"%{query}%"
    return conn.execute("""
        SELECT s.id, s.name, s.description, s.material,
               c.name AS category_name, c.color AS category_color, c.icon AS category_icon,
               ds.name AS dim_set_name
        FROM shapes s
        LEFT JOIN design_categories c  ON c.id  = s.category_id
        LEFT JOIN dimension_sets    ds ON ds.id = s.dim_set_id
        WHERE s.name LIKE ? OR s.description LIKE ? OR s.material LIKE ?
        ORDER BY s.name
    """, (q, q, q)).fetchall()


def fetch_shapes_with_dimensions(conn, dim_set_id: int,
                                  category_id: int = None) -> list:
    """
    يرجع الأشكال مع قيم مقاساتها لمجموعة مقاسات معينة.
    مفيد لعرض الجدول المقارن.
    """
    shapes = fetch_all_shapes(conn, category_id=category_id,
                               dim_set_id=dim_set_id)
    fields = fetch_fields_for_set(conn, dim_set_id)
    result = []
    for shape in shapes:
        dims = fetch_shape_dimensions(conn, shape["id"])
        row = dict(shape)
        row["_fields"] = [dict(f) for f in fields]
        row["_dims"]   = dims
        result.append(row)
    return result


def count_shapes_per_category(conn) -> dict:
    rows = conn.execute("""
        SELECT category_id, COUNT(*) as cnt FROM shapes
        GROUP BY category_id
    """).fetchall()
    return {r["category_id"]: r["cnt"] for r in rows}


def count_shapes_per_dim_set(conn) -> dict:
    rows = conn.execute("""
        SELECT dim_set_id, COUNT(*) as cnt FROM shapes
        GROUP BY dim_set_id
    """).fetchall()
    return {r["dim_set_id"]: r["cnt"] for r in rows}