"""
إضافات على design_repo.py
===========================
أضف الدوال دي في نهاية ملف db/design/design_repo.py الموجود.
"""

import json


# ══════════════════════════════════════════════════════════
# تصنيفات مجموعات المقاسات  (dim_set_categories)
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
         color, icon, notes or "")
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
         color, icon, notes or "", cat_id)
    )
    conn.commit()


def delete_dim_set_category(conn, cat_id: int):
    conn.execute("DELETE FROM dim_set_categories WHERE id=?", (cat_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# الحقول الافتراضية (template) لكل تصنيف
# ══════════════════════════════════════════════════════════

def fetch_category_template_fields(conn, cat_id: int) -> list:
    """يرجع الحقول الافتراضية لتصنيف مجموعة المقاسات."""
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
        (cat_id, name, label, unit, field_type,
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
        (name, label, unit, field_type, opts_json,
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


# ══════════════════════════════════════════════════════════
# نسخ الحقول الافتراضية إلى مجموعة مقاسات جديدة
# ══════════════════════════════════════════════════════════

def apply_category_template_to_set(conn, set_id: int, cat_id: int):
    """
    ينسخ الحقول الافتراضية من تصنيف المجموعة إلى مجموعة المقاسات.
    يُستدعى عند إنشاء مجموعة جديدة أو عند طلب "تطبيق القالب".
    """
    fields = fetch_category_template_fields(conn, cat_id)
    for f in fields:
        opts = None
        if f["options"]:
            try:
                opts = json.loads(f["options"])
            except Exception:
                opts = None
        # تجنب التكرار
        existing = conn.execute(
            "SELECT id FROM dimension_fields WHERE set_id=? AND name=?",
            (set_id, f["name"])
        ).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO dimension_fields "
            "(set_id, name, label, unit, field_type, options, required, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (set_id, f["name"], f["label"], f["unit"] or "",
             f["field_type"],
             json.dumps(opts, ensure_ascii=False) if opts else None,
             f["required"], f["sort_order"])
        )
    conn.commit()