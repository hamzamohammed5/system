"""
db/designs/design_schema.py
============================
Schema قاعدة بيانات التصميمات (designs.db).

الجداول:
  design_categories   — تصنيفات التصميمات (مع template_fields)
  dimension_sets      — مجموعات المقاسات (كل مجموعة = نوع مقاسات)
  dimension_fields    — حقول كل مجموعة مقاسات (طول، عرض، ...)
  dimension_field_deps— اعتماديات الحقول (حقل = حقل آخر + offset)
  designs             — التصميمات
  design_dimensions   — ربط التصميم بالمقاسات (التصميم ↔ مجموعة ↔ قيم)
  design_dim_values   — قيم الحقول لكل ربط
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
        -- تصنيفات التصميمات
        CREATE TABLE IF NOT EXISTS design_categories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            color           TEXT    NOT NULL DEFAULT '#1565c0',
            parent_id       INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
            notes           TEXT
        );

        -- مجموعات المقاسات
        -- كل مجموعة تمثل "نوع" مقاسات (مثلاً: مقاسات الثوب = طول + عرض)
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

        -- اعتماديات حقل على حقل آخر
        -- قيمة الحقل = قيمة source_field_id + offset
        CREATE TABLE IF NOT EXISTS dimension_field_deps (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id        INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            source_field_id INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            offset          REAL    NOT NULL DEFAULT 0,
            notes           TEXT,
            UNIQUE(field_id)
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
        -- التصميم الواحد ممكن يكون له أكثر من ربط (أحجام مختلفة)
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
            link_id     INTEGER NOT NULL REFERENCES design_dimensions(id) ON DELETE CASCADE,
            field_id    INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            value_num   REAL,
            value_text  TEXT,
            is_auto     INTEGER NOT NULL DEFAULT 0,
            UNIQUE(link_id, field_id)
        );
    """)
    conn.commit()