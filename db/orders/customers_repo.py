"""
db/orders/customers_repo.py
============================
عمليات CRUD للعملاء وجهات الاتصال.

إصلاح 15: _next_customer_code تستخدم GLOB بدل LIKE للتحقق من
           الصيغة الرقمية قبل CAST، لتجنب تكرار CUS-0001 عند وجود
           كودات بصيغة غير رقمية مثل "CUS-abc".
"""


# ══════════════════════════════════════════════════════════
# توليد الكود التلقائي
# ══════════════════════════════════════════════════════════

def _next_customer_code(conn) -> str:
    """
    [إصلاح 15] يستخدم GLOB 'CUS-[0-9]*' للتحقق من الصيغة الرقمية
    قبل CAST، بدلاً من LIKE 'CUS-%' الذي يقبل أي لاحقة نصية.

    مشكلة النسخة القديمة:
      - CAST("abc" AS INTEGER) = 0 بصمت → يُعيد CUS-0001 مجدداً
      - ينتهك الـ UNIQUE constraint على عمود code

    الحل:
      - GLOB 'CUS-[0-9]*' تُطابق CUS- متبوعاً برقم واحد على الأقل
      - بالتالي CAST آمن دائماً
    """
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(code, 5) AS INTEGER)) as mx "
        "FROM customers WHERE code GLOB 'CUS-[0-9]*'"
    ).fetchone()
    nxt = (row["mx"] or 0) + 1
    return f"CUS-{nxt:04d}"


# ══════════════════════════════════════════════════════════
# جلب العملاء
# ══════════════════════════════════════════════════════════

def fetch_all_customers(conn, active_only: bool = False) -> list:
    sql = """
        SELECT c.id, c.code, c.name, c.customer_type,
               c.phone, c.phone2, c.email, c.city,
               c.is_active, c.created_at, c.updated_at,
               COUNT(o.id) AS orders_count
        FROM   customers c
        LEFT JOIN orders o ON o.customer_id = c.id
    """
    if active_only:
        sql += " WHERE c.is_active = 1"
    sql += " GROUP BY c.id ORDER BY c.name"
    return conn.execute(sql).fetchall()


def fetch_customer(conn, customer_id: int):
    return conn.execute("""
        SELECT id, code, name, customer_type,
               phone, phone2, email, address,
               city, notes, is_active,
               created_at, updated_at
        FROM   customers WHERE id = ?
    """, (customer_id,)).fetchone()


def search_customers(conn, query: str, limit: int = 20) -> list:
    """بحث بالاسم أو الكود أو الهاتف."""
    q = f"%{query}%"
    return conn.execute("""
        SELECT id, code, name, customer_type, phone, city, is_active
        FROM   customers
        WHERE  (name LIKE ? OR code LIKE ? OR phone LIKE ? OR phone2 LIKE ?)
          AND  is_active = 1
        ORDER  BY name
        LIMIT  ?
    """, (q, q, q, q, limit)).fetchall()


def fetch_customer_stats(conn, customer_id: int) -> dict:
    """إحصائيات عميل معين."""
    row = conn.execute("""
        SELECT
            COUNT(*)                                    AS total_orders,
            SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) AS delivered,
            SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) AS cancelled,
            SUM(CASE WHEN status NOT IN ('delivered','cancelled') THEN 1 ELSE 0 END) AS active,
            SUM(net_amount)                             AS total_value,
            SUM(paid_amount)                            AS total_paid,
            MAX(order_date)                             AS last_order_date
        FROM orders WHERE customer_id = ?
    """, (customer_id,)).fetchone()
    return dict(row) if row else {}


# ══════════════════════════════════════════════════════════
# إضافة / تعديل / حذف العملاء
# ══════════════════════════════════════════════════════════

def insert_customer(conn,
                    name: str,
                    customer_type: str = "individual",
                    phone: str = "",
                    phone2: str = "",
                    email: str = "",
                    address: str = "",
                    city: str = "",
                    notes: str = "") -> int:
    code = _next_customer_code(conn)
    cur = conn.execute("""
        INSERT INTO customers
            (code, name, customer_type, phone, phone2,
             email, address, city, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, name, customer_type, phone or "", phone2 or "",
          email or "", address or "", city or "", notes or ""))
    conn.commit()
    return cur.lastrowid


def update_customer(conn, customer_id: int,
                    name: str,
                    customer_type: str = "individual",
                    phone: str = "",
                    phone2: str = "",
                    email: str = "",
                    address: str = "",
                    city: str = "",
                    notes: str = "",
                    is_active: int = 1):
    conn.execute("""
        UPDATE customers
        SET name=?, customer_type=?, phone=?, phone2=?,
            email=?, address=?, city=?, notes=?,
            is_active=?, updated_at=datetime('now')
        WHERE id=?
    """, (name, customer_type, phone or "", phone2 or "",
          email or "", address or "", city or "", notes or "",
          is_active, customer_id))
    conn.commit()


def delete_customer(conn, customer_id: int) -> bool:
    """
    يحاول الحذف — يرفض لو في طلبات مرتبطة.
    يرجع True لو نجح.
    """
    cnt = conn.execute(
        "SELECT COUNT(*) AS c FROM orders WHERE customer_id=?",
        (customer_id,)
    ).fetchone()["c"]
    if cnt > 0:
        return False
    conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.commit()
    return True


def toggle_customer_active(conn, customer_id: int):
    conn.execute(
        "UPDATE customers SET is_active = 1 - is_active, updated_at=datetime('now') WHERE id=?",
        (customer_id,)
    )
    conn.commit()


# ══════════════════════════════════════════════════════════
# جهات الاتصال
# ══════════════════════════════════════════════════════════

def fetch_contacts(conn, customer_id: int) -> list:
    return conn.execute(
        "SELECT id, name, role, phone, email, notes"
        " FROM customer_contacts WHERE customer_id=? ORDER BY id",
        (customer_id,)
    ).fetchall()


def insert_contact(conn, customer_id: int, name: str,
                   role: str = "", phone: str = "",
                   email: str = "", notes: str = "") -> int:
    cur = conn.execute("""
        INSERT INTO customer_contacts
            (customer_id, name, role, phone, email, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_id, name, role or "", phone or "",
          email or "", notes or ""))
    conn.commit()
    return cur.lastrowid


def update_contact(conn, contact_id: int, name: str,
                   role: str = "", phone: str = "",
                   email: str = "", notes: str = ""):
    conn.execute("""
        UPDATE customer_contacts
        SET name=?, role=?, phone=?, email=?, notes=?
        WHERE id=?
    """, (name, role or "", phone or "", email or "", notes or "", contact_id))
    conn.commit()


def delete_contact(conn, contact_id: int):
    conn.execute("DELETE FROM customer_contacts WHERE id=?", (contact_id,))
    conn.commit()