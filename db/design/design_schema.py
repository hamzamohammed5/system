"""
db/design_schema.py
====================
إنشاء جداول قاعدة بيانات التصميمات (designs.db).

الجداول:
  dim_set_categories       — تصنيفات مجموعات المقاسات (خشب، معدن، قماش...)
  dim_set_category_fields  — الحقول الافتراضية (template) لكل تصنيف
  design_categories        — تصنيفات التصميم (أثاث، ديكور، ...)
  dimension_sets           — مجموعات المقاسات
  dimension_fields         — الحقول/الأعمدة لكل مجموعة مقاسات
  shapes                   — الأشكال
  shape_dimensions         — قيم المقاسات لكل شكل
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
    # ══════════════════════════════════════════════════════
    # الجداول الأساسية — بدون category_id في dimension_sets
    # (يُضاف لاحقاً بـ migration آمن تحت)
    # ══════════════════════════════════════════════════════
    conn.executescript("""
        -- ══════════════════════════════════════════════
        -- تصنيفات مجموعات المقاسات
        -- ══════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS dim_set_categories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            description     TEXT,
            default_unit    TEXT    NOT NULL DEFAULT 'mm',
            color           TEXT    NOT NULL DEFAULT '#1565c0',
            icon            TEXT    NOT NULL DEFAULT '📏',
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- الحقول الافتراضية (template) لكل تصنيف مقاسات
        CREATE TABLE IF NOT EXISTS dim_set_category_fields (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL
                REFERENCES dim_set_categories(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            label       TEXT    NOT NULL,
            unit        TEXT,
            field_type  TEXT    NOT NULL DEFAULT 'number'
                CHECK(field_type IN ('number', 'text', 'boolean', 'select')),
            options     TEXT,
            required    INTEGER NOT NULL DEFAULT 1,
            sort_order  INTEGER NOT NULL DEFAULT 0
        );

        -- ══════════════════════════════════════════════
        -- تصنيفات التصميم
        -- ══════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS design_categories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            color      TEXT    NOT NULL DEFAULT '#607d8b',
            icon       TEXT    NOT NULL DEFAULT '📐',
            notes      TEXT,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- مجموعات المقاسات — بدون category_id (يُضاف بـ migration)
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
            options      TEXT,
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

        -- فهارس
        CREATE INDEX IF NOT EXISTS idx_shapes_category   ON shapes(category_id);
        CREATE INDEX IF NOT EXISTS idx_shapes_dimset     ON shapes(dim_set_id);
        CREATE INDEX IF NOT EXISTS idx_dimfields_set     ON dimension_fields(set_id);
        CREATE INDEX IF NOT EXISTS idx_shapedims_shape   ON shape_dimensions(shape_id);
        CREATE INDEX IF NOT EXISTS idx_dscfields_cat     ON dim_set_category_fields(category_id);
    """)

    # ══════════════════════════════════════════════════════
    # Migration آمن: عمود category_id في dimension_sets
    # يعمل مع DB جديدة وقديمة على حدٍّ سواء
    # ══════════════════════════════════════════════════════
    try:
        conn.execute(
            "ALTER TABLE dimension_sets ADD COLUMN category_id INTEGER "
            "REFERENCES dim_set_categories(id) ON DELETE SET NULL"
        )
        conn.commit()
    except Exception:
        pass  # العمود موجود بالفعل — نتجاهل الخطأ

    # ══════════════════════════════════════════════════════
    # Migration آمن: فهرس category_id في dimension_sets
    # ══════════════════════════════════════════════════════
    try:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_dimsets_category "
            "ON dimension_sets(category_id)"
        )
        conn.commit()
    except Exception:
        pass

    conn.commit()
    _seed_defaults(conn)


def _seed_defaults(conn):
    """بيانات افتراضية لو قاعدة البيانات فارغة."""

    # ── تصنيفات مجموعات المقاسات ──
    count = conn.execute(
        "SELECT COUNT(*) as c FROM dim_set_categories"
    ).fetchone()["c"]

    if count == 0:
        set_cats = [
            ("خشب",   "مقاسات الأشكال الخشبية",   "mm",   "#795548", "🪵"),
            ("معدن",  "مقاسات الأشكال المعدنية",   "mm",   "#546e7a", "⚙️"),
            ("قماش",  "مقاسات الأقمشة والمفروشات", "cm",   "#7b1fa2", "🧵"),
            ("زجاج",  "مقاسات الزجاج والمرايا",    "mm",   "#0288d1", "🪟"),
        ]
        template_fields = {
            "خشب":  [
                ("length",    "الطول",    "mm", "number", 0),
                ("width",     "العرض",    "mm", "number", 1),
                ("height",    "الارتفاع", "mm", "number", 2),
                ("thickness", "السُمك",   "mm", "number", 3),
            ],
            "معدن": [
                ("length",    "الطول",    "mm", "number", 0),
                ("width",     "العرض",    "mm", "number", 1),
                ("thickness", "السُمك",   "mm", "number", 2),
            ],
            "قماش": [
                ("length",    "الطول",    "cm", "number", 0),
                ("width",     "العرض",    "cm", "number", 1),
            ],
            "زجاج": [
                ("length",    "الطول",    "mm", "number", 0),
                ("width",     "العرض",    "mm", "number", 1),
                ("thickness", "السُمك",   "mm", "number", 2),
            ],
        }

        for name, desc, unit, color, icon in set_cats:
            cur = conn.execute(
                "INSERT INTO dim_set_categories (name, description, default_unit, color, icon) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, desc, unit, color, icon)
            )
            cat_id = cur.lastrowid
            for fname, flabel, funit, ftype, order in template_fields.get(name, []):
                conn.execute(
                    "INSERT INTO dim_set_category_fields "
                    "(category_id, name, label, unit, field_type, required, sort_order) "
                    "VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (cat_id, fname, flabel, funit, ftype, order)
                )

    # ── تصنيفات التصميم ──
    count2 = conn.execute(
        "SELECT COUNT(*) as c FROM design_categories"
    ).fetchone()["c"]
    if count2 == 0:
        cats = [
            ("أثاث",            "#795548", "🪑"),
            ("ديكور",           "#9c27b0", "🖼"),
            ("أبواب وشبابيك",  "#2196f3", "🚪"),
            ("أخرى",            "#607d8b", "📦"),
        ]
        for name, color, icon in cats:
            conn.execute(
                "INSERT INTO design_categories (name, color, icon) VALUES (?, ?, ?)",
                (name, color, icon)
            )

    # ── مجموعة مقاسات افتراضية ──
    count3 = conn.execute(
        "SELECT COUNT(*) as c FROM dimension_sets"
    ).fetchone()["c"]
    if count3 == 0:
        cur = conn.execute(
            "INSERT INTO dimension_sets (name, description, unit, color) VALUES (?, ?, ?, ?)",
            ("مقاسات قياسية", "طول × عرض × ارتفاع × سُمك", "mm", "#1565c0")
        )
        set_id = cur.lastrowid
        fields = [
            ("length",    "الطول",    "mm", "number", 0),
            ("width",     "العرض",    "mm", "number", 1),
            ("height",    "الارتفاع", "mm", "number", 2),
            ("thickness", "السُمك",   "mm", "number", 3),
        ]
        for name, label, unit, ftype, order in fields:
            conn.execute(
                "INSERT INTO dimension_fields "
                "(set_id, name, label, unit, field_type, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (set_id, name, label, unit, ftype, order)
            )

    conn.commit()