"""
db/designs/designs_sizes_repo.py
=================================
عمليات CRUD لجدول design_sizes —
ربط التصميمات بالمقاسات الفعلية (instances) + مسارات GIMP.
"""


# ══════════════════════════════════════════════════════════
# جلب مقاسات تصميم
# ══════════════════════════════════════════════════════════

def fetch_design_sizes(conn, design_id: int) -> list:
    """
    كل مقاسات تصميم معين مع بيانات المجموعة والـ instance.
    """
    return conn.execute("""
        SELECT
            ds.id,
            ds.design_id,
            ds.set_id,
            ds.instance_id,
            ds.width_field_id,
            ds.height_field_id,
            ds.dpi_field_id,
            ds.xcf_path,
            ds.notes,
            ds.sort_order,
            ds.created_at,
            dset.name    AS set_name,
            inst.name    AS instance_name,
            wf.label     AS width_label,
            hf.label     AS height_label,
            df.label     AS dpi_label
        FROM   design_sizes ds
        JOIN   dimension_sets dset          ON dset.id = ds.set_id
        JOIN   dimension_set_instances inst  ON inst.id = ds.instance_id
        LEFT JOIN dimension_fields wf        ON wf.id   = ds.width_field_id
        LEFT JOIN dimension_fields hf        ON hf.id   = ds.height_field_id
        LEFT JOIN dimension_fields df        ON df.id   = ds.dpi_field_id
        WHERE  ds.design_id = ?
        ORDER  BY ds.sort_order, ds.id
    """, (design_id,)).fetchall()


def fetch_design_size(conn, size_id: int):
    """مقاس واحد بكل بياناته."""
    return conn.execute("""
        SELECT
            ds.id,
            ds.design_id,
            ds.set_id,
            ds.instance_id,
            ds.width_field_id,
            ds.height_field_id,
            ds.dpi_field_id,
            ds.xcf_path,
            ds.notes,
            ds.sort_order,
            dset.name    AS set_name,
            inst.name    AS instance_name,
            wf.label     AS width_label,
            hf.label     AS height_label,
            df.label     AS dpi_label
        FROM   design_sizes ds
        JOIN   dimension_sets dset          ON dset.id = ds.set_id
        JOIN   dimension_set_instances inst  ON inst.id = ds.instance_id
        LEFT JOIN dimension_fields wf        ON wf.id   = ds.width_field_id
        LEFT JOIN dimension_fields hf        ON hf.id   = ds.height_field_id
        LEFT JOIN dimension_fields df        ON df.id   = ds.dpi_field_id
        WHERE  ds.id = ?
    """, (size_id,)).fetchone()


# ══════════════════════════════════════════════════════════
# إضافة / تعديل / حذف
# ══════════════════════════════════════════════════════════

def insert_design_size(conn, design_id: int, set_id: int, instance_id: int,
                       width_field_id: int = None, height_field_id: int = None,
                       xcf_path: str = None, notes: str = "",
                       sort_order: int = None,
                       dpi_field_id: int = None) -> int:
    if sort_order is None:
        cnt = conn.execute(
            "SELECT COUNT(*) as c FROM design_sizes WHERE design_id=?",
            (design_id,)
        ).fetchone()["c"]
        sort_order = cnt

    cur = conn.execute(
        """INSERT INTO design_sizes
           (design_id, set_id, instance_id, width_field_id, height_field_id,
            dpi_field_id, xcf_path, notes, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (design_id, set_id, instance_id, width_field_id, height_field_id,
         dpi_field_id, xcf_path or None, notes or "", sort_order)
    )
    conn.commit()
    return cur.lastrowid


def update_design_size(conn, size_id: int,
                       width_field_id: int = None, height_field_id: int = None,
                       xcf_path: str = None, notes: str = "",
                       dpi_field_id: int = None):
    conn.execute(
        """UPDATE design_sizes
           SET width_field_id=?, height_field_id=?, dpi_field_id=?,
               xcf_path=?, notes=?
           WHERE id=?""",
        (width_field_id, height_field_id, dpi_field_id,
         xcf_path or None, notes or "", size_id)
    )
    conn.commit()


def update_design_size_path(conn, size_id: int, xcf_path: str):
    """تحديث مسار الملف فقط."""
    conn.execute(
        "UPDATE design_sizes SET xcf_path=? WHERE id=?",
        (xcf_path or None, size_id)
    )
    conn.commit()


def delete_design_size(conn, size_id: int):
    conn.execute("DELETE FROM design_sizes WHERE id=?", (size_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# مساعدات الـ instance + قيمه
# ══════════════════════════════════════════════════════════

def fetch_canvas_size(conn, size_id: int) -> tuple[float | None, float | None]:
    """
    يرجع (width_val, height_val) من قيم الـ instance.
    يرجع (None, None) لو الحقول غير محددة أو القيم ناقصة.
    """
    row = conn.execute(
        "SELECT instance_id, width_field_id, height_field_id FROM design_sizes WHERE id=?",
        (size_id,)
    ).fetchone()
    if not row:
        return None, None

    w_val = h_val = None

    if row["width_field_id"]:
        r = conn.execute(
            "SELECT value_num FROM dimension_set_values WHERE instance_id=? AND field_id=?",
            (row["instance_id"], row["width_field_id"])
        ).fetchone()
        if r:
            w_val = r["value_num"]

    if row["height_field_id"]:
        r = conn.execute(
            "SELECT value_num FROM dimension_set_values WHERE instance_id=? AND field_id=?",
            (row["instance_id"], row["height_field_id"])
        ).fetchone()
        if r:
            h_val = r["value_num"]

    return w_val, h_val


def fetch_canvas_dpi(conn, size_id: int) -> float | None:
    """
    يرجع قيمة الـ DPI من حقل الـ instance المحدد.
    يرجع None لو الحقل غير محدد أو القيمة غير موجودة.
    """
    row = conn.execute(
        "SELECT instance_id, dpi_field_id FROM design_sizes WHERE id=?",
        (size_id,)
    ).fetchone()
    if not row or not row["dpi_field_id"]:
        return None

    r = conn.execute(
        "SELECT value_num FROM dimension_set_values WHERE instance_id=? AND field_id=?",
        (row["instance_id"], row["dpi_field_id"])
    ).fetchone()
    return float(r["value_num"]) if r and r["value_num"] is not None else None


def fetch_instances_for_set_with_values(conn, set_id: int) -> list:
    """
    كل instances مجموعة مقاسات مع قيم حقولها.
    يُستخدم في الـ combo لاختيار المقاس.
    """
    return conn.execute("""
        SELECT inst.id, inst.name, inst.sort_order
        FROM   dimension_set_instances inst
        WHERE  inst.set_id = ?
        ORDER  BY inst.sort_order, inst.id
    """, (set_id,)).fetchall()


def instance_already_used(conn, design_id: int, instance_id: int,
                           exclude_size_id: int = None) -> bool:
    """هل هذا الـ instance مضاف مسبقاً لهذا التصميم؟"""
    sql = "SELECT 1 FROM design_sizes WHERE design_id=? AND instance_id=?"
    params = [design_id, instance_id]
    if exclude_size_id:
        sql += " AND id != ?"
        params.append(exclude_size_id)
    return conn.execute(sql, params).fetchone() is not None


def fetch_all_designs_summary(conn) -> list:
    """
    كل التصميمات مع عدد المقاسات وعدد الملفات الموجودة.
    """
    return conn.execute("""
        SELECT
            d.id,
            d.name,
            d.notes,
            d.created_at,
            d.updated_at,
            dc.name                                    AS category_name,
            COUNT(ds.id)                               AS sizes_count,
            SUM(CASE WHEN ds.xcf_path IS NOT NULL AND ds.xcf_path != '' THEN 1 ELSE 0 END)
                                                       AS files_count
        FROM   designs d
        LEFT JOIN design_categories dc ON dc.id = d.category_id
        LEFT JOIN design_sizes ds      ON ds.design_id = d.id
        GROUP  BY d.id
        ORDER  BY d.updated_at DESC, d.name
    """).fetchall()