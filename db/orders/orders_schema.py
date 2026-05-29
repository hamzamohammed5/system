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

تحسين 25:
  - _run_migrations مُنفَّذة بـ framework حقيقي (مش pass فارغ).
  - كل migration مُعرَّف كـ entry في _MIGRATIONS dict.
  - جدول schema_migrations يحفظ الـ migrations المُطبَّقة.
  - آمن للاستدعاء المتكرر (idempotent).

[Q-02] توثيق سلوك الـ migration framework عند الفشل:
  إذا نجح _ensure_migrations_table لكن فشل _apply_migration، الجدول
  موجود بدون entries. عند إعادة التشغيل، _is_applied() يرجع False
  لأن migration_name غير موجود → يُعاد تطبيق الـ migration.
  هذا السلوك صحيح ومقصود: الـ migrations يجب أن تكون idempotent.
  لكل migration تأكد من أنه آمن للتطبيق أكثر من مرة (استخدم
  IF NOT EXISTS, OR IGNORE, COALESCE, إلخ).
"""

import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

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
            code            TEXT    UNIQUE,
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
            role        TEXT,
            phone       TEXT,
            email       TEXT,
            notes       TEXT
        );

        -- ══ الطلبات ══════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number    TEXT    UNIQUE NOT NULL,
            customer_id     INTEGER NOT NULL
                            REFERENCES customers(id) ON DELETE RESTRICT,
            order_type      TEXT    NOT NULL DEFAULT 'new'
                            CHECK(order_type IN ('new','reorder','custom')),
            status          TEXT    NOT NULL DEFAULT 'pending'
                            CHECK(status IN (
                                'pending','confirmed','in_progress',
                                'ready','delivered','cancelled','on_hold'
                            )),
            priority        TEXT    NOT NULL DEFAULT 'normal'
                            CHECK(priority IN ('low','normal','high','urgent')),
            order_date      TEXT    NOT NULL DEFAULT (date('now')),
            due_date        TEXT,
            delivery_date   TEXT,
            total_amount    REAL    NOT NULL DEFAULT 0,
            discount        REAL    NOT NULL DEFAULT 0,
            net_amount      REAL    NOT NULL DEFAULT 0,
            paid_amount     REAL    NOT NULL DEFAULT 0,
            notes           TEXT,
            internal_notes  TEXT,
            reference_order INTEGER
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
            design_ref      TEXT,
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


# ══════════════════════════════════════════════════════════
# Migration Framework — تحسين 25
# ══════════════════════════════════════════════════════════

def _ensure_migrations_table(conn):
    """
    ينشئ جدول schema_migrations لتتبع الـ migrations المُطبَّقة.
    آمن للاستدعاء المتكرر (idempotent).
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,
            applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _is_applied(conn, name: str) -> bool:
    """
    هل تم تطبيق migration بهذا الاسم مسبقاً؟

    [Q-02] ملاحظة السلوك عند فشل migration سابق:
    إذا فشل _apply_migration في التسجيل عبر _mark_applied لكن نجح
    في تطبيق التغييرات الفعلية، سيُعاد تطبيق الـ migration في التشغيل التالي.
    لهذا يجب أن تكون كل الـ migrations idempotent (آمنة للتطبيق مرتين).
    """
    try:
        row = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE name=?", (name,)
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _mark_applied(conn, name: str):
    """سجّل الـ migration كـ مُطبَّق."""
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations (name) VALUES (?)", (name,)
    )
    conn.commit()


def _apply_migration(conn, name: str, fn):
    """
    يُطبّق migration واحد بشكل آمن.
    - لو مطبَّق مسبقاً → يتخطاه
    - لو فشل → يُسجّل تحذيراً ويكمل (لا يوقف التطبيق)

    [Q-02] إذا نجح fn() لكن فشل _mark_applied() (حالة نادرة جداً مثل
    disk full)، سيُعاد تطبيق الـ migration في التشغيل التالي. هذا مقبول
    لأن كل migration يجب أن يكون idempotent (IF NOT EXISTS, OR IGNORE, إلخ).
    """
    if _is_applied(conn, name):
        return

    try:
        fn(conn)
        _mark_applied(conn, name)
        logger.info("[orders_schema] migration '%s' applied successfully", name)
    except Exception as e:
        logger.warning(
            "[orders_schema] migration '%s' failed: %s — skipping", name, e
        )


# ══════════════════════════════════════════════════════════
# تعريف الـ Migrations
# ══════════════════════════════════════════════════════════

def _m001_add_internal_notes(conn):
    """
    M001: إضافة عمود internal_notes لجدول orders لو ناقص.
    idempotent: يتحقق من وجود العمود قبل إضافته.
    """
    if _table_exists(conn, "orders") and not _column_exists(conn, "orders", "internal_notes"):
        conn.execute("ALTER TABLE orders ADD COLUMN internal_notes TEXT")
        conn.commit()


def _m002_add_customers_phone2(conn):
    """
    M002: إضافة عمود phone2 لجدول customers لو ناقص.
    idempotent: يتحقق من وجود العمود قبل إضافته.
    """
    if _table_exists(conn, "customers") and not _column_exists(conn, "customers", "phone2"):
        conn.execute("ALTER TABLE customers ADD COLUMN phone2 TEXT")
        conn.commit()


def _m003_add_orders_priority(conn):
    """
    M003: إضافة عمود priority لجدول orders لو ناقص.
    idempotent: يتحقق من وجود العمود قبل إضافته.
    """
    if _table_exists(conn, "orders") and not _column_exists(conn, "orders", "priority"):
        conn.execute(
            "ALTER TABLE orders ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'"
        )
        conn.commit()


def _m004_add_idx_orders_priority(conn):
    """
    M004: إضافة index على priority للـ filtering السريع.
    idempotent: IF NOT EXISTS يضمن عدم الفشل عند إعادة التطبيق.
    """
    try:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_orders_priority ON orders(priority)"
        )
        conn.commit()
    except Exception:
        pass


def _m005_add_customer_contacts_role(conn):
    """
    M005: إضافة عمود role لجدول customer_contacts لو ناقص.
    idempotent: يتحقق من وجود العمود قبل إضافته.
    """
    if (_table_exists(conn, "customer_contacts") and
            not _column_exists(conn, "customer_contacts", "role")):
        conn.execute("ALTER TABLE customer_contacts ADD COLUMN role TEXT")
        conn.commit()


# قائمة كل الـ migrations مرتبة
# كل entry: (اسم فريد, الدالة)
# الترتيب مهم — migrations تُطبَّق بالترتيب
# [Q-02] كل migration يجب أن يكون idempotent (آمن للتطبيق مرتين)
_MIGRATIONS = [
    ("m001_add_internal_notes",         _m001_add_internal_notes),
    ("m002_add_customers_phone2",       _m002_add_customers_phone2),
    ("m003_add_orders_priority",        _m003_add_orders_priority),
    ("m004_add_idx_orders_priority",    _m004_add_idx_orders_priority),
    ("m005_add_customer_contacts_role", _m005_add_customer_contacts_role),
]


def _run_migrations(conn):
    """
    [تحسين 25] Framework كامل للـ migrations بدل pass الفارغ.

    يُنشئ جدول schema_migrations لتتبع ما تم تطبيقه،
    ويُطبّق كل migration مرة واحدة فقط بشكل آمن.

    [Q-02] سلوك الـ framework عند الفشل:
    - إذا فشل _ensure_migrations_table → لا migrations تُطبَّق (مع warning)
    - إذا فشل migration معين → يُسجَّل warning ويُتخطى (الباقي يكمل)
    - إذا نجح migration لكن فشل _mark_applied → يُعاد تطبيقه في التشغيل التالي
      (مقبول لأن كل migration يجب أن يكون idempotent)

    لإضافة migration جديد:
      1. عرّف دالة idempotent: def _mXXX_description(conn): ...
      2. أضفها لقائمة _MIGRATIONS بالترتيب الصحيح

    مثال migration idempotent:
      def _m006_add_order_tags(conn):
          # IF NOT EXISTS يضمن الأمان عند إعادة التطبيق
          if not _column_exists(conn, "orders", "tags"):
              conn.execute("ALTER TABLE orders ADD COLUMN tags TEXT")
              conn.commit()
    """
    try:
        _ensure_migrations_table(conn)
    except Exception as e:
        logger.warning(
            "[orders_schema] فشل إنشاء جدول schema_migrations: %s — "
            "الـ migrations لن تُطبَّق", e
        )
        return

    for name, fn in _MIGRATIONS:
        _apply_migration(conn, name, fn)
