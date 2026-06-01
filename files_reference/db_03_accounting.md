# دليل الكود — DB (3): المحاسبة (accounting.db)

> جداول `accounting.db` — الحسابات، القيود، القوائم المالية، المستثمرون، Audit Log.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [schema](#schema) | `db/accounting/accounting_schema.py` |
| [accounting_schema_constants](#accounting_schema_constants) | `db/accounting/accounting_schema_constants.py` |
| [accounting_schema_seed](#accounting_schema_seed) | `db/accounting/accounting_schema_seed.py` |
| [accounting_accounts_repo](#accounting_accounts_repo) | `db/accounting/accounting_accounts_repo.py` |
| [accounting_journal_repo](#accounting_journal_repo) | `db/accounting/accounting_journal_repo.py` |
| [accounting_statements_repo](#accounting_statements_repo) | `db/accounting/accounting_statements_repo.py` |
| [accounting_inventory_repo](#accounting_inventory_repo) | `db/accounting/accounting_inventory_repo.py` |
| [accounting_audit_repo](#accounting_audit_repo) | `db/accounting/accounting_audit_repo.py` |
| [investors_repo](#investors_repo) | `db/accounting/investors_repo.py` |
| [accounting_repo (Facade)](#accounting_repo-facade) | `db/accounting/accounting_repo.py` |
| [accounting_repo_ui_helpers](#accounting_repo_ui_helpers) | `db/accounting/accounting_repo_ui_helpers.py` |

---

## schema

### `db/accounting/accounting_schema.py`

Facade يُعيد تصدير من الملفات المقسّمة:
- `accounting_schema_constants.py` — الثوابت
- `accounting_schema_migrations.py` — الـ migrations
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

## accounting_schema_constants

### `db/accounting/accounting_schema_constants.py`

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

## accounting_schema_seed

### `db/accounting/accounting_schema_seed.py`

```python
seed_default_accounts(conn)
# يُضيف شجرة الحسابات الافتراضية لو كانت قاعدة البيانات فارغة
# يتحقق أولاً بـ _account_exists() + _verify_conn_is_accounting()

_verify_conn_is_accounting(conn) -> bool
# [إصلاح 9 + 11 + Q-01] ثلاث محاولات:
#   1. main.sqlite_master — الأكثر دقة (يتجاهل attached DBs)
#   2. sqlite_master العادي — للـ SQLite القديم
#   3. اختبار مباشر للجداول — fallback لـ ProtectedConnection
# يتحقق: accounts موجود AND items غير موجود
# يرجع True كـ backward compat لو فشل كل شيء
```

**الحسابات الافتراضية (34 حساب):**

| النطاق | الأكواد |
|--------|---------|
| الأصول | 1, 11, 111-115, 12, 121-122 |
| الخصوم | 2, 21, 211-212, 22, 221 |
| حقوق الملكية | 3, 31-33 |
| الإيرادات | 4, 41-42 |
| المصروفات | 5, 51-53, 521-524, 531 |

> ⚠️ استخدم `_verify_conn_is_accounting()` قبل أي عملية كتابة على `accounting.db` لتجنب الكتابة على `erp.db` بالخطأ.

---

## accounting_accounts_repo

### `db/accounting/accounting_accounts_repo.py`

#### قراءة الحسابات — [P-01] دالتان مقسّمتان

```python
fetch_all_accounts_basic(conn, acc_type=None) -> list
# بدون balance — سريعة للـ dropdowns والـ combos
# LEFT JOIN مع accounts (parent) و account_groups فقط
# الأعمدة: id, code, name, type, subtype, parent_id, is_leaf, group_id,
#          parent_name, group_name, group_color

fetch_all_accounts_with_balance(conn, acc_type=None) -> list
# مع balance = SUM(debit) - SUM(credit)
# [تحسين 38] LEFT JOIN + GROUP BY بدل correlated subquery = O(1) بدل O(n)
# يضيف عمود: balance

fetch_all_accounts(conn, acc_type=None) -> list
# للتوافق القديم — يُفوَّض لـ fetch_all_accounts_with_balance

fetch_account(conn, account_id) -> row
# مع parent_name و group_name و group_color
fetch_account_by_code(conn, code) -> row | None
fetch_leaf_accounts(conn, acc_type=None) -> list
# is_leaf=1 فقط — للاختيار في القيود
```

#### كتابة الحسابات

```python
insert_account(conn, code, name, acc_type, parent_id=None,
               group_id=None, subtype=None, notes=None) -> int
# لو parent_id محدد → UPDATE accounts SET is_leaf=0 على الأب تلقائياً
# is_leaf=1 للحساب الجديد دائماً

update_account(conn, account_id, name, group_id=None, notes=None)
# لا يُغيّر code أو type أو parent_id
delete_account(conn, account_id)
# CASCADE على الأبناء
```

#### أرصدة الحسابات

```python
get_account_balance(conn, account_id) -> float
# COALESCE(SUM(debit) - SUM(credit), 0)

get_account_natural_balance(conn, account_id) -> float
# يراعي الـ normal balance (dr/cr)

get_normal_balance(acc_type: str) -> str
# "dr" لـ asset/expense/drawings | "cr" لـ liability/capital/revenue

calc_signed_amount(acc_type, increase: bool, amount: float) -> tuple[float, float]
# يرجع (debit, credit)

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
# [تحسين 3] O(n) dicts بدل O(3n)
# يضمن ظهور الأب قبل أبنائه دائماً

_get_group_descendants(conn, group_id) -> set
# Private — استورد مباشرة من accounting_accounts_repo لو احتجتها
```

---

## accounting_journal_repo

### `db/accounting/accounting_journal_repo.py`

#### رقم القيد التلقائي

```python
next_ref_no(conn) -> str
# "JE-00001", "JE-00002", ...
# MAX(CAST(SUBSTR(ref_no,4) AS INTEGER)) + 1
```

#### قراءة القيود

```python
fetch_all_entries(conn, limit=200) -> list
# آخر القيود بحد أقصى limit — مع total_debit و total_credit
# [إصلاح 29] استخدم fetch_entries_count() في الـ UI لمعرفة الإجمالي

fetch_entries_count(conn) -> int
# [إصلاح 29] إجمالي عدد القيود — للـ UI pagination

fetch_all_entries_paginated(conn, limit=200, offset=0,
                             date_from=None, date_to=None,
                             search=None, entry_type=None) -> list
# [إصلاح 29] pagination كاملة مع فلترة
# search: يبحث في ref_no و description

fetch_entry(conn, entry_id) -> row | None
# SELECT * FROM journal_entries

fetch_entry_lines(conn, entry_id) -> list
# مع account_code, account_name, account_type من JOIN
```

#### كتابة القيود

```python
insert_entry(conn, date, description, entry_type="manual",
             notes=None, ref_id=None, ref_type=None) -> int
# يولد ref_no تلقائياً بـ next_ref_no()
# status="posted" دائماً

add_entry_lines(conn, entry_id, lines: list)
# lines: [{"account_id", "debit", "credit", "description"}, ...]

delete_entry(conn, entry_id, changed_by="system")
# [مقترح 52] يأخذ snapshot بـ snapshot_journal_entry قبل الحذف
# يُسجّل في audit_log ثم يحذف
# فشل الـ audit لا يوقف الحذف — يُسجَّل كـ warning فقط

validate_entry_balance(lines: list) -> bool
# abs(total_debit - total_credit) < 0.001
```

#### دفتر الأستاذ

```python
fetch_t_account(conn, account_id) -> dict
# {account: dict, lines: [dict], total_debit, total_credit,
#  balance, normal_balance}
# lines مرتبة بـ date, id
```

---

## accounting_statements_repo

### `db/accounting/accounting_statements_repo.py`

```python
trial_balance(conn) -> list
# كل الـ leaf accounts مع total_debit, total_credit, balance
# balance = total_debit - total_credit

income_statement(conn) -> dict
# {revenues: [dict], expenses: [dict],
#  total_rev, total_exp, net_income}
# revenues: credit - debit | expenses: debit - credit

balance_sheet(conn) -> dict
# {assets, liabilities, capital, drawings, net_income,
#  total_assets, total_liab, total_equity}
# total_equity = capital - drawings + net_income

owners_equity_statement(conn) -> dict
# {capital_accounts, drawings_accounts, net_income,
#  total_capital, total_drawings, total_equity}
```

---

## accounting_inventory_repo

### `db/accounting/accounting_inventory_repo.py`

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
- حساب المخزون غير موجود → ValueError (يجرب account_code أولاً ثم subtype='inventory')
- payment_account_id فارغ → ValueError

**المرحلتان:**
1. إنشاء قيد محاسبي في `accounting.db` (مدين: حساب مخزون، دائن: حساب دفع)
2. تسجيل حركة وارد في `inventory.db`

**[إصلاح 32] Rollback محصّن:**
```python
# لو فشلت المرحلة 2:
#   - يحاول حذف القيد المحاسبي
#   - [مقترح 52] يُسجّل rollback في audit_log قبل الحذف
#   - لو فشل الـ rollback → CRITICAL log + RuntimeError واضحة
#   - entry_id=None guard يمنع rollback بدون قيد حقيقي
```

**دوال مساعدة [مقترح 52]:**
```python
_audit_rollback(acc_conn, entry_id, reason, changed_by)
# يُسجّل عملية الـ rollback في audit_log قبل الحذف
# فشله لا يوقف الـ rollback

_audit_critical_inconsistency(acc_conn, entry_id, inv_err, rb_err,
                               inv_id, qty, unit_cost, date, changed_by)
# يُسجّل حالة التناقض الحرجة — يُحاوِل الكتابة حتى لو الـ conn غير مستقر
```

**Raises:**
- `ValueError` — بيانات غير صحيحة أو فشل إنشاء القيد
- `RuntimeError` — فشل تسجيل المخزون (مع rollback) أو فشل الـ rollback نفسه

---

## accounting_audit_repo

### `db/accounting/accounting_audit_repo.py`

```python
AUDIT_LOG_DDL  # CREATE TABLE IF NOT EXISTS audit_log (...)

create_audit_log_table(conn)
# يستخدم executescript(AUDIT_LOG_DDL) + commit
# فشله يُسجَّل كـ warning فقط
```

#### كتابة السجلات

```python
log_action(conn, action, table_name, record_id=None,
           old_data=None, changed_by="system") -> int | None
# action: "delete" | "update" | "create"
# old_data: dict | list | str → يُحوَّل لـ JSON تلقائياً
# فشل الـ insert يُسجَّل كـ warning — لا يوقف العملية الأصلية
# يرجع id السجل الجديد أو None عند الفشل

log_delete(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_update(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_create(conn, table_name, record_id, data=None, changed_by="system") -> int | None
```

#### Snapshots قبل الحذف

```python
snapshot_journal_entry(conn, entry_id) -> dict | None
# {entry: dict, lines: [dict]} — مع account_code و account_name

snapshot_account(conn, account_id) -> dict | None
# dict(row) من accounts

snapshot_row(conn, table, record_id, id_col="id") -> dict | None
# snapshot عام لأي جدول بسيط
```

#### قراءة السجل

```python
fetch_audit_log(conn, table_name=None, action=None,
                limit=200, offset=0) -> list
# كل dict يحتوي: id, action, table_name, record_id,
#   old_data (string), old_data_parsed (dict | None), changed_by, created_at

fetch_audit_log_count(conn, table_name=None, action=None) -> int

fetch_record_history(conn, table_name, record_id) -> list
# كل تعديلات سجل بعينه مرتبة DESC
```

---

## investors_repo

### `db/accounting/investors_repo.py`

#### Cache الـ Migration — [إصلاح 31]

```python
_investors_migrated: set   # مجموعة db_paths التي تمّ migration عليها

_get_db_path(conn) -> str
# [تحسين 7] Fast path: ProtectedConnection._path مباشرة O(1)
# Slow path: PRAGMA database_list للـ connections العادية

_migrate_investors(conn)
# يُنفَّذ مرة واحدة per-connection-path
# يتحقق من شكل investor_entries — إذا كان schema قديم يُهاجره
# Migration القديم: investor_entries كان يحتوي REFERENCES journal_entries
# Migration الجديد: entry_id و line_id بدون FK عبر DBs

invalidate_investors_migration_cache(conn=None)
# conn=None → يمسح كل الـ cache | conn محدد → يمسح هذا المسار فقط
```

#### CRUD — المستثمرون

```python
fetch_all_investors(conn) -> list   # ORDER BY name
fetch_investor(conn, investor_id) -> row
insert_investor(conn, name, notes=None, joined_at=None) -> int
# joined_at الافتراضي: today بـ datetime.now().strftime("%Y-%m-%d")
update_investor(conn, investor_id, name, notes=None, joined_at=None)
delete_investor(conn, investor_id)
# CASCADE على investor_entries
investor_exists(conn, name) -> int | None
# يرجع id لو موجود أو None
```

#### ربط المستثمر بالقيود

```python
link_investor_to_line(conn, investor_id, entry_id, line_id,
                       move_type, amount, notes=None) -> int
# move_type: "capital" | "drawings"

fetch_investor_entries(conn, investor_id, acc_conn=None) -> list
# لو acc_conn متاح → يجلب بيانات القيود (ref_no, date, description)
#                    + بيانات السطور (debit, credit, account_code, account_name)
# كل entry كـ dict مع كل الحقول

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
# [إصلاح 40] O(1) + O(entries) بدل O(n×m) queries
# خطوات:
#   1. جلب كل investor_entries دفعة واحدة
#   2. تجميع حسب investor_id في defaultdict
#   3. لو acc_conn: جلب je_cache و jl_cache دفعة واحدة بـ IN (...)
#   4. بناء النتائج بدون queries إضافية
# النتائج مُرتَّبة بـ net_investment DESC
```

---

## accounting_repo (Facade)

### `db/accounting/accounting_repo.py`

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
    # audit log [مقترح 52]
    create_audit_log_table,
    log_action, log_delete, log_update, log_create,
    snapshot_journal_entry, snapshot_account, snapshot_row,
    fetch_audit_log, fetch_audit_log_count, fetch_record_history,
)
```

> ⚠️ `_get_group_descendants` **محذوفة** من الـ facade [تحسين 14] — هي private function. استوردها مباشرة من `accounting_accounts_repo` لو احتجتها.

---

## accounting_repo_ui_helpers

### `db/accounting/accounting_repo_ui_helpers.py`

دوال مساعدة نُقلت من الـ UI widgets إلى DB layer لفصل المسؤوليات.

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
# SELECT entry_id FROM investor_entries WHERE id=?
# يأخذ erp_conn (ليس acc_conn) لأن investor_entries في erp.db
```

> ⚠️ كل الدوال تُعيد `None` أو `0` عند الفشل — لا ترمي exceptions.

---

## ملاحظات

- الـ `accounting.db` منفصل تماماً عن `erp.db` — لا FOREIGN KEYS بينهما.
- استخدم `_verify_conn_is_accounting()` للتحقق من صحة الـ connection قبل الكتابة.
- `purchase_inventory` يحتاج **connection-ين** منفصلين: `inv_conn` لـ inventory و `acc_conn` لـ accounting.
- `calc_all_investors_summary` يجلب acc_conn data دفعة واحدة [إصلاح 40] — استخدمه بدل `calc_investor_summary` في حلقات.
- `delete_entry` يُسجّل snapshot في audit_log قبل الحذف تلقائياً [مقترح 52].