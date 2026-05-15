"""
db/shared/categories_repo.py
=====================
عمليات قراءة/كتابة جدول categories — مع دعم:
  - التصنيفات الفرعية (شجرة)
  - scope='design' للتصنيفات الخاصة بمجموعات المقاسات
  - template_fields (JSON) لتخزين الحقول الافتراضية لكل تصنيف
  - default_unit لتخزين الوحدة الافتراضية
"""

import json

SCOPES = {
    "all":     "الكل",
    "raw":     "الخامات",
    "semi":    "نصف مصنع",
    "final":   "منتج نهائي",
    "labor":   "العمالة",
    "machine": "التشغيل",
    "pricing": "التسعير",
    "design":  "مجموعات المقاسات",
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


def fetch_categories_by_scope(conn, scope: str):
    """تصنيفات scope محدد فقط — بدون 'all'."""
    return conn.execute("""
        SELECT c.id, c.name, c.scope, c.color, c.parent_id,
               c.template_fields, c.default_unit,
               p.name AS parent_name
        FROM   categories c
        LEFT JOIN categories p ON p.id = c.parent_id
        WHERE  c.scope = ?
        ORDER  BY c.parent_id NULLS FIRST, c.name
    """, (scope,)).fetchall()


def fetch_category(conn, cat_id: int):
    return conn.execute(
        """SELECT id, name, scope, color, parent_id,
                  template_fields, default_unit
           FROM categories WHERE id=?""",
        (cat_id,)
    ).fetchone()


def fetch_descendants(conn, cat_id: int) -> list[int]:
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
                    color: str = "#607d8b", parent_id: int = None,
                    template_fields: list = None,
                    default_unit: str = "mm") -> int:
    fields_json = json.dumps(template_fields, ensure_ascii=False) if template_fields else None
    cur = conn.execute(
        """INSERT INTO categories
           (name, scope, color, parent_id, template_fields, default_unit)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, scope, color, parent_id, fields_json, default_unit or "mm")
    )
    conn.commit()
    return cur.lastrowid


def update_category(conn, cat_id: int, name: str, scope: str,
                    color: str, parent_id: int = None,
                    template_fields: list = None,
                    default_unit: str = "mm"):
    if parent_id is not None:
        descendants = fetch_descendants(conn, cat_id)
        if parent_id in descendants:
            raise ValueError("لا يمكن جعل تصنيف فرعياً لأحد أبنائه")
    fields_json = json.dumps(template_fields, ensure_ascii=False) if template_fields else None
    conn.execute(
        """UPDATE categories
           SET name=?, scope=?, color=?, parent_id=?,
               template_fields=?, default_unit=?
           WHERE id=?""",
        (name, scope, color, parent_id, fields_json, default_unit or "mm", cat_id)
    )
    conn.commit()


def delete_category(conn, cat_id: int):
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()


def count_category_items(conn, cat_id: int) -> dict:
    ids          = fetch_descendants(conn, cat_id)
    placeholders = ",".join("?" * len(ids))
    results      = {}
    for table, label in [
        ("items",       "عناصر"),
        ("labor_ops",   "عمليات عمالة"),
        ("machine_ops", "عمليات تشغيل"),
        ("machines",    "ماكينات"),
    ]:
        try:
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM {table} "
                f"WHERE category_id IN ({placeholders})", ids
            ).fetchone()
            results[label] = row["cnt"] if row else 0
        except Exception:
            results[label] = 0
    return results


def build_tree(rows) -> list[dict]:
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


# ══════════════════════════════════════════════════════════
# Template Fields — حقول القالب الافتراضية للتصنيفات
# (تُخزَّن كـ JSON في عمود template_fields)
# ══════════════════════════════════════════════════════════

def get_template_fields(conn, cat_id: int) -> list[dict]:
    """
    يرجع حقول القالب الافتراضية للتصنيف.
    كل حقل: {name, label, unit, field_type, required, sort_order}
    """
    row = conn.execute(
        "SELECT template_fields FROM categories WHERE id=?", (cat_id,)
    ).fetchone()
    if not row or not row["template_fields"]:
        return []
    try:
        return json.loads(row["template_fields"])
    except Exception:
        return []


def set_template_fields(conn, cat_id: int, fields: list[dict]):
    """يحفظ حقول القالب الافتراضية للتصنيف."""
    conn.execute(
        "UPDATE categories SET template_fields=? WHERE id=?",
        (json.dumps(fields, ensure_ascii=False), cat_id)
    )
    conn.commit()


def apply_template_to_dimension_set(conn_erp, conn_design,
                                     cat_id: int, set_id: int) -> int:
    """
    ينسخ حقول القالب من التصنيف (erp.db) إلى مجموعة المقاسات (designs.db).
    يرجع عدد الحقول المنسوخة.
    يتجاهل الحقول المكررة (نفس الـ name).

    conn_erp    : connection لـ erp.db (فيه categories)
    conn_design : connection لـ designs.db (فيه dimension_fields)
    """
    fields = get_template_fields(conn_erp, cat_id)
    if not fields:
        return 0

    # الحقول الموجودة فعلاً في المجموعة
    existing = {
        r["name"] for r in conn_design.execute(
            "SELECT name FROM dimension_fields WHERE set_id=?", (set_id,)
        ).fetchall()
    }

    count = 0
    for i, f in enumerate(fields):
        name = f.get("name", "").strip()
        if not name or name in existing:
            continue
        conn_design.execute(
            """INSERT INTO dimension_fields
               (set_id, name, label, unit, field_type, required, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                set_id,
                name,
                f.get("label", name),
                f.get("unit", ""),
                f.get("field_type", "number"),
                1 if f.get("required", True) else 0,
                f.get("sort_order", i),
            )
        )
        existing.add(name)
        count += 1

    conn_design.commit()
    return count