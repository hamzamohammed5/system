"""
db/shared/connection.py  (نسخة multi-company)
================================================
إدارة اتصالات قاعدة البيانات مع دعم الشركات المتعددة.

الوضع الجديد:
  - كل شركة لها مجلد خاص بملفات DB الخاصة بها
  - company_state يحفظ الشركة النشطة حالياً
  - الدوال القديمة (get_connection / get_costing_connection ...) 
    مازالت تعمل لكن ترجع connections الشركة النشطة

للتوافق مع الكود القديم:
  from db.shared.connection import get_connection
  conn = get_connection()          # erp.db للشركة النشطة
  conn = get_connection("erp")     # نفس الشيء
  conn = get_connection("accounting")

للاستخدام الجديد:
  from db.companies.company_state import company_state
  erp_conn = company_state.get_erp_conn()

إصلاح 10:
  get_connection("costing") يُصدر DeprecationWarning ليساعد المطورين
  على تحديث الكود بدل الاعتماد على الـ hidden alias.
"""

import sqlite3
import os
import warnings

# ── مسارات قاعدة بيانات الشركات المركزية ─────────────────
_BASE_DIR   = os.path.join(os.path.dirname(__file__), "..", "..")
CENTRAL_DB  = os.path.join(_BASE_DIR, "companies.db")


def _make_conn(path: str) -> sqlite3.Connection:
    """إنشاء connection موحد الإعدادات."""
    conn = sqlite3.connect(path)
    conn.row_factory   = sqlite3.Row
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_central_connection() -> sqlite3.Connection:
    """Connection لقاعدة بيانات الشركات المركزية."""
    return _make_conn(CENTRAL_DB)


def get_connection(db: str = "erp") -> sqlite3.Connection:
    """
    يرجع connection للشركة النشطة.
    db: "erp" | "accounting" | "inventory" | "orders" | "designs"

    للتوافق مع الكود القديم:
      get_connection()           → erp.db
      get_connection("costing")  → erp.db  (مُهمَل — استخدم "erp")

    [إصلاح 10] get_connection("costing") يُصدر DeprecationWarning:
    الاسم القديم "costing" كان alias مخفي لـ "erp" مما يُسبب
    ارتباكاً عند الـ debugging. الـ warning يساعد المطورين على
    تحديث الكود تدريجياً.
    """
    # [إصلاح 10] DeprecationWarning للاسم القديم
    if db == "costing":
        warnings.warn(
            "get_connection('costing') مُهمَل — "
            "استخدم get_connection('erp') أو company_state.get_erp_conn() مباشرة.",
            DeprecationWarning,
            stacklevel=2,
        )
        db = "erp"

    # mapping للتوافق مع أي أسماء أخرى غير متوقعة
    _alias = {
        "erp":        "erp",
        "accounting": "accounting",
        "inventory":  "inventory",
        "orders":     "orders",
        "designs":    "designs",
    }
    db_name = _alias.get(db, "erp")

    from db.companies.company_state import company_state
    if not company_state.is_ready:
        raise RuntimeError(
            "لم يتم تحديد شركة نشطة.\n"
            "اختر شركة من القائمة أولاً."
        )

    return company_state._get_conn(db_name)


# ── دوال اختصار للتوافق مع الكود القديم ─────────────────

def get_costing_connection() -> sqlite3.Connection:
    """
    اختصار → erp.db للشركة النشطة.

    .. deprecated::
        استخدم company_state.get_erp_conn() أو get_connection("erp") مباشرة.
    """
    warnings.warn(
        "get_costing_connection() مُهمَل — "
        "استخدم company_state.get_erp_conn() مباشرة.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_connection("erp")


def get_accounting_connection() -> sqlite3.Connection:
    """اختصار → accounting.db للشركة النشطة."""
    return get_connection("accounting")


def get_inventory_connection() -> sqlite3.Connection:
    """اختصار → inventory.db للشركة النشطة."""
    return get_connection("inventory")


def get_linked_connection(primary: str = "inventory",
                          attach: list[str] = None) -> sqlite3.Connection:
    """
    يرجع connection مع ATTACH لقواعد بيانات إضافية.
    يُستخدم لـ JOIN بين قواعد البيانات المختلفة.
    """
    from db.companies.company_state import company_state
    from db.companies.companies_schema import get_company_db_path

    if not company_state.is_ready:
        raise RuntimeError("لم يتم تحديد شركة نشطة.")

    # normalize اسم الـ DB
    primary_name = "erp" if primary in ("costing", "erp") else primary
    path = get_company_db_path(company_state.company_id, primary_name)
    conn = _make_conn(path)

    if attach:
        for db_name in attach:
            real_name = "erp" if db_name in ("costing", "erp") else db_name
            att_path  = get_company_db_path(company_state.company_id, real_name)
            if os.path.exists(att_path):
                conn.execute(f"ATTACH DATABASE '{att_path}' AS {db_name}")

    return conn