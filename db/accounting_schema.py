"""
db/accounting_schema.py (إصلاح مشكلة CHECK constraint)
==================================
المشكلة: جدول accounts موجود بـ CHECK constraint قديم يقبل فقط:
  'asset', 'liability', 'equity', 'revenue', 'expense'

الكود الجديد بيضيف أنواع: 'capital', 'drawings'
→ SQLite يرفضها بـ IntegrityError

الحل: migration يعيد بناء الجدول بالـ constraint الجديد بشكل آمن.
"""

TYPE_AR = {
    "asset":     "أصول",
    "liability": "خصوم",
    "capital":   "رأس المال",
    "revenue":   "إيرادات",
    "expense":   "مصروفات",
    "drawings":  "مسحوبات",
}

NORMAL_BALANCE = {
    "asset":     "dr",
    "expense":   "dr",
    "drawings":  "dr",
    "liability": "cr",
    "capital":   "cr",
    "revenue":   "cr",
}

_VALID_TYPES = "('asset','liability','capital','revenue','expense','drawings')"

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


def _get_current_type_constraint(conn) -> str:
    """يرجع الـ CHECK constraint الموجود في جدول accounts."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts'"
    ).fetchone()
    return row["sql"] if row else ""


def _needs_migration(conn) -> bool:
    """يشيك لو الجدول محتاج migration (مش بيقبل الأنواع الجديدة)."""
    current_sql = _get_current_type_constraint(conn)
    if not current_sql:
        return False  # الجدول مش موجود أصلاً
    # لو 'capital' مش موجود في الـ constraint، محتاجين migration
    return "'capital'" not in current_sql


def _migrate_accounts_type_constraint(conn):
    """
    يعيد بناء جدول accounts بـ CHECK constraint جديد يقبل capital و drawings.
    يحافظ على كل البيانات مع تحويل 'equity' → 'capital'.
    """
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        # 1. جدول مؤقت بالـ constraint الجديد
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

        # 2. نقل البيانات مع تحويل 'equity' → 'capital'
        #    (لو عندك بيانات قديمة type='equity')
        #
        #    نتحقق أول لو عمود group_id موجود في الجدول القديم
        old_cols = {r["name"] for r in conn.execute("PRAGMA table_info(accounts)").fetchall()}
        if "group_id" in old_cols:
            conn.execute(f"""
                INSERT INTO _accounts_new
                    (id, code, name, type, subtype, parent_id, is_leaf, group_id, notes, created_at)
                SELECT
                    id, code, name,
                    CASE type
                        WHEN 'equity' THEN 'capital'
                        ELSE type
                    END,
                    subtype, parent_id, is_leaf,
                    group_id,
                    notes, created_at
                FROM accounts
            """)
        else:
            conn.execute(f"""
                INSERT INTO _accounts_new
                    (id, code, name, type, subtype, parent_id, is_leaf, notes, created_at)
                SELECT
                    id, code, name,
                    CASE type
                        WHEN 'equity' THEN 'capital'
                        ELSE type
                    END,
                    subtype, parent_id, is_leaf,
                    notes, created_at
                FROM accounts
            """)

        # 3. احذف القديم وعيد التسمية
        conn.execute("DROP TABLE accounts")
        conn.execute("ALTER TABLE _accounts_new RENAME TO accounts")
        conn.commit()

    except Exception:
        conn.rollback()
        # احذف الجدول المؤقت لو موجود
        try:
            conn.execute("DROP TABLE IF EXISTS _accounts_new")
            conn.commit()
        except Exception:
            pass
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _column_exists(conn, table: str, col: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == col for r in rows)


def _migrate_schema(conn):
    # ── أولاً: إصلاح CHECK constraint ──
    if _needs_migration(conn):
        _migrate_accounts_type_constraint(conn)

    # ── ثانياً: إضافة group_id لو ناقص ──
    if not _column_exists(conn, "accounts", "group_id"):
        conn.execute("ALTER TABLE accounts ADD COLUMN group_id INTEGER")
        conn.commit()

    # ── ثالثاً: إضافة notes لجدول account_groups لو ناقص ──
    if not _column_exists(conn, "account_groups", "notes"):
        conn.execute("ALTER TABLE account_groups ADD COLUMN notes TEXT")
        conn.commit()


def create_accounting_tables(conn):
    """يُستدعى من init_db — ينشئ الجداول ويشغّل الـ migrations."""

    # ── جداول groups (تصنيفات الحسابات) ──
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

    # ── جدول accounts — أنشئه لو مش موجود ──
    conn.executescript(_ACCOUNTS_DDL)
    conn.commit()

    # ── جداول القيود ──
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

    # ── شغّل migrations ──
    _migrate_schema(conn)

    # ── بذر الحسابات الافتراضية ──
    _seed_default_accounts(conn)


def _account_exists(conn) -> bool:
    row = conn.execute("SELECT COUNT(*) as c FROM accounts").fetchone()
    return row["c"] > 0


def _seed_default_accounts(conn):
    """يضيف الحسابات الافتراضية لو الجدول فاضي."""
    if _account_exists(conn):
        return

    accounts = [
        # ── أصول ────────────────────────────────────────────
        ("1",    "الأصول",                "asset",     None,             None),
        ("11",   "الأصول المتداولة",       "asset",     "current_asset",  "1"),
        ("111",  "الصندوق",               "asset",     "cash",           "11"),
        ("112",  "البنك",                 "asset",     "bank",           "11"),
        ("113",  "العملاء / ذمم مدينة",   "asset",     "receivable",     "11"),
        ("114",  "المخزون",               "asset",     "inventory",      "11"),
        ("115",  "مصروفات مقدمة",         "asset",     "prepaid",        "11"),
        ("12",   "الأصول الثابتة",         "asset",     "fixed_asset",    "1"),
        ("121",  "المعدات والآلات",        "asset",     "equipment",      "12"),
        ("122",  "مجمع الاستهلاك",        "asset",     "depreciation",   "12"),

        # ── خصوم ────────────────────────────────────────────
        ("2",    "الخصوم",                "liability", None,             None),
        ("21",   "الخصوم المتداولة",       "liability", "current",        "2"),
        ("211",  "الموردون / ذمم دائنة",  "liability", "payable",        "21"),
        ("212",  "مصروفات مستحقة",        "liability", "accrued",        "21"),
        ("22",   "الخصوم طويلة الأجل",    "liability", "long_term",      "2"),
        ("221",  "قروض طويلة الأجل",      "liability", "loan",           "22"),

        # ── حقوق الملكية (capital بدل equity) ───────────────
        ("3",    "حقوق الملكية",           "capital",   None,             None),
        ("31",   "رأس المال",              "capital",   "capital",        "3"),
        ("32",   "الأرباح المحتجزة",       "capital",   "retained",       "3"),
        ("33",   "السحوبات",              "drawings",  "drawings",       "3"),

        # ── إيرادات ─────────────────────────────────────────
        ("4",    "الإيرادات",              "revenue",   None,             None),
        ("41",   "إيرادات المبيعات",       "revenue",   "sales",          "4"),
        ("42",   "إيرادات أخرى",          "revenue",   "other",          "4"),

        # ── مصروفات ─────────────────────────────────────────
        ("5",    "المصروفات",              "expense",   None,             None),
        ("51",   "تكلفة البضاعة المباعة",  "expense",   "cogs",           "5"),
        ("52",   "مصروفات تشغيلية",       "expense",   "operating",      "5"),
        ("521",  "رواتب وأجور",           "expense",   "salaries",       "52"),
        ("522",  "إيجار",                 "expense",   "rent",           "52"),
        ("523",  "مرافق (كهرباء/مياه)",   "expense",   "utilities",      "52"),
        ("524",  "مصروفات نثرية",         "expense",   "misc",           "52"),
        ("53",   "مصروفات تمويلية",       "expense",   "financial",      "5"),
        ("531",  "فوائد بنكية",           "expense",   "interest",       "53"),
    ]

    for code, name, acc_type, subtype, parent_code in accounts:
        parent_id = None
        if parent_code:
            row = conn.execute(
                "SELECT id FROM accounts WHERE code=?", (parent_code,)
            ).fetchone()
            if row:
                parent_id = row["id"]
                conn.execute(
                    "UPDATE accounts SET is_leaf=0 WHERE id=?", (parent_id,)
                )

        is_leaf = 0 if len(code) <= 2 else 1

        conn.execute("""
            INSERT OR IGNORE INTO accounts
                (code, name, type, subtype, parent_id, is_leaf)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, name, acc_type, subtype, parent_id, is_leaf))

    conn.commit()