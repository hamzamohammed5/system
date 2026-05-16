"""
db/designs/design_schema.py
============================
Schema قاعدة بيانات التصميمات (designs.db).

الجداول:
  dimension_sets          — مجموعات المقاسات (مع parent_set_id للتدرج الهرمي)
  dimension_fields        — حقول كل مجموعة مقاسات
  dimension_field_deps    — اعتماديات الحقول
  designs                 — التصميمات
  design_dimensions       — ربط التصميم بالمقاسات
  design_dim_values       — قيم الحقول لكل ربط
  dimension_set_values    — قيم مستقلة (بدون تصميم)
  dimension_value_sessions— جلسات إدخال القيم المستقلة (كل جلسة لها اسم)
"""

import os
import sqlite3

_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
DESIGNS_DB_PATH = os.path.join(_BASE_DIR, "designs.db")


def get_designs_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DESIGNS_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.isolation_level = None
    return conn


def create_designs_tables(conn):
    """إنشاء كل جداول designs.db."""
    conn.executescript("""
        -- مجموعات المقاسات (بدون تصنيفات — مع parent_set_id للتدرج)
        CREATE TABLE IF NOT EXISTS dimension_sets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            parent_set_id   INTEGER REFERENCES dimension_sets(id) ON DELETE SET NULL,
            default_unit    TEXT    NOT NULL DEFAULT 'cm',
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- حقول مجموعة المقاسات
        CREATE TABLE IF NOT EXISTS dimension_fields (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id      INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            label       TEXT    NOT NULL,
            unit        TEXT    NOT NULL DEFAULT 'cm',
            field_type  TEXT    NOT NULL DEFAULT 'number'
                CHECK(field_type IN ('number', 'text')),
            required    INTEGER NOT NULL DEFAULT 1,
            sort_order  INTEGER NOT NULL DEFAULT 0
        );

        -- اعتماديات حقل على حقل آخر
        CREATE TABLE IF NOT EXISTS dimension_field_deps (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id        INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            source_field_id INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            source_set_id   INTEGER REFERENCES dimension_sets(id) ON DELETE SET NULL,
            offset          REAL    NOT NULL DEFAULT 0,
            notes           TEXT,
            UNIQUE(field_id)
        );

        -- التصميمات
        CREATE TABLE IF NOT EXISTS designs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            notes       TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ربط التصميم بالمقاسات
        CREATE TABLE IF NOT EXISTS design_dimensions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            design_id   INTEGER NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
            set_id      INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE RESTRICT,
            label       TEXT,
            sort_order  INTEGER NOT NULL DEFAULT 0
        );

        -- قيم الحقول لكل ربط تصميم
        CREATE TABLE IF NOT EXISTS design_dim_values (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id     INTEGER NOT NULL REFERENCES design_dimensions(id) ON DELETE CASCADE,
            field_id    INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            value_num   REAL,
            value_text  TEXT,
            is_auto     INTEGER NOT NULL DEFAULT 0,
            UNIQUE(link_id, field_id)
        );

        -- جلسات إدخال القيم المستقلة (كل جلسة لها اسم)
        CREATE TABLE IF NOT EXISTS dimension_value_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id      INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL DEFAULT 'جلسة جديدة',
            notes       TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- قيم الحقول لكل جلسة مستقلة
        CREATE TABLE IF NOT EXISTS dimension_set_values (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL REFERENCES dimension_value_sessions(id) ON DELETE CASCADE,
            set_id      INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
            field_id    INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            value_num   REAL,
            UNIQUE(session_id, field_id)
        );
    """)

    # ── Migrations للقواعد القديمة ──
    _run_migrations(conn)
    conn.commit()


def _run_migrations(conn):
    """إضافة الأعمدة الجديدة لو الجدول موجود من قبل."""
    cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(dimension_sets)"
    ).fetchall()]

    # استبدال category_id بـ parent_set_id
    if "category_id" in cols and "parent_set_id" not in cols:
        conn.execute(
            "ALTER TABLE dimension_sets ADD COLUMN parent_set_id INTEGER "
            "REFERENCES dimension_sets(id) ON DELETE SET NULL"
        )

    if "parent_set_id" not in cols and "category_id" not in cols:
        conn.execute(
            "ALTER TABLE dimension_sets ADD COLUMN parent_set_id INTEGER "
            "REFERENCES dimension_sets(id) ON DELETE SET NULL"
        )

    # source_set_id في dimension_field_deps
    dep_cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(dimension_field_deps)"
    ).fetchall()]
    if "source_set_id" not in dep_cols:
        conn.execute(
            "ALTER TABLE dimension_field_deps ADD COLUMN source_set_id INTEGER "
            "REFERENCES dimension_sets(id) ON DELETE SET NULL"
        )

    # جلسات القيم المستقلة
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]

    if "dimension_value_sessions" not in tables:
        conn.execute("""
            CREATE TABLE dimension_value_sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id     INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
                name       TEXT    NOT NULL DEFAULT 'جلسة جديدة',
                notes      TEXT,
                created_at TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)

    # تعديل dimension_set_values لتدعم session_id
    if "dimension_set_values" in tables:
        sv_cols = [r[1] for r in conn.execute(
            "PRAGMA table_info(dimension_set_values)"
        ).fetchall()]
        if "session_id" not in sv_cols:
            # نعيد بناء الجدول بالشكل الجديد
            conn.executescript("""
                ALTER TABLE dimension_set_values RENAME TO _dsv_old;

                CREATE TABLE dimension_set_values (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL
                               REFERENCES dimension_value_sessions(id) ON DELETE CASCADE,
                    set_id     INTEGER NOT NULL
                               REFERENCES dimension_sets(id) ON DELETE CASCADE,
                    field_id   INTEGER NOT NULL
                               REFERENCES dimension_fields(id) ON DELETE CASCADE,
                    value_num  REAL,
                    UNIQUE(session_id, field_id)
                );

                DROP TABLE _dsv_old;
            """)