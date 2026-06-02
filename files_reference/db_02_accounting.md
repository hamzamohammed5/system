# دليل الكود — DB: المحاسبة (db/accounting/)

> جداول `accounting.db` — الحسابات، القيود، القوائم المالية، المستثمرون، Audit Log.
> **آخر تحديث:** يعكس الكود الفعلي في السياق بالكامل.

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
| [accounting_audit_repo.py](#accounting_audit_repopy) | Audit Log |
| [accounting_repo.py](#accounting_repopy) | Facade للتوافق القديم |
| [accounting_repo_ui_helpers.py](#accounting_repo_ui_helperspy) | دوال مساعدة للـ UI |
| [investors_repo.py](#investors_repopy) | إدارة المستثمرين |

---

## accounting_schema.py

Facade يُعيد تصدير من الملفات المقسّمة:
- `accounting_schema_constants.py` — الثوابت
- `accounting_schema_seed.py` — البيانات الافتراضية
- `accounting_audit_repo.py` — Audit Log [مقترح 52]

```python
create_accounting_tables(conn)
# ينشئ: account_groups, accounts, journal_entries, journal_lines, audit_log
# ثم يُطبّق _create_audit_log_table + seed_default_accounts
# كل خطوة محاطة بـ try/except مستقل — الفشل لا يوقف الخطوات الأخرى
```

**جداول accounting.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `account_groups` | `id, name, acc_type, parent_id→SET NULL, color DEFAULT "#607d8b", notes` |
| `accounts` | `id, code UNIQUE, name, type CHECK(6 types), subtype, parent_id→CASCADE, is_leaf DEFAULT 1, group_id, notes` |
| `journal_entries` | `id, ref_no UNIQUE, date, description, type DEFAULT "manual", status DEFAULT "posted", ref_id, ref_type, notes` |
| `journal_lines` | `id, entry_id→CASCADE, account_id→accounts, debit DEFAULT 0, credit DEFAULT 0, description` |
| `audit_log` | `id, action CHECK("delete"\|"update"\|"create"), table_name, record_id, old_data TEXT, changed_by DEFAULT "system", created_at` |
| `investors` | `id, name UNIQUE, notes, joined_at DEFAULT date("now"), created_at` |
| `investor_entries` | `id, investor_id→CASCADE, entry_id, line_id, move_type CHECK("capital"\|"drawings"), amount DEFAULT 0, notes` |

**أنواع الحسابات (`type`):** `asset | liability | capital | revenue | expense | drawings`

**أنواع القيود (`type`):** `manual | purchase | sale | payment | receipt | adjustment`

**حالات القيود (`status`):** `draft | posted | reversed`

**قيود على `journal_lines`:**
```sql
CHECK(debit >= 0 AND credit >= 0)
CHECK(NOT (debit > 0 AND credit > 0))
```

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
# يتحقق أولاً بـ _account_exists() + _verify_conn_is_accounting()

_verify_conn_is_accounting(conn) -> bool
```

**[إصلاح 9 + 11 + Q-01] ثلاث محاولات بالترتيب:**

```python
# المحاولة 1: main.sqlite_master (الأكثر دقة)
#   → يتجاهل attached DBs تماماً
#   → يتحقق: accounts موجود AND items غير موجود
#   → يعمل مع ProtectedConnection لأن execute() مُعرَّفة صريحاً

# المحاولة 2: sqlite_master العادي
#   → للـ SQLite القديم أو بيئات خاصة
#   → نفس منطق المحاولة 1

# المحاولة 3 [Q-01]: اختبار مباشر للجداول
#   → يُجرب "SELECT 1 FROM accounts LIMIT 1" → has_accounts_table
#   → يُجرب "SELECT 1 FROM items LIMIT 1"    → has_items_table
#   → لو الاثنان موجودان: يرجع has_accounts AND NOT has_items
#   → يتجنب الحاجة لـ object.__getattribute__(conn, '_raw') مباشرة
#   → ProtectedConnection يمرر execute() عبر __getattr__ → _get_raw().execute()

# Fallback: يرجع True (backward compat) لو فشل كل شيء
```

> ⚠️ **[Q-01]** المحاولة الثالثة هي الأهم لـ `ProtectedConnection` — لا تحتاج الوصول المباشر لـ `_raw`.

**الحسابات الافتراضية (34 حساب):**

| النطاق | الأكواد |
|--------|---------|
| الأصول | 1, 11, 111-115, 12, 121-122 |
| الخصوم | 2, 21, 211-212, 22, 221 |
| حقوق الملكية | 3, 31-33 |
| الإيرادات | 4, 41-42 |
| المصروفات | 5, 51-53, 521-524, 531 |

---

## accounting_accounts_repo.py

#### قراءة الحسابات — [P-01] دالتان مقسّمتان

```python
fetch_all_accounts_basic(conn, acc_type=None) -> list
# بدون balance — سريعة للـ dropdowns والـ combos
# الأعمدة: id, code, name, type, subtype, parent_id, is_leaf, group_id,
#          parent_name, group_name, group_color
# JOIN: accounts LEFT JOIN accounts(parent) LEFT JOIN account_groups
# بدون JOIN مع journal_lines → أسرع بكثير

fetch_all_accounts_with_balance(conn, acc_type=None) -> list
# مع balance = SUM(debit) - SUM(credit)
# [تحسين 38] LEFT JOIN + GROUP BY بدل correlated subquery = O(1) بدل O(n)
# GROUP BY يشمل كل الأعمدة المحددة في SELECT

fetch_all_accounts(conn, acc_type=None) -> list
# للتوافق القديم — يُفوَّض لـ fetch_all_accounts_with_balance

fetch_account(conn, account_id) -> row
fetch_account_by_code(conn, code) -> row | None
fetch_leaf_accounts(conn, acc_type=None) -> list
# is_leaf=1 فقط — للاختيار في القيود
```

#### كتابة الحسابات

```python
insert_account(conn, code, name, acc_type, parent_id=None,
               group_id=None, subtype=None, notes=None) -> int
# لو parent_id محدد → UPDATE accounts SET is_leaf=0 على الأب تلقائياً

update_account(conn, account_id, name, group_id=None, notes=None)
# لا يُغيّر code أو type أو parent_id

delete_account(conn, account_id)
# CASCADE على الأبناء
```

#### أرصدة الحسابات

```python
get_account_balance(conn, account_id) -> float
get_account_natural_balance(conn, account_id) -> float
get_normal_balance(acc_type: str) -> str
# "dr" لـ asset/expense/drawings | "cr" لـ liability/capital/revenue
calc_signed_amount(acc_type, increase: bool, amount: float) -> tuple[float, float]
get_balances_by_type(conn) -> dict
# {type: {"debit": float, "credit": float, "balance": float}}
```

#### تصنيفات الحسابات (account_groups)

```python
fetch_all_groups(conn, acc_type=None) -> list
# مُرتَّبة بـ _sort_groups_parents_first()
fetch_group(conn, group_id) -> row
insert_group(conn, name, acc_type, parent_id=None, color="#607d8b") -> int
update_group(conn, group_id, name, parent_id=None, color="#607d8b")
delete_group(conn, group_id)
# يُعيد ضبط group_id=NULL في accounts أولاً

build_group_tree(rows) -> list
# [تحسين 3] id_map يُشير لنفس الـ dict objects بدل نسخ إضافية

_sort_groups_parents_first(rows) -> list
# [تحسين 3] O(n) dicts بدل O(3n):
#   - تحويل لـ dicts مرة واحدة في rows_list
#   - id_map = {r["id"]: r for r in rows_list}  ← يُشير لنفس objects
#   - DFS visit() يضمن ظهور الأب قبل أبنائه

_get_group_descendants(conn, group_id) -> set
# Private — استورد مباشرة من accounting_accounts_repo لو احتجتها
# [تحسين 14] محذوفة من الـ facade (accounting_repo.py) — private function
```

---

## accounting_journal_repo.py

#### رقم القيد التلقائي

```python
next_ref_no(conn) -> str
# "JE-00001", "JE-00002", ...
# MAX(CAST(SUBSTR(ref_no,4) AS INTEGER)) + 1
```

#### قراءة القيود

```python
fetch_all_entries(conn, limit=200) -> list
# آخر القيود بحد أقصى limit — مع total_debit و total_credit (correlated subqueries)
# [إصلاح 29] استخدم fetch_entries_count() في الـ UI لمعرفة الإجمالي

fetch_entries_count(conn) -> int
# [إصلاح 29] إجمالي عدد القيود — للـ UI pagination
# SELECT COUNT(*) as c FROM journal_entries

fetch_all_entries_paginated(conn, limit=200, offset=0,
                             date_from=None, date_to=None,
                             search=None, entry_type=None) -> list
# [إصلاح 29] pagination كاملة مع فلترة ديناميكية
# conditions تُبنى بـ list + params: آمن من SQL injection
# search: يبحث في ref_no و description بـ LIKE %search%

fetch_entry(conn, entry_id) -> row | None
fetch_entry_lines(conn, entry_id) -> list
# مع account_code, account_name, account_type من JOIN
```

#### كتابة القيود

```python
insert_entry(conn, date, description, entry_type="manual",
             notes=None, ref_id=None, ref_type=None) -> int
# يولد ref_no تلقائياً | status="posted" دائماً

add_entry_lines(conn, entry_id, lines: list)
# lines: [{"account_id", "debit", "credit", "description"}, ...]

delete_entry(conn, entry_id, changed_by="system")
# [مقترح 52] snapshot قبل الحذف في audit_log:
#   1. snapshot_journal_entry(conn, entry_id) → old_data
#   2. log_delete(conn, "journal_entries", entry_id, old_data, changed_by)
#   3. DELETE FROM journal_entries WHERE id=?
# فشل الـ audit لا يوقف الحذف (try/except مع logging.warning)

validate_entry_balance(lines: list) -> bool
# abs(total_debit - total_credit) < 0.001
```

#### دفتر الأستاذ

```python
fetch_t_account(conn, account_id) -> dict
# {account, lines, total_debit, total_credit, balance, normal_balance}
# lines مع: ref_no, date, entry_desc من JOIN
```

---

## accounting_statements_repo.py

```python
trial_balance(conn) -> list
# كل الـ leaf accounts مع total_debit, total_credit, balance
# balance = total_debit - total_credit

income_statement(conn) -> dict
# revenues: SUM(credit) - SUM(debit) لكل revenue account
# expenses: SUM(debit) - SUM(credit) لكل expense account
# {revenues, expenses, total_rev, total_exp, net_income}

balance_sheet(conn) -> dict
# {assets, liabilities, capital, drawings, net_income,
#  total_assets, total_liab, total_equity}
# total_equity = capital - drawings + net_income
# يستدعي income_statement() داخلياً لحساب net_income

owners_equity_statement(conn) -> dict
# {capital_accounts, drawings_accounts, net_income,
#  total_capital, total_drawings, total_equity}
# total_equity = total_capital - total_drawings + net_income
```

---

## accounting_inventory_repo.py

```python
purchase_inventory(inv_conn, acc_conn,
                   inv_id, qty, unit_cost, date,
                   payment_account_id, notes=None,
                   changed_by="system") -> tuple[entry_id, move_id]
```

**التحقق من المدخلات:**
- `qty <= 0` → ValueError
- `unit_cost < 0` → ValueError
- الصنف غير موجود → ValueError
- حساب المخزون غير موجود → ValueError (يُجرب account_code ثم subtype='inventory')
- payment_account_id فارغ → ValueError

**المرحلتان:**
1. إنشاء قيد محاسبي في `accounting.db` (debit: inv_acc, credit: payment_acc)
2. تسجيل حركة وارد في `inventory.db` عبر `record_inventory_move`

**[إصلاح 32] Rollback محصّن بالكامل:**
```python
# entry_id=None guard: لا rollback بدون قيد حقيقي

# لو فشلت المرحلة 2:
#   محاولة rollback:
#     1. _audit_rollback(acc_conn, entry_id, reason, changed_by)
#        → snapshot_journal_entry + log_action("delete")
#     2. DELETE FROM journal_entries WHERE id=?
#     3. rollback_ok = True → يرمي RuntimeError واضحة

#   لو فشل الـ rollback نفسه:
#     _audit_critical_inconsistency(...):
#       old_data["status"] = "CRITICAL_INCONSISTENCY"
#       changed_by مُعدَّل: f"{changed_by}:CRITICAL_ROLLBACK_FAIL"
#     logger.critical(...)
#     يرمي RuntimeError بتفاصيل كاملة
```

**دوال مساعدة للـ Audit [مقترح 52]:**
```python
_audit_rollback(acc_conn, entry_id, reason, changed_by)
# snapshot + log_action("delete") قبل حذف القيد
# الفشل لا يوقف الـ rollback (try/except مع logger.warning)

_audit_critical_inconsistency(acc_conn, entry_id, inv_err, rb_err,
                               inv_id, qty, unit_cost, date, changed_by)
# يُسجّل حالة تناقض حرجة في audit_log
# يُحاوِل الكتابة حتى لو conn في حالة غير مستقرة
```

**Raises:**
- `ValueError` — بيانات غير صحيحة أو فشل إنشاء القيد
- `RuntimeError` — فشل تسجيل المخزون أو فشل الـ rollback

---

## accounting_audit_repo.py

```python
AUDIT_LOG_DDL
# CREATE TABLE IF NOT EXISTS audit_log (...)
# action CHECK("delete"|"update"|"create")
# old_data TEXT — JSON snapshot
# changed_by TEXT DEFAULT "system"

create_audit_log_table(conn)
# executescript(AUDIT_LOG_DDL) + commit
# محاط بـ try/except مع logger.warning
```

#### كتابة السجلات

```python
log_action(conn, action, table_name, record_id=None,
           old_data=None, changed_by="system") -> int | None
# action: "delete" | "update" | "create"
# old_data: dict | list | str | None
#   → None: old_json = None
#   → str: يُخزَّن كما هو
#   → dict/list: json.dumps(ensure_ascii=False, default=str)
# فشل الـ insert يُسجَّل كـ warning — لا يوقف العملية الأصلية
# يرجع lastrowid أو None عند الفشل

log_delete(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_update(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_create(conn, table_name, record_id, data=None, changed_by="system") -> int | None
```

#### Snapshots قبل الحذف

```python
snapshot_journal_entry(conn, entry_id) -> dict | None
# {"entry": dict(entry_row), "lines": [dict(line) for line in lines]}
# lines مع: account_code, account_name من JOIN

snapshot_account(conn, account_id) -> dict | None
# dict(row) أو None

snapshot_row(conn, table, record_id, id_col="id") -> dict | None
# snapshot عام لأي جدول بسيط
```

#### قراءة السجل

```python
fetch_audit_log(conn, table_name=None, action=None,
                limit=200, offset=0) -> list
# كل row يحتوي إضافةً على "old_data_parsed" (JSON parsed) لو أمكن

fetch_audit_log_count(conn, table_name=None, action=None) -> int
fetch_record_history(conn, table_name, record_id) -> list
# تاريخ كامل لسجل معين — ORDER BY id DESC
```

---

## accounting_repo.py

Facade للتوافق مع الكود القديم — يُعيد تصدير كل الدوال من الملفات المقسّمة.

```python
from db.accounting.accounting_repo import (
    # [P-01] دوال مقسّمة جديدة
    fetch_all_accounts_basic, fetch_all_accounts_with_balance,
    # للتوافق القديم
    fetch_all_accounts, fetch_account, fetch_account_by_code,
    fetch_leaf_accounts, insert_account, update_account, delete_account,
    get_account_balance, get_account_natural_balance, get_normal_balance,
    calc_signed_amount, get_balances_by_type,
    # groups
    fetch_all_groups, fetch_group, insert_group, update_group,
    delete_group, build_group_tree,
    # journal
    next_ref_no, fetch_all_entries, fetch_entries_count,
    fetch_all_entries_paginated,
    fetch_entry, fetch_entry_lines,
    insert_entry, add_entry_lines, delete_entry, validate_entry_balance,
    fetch_t_account,
    # statements
    trial_balance, income_statement, balance_sheet, owners_equity_statement,
    # inventory
    purchase_inventory,
    # audit log
    create_audit_log_table,
    log_action, log_delete, log_update, log_create,
    snapshot_journal_entry, snapshot_account, snapshot_row,
    fetch_audit_log, fetch_audit_log_count, fetch_record_history,
)
```

> ⚠️ `_get_group_descendants` **محذوفة** من الـ facade [تحسين 14] — هي private function. استوردها مباشرة من `accounting_accounts_repo`.

---

## accounting_repo_ui_helpers.py

دوال مساعدة نُقلت من الـ UI widgets إلى DB layer.

```python
fetch_account_by_code(conn, code: str) -> row | None
# SELECT id FROM accounts WHERE code=?

fetch_capital_line_for_entry(conn, entry_id: int) -> int
# يرجع id أول سطر دائن (credit > 0) في القيد، أو 0

fetch_drawings_line_for_entry(conn, entry_id: int) -> int
# يرجع id أول سطر مدين (debit > 0) في القيد، أو 0

fetch_entry_by_ref(conn, ref_no: str) -> row | None
# SELECT id FROM journal_entries WHERE ref_no=?

fetch_investor_entry_id(erp_conn, link_id: int) -> int | None
# يأخذ erp_conn (ليس acc_conn) لأن investor_entries في erp.db
# SELECT entry_id FROM investor_entries WHERE id=?
```

> ⚠️ كل الدوال تُعيد `None` أو `0` عند الفشل — لا ترمي exceptions.

---

## investors_repo.py

#### Cache الـ Migration — [إصلاح 31] + [تحسين 7]

```python
_investors_migrated: set   # مجموعة db_paths التي تمّ migration عليها

_get_db_path(conn) -> str
# [تحسين 7] Fast path — ProtectedConnection:
#   try:
#     path = object.__getattribute__(conn, '_path')
#     if path and isinstance(path, str): return path
#   except AttributeError: pass
#   → يستخدم object.__getattribute__ مباشرة لتجاوز الـ proxy
#   → O(1) بدون أي I/O أو PRAGMA
#
# Slow path — sqlite3.Connection العادي:
#   conn.execute("PRAGMA database_list").fetchone()[2]
#   → يُستدعى فقط لو conn ليس ProtectedConnection أو _path فشل
#   → fallback: str(id(conn)) لو PRAGMA فشل أيضاً

_migrate_investors(conn)
# [إصلاح 31] يُنفَّذ مرة واحدة per-connection-path:
#   1. path = _get_db_path(conn)
#   2. لو path في _investors_migrated → return فوراً
#   3. يتحقق من وجود جدول investors
#   4. لو غير موجود → create_investors_tables(conn) → إضافة path → return
#   5. يتحقق من شكل investor_entries:
#      sql_row = SELECT sql FROM sqlite_master WHERE name='investor_entries'
#      لو "REFERENCES journal_" في sql → migration بـ executescript:
#        PRAGMA foreign_keys = OFF;
#        CREATE TABLE _investor_entries_new (...بدون REFERENCES journal_...);
#        INSERT ... SELECT ... FROM investor_entries;
#        DROP TABLE investor_entries;
#        ALTER TABLE _investor_entries_new RENAME TO investor_entries;
#        PRAGMA foreign_keys = ON;
#   6. إضافة path لـ _investors_migrated

invalidate_investors_migration_cache(conn=None)
# يُمسح الـ cache — استدعه لو احتجت إعادة فحص الـ schema
# conn=None → _investors_migrated.clear()
# conn=<conn> → _investors_migrated.discard(_get_db_path(conn))
```

#### إنشاء الجداول

```python
create_investors_tables(conn)
# executescript:
#   CREATE TABLE IF NOT EXISTS investors (id, name UNIQUE, notes, joined_at, created_at)
#   CREATE TABLE IF NOT EXISTS investor_entries (
#       id, investor_id→CASCADE, entry_id, line_id,
#       move_type CHECK("capital"|"drawings"), amount DEFAULT 0, notes
#   )
# ملاحظة: investor_entries لا تحتوي REFERENCES لـ journal_entries
#   (تم إزالتها في migration لأن القيود موجودة في accounting.db منفصل)
```

#### CRUD — المستثمرون

```python
fetch_all_investors(conn) -> list
# يستدعي _migrate_investors(conn) أولاً
# SELECT id, name, notes, joined_at, created_at FROM investors ORDER BY name

fetch_investor(conn, investor_id) -> row
# يستدعي _migrate_investors(conn) أولاً

insert_investor(conn, name, notes=None, joined_at=None) -> int
# joined_at افتراضياً = today (datetime.now().strftime("%Y-%m-%d"))
# يستدعي _migrate_investors(conn) أولاً

update_investor(conn, investor_id, name, notes=None, joined_at=None)
delete_investor(conn, investor_id)

investor_exists(conn, name) -> int | None
# يرجع investor_id لو موجود، أو None
```

#### ربط المستثمر بالقيود

```python
link_investor_to_line(conn, investor_id, entry_id, line_id,
                       move_type, amount, notes=None) -> int
# move_type: "capital" | "drawings"

fetch_investor_entries(conn, investor_id, acc_conn=None) -> list
# لو acc_conn متاح → يجلب بيانات القيد (ref_no, date, account_code, ...)
# كل entry: {id, move_type, amount, notes, created_at,
#             ref_no, date, entry_desc, debit, credit,
#             line_desc, account_code, account_name, account_type}
# fallback لو acc_conn=None: ref_no=f"Entry#{entry_id}", date="—"

fetch_entry_investor_links(conn, entry_id) -> list
# مع investor_name من JOIN
delete_investor_link(conn, link_id)
delete_entry_investor_links(conn, entry_id)
```

#### تقارير — [إصلاح 40]

```python
calc_investor_summary(conn, investor_id, acc_conn=None) -> dict
# {investor_id, investor_name, joined_at, notes,
#  total_capital, total_drawings, net_investment, entries}

calc_all_investors_summary(conn, acc_conn=None) -> list
# [إصلاح 40] O(1) + O(entries) بدل O(n×m) queries:
#
#   الخطوة 1: جلب كل investor_entries دفعة واحدة
#     SELECT * FROM investor_entries ORDER BY investor_id, created_at DESC
#
#   الخطوة 2: تجميع entries بـ defaultdict(list) حسب investor_id
#
#   الخطوة 3: لو acc_conn متاح → batch queries:
#     all_entry_ids = {r["entry_id"] for r in all_entries}
#     all_line_ids  = {r["line_id"]  for r in all_entries}
#     SELECT ... FROM journal_entries WHERE id IN (...)   → je_cache
#     SELECT ... FROM journal_lines JOIN accounts WHERE id IN (...) → jl_cache
#
#   الخطوة 4: بناء النتائج من الـ cache بدون queries إضافية
#
# النتائج مُرتَّبة بـ net_investment DESC
```

---

## ملاحظات

- `accounting.db` منفصل تماماً عن `erp.db` — لا FOREIGN KEYS بينهما.
- استخدم `_verify_conn_is_accounting()` للتحقق من صحة الـ connection قبل الكتابة.
- `purchase_inventory` يحتاج **connection-ين** منفصلين: `inv_conn` و `acc_conn`.
- `calc_all_investors_summary` يجلب acc_conn data دفعة واحدة [إصلاح 40].
- `delete_entry` يُسجّل snapshot في audit_log قبل الحذف تلقائياً [مقترح 52].
- `_migrate_investors` تُنفَّذ مرة واحدة per-path بفضل `_investors_migrated` set [إصلاح 31].
- `invalidate_investors_migration_cache()` متاحة لإعادة فحص الـ schema لو احتجت.
- `_get_db_path` fast path O(1) لـ ProtectedConnection عبر `object.__getattribute__` [تحسين 7].
- `fetch_all_accounts_basic` للـ dropdowns | `fetch_all_accounts_with_balance` للتقارير [P-01].
- `_sort_groups_parents_first` تستخدم O(n) dicts بدل O(3n) [تحسين 3].
- `_verify_conn_is_accounting` تدعم ProtectedConnection عبر المحاولة الثالثة [Q-01].