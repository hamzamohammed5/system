# دليل الكود — DB (3): المحاسبة (accounting.db)

> جداول `accounting.db` — الحسابات، القيود، القوائم المالية، المستثمرون، Audit Log.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [schema](#schema) | `db/accounting/accounting_schema.py` |
| [accounting_accounts_repo](#accounting_accounts_repo) | `db/accounting/accounting_accounts_repo.py` |
| [accounting_journal_repo](#accounting_journal_repo) | `db/accounting/accounting_journal_repo.py` |
| [accounting_statements_repo](#accounting_statements_repo) | `db/accounting/accounting_statements_repo.py` |
| [accounting_inventory_repo](#accounting_inventory_repo) | `db/accounting/accounting_inventory_repo.py` |
| [accounting_audit_repo](#accounting_audit_repo) | `db/accounting/accounting_audit_repo.py` |
| [investors_repo](#investors_repo) | `db/accounting/investors_repo.py` |
| [accounting_repo (Facade)](#accounting_repo-facade) | `db/accounting/accounting_repo.py` |

---

## schema

### `db/accounting/accounting_schema.py`

```python
create_accounting_tables(conn)
# ينشئ: account_groups, accounts, journal_entries, journal_lines, audit_log
# ثم يُطبّق الـ migrations ويُشغّل seed_default_accounts
```

**جداول accounting.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `account_groups` | `id, name, acc_type, parent_id, color, notes` |
| `accounts` | `id, code UNIQUE, name, type, subtype, parent_id, is_leaf, group_id, notes` |
| `journal_entries` | `id, ref_no UNIQUE, date, description, type, status, ref_id, ref_type, notes` |
| `journal_lines` | `id, entry_id→CASCADE, account_id, debit, credit, description` |
| `audit_log` | `id, action, table_name, record_id, old_data, changed_by, created_at` |
| `investors` | `id, name UNIQUE, notes, joined_at, created_at` |
| `investor_entries` | `id, investor_id→CASCADE, entry_id, line_id, move_type, amount, notes` |

**أنواع الحسابات (`type`):** `asset | liability | capital | revenue | expense | drawings`

**أنواع القيود (`type`):** `manual | purchase | sale | payment | receipt | adjustment`

**حالات القيود (`status`):** `draft | posted | reversed`

**ثوابت مُصدَّرة من `accounting_schema_constants.py`:**
```python
TYPE_AR      # {"asset": "أصول", "liability": "خصوم", ...}
EQUITY_TYPES # {"capital", "drawings", "revenue", "expense"}
TYPE_GROUP   # {"asset": "asset", "capital": "equity", ...}
GROUP_AR     # {"asset": "الأصول", "liability": "الخصوم", "equity": "حقوق الملكية"}
NORMAL_BALANCE # {"asset": "dr", "expense": "dr", ..., "liability": "cr", "capital": "cr"}
```

---

## accounting_accounts_repo

### `db/accounting/accounting_accounts_repo.py`

#### قراءة الحسابات

```python
# [P-01] دالتان مقسّمتان حسب الاحتياج:
fetch_all_accounts_basic(conn, acc_type=None) -> list
# بدون balance — سريعة للـ dropdowns والـ combos
# لا تحتاج JOIN مع journal_lines

fetch_all_accounts_with_balance(conn, acc_type=None) -> list
# مع balance — للتقارير والقوائم المالية
# [تحسين 38] LEFT JOIN بدل correlated subquery = O(1) بدل O(n)

fetch_all_accounts(conn, acc_type=None) -> list
# للتوافق مع الكود القديم — يُفوَّض لـ fetch_all_accounts_with_balance

fetch_account(conn, account_id) -> row
fetch_account_by_code(conn, code) -> row | None
fetch_leaf_accounts(conn, acc_type=None) -> list
```

#### كتابة الحسابات

```python
insert_account(conn, code, name, acc_type, parent_id=None,
               group_id=None, subtype=None, notes=None) -> int
# لو parent_id محدد → يُحدِّث is_leaf=0 على الأب تلقائياً

update_account(conn, account_id, name, group_id=None, notes=None)
delete_account(conn, account_id)
```

#### أرصدة الحسابات

```python
get_account_balance(conn, account_id) -> float
# = SUM(debit) - SUM(credit) من journal_lines

get_account_natural_balance(conn, account_id) -> float
# الرصيد بالإشارة الطبيعية للحساب

get_normal_balance(acc_type: str) -> str
# "dr" لـ asset/expense/drawings | "cr" لـ liability/capital/revenue

calc_signed_amount(acc_type, increase, amount) -> tuple[float, float]
# يرجع (debit, credit) حسب نوع الحساب وهل هو زيادة أم نقص

get_balances_by_type(conn) -> dict
# {type: {"debit": float, "credit": float, "balance": float}}
```

#### تصنيفات الحسابات (account_groups)

```python
fetch_all_groups(conn, acc_type=None) -> list
# [تحسين 3] مُرتّبة بحيث الأب قبل أبنائه دائماً — O(n) ذاكرة

fetch_group(conn, group_id) -> row
insert_group(conn, name, acc_type, parent_id=None, color="#607d8b") -> int
update_group(conn, group_id, name, parent_id=None, color="#607d8b")
delete_group(conn, group_id)
# يُفرِّغ group_id من الحسابات قبل الحذف

build_group_tree(rows) -> list
# يبني شجرة هرمية من قائمة مسطحة
# كل node: {id, name, acc_type, parent_id, color, children:[...]}
```

> ⚠️ `_get_group_descendants` دالة private — لا تُصدَّر من الـ facade.
> استوردها مباشرة من `accounting_accounts_repo` لو احتجتها.

---

## accounting_journal_repo

### `db/accounting/accounting_journal_repo.py`

#### رقم القيد التلقائي

```python
next_ref_no(conn) -> str
# "JE-00001", "JE-00002", ...
# يأخذ MAX من ref_no الموجودة ويزيد 1
```

#### قراءة القيود

```python
fetch_all_entries(conn, limit=200) -> list
# [إصلاح 29] يقطع البيانات بصمت عند limit — استخدم مع fetch_entries_count

fetch_entries_count(conn) -> int
# [إصلاح 29] إجمالي عدد القيود — للـ pagination وعرض "يعرض X من أصل Y"

fetch_all_entries_paginated(conn, limit=200, offset=0,
                             date_from=None, date_to=None,
                             search=None, entry_type=None) -> list
# [إصلاح 29] pagination كاملة مع فلترة — البديل الأفضل لـ fetch_all_entries

fetch_entry(conn, entry_id) -> row | None
fetch_entry_lines(conn, entry_id) -> list
# يرجع السطور مع بيانات الحساب (code, name, type)
```

**مثال pagination في الـ UI:**
```python
PAGE = 200
total   = fetch_entries_count(conn)
entries = fetch_all_entries_paginated(conn, limit=PAGE, offset=page * PAGE)
if total > len(entries):
    label.setText(f"يعرض {len(entries)} من أصل {total} قيد")
```

#### كتابة القيود

```python
insert_entry(conn, date, description, entry_type="manual",
             notes=None, ref_id=None, ref_type=None) -> int
# يولد ref_no تلقائياً عبر next_ref_no()

add_entry_lines(conn, entry_id, lines: list)
# lines: [{"account_id", "debit", "credit", "description"}, ...]

delete_entry(conn, entry_id, changed_by="system")
# [مقترح 52] يأخذ snapshot كامل في audit_log قبل الحذف
# الفشل في الـ audit لا يوقف الحذف

validate_entry_balance(lines: list) -> bool
# يتحقق أن SUM(debit) == SUM(credit) بهامش 0.001
```

#### دفتر الأستاذ (T Account)

```python
fetch_t_account(conn, account_id) -> dict
# {account, lines, total_debit, total_credit, balance, normal_balance}
```

---

## accounting_statements_repo

### `db/accounting/accounting_statements_repo.py`

```python
trial_balance(conn) -> list
# ميزان المراجعة — كل الحسابات الورقية (is_leaf=1) مع إجمالي المدين والدائن
# كل صف: {code, name, type, total_debit, total_credit, balance}

income_statement(conn) -> dict
# قائمة الدخل
# {revenues: [...], expenses: [...], total_rev, total_exp, net_income}

balance_sheet(conn) -> dict
# الميزانية العمومية
# {assets, liabilities, capital, drawings, net_income,
#  total_assets, total_liab, total_equity}

owners_equity_statement(conn) -> dict
# قائمة حقوق الملكية
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

يسجل شراء مخزن في خطوتين:
1. ينشئ قيد محاسبي في `accounting.db` (مدين المخزون / دائن حساب الدفع)
2. يسجل حركة وارد في `inventory.db`

**[إصلاح 32] Rollback محصّن:**
- لو فشل `record_inventory_move` → يحذف القيد المحاسبي تلقائياً
- لو فشل الـ rollback نفسه → يُسجّل `CRITICAL` في audit_log ويرفع `RuntimeError`

**[مقترح 52]** يُسجّل في audit_log قبل أي حذف للـ rollback.

**Raises:**
- `ValueError` — بيانات غير صحيحة أو حساب غير موجود
- `RuntimeError` — فشل الـ rollback (حالة حرجة تحتاج تدخل يدوي)

---

## accounting_audit_repo

### `db/accounting/accounting_audit_repo.py`

نظام تدقيق العمليات الحساسة — [مقترح 52].

**فلسفة الـ Audit Log:**
- يُكتب دائماً **قبل** تنفيذ العملية (pre-action snapshot)
- الفشل في الكتابة لا يوقف العملية الأصلية — يُسجَّل كـ warning فقط
- `old_data` مخزّن كـ JSON للمرونة
- `changed_by` يُمرَّر من الـ UI أو يبقى `'system'`

#### إنشاء الجدول

```python
create_audit_log_table(conn)
# ينشئ جدول audit_log لو لم يكن موجوداً
```

#### تسجيل العمليات

```python
log_action(conn, action, table_name, record_id=None,
           old_data=None, changed_by="system") -> int | None
# action: 'delete' | 'update' | 'create'
# old_data: dict | list | str — يُحوَّل لـ JSON تلقائياً
# يرجع id السجل الجديد أو None لو فشل

log_delete(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_update(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_create(conn, table_name, record_id, data=None, changed_by="system") -> int | None
```

#### Snapshots قبل الحذف

```python
snapshot_journal_entry(conn, entry_id) -> dict | None
# snapshot كامل للقيد وسطوره
# {"entry": {...}, "lines": [...]}

snapshot_account(conn, account_id) -> dict | None
# snapshot للحساب

snapshot_row(conn, table, record_id, id_col="id") -> dict | None
# snapshot عام لأي جدول وأي سجل
```

#### قراءة سجل التدقيق

```python
fetch_audit_log(conn, table_name=None, action=None,
                limit=200, offset=0) -> list
# يجلب سجلات الـ audit مع دعم فلترة وـ pagination
# كل صف يحتوي old_data_parsed (dict مُحلَّل من JSON)

fetch_audit_log_count(conn, table_name=None, action=None) -> int
# إجمالي عدد السجلات — للـ pagination

fetch_record_history(conn, table_name, record_id) -> list
# كل سجلات الـ audit لسجل معين — لعرض تاريخ التعديلات
```

---

## investors_repo

### `db/accounting/investors_repo.py`

#### ملاحظات هامة

- [إصلاح 30] نُقل من `db/inventory/` إلى `db/accounting/` لأن المستثمرين مرتبطون بـ `journal_entries`
- [إصلاح 31] `_migrate_investors` تُستدعى مرة واحدة per-connection باستخدام flag بمفتاح `db_path`
- [تحسين 7] `_get_db_path` تستخدم fast path لـ `ProtectedConnection` عبر `_path` مباشرة

#### CRUD — المستثمرون

```python
fetch_all_investors(conn) -> list
fetch_investor(conn, investor_id) -> row
insert_investor(conn, name, notes=None, joined_at=None) -> int
update_investor(conn, investor_id, name, notes=None, joined_at=None)
delete_investor(conn, investor_id)
investor_exists(conn, name) -> int | None   # يرجع id لو موجود
```

#### ربط المستثمر بالقيود

```python
link_investor_to_line(conn, investor_id, entry_id, line_id,
                       move_type, amount, notes=None) -> int
# move_type: 'capital' | 'drawings'

fetch_investor_entries(conn, investor_id, acc_conn=None) -> list
# يجيب حركات المستثمر مع بيانات القيود لو acc_conn متاح

fetch_entry_investor_links(conn, entry_id) -> list
# كل المستثمرين المرتبطين بقيد معين

delete_investor_link(conn, link_id)
delete_entry_investor_links(conn, entry_id)
```

#### تقارير

```python
calc_investor_summary(conn, investor_id, acc_conn=None) -> dict
# {investor_id, investor_name, joined_at, notes,
#  total_capital, total_drawings, net_investment, entries}

calc_all_investors_summary(conn, acc_conn=None) -> list
# [إصلاح 40] يجلب كل entries دفعة واحدة بدل query لكل مستثمر
# يُقلّص الـ queries من O(n×m) إلى O(1) + O(entries)
# مُرتّبة تنازلياً حسب net_investment
```

#### Cache invalidation

```python
invalidate_investors_migration_cache(conn=None)
# conn=None → يمسح كل الـ cache
# conn=<connection> → يمسح cache هذا الملف فقط
```

---

## accounting_repo (Facade)

### `db/accounting/accounting_repo.py`

Facade للتوافق مع الكود القديم — يُعيد تصدير كل الدوال من الملفات المقسّمة.

```python
from db.accounting.accounting_repo import (
    # accounts — [P-01] دوال جديدة مقسّمة
    fetch_all_accounts_basic,
    fetch_all_accounts_with_balance,
    # accounts — للتوافق مع الكود القديم
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

> ⚠️ `_get_group_descendants` **محذوفة** من الـ facade [تحسين 14] — هي private function.
> استوردها مباشرة من `accounting_accounts_repo` لو احتجتها.

---

## دوال مساعدة للـ UI

### `db/accounting/accounting_repo_ui_helpers.py`

```python
fetch_account_by_code(conn, code) -> row | None
# يجلب حساباً بالكود — للتحديد التلقائي في الـ UI

fetch_capital_line_for_entry(conn, entry_id) -> int
# يرجع id أول سطر دائن (CR) في قيد رأس المال، أو 0

fetch_drawings_line_for_entry(conn, entry_id) -> int
# يرجع id أول سطر مدين (DR) في قيد المسحوبات، أو 0

fetch_entry_by_ref(conn, ref_no) -> row | None
# يجلب قيداً برقمه المرجعي

fetch_investor_entry_id(erp_conn, link_id) -> int | None
# يجلب entry_id المرتبط بـ link_id من investor_entries
# يُستخدم قبل حذف قيد عند حذف حركة مستثمر
```

---

## ملاحظات

- الـ `accounting.db` منفصل تماماً عن `erp.db` — لا FOREIGN KEYS بينهما.
- الربط بالمخزون يتم عبر `ref_entry_id` في `inventory_moves` (بدون FK صريح).
- استخدم `_verify_conn_is_accounting()` من `accounting_schema_seed` للتحقق من أن الـ connection فعلاً على `accounting.db` وليس `erp.db`.
- `purchase_inventory` يحتاج **connection-ين** منفصلين: `inv_conn` لـ inventory و `acc_conn` لـ accounting.