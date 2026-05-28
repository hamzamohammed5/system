"""
db/orders/orders_repo.py
=========================
عمليات CRUD للطلبات وبنودها وسجل الحالة.

تحسين 21: delete_order يتحقق من paid_amount قبل الحذف.
تحسين 22: insert_order يتحقق من وجود العميل وكونه نشطاً.
"""

import datetime


# ══════════════════════════════════════════════════════════
# توليد رقم الطلب التلقائي
# ══════════════════════════════════════════════════════════

def _next_order_number(conn) -> str:
    year = datetime.date.today().year
    prefix = f"ORD-{year}-"
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(order_number, ?) AS INTEGER)) AS mx "
        "FROM orders WHERE order_number LIKE ?",
        (len(prefix) + 1, f"{prefix}%")
    ).fetchone()
    nxt = (row["mx"] or 0) + 1
    return f"{prefix}{nxt:04d}"


# ══════════════════════════════════════════════════════════
# جلب الطلبات
# ══════════════════════════════════════════════════════════

def fetch_all_orders(conn,
                     status: str = None,
                     customer_id: int = None,
                     order_type: str = None,
                     date_from: str = None,
                     date_to: str = None,
                     search: str = None) -> list:
    sql = """
        SELECT o.id, o.order_number, o.order_type, o.status,
               o.priority, o.order_date, o.due_date,
               o.total_amount, o.net_amount, o.paid_amount,
               o.created_at, o.updated_at,
               c.id   AS customer_id,
               c.name AS customer_name,
               c.code AS customer_code,
               c.phone AS customer_phone,
               r.order_number AS ref_order_number
        FROM   orders o
        JOIN   customers c ON c.id = o.customer_id
        LEFT JOIN orders r ON r.id = o.reference_order
    """
    conditions, params = [], []

    if status:
        conditions.append("o.status = ?")
        params.append(status)
    if customer_id:
        conditions.append("o.customer_id = ?")
        params.append(customer_id)
    if order_type:
        conditions.append("o.order_type = ?")
        params.append(order_type)
    if date_from:
        conditions.append("o.order_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("o.order_date <= ?")
        params.append(date_to)
    if search:
        conditions.append(
            "(o.order_number LIKE ? OR c.name LIKE ? OR c.code LIKE ?)"
        )
        q = f"%{search}%"
        params.extend([q, q, q])

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY o.created_at DESC"
    return conn.execute(sql, params).fetchall()


def fetch_order(conn, order_id: int):
    return conn.execute("""
        SELECT o.id, o.order_number, o.order_type, o.status,
               o.priority, o.order_date, o.due_date, o.delivery_date,
               o.total_amount, o.discount, o.net_amount,
               o.paid_amount, o.notes, o.internal_notes,
               o.reference_order, o.created_by,
               o.created_at, o.updated_at,
               c.id   AS customer_id,
               c.name AS customer_name,
               c.code AS customer_code,
               c.phone AS customer_phone,
               c.city  AS customer_city,
               r.order_number AS ref_order_number
        FROM   orders o
        JOIN   customers c ON c.id = o.customer_id
        LEFT JOIN orders r ON r.id = o.reference_order
        WHERE  o.id = ?
    """, (order_id,)).fetchone()


def fetch_customer_orders(conn, customer_id: int) -> list:
    return conn.execute("""
        SELECT id, order_number, order_type, status, priority,
               order_date, due_date, net_amount, paid_amount
        FROM   orders WHERE customer_id=?
        ORDER  BY created_at DESC
    """, (customer_id,)).fetchall()


# ══════════════════════════════════════════════════════════
# إضافة / تعديل / إلغاء الطلبات
# ══════════════════════════════════════════════════════════

def insert_order(conn,
                 customer_id: int,
                 order_type: str = "new",
                 status: str = "pending",
                 priority: str = "normal",
                 order_date: str = None,
                 due_date: str = None,
                 total_amount: float = 0,
                 discount: float = 0,
                 paid_amount: float = 0,
                 notes: str = "",
                 internal_notes: str = "",
                 reference_order: int = None,
                 created_by: str = "system") -> int:
    """
    [تحسين 22] يتحقق من وجود العميل وكونه نشطاً قبل إنشاء الطلب.
    يمنع إنشاء طلبات لعملاء محذوفين أو معطّلين.
    """
    customer = conn.execute(
        "SELECT id, is_active FROM customers WHERE id=?", (customer_id,)
    ).fetchone()
    if not customer:
        raise ValueError(f"العميل رقم {customer_id} غير موجود")
    if not customer["is_active"]:
        raise ValueError(
            f"العميل رقم {customer_id} غير نشط — فعّله أولاً لإنشاء طلبات جديدة"
        )

    order_number = _next_order_number(conn)
    net_amount   = total_amount - discount
    if order_date is None:
        order_date = datetime.date.today().isoformat()

    cur = conn.execute("""
        INSERT INTO orders
            (order_number, customer_id, order_type, status,
             priority, order_date, due_date,
             total_amount, discount, net_amount, paid_amount,
             notes, internal_notes, reference_order, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (order_number, customer_id, order_type, status,
          priority, order_date, due_date,
          total_amount, discount, net_amount, paid_amount,
          notes or "", internal_notes or "",
          reference_order, created_by))
    conn.commit()
    order_id = cur.lastrowid

    _log_status(conn, order_id, None, status, "إنشاء الطلب", created_by)
    return order_id


def update_order(conn, order_id: int,
                 priority: str = "normal",
                 due_date: str = None,
                 total_amount: float = 0,
                 discount: float = 0,
                 paid_amount: float = 0,
                 notes: str = "",
                 internal_notes: str = ""):
    net_amount = total_amount - discount
    conn.execute("""
        UPDATE orders
        SET priority=?, due_date=?,
            total_amount=?, discount=?, net_amount=?,
            paid_amount=?, notes=?, internal_notes=?,
            updated_at=datetime('now')
        WHERE id=?
    """, (priority, due_date, total_amount, discount, net_amount,
          paid_amount, notes or "", internal_notes or "", order_id))
    conn.commit()


def change_order_status(conn, order_id: int,
                         new_status: str,
                         notes: str = "",
                         changed_by: str = "system"):
    row = conn.execute(
        "SELECT status FROM orders WHERE id=?", (order_id,)
    ).fetchone()
    if not row:
        return False

    old_status = row["status"]
    delivery_date = None
    if new_status == "delivered":
        delivery_date = datetime.date.today().isoformat()

    conn.execute("""
        UPDATE orders
        SET status=?, delivery_date=COALESCE(?, delivery_date),
            updated_at=datetime('now')
        WHERE id=?
    """, (new_status, delivery_date, order_id))
    conn.commit()

    _log_status(conn, order_id, old_status, new_status, notes, changed_by)
    return True


def cancel_order(conn, order_id: int,
                 reason: str = "", changed_by: str = "system") -> bool:
    return change_order_status(conn, order_id, "cancelled",
                               notes=reason, changed_by=changed_by)


def reorder(conn, original_order_id: int,
            notes: str = "", created_by: str = "system") -> int:
    """إنشاء طلب جديد بناءً على طلب سابق (إعادة طلب)."""
    orig = fetch_order(conn, original_order_id)
    if not orig:
        return None

    new_id = insert_order(
        conn,
        customer_id=orig["customer_id"],
        order_type="reorder",
        priority=orig["priority"],
        notes=notes or f"إعادة طلب من: {orig['order_number']}",
        reference_order=original_order_id,
        created_by=created_by,
    )

    orig_items = fetch_order_items(conn, original_order_id)
    for item in orig_items:
        insert_order_item(
            conn, new_id,
            item_name=item["item_name"],
            description=item["description"] or "",
            quantity=item["quantity"],
            unit=item["unit"],
            unit_price=item["unit_price"],
            discount_pct=item["discount_pct"],
            design_ref=item["design_ref"] or "",
            notes=item["notes"] or "",
            sort_order=item["sort_order"],
        )
    _recalc_order_total(conn, new_id)
    return new_id


def delete_order(conn, order_id: int) -> bool:
    """
    يحذف الطلب نهائياً — فقط لو كان pending أو cancelled.

    [تحسين 21] يرفض الحذف لو paid_amount > 0
    لتجنب حذف طلب له مدفوعات مسجّلة.
    """
    row = conn.execute(
        "SELECT status, paid_amount FROM orders WHERE id=?", (order_id,)
    ).fetchone()
    if not row:
        return False
    if row["status"] not in ("pending", "cancelled"):
        return False
    # [تحسين 21] لا تحذف طلب له مدفوعات
    if row["paid_amount"] and float(row["paid_amount"]) > 0:
        return False
    conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    return True


# ══════════════════════════════════════════════════════════
# بنود الطلب
# ══════════════════════════════════════════════════════════

def fetch_order_items(conn, order_id: int) -> list:
    return conn.execute("""
        SELECT id, order_id, item_name, description,
               quantity, unit, unit_price, discount_pct,
               total_price, design_ref, notes, sort_order
        FROM   order_items WHERE order_id=?
        ORDER  BY sort_order, id
    """, (order_id,)).fetchall()


def insert_order_item(conn, order_id: int,
                       item_name: str,
                       description: str = "",
                       quantity: float = 1,
                       unit: str = "قطعة",
                       unit_price: float = 0,
                       discount_pct: float = 0,
                       design_ref: str = "",
                       notes: str = "",
                       sort_order: int = None) -> int:
    if sort_order is None:
        cnt = conn.execute(
            "SELECT COUNT(*) AS c FROM order_items WHERE order_id=?",
            (order_id,)
        ).fetchone()["c"]
        sort_order = cnt

    total = quantity * unit_price * (1 - discount_pct / 100)
    cur = conn.execute("""
        INSERT INTO order_items
            (order_id, item_name, description, quantity, unit,
             unit_price, discount_pct, total_price,
             design_ref, notes, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (order_id, item_name, description or "", quantity, unit,
          unit_price, discount_pct, total,
          design_ref or "", notes or "", sort_order))
    conn.commit()
    _recalc_order_total(conn, order_id)
    return cur.lastrowid


def update_order_item(conn, item_id: int,
                       item_name: str,
                       description: str = "",
                       quantity: float = 1,
                       unit: str = "قطعة",
                       unit_price: float = 0,
                       discount_pct: float = 0,
                       design_ref: str = "",
                       notes: str = ""):
    total = quantity * unit_price * (1 - discount_pct / 100)
    conn.execute("""
        UPDATE order_items
        SET item_name=?, description=?, quantity=?, unit=?,
            unit_price=?, discount_pct=?, total_price=?,
            design_ref=?, notes=?
        WHERE id=?
    """, (item_name, description or "", quantity, unit,
          unit_price, discount_pct, total,
          design_ref or "", notes or "", item_id))
    conn.commit()
    row = conn.execute(
        "SELECT order_id FROM order_items WHERE id=?", (item_id,)
    ).fetchone()
    if row:
        _recalc_order_total(conn, row["order_id"])


def delete_order_item(conn, item_id: int):
    row = conn.execute(
        "SELECT order_id FROM order_items WHERE id=?", (item_id,)
    ).fetchone()
    conn.execute("DELETE FROM order_items WHERE id=?", (item_id,))
    conn.commit()
    if row:
        _recalc_order_total(conn, row["order_id"])


def _recalc_order_total(conn, order_id: int):
    row = conn.execute(
        "SELECT SUM(total_price) AS t FROM order_items WHERE order_id=?",
        (order_id,)
    ).fetchone()
    total = row["t"] or 0.0
    disc_row = conn.execute(
        "SELECT discount, paid_amount FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()
    if disc_row:
        discount   = disc_row["discount"] or 0
        net_amount = total - discount
        conn.execute("""
            UPDATE orders
            SET total_amount=?, net_amount=?, updated_at=datetime('now')
            WHERE id=?
        """, (total, net_amount, order_id))
        conn.commit()


# ══════════════════════════════════════════════════════════
# سجل الحالة
# ══════════════════════════════════════════════════════════

def _log_status(conn, order_id: int, old_status, new_status: str,
                notes: str = "", changed_by: str = "system"):
    conn.execute("""
        INSERT INTO order_status_log
            (order_id, old_status, new_status, notes, changed_by)
        VALUES (?, ?, ?, ?, ?)
    """, (order_id, old_status, new_status, notes or "", changed_by))
    conn.commit()


def fetch_status_log(conn, order_id: int) -> list:
    return conn.execute("""
        SELECT id, old_status, new_status, notes, changed_by, changed_at
        FROM   order_status_log
        WHERE  order_id=?
        ORDER  BY changed_at ASC
    """, (order_id,)).fetchall()


# ══════════════════════════════════════════════════════════
# إحصائيات عامة للـ Dashboard
# ══════════════════════════════════════════════════════════

def fetch_orders_summary(conn) -> dict:
    row = conn.execute("""
        SELECT
            COUNT(*)                                                   AS total,
            SUM(CASE WHEN status='pending'     THEN 1 ELSE 0 END)     AS pending,
            SUM(CASE WHEN status='confirmed'   THEN 1 ELSE 0 END)     AS confirmed,
            SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END)     AS in_progress,
            SUM(CASE WHEN status='ready'       THEN 1 ELSE 0 END)     AS ready,
            SUM(CASE WHEN status='delivered'   THEN 1 ELSE 0 END)     AS delivered,
            SUM(CASE WHEN status='cancelled'   THEN 1 ELSE 0 END)     AS cancelled,
            SUM(CASE WHEN status='on_hold'     THEN 1 ELSE 0 END)     AS on_hold,
            SUM(CASE WHEN priority='urgent'    THEN 1 ELSE 0 END)     AS urgent,
            SUM(net_amount)                                            AS total_value,
            SUM(paid_amount)                                           AS total_paid
        FROM orders
    """).fetchone()
    return dict(row) if row else {}