"""
db/connection.py
================
إدارة اتصالات قاعدة البيانات.

الملفات:
  erp.db          — التكاليف والتسعير (الأصلي)
  accounting.db   — الحسابات والقيود المحاسبية
  inventory.db    — المخزن وحركاته

كل ملف له connection منفصل، لكن ممكن نربطهم بـ ATTACH لو احتجنا JOIN.
"""

import sqlite3
import os

# مسارات الملفات
_BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

DB_PATHS = {
    "costing":    os.path.join(_BASE_DIR, "erp.db"),
    "accounting": os.path.join(_BASE_DIR, "accounting.db"),
    "inventory":  os.path.join(_BASE_DIR, "inventory.db"),
}

# للتوافق مع الكود القديم
DB_PATH = DB_PATHS["costing"]


def _make_conn(path: str) -> sqlite3.Connection:
    """إنشاء connection موحد الإعدادات."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # أداء أفضل مع WAL
    conn.isolation_level = None                  # autocommit
    return conn


def get_connection(db: str = "costing") -> sqlite3.Connection:
    """
    يرجع connection لقاعدة البيانات المطلوبة.

    db: "costing" | "accounting" | "inventory"
    """
    path = DB_PATHS.get(db, DB_PATHS["costing"])
    return _make_conn(path)


def get_costing_connection() -> sqlite3.Connection:
    """اختصار لقاعدة بيانات التكاليف."""
    return _make_conn(DB_PATHS["costing"])


def get_accounting_connection() -> sqlite3.Connection:
    """اختصار لقاعدة بيانات الحسابات."""
    return _make_conn(DB_PATHS["accounting"])


def get_inventory_connection() -> sqlite3.Connection:
    """اختصار لقاعدة بيانات المخزن."""
    return _make_conn(DB_PATHS["inventory"])


def get_linked_connection(primary: str = "inventory",
                          attach: list[str] = None) -> sqlite3.Connection:
    """
    يرجع connection مع ATTACH لقواعد بيانات إضافية.
    يُستخدم لـ JOIN بين قواعد البيانات المختلفة.

    مثال:
        conn = get_linked_connection("inventory", ["accounting"])
        # الآن ممكن تكتب:
        # SELECT * FROM accounting.accounts ...
        # SELECT * FROM main.inventory_items ...

    primary: قاعدة البيانات الرئيسية (main)
    attach:  قواعد البيانات الإضافية المربوطة
    """
    conn = _make_conn(DB_PATHS[primary])
    if attach:
        for db_name in attach:
            path = DB_PATHS.get(db_name)
            if path:
                conn.execute(f"ATTACH DATABASE '{path}' AS {db_name}")
    return conn