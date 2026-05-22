"""
db/companies/companies_schema.py
=================================
قاعدة بيانات مركزية للشركات (companies.db).

الجداول:
  companies           — بيانات الشركات
  shared_items        — العناصر المشتركة بين الشركات (خامات / عمليات / إلخ)
  company_shared_links — ربط الشركة بالعناصر المشتركة

كل شركة لها مجلد خاص:
  company_data/
    {company_id}/
      erp.db
      accounting.db
      inventory.db
      orders.db
      designs.db
"""

import os
import sqlite3

_BASE_DIR   = os.path.join(os.path.dirname(__file__), "..", "..", "..")
CENTRAL_DB  = os.path.join(_BASE_DIR, "companies.db")
DATA_DIR    = os.path.join(_BASE_DIR, "company_data")


# ══════════════════════════════════════════════════════════
# Connection
# ══════════════════════════════════════════════════════════

def get_central_connection() -> sqlite3.Connection:
    """Connection لقاعدة بيانات الشركات المركزية."""
    conn = sqlite3.connect(CENTRAL_DB)
    conn.row_factory   = sqlite3.Row
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ══════════════════════════════════════════════════════════
# مسارات ملفات الشركة
# ══════════════════════════════════════════════════════════

def get_company_dir(company_id: int) -> str:
    """المجلد الخاص بشركة معينة."""
    return os.path.join(DATA_DIR, str(company_id))


def get_company_db_path(company_id: int, db_name: str) -> str:
    """
    مسار ملف DB لشركة معينة.
    db_name: "erp" | "accounting" | "inventory" | "orders" | "designs"
    """
    return os.path.join(get_company_dir(company_id), f"{db_name}.db")


def ensure_company_dir(company_id: int):
    """إنشاء مجلد الشركة لو مش موجود."""
    path = get_company_dir(company_id)
    os.makedirs(path, exist_ok=True)
    return path


# ══════════════════════════════════════════════════════════
# Schema الجداول المركزية
# ══════════════════════════════════════════════════════════

def create_central_tables(conn):
    """إنشاء جداول companies.db."""
    conn.executescript("""
        -- ══ الشركات ══════════════════════════════════════
        CREATE TABLE IF NOT EXISTS companies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            short_name  TEXT,
            logo_path   TEXT,
            color       TEXT    NOT NULL DEFAULT '#1565c0',
            is_active   INTEGER NOT NULL DEFAULT 1,
            notes       TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ══ العناصر المشتركة ══════════════════════════════
        -- source_company_id: الشركة صاحبة العنصر الأصلي
        -- shared_type: نوع العنصر (raw / labor_op / machine_op / machine)
        -- source_item_id: id العنصر في erp.db الخاص بالشركة المصدر
        CREATE TABLE IF NOT EXISTS shared_items (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT    NOT NULL,
            shared_type      TEXT    NOT NULL
                CHECK(shared_type IN ('raw','labor_op','machine_op','machine')),
            source_company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            source_item_id   INTEGER NOT NULL,
            notes            TEXT,
            created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ══ ربط الشركات بالعناصر المشتركة ════════════════
        -- company_id: الشركة التي تستخدم العنصر المشترك
        -- local_item_id: id العنصر في erp.db الخاص بهذه الشركة (بعد النسخ)
        CREATE TABLE IF NOT EXISTS company_shared_links (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            shared_item_id INTEGER NOT NULL REFERENCES shared_items(id) ON DELETE CASCADE,
            company_id     INTEGER NOT NULL REFERENCES companies(id)    ON DELETE CASCADE,
            local_item_id  INTEGER,   -- id الـ mirror في erp.db الخاص بالشركة
            is_synced      INTEGER NOT NULL DEFAULT 0,
            linked_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(shared_item_id, company_id)
        );
    """)
    conn.commit()
    _migrate_central(conn)


def _migrate_central(conn):
    """Migrations مستقبلية على companies.db."""
    pass