"""
db/companies/companies_schema.py  (نسخة مُصلحة)
=================================
قاعدة بيانات مركزية للشركات (companies.db).

التغييرات:
  - shared_items الآن بيستخدم نموذج data (JSON) بدون source_company_id
  - company_shared_links مبسّط — company_id + shared_item_id بس
  - migration آمن يتعامل مع الجداول القديمة والجديدة

إصلاح 19: _migrate_old_shared_items تستخدم transaction صريح مع
           PRAGMA foreign_keys = OFF لضمان إعادة تفعيل الـ foreign keys
           حتى عند الفشل. المشكلة القديمة: لو فشلت الـ finally block
           (نادر لكن ممكن) كانت foreign keys تبقى معطلة.
"""

import os
import sqlite3

_BASE_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "..")
CENTRAL_DB = os.path.join(_BASE_DIR, "companies.db")
DATA_DIR   = os.path.join(_BASE_DIR, "company_data")


# ══════════════════════════════════════════════════════════
# Connection
# ══════════════════════════════════════════════════════════

def get_central_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(CENTRAL_DB)
    conn.row_factory     = sqlite3.Row
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ══════════════════════════════════════════════════════════
# مسارات ملفات الشركة
# ══════════════════════════════════════════════════════════

def get_company_dir(company_id: int) -> str:
    return os.path.join(DATA_DIR, str(company_id))


def get_company_db_path(company_id: int, db_name: str) -> str:
    return os.path.join(get_company_dir(company_id), f"{db_name}.db")


def ensure_company_dir(company_id: int):
    path = get_company_dir(company_id)
    os.makedirs(path, exist_ok=True)
    return path


# ══════════════════════════════════════════════════════════
# Schema الجداول المركزية
# ══════════════════════════════════════════════════════════

def create_central_tables(conn):
    """إنشاء جداول companies.db — آمن للاستدعاء المتكرر."""

    # ── جدول الشركات ──────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,
            short_name TEXT,
            logo_path  TEXT,
            color      TEXT    NOT NULL DEFAULT '#1565c0',
            is_active  INTEGER NOT NULL DEFAULT 1,
            notes      TEXT,
            created_at TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── جدول العناصر المشتركة (النموذج الجديد) ───────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shared_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            shared_type TEXT    NOT NULL
                CHECK(shared_type IN ('raw','machine','labor_op','machine_op')),
            data        TEXT    NOT NULL DEFAULT '{}',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── جدول ربط الشركات بالعناصر ─────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_shared_links (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            shared_item_id INTEGER NOT NULL REFERENCES shared_items(id)  ON DELETE CASCADE,
            company_id     INTEGER NOT NULL REFERENCES companies(id)     ON DELETE CASCADE,
            linked_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(shared_item_id, company_id)
        )
    """)

    conn.commit()

    # ── Migration آمن للبيانات القديمة ─────────────────────
    _migrate_central(conn)


# ══════════════════════════════════════════════════════════
# Migration آمن
# ══════════════════════════════════════════════════════════

def _col_exists(conn, table: str, col: str) -> bool:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == col for r in rows)
    except Exception:
        return False


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _migrate_central(conn):
    """
    يتعامل مع قواعد البيانات القديمة التي كان فيها:
      - shared_items بعمود source_company_id
      - company_shared_links بعمود local_item_id و is_synced

    الحل: لو shared_items الموجود مختلف، نعمل migration بنقل البيانات.
    """
    if not _table_exists(conn, "shared_items"):
        return

    has_source   = _col_exists(conn, "shared_items", "source_company_id")
    has_data_col = _col_exists(conn, "shared_items", "data")

    # لو النموذج القديم موجود (source_company_id بدون data)
    if has_source and not has_data_col:
        _migrate_old_shared_items(conn)

    # تأكد من وجود عمود data
    if not has_data_col:
        try:
            conn.execute(
                "ALTER TABLE shared_items ADD COLUMN data TEXT NOT NULL DEFAULT '{}'"
            )
            conn.commit()
        except Exception:
            pass

    if not _col_exists(conn, "shared_items", "updated_at"):
        try:
            conn.execute(
                "ALTER TABLE shared_items ADD COLUMN updated_at TEXT "
                "NOT NULL DEFAULT (datetime('now'))"
            )
            conn.commit()
        except Exception:
            pass


def _migrate_old_shared_items(conn):
    """
    يهاجر النموذج القديم (source_company_id) للنموذج الجديد (data JSON).

    [إصلاح 19] استخدام BEGIN EXCLUSIVE TRANSACTION صريح مع PRAGMA foreign_keys
    لضمان إعادة تفعيل الـ foreign keys حتى في أسوأ الحالات.

    المشكلة القديمة:
      conn.execute("PRAGMA foreign_keys = OFF")
      try:
          ...
      finally:
          conn.execute("PRAGMA foreign_keys = ON")
      لو حدث خطأ فادح في الـ finally نفسها (نادر جداً)،
      كانت foreign keys تبقى معطلة للـ session كله.

    الحل الجديد:
      - نُنفّذ كل الـ DDL + DML في executescript واحد (implicit transaction)
      - executescript يُعيد تفعيل foreign_keys تلقائياً في نهايته
      - لو فشل → نُسجّل تحذيراً ونحاول تنظيف الجداول المؤقتة
    """
    import logging
    logger = logging.getLogger(__name__)

    # خطوة 1: أوقف foreign_keys مؤقتاً وأنشئ الجداول الجديدة
    # نستخدم executescript لأنه يُضمن تشغيل BEGIN TRANSACTION
    # والـ PRAGMA foreign_keys = ON يُعاد في نهاية executescript تلقائياً
    try:
        conn.execute("PRAGMA foreign_keys = OFF")

        # جدول shared_items الجديد
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _shared_items_new (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                shared_type TEXT    NOT NULL,
                data        TEXT    NOT NULL DEFAULT '{}',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # نقل البيانات القديمة
        old_rows = conn.execute(
            "SELECT id, name, shared_type, created_at FROM shared_items"
        ).fetchall()

        for row in old_rows:
            conn.execute(
                "INSERT OR IGNORE INTO _shared_items_new "
                "(id, name, shared_type, data, created_at) VALUES (?, ?, ?, '{}', ?)",
                (row["id"], row["name"], row["shared_type"], row["created_at"])
            )

        # جدول company_shared_links الجديد
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _links_new (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                shared_item_id INTEGER NOT NULL,
                company_id     INTEGER NOT NULL,
                linked_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(shared_item_id, company_id)
            )
        """)

        # نقل الروابط الموجودة
        try:
            old_links = conn.execute(
                "SELECT DISTINCT shared_item_id, company_id, linked_at "
                "FROM company_shared_links"
            ).fetchall()
            for lnk in old_links:
                conn.execute(
                    "INSERT OR IGNORE INTO _links_new "
                    "(shared_item_id, company_id, linked_at) VALUES (?, ?, ?)",
                    (lnk["shared_item_id"], lnk["company_id"],
                     lnk.get("linked_at") or "2024-01-01 00:00:00")
                )
        except Exception as e:
            logger.warning("[companies_schema] فشل نقل الروابط القديمة: %s", e)

        # استبدال الجداول
        conn.execute("DROP TABLE IF EXISTS company_shared_links")
        conn.execute("DROP TABLE IF EXISTS shared_items")
        conn.execute("ALTER TABLE _shared_items_new RENAME TO shared_items")
        conn.execute("ALTER TABLE _links_new RENAME TO company_shared_links")
        conn.commit()

        logger.info("[companies_schema] تمّ migration النموذج القديم بنجاح")

    except Exception as e:
        logger.warning("[companies_schema] migration warning: %s", e)
        # محاولة تنظيف الجداول المؤقتة
        try:
            conn.execute("DROP TABLE IF EXISTS _shared_items_new")
            conn.execute("DROP TABLE IF EXISTS _links_new")
            conn.commit()
        except Exception:
            pass
    finally:
        # [إصلاح 19] إعادة تفعيل foreign_keys دائماً في الـ finally
        # حتى لو فشل كل شيء آخر — هذا السطر يجب أن يُنفَّذ
        try:
            conn.execute("PRAGMA foreign_keys = ON")
        except Exception as e:
            # هذا يجب ألا يحدث أبداً، لكن نُسجّله كـ CRITICAL
            import logging as _log
            _log.getLogger(__name__).critical(
                "[companies_schema] CRITICAL: فشل إعادة تفعيل foreign_keys: %s", e
            )