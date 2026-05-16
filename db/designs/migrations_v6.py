"""
db/designs/migrations_v6.py
============================
Migration لإضافة عمود preview_image في جدول designs.
يخزن مسار صورة المعاينة PNG/JPG الخاصة بكل تصميم.
"""


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def run_migrations_v6(conn):
    """إضافة عمود preview_image لجدول designs."""
    if not _column_exists(conn, "designs", "preview_image"):
        try:
            conn.execute(
                "ALTER TABLE designs ADD COLUMN preview_image TEXT"
            )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v6] preview_image column: {e}")