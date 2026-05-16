"""
db/designs/dimension_sets_repo.py
==================================
عمليات قراءة/كتابة مجموعات المقاسات وحقولها واعتمادياتها.

التغييرات:
  - حذف كل دوال design_categories واستبدالها بـ parent_set (تدرج هرمي بين المجموعات)
  - إضافة دوال جلسات الإدخال المستقلة (dimension_value_sessions)
"""


# ══════════════════════════════════════════════════════════
# مجموعات المقاسات — مع دعم parent_set_id
# ══════════════════════════════════════════════════════════

def fetch_all_dimension_sets(conn) -> list:
    return conn.execute("""
        SELECT ds.id, ds.name, ds.parent_set_id, ds.default_unit, ds.notes,
               ps.name AS parent_set_name
        FROM   dimension_sets ds
        LEFT JOIN dimension_sets ps ON ps.id = ds.parent_set_id
        ORDER  BY ds.parent_set_id NULLS FIRST, ds.name
    """).fetchall()


def fetch_dimension_set(conn, set_id: int):
    return conn.execute("""
        SELECT ds.id, ds.name, ds.parent_set_id, ds.default_unit, ds.notes,
               ps.name AS parent_set_name
        FROM   dimension_sets ds
        LEFT JOIN dimension_sets ps ON ps.id = ds.parent_set_id
        WHERE  ds.id = ?
    """, (set_id,)).fetchone()


def insert_dimension_set(conn, name: str, parent_set_id: int = None,
                          default_unit: str = "cm", notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO dimension_sets (name, parent_set_id, default_unit, notes)"
        " VALUES (?, ?, ?, ?)",
        (name, parent_set_id, default_unit or "cm", notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_dimension_set(conn, set_id: int, name: str,
                          parent_set_id: int = None, default_unit: str = "cm",
                          notes: str = ""):
    conn.execute(
        "UPDATE dimension_sets SET name=?, parent_set_id=?, default_unit=?, notes=?"
        " WHERE id=?",
        (name, parent_set_id, default_unit or "cm", notes or "", set_id)
    )
    conn.commit()


def delete_dimension_set(conn, set_id: int):
    conn.execute("DELETE FROM dimension_sets WHERE id=?", (set_id,))
    conn.commit()


def build_sets_tree(rows) -> list:
    """يبني شجرة هرمية من قائمة المجموعات."""
    nodes = {
        r["id"]: {
            "id":            r["id"],
            "name":          r["name"],
            "parent_set_id": r["parent_set_id"],
            "default_unit":  r["default_unit"],
            "notes":         r["notes"] if "notes" in r.keys() else "",
            "children":      [],
        }
        for r in rows
    }
    roots = []
    for node in nodes.values():
        pid = node["parent_set_id"]
        if pid and pid in nodes:
            nodes[pid]["children"].append(node)
        else:
            roots.append(node)
    return roots


def fetch_set_descendants(conn, set_id: int) -> list:
    """يجيب كل أحفاد مجموعة (بشكل متكرر) بما فيها هي."""
    result, queue = set(), [set_id]
    while queue:
        cur = queue.pop()
        if cur in result:
            continue
        result.add(cur)
        children = conn.execute(
            "SELECT id FROM dimension_sets WHERE parent_set_id=?", (cur,)
        ).fetchall()
        queue.extend(r["id"] for r in children)
    return list(result)


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
    كل الحقول الرقمية من كل المجموعات مرتبة بالمجموعة.
    كل صف: field_id, field_label, set_id, set_name
    """
    sql = """
        SELECT f.id      AS field_id,
               f.label   AS field_label,
               f.set_id,
               ds.name   AS set_name
        FROM   dimension_fields f
        JOIN   dimension_sets ds ON ds.id = f.set_id
        WHERE  f.field_type = 'number'
    """
    params = []
    if exclude_field_id is not None:
        sql += " AND f.id != ?"
        params.append(exclude_field_id)
    sql += " ORDER BY ds.name, f.sort_order, f.id"
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
# جلسات الإدخال المستقلة
# ══════════════════════════════════════════════════════════

def fetch_sessions_for_set(conn, set_id: int) -> list:
    """كل جلسات الإدخال الخاصة بمجموعة معينة."""
    return conn.execute("""
        SELECT id, set_id, name, notes, created_at, updated_at
        FROM   dimension_value_sessions
        WHERE  set_id = ?
        ORDER  BY updated_at DESC, id DESC
    """, (set_id,)).fetchall()


def fetch_session(conn, session_id: int):
    return conn.execute(
        "SELECT id, set_id, name, notes, created_at, updated_at "
        "FROM dimension_value_sessions WHERE id=?",
        (session_id,)
    ).fetchone()


def insert_session(conn, set_id: int, name: str, notes: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO dimension_value_sessions (set_id, name, notes) VALUES (?, ?, ?)",
        (set_id, name or "جلسة جديدة", notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_session(conn, session_id: int, name: str, notes: str = ""):
    conn.execute(
        "UPDATE dimension_value_sessions SET name=?, notes=?,"
        " updated_at=datetime('now') WHERE id=?",
        (name or "جلسة جديدة", notes or "", session_id)
    )
    conn.commit()


def delete_session(conn, session_id: int):
    conn.execute(
        "DELETE FROM dimension_value_sessions WHERE id=?", (session_id,)
    )
    conn.commit()


def fetch_session_values(conn, session_id: int) -> dict:
    """يرجع {field_id: value_num} لجلسة معينة."""
    rows = conn.execute(
        "SELECT field_id, value_num FROM dimension_set_values WHERE session_id=?",
        (session_id,)
    ).fetchall()
    return {r["field_id"]: r["value_num"] for r in rows}


def save_session_value(conn, session_id: int, set_id: int,
                        field_id: int, value_num: float = None):
    conn.execute("""
        INSERT INTO dimension_set_values (session_id, set_id, field_id, value_num)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id, field_id) DO UPDATE SET value_num=excluded.value_num
    """, (session_id, set_id, field_id, value_num))
    conn.commit()


def calc_standalone_cross_auto(conn, field_id: int, current_set_id: int,
                                session_id: int = None):
    """
    يحسب القيمة التلقائية في وضع الإدخال المستقل.
    يبحث في dimension_set_values بالـ session_id أو بالـ set_id.
    """
    dep = fetch_field_dep(conn, field_id)
    if not dep:
        return None

    source_field_id = dep["source_field_id"]
    source_set_id   = dep["source_set_id"] if dep["source_set_id"] else current_set_id
    offset          = float(dep["offset"])

    if session_id is not None:
        # نبحث في نفس الجلسة أولاً
        val_row = conn.execute(
            "SELECT value_num FROM dimension_set_values "
            "WHERE session_id=? AND field_id=?",
            (session_id, source_field_id)
        ).fetchone()
        if val_row and val_row["value_num"] is not None:
            return float(val_row["value_num"]) + offset

    # fallback: أحدث قيمة للحقل المصدر في نفس المجموعة
    val_row = conn.execute("""
        SELECT dsv.value_num
        FROM   dimension_set_values dsv
        JOIN   dimension_value_sessions ses ON ses.id = dsv.session_id
        WHERE  ses.set_id = ? AND dsv.field_id = ?
        ORDER  BY ses.updated_at DESC
        LIMIT  1
    """, (source_set_id, source_field_id)).fetchone()

    if not val_row or val_row["value_num"] is None:
        return None

    return float(val_row["value_num"]) + offset