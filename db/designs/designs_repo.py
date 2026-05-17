"""
db/designs/designs_repo.py
===========================
عمليات قراءة/كتابة التصميمات وربطها بالمقاسات.

ملاحظة:
  - item_category_id → تصنيف التصميم (design_item_categories) ← الجديد
  - category_id      → تصنيف مجموعة المقاسات (design_categories) ← قديم/غير مستخدم
"""

from db.designs.dimension_sets_repo import calc_auto_value


# ══════════════════════════════════════════════════════════
# التصميمات — CRUD
# ══════════════════════════════════════════════════════════

def fetch_all_designs(conn, category_id: int = None,
                      set_id: int = None, name_q: str = "") -> list:
    """
    جلب التصميمات مع فلترة اختيارية.
    category_id هنا = item_category_id (تصنيف التصميم المستقل).
    """
    sql = """
        SELECT DISTINCT d.id, d.name, d.item_category_id, d.notes,
               d.created_at, d.updated_at,
               ic.name AS category_name,
               ic.color AS category_color
        FROM   designs d
        LEFT JOIN design_item_categories ic ON ic.id = d.item_category_id
    """
    params = []

    if set_id is not None:
        sql += """
            JOIN design_dimensions dd ON dd.design_id = d.id
                AND dd.set_id = ?
        """
        params.append(set_id)

    conditions = []
    if category_id is not None:
        conditions.append("d.item_category_id = ?")
        params.append(category_id)
    if name_q:
        conditions.append("d.name LIKE ?")
        params.append(f"%{name_q}%")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY d.updated_at DESC, d.name"
    return conn.execute(sql, params).fetchall()


def fetch_design(conn, design_id: int):
    return conn.execute("""
        SELECT d.id, d.name, d.item_category_id, d.notes,
               d.created_at, d.updated_at,
               ic.name AS category_name,
               ic.color AS category_color
        FROM   designs d
        LEFT JOIN design_item_categories ic ON ic.id = d.item_category_id
        WHERE  d.id = ?
    """, (design_id,)).fetchone()


def insert_design(conn, name: str, item_category_id: int = None,
                  notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO designs (name, item_category_id, notes) VALUES (?, ?, ?)",
        (name, item_category_id, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_design(conn, design_id: int, name: str,
                  item_category_id: int = None, notes: str = ""):
    conn.execute(
        "UPDATE designs SET name=?, item_category_id=?, notes=?, "
        "updated_at=datetime('now') WHERE id=?",
        (name, item_category_id, notes or "", design_id)
    )
    conn.commit()


def delete_design(conn, design_id: int):
    conn.execute("DELETE FROM designs WHERE id=?", (design_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# ربط التصميم بالمقاسات (design_dimensions) — legacy
# ══════════════════════════════════════════════════════════

def fetch_design_links(conn, design_id: int) -> list:
    return conn.execute("""
        SELECT dd.id, dd.design_id, dd.set_id, dd.label, dd.sort_order,
               ds.name AS set_name, ds.default_unit,
               dc.name AS category_name
        FROM   design_dimensions dd
        JOIN   dimension_sets ds ON ds.id = dd.set_id
        LEFT JOIN design_categories dc ON dc.id = ds.category_id
        ORDER  BY dd.sort_order, dd.id
    """).fetchall()


def fetch_design_links_for_design(conn, design_id: int) -> list:
    return conn.execute("""
        SELECT dd.id, dd.design_id, dd.set_id, dd.label, dd.sort_order,
               ds.name AS set_name, ds.default_unit
        FROM   design_dimensions dd
        JOIN   dimension_sets ds ON ds.id = dd.set_id
        WHERE  dd.design_id = ?
        ORDER  BY dd.sort_order, dd.id
    """, (design_id,)).fetchall()


def fetch_link(conn, link_id: int):
    return conn.execute(
        "SELECT id, design_id, set_id, label, sort_order "
        "FROM design_dimensions WHERE id=?", (link_id,)
    ).fetchone()


def add_design_link(conn, design_id: int, set_id: int,
                    label: str = "", sort_order: int = 0) -> int:
    cur = conn.execute(
        "INSERT INTO design_dimensions (design_id, set_id, label, sort_order)"
        " VALUES (?, ?, ?, ?)",
        (design_id, set_id, label or "", sort_order)
    )
    conn.commit()
    return cur.lastrowid


def remove_design_link(conn, link_id: int):
    conn.execute("DELETE FROM design_dimensions WHERE id=?", (link_id,))
    conn.commit()


def update_design_link_label(conn, link_id: int, label: str):
    conn.execute(
        "UPDATE design_dimensions SET label=? WHERE id=?",
        (label or "", link_id)
    )
    conn.commit()


# ══════════════════════════════════════════════════════════
# قيم الحقول
# ══════════════════════════════════════════════════════════

def fetch_dim_values(conn, link_id: int) -> dict:
    rows = conn.execute(
        "SELECT field_id, value_num, value_text, is_auto "
        "FROM design_dim_values WHERE link_id=?",
        (link_id,)
    ).fetchall()
    return {
        r["field_id"]: {
            "value_num":  r["value_num"],
            "value_text": r["value_text"],
            "is_auto":    r["is_auto"],
        }
        for r in rows
    }


def set_dim_value(conn, link_id: int, field_id: int,
                  value_num: float = None, value_text: str = None,
                  is_auto: bool = False):
    conn.execute(
        """INSERT INTO design_dim_values (link_id, field_id, value_num, value_text, is_auto)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(link_id, field_id) DO UPDATE SET
               value_num=excluded.value_num,
               value_text=excluded.value_text,
               is_auto=excluded.is_auto""",
        (link_id, field_id, value_num, value_text, 1 if is_auto else 0)
    )
    conn.commit()


def save_all_dim_values(conn, link_id: int,
                        values: dict[int, float | str],
                        auto_flags: dict[int, bool] = None):
    if auto_flags is None:
        auto_flags = {}
    for field_id, val in values.items():
        is_auto = auto_flags.get(field_id, False)
        if isinstance(val, str):
            set_dim_value(conn, link_id, field_id,
                          value_text=val, is_auto=is_auto)
        else:
            set_dim_value(conn, link_id, field_id,
                          value_num=float(val) if val is not None else None,
                          is_auto=is_auto)


def recalc_auto_values(conn, link_id: int) -> dict[int, float]:
    link = fetch_link(conn, link_id)
    if not link:
        return {}
    deps = conn.execute("""
        SELECT dep.field_id, dep.source_field_id, dep.offset
        FROM   dimension_field_deps dep
        JOIN   dimension_fields f ON f.id = dep.field_id
        WHERE  f.set_id = (
            SELECT set_id FROM design_dimensions WHERE id=?
        )
    """, (link_id,)).fetchall()
    computed = {}
    for dep in deps:
        val = calc_auto_value(conn, dep["field_id"], link_id)
        if val is not None:
            set_dim_value(conn, link_id, dep["field_id"],
                          value_num=val, is_auto=True)
            computed[dep["field_id"]] = val
    return computed


def fetch_full_design_data(conn, design_id: int) -> dict:
    design = fetch_design(conn, design_id)
    if not design:
        return {}
    links = fetch_design_links_for_design(conn, design_id)
    result = {
        "id":            design["id"],
        "name":          design["name"],
        "category_name": design["category_name"],
        "notes":         design["notes"],
        "links":         [],
    }
    for link in links:
        from db.designs.dimension_sets_repo import fetch_fields_for_set
        fields = fetch_fields_for_set(conn, link["set_id"])
        values = fetch_dim_values(conn, link["id"])
        link_data = {
            "link_id":  link["id"],
            "set_name": link["set_name"],
            "label":    link["label"] or link["set_name"],
            "unit":     link["default_unit"],
            "fields":   [],
        }
        for f in fields:
            val_info = values.get(f["id"], {})
            link_data["fields"].append({
                "id":      f["id"],
                "label":   f["label"],
                "unit":    f["unit"],
                "value":   val_info.get("value_num"),
                "is_auto": val_info.get("is_auto", False),
            })
        result["links"].append(link_data)
    return result