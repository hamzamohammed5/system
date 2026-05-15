"""
db/inventory_schema.py
======================
جداول نظام المخزن في inventory.db.

الجداول:
  inventory_categories  — تصنيفات المخزن
  inventory_items       — أصناف المخزن
  inventory_moves       — حركات المخزن (وارد / صادر / تسوية)

الربط مع الحسابات:
  يتم عبر ref_entry_id → يشير لـ journal_entries.id في accounting.db
  (لا نستخدم FOREIGN KEY عبر DBs مختلفة، نتحقق manually)
"""


def create_inventory_tables(conn):
    conn.executescript("""
        -- ══ تصنيفات المخزن ════════════════════════════════════
        CREATE TABLE IF NOT EXISTS inventory_categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT    NOT NULL,
            color TEXT    NOT NULL DEFAULT '#607d8b',
            notes TEXT
        );

        -- ══ أصناف المخزن ══════════════════════════════════════
        CREATE TABLE IF NOT EXISTS inventory_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            unit            TEXT    NOT NULL DEFAULT 'قطعة',
            category_id     INTEGER REFERENCES inventory_categories(id) ON DELETE SET NULL,
            qty_on_hand     REAL    NOT NULL DEFAULT 0,
            qty_min         REAL    NOT NULL DEFAULT 0,       -- حد الطلب
            avg_cost        REAL    NOT NULL DEFAULT 0,       -- متوسط التكلفة (WACC)
            costing_item_id INTEGER,    -- ربط اختياري بـ items في erp.db
            account_code    TEXT    DEFAULT '114',            -- كود حساب المخزون في accounting.db
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ══ حركات المخزن ══════════════════════════════════════
        CREATE TABLE IF NOT EXISTS inventory_moves (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id    INTEGER NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
            move_type       TEXT    NOT NULL
                CHECK(move_type IN (
                    'in',       -- وارد (شراء / إنتاج)
                    'out',      -- صادر (استهلاك / بيع)
                    'adjust'    -- تسوية جرد
                )),
            qty             REAL    NOT NULL,
            unit_cost       REAL    NOT NULL DEFAULT 0,
            total_cost      REAL    NOT NULL DEFAULT 0,
            date            TEXT    NOT NULL,
            ref_entry_id    INTEGER,   -- ID القيد في accounting.db (بدون FK)
            ref_entry_no    TEXT,      -- رقم القيد للعرض
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()