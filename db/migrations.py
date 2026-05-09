"""
db/migrations.py
================
Migrations آمنة للـ DB الموجودة — تُضاف أعمدة وجداول جديدة بدون حذف بيانات.
يُستدعى من init_db() بعد CREATE TABLE.
"""

from db.offers_repo import create_offers_tables



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


_CATEGORIES_VALID_SCOPES = ("raw", "semi", "final", "labor", "machine", "all", "pricing")


def _fix_categories_check_constraint(conn):
    """إعادة بناء جدول categories لو الـ CHECK constraint ناقص منه scopes."""
    current_sql = _get_table_sql(conn, "categories")
    if not current_sql:
        return

    missing = [s for s in _CATEGORIES_VALID_SCOPES if f"'{s}'" not in current_sql]
    if not missing:
        return

    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("""
            CREATE TABLE _categories_new (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT    NOT NULL,
                scope TEXT    NOT NULL DEFAULT 'all'
                    CHECK(scope IN ('raw','semi','final','labor','machine','all','pricing')),
                color TEXT    NOT NULL DEFAULT '#607d8b'
            )
        """)
        conn.execute(f"""
            INSERT INTO _categories_new (id, name, scope, color)
            SELECT id, name,
                CASE
                    WHEN scope IN ({', '.join(f"'{s}'" for s in _CATEGORIES_VALID_SCOPES)})
                    THEN scope ELSE 'all'
                END,
                color
            FROM categories
        """)
        conn.execute("DROP TABLE categories")
        conn.execute("ALTER TABLE _categories_new RENAME TO categories")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def run_migrations(conn):
    """نفّذ كل الـ migrations بشكل آمن."""

    # ══ 1. جدول categories ══════════════════════════════
    if not _table_exists(conn, "categories"):
        conn.execute("""
            CREATE TABLE categories (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT    NOT NULL,
                scope TEXT    NOT NULL DEFAULT 'all'
                    CHECK(scope IN ('raw','semi','final','labor','machine','all','pricing')),
                color TEXT    NOT NULL DEFAULT '#607d8b'
            )
        """)
        conn.commit()
    else:
        _fix_categories_check_constraint(conn)
        conn.commit()

    # ══ 2. جدول pricing ═════════════════════════════════
    if not _table_exists(conn, "pricing"):
        conn.execute("""
            CREATE TABLE pricing (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL UNIQUE REFERENCES items(id) ON DELETE CASCADE,
                margin  REAL    NOT NULL DEFAULT 1.0,
                price   REAL    NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

    # ══ 3. عمود category_id في items ════════════════════
    if not _column_exists(conn, "items", "category_id"):
        conn.execute(
            "ALTER TABLE items ADD COLUMN category_id INTEGER "
            "REFERENCES categories(id) ON DELETE SET NULL"
        )
        conn.commit()

    # ══ 4. عمود category_id في labor_ops ════════════════
    if not _column_exists(conn, "labor_ops", "category_id"):
        conn.execute(
            "ALTER TABLE labor_ops ADD COLUMN category_id INTEGER "
            "REFERENCES categories(id) ON DELETE SET NULL"
        )
        conn.commit()

    # ══ 5. عمود category_id في machine_ops ══════════════
    if not _column_exists(conn, "machine_ops", "category_id"):
        conn.execute(
            "ALTER TABLE machine_ops ADD COLUMN category_id INTEGER "
            "REFERENCES categories(id) ON DELETE SET NULL"
        )
        conn.commit()

    # ══ 6. عمود category_id في machines ═════════════════
    if not _column_exists(conn, "machines", "category_id"):
        conn.execute(
            "ALTER TABLE machines ADD COLUMN category_id INTEGER "
            "REFERENCES categories(id) ON DELETE SET NULL"
        )
        conn.commit()

    # ══ 7. عمود child_name في bom ════════════════════════
    if not _column_exists(conn, "bom", "child_name"):
        conn.execute("ALTER TABLE bom ADD COLUMN child_name TEXT")
        conn.commit()
    
    # ══ 8. عمود parent_id في categories ══════════════════════
    if not _column_exists(conn, "categories", "parent_id"):
        conn.execute(
            "ALTER TABLE categories ADD COLUMN parent_id INTEGER "
            "REFERENCES categories(id) ON DELETE SET NULL"
        )
        conn.commit()
    # ══ 9. عمود total_qty في items ══════════════════════
    if not _column_exists(conn, "items", "total_qty"):
        conn.execute("ALTER TABLE items ADD COLUMN total_qty REAL")
        conn.commit()
    create_offers_tables(conn)
    