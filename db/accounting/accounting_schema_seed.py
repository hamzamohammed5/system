"""
db/accounting/accounting_schema_seed.py
======================================
البيانات الافتراضية للحسابات.

إصلاح (v2):
  - _verify_conn_is_accounting: تتحقق إن الـ conn فعلاً لـ accounting.db
    قبل ما تعمل seed — يمنع إدراج بيانات في DB غلط.
"""

import os


def _account_exists(conn) -> bool:
    try:
        row = conn.execute("SELECT COUNT(*) as c FROM accounts").fetchone()
        return row["c"] > 0
    except Exception:
        return False


def _verify_conn_is_accounting(conn) -> bool:
    """
    يتحقق إن الـ conn مفتوح على ملف اسمه accounting.db.
    يمنع الـ seed من الاشتغال على erp.db أو أي DB تاني بالغلط.
    """
    try:
        row = conn.execute("PRAGMA database_list").fetchone()
        if not row:
            return False
        path = row[2] if len(row) > 2 else ""
        return os.path.basename(path).lower() == "accounting.db"
    except Exception:
        # لو مش قادر يتحقق، نسمح بالمتابعة (backward compat)
        return True


def seed_default_accounts(conn):
    """يُدرج الحسابات الافتراضية لو كانت قاعدة البيانات فارغة."""

    # [إصلاح] تحقق إن الـ conn للـ DB الصح
    if not _verify_conn_is_accounting(conn):
        print("[accounting_schema_seed] تحذير: conn ليس لـ accounting.db — تم تخطي الـ seed")
        return

    if _account_exists(conn):
        return

    accounts = [
        ("1",    "الأصول",                "asset",     None,             None),
        ("11",   "الأصول المتداولة",       "asset",     "current_asset",  "1"),
        ("111",  "الصندوق",               "asset",     "cash",           "11"),
        ("112",  "البنك",                 "asset",     "bank",           "11"),
        ("113",  "العملاء / ذمم مدينة",   "asset",     "receivable",     "11"),
        ("114",  "المخزون",               "asset",     "inventory",      "11"),
        ("115",  "مصروفات مقدمة",         "asset",     "prepaid",        "11"),
        ("12",   "الأصول الثابتة",         "asset",     "fixed_asset",    "1"),
        ("121",  "المعدات والآلات",        "asset",     "equipment",      "12"),
        ("122",  "مجمع الاستهلاك",        "asset",     "depreciation",   "12"),

        ("2",    "الخصوم",                "liability", None,             None),
        ("21",   "الخصوم المتداولة",       "liability", "current",        "2"),
        ("211",  "الموردون / ذمم دائنة",  "liability", "payable",        "21"),
        ("212",  "مصروفات مستحقة",        "liability", "accrued",        "21"),
        ("22",   "الخصوم طويلة الأجل",    "liability", "long_term",      "2"),
        ("221",  "قروض طويلة الأجل",      "liability", "loan",           "22"),

        ("3",    "حقوق الملكية",           "capital",   None,             None),
        ("31",   "رأس المال",              "capital",   "capital",        "3"),
        ("32",   "الأرباح المحتجزة",       "capital",   "retained",       "3"),
        ("33",   "السحوبات",              "drawings",  "drawings",       "3"),

        ("4",    "الإيرادات",              "revenue",   None,             None),
        ("41",   "إيرادات المبيعات",       "revenue",   "sales",          "4"),
        ("42",   "إيرادات أخرى",          "revenue",   "other",          "4"),

        ("5",    "المصروفات",              "expense",   None,             None),
        ("51",   "تكلفة البضاعة المباعة",  "expense",   "cogs",           "5"),
        ("52",   "مصروفات تشغيلية",       "expense",   "operating",      "5"),
        ("521",  "رواتب وأجور",           "expense",   "salaries",       "52"),
        ("522",  "إيجار",                 "expense",   "rent",           "52"),
        ("523",  "مرافق (كهرباء/مياه)",   "expense",   "utilities",      "52"),
        ("524",  "مصروفات نثرية",         "expense",   "misc",           "52"),
        ("53",   "مصروفات تمويلية",       "expense",   "financial",      "5"),
        ("531",  "فوائد بنكية",           "expense",   "interest",       "53"),
    ]

    for code, name, acc_type, subtype, parent_code in accounts:
        parent_id = None
        if parent_code:
            row = conn.execute(
                "SELECT id FROM accounts WHERE code=?", (parent_code,)
            ).fetchone()
            if row:
                parent_id = row["id"]

        conn.execute("""
            INSERT OR IGNORE INTO accounts
                (code, name, type, subtype, parent_id, is_leaf)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (code, name, acc_type, subtype, parent_id))

    conn.commit()