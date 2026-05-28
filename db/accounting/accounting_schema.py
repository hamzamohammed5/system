"""
db/accounting_schema.py
========================
Facade للتوافق مع الكود القديم — يُعيد تصدير من الملفات المقسّمة:

  accounting_schema_constants.py   → TYPE_AR, EQUITY_TYPES, ...
  accounting_schema_migrations.py  → _fix_is_leaf, run_schema_migrations, ...
  accounting_schema_seed.py        → seed_default_accounts
  accounting_audit_repo.py         → create_audit_log_table [مقترح 52]
"""

# ── الثوابت ──────────────────────────────────────────────
from db.accounting.accounting_schema_constants import (
    TYPE_AR,
    EQUITY_TYPES,
    TYPE_GROUP,
    GROUP_AR,
    NORMAL_BALANCE,
    _VALID_TYPES,
)


# ── Seed ─────────────────────────────────────────────────
from db.accounting.accounting_schema_seed import seed_default_accounts as _seed_default_accounts

# ── Audit Log [مقترح 52] ─────────────────────────────────
from db.accounting.accounting_audit_repo import create_audit_log_table as _create_audit_log_table

# ── DDL الجداول ──────────────────────────────────────────
_ACCOUNTS_DDL = f"""
    CREATE TABLE IF NOT EXISTS accounts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT    NOT NULL UNIQUE,
        name        TEXT    NOT NULL,
        type        TEXT    NOT NULL
            CHECK(type IN {_VALID_TYPES}),
        subtype     TEXT,
        parent_id   INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
        is_leaf     INTEGER NOT NULL DEFAULT 1,
        group_id    INTEGER,
        notes       TEXT,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    );
"""


def create_accounting_tables(conn):
    """يُنشئ الجداول ويُطبّق الـ migrations والبيانات الافتراضية."""
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS account_groups (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT    NOT NULL,
                acc_type  TEXT    NOT NULL,
                parent_id INTEGER REFERENCES account_groups(id) ON DELETE SET NULL,
                color     TEXT    NOT NULL DEFAULT '#607d8b',
                notes     TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"[accounting_schema] account_groups error: {e}")

    try:
        conn.executescript(_ACCOUNTS_DDL)
        conn.commit()
    except Exception as e:
        print(f"[accounting_schema] accounts DDL error: {e}")

    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ref_no      TEXT    NOT NULL UNIQUE,
                date        TEXT    NOT NULL,
                description TEXT    NOT NULL,
                type        TEXT    NOT NULL DEFAULT 'manual'
                    CHECK(type IN (
                        'manual', 'purchase', 'sale',
                        'payment', 'receipt', 'adjustment'
                    )),
                status      TEXT    NOT NULL DEFAULT 'posted'
                    CHECK(status IN ('draft', 'posted', 'reversed')),
                ref_id      INTEGER,
                ref_type    TEXT,
                notes       TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS journal_lines (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id    INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
                account_id  INTEGER NOT NULL REFERENCES accounts(id),
                debit       REAL    NOT NULL DEFAULT 0,
                credit      REAL    NOT NULL DEFAULT 0,
                description TEXT,
                CHECK(debit >= 0 AND credit >= 0),
                CHECK(NOT (debit > 0 AND credit > 0))
            );
        """)
        conn.commit()
    except Exception as e:
        print(f"[accounting_schema] journal tables error: {e}")

    # ── [مقترح 52] إنشاء جدول الـ Audit Log ────────────────
    try:
        _create_audit_log_table(conn)
    except Exception as e:
        print(f"[accounting_schema] audit_log error: {e}")

    try:
        _seed_default_accounts(conn)
    except Exception as e:
        print(f"[accounting_schema] seed error: {e}")