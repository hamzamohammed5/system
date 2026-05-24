"""
ui/tabs/accounting/_conn_guard.py
==================================
ConnGuard — منطق التحقق من صلاحية الـ connections للشركة النشطة.

مُستخرج من accounting_section.py لتقليل حجمه وتسهيل الاختبار.
يُستدعى فقط من AccountingTab._build().

دوال:
  is_ready()                         → هل شركة محددة؟
  get_current_company_id()           → company_id النشط
  get_acc_conn()                     → accounting connection
  get_erp_conn()                     → erp connection
  verify_conn_belongs_to_company()   → هل الـ conn للشركة الصح؟
  get_current_acc_db_path()          → مسار DB الشركة النشطة
"""

import os


def is_ready() -> bool:
    """هل تم اختيار شركة وجاهزة للاستخدام؟"""
    from db.companies.company_state import company_state
    return company_state.is_ready


def get_current_company_id():
    """يرجع company_id النشط أو None."""
    from db.companies.company_state import company_state
    return company_state.company_id if company_state.is_ready else None


def get_acc_conn():
    """يجيب accounting connection للشركة النشطة."""
    from db.shared.connection import get_accounting_connection
    return get_accounting_connection()


def get_erp_conn():
    """يجيب erp connection للشركة النشطة."""
    from db.shared.connection import get_connection
    return get_connection()


def get_current_acc_db_path():
    """يرجع مسار DB المحاسبة للشركة النشطة أو None."""
    cid = get_current_company_id()
    if cid is None:
        return None
    try:
        from db.companies.companies_schema import get_company_db_path
        return get_company_db_path(cid, "accounting")
    except Exception:
        return None


def verify_conn_belongs_to_company(conn, expected_company_id: int) -> bool:
    """
    يتحقق إن الـ conn هو فعلاً لقاعدة بيانات الشركة المحددة.

    يستخدم PRAGMA database_list لمقارنة المسارات.
    يرجع False لو conn=None أو company_id=None أو المسارات مختلفة.
    """
    if conn is None or expected_company_id is None:
        return False
    try:
        conn.execute("SELECT 1").fetchone()
        row = conn.execute("PRAGMA database_list").fetchone()
        if not row:
            return False

        actual_path   = row[2] if len(row) > 2 else ""
        expected_path = _get_expected_path(expected_company_id)
        if not expected_path:
            return False

        actual_norm   = os.path.normcase(os.path.realpath(actual_path))
        expected_norm = os.path.normcase(os.path.realpath(expected_path))
        return actual_norm == expected_norm

    except Exception:
        return False


def _get_expected_path(company_id: int) -> str | None:
    """Helper داخلي لجلب المسار المتوقع."""
    try:
        from db.companies.companies_schema import get_company_db_path
        return get_company_db_path(company_id, "accounting")
    except Exception:
        return None


def init_schemas(acc_conn, erp_conn, initialized_cache: dict) -> bool:
    """
    يهيئ schemas قاعدة البيانات لو لم تهيأ بعد.

    initialized_cache: dict {company_id: db_path} — يُمرر من AccountingTab
    يرجع True لو تمت التهيئة أو كانت موجودة، False لو فشل.
    """
    if not is_ready():
        return False

    cid          = get_current_company_id()
    current_path = get_current_acc_db_path()
    cached_path  = initialized_cache.get(cid)

    if cached_path and cached_path == current_path:
        return True

    try:
        from db.accounting.accounting_schema import create_accounting_tables
        create_accounting_tables(acc_conn)
    except Exception as e:
        print(f"[ConnGuard] accounting schema error: {e}")

    try:
        from db.inventory.investors_repo import create_investors_tables
        create_investors_tables(erp_conn)
    except Exception as e:
        print(f"[ConnGuard] investors schema error: {e}")

    if current_path:
        initialized_cache[cid] = current_path

    return True