"""
db/designs/dimension_sets_repo.py
=================================
عمليات قراءة/كتابة مجموعات المقاسات وحقولها واعتمادياتها.

تحسين 46: تم تقسيم الملف الأصلي (700+ سطر) إلى 3 ملفات:
  - design_categories_repo.py     ← تصنيفات التصميمات (dimension_sets)
  - dimension_sets_repo.py        ← هذا الملف: المجموعات + الحقول + الاعتماديات
  - dimension_instances_repo.py   ← Instances + قيمها

[تحسين 10] تحقق من Circular Imports:
  هذا الملف يُعيد تصدير دوال من ملفين آخرين للتوافق مع الكود القديم.
  ترتيب الاستيراد الآمن الحالي:
    dimension_sets_repo  ← design_categories_repo   (آمن ✓)
    dimension_sets_repo  ← dimension_instances_repo  (آمن ✓)

  قاعدة منع الـ circular imports:
    - design_categories_repo   يجب ألّا يستورد من dimension_sets_repo
    - dimension_instances_repo يجب ألّا يستورد من dimension_sets_repo
    - لو احتجت دالة من dimension_sets_repo داخل أحد الملفين
      الفرعيين، انقلها لملف مساعد مستقل (مثلاً: dimension_utils_repo.py)
      بدل إنشاء circular import.

  التحقق الدوري: نفّذ `python -c "import db.designs.dimension_sets_repo"`
  بعد أي تعديل على الملفات الثلاثة للتأكد من عدم وجود circular imports.

للتوافق مع الكود القديم يُعاد تصدير كل الدوال من الملفات الجديدة:
"""

# ── إعادة تصدير Categories (للتوافق مع الكود القديم) ─────
from db.designs.design_categories_repo import (          # noqa: F401
    fetch_all_design_categories,
    fetch_design_category,
    fetch_category_descendants,
    insert_design_category,
    update_design_category,
    delete_design_category,
    build_category_tree,
)

# ── إعادة تصدير Instances (للتوافق مع الكود القديم) ──────
from db.designs.dimension_instances_repo import (        # noqa: F401
    fetch_instances_for_set,
    fetch_instance,
    insert_instance,
    update_instance,
    delete_instance,
    duplicate_instance,
    fetch_instance_values,
    save_instance_values,
    calc_instance_cross_auto,
    fetch_standalone_values,
    save_standalone_value,
    fetch_source_set_values,
    calc_standalone_cross_auto,
    get_source_ref,
)


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
        "INSERT INTO dimension_sets (name, category_id, default_unit, notes)"
        " VALUES (?, ?, ?, ?)",
        (name, category_id, default_unit or "cm", notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_dimension_set(conn, set_id: int, name: str,
                          category_id: int = None, default_unit: str = "cm",
                          notes: str = ""):
    conn.execute(
        "UPDATE dimension_sets SET name=?, category_id=?, default_unit=?, notes=?"
        " WHERE id=?",
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
               sf.label  AS source_label,
               ss.name   AS source_set_name
        FROM   dimension_fields f
        LEFT JOIN dimension_field_deps dep ON dep.field_id = f.id
        LEFT JOIN dimension_fields sf ON sf.id = dep.source_field_id
        LEFT JOIN dimension_sets   ss ON ss.id = dep.source_set_id
        WHERE  f.set_id = ?
        ORDER  BY f.sort_order, f.id
    """, (set_id,)).fetchall()


def fetch_all_fields_for_combo(conn, exclude_field_id: int = None) -> list:
    """كل الحقول الرقمية مجمّعة حسب المجموعة والتصنيف — للـ comboboxes."""
    sql = """
        SELECT f.id      AS field_id,
               f.label   AS field_label,
               f.set_id,
               ds.name   AS set_name,
               COALESCE(dc.id, -1)                  AS cat_id,
               COALESCE(dc.name, '— بدون تصنيف —')  AS cat_name
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
        "SELECT id, set_id, name, label, unit, field_type, required, sort_order"
        " FROM dimension_fields WHERE id=?",
        (field_id,)
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
    """يُعيد ترتيب الحقول حسب القائمة المعطاة."""
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
        "SELECT id, field_id, source_field_id, source_set_id, offset, notes"
        " FROM dimension_field_deps WHERE field_id=?",
        (field_id,)
    ).fetchone()


def set_field_dep(conn, field_id: int, source_field_id: int,
                  offset: float = 0.0, notes: str = "",
                  source_set_id: int = None):
    conn.execute(
        "DELETE FROM dimension_field_deps WHERE field_id=?", (field_id,)
    )
    conn.execute(
        "INSERT INTO dimension_field_deps"
        " (field_id, source_field_id, source_set_id, offset, notes)"
        " VALUES (?, ?, ?, ?, ?)",
        (field_id, source_field_id, source_set_id, offset, notes or "")
    )
    conn.commit()


def remove_field_dep(conn, field_id: int):
    conn.execute(
        "DELETE FROM dimension_field_deps WHERE field_id=?", (field_id,)
    )
    conn.commit()


def calc_auto_value(conn, field_id: int, link_id: int) -> "float | None":
    """
    يحسب القيمة التلقائية في وضع التصميم (design_dim_values)
    مع دعم cross-set dependencies.
    """
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
            "SELECT id FROM design_dimensions"
            " WHERE design_id=? AND set_id=? LIMIT 1",
            (link_row["design_id"], source_set_id)
        ).fetchone()
        if not src_link_row:
            return None
        source_link_id = src_link_row["id"]

    val_row = conn.execute(
        "SELECT value_num FROM design_dim_values"
        " WHERE link_id=? AND field_id=?",
        (source_link_id, source_field_id)
    ).fetchone()

    if not val_row or val_row["value_num"] is None:
        return None

    return float(val_row["value_num"]) + offset