"""
db/designs/migrations_v4.py
============================
Migration لإضافة نظام الـ Instances في مجموعات المقاسات.

التغييرات:
  1. جدول dimension_set_instances — كل instance له اسم + set_id
     (مثال: "مقاس A6"، "مقاس A4" لمجموعة "مقاسات ورق")
  2. عمود instance_id في dimension_set_values بدل الاعتماد على set_id فقط
  3. ترحيل البيانات القديمة → instance تلقائي بدون اسم لكل set
"""


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def run_migrations_v4(conn):
    """تنفيذ migration v4 — نظام الـ instances."""

    # ══ 1. جدول dimension_set_instances ══════════════════
    if not _table_exists(conn, "dimension_set_instances"):
        conn.execute("""
            CREATE TABLE dimension_set_instances (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id     INTEGER NOT NULL
                           REFERENCES dimension_sets(id) ON DELETE CASCADE,
                name       TEXT    NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                notes      TEXT,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

        # ترحيل: كل set عنده قيم → instance واحد بدون اسم
        try:
            sets_with_vals = conn.execute(
                "SELECT DISTINCT set_id FROM dimension_set_values"
            ).fetchall()
            for row in sets_with_vals:
                conn.execute(
                    "INSERT INTO dimension_set_instances (set_id, name, sort_order)"
                    " VALUES (?, '', 0)",
                    (row["set_id"],)
                )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v4] instance migration warning: {e}")

    # ══ 2. عمود instance_id في dimension_set_values ══════
    if not _column_exists(conn, "dimension_set_values", "instance_id"):
        try:
            conn.execute(
                "ALTER TABLE dimension_set_values"
                " ADD COLUMN instance_id INTEGER"
                " REFERENCES dimension_set_instances(id) ON DELETE CASCADE"
            )
            conn.commit()

            # ربط القيم الموجودة بأول instance لكل set
            existing_vals = conn.execute(
                "SELECT id, set_id FROM dimension_set_values WHERE instance_id IS NULL"
            ).fetchall()
            for val in existing_vals:
                inst = conn.execute(
                    "SELECT id FROM dimension_set_instances WHERE set_id=?"
                    " ORDER BY id LIMIT 1",
                    (val["set_id"],)
                ).fetchone()
                if inst:
                    conn.execute(
                        "UPDATE dimension_set_values SET instance_id=? WHERE id=?",
                        (inst["id"], val["id"])
                    )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v4] instance_id column warning: {e}")