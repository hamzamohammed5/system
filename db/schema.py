"""
db/schema.py
============
إنشاء الجداول والقيم الافتراضية.
يُستدعى مرة واحدة عند التشغيل من main.py.
"""

from db.connection  import get_connection, get_accounting_connection, get_inventory_connection
from db.migrations  import run_migrations


def init_db():
    # ── 1. قاعدة التكاليف (erp.db) ──
    conn = get_connection()
    cur  = conn.cursor()

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
    conn.commit()
    run_migrations(conn)
    conn.close()

    # ── 2. قاعدة الحسابات (accounting.db) ──
    acc_conn = get_accounting_connection()
    from db.accounting_schema import create_accounting_tables
    create_accounting_tables(acc_conn)
    acc_conn.close()

    # ── 3. قاعدة المخزن (inventory.db) ──
    inv_conn = get_inventory_connection()
    from db.inventory_schema import create_inventory_tables
    create_inventory_tables(inv_conn)
    inv_conn.close()