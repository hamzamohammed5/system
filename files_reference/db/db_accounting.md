# دليل الكود — DB: المحاسبة (db/accounting/) — نسخة محدَّثة

> جداول `accounting.db` — الحسابات، القيود، القوائم المالية، المستثمرون، Audit Log.
> **آخر تحديث:** يعكس الكود الفعلي في السياق — يُستخدم بدلاً من `db_accounting.md`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [accounting_schema.py](#accounting_schemapy) | Facade إنشاء الجداول |
| [accounting_schema_constants.py](#accounting_schema_constantspy) | ثوابت أنواع الحسابات |
| [accounting_schema_seed.py](#accounting_schema_seedpy) | البيانات الافتراضية |
| [accounting_accounts_repo.py](#accounting_accounts_repopy) | CRUD الحسابات والتصنيفات |
| [accounting_journal_repo.py](#accounting_journal_repopy) | CRUD القيود ودفتر الأستاذ |
| [accounting_statements_repo.py](#accounting_statements_repopy) | القوائم المالية |
| [accounting_inventory_repo.py](#accounting_inventory_repopy) | ربط المخزن بالمحاسبة |
| [accounting_audit_repo.py](#accounting_audit_repopy) | Audit Log [مقترح 52] |
| [accounting_repo.py](#accounting_repopy) | Facade للتوافق القديم |
| [accounting_repo_ui_helpers.py](#accounting_repo_ui_helperspy) | دوال مساعدة للـ UI |
| [investors_repo.py](#investors_repopy) | إدارة المستثمرين |

---

## accounting_schema.py

**الملف الفعلي:** Facade يُعيد تصدير من الملفات المقسَّمة. لا يحتوي على `accounting_schema_migrations.py` — الـ migrations مُدمجة في seed و schema نفسه.

```python
create_accounting_tables(conn)
# ينشئ بالترتيب:
#   1. account_groups
#   2. accounts (عبر _ACCOUNTS_DDL)
#   3. journal_entries + journal_lines (executescript)
#   4. audit_log عبر _create_audit_log_table()
#   5. seed_default_accounts()
# كل خطوة في try/except مستقل — فشل خطوة لا يوقف الباقي
```

**الثوابت المُعاد تصديرها من accounting_schema_constants.py:**
```python
TYPE_AR, EQUITY_TYPES, TYPE_GROUP, GROUP_AR, NORMAL_BALANCE, _VALID_TYPES
```

**_ACCOUNTS_DDL (مُعرَّف داخلياً في accounting_schema.py):**
```sql
CREATE TABLE IF NOT EXISTS accounts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    type       TEXT NOT NULL CHECK(type IN ('asset','liability','capital','revenue','expense','drawings')),
    subtype    TEXT,
    parent_id  INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    is_leaf    INTEGER NOT NULL DEFAULT 1,
    group_id   INTEGER,
    notes      TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
```

> ⚠️ `accounting_schema_migrations.py` مذكور في docstring لكنه **غير موجود** كملف مستقل — الـ migrations مُدمجة مباشرة في `create_accounting_tables` و `seed_default_accounts`.

---

## accounting_schema_constants.py

```python
TYPE_AR = {
    "asset": "أصول", "liability": "خصوم", "capital": "رأس المال",
    "revenue": "إيرادات", "expense": "مصروفات", "drawings": "مسحوبات",
}

EQUITY_TYPES = {"capital", "drawings", "revenue", "expense"}

TYPE_GROUP = {
    "asset": "asset", "liability": "liability",
    "capital": "equity", "drawings": "equity",
    "revenue": "equity", "expense": "equity",
}

GROUP_AR = {
    "asset": "الأصول", "liability": "الخصوم", "equity": "حقوق الملكية",
}

NORMAL_BALANCE = {
    "asset": "dr", "expense": "dr", "drawings": "dr",
    "liability": "cr", "capital": "cr", "revenue": "cr",
}

_VALID_TYPES = "('asset','liability','capital','revenue','expense','drawings')"
```

---

## accounting_schema_seed.py

```python
seed_default_accounts(conn)
# يُضيف شجرة الحسابات الافتراضية لو كانت قاعدة البيانات فارغة
# يتحقق بـ _account_exists() + _verify_conn_is_accounting() أولاً

_verify_conn_is_accounting(conn) -> bool
# [إصلاح 9 + 11 + Q-01] ثلاث محاولات للتحقق:
```

**ثلاث محاولات بالترتيب:**

| المحاولة | الأسلوب | الهدف |
|----------|---------|-------|
| 1 | `main.sqlite_master` | أكثر دقة — يتجاهل attached DBs |
| 2 | `sqlite_master` العادي | للـ SQLite القديم |
| 3 | `SELECT 1 FROM accounts/items LIMIT 1` | للـ ProtectedConnection |

المنطق: `has_accounts=True AND has_items=False` = accounting.db فعلاً.

**الحسابات الافتراضية (34 حساب):**

| النطاق | الأكواد |
|--------|---------|
| الأصول (asset) | 1, 11, 111-115, 12, 121-122 |
| الخصوم (liability) | 2, 21, 211-212, 22, 221 |
| حقوق الملكية (capital/drawings) | 3, 31-33 |
| الإيرادات (revenue) | 4, 41-42 |
| المصروفات (expense) | 5, 51-53, 521-524, 531 |

---

## accounting_accounts_repo.py

### القراءة — [P-01] دالتان مقسَّمتان

```python
fetch_all_accounts_basic(conn, acc_type: str = None) -> list
# بدون balance — للـ dropdowns والـ combos (سريعة)
# JOIN: accounts ← accounts(parent) ← account_groups
# الأعمدة: id, code, name, type, subtype, parent_id, is_leaf, group_id,
#           parent_name, group_name, group_color

fetch_all_accounts_with_balance(conn, acc_type: str = None) -> list
# مع balance = COALESCE(SUM(debit)-SUM(credit), 0)
# [تحسين 38] LEFT JOIN journal_lines + GROUP BY — O(1) بدل O(n) correlated subqueries
# GROUP BY يشمل كل الأعمدة في SELECT

fetch_all_accounts(conn, acc_type: str = None) -> list
# للتوافق القديم → يُفوَّض لـ fetch_all_accounts_with_balance()

fetch_account(conn, account_id: int) -> row | None
# مع parent_name, group_name, group_color من JOIN

fetch_account_by_code(conn, code: str) -> row | None
# SELECT * FROM accounts WHERE code=?

fetch_leaf_accounts(conn, acc_type: str = None) -> list
# is_leaf=1 — للاختيار في القيود
# الأعمدة: id, code, name, type, subtype, group_id
```

### الكتابة

```python
insert_account(conn, code, name, acc_type, parent_id=None,
               group_id=None, subtype=None, notes=None) -> int
# لو parent_id محدد → UPDATE accounts SET is_leaf=0 على الأب تلقائياً

update_account(conn, account_id, name, group_id=None, notes=None)
# لا يُغيّر code أو type أو parent_id

delete_account(conn, account_id)
# CASCADE على الأبناء
```

### الأرصدة

```python
get_account_balance(conn, account_id: int) -> float
# COALESCE(SUM(debit)-SUM(credit), 0)

get_account_natural_balance(conn, account_id: int) -> float
# bal إذا normal_balance="dr"، أو -bal إذا "cr"

get_normal_balance(acc_type: str) -> str
# "dr" ← asset/expense/drawings
# "cr" ← liability/capital/revenue

calc_signed_amount(acc_type: str, increase: bool, amount: float) -> tuple[float, float]
# يرجع (debit, credit) حسب نوع الحساب وهل يزيد أم يقل

get_balances_by_type(conn) -> dict
# {type: {"debit": float, "credit": float, "balance": float}}
```

### تصنيفات الحسابات (account_groups)

```python
fetch_all_groups(conn, acc_type: str = None) -> list
# مُرتَّبة بـ _sort_groups_parents_first() — الأب قبل أبنائه دائماً
# الأعمدة: id, name, acc_type, parent_id, color, notes

fetch_group(conn, group_id: int) -> row
insert_group(conn, name, acc_type, parent_id=None, color="#607d8b") -> int
update_group(conn, group_id, name, parent_id=None, color="#607d8b")

delete_group(conn, group_id)
# يُعيد ضبط group_id=NULL في accounts أولاً

build_group_tree(rows) -> list
# [{id, name, acc_type, parent_id, color, children: [...]}, ...]
# [تحسين 3] id_map يُشير لنفس dict objects (O(n) بدل O(3n))

_sort_groups_parents_first(rows) -> list
# [تحسين 3] DFS visit() — O(n) dicts بدل O(3n)

_get_group_descendants(conn, group_id: int) -> set
# PRIVATE — لا تستورد من accounting_repo.py (محذوفة من الـ facade)
# استورد مباشرة: from db.accounting.accounting_accounts_repo import _get_group_descendants
```

---

## accounting_journal_repo.py

### رقم القيد التلقائي

```python
next_ref_no(conn) -> str
# "JE-00001", "JE-00002", ...
# MAX(CAST(SUBSTR(ref_no,4) AS INTEGER)) + 1
# يبدأ من 1 عند أي exception
```

### القراءة

```python
fetch_all_entries(conn, limit: int = 200) -> list
# آخر القيود بـ ORDER BY date DESC, id DESC LIMIT ?
# كل row: id, ref_no, date, description, type, status, notes, created_at,
#          total_debit (correlated subquery), total_credit (correlated subquery)
# [إصلاح 29] استخدم fetch_entries_count() لمعرفة الإجمالي قبل العرض

fetch_entries_count(conn) -> int
# [إصلاح 29] SELECT COUNT(*) — للـ UI pagination
# مثال: "يعرض 200 من أصل 1500 قيد"

fetch_all_entries_paginated(conn, limit=200, offset=0,
                             date_from=None, date_to=None,
                             search=None, entry_type=None) -> list
# [إصلاح 29] pagination + فلترة ديناميكية آمنة (parameterized)
# search: LIKE %search% على ref_no OR description
# entry_type: فلتر نوع القيد

fetch_entry(conn, entry_id: int) -> row | None
# SELECT * FROM journal_entries WHERE id=?

fetch_entry_lines(conn, entry_id: int) -> list
# مع account_code, account_name, account_type من JOIN accounts
# ORDER BY jl.id
```

### الكتابة

```python
insert_entry(conn, date, description, entry_type="manual",
             notes=None, ref_id=None, ref_type=None) -> int
# يولد ref_no تلقائياً | status="posted" دائماً

add_entry_lines(conn, entry_id: int, lines: list)
# lines: [{"account_id", "debit"?, "credit"?, "description"?}, ...]
# debit/credit افتراضياً 0

delete_entry(conn, entry_id: int, changed_by: str = "system")
# [مقترح 52] snapshot أولاً في audit_log ثم الحذف:
#   1. snapshot_journal_entry(conn, entry_id) → old_data
#   2. log_delete(conn, "journal_entries", entry_id, old_data, changed_by)
#   3. DELETE FROM journal_entries WHERE id=?
#   4. commit
# فشل audit لا يوقف الحذف (try/except + logging.warning)

validate_entry_balance(lines: list) -> bool
# abs(total_debit - total_credit) < 0.001
```

### دفتر الأستاذ (T-Account)

```python
fetch_t_account(conn, account_id: int) -> dict
# {
#   "account": dict(acc),
#   "lines": [{"id","debit","credit","description","ref_no","date","entry_desc"}, ...],
#   "total_debit": float,
#   "total_credit": float,
#   "balance": float,         # total_debit - total_credit
#   "normal_balance": "dr"|"cr"
# }
# يرجع {} لو الحساب غير موجود
```

---

## accounting_statements_repo.py

جميع الدوال تستخدم `is_leaf=1` لتجنب الحسابات التجميعية.

```python
trial_balance(conn) -> list
# كل leaf accounts مع total_debit, total_credit, balance
# balance = total_debit - total_credit
# [{"code","name","type","total_debit","total_credit","balance"}, ...]

income_statement(conn) -> dict
# {
#   "revenues": [{"code","name","amount"}, ...],  # SUM(credit)-SUM(debit)
#   "expenses": [{"code","name","amount"}, ...],  # SUM(debit)-SUM(credit)
#   "total_rev": float,
#   "total_exp": float,
#   "net_income": float   # total_rev - total_exp
# }

balance_sheet(conn) -> dict
# {
#   "assets": [...], "liabilities": [...],
#   "capital": [...], "drawings": [...],
#   "net_income": float,
#   "total_assets": float, "total_liab": float, "total_equity": float
# }
# total_equity = total_capital - total_drawings + net_income
# يستدعي income_statement() داخلياً

owners_equity_statement(conn) -> dict
# {
#   "capital_accounts": [...], "drawings_accounts": [...],
#   "net_income": float,
#   "total_capital": float, "total_drawings": float, "total_equity": float
# }
# يستدعي income_statement() داخلياً

# ملاحظة: assets في balance_sheet تستخدم SUM(debit)-SUM(credit)
# بينما liabilities/capital تستخدم نفس الصيغة — تحقق من الإشارات عند العرض
```

---

## accounting_inventory_repo.py

```python
purchase_inventory(inv_conn, acc_conn,
                   inv_id: int, qty: float, unit_cost: float,
                   date: str, payment_account_id: int,
                   notes: str = None,
                   changed_by: str = "system") -> tuple[int, int]
# يرجع (entry_id, move_id)
```

**التحقق من المدخلات (يرمي ValueError):**
- `qty <= 0`
- `unit_cost < 0`
- الصنف غير موجود في inv_conn
- حساب المخزون غير موجود (يُجرب account_code ثم subtype='inventory')
- `payment_account_id` فارغ أو None

**منطق البحث عن حساب المخزون:**
```python
# 1. inv.get("account_code") or "114"
# 2. fetch_account_by_code(acc_conn, acc_code)
# 3. Fallback: SELECT id FROM accounts WHERE subtype='inventory' AND is_leaf=1 LIMIT 1
# 4. لو كل شيء فشل → ValueError
```

**المرحلتان:**
```
المرحلة 1: القيد المحاسبي (acc_conn)
  INSERT journal_entry (type="purchase", status="posted")
  INSERT journal_lines:
    DR: inv_acc_id  = total_cost
    CR: payment_acc = total_cost

المرحلة 2: حركة المخزون (inv_conn)
  record_inventory_move(inv_conn, inv_id, "in", qty, unit_cost, date, ...)
```

**[إصلاح 32] Rollback محصَّن:**

```python
# لو فشلت المرحلة 2:
try:
    _audit_rollback(acc_conn, entry_id, reason=str(inv_err), changed_by)
    DELETE FROM journal_entries WHERE id=entry_id
    acc_conn.commit()
    rollback_ok = True
    → raise RuntimeError("فشل تسجيل المخزون — تم إلغاء القيد تلقائياً")

except Exception as rb_err:
    _audit_critical_inconsistency(...)
    logger.critical("CRITICAL DATA INCONSISTENCY: ...")
    → raise RuntimeError(f"القيد {entry_id} يحتاج مراجعة يدوية")
```

**دوال مساعدة للـ Audit [مقترح 52]:**

```python
_audit_rollback(acc_conn, entry_id, reason, changed_by)
# snapshot_journal_entry → log_action("delete") → الفشل لا يوقف rollback

_audit_critical_inconsistency(acc_conn, entry_id, inv_err, rb_err,
                               inv_id, qty, unit_cost, date, changed_by)
# old_data["status"] = "CRITICAL_INCONSISTENCY"
# changed_by = f"{changed_by}:CRITICAL_ROLLBACK_FAIL"
```

---

## accounting_audit_repo.py

### DDL

```python
AUDIT_LOG_DDL = """
    CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        action      TEXT NOT NULL CHECK(action IN ('delete','update','create')),
        table_name  TEXT NOT NULL,
        record_id   INTEGER,
        old_data    TEXT,
        changed_by  TEXT NOT NULL DEFAULT 'system',
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
"""

create_audit_log_table(conn)
# executescript(AUDIT_LOG_DDL) + commit
# try/except مع logger.warning عند الفشل
```

### الكتابة

```python
log_action(conn, action, table_name, record_id=None,
           old_data=None, changed_by="system") -> int | None
# action: "delete" | "update" | "create"
# old_data: None → NULL | str → كما هو | dict/list → json.dumps(ensure_ascii=False)
# فشل INSERT → logger.warning → يرجع None (لا يوقف العملية)
# يرجع lastrowid عند النجاح

log_delete(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_update(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_create(conn, table_name, record_id, data=None, changed_by="system") -> int | None
```

### Snapshots

```python
snapshot_journal_entry(conn, entry_id: int) -> dict | None
# {"entry": dict(row), "lines": [dict(l) for l in lines]}
# lines مع account_code, account_name من JOIN
# يرجع None لو القيد غير موجود أو exception

snapshot_account(conn, account_id: int) -> dict | None
# dict(row) أو None

snapshot_row(conn, table: str, record_id: int, id_col: str = "id") -> dict | None
# snapshot عام لأي جدول بسيط — f"SELECT * FROM {table} WHERE {id_col}=?"
```

### القراءة

```python
fetch_audit_log(conn, table_name=None, action=None,
                limit=200, offset=0) -> list
# كل dict يحتوي "old_data_parsed" (JSON parsed) إضافةً إلى "old_data" النصي
# ORDER BY id DESC

fetch_audit_log_count(conn, table_name=None, action=None) -> int
# للـ pagination

fetch_record_history(conn, table_name: str, record_id: int) -> list
# تاريخ سجل معين — ORDER BY id DESC
```

---

## accounting_repo.py

**Facade للتوافق القديم** — يُعيد تصدير كل الدوال.

```python
# الاستيراد الصحيح للكود الجديد:
from db.accounting.accounting_repo import (
    fetch_all_accounts_basic,        # [P-01] جديدة
    fetch_all_accounts_with_balance, # [P-01] جديدة
    fetch_all_accounts,              # للتوافق القديم
    fetch_entries_count,             # [إصلاح 29] جديدة
    fetch_all_entries_paginated,     # [إصلاح 29] جديدة
    trial_balance, income_statement, balance_sheet, owners_equity_statement,
    purchase_inventory,
    log_action, log_delete, log_update, log_create,
    snapshot_journal_entry, snapshot_account, snapshot_row,
    fetch_audit_log, fetch_audit_log_count, fetch_record_history,
    # ... إلخ
)
```

> ⚠️ `_get_group_descendants` **محذوفة** من الـ facade [تحسين 14].
> استورد مباشرة: `from db.accounting.accounting_accounts_repo import _get_group_descendants`

---

## accounting_repo_ui_helpers.py

دوال نُقلت من الـ UI widgets إلى DB layer لفصل المنطق.

```python
fetch_account_by_code(conn, code: str) -> row | None
# SELECT id FROM accounts WHERE code=?

fetch_capital_line_for_entry(conn, entry_id: int) -> int
# أول سطر دائن (credit > 0) في القيد → id أو 0

fetch_drawings_line_for_entry(conn, entry_id: int) -> int
# أول سطر مدين (debit > 0) في القيد → id أو 0

fetch_entry_by_ref(conn, ref_no: str) -> row | None
# SELECT id FROM journal_entries WHERE ref_no=?

fetch_investor_entry_id(erp_conn, link_id: int) -> int | None
# يستقبل erp_conn (ليس acc_conn) — investor_entries في erp.db
# SELECT entry_id FROM investor_entries WHERE id=?
```

> ⚠️ كل الدوال تُعيد `None` أو `0` عند الفشل — لا ترمي exceptions.

---

## investors_repo.py

### Cache الـ Migration — [إصلاح 31] + [تحسين 7]

```python
_investors_migrated: set[str]   # مجموعة db_paths التي تمّ migration عليها

_get_db_path(conn) -> str
# Fast path (O(1)) — ProtectedConnection:
#   object.__getattribute__(conn, '_path') → يتجاوز __getattr__ proxy
#
# Slow path — sqlite3.Connection العادي:
#   PRAGMA database_list → row[2]
#   Fallback: str(id(conn))

_migrate_investors(conn)
# [إصلاح 31] يُنفَّذ مرة واحدة per-db-path:
#   1. _get_db_path → لو في _investors_migrated → return فوراً
#   2. لو investors غير موجود → create_investors_tables → return
#   3. يتحقق من sql investor_entries:
#      لو "REFERENCES journal_" موجود في SQL:
#        PRAGMA FK=OFF → إنشاء جديد → نقل بيانات → DROP → RENAME → PRAGMA FK=ON
#   4. إضافة path لـ _investors_migrated

invalidate_investors_migration_cache(conn=None)
# conn=None → clear كامل | conn=<conn> → discard path محدد
```

### إنشاء الجداول

```python
create_investors_tables(conn)
# investors: id, name UNIQUE, notes, joined_at, created_at
# investor_entries: id, investor_id→CASCADE, entry_id, line_id,
#                   move_type CHECK("capital"|"drawings"), amount, notes, created_at
# ملاحظة مهمة: investor_entries لا تحتوي REFERENCES لـ journal_entries
#   (لأنهما في DBs مختلفة — تم إزالتها في migration)
```

### CRUD — المستثمرون

```python
fetch_all_investors(conn) -> list
fetch_investor(conn, investor_id: int) -> row
insert_investor(conn, name, notes=None, joined_at=None) -> int
# joined_at افتراضياً = today (YYYY-MM-DD)
update_investor(conn, investor_id, name, notes=None, joined_at=None)
delete_investor(conn, investor_id)
investor_exists(conn, name: str) -> int | None
# يرجع investor_id أو None
```

> ⚠️ كل دوال الـ CRUD تستدعي `_migrate_investors(conn)` أولاً.

### ربط المستثمر بالقيود

```python
link_investor_to_line(conn, investor_id, entry_id, line_id,
                       move_type, amount, notes=None) -> int
# move_type: "capital" | "drawings"

fetch_investor_entries(conn, investor_id: int, acc_conn=None) -> list[dict]
# لو acc_conn متاح → يجلب ref_no, date, account_code من accounting.db
# كل entry dict:
# {id, move_type, amount, notes, created_at,
#  ref_no, date, entry_desc,
#  debit, credit, line_desc,
#  account_code, account_name, account_type}
# بدون acc_conn: ref_no=f"Entry#{entry_id}", date="—", account_code="—"

fetch_entry_investor_links(conn, entry_id: int) -> list
# مع investor_name من JOIN

delete_investor_link(conn, link_id: int)
delete_entry_investor_links(conn, entry_id: int)
```

### تقارير المستثمرين — [إصلاح 40]

```python
calc_investor_summary(conn, investor_id: int, acc_conn=None) -> dict
# {investor_id, investor_name, joined_at, notes,
#  total_capital, total_drawings, net_investment, entries}

calc_all_investors_summary(conn, acc_conn=None) -> list
# [إصلاح 40] O(1)+O(entries) بدل O(n×m):
#   1. جلب كل investor_entries دفعة واحدة
#   2. تجميع بـ defaultdict(list) حسب investor_id
#   3. لو acc_conn: batch queries لـ journal_entries و journal_lines
#      (placeholders ديناميكية: "?" * len(ids))
#   4. بناء النتائج من je_cache و jl_cache
#   النتائج مُرتَّبة بـ net_investment DESC
```

---

## جداول accounting.db (كاملة)

| الجدول | الأعمدة الرئيسية | ملاحظات |
|--------|-----------------|---------|
| `account_groups` | id, name, acc_type, parent_id→SET NULL, color, notes | تصنيفات الحسابات |
| `accounts` | id, code UNIQUE, name, type(6 أنواع), subtype, parent_id→CASCADE, is_leaf=1, group_id, notes | شجرة الحسابات |
| `journal_entries` | id, ref_no UNIQUE, date, description, type(6 أنواع), status(3 حالات), ref_id, ref_type, notes | القيود |
| `journal_lines` | id, entry_id→CASCADE, account_id→accounts, debit≥0, credit≥0 | سطور القيود |
| `audit_log` | id, action(delete/update/create), table_name, record_id, old_data TEXT, changed_by, created_at | سجل التدقيق |
| `investors` | id, name UNIQUE, notes, joined_at, created_at | المستثمرون |
| `investor_entries` | id, investor_id→CASCADE, entry_id, line_id, move_type(capital/drawings), amount, notes | حركات المستثمرين |

**قيود journal_lines:**
```sql
CHECK(debit >= 0 AND credit >= 0)
CHECK(NOT (debit > 0 AND credit > 0))
```

**أنواع القيود:** `manual | purchase | sale | payment | receipt | adjustment`
**حالات القيود:** `draft | posted | reversed`

---

## ملاحظات مهمة

- `accounting.db` منفصل تماماً عن `erp.db` — لا FOREIGN KEYS بينهما.
- `purchase_inventory` يحتاج **connection-ين** منفصلين: `inv_conn` لـ inventory.db و `acc_conn` لـ accounting.db.
- `fetch_all_accounts_basic` للـ dropdowns | `fetch_all_accounts_with_balance` للتقارير [P-01].
- `delete_entry` يُسجَّل snapshot في audit_log قبل الحذف تلقائياً [مقترح 52].
- `calc_all_investors_summary` يجلب كل entries دفعة واحدة [إصلاح 40].
- `_migrate_investors` تُنفَّذ مرة واحدة per-path بفضل `_investors_migrated` set [إصلاح 31].
- `_get_db_path` fast path O(1) لـ ProtectedConnection عبر `object.__getattribute__` [تحسين 7].
- `_get_group_descendants` **private** — استورد مباشرة من `accounting_accounts_repo`.
- `accounting_schema_migrations.py` **غير موجود** كملف مستقل — الـ migrations مُدمجة.