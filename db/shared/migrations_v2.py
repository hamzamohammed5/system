"""
db/migrations_v2.py
====================
Migrations إضافية للميزات الجديدة:

1. جدول machine_op_rows  — صفوف (sub-rows) لكل عملية تشغيل
   كل عملية ممكن يكون ليها أكثر من صف (قيمة + عدد)
   وضع الحساب (time/unit) يُورث من الماكينة مباشرة

2. جداول bom_scenarios و bom_scenario_rows — سيناريوهات BOM متعددة
   لكل منتج سيناريو واحد أو أكثر، وواحد منهم هو الـ default
"""


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def run_migrations_v2(conn):
    """تنفيذ Migrations الجديدة."""

    # ══ 1. جدول machine_op_rows ══════════════════════════════════
    if not _table_exists(conn, "machine_op_rows"):
        conn.execute("""
            CREATE TABLE machine_op_rows (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                op_id       INTEGER NOT NULL REFERENCES machine_ops(id) ON DELETE CASCADE,
                label       TEXT    NOT NULL DEFAULT '',
                value       REAL    NOT NULL DEFAULT 0,
                count       REAL    NOT NULL DEFAULT 1
                    CHECK(count > 0),
                sort_order  INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

        # ترحيل البيانات الموجودة: كل عملية → صف واحد بنفس value/count=1
        try:
            existing_ops = conn.execute(
                "SELECT id, value FROM machine_ops"
            ).fetchall()
            for op in existing_ops:
                conn.execute(
                    "INSERT INTO machine_op_rows (op_id, label, value, count, sort_order)"
                    " VALUES (?, '', ?, 1, 0)",
                    (op["id"], op["value"])
                )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v2] machine_op_rows migration warning: {e}")

    # ══ 2. عمود machine_op_row_id في bom ════════════════════════
    if not _column_exists(conn, "bom", "machine_op_row_id"):
        try:
            conn.execute(
                "ALTER TABLE bom ADD COLUMN machine_op_row_id INTEGER "
                "REFERENCES machine_op_rows(id) ON DELETE SET NULL"
            )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v2] machine_op_row_id column warning: {e}")

    # ══ 3. جدول bom_scenarios ════════════════════════════════════
    if not _table_exists(conn, "bom_scenarios"):
        conn.execute("""
            CREATE TABLE bom_scenarios (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                name        TEXT    NOT NULL DEFAULT 'سيناريو 1',
                is_default  INTEGER NOT NULL DEFAULT 0,
                notes       TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

        # ترحيل BOM الموجود → سيناريو default لكل منتج
        try:
            products = conn.execute(
                "SELECT DISTINCT parent_id FROM bom"
            ).fetchall()
            for p in products:
                pid = p["parent_id"]
                conn.execute(
                    "INSERT INTO bom_scenarios (item_id, name, is_default) VALUES (?, ?, 1)",
                    (pid, "سيناريو 1")
                )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v2] bom_scenarios migration warning: {e}")

    # ══ 4. عمود scenario_id في bom ══════════════════════════════
    if not _column_exists(conn, "bom", "scenario_id"):
        try:
            conn.execute(
                "ALTER TABLE bom ADD COLUMN scenario_id INTEGER "
                "REFERENCES bom_scenarios(id) ON DELETE CASCADE"
            )
            conn.commit()

            # ربط الصفوف الموجودة بالسيناريو الـ default الخاص بمنتجها
            bom_rows = conn.execute(
                "SELECT id, parent_id FROM bom WHERE scenario_id IS NULL"
            ).fetchall()
            for row in bom_rows:
                sc = conn.execute(
                    "SELECT id FROM bom_scenarios WHERE item_id=? AND is_default=1",
                    (row["parent_id"],)
                ).fetchone()
                if sc:
                    conn.execute(
                        "UPDATE bom SET scenario_id=? WHERE id=?",
                        (sc["id"], row["id"])
                    )
            conn.commit()
        except Exception as e:
            print(f"[migrations_v2] scenario_id column warning: {e}")

    # ══ 5. تأكيد ربط كل BOM rows بسيناريو ══════════════
    try:
        orphan_bom = conn.execute(
            "SELECT DISTINCT parent_id FROM bom WHERE scenario_id IS NULL"
        ).fetchall()
        for p in orphan_bom:
            pid = p["parent_id"]
            sc = conn.execute(
                "SELECT id FROM bom_scenarios WHERE item_id=? AND is_default=1 LIMIT 1",
                (pid,)
            ).fetchone()
            if not sc:
                sc = conn.execute(
                    "SELECT id FROM bom_scenarios WHERE item_id=? ORDER BY id LIMIT 1",
                    (pid,)
                ).fetchone()
            if not sc:
                # أنشئ سيناريو default جديد
                cur = conn.execute(
                    "INSERT INTO bom_scenarios (item_id, name, is_default) VALUES (?, ?, 1)",
                    (pid, "سيناريو 1")
                )
                sc_id = cur.lastrowid
            else:
                sc_id = sc["id"]
            conn.execute(
                "UPDATE bom SET scenario_id=? WHERE parent_id=? AND scenario_id IS NULL",
                (sc_id, pid)
            )
        conn.commit()
    except Exception as e:
        print(f"[migrations_v2] orphan bom fix warning: {e}")
