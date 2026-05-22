"""
db/costing/schema.py  (نسخة multi-company)
============================================
إنشاء الجداول والقيم الافتراضية لـ erp.db الخاص بشركة.

التغيير: أضفنا _init_erp_db(conn) التي تقبل connection جاهز
بدلاً من إنشاء connection داخلياً — عشان تدعم multi-company.
"""

from db.shared.migrations   import run_migrations
from db.shared.migrations_v2 import run_migrations_v2
from db.shared.migrations_v3 import run_migrations_v3


# ══════════════════════════════════════════════════════════
# الدالة الأساسية — تقبل connection جاهز
# ══════════════════════════════════════════════════════════

def _init_erp_db(conn):
    """
    يُهيئ erp.db من connection جاهز.
    يُستدعى من companies_repo عند إنشاء شركة جديدة.
    """
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            type        TEXT    NOT NULL CHECK(type IN ('raw','semi','final')),
            price       REAL    NOT NULL DEFAULT 0,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS machines (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            rate_per_hour REAL    NOT NULL DEFAULT 0,
            rate_per_unit REAL    NOT NULL DEFAULT 0,
            category_id   INTEGER REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS labor_ops (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            minutes     REAL    NOT NULL DEFAULT 0,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS machine_ops (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id  INTEGER NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            mode        TEXT    NOT NULL CHECK(mode IN ('time','unit')),
            value       REAL    NOT NULL DEFAULT 0,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS bom (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id  INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            child_type TEXT    NOT NULL
                CHECK(child_type IN ('raw','semi','labor_op','machine_op')),
            child_id   INTEGER NOT NULL,
            qty        REAL    NOT NULL DEFAULT 1,
            child_name TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value REAL NOT NULL DEFAULT 0
        );
    """)

    cur.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        [
            ("monthly_salary",    3000.0),
            ("working_days",        25.0),
            ("holiday_days",         4.0),
            ("working_hours_day",    8.0),
            ("overhead_factor",      1.10),
            ("font_size",           11.0),
        ]
    )

    run_migrations(conn)
    run_migrations_v2(conn)
    run_migrations_v3(conn)


# ══════════════════════════════════════════════════════════
# نقطة الدخول القديمة (للتوافق) — لا تُستخدم في multi-company
# ══════════════════════════════════════════════════════════

def init_db():
    """
    ⚠️ هذه الدالة موجودة للتوافق فقط.
    في وضع multi-company يتم إنشاء الـ DBs عبر companies_repo.
    تُهيئ فقط قاعدة بيانات الشركات المركزية (companies.db).
    """
    # تهيئة companies.db
    from db.companies.companies_schema import (
        get_central_connection, create_central_tables
    )
    central = get_central_connection()
    create_central_tables(central)
    central.close()