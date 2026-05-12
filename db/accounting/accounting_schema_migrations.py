"""
db/accounting/accounting_schema_migrations.py
====================================
Migration helpers لقاعدة بيانات الحسابات.
"""

from db.accounting.accounting_schema_constants import _VALID_TYPES


# ══════════════════════════════════════════════════════════
# فحص الـ Schema
# ══════════════════════════════════════════════════════════

def _get_current_type_constraint(conn) -> str:
    try:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts'"
        ).fetchone()
        return row["sql"] if row else ""
    except Exception:
        return ""


def _needs_migration(conn) -> bool:
    current_sql = _get_current_type_constraint(conn)
    if not current_sql:
        return False
    return "'capital'" not in current_sql


def _column_exists(conn, table: str, col: str) -> bool:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == col for r in rows)
    except Exception:
        return False


def _table_exists(conn, table: str) -> bool:
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        return row is not None
    except Exception:
        return False


# ══════════════════════════════════════════════════════════
# Migrations
# ══════════════════════════════════════════════════════════

def _migrate_accounts_type_constraint(conn):
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute(f"""
            CREATE TABLE _accounts_new (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT    NOT NULL UNIQUE,
                name        TEXT    NOT NULL,
                type        TEXT    NOT NULL
                    CHECK(type IN {_VALID_TYPES}),
                subtype     TEXT,
                parent_id   INTEGER REFERENCES _accounts_new(id) ON DELETE CASCADE,
                is_leaf     INTEGER NOT NULL DEFAULT 1,
                group_id    INTEGER,
                notes       TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        old_cols = {r["name"] for r in conn.execute("PRAGMA table_info(accounts)").fetchall()}
        if "group_id" in old_cols:
            conn.execute(f"""
                INSERT INTO _accounts_new
                    (id, code, name, type, subtype, parent_id, is_leaf, group_id, notes, created_at)
                SELECT id, code, name,
                    CASE type WHEN 'equity' THEN 'capital' ELSE type END,
                    subtype, parent_id, is_leaf, group_id, notes, created_at
                FROM accounts
            """)
        else:
            conn.execute(f"""
                INSERT INTO _accounts_new
                    (id, code, name, type, subtype, parent_id, is_leaf, notes, created_at)
                SELECT id, code, name,
                    CASE type WHEN 'equity' THEN 'capital' ELSE type END,
                    subtype, parent_id, is_leaf, notes, created_at
                FROM accounts
            """)
        conn.execute("DROP TABLE accounts")
        conn.execute("ALTER TABLE _accounts_new RENAME TO accounts")
        conn.commit()
    except Exception:
        conn.rollback()
        try:
            conn.execute("DROP TABLE IF EXISTS _accounts_new")
            conn.commit()
        except Exception:
            pass
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _fix_is_leaf(conn):
    try:
        conn.execute("""
            UPDATE accounts SET is_leaf = 0
            WHERE id IN (
                SELECT DISTINCT parent_id FROM accounts WHERE parent_id IS NOT NULL
            )
        """)
        conn.execute("""
            UPDATE accounts SET is_leaf = 1
            WHERE id NOT IN (
                SELECT DISTINCT parent_id FROM accounts WHERE parent_id IS NOT NULL
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"[accounting_schema_migrations] _fix_is_leaf error: {e}")


def run_schema_migrations(conn):
    """تُطبّق كل الـ migrations المطلوبة بأمان."""
    if _needs_migration(conn):
        try:
            _migrate_accounts_type_constraint(conn)
        except Exception as e:
            print(f"[accounting_schema_migrations] migration warning: {e}")

    if not _column_exists(conn, "accounts", "group_id"):
        try:
            conn.execute("ALTER TABLE accounts ADD COLUMN group_id INTEGER")
            conn.commit()
        except Exception:
            pass

    if not _column_exists(conn, "account_groups", "notes"):
        try:
            conn.execute("ALTER TABLE account_groups ADD COLUMN notes TEXT")
            conn.commit()
        except Exception:
            pass

    if not _table_exists(conn, "entry_templates"):
        try:
            conn.execute("""
                CREATE TABLE entry_templates (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL,
                    account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    description TEXT,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        except Exception:
            pass

    if not _table_exists(conn, "sub_account_ledger"):
        try:
            conn.execute("""
                CREATE TABLE sub_account_ledger (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    person_name TEXT    NOT NULL,
                    move_type   TEXT    NOT NULL CHECK(move_type IN ('in','out')),
                    amount      REAL    NOT NULL DEFAULT 0,
                    notes       TEXT,
                    date        TEXT    NOT NULL,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        except Exception:
            pass