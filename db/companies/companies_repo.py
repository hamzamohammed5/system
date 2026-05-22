"""
db/companies/companies_repo.py
================================
عمليات CRUD للشركات والعناصر المشتركة.

إصلاح: كل central connections بتُفتح وتُغلق بشكل صحيح في try/finally
"""

import os
from db.companies.companies_schema import (
    get_central_connection,
    get_company_db_path,
    ensure_company_dir,
    create_central_tables,
)


# ══════════════════════════════════════════════════════════
# CRUD — الشركات
# ══════════════════════════════════════════════════════════

def fetch_all_companies(conn, active_only: bool = False) -> list:
    sql = """
        SELECT id, name, short_name, logo_path, color,
               is_active, notes, created_at, updated_at
        FROM companies
    """
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY name"
    return conn.execute(sql).fetchall()


def fetch_company(conn, company_id: int):
    return conn.execute(
        "SELECT * FROM companies WHERE id = ?", (company_id,)
    ).fetchone()


def insert_company(conn,
                   name: str,
                   short_name: str = "",
                   color: str = "#1565c0",
                   notes: str = "") -> int:
    """
    ينشئ الشركة في companies.db ومجلدها وملفات DB الخاصة بها.
    """
    cur = conn.execute(
        """INSERT INTO companies (name, short_name, color, notes)
           VALUES (?, ?, ?, ?)""",
        (name, short_name or "", color or "#1565c0", notes or "")
    )
    company_id = cur.lastrowid

    ensure_company_dir(company_id)
    _init_company_databases(company_id)

    return company_id


def update_company(conn, company_id: int,
                   name: str,
                   short_name: str = "",
                   color: str = "#1565c0",
                   notes: str = "",
                   is_active: int = 1):
    conn.execute(
        """UPDATE companies
           SET name=?, short_name=?, color=?, notes=?,
               is_active=?, updated_at=datetime('now')
           WHERE id=?""",
        (name, short_name or "", color or "#1565c0",
         notes or "", is_active, company_id)
    )


def delete_company(conn, company_id: int) -> bool:
    """
    يحذف الشركة من companies.db.
    ملفات DB الخاصة بها تبقى على الديسك (للأمان).
    """
    conn.execute("DELETE FROM companies WHERE id=?", (company_id,))
    return True


def toggle_company_active(conn, company_id: int):
    conn.execute(
        "UPDATE companies SET is_active = 1 - is_active WHERE id=?",
        (company_id,)
    )


# ══════════════════════════════════════════════════════════
# تهيئة قواعد بيانات الشركة الجديدة
# ══════════════════════════════════════════════════════════

def _init_company_databases(company_id: int):
    """
    ينشئ ويهيئ erp.db + accounting.db + inventory.db + orders.db + designs.db
    داخل مجلد الشركة.
    ملاحظة: هذه connections مؤقتة للتهيئة فقط — تُغلق بعد الانتهاء.
    """
    import sqlite3

    def _open(db_name: str) -> sqlite3.Connection:
        path = get_company_db_path(company_id, db_name)
        c = sqlite3.connect(path)
        c.row_factory     = sqlite3.Row
        c.isolation_level = None
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("PRAGMA journal_mode = WAL")
        return c

    erp = _open("erp")
    try:
        from db.costing.schema import _init_erp_db
        _init_erp_db(erp)
    finally:
        erp.close()

    acc = _open("accounting")
    try:
        from db.accounting.accounting_schema import create_accounting_tables
        create_accounting_tables(acc)
    finally:
        acc.close()

    inv = _open("inventory")
    try:
        from db.inventory.inventory_schema import create_inventory_tables
        create_inventory_tables(inv)
    finally:
        inv.close()

    ord_ = _open("orders")
    try:
        from db.orders.orders_schema import create_orders_tables
        create_orders_tables(ord_)
    finally:
        ord_.close()

    des = _open("designs")
    try:
        from db.designs.design_schema import create_designs_tables
        create_designs_tables(des)
    finally:
        des.close()


# ══════════════════════════════════════════════════════════
# CRUD — العناصر المشتركة
# ══════════════════════════════════════════════════════════

def fetch_all_shared_items(conn, shared_type: str = None) -> list:
    sql = """
        SELECT s.id, s.name, s.shared_type,
               s.source_company_id, s.source_item_id,
               s.notes, s.created_at,
               c.name AS source_company_name
        FROM   shared_items s
        JOIN   companies c ON c.id = s.source_company_id
    """
    if shared_type:
        sql += " WHERE s.shared_type = ?"
        return conn.execute(sql, (shared_type,)).fetchall()
    return conn.execute(sql).fetchall()


def fetch_shared_items_for_company(conn, company_id: int) -> list:
    """كل العناصر المشتركة التي تستخدمها شركة معينة."""
    return conn.execute("""
        SELECT s.id, s.name, s.shared_type,
               s.source_company_id, s.source_item_id,
               s.notes,
               c.name  AS source_company_name,
               lnk.id  AS link_id,
               lnk.local_item_id,
               lnk.is_synced,
               lnk.linked_at
        FROM   company_shared_links lnk
        JOIN   shared_items s ON s.id = lnk.shared_item_id
        JOIN   companies    c ON c.id = s.source_company_id
        WHERE  lnk.company_id = ?
        ORDER  BY s.shared_type, s.name
    """, (company_id,)).fetchall()


def publish_item_as_shared(central_conn,
                            source_company_id: int,
                            source_item_id: int,
                            shared_type: str,
                            name: str,
                            notes: str = "") -> int:
    """
    ينشر عنصر من شركة معينة كعنصر مشترك.
    يربطه تلقائياً بالشركة المصدر.
    """
    existing = central_conn.execute(
        """SELECT id FROM shared_items
           WHERE source_company_id=? AND source_item_id=? AND shared_type=?""",
        (source_company_id, source_item_id, shared_type)
    ).fetchone()
    if existing:
        return existing["id"]

    cur = central_conn.execute(
        """INSERT INTO shared_items
           (name, shared_type, source_company_id, source_item_id, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (name, shared_type, source_company_id, source_item_id, notes or "")
    )
    shared_id = cur.lastrowid

    central_conn.execute(
        """INSERT OR IGNORE INTO company_shared_links
           (shared_item_id, company_id, local_item_id, is_synced)
           VALUES (?, ?, ?, 1)""",
        (shared_id, source_company_id, source_item_id)
    )
    return shared_id


def link_shared_item_to_company(central_conn,
                                 erp_conn,
                                 shared_item_id: int,
                                 target_company_id: int) -> int:
    """
    يربط عنصراً مشتركاً بشركة جديدة.
    erp_conn: connection لـ erp.db الخاص بالشركة المصدر (shared — لا تُغلقه)
    """
    shared = central_conn.execute(
        "SELECT * FROM shared_items WHERE id=?", (shared_item_id,)
    ).fetchone()
    if not shared:
        raise ValueError(f"العنصر المشترك {shared_item_id} غير موجود")

    existing = central_conn.execute(
        """SELECT id, local_item_id FROM company_shared_links
           WHERE shared_item_id=? AND company_id=?""",
        (shared_item_id, target_company_id)
    ).fetchone()
    if existing:
        return existing["local_item_id"]

    # فتح erp.db الخاص بالشركة الهدف (connection مؤقت)
    import sqlite3
    target_erp_path = get_company_db_path(target_company_id, "erp")
    target_erp = sqlite3.connect(target_erp_path)
    target_erp.row_factory     = sqlite3.Row
    target_erp.isolation_level = None
    target_erp.execute("PRAGMA foreign_keys = ON")

    try:
        local_item_id = _copy_item_to_company(
            erp_conn, target_erp,
            shared["shared_type"], shared["source_item_id"],
            shared["name"]
        )
    finally:
        target_erp.close()

    central_conn.execute(
        """INSERT OR REPLACE INTO company_shared_links
           (shared_item_id, company_id, local_item_id, is_synced)
           VALUES (?, ?, ?, 1)""",
        (shared_item_id, target_company_id, local_item_id)
    )
    return local_item_id


def unlink_shared_item(central_conn, shared_item_id: int, company_id: int):
    """إلغاء ربط عنصر مشترك من شركة (لا يحذف العنصر المحلي)."""
    central_conn.execute(
        "DELETE FROM company_shared_links WHERE shared_item_id=? AND company_id=?",
        (shared_item_id, company_id)
    )


def delete_shared_item(central_conn, shared_item_id: int):
    """حذف العنصر المشترك وكل روابطه (لا يحذف النسخ المحلية)."""
    central_conn.execute(
        "DELETE FROM shared_items WHERE id=?", (shared_item_id,)
    )


def sync_shared_item(central_conn,
                     source_erp_conn,
                     shared_item_id: int):
    """
    يحدّث بيانات العنصر المشترك في كل الشركات المرتبطة به.
    source_erp_conn: shared connection — لا تُغلقه
    """
    shared = central_conn.execute(
        "SELECT * FROM shared_items WHERE id=?", (shared_item_id,)
    ).fetchone()
    if not shared:
        return

    links = central_conn.execute(
        """SELECT company_id, local_item_id FROM company_shared_links
           WHERE shared_item_id=? AND company_id != ?""",
        (shared_item_id, shared["source_company_id"])
    ).fetchall()

    import sqlite3
    for lnk in links:
        if not lnk["local_item_id"]:
            continue
        target_path = get_company_db_path(lnk["company_id"], "erp")
        if not os.path.exists(target_path):
            continue
        # هذا connection مؤقت — يُغلق بعد الانتهاء
        target_erp = sqlite3.connect(target_path)
        target_erp.row_factory     = sqlite3.Row
        target_erp.isolation_level = None
        try:
            _sync_item(
                source_erp_conn, target_erp,
                shared["shared_type"],
                shared["source_item_id"],
                lnk["local_item_id"]
            )
            central_conn.execute(
                "UPDATE company_shared_links SET is_synced=1 WHERE shared_item_id=? AND company_id=?",
                (shared_item_id, lnk["company_id"])
            )
        finally:
            target_erp.close()


# ══════════════════════════════════════════════════════════
# مساعدات نسخ العناصر بين DBs
# ══════════════════════════════════════════════════════════

def _copy_item_to_company(source_erp, target_erp,
                           shared_type: str,
                           source_item_id: int,
                           name: str) -> int:
    """ينسخ عنصراً من source_erp إلى target_erp، يرجع الـ id الجديد."""

    if shared_type == "raw":
        row = source_erp.execute(
            "SELECT * FROM items WHERE id=? AND type='raw'", (source_item_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"الخامة {source_item_id} غير موجودة")
        cur = target_erp.execute(
            "INSERT INTO items (name, type, price, total_qty) VALUES (?, 'raw', ?, ?)",
            (row["name"], row["price"], row["total_qty"])
        )
        return cur.lastrowid

    elif shared_type == "machine":
        row = source_erp.execute(
            "SELECT * FROM machines WHERE id=?", (source_item_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"الماكينة {source_item_id} غير موجودة")
        cur = target_erp.execute(
            "INSERT INTO machines (name, rate_per_hour, rate_per_unit) VALUES (?, ?, ?)",
            (row["name"], row["rate_per_hour"], row["rate_per_unit"])
        )
        return cur.lastrowid

    elif shared_type == "labor_op":
        row = source_erp.execute(
            "SELECT * FROM labor_ops WHERE id=?", (source_item_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"عملية العمالة {source_item_id} غير موجودة")
        cur = target_erp.execute(
            "INSERT INTO labor_ops (name, minutes) VALUES (?, ?)",
            (row["name"], row["minutes"])
        )
        return cur.lastrowid

    elif shared_type == "machine_op":
        row = source_erp.execute("""
            SELECT mo.*, m.name AS machine_name,
                   m.rate_per_hour, m.rate_per_unit
            FROM machine_ops mo
            JOIN machines m ON m.id = mo.machine_id
            WHERE mo.id=?
        """, (source_item_id,)).fetchone()
        if not row:
            raise ValueError(f"عملية التشغيل {source_item_id} غير موجودة")
        existing_machine = target_erp.execute(
            "SELECT id FROM machines WHERE name=?", (row["machine_name"],)
        ).fetchone()
        if existing_machine:
            machine_id = existing_machine["id"]
        else:
            mc = target_erp.execute(
                "INSERT INTO machines (name, rate_per_hour, rate_per_unit) VALUES (?, ?, ?)",
                (row["machine_name"], row["rate_per_hour"], row["rate_per_unit"])
            )
            machine_id = mc.lastrowid

        cur = target_erp.execute(
            "INSERT INTO machine_ops (machine_id, name, mode, value) VALUES (?, ?, ?, ?)",
            (machine_id, row["name"], row["mode"], row["value"])
        )
        return cur.lastrowid

    raise ValueError(f"نوع غير معروف: {shared_type}")


def _sync_item(source_erp, target_erp,
               shared_type: str,
               source_item_id: int,
               local_item_id: int):
    """يحدّث بيانات نسخة محلية من عنصر مشترك."""

    if shared_type == "raw":
        row = source_erp.execute(
            "SELECT name, price, total_qty FROM items WHERE id=?",
            (source_item_id,)
        ).fetchone()
        if row:
            target_erp.execute(
                "UPDATE items SET name=?, price=?, total_qty=? WHERE id=?",
                (row["name"], row["price"], row["total_qty"], local_item_id)
            )

    elif shared_type == "machine":
        row = source_erp.execute(
            "SELECT name, rate_per_hour, rate_per_unit FROM machines WHERE id=?",
            (source_item_id,)
        ).fetchone()
        if row:
            target_erp.execute(
                "UPDATE machines SET name=?, rate_per_hour=?, rate_per_unit=? WHERE id=?",
                (row["name"], row["rate_per_hour"], row["rate_per_unit"], local_item_id)
            )

    elif shared_type == "labor_op":
        row = source_erp.execute(
            "SELECT name, minutes FROM labor_ops WHERE id=?",
            (source_item_id,)
        ).fetchone()
        if row:
            target_erp.execute(
                "UPDATE labor_ops SET name=?, minutes=? WHERE id=?",
                (row["name"], row["minutes"], local_item_id)
            )

    elif shared_type == "machine_op":
        row = source_erp.execute(
            "SELECT name, mode, value FROM machine_ops WHERE id=?",
            (source_item_id,)
        ).fetchone()
        if row:
            target_erp.execute(
                "UPDATE machine_ops SET name=?, mode=?, value=? WHERE id=?",
                (row["name"], row["mode"], row["value"], local_item_id)
            )