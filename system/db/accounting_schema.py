"""
db/accounting_schema.py (محدَّث)
==================================
جداول نظام الحسابات في accounting.db.

مبادئ المحاسبة:
  Assets = Liabilities + Owner's Equity

الجداول:
  accounts          — شجرة الحسابات (Chart of Accounts)
  journal_entries   — القيود المحاسبية (Journal Entries)
  journal_lines     — سطور كل قيد (مدين / دائن)
"""


def create_accounting_tables(conn):
    conn.executescript("""
        -- ══ شجرة الحسابات ══════════════════════════════════
        CREATE TABLE IF NOT EXISTS accounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,
            name        TEXT    NOT NULL,
            type        TEXT    NOT NULL
                CHECK(type IN (
                    'asset',        -- أصول
                    'liability',    -- خصوم
                    'equity',       -- حقوق ملكية
                    'revenue',      -- إيرادات
                    'expense'       -- مصروفات
                )),
            subtype     TEXT,
            parent_id   INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
            is_leaf     INTEGER NOT NULL DEFAULT 1,
            notes       TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ══ القيود المحاسبية ═════════════════════════════════
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

        -- ══ سطور القيود ══════════════════════════════════════
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

        # ── حقوق الملكية ─────────────────────────────────────
        ("3",    "حقوق الملكية",           "equity",    None,             None),
        ("31",   "رأس المال",              "equity",    "capital",        "3"),
        ("32",   "الأرباح المحتجزة",       "equity",    "retained",       "3"),
        ("33",   "السحوبات",              "equity",    "drawings",       "3"),

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