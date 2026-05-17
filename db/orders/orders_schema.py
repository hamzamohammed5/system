"""
db/orders/orders_schema.py
===========================
Schema قاعدة بيانات العملاء والطلبات (orders.db).

الجداول:
  customers          — بيانات العملاء
  customer_contacts  — جهات الاتصال المتعددة لكل عميل
  orders             — الطلبات (جديد / إعادة طلب)
  order_items        — بنود كل طلب
  order_status_log   — سجل تغييرات حالة الطلب
"""

import os
import sqlite3

_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
ORDERS_DB_PATH = os.path.join(_BASE_DIR, "orders.db")


def get_orders_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(ORDERS_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.isolation_level = None  # autocommit
    return conn


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def create_orders_tables(conn):
    """إنشاء كل جداول orders.db."""

    conn.executescript("""
        -- ══ العملاء ══════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS customers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            code            TEXT    UNIQUE,          -- كود العميل التلقائي CUS-0001
            name            TEXT    NOT NULL,
            customer_type   TEXT    NOT NULL DEFAULT 'individual'
                            CHECK(customer_type IN ('individual','company')),
            phone           TEXT,
            phone2          TEXT,
            email           TEXT,
            address         TEXT,
            city            TEXT,
            notes           TEXT,
            is_active       INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ══ جهات اتصال إضافية للعميل ════════════════════════
        CREATE TABLE IF NOT EXISTS customer_contacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL
                        REFERENCES customers(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            role        TEXT,               -- مثال: مدير، محاسب
            phone       TEXT,
            email       TEXT,
            notes       TEXT
        );

        -- ══ الطلبات ══════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number    TEXT    UNIQUE NOT NULL,    -- ORD-2025-0001
            customer_id     INTEGER NOT NULL
                            REFERENCES customers(id) ON DELETE RESTRICT,
            order_type      TEXT    NOT NULL DEFAULT 'new'
                            CHECK(order_type IN ('new','reorder','custom')),
            status          TEXT    NOT NULL DEFAULT 'pending'
                            CHECK(status IN (
                                'pending',      -- قيد الانتظار
                                'confirmed',    -- مؤكد
                                'in_progress',  -- قيد التنفيذ
                                'ready',        -- جاهز
                                'delivered',    -- تم التسليم
                                'cancelled',    -- ملغي
                                'on_hold'       -- معلق
                            )),
            priority        TEXT    NOT NULL DEFAULT 'normal'
                            CHECK(priority IN ('low','normal','high','urgent')),
            order_date      TEXT    NOT NULL DEFAULT (date('now')),
            due_date        TEXT,                       -- تاريخ التسليم المطلوب
            delivery_date   TEXT,                       -- تاريخ التسليم الفعلي
            total_amount    REAL    NOT NULL DEFAULT 0,
            discount        REAL    NOT NULL DEFAULT 0,
            net_amount      REAL    NOT NULL DEFAULT 0,
            paid_amount     REAL    NOT NULL DEFAULT 0,
            notes           TEXT,
            internal_notes  TEXT,                       -- ملاحظات داخلية
            reference_order INTEGER                     -- للإعادة: رقم الطلب الأصلي
                            REFERENCES orders(id) ON DELETE SET NULL,
            created_by      TEXT    DEFAULT 'system',
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ══ بنود الطلب ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS order_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL
                            REFERENCES orders(id) ON DELETE CASCADE,
            item_name       TEXT    NOT NULL,
            description     TEXT,
            quantity        REAL    NOT NULL DEFAULT 1
                            CHECK(quantity > 0),
            unit            TEXT    NOT NULL DEFAULT 'قطعة',
            unit_price      REAL    NOT NULL DEFAULT 0,
            discount_pct    REAL    NOT NULL DEFAULT 0,
            total_price     REAL    NOT NULL DEFAULT 0,
            design_ref      TEXT,                       -- مرجع التصميم (اختياري)
            notes           TEXT,
            sort_order      INTEGER NOT NULL DEFAULT 0
        );

        -- ══ سجل تغييرات الحالة ═══════════════════════════════
        CREATE TABLE IF NOT EXISTS order_status_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL
                        REFERENCES orders(id) ON DELETE CASCADE,
            old_status  TEXT,
            new_status  TEXT    NOT NULL,
            notes       TEXT,
            changed_by  TEXT    DEFAULT 'system',
            changed_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ══ Indexes ═══════════════════════════════════════════
        CREATE INDEX IF NOT EXISTS idx_orders_customer
            ON orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status
            ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_date
            ON orders(order_date);
        CREATE INDEX IF NOT EXISTS idx_order_items_order
            ON order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_status_log_order
            ON order_status_log(order_id);
        CREATE INDEX IF NOT EXISTS idx_customers_code
            ON customers(code);
    """)
    conn.commit()

    _run_migrations(conn)


def _run_migrations(conn):
    """Migrations آمنة مستقبلية."""
    pass  # للتوسع لاحقاً