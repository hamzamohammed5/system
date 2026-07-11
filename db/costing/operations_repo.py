"""
db/costing/operations_repo.py
=====================
كل عمليات قراءة/كتابة جداول machines و labor_ops و machine_ops.

تحسين 19: إضافة count_machine_ops() للتحقق من عدد عمليات الماكينة
           قبل حذفها. الـ schema تحتوي CASCADE DELETE صامت على machine_ops
           عند حذف الماكينة، مما يحذف عمليات تشغيل بدون تحذير.
           الـ UI يجب أن يستدعي count_machine_ops() ويُظهر تأكيداً.
"""


# ══════════════════════════════════════════════════════════
# الماكينات
# ══════════════════════════════════════════════════════════

def fetch_all_machines(conn):
    return conn.execute("""
        SELECT m.id, m.name, m.rate_per_hour, m.rate_per_unit,
               m.category_id,
               c.name AS category_name
        FROM   machines m
        LEFT JOIN categories c ON c.id = m.category_id
        ORDER  BY m.name
    """).fetchall()


def fetch_machine(conn, machine_id: int):
    return conn.execute("""
        SELECT m.id, m.name, m.rate_per_hour, m.rate_per_unit,
               m.category_id,
               c.name AS category_name
        FROM   machines m
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE  m.id = ?
    """, (machine_id,)).fetchone()


def insert_machine(conn, name: str, rate_per_hour: float, rate_per_unit: float,
                   category_id: int = None) -> int:
    cur = conn.execute(
        "INSERT INTO machines (name, rate_per_hour, rate_per_unit, category_id) VALUES (?, ?, ?, ?)",
        (name, rate_per_hour, rate_per_unit, category_id)
    )
    conn.commit()
    return cur.lastrowid


def update_machine(conn, machine_id: int, name: str,
                   rate_per_hour: float, rate_per_unit: float,
                   category_id: int = None):
    conn.execute(
        "UPDATE machines SET name=?, rate_per_hour=?, rate_per_unit=?, category_id=? WHERE id=?",
        (name, rate_per_hour, rate_per_unit, category_id, machine_id)
    )
    conn.commit()


def count_machine_ops(conn, machine_id: int) -> int:
    """
    [تحسين 19] يرجع عدد عمليات التشغيل المرتبطة بماكينة معينة.

    يُستخدم قبل حذف الماكينة لتحذير المستخدم:
        ops_count = count_machine_ops(conn, machine_id)
        if ops_count > 0:
            confirm = QMessageBox.warning(
                self,
                "تأكيد الحذف",
                f"حذف هذه الماكينة سيحذف {ops_count} عملية تشغيل مرتبطة بها.\n"
                "هل تريد المتابعة؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return

    المشكلة:
        الـ schema تحتوي على:
            machine_ops.machine_id → REFERENCES machines(id) ON DELETE CASCADE
        مما يحذف كل machine_ops صامتاً عند حذف الماكينة.
        المستخدم قد لا يعرف أنه فقد عمليات تشغيل مهمة.
    """
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM machine_ops WHERE machine_id=?",
        (machine_id,)
    ).fetchone()
    return row["c"] if row else 0


def delete_machine(conn, machine_id: int):
    """
    يحذف الماكينة وكل عمليات التشغيل المرتبطة بها (CASCADE).

    تحذير: استدعِ count_machine_ops() أولاً في الـ UI لإبلاغ المستخدم.
    """
    conn.execute("DELETE FROM machines WHERE id=?", (machine_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# عمليات العمالة
# ══════════════════════════════════════════════════════════

def fetch_all_labor_ops(conn):
    return conn.execute("""
        SELECT lo.id, lo.name, lo.minutes,
               lo.category_id,
               c.name AS category_name
        FROM   labor_ops lo
        LEFT JOIN categories c ON c.id = lo.category_id
        ORDER  BY lo.name
    """).fetchall()


def fetch_labor_op(conn, op_id: int):
    return conn.execute("""
        SELECT lo.id, lo.name, lo.minutes,
               lo.category_id,
               c.name AS category_name
        FROM   labor_ops lo
        LEFT JOIN categories c ON c.id = lo.category_id
        WHERE  lo.id = ?
    """, (op_id,)).fetchone()


def insert_labor_op(conn, name: str, minutes: float,
                    category_id: int = None) -> int:
    cur = conn.execute(
        "INSERT INTO labor_ops (name, minutes, category_id) VALUES (?, ?, ?)",
        (name, minutes, category_id)
    )
    conn.commit()
    return cur.lastrowid


def update_labor_op(conn, op_id: int, name: str, minutes: float,
                    category_id: int = None):
    conn.execute(
        "UPDATE labor_ops SET name=?, minutes=?, category_id=? WHERE id=?",
        (name, minutes, category_id, op_id)
    )
    conn.commit()


def delete_labor_op(conn, op_id: int):
    conn.execute("DELETE FROM labor_ops WHERE id=?", (op_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# عمليات التشغيل
# ══════════════════════════════════════════════════════════

def fetch_all_machine_ops(conn):
    return conn.execute("""
        SELECT mo.id, mo.name, mo.mode, mo.value,
               mo.machine_id, mo.category_id,
               m.name  AS machine_name,
               m.rate_per_hour, m.rate_per_unit,
               c.name  AS category_name
        FROM   machine_ops mo
        JOIN   machines m ON m.id = mo.machine_id
        LEFT JOIN categories c ON c.id = mo.category_id
        ORDER  BY mo.name
    """).fetchall()


def fetch_machine_op(conn, op_id: int):
    return conn.execute("""
        SELECT mo.id, mo.name, mo.mode, mo.value,
               mo.machine_id, mo.category_id,
               m.name  AS machine_name,
               m.rate_per_hour, m.rate_per_unit,
               c.name  AS category_name
        FROM   machine_ops mo
        JOIN   machines m ON m.id = mo.machine_id
        LEFT JOIN categories c ON c.id = mo.category_id
        WHERE  mo.id = ?
    """, (op_id,)).fetchone()


def insert_machine_op(conn, machine_id: int, name: str,
                      mode: str, value: float,
                      category_id: int = None) -> int:
    cur = conn.execute(
        "INSERT INTO machine_ops (machine_id, name, mode, value, category_id) VALUES (?, ?, ?, ?, ?)",
        (machine_id, name, mode, value, category_id)
    )
    conn.commit()
    return cur.lastrowid


def update_machine_op(conn, op_id: int, machine_id: int,
                      name: str, mode: str, value: float,
                      category_id: int = None):
    conn.execute(
        "UPDATE machine_ops SET machine_id=?, name=?, mode=?, value=?, category_id=? WHERE id=?",
        (machine_id, name, mode, value, category_id, op_id)
    )
    conn.commit()


def delete_machine_op(conn, op_id: int):
    conn.execute("DELETE FROM machine_ops WHERE id=?", (op_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# مساعدات BOM (Bulk Replace)
# ══════════════════════════════════════════════════════════
#
# [إصلاح هيكلي] الدالتان التاليتان كانتا داخل:
#   ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py
# وهو مكان خاطئ — استعلامات SQL يجب أن تكون في db/ فقط.
# انتقلتا هنا حتى يستدعيهما services/costing/bulk_replace_service.py
# من db/costing مباشرة، بدون المرور عبر ui/.

def fetch_element_name(conn, child_type: str, child_id: int) -> "str | None":
    """
    يرجع اسم عنصر BOM حسب نوعه:
      - raw / semi   → من جدول items
      - labor_op     → من جدول labor_ops
      - machine_op   → من جدول machine_ops
    يرجع None لو غير موجود (المستدعي مسؤول عن fallback مثل f"ID:{id}").
    """
    if child_type in ("raw", "semi"):
        row = conn.execute(
            "SELECT name FROM items WHERE id=?", (child_id,)
        ).fetchone()
    elif child_type == "labor_op":
        row = conn.execute(
            "SELECT name FROM labor_ops WHERE id=?", (child_id,)
        ).fetchone()
    elif child_type == "machine_op":
        row = conn.execute(
            "SELECT name FROM machine_ops WHERE id=?", (child_id,)
        ).fetchone()
    else:
        row = None
    return row["name"] if row else None


def fetch_products_using_child(conn, child_type: str, child_id: int) -> list:
    """
    يرجع كل المنتجات (semi + final) التي تحتوي على child_id/child_type
    مباشرةً في جدول bom الرئيسي.

    كل صف يحتوي: parent_id, qty, name, type, category_id, category_name
    """
    return conn.execute("""
        SELECT b.parent_id, b.qty,
               i.name, i.type, i.category_id,
               c.name AS category_name
        FROM   bom b
        JOIN   items i ON i.id = b.parent_id
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE  b.child_type = ?
          AND  b.child_id   = ?
          AND  i.type IN ('semi','final')
        ORDER  BY i.name
    """, (child_type, child_id)).fetchall()