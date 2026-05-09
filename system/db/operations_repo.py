"""
db/operations_repo.py
=====================
كل عمليات قراءة/كتابة جداول machines و labor_ops و machine_ops.
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


def delete_machine(conn, machine_id: int):
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