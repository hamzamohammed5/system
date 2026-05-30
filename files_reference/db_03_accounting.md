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

---

## accounting_schema_constants

### `db/accounting/accounting_schema_constants.py`

```python
TYPE_AR      # {"asset": "أصول", "liability": "خصوم", ...}
EQUITY_TYPES # {"capital", "drawings", "revenue", "expense"}
TYPE_GROUP   # {"asset": "asset", "capital": "equity", ...}
GROUP_AR     # {"asset": "الأصول", "liability": "الخصوم", "equity": "حقوق الملكية"}
NORMAL_BALANCE # {"asset": "dr", "expense": "dr", ..., "liability": "cr", "capital": "cr"}
```

---

## accounting_schema_seed

### `db/accounting/accounting_schema_seed.py`

```python
seed_default_accounts(conn)
# يُضيف شجرة الحسابات الافتراضية لو لم تكن موجودة

_verify_conn_is_accounting(conn)
# يتحقق من أن الـ connection فعلاً على accounting.db وليس erp.db
# يُستدعى قبل أي seed أو write حساس [إصلاح 9 + 11 + Q-01]
```

> ⚠️ استخدم `_verify_conn_is_accounting()` قبل أي عملية كتابة على `accounting.db` لتجنب الكتابة على `erp.db` بالخطأ.

---

## accounting_accounts_repo

### `db/accounting/accounting_accounts_repo.py`

#### قراءة الحسابات

```python
# [P-01] دالتان مقسّمتان حسب الاحتياج:
fetch_all_accounts_basic(conn, acc_type=None) -> list
# بدون balance — سريعة للـ dropdowns والـ combos

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
get_account_natural_balance(conn, account_id) -> float
get_normal_balance(acc_type: str) -> str
# "dr" لـ asset/expense/drawings | "cr" لـ liability/capital/revenue

calc_signed_amount(acc_type, increase, amount) -> tuple[float, float]
# يرجع (debit, credit)
get_balances_by_type(conn) -> dict
```

#### تصنيفات الحسابات (account_groups)

```python
fetch_all_groups(conn, acc_type=None) -> list
fetch_group(conn, group_id) -> row
insert_group(conn, name, acc_type, parent_id=None, color="#607d8b") -> int
update_group(conn, group_id, name, parent_id=None, color="#607d8b")
delete_group(conn, group_id)
build_group_tree(rows) -> list
```

> ⚠️ `_get_group_descendants` دالة private — استوردها مباشرة من `accounting_accounts_repo` لو احتجتها.

---

## accounting_journal_repo

### `db/accounting/accounting_journal_repo.py`

#### رقم القيد التلقائي

```python
next_ref_no(conn) -> str   # "JE-00001", "JE-00002", ...
```

#### قراءة القيود

```python
fetch_all_entries(conn, limit=200) -> list
fetch_entries_count(conn) -> int
fetch_all_entries_paginated(conn, limit=200, offset=0,
                             date_from=None, date_to=None,
                             search=None, entry_type=None) -> list
fetch_entry(conn, entry_id) -> row | None
fetch_entry_lines(conn, entry_id) -> list
```

#### كتابة القيود

```python
insert_entry(conn, date, description, entry_type="manual",
             notes=None, ref_id=None, ref_type=None) -> int
add_entry_lines(conn, entry_id, lines: list)
# lines: [{"account_id", "debit", "credit", "description"}, ...]
delete_entry(conn, entry_id, changed_by="system")
validate_entry_balance(lines: list) -> bool
```

#### دفتر الأستاذ

```python
fetch_t_account(conn, account_id) -> dict
# {account, lines, total_debit, total_credit, balance, normal_balance}
```

---

## accounting_statements_repo

### `db/accounting/accounting_statements_repo.py`

```python
trial_balance(conn) -> list
income_statement(conn) -> dict
balance_sheet(conn) -> dict
owners_equity_statement(conn) -> dict
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
1. ينشئ قيد محاسبي في `accounting.db`
2. يسجل حركة وارد في `inventory.db`

**[إصلاح 32] Rollback محصّن:** لو فشل `record_inventory_move` → يحذف القيد تلقائياً.

**Raises:** `ValueError` | `RuntimeError` (فشل الـ rollback)

---

## accounting_audit_repo

### `db/accounting/accounting_audit_repo.py`

```python
create_audit_log_table(conn)

log_action(conn, action, table_name, record_id=None,
           old_data=None, changed_by="system") -> int | None
log_delete(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_update(conn, table_name, record_id, old_data=None, changed_by="system") -> int | None
log_create(conn, table_name, record_id, data=None, changed_by="system") -> int | None

snapshot_journal_entry(conn, entry_id) -> dict | None
snapshot_account(conn, account_id) -> dict | None
snapshot_row(conn, table, record_id, id_col="id") -> dict | None

fetch_audit_log(conn, table_name=None, action=None,
                limit=200, offset=0) -> list
fetch_audit_log_count(conn, table_name=None, action=None) -> int
fetch_record_history(conn, table_name, record_id) -> list
```

---

## investors_repo

### `db/accounting/investors_repo.py`

#### CRUD — المستثمرون

```python
fetch_all_investors(conn) -> list
fetch_investor(conn, investor_id) -> row
insert_investor(conn, name, notes=None, joined_at=None) -> int
update_investor(conn, investor_id, name, notes=None, joined_at=None)
delete_investor(conn, investor_id)
investor_exists(conn, name) -> int | None
```

#### ربط المستثمر بالقيود

```python
link_investor_to_line(conn, investor_id, entry_id, line_id,
                       move_type, amount, notes=None) -> int
# move_type: 'capital' | 'drawings'

fetch_investor_entries(conn, investor_id, acc_conn=None) -> list
fetch_entry_investor_links(conn, entry_id) -> list
delete_investor_link(conn, link_id)
delete_entry_investor_links(conn, entry_id)
```

#### تقارير

```python
calc_investor_summary(conn, investor_id, acc_conn=None) -> dict
calc_all_investors_summary(conn, acc_conn=None) -> list
# [إصلاح 40] O(1) + O(entries) بدل O(n×m)
```

#### Cache invalidation

```python
invalidate_investors_migration_cache(conn=None)
```

---

## accounting_repo (Facade)

### `db/accounting/accounting_repo.py`

Facade للتوافق مع الكود القديم — يُعيد تصدير كل الدوال من الملفات المقسّمة.

```python
from db.accounting.accounting_repo import (
    fetch_all_accounts_basic, fetch_all_accounts_with_balance,
    fetch_all_accounts, fetch_account, fetch_account_by_code,
    fetch_leaf_accounts, insert_account, update_account, delete_account,
    get_account_balance, get_account_natural_balance, get_normal_balance,
    calc_signed_amount, get_balances_by_type,
    fetch_all_groups, fetch_group, insert_group, update_group,
    delete_group, build_group_tree,
    next_ref_no, fetch_all_entries, fetch_entries_count,
    fetch_all_entries_paginated,
    fetch_entry, fetch_entry_lines,
    insert_entry, add_entry_lines, delete_entry, validate_entry_balance,
    fetch_t_account,
    trial_balance, income_statement, balance_sheet, owners_equity_statement,
    purchase_inventory,
    create_audit_log_table,
    log_action, log_delete, log_update, log_create,
    snapshot_journal_entry, snapshot_account, snapshot_row,
    fetch_audit_log, fetch_audit_log_count, fetch_record_history,
)
```

> ⚠️ `_get_group_descendants` **محذوفة** من الـ facade [تحسين 14].

---

## accounting_repo_ui_helpers

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
```

---

## ملاحظات

- الـ `accounting.db` منفصل تماماً عن `erp.db` — لا FOREIGN KEYS بينهما.
- استخدم `_verify_conn_is_accounting()` للتحقق من صحة الـ connection قبل الكتابة.
- `purchase_inventory` يحتاج **connection-ين** منفصلين: `inv_conn` لـ inventory و `acc_conn` لـ accounting.