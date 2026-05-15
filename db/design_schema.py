"""
db/design_schema.py
====================
إنشاء جداول قاعدة بيانات التصميمات (designs.db).

الجداول:
  design_categories   — تصنيفات التصميم (أثاث، ديكور، ...)
  dimension_sets      — مجموعات المقاسات (مجموعة مقاسات كاملة)
  dimension_fields    — الحقول/الأعمدة لكل مجموعة مقاسات (طول، عرض، سُمك...)
  shapes              — الأشكال (الوحدات القابلة للتصنيع)
  shape_dimensions    — قيم المقاسات لكل شكل (shape × dimension_field → value)

العلاقات:
  - الشكل ينتمي لتصنيف design_categories
  - الشكل يرتبط بـ dimension_set (مجموعة مقاساته)
  - كل حقل (dimension_field) ينتمي لـ dimension_set
  - shape_dimensions تخزن القيمة الفعلية لكل حقل لكل شكل
"""

import sqlite3
import os

_BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DESIGN_DB_PATH = os.path.join(_BASE_DIR, "designs.db")


def get_design_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DESIGN_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.isolation_level = None
    return conn


def create_design_tables(conn):
    conn.executescript("""
        -- تصنيفات التصميم
        CREATE TABLE IF NOT EXISTS design_categories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            color      TEXT    NOT NULL DEFAULT '#607d8b',
            icon       TEXT    NOT NULL DEFAULT '📐',
            notes      TEXT,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- مجموعات المقاسات (template للحقول)
        CREATE TABLE IF NOT EXISTS dimension_sets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT,
            unit        TEXT    NOT NULL DEFAULT 'mm',
            color       TEXT    NOT NULL DEFAULT '#1565c0',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- حقول/أعمدة كل مجموعة مقاسات
        CREATE TABLE IF NOT EXISTS dimension_fields (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id       INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
            name         TEXT    NOT NULL,
            label        TEXT    NOT NULL,
            unit         TEXT,
            field_type   TEXT    NOT NULL DEFAULT 'number'
                CHECK(field_type IN ('number', 'text', 'boolean', 'select')),
            options      TEXT,   -- JSON لـ select field
            required     INTEGER NOT NULL DEFAULT 1,
            sort_order   INTEGER NOT NULL DEFAULT 0,
            notes        TEXT
        );

        -- الأشكال
        CREATE TABLE IF NOT EXISTS shapes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            category_id  INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
            dim_set_id   INTEGER REFERENCES dimension_sets(id) ON DELETE SET NULL,
            description  TEXT,
            material     TEXT,
            notes        TEXT,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- قيم المقاسات لكل شكل
        CREATE TABLE IF NOT EXISTS shape_dimensions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            shape_id  INTEGER NOT NULL REFERENCES shapes(id) ON DELETE CASCADE,
            field_id  INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
            value     TEXT    NOT NULL DEFAULT '',
            UNIQUE(shape_id, field_id)
        );

        -- فهارس للأداء
        CREATE INDEX IF NOT EXISTS idx_shapes_category ON shapes(category_id);
        CREATE INDEX IF NOT EXISTS idx_shapes_dimset   ON shapes(dim_set_id);
        CREATE INDEX IF NOT EXISTS idx_dimfields_set   ON dimension_fields(set_id);
        CREATE INDEX IF NOT EXISTS idx_shapedims_shape ON shape_dimensions(shape_id);
    """)
    conn.commit()
    _seed_defaults(conn)


def _seed_defaults(conn):
    """بيانات افتراضية لو قاعدة البيانات فارغة."""
    count = conn.execute("SELECT COUNT(*) as c FROM design_categories").fetchone()["c"]
    if count > 0:
        return

    # تصنيفات افتراضية
    cats = [
        ("أثاث", "#795548", "🪑"),
        ("ديكور", "#9c27b0", "🖼"),
        ("أبواب وشبابيك", "#2196f3", "🚪"),
        ("أخرى", "#607d8b", "📦"),
    ]
    for name, color, icon in cats:
        conn.execute(
            "INSERT INTO design_categories (name, color, icon) VALUES (?, ?, ?)",
            (name, color, icon)
        )

    # مجموعة مقاسات افتراضية
    cur = conn.execute(
        "INSERT INTO dimension_sets (name, description, unit, color) VALUES (?, ?, ?, ?)",
        ("مقاسات قياسية", "طول × عرض × ارتفاع × سُمك", "mm", "#1565c0")
    )
    set_id = cur.lastrowid

    fields = [
        ("length",   "الطول",   "mm", "number", 0),
        ("width",    "العرض",   "mm", "number", 1),
        ("height",   "الارتفاع","mm", "number", 2),
        ("thickness","السُمك",  "mm", "number", 3),
    ]
    for name, label, unit, ftype, order in fields:
        conn.execute(
            "INSERT INTO dimension_fields (set_id, name, label, unit, field_type, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (set_id, name, label, unit, ftype, order)
        )

    conn.commit()