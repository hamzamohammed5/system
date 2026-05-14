"""
db/machine_op_rows_repo.py
===========================
عمليات قراءة/كتابة جدول machine_op_rows.

كل عملية تشغيل (machine_op) ممكن يكون ليها أكثر من صف.
كل صف: label + value + count
تكلفة الصف = (value × rate_per_hour ÷ 60)  ÷ count   [لو mode=time]
           = (value × rate_per_unit)         ÷ count   [لو mode=unit]

mode يُحدد من الماكينة المرتبطة بالعملية.
"""


def fetch_op_rows(conn, op_id: int) -> list:
    """كل الصفوف الخاصة بعملية تشغيل مرتبة."""
    return conn.execute(
        "SELECT id, op_id, label, value, count, sort_order "
        "FROM machine_op_rows WHERE op_id=? ORDER BY sort_order, id",
        (op_id,)
    ).fetchall()


def fetch_op_row(conn, row_id: int):
    return conn.execute(
        "SELECT id, op_id, label, value, count, sort_order "
        "FROM machine_op_rows WHERE id=?",
        (row_id,)
    ).fetchone()


def insert_op_row(conn, op_id: int, label: str = "",
                  value: float = 0.0, count: float = 1.0,
                  sort_order: int = 0) -> int:
    cur = conn.execute(
        "INSERT INTO machine_op_rows (op_id, label, value, count, sort_order)"
        " VALUES (?, ?, ?, ?, ?)",
        (op_id, label or "", value, max(count, 0.0001), sort_order)
    )
    conn.commit()
    return cur.lastrowid


def update_op_row(conn, row_id: int, label: str,
                  value: float, count: float, sort_order: int = 0):
    conn.execute(
        "UPDATE machine_op_rows SET label=?, value=?, count=?, sort_order=?"
        " WHERE id=?",
        (label or "", value, max(count, 0.0001), sort_order, row_id)
    )
    conn.commit()


def delete_op_row(conn, row_id: int):
    conn.execute("DELETE FROM machine_op_rows WHERE id=?", (row_id,))
    conn.commit()


def replace_op_rows(conn, op_id: int, rows: list[tuple]):
    """
    rows: list of (label, value, count)
    يحذف الصفوف القديمة ويضيف الجديدة.
    """
    conn.execute("DELETE FROM machine_op_rows WHERE op_id=?", (op_id,))
    for i, (label, value, count) in enumerate(rows):
        conn.execute(
            "INSERT INTO machine_op_rows (op_id, label, value, count, sort_order)"
            " VALUES (?, ?, ?, ?, ?)",
            (op_id, label or "", value, max(count, 0.0001), i)
        )
    conn.commit()


def calc_op_row_cost(conn, row_id: int) -> float:
    """
    يحسب تكلفة صف واحد:
    تكلفة = (value × rate) ÷ count
    rate يُحدد من الماكينة المرتبطة بالعملية + mode
    """
    row = fetch_op_row(conn, row_id)
    if not row:
        return 0.0

    op_data = conn.execute("""
        SELECT mo.mode, m.rate_per_hour, m.rate_per_unit
        FROM   machine_ops mo
        JOIN   machines m ON m.id = mo.machine_id
        WHERE  mo.id = ?
    """, (row["op_id"],)).fetchone()

    if not op_data:
        return 0.0

    value = float(row["value"])
    count = max(float(row["count"]), 0.0001)

    if op_data["mode"] == "time":
        raw_cost = (value / 60.0) * float(op_data["rate_per_hour"])
    else:
        raw_cost = value * float(op_data["rate_per_unit"])

    return raw_cost / count


def calc_op_total_cost(conn, op_id: int) -> float:
    """
    التكلفة الكلية للعملية = مجموع تكاليف كل الصفوف.
    (للتوافق مع الكود القديم الذي يحسب تكلفة العملية ككل)
    """
    rows = fetch_op_rows(conn, op_id)
    if not rows:
        return 0.0
    total = 0.0
    for row in rows:
        total += calc_op_row_cost(conn, row["id"])
    return total