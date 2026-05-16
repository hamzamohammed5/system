"""
db/designs/migrations_v5.py
============================
Migration لإضافة نظام ربط التصميمات بالمقاسات الفعلية + مسارات GIMP.

الجديد:
  1. جدول design_sizes — ربط التصميم بـ instance محدد من مجموعة مقاسات
     + مسار ملف GIMP (.xcf) + اختيار حقلَي العرض والطول
  2. عمود dpi_field_id — حقل رقمي من نفس المجموعة يحمل قيمة الـ DPI
     (تُقرأ قيمته من الـ instance تماماً كالعرض والطول)
"""


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def run_migrations_v5(conn):
    """تنفيذ migration v5 — نظام design_sizes."""

    # ══ 1. جدول design_sizes ══════════════════════════════
    if not _table_exists(conn, "design_sizes"):
        conn.execute("""
            CREATE TABLE design_sizes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                design_id       INTEGER NOT NULL
                                REFERENCES designs(id) ON DELETE CASCADE,
                set_id          INTEGER NOT NULL
                                REFERENCES dimension_sets(id) ON DELETE RESTRICT,
                instance_id     INTEGER NOT NULL
                                REFERENCES dimension_set_instances(id) ON DELETE RESTRICT,
                width_field_id  INTEGER
                                REFERENCES dimension_fields(id) ON DELETE SET NULL,
                height_field_id INTEGER
                                REFERENCES dimension_fields(id) ON DELETE SET NULL,
                dpi_field_id    INTEGER
                                REFERENCES dimension_fields(id) ON DELETE SET NULL,
                xcf_path        TEXT,
                notes           TEXT,
                sort_order      INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(design_id, instance_id)
            )
        """)
        conn.commit()

    # ══ 2. عمود dpi_field_id في design_sizes (للجداول الموجودة) ══
    if not _column_exists(conn, "design_sizes", "dpi_field_id"):
        conn.execute(
            "ALTER TABLE design_sizes ADD COLUMN dpi_field_id INTEGER "
            "REFERENCES dimension_fields(id) ON DELETE SET NULL"
        )
        conn.commit()