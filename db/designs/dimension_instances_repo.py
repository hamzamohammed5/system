"""
db/designs/dimension_instances_repo.py
========================================
عمليات CRUD لـ Instances مجموعات المقاسات وقيمها.

مستخرج من dimension_sets_repo.py (تحسين 46 — تقسيم الملف الضخم).

الجداول المغطاة:
  - dimension_set_instances  → إنشاء / تعديل / حذف instances
  - dimension_set_values     → قيم الحقول لكل instance
"""


# ══════════════════════════════════════════════════════════
# Instances — CRUD
# ══════════════════════════════════════════════════════════

def fetch_instances_for_set(conn, set_id: int) -> list:
    """كل instances مجموعة مقاسات مرتبة."""
    return conn.execute(
        "SELECT id, set_id, name, sort_order, notes, created_at"
        " FROM dimension_set_instances"
        " WHERE set_id=?"
        " ORDER BY sort_order, id",
        (set_id,)
    ).fetchall()


def fetch_instance(conn, instance_id: int):
    return conn.execute(
        "SELECT id, set_id, name, sort_order, notes"
        " FROM dimension_set_instances WHERE id=?",
        (instance_id,)
    ).fetchone()


def insert_instance(conn, set_id: int, name: str = "",
                    notes: str = "", sort_order: int = None) -> int:
    if sort_order is None:
        cnt = conn.execute(
            "SELECT COUNT(*) as c FROM dimension_set_instances WHERE set_id=?",
            (set_id,)
        ).fetchone()["c"]
        sort_order = cnt
    cur = conn.execute(
        "INSERT INTO dimension_set_instances (set_id, name, sort_order, notes)"
        " VALUES (?, ?, ?, ?)",
        (set_id, name or "", sort_order, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_instance(conn, instance_id: int, name: str, notes: str = ""):
    conn.execute(
        "UPDATE dimension_set_instances SET name=?, notes=? WHERE id=?",
        (name or "", notes or "", instance_id)
    )
    conn.commit()


def delete_instance(conn, instance_id: int):
    conn.execute(
        "DELETE FROM dimension_set_instances WHERE id=?",
        (instance_id,)
    )
    conn.commit()


def duplicate_instance(conn, instance_id: int, new_name: str) -> "int | None":
    """
    ينسخ instance موجود (كل قيمه) ويعيد ID الجديد.
    مفيد لإنشاء مقاس مشابه بسرعة.
    """
    src = fetch_instance(conn, instance_id)
    if not src:
        return None
    new_id = insert_instance(conn, src["set_id"], new_name)
    vals = conn.execute(
        "SELECT field_id, value_num, value_text"
        " FROM dimension_set_values WHERE instance_id=?",
        (instance_id,)
    ).fetchall()
    for v in vals:
        conn.execute(
            "INSERT INTO dimension_set_values"
            " (set_id, field_id, instance_id, value_num, value_text)"
            " VALUES (?, ?, ?, ?, ?)",
            (src["set_id"], v["field_id"], new_id,
             v["value_num"], v["value_text"])
        )
    conn.commit()
    return new_id


# ══════════════════════════════════════════════════════════
# قيم Instance
# ══════════════════════════════════════════════════════════

def fetch_instance_values(conn, instance_id: int) -> dict:
    """
    يرجع dict: {field_id: {"value_num": float|None, "value_text": str}}
    """
    rows = conn.execute(
        "SELECT field_id, value_num, value_text"
        " FROM dimension_set_values WHERE instance_id=?",
        (instance_id,)
    ).fetchall()
    return {
        r["field_id"]: {
            "value_num":  r["value_num"],
            "value_text": r["value_text"] or "",
        }
        for r in rows
    }


def save_instance_values(conn, instance_id: int, set_id: int,
                          values: dict) -> None:
    """
    values: {field_id: float | None}
    يحفظ كل قيم الـ instance دفعة واحدة.
    """
    for field_id, val in values.items():
        conn.execute("""
            INSERT INTO dimension_set_values
                (set_id, field_id, instance_id, value_num)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(instance_id, field_id) DO UPDATE SET
                value_num = excluded.value_num
        """, (set_id, field_id, instance_id, val))
    conn.commit()


def calc_instance_cross_auto(conn, field_id: int,
                              instance_id: int) -> "float | None":
    """
    يحسب القيمة التلقائية لحقل في instance معين.
    يدعم cross-set: source_set_id → يبحث عن أول instance في المجموعة المصدر.

    يرجع float أو None لو القيمة المصدر غير موجودة.
    """
    dep = conn.execute(
        "SELECT source_field_id, source_set_id, offset"
        " FROM dimension_field_deps WHERE field_id=?",
        (field_id,)
    ).fetchone()
    if not dep:
        return None

    source_field_id = dep["source_field_id"]
    offset          = float(dep["offset"])

    if dep["source_set_id"] is None:
        # نفس المجموعة → نفس الـ instance
        source_instance_id = instance_id
    else:
        # مجموعة أخرى → نأخذ أول instance فيها
        src_inst = conn.execute(
            "SELECT id FROM dimension_set_instances WHERE set_id=?"
            " ORDER BY sort_order, id LIMIT 1",
            (dep["source_set_id"],)
        ).fetchone()
        if not src_inst:
            return None
        source_instance_id = src_inst["id"]

    val_row = conn.execute(
        "SELECT value_num FROM dimension_set_values"
        " WHERE instance_id=? AND field_id=?",
        (source_instance_id, source_field_id)
    ).fetchone()

    if not val_row or val_row["value_num"] is None:
        return None

    return float(val_row["value_num"]) + offset


# ══════════════════════════════════════════════════════════
# قيم المجموعة المستقلة — Legacy (للتوافق مع الكود القديم)
# ══════════════════════════════════════════════════════════

def fetch_standalone_values(conn, set_id: int) -> dict:
    """
    Legacy — يرجع قيم أول instance للمجموعة.
    يُستخدم للتوافق مع الكود القديم اللي كان يستدعي هذه الدالة.
    """
    inst = conn.execute(
        "SELECT id FROM dimension_set_instances WHERE set_id=?"
        " ORDER BY sort_order, id LIMIT 1",
        (set_id,)
    ).fetchone()
    if not inst:
        return {}
    return fetch_instance_values(conn, inst["id"])


def save_standalone_value(conn, set_id: int, field_id: int,
                           value_num: float = None, value_text: str = None):
    """
    Legacy — يحفظ قيمة في أول instance للمجموعة.
    لو مفيش instance → ينشئ واحد تلقائياً.
    """
    inst = conn.execute(
        "SELECT id FROM dimension_set_instances WHERE set_id=?"
        " ORDER BY sort_order, id LIMIT 1",
        (set_id,)
    ).fetchone()
    if not inst:
        inst_id = insert_instance(conn, set_id, "")
    else:
        inst_id = inst["id"]

    conn.execute("""
        INSERT INTO dimension_set_values
            (set_id, field_id, instance_id, value_num, value_text)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(instance_id, field_id) DO UPDATE SET
            value_num  = excluded.value_num,
            value_text = excluded.value_text
    """, (set_id, field_id, inst_id, value_num, value_text))
    conn.commit()


def fetch_source_set_values(conn, source_set_id: int) -> dict:
    """
    يجلب قيم أول instance لمجموعة مقاسات محددة.
    يرجع dict: {field_id: {"value_num", "value_text", "label", "unit"}}
    """
    inst = conn.execute(
        "SELECT id FROM dimension_set_instances WHERE set_id=?"
        " ORDER BY sort_order, id LIMIT 1",
        (source_set_id,)
    ).fetchone()
    if not inst:
        return {}

    rows = conn.execute("""
        SELECT dsv.field_id, dsv.value_num, dsv.value_text,
               df.label, df.unit
        FROM   dimension_set_values dsv
        JOIN   dimension_fields df ON df.id = dsv.field_id
        WHERE  dsv.instance_id = ?
    """, (inst["id"],)).fetchall()

    return {
        r["field_id"]: {
            "value_num":  r["value_num"],
            "value_text": r["value_text"] or "",
            "label":      r["label"],
            "unit":       r["unit"] or "",
        }
        for r in rows
    }


def calc_standalone_cross_auto(conn, field_id: int,
                                current_set_id: int) -> "float | None":
    """
    Legacy — يحسب القيمة التلقائية في وضع الإدخال المستقل.
    يستخدم أول instance للمجموعة الحالية.
    """
    inst = conn.execute(
        "SELECT id FROM dimension_set_instances WHERE set_id=?"
        " ORDER BY sort_order, id LIMIT 1",
        (current_set_id,)
    ).fetchone()
    if not inst:
        return None
    return calc_instance_cross_auto(conn, field_id, inst["id"])


def get_source_ref(conn, field_id: int, current_set_id: int) -> "dict | None":
    """
    Legacy — يجيب بيانات المصدر لعرض الـ reference label.
    يرجع dict أو None.
    """
    dep = conn.execute(
        "SELECT source_field_id, source_set_id, offset"
        " FROM dimension_field_deps WHERE field_id=?",
        (field_id,)
    ).fetchone()
    if not dep:
        return None

    source_field_id = dep["source_field_id"]
    source_set_id   = dep["source_set_id"] if dep["source_set_id"] else current_set_id
    offset          = float(dep["offset"])

    src_inst = conn.execute(
        "SELECT id FROM dimension_set_instances WHERE set_id=?"
        " ORDER BY sort_order, id LIMIT 1",
        (source_set_id,)
    ).fetchone()
    if not src_inst:
        return None

    row = conn.execute(
        "SELECT dsv.value_num, ds.name AS set_name"
        " FROM dimension_set_values dsv"
        " JOIN dimension_sets ds ON ds.id = dsv.set_id"
        " WHERE dsv.instance_id=? AND dsv.field_id=?",
        (src_inst["id"], source_field_id)
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