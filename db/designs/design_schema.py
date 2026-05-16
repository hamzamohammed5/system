"""
db/designs/design_schema.py
============================
Schema قاعدة بيانات التصميمات (designs.db).
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


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _run_migrations(conn):
    """Migrations آمنة على designs.db — تُضاف أعمدة جديدة بدون حذف بيانات."""

    # ══ 1. source_set_id في dimension_field_deps ══
    # يسمح بالاعتمادية على حقل من مجموعة مقاسات مختلفة (cross-set)
    if _table_exists(conn, "dimension_field_deps"):
        if not _column_exists(conn, "dimension_field_deps", "source_set_id"):
            try:
                conn.execute(
                    "ALTER TABLE dimension_field_deps "
                    "ADD COLUMN source_set_id INTEGER "
                    "REFERENCES dimension_sets(id) ON DELETE SET NULL"
                )
                conn.commit()
            except Exception as e:
                print(f"[design_schema] migration source_set_id: {e}")

    # ══ 2. جدول dimension_set_values ══
    # قيم مستقلة لمجموعة المقاسات (بدون ربط بتصميم)
    if not _table_exists(conn, "dimension_set_values"):
        try:
            conn.execute("""
                CREATE TABLE dimension_set_values (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_id      INTEGER NOT NULL
                                REFERENCES dimension_sets(id) ON DELETE CASCADE,
                    field_id    INTEGER NOT NULL
                                REFERENCES dimension_fields(id) ON DELETE CASCADE,
                    value_num   REAL,
                    value_text  TEXT,
                    UNIQUE(set_id, field_id)
                )
            """)
            conn.commit()
        except Exception as e:
            print(f"[design_schema] migration dimension_set_values: {e}")


def create_designs_tables(conn):
    """إنشاء كل جداول designs.db ثم تنفيذ الـ migrations."""

    conn.executescript("""
        -- تصنيفات التصميمات
        CREATE TABLE IF NOT EXISTS design_categories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            color           TEXT    NOT NULL DEFAULT '#1565c0',
            parent_id       INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
            notes           TEXT
        );

        -- مجموعات المقاسات
        CREATE TABLE IF NOT EXISTS dimension_sets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            category_id     INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
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

        -- اعتماديات حقل على حقل آخر (مع دعم cross-set)
        CREATE TABLE IF NOT EXISTS dimension_field_deps (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id        INTEGER NOT NULL
                            REFERENCES dimension_fields(id) ON DELETE CASCADE,
            source_field_id INTEGER NOT NULL
                            REFERENCES dimension_fields(id) ON DELETE CASCADE,
            source_set_id   INTEGER
                            REFERENCES dimension_sets(id) ON DELETE SET NULL,
            offset          REAL    NOT NULL DEFAULT 0,
            notes           TEXT,
            UNIQUE(field_id)
        );

        -- قيم مستقلة لمجموعة المقاسات (بدون ربط بتصميم)
        CREATE TABLE IF NOT EXISTS dimension_set_values (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id      INTEGER NOT NULL
                        REFERENCES dimension_sets(id) ON DELETE CASCADE,
            field_id    INTEGER NOT NULL
                        REFERENCES dimension_fields(id) ON DELETE CASCADE,
            value_num   REAL,
            value_text  TEXT,
            UNIQUE(set_id, field_id)
        );

        -- التصميمات
        CREATE TABLE IF NOT EXISTS designs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category_id INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
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

        -- قيم الحقول لكل ربط تصميم ↔ مقاسات
        CREATE TABLE IF NOT EXISTS design_dim_values (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id     INTEGER NOT NULL
                        REFERENCES design_dimensions(id) ON DELETE CASCADE,
            field_id    INTEGER NOT NULL
                        REFERENCES dimension_fields(id) ON DELETE CASCADE,
            value_num   REAL,
            value_text  TEXT,
            is_auto     INTEGER NOT NULL DEFAULT 0,
            UNIQUE(link_id, field_id)
        );
    """)
    conn.commit()

    # تنفيذ الـ migrations على قواعد البيانات الموجودة
    _run_migrations(conn)