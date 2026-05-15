"""
db/shared/migrations_v3.py
===========================
Migration لإضافة:
  1. scope 'design' في جدول categories (إعادة بناء الـ CHECK constraint)
  2. عمود template_fields (JSON) في categories — لتخزين الحقول الافتراضية
  3. عمود default_unit في categories — لتخزين الوحدة الافتراضية
  4. عمود category_id في dimension_sets — لربط المجموعة بتصنيفها

يُستدعى من init_db() بعد run_migrations_v2().
"""

import json


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _get_table_sql(conn, table: str) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row["sql"] if row else ""


_ALL_SCOPES = (
    "raw", "semi", "final", "labor", "machine", "all", "pricing", "design"
)


def _fix_categories_scope(conn):
    """
    يضيف 'design' للـ CHECK constraint في categories.
    يعيد بناء الجدول بأمان (مع حفظ البيانات).
    """
    current_sql = _get_table_sql(conn, "categories")
    if not current_sql:
        return

    if "'design'" in current_sql:
        return  # موجود بالفعل

    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        scope_list = ", ".join(f"'{s}'" for s in _ALL_SCOPES)
        conn.execute(f"""
            CREATE TABLE _categories_v3 (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                scope           TEXT    NOT NULL DEFAULT 'all'
                    CHECK(scope IN ({scope_list})),
                color           TEXT    NOT NULL DEFAULT '#607d8b',
                parent_id       INTEGER REFERENCES _categories_v3(id) ON DELETE SET NULL,
                template_fields TEXT,
                default_unit    TEXT    NOT NULL DEFAULT 'mm'
            )
        """)
        conn.execute("""
            INSERT INTO _categories_v3 (id, name, scope, color, parent_id)
            SELECT id, name, scope, color, parent_id FROM categories
        """)
        conn.execute("DROP TABLE categories")
        conn.execute("ALTER TABLE _categories_v3 RENAME TO categories")
        conn.commit()
    except Exception as e:
        print(f"[migrations_v3] categories rebuild error: {e}")
        try:
            conn.execute("DROP TABLE IF EXISTS _categories_v3")
        except Exception:
            pass
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def run_migrations_v3(conn):
    """تنفيذ migrations v3."""

    # ══ 1. scope 'design' في categories ══════════════════
    _fix_categories_scope(conn)

    # ══ 2. عمود template_fields (fallback لو الجدول لم يُعد بناؤه) ══
    if not _column_exists(conn, "categories", "template_fields"):
        try:
            conn.execute(
                "ALTER TABLE categories ADD COLUMN template_fields TEXT"
            )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v3] template_fields column: {e}")

    # ══ 3. عمود default_unit في categories ══════════════
    if not _column_exists(conn, "categories", "default_unit"):
        try:
            conn.execute(
                "ALTER TABLE categories ADD COLUMN default_unit TEXT NOT NULL DEFAULT 'mm'"
            )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v3] default_unit column: {e}")

    # ══ 4. عمود category_id في dimension_sets ══════════
    # dimension_sets في designs.db — هنتعامل معاه بشكل منفصل
    # (الـ migration ده بيشتغل على erp.db بس)
    # التعديل على designs.db بيحصل في design_schema.py

    conn.commit()