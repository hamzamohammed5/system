"""
db/designs/migrations_v7.py
============================
Migration لإضافة جدول design_item_categories —
تصنيفات التصميمات المستقلة (منفصلة عن design_categories الخاصة بمجموعات المقاسات).

التغييرات:
  1. جدول design_item_categories — هرمي (parent_id) مع اسم ولون
  2. عمود item_category_id في designs — يشير للجدول الجديد
     (category_id القديم يبقى للتوافق مع مجموعات المقاسات)
"""


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def run_migrations_v7(conn):
    """تنفيذ migration v7 — تصنيفات التصميمات المستقلة."""

    # ══ 1. جدول design_item_categories ══════════════════
    if not _table_exists(conn, "design_item_categories"):
        conn.execute("""
            CREATE TABLE design_item_categories (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT    NOT NULL,
                color     TEXT    NOT NULL DEFAULT '#7c3aed',
                parent_id INTEGER
                          REFERENCES design_item_categories(id) ON DELETE SET NULL,
                notes     TEXT
            )
        """)
        conn.commit()

    # ══ 2. عمود item_category_id في designs ══════════════
    if not _column_exists(conn, "designs", "item_category_id"):
        try:
            conn.execute(
                "ALTER TABLE designs ADD COLUMN item_category_id INTEGER "
                "REFERENCES design_item_categories(id) ON DELETE SET NULL"
            )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v7] item_category_id column: {e}")