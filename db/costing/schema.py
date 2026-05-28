"""
db/costing/schema.py  (نسخة multi-company)
============================================
إنشاء الجداول والقيم الافتراضية لـ erp.db الخاص بشركة.

التغيير: أضفنا _init_erp_db(conn) التي تقبل connection جاهز
بدلاً من إنشاء connection داخلياً — عشان تدعم multi-company.

إصلاح 3: إضافة عمود total_qty لجدول items.
إصلاح 4: إنشاء جدول categories قبل بقية الجداول التي تُحيل إليه.
إصلاح 5: تغيير نوع عمود settings.value من REAL إلى TEXT
          لدعم القيم النصية مثل ui_theme وgimp_path.
"""

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
        -- [إصلاح 4] categories يجب أن يُنشأ أولاً لأن بقية الجداول
        -- تحتوي على REFERENCES categories(id)
        CREATE TABLE IF NOT EXISTS categories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            scope           TEXT    NOT NULL DEFAULT 'all',
            color           TEXT    NOT NULL DEFAULT '#607d8b',
            parent_id       INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            template_fields TEXT,
            default_unit    TEXT    NOT NULL DEFAULT 'mm'
        );

        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            type        TEXT    NOT NULL CHECK(type IN ('raw','semi','final')),
            price       REAL    NOT NULL DEFAULT 0,
            total_qty   REAL,
            -- [إصلاح 3] total_qty مطلوب في items_repo و shared_items_bridge و models/costing
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

        -- [إصلاح 5] value كـ TEXT بدل REAL لدعم القيم النصية
        -- (ui_theme, ui_language, gimp_path, ...)
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );
    """)

    # القيم الافتراضية — كلها نصوص الآن (TEXT column)
    cur.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        [
            ("monthly_salary",    "3000.0"),
            ("working_days",        "25.0"),
            ("holiday_days",         "4.0"),
            ("working_hours_day",    "8.0"),
            ("overhead_factor",      "1.10"),
            ("font_size",           "11.0"),
        ]
    )

    # migration آمن للشركات القديمة التي تحتوي settings.value كـ REAL
    _migrate_erp_db(conn)


def _migrate_erp_db(conn):
    """
    Migrations آمنة للشركات الموجودة.

    [إصلاح 3] يضيف total_qty لجدول items لو ناقص.
    [إصلاح 4] يضيف جدول categories لو ناقص.
    [إصلاح 5] لا يمكن تغيير نوع عمود في SQLite مباشرة،
               لكن الـ settings الجديدة ستُخزَّن كـ TEXT بشفافية
               (SQLite يدعم type affinity — TEXT يقبل كل القيم).
    """
    # فحص وجود الأعمدة والجداول
    def _table_exists(tbl):
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
        ).fetchone()
        return row is not None

    def _col_exists(tbl, col):
        try:
            rows = conn.execute(f"PRAGMA table_info({tbl})").fetchall()
            return any(r["name"] == col for r in rows)
        except Exception:
            return False

    # [إصلاح 4] أنشئ categories لو ناقصة
    if not _table_exists("categories"):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                scope           TEXT    NOT NULL DEFAULT 'all',
                color           TEXT    NOT NULL DEFAULT '#607d8b',
                parent_id       INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                template_fields TEXT,
                default_unit    TEXT    NOT NULL DEFAULT 'mm'
            )
        """)
        conn.commit()

    # [إصلاح 3] أضف total_qty لجدول items لو ناقص
    if _table_exists("items") and not _col_exists("items", "total_qty"):
        conn.execute("ALTER TABLE items ADD COLUMN total_qty REAL")
        conn.commit()


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