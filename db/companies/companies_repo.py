"""
db/companies/companies_repo.py
================================
عمليات CRUD للشركات والعناصر المشتركة.

إصلاح (v2):
  - حذف الدوال القديمة التي تعمل JOIN على source_company_id (عمود محذوف)
  - fetch_all_shared_items و fetch_shared_items_for_company تُحوَّل لـ shared_items_repo
  - كل central connections تُفتح وتُغلق بشكل صحيح في try/finally

[تحسين 47]:
  - الدوال الـ legacy اللي تُفوَّض لـ shared_items_repo تعطي DeprecationWarning
    ليسهل إزالتها تدريجياً وتوجيه الـ imports للمصدر الصح.
"""

import os
import warnings
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
# العناصر المشتركة — Legacy (مع DeprecationWarning)
# ══════════════════════════════════════════════════════════
# [تحسين 47] هذه الدوال موجودة للتوافق مع الكود القديم فقط.
# استخدم db.companies.shared_items_repo مباشرة في الكود الجديد.
# ستُزال هذه الدوال في إصدار مستقبلي.

def fetch_all_shared_items(conn, shared_type: str = None) -> list:
    """
    .. deprecated::
        استخدم ``db.companies.shared_items_repo.fetch_all_shared_items`` مباشرة.
    """
    warnings.warn(
        "fetch_all_shared_items في companies_repo مُهمَلة — "
        "استورد من db.companies.shared_items_repo مباشرة.",
        DeprecationWarning,
        stacklevel=2,
    )
    from db.companies.shared_items_repo import fetch_all_shared_items as _fetch
    return _fetch(conn, shared_type)


def fetch_shared_items_for_company(conn, company_id: int) -> list:
    """
    .. deprecated::
        استخدم ``db.companies.shared_items_repo.fetch_shared_items_for_company`` مباشرة.
    """
    warnings.warn(
        "fetch_shared_items_for_company في companies_repo مُهمَلة — "
        "استورد من db.companies.shared_items_repo مباشرة.",
        DeprecationWarning,
        stacklevel=2,
    )
    from db.companies.shared_items_repo import fetch_shared_items_for_company as _fetch
    return _fetch(conn, company_id)


def publish_item_as_shared(central_conn,
                            source_company_id: int,
                            source_item_id: int,
                            shared_type: str,
                            name: str,
                            notes: str = "") -> int:
    """
    ينشر عنصر كمشترك — النموذج الجديد يخزن البيانات في data JSON.
    يربطه تلقائياً بالشركة المصدر.
    """
    from db.companies.shared_items_repo import (
        fetch_all_shared_items, insert_shared_item, link_company, _default_data
    )

    # تحقق من وجود عنصر بنفس الاسم والنوع
    existing_list = fetch_all_shared_items(central_conn, shared_type)
    for ex in existing_list:
        if ex["name"].strip().lower() == name.strip().lower():
            # ربط الشركة بالعنصر الموجود
            link_company(central_conn, ex["id"], source_company_id)
            return ex["id"]

    data = _default_data(shared_type)
    data["source_company_id"] = source_company_id

    shared_id = insert_shared_item(central_conn, name, shared_type, data)
    link_company(central_conn, shared_id, source_company_id)
    return shared_id


def link_shared_item_to_company(central_conn,
                                 erp_conn,
                                 shared_item_id: int,
                                 target_company_id: int) -> int:
    """
    يربط عنصراً مشتركاً بشركة — النموذج الجديد بدون نسخ محلية.
    يرجع shared_item_id مباشرة.
    """
    from db.companies.shared_items_repo import link_company, is_company_linked

    if not is_company_linked(central_conn, shared_item_id, target_company_id):
        link_company(central_conn, shared_item_id, target_company_id)

    return shared_item_id


def unlink_shared_item(central_conn, shared_item_id: int, company_id: int):
    """إلغاء ربط عنصر مشترك من شركة."""
    from db.companies.shared_items_repo import unlink_company
    unlink_company(central_conn, shared_item_id, company_id)


def delete_shared_item(central_conn, shared_item_id: int):
    """حذف العنصر المشترك وكل روابطه."""
    from db.companies.shared_items_repo import delete_shared_item as _delete
    _delete(central_conn, shared_item_id)


def sync_shared_item(central_conn,
                     source_erp_conn,
                     shared_item_id: int):
    """
    في النموذج الجديد لا توجد نسخ محلية — البيانات تُقرأ مباشرة من companies.db.
    هذه الدالة أصبحت no-op للتوافق مع الكود القديم.
    """
    pass