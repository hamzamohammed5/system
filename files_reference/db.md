# دليل الكود — DB / قاعدة البيانات

> مرجع سريع لكل ملفات `db/` في النظام.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [DB — قاعدة البيانات المركزية](#db--قاعدة-البيانات-المركزية) | `companies_schema`, `companies_repo`, `company_state`, `shared_items_repo` |
| [DB — ERP (erp.db)](#db--erp) | `costing/schema`, `shared/items_repo`, `shared/categories_repo`, `shared/settings_repo` |
| [DB — المحاسبة](#db--المحاسبة) | `accounting_accounts_repo`, `accounting_journal_repo`, `accounting_statements_repo`, `accounting_inventory_repo`, `accounting_audit_repo`, `accounting_repo_ui_helpers`, `investors_repo` |
| [DB — المخزن](#db--المخزن) | `inventory_schema`, `inventory_repo` |
| [DB — الطلبات](#db--الطلبات) | `orders_schema`, `orders_repo`, `customers_repo` |
| [DB — التصميمات](#db--التصميمات) | `design_schema`, `designs_repo`, `designs_sizes_repo`, `dimension_sets_repo`, `design_item_categories_repo` |
| [DB — التكلفة](#db--التكلفة) | `bom_scenarios_repo`, `operations_repo`, `machine_op_rows_repo`, `raw_variants_repo` |
| [DB — التسعير](#db--التسعير) | `pricing_repo`, `offers_repo` |
| [DB — مشترك](#db--مشترك) | `shared/connection`, `shared/json_utils`, `shared/shared_items_bridge` |

---

## DB — قاعدة البيانات المركزية

### `db/companies/companies_schema.py`

**المسارات:**
- `CENTRAL_DB` — مسار `companies.db`
- `DATA_DIR` — مجلد بيانات الشركات

```python
get_central_connection() -> sqlite3.Connection
# يفتح اتصال بـ companies.db
# isolation_level=None, foreign_keys=ON, journal_mode=WAL

get_company_dir(company_id: int) -> str
get_company_db_path(company_id: int, db_name: str) -> str
# db_name: "erp" | "accounting" | "inventory" | "orders" | "designs"

ensure_company_dir(company_id: int) -> str

create_central_tables(conn)
# ينشئ: companies, shared_items, company_shared_links
# ثم يُطبق _migrate_central()
```

---

### `db/companies/companies_repo.py`

```python
fetch_all_companies(conn, active_only=False) -> list
# كل row: id, name, short_name, color, is_active, notes

fetch_company(conn, company_id: int)

insert_company(conn, name, short_name="", color="#1565c0", notes="") -> int
# ينشئ شركة + مجلدها + كل ملفات DB (erp, accounting, inventory, orders, designs)

update_company(conn, company_id, name, short_name="", color="#1565c0", notes="", is_active=1)

delete_company(conn, company_id) -> bool
# يحذف من companies.db فقط — الملفات تبقى على الديسك

toggle_company_active(conn, company_id)

publish_item_as_shared(central_conn, source_company_id, source_item_id,
                       shared_type, name, notes="") -> int
# shared_type: "raw" | "machine" | "labor_op" | "machine_op"

link_shared_item_to_company(central_conn, erp_conn, shared_item_id,
                             target_company_id) -> int

unlink_shared_item(central_conn, shared_item_id, company_id)
delete_shared_item(central_conn, shared_item_id)
sync_shared_item(central_conn, source_erp_conn, shared_item_id)  # no-op
```

---

### `db/companies/company_state.py`

#### `ProtectedConnection`

Wrapper على sqlite3.Connection يمنع الإغلاق العرضي ويعيد الاتصال تلقائياً.

```python
ProtectedConnection(path: str)

conn.execute(sql, params=())
conn.executemany(sql, seq)
conn.executescript(script)
conn.commit() / conn.rollback()
conn.close()       # no-op
conn.real_close()  # الإغلاق الحقيقي
conn.path_matches(expected_path) -> bool
conn.validate(expected_path) -> bool
```

#### `CompanyState` (Singleton)

```python
company_state = CompanyState()

# Properties
company_state.company_id    # int | None
company_state.company_name  # str
company_state.company_color # str
company_state.is_ready      # bool

# Methods
company_state.set_active(company_id, name="", color="#1565c0")
company_state.clear()

company_state.get_erp_conn() -> ProtectedConnection
company_state.get_accounting_conn() -> ProtectedConnection
company_state.get_inventory_conn() -> ProtectedConnection
company_state.get_orders_conn() -> ProtectedConnection
company_state.get_designs_conn() -> ProtectedConnection

company_state.wait_for_invalidate(timeout=1.0)
```

---

### `db/companies/shared_items_repo.py`

```python
create_shared_items_tables(conn)

fetch_all_shared_items(conn, shared_type=None) -> list
fetch_shared_item(conn, item_id) -> row
insert_shared_item(conn, name, shared_type, data=None) -> int
# data: dict — يُخزَّن كـ JSON
update_shared_item(conn, item_id, name, data: dict)
delete_shared_item(conn, item_id)

fetch_linked_companies(conn, shared_item_id) -> list
fetch_shared_items_for_company(conn, company_id, shared_type=None) -> list
is_company_linked(conn, shared_item_id, company_id) -> bool
link_company(conn, shared_item_id, company_id)
unlink_company(conn, shared_item_id, company_id)
set_linked_companies(conn, shared_item_id, company_ids: list)

get_item_data(conn, shared_item_id) -> dict
get_item_as_raw(conn, shared_item_id) -> dict | None
get_item_as_machine(conn, shared_item_id) -> dict | None
get_item_as_labor_op(conn, shared_item_id) -> dict | None
```

---

## DB — ERP

### `db/costing/schema.py`

```python
init_db()
# يُهيئ companies.db فقط الآن

_init_erp_db(conn)
# يُهيئ erp.db — ينشئ: categories, items, machines, labor_ops,
#   machine_ops, bom, settings
# القيم الافتراضية في settings:
#   monthly_salary=3000, working_days=25, holiday_days=4,
#   working_hours_day=8, overhead_factor=1.10, font_size=11
```

**جداول erp.db:**
- `categories(id, name, scope, color, parent_id, template_fields, default_unit)`
- `items(id, name, type["raw"|"semi"|"final"], price, total_qty, category_id)`
- `machines(id, name, rate_per_hour, rate_per_unit, category_id)`
- `labor_ops(id, name, minutes, category_id)`
- `machine_ops(id, machine_id, name, mode["time"|"unit"], value, category_id)`
- `bom(id, parent_id, child_type, child_id, qty, child_name, waste_pct?, variant_id?, machine_op_row_id?, scenario_id?)`
- `settings(key TEXT PK, value TEXT)`

---

### `db/shared/items_repo.py`

```python
# ── العناصر المشتركة ──
is_shared_id(item_id) -> bool
extract_shared_id(item_id) -> int | None
# "shared:42" → 42

# ── CRUD ──
fetch_all_items(conn) -> list
fetch_items_by_type(conn, item_type: str) -> list
fetch_items_by_type_with_shared(conn, item_type, company_id=None) -> list
# يدمج المحلي + المشترك من companies.db

fetch_item(conn, item_id) -> row | _SharedItemRow
# يدعم int أو "shared:{n}"

insert_item(conn, name, item_type, price=0, category_id=None, total_qty=None) -> int
update_item(conn, item_id, name, price, category_id=None, total_qty=None)
delete_item(conn, item_id)
update_item_category(conn, item_id, category_id)

# ── BOM ──
fetch_bom(conn, parent_id) -> list
insert_bom_row(conn, parent_id, child_type, child_id, qty,
               waste_pct=0.0, variant_id=None)
delete_bom_row(conn, parent_id, child_type, child_id)
replace_bom(conn, parent_id, rows: list[tuple])
# rows: [(child_type, child_id, qty, waste_pct, variant_id), ...]

fetch_orphan_bom_rows(conn, parent_id) -> list[dict]
delete_orphan_bom_rows(conn, parent_id) -> int
fetch_products_with_orphan(conn, child_type, child_id) -> list[int]

# ── Cache ──
invalidate_bom_cols_cache(conn=None)
invalidate_central_conn_cache()
```

---

### `db/shared/categories_repo.py`

```python
fetch_all_categories(conn, scope=None) -> list
fetch_categories_by_scope(conn, scope) -> list
fetch_category(conn, cat_id) -> row

fetch_descendants(conn, cat_id) -> list[int]
# CTE Recursive — O(1) query

insert_category(conn, name, scope="all", color="#607d8b", parent_id=None,
                template_fields=None, default_unit="mm") -> int

update_category(conn, cat_id, name, scope, color, parent_id=None,
                template_fields=None, default_unit="mm")
# يتحقق من circular reference تلقائياً

delete_category(conn, cat_id)
count_category_items(conn, cat_id) -> dict
# {"عناصر": n, "عمليات عمالة": n, "عمليات تشغيل": n, "ماكينات": n}

build_tree(rows) -> list[dict]
# قائمة مسطحة → شجرة هرمية
# كل node: {id, name, scope, color, parent_id, children:[...]}

get_template_fields(conn, cat_id) -> list[dict]
set_template_fields(conn, cat_id, fields: list[dict])
apply_template_to_dimension_set(conn_erp, conn_design, cat_id, set_id) -> int
```

**الـ scopes المتاحة:** `all | raw | semi | final | labor | machine | pricing | design`

---

### `db/shared/settings_repo.py`

```python
get_setting(conn, key: str, default=None) -> str | None
set_setting(conn, key: str, value)
```

---

## DB — المحاسبة

**جداول accounting.db:**
- `accounts(id, code TEXT UNIQUE, name, type, subtype, parent_id, is_leaf, group_id, notes)`
- `account_groups(id, name, acc_type, parent_id, color, notes)`
- `journal_entries(id, ref_no UNIQUE, date, description, type, status, ref_id, ref_type, notes)`
- `journal_lines(id, entry_id→CASCADE, account_id, debit, credit, description)`
- `audit_log(id, action, table_name, record_id, old_data JSON, changed_by, created_at)`

**أنواع الحسابات:** `asset | liability | capital | revenue | expense | drawings`  
**أنواع القيود:** `manual | purchase | sale | payment | receipt | adjustment`  
**حالات القيود:** `draft | posted | reversed`

---

### `db/accounting/accounting_accounts_repo.py`

```python
# ── قراءة ──
fetch_all_accounts_basic(conn, acc_type=None) -> list      # بدون أرصدة
fetch_all_accounts_with_balance(conn, acc_type=None) -> list  # مع balance
fetch_all_accounts(conn, acc_type=None) -> list            # = with_balance
fetch_account(conn, account_id) -> row
fetch_account_by_code(conn, code: str) -> row | None
fetch_leaf_accounts(conn, acc_type=None) -> list           # is_leaf=1

get_account_balance(conn, account_id) -> float             # SUM(debit) - SUM(credit)
get_account_natural_balance(conn, account_id) -> float
get_normal_balance(acc_type: str) -> str                   # "dr" | "cr"
calc_signed_amount(acc_type, increase: bool, amount) -> tuple  # (debit, credit)
get_balances_by_type(conn) -> dict                         # {type: {debit, credit, balance}}

# ── كتابة ──
insert_account(conn, code, name, acc_type, parent_id=None, group_id=None,
               subtype=None, notes=None) -> int
update_account(conn, account_id, name, group_id=None, notes=None)
delete_account(conn, account_id)

# ── تصنيفات الحسابات ──
fetch_all_groups(conn, acc_type=None) -> list
fetch_group(conn, group_id) -> row
insert_group(conn, name, acc_type, parent_id=None, color="#607d8b") -> int
update_group(conn, group_id, name, parent_id=None, color="#607d8b")
delete_group(conn, group_id)
build_group_tree(rows) -> list[dict]
```

---

### `db/accounting/accounting_journal_repo.py`

```python
next_ref_no(conn) -> str
# "JE-00001", "JE-00002", ...

# ── قراءة ──
fetch_all_entries(conn, limit=200) -> list
fetch_entries_count(conn) -> int
fetch_all_entries_paginated(conn, limit=200, offset=0,
                            date_from=None, date_to=None,
                            search=None, entry_type=None) -> list
fetch_entry(conn, entry_id) -> row
fetch_entry_lines(conn, entry_id) -> list
# كل row: id, account_id, debit, credit, description,
#         account_code, account_name, account_type

fetch_t_account(conn, account_id) -> dict
# {account, lines, total_debit, total_credit, balance, normal_balance}

# ── كتابة ──
insert_entry(conn, date, description, entry_type="manual",
             notes=None, ref_id=None, ref_type=None) -> int

add_entry_lines(conn, entry_id, lines: list)
# lines: [{"account_id", "debit", "credit", "description"}, ...]

delete_entry(conn, entry_id, changed_by="system")
# snapshot → audit_log → حذف

validate_entry_balance(lines: list) -> bool
```

---

### `db/accounting/accounting_statements_repo.py`

```python
trial_balance(conn) -> list
# كل row: code, name, type, total_debit, total_credit, balance

income_statement(conn) -> dict
# {revenues, expenses, total_rev, total_exp, net_income}

balance_sheet(conn) -> dict
# {assets, liabilities, capital, drawings, net_income,
#  total_assets, total_liab, total_equity}

owners_equity_statement(conn) -> dict
# {capital_accounts, drawings_accounts, net_income,
#  total_capital, total_drawings, total_equity}
```

---

### `db/accounting/accounting_inventory_repo.py`

```python
purchase_inventory(inv_conn, acc_conn, inv_id, qty, unit_cost, date,
                   payment_account_id, notes=None, changed_by="system") -> tuple
# يسجل شراء مخزن + قيد محاسبي تلقائي
# Returns: (entry_id, move_id)
# Raises: ValueError | RuntimeError
```

---

### `db/accounting/accounting_audit_repo.py`

```python
create_audit_log_table(conn)

log_action(conn, action, table_name, record_id=None,
           old_data=None, changed_by="system") -> int | None
# action: "delete" | "update" | "create"

log_delete(conn, table_name, record_id, old_data=None, changed_by="system")
log_update(conn, table_name, record_id, old_data=None, changed_by="system")
log_create(conn, table_name, record_id, data=None, changed_by="system")

snapshot_journal_entry(conn, entry_id) -> dict | None
# {entry: {...}, lines: [...]}
snapshot_account(conn, account_id) -> dict | None
snapshot_row(conn, table, record_id, id_col="id") -> dict | None

fetch_audit_log(conn, table_name=None, action=None,
                limit=200, offset=0) -> list
fetch_audit_log_count(conn, table_name=None, action=None) -> int
fetch_record_history(conn, table_name, record_id) -> list
```

---

### `db/accounting/accounting_repo_ui_helpers.py`

```python
fetch_account_by_code(conn, code: str) -> row | None
fetch_capital_line_for_entry(conn, entry_id) -> int   # id أول سطر CR أو 0
fetch_drawings_line_for_entry(conn, entry_id) -> int  # id أول سطر DR أو 0
fetch_entry_by_ref(conn, ref_no: str) -> row | None
fetch_investor_entry_id(erp_conn, link_id) -> int | None
```

---

### `db/accounting/investors_repo.py`

```python
# ── CRUD ──
fetch_all_investors(conn) -> list
fetch_investor(conn, investor_id) -> row
insert_investor(conn, name, notes=None, joined_at=None) -> int
update_investor(conn, investor_id, name, notes=None, joined_at=None)
delete_investor(conn, investor_id)
investor_exists(conn, name) -> int | None

# ── ربط بالقيود ──
link_investor_to_line(conn, investor_id, entry_id, line_id,
                      move_type, amount, notes=None) -> int
# move_type: "capital" | "drawings"

fetch_investor_entries(conn, investor_id, acc_conn=None) -> list
fetch_entry_investor_links(conn, entry_id) -> list
delete_investor_link(conn, link_id)
delete_entry_investor_links(conn, entry_id)

# ── تقارير ──
calc_investor_summary(conn, investor_id, acc_conn=None) -> dict
# {investor_id, investor_name, total_capital, total_drawings,
#  net_investment, entries}

calc_all_investors_summary(conn, acc_conn=None) -> list
# batch query — O(1)
```

---

## DB — المخزن

**جداول inventory.db:**
- `inventory_categories(id, name, color, notes)`
- `inventory_items(id, name, unit, category_id, qty_on_hand, qty_min, avg_cost, costing_item_id, account_code, notes)`
- `inventory_moves(id, inventory_id→CASCADE, move_type["in"|"out"|"adjust"], qty, unit_cost, total_cost, date, ref_entry_id, ref_entry_no, notes)`

### `db/inventory/inventory_repo.py`

```python
# ── تصنيفات ──
fetch_all_inv_categories(conn) -> list
insert_inv_category(conn, name, color="#607d8b", notes=None) -> int
delete_inv_category(conn, cat_id)

# ── أصناف ──
fetch_all_inventory(conn) -> list         # مع total_value = qty × avg_cost
fetch_inventory_item(conn, inv_id) -> row
insert_inventory_item(conn, name, unit="قطعة", qty_min=0,
                      account_code="114", category_id=None,
                      costing_item_id=None, notes=None) -> int
update_inventory_item(conn, inv_id, name, unit, qty_min,
                      account_code="114", category_id=None, notes=None)
delete_inventory_item(conn, inv_id)

# ── حركات ──
fetch_inventory_moves(conn, inv_id) -> list
fetch_recent_moves(conn, move_type=None, limit=100) -> list

record_inventory_move(conn, inv_id, move_type, qty, unit_cost, date,
                      notes=None, ref_entry_id=None, ref_entry_no=None) -> int
# move_type: "in" | "out" | "adjust"
# "in":     يحسب avg_cost الجديد بـ WACC
# "out":    يتحقق من الكمية الكافية
# "adjust": يضع qty مباشرة
# Raises: ValueError لو qty أكبر من الرصيد في out
```

---

## DB — الطلبات

**جداول orders.db:**
- `customers(id, code UNIQUE, name, customer_type["individual"|"company"], phone, phone2, email, address, city, notes, is_active)`
- `customer_contacts(id, customer_id→CASCADE, name, role, phone, email, notes)`
- `orders(id, order_number UNIQUE, customer_id→RESTRICT, order_type, status, priority, order_date, due_date, total_amount, discount, net_amount, paid_amount, notes, internal_notes)`
- `order_items(id, order_id→CASCADE, item_name, quantity, unit, unit_price, discount_pct, total_price, sort_order, ...)`
- `order_status_log(id, order_id→CASCADE, old_status, new_status, notes, changed_by, changed_at)`

**حالات الطلب:** `pending → confirmed → in_progress → ready → delivered` (مع `cancelled`, `on_hold`)

### `db/orders/customers_repo.py`

```python
fetch_all_customers(conn, active_only=False) -> list   # مع orders_count
fetch_customer(conn, customer_id) -> row
search_customers(conn, query, limit=20) -> list
fetch_customer_stats(conn, customer_id) -> dict
# {total_orders, delivered, cancelled, active, total_value, total_paid, last_order_date}

insert_customer(conn, name, customer_type="individual", phone="",
                phone2="", email="", address="", city="", notes="") -> int
# يولد code تلقائياً: "CUS-0001"

update_customer(conn, customer_id, name, ..., is_active=1)
delete_customer(conn, customer_id) -> bool   # يرفض لو في طلبات مرتبطة
toggle_customer_active(conn, customer_id)

fetch_contacts(conn, customer_id) -> list
insert_contact(conn, customer_id, name, role="", phone="", email="", notes="") -> int
update_contact(conn, contact_id, name, ...)
delete_contact(conn, contact_id)
```

---

### `db/orders/orders_repo.py`

```python
# ── قراءة ──
fetch_all_orders(conn, status=None, customer_id=None, order_type=None,
                 date_from=None, date_to=None, search=None) -> list
fetch_order(conn, order_id) -> row
fetch_customer_orders(conn, customer_id) -> list

# ── كتابة ──
insert_order(conn, customer_id, order_type="new", status="pending",
             priority="normal", order_date=None, due_date=None,
             total_amount=0, discount=0, paid_amount=0,
             notes="", internal_notes="", reference_order=None,
             created_by="system") -> int
# يتحقق من وجود العميل وكونه نشطاً
# يولد order_number: "ORD-YYYY-0001"

update_order(conn, order_id, priority="normal", due_date=None,
             total_amount=0, discount=0, paid_amount=0, notes="",
             internal_notes="", customer_id=None, changed_by="system") -> bool

change_order_status(conn, order_id, new_status, notes="", changed_by="system") -> bool
cancel_order(conn, order_id, reason="", changed_by="system") -> bool
reorder(conn, original_order_id, notes="", created_by="system") -> int
# ينسخ الطلب القديم كطلب جديد من نوع "reorder"

delete_order(conn, order_id) -> bool
# يرفض لو status ليس pending/cancelled أو paid_amount > 0

# ── بنود الطلب ──
fetch_order_items(conn, order_id) -> list
insert_order_item(conn, order_id, item_name, description="",
                  quantity=1, unit="قطعة", unit_price=0,
                  discount_pct=0, design_ref="", notes="",
                  sort_order=None) -> int
update_order_item(conn, item_id, item_name, ...)
delete_order_item(conn, item_id)

# ── سجل الحالة ──
fetch_status_log(conn, order_id) -> list
fetch_orders_summary(conn) -> dict
# {total, pending, confirmed, in_progress, ready, delivered,
#  cancelled, urgent, total_value, total_paid}
```

---

## DB — التصميمات

**جداول designs.db:**
- `design_categories(id, name, color, parent_id, notes)`
- `design_item_categories(id, name, color, parent_id, notes)`
- `dimension_sets(id, name, category_id, default_unit, notes)`
- `dimension_fields(id, set_id→CASCADE, name, label, unit, field_type["number"|"text"], required, sort_order)`
- `dimension_field_deps(id, field_id UNIQUE, source_field_id, source_set_id, offset, notes)`
- `dimension_set_instances(id, set_id→CASCADE, name, sort_order, notes)`
- `dimension_set_values(id, set_id, field_id, instance_id→CASCADE, value_num, value_text, UNIQUE(instance_id,field_id))`
- `designs(id, name, category_id, item_category_id, notes, preview_image, created_at, updated_at)`
- `design_sizes(id, design_id→CASCADE, set_id, instance_id, width_field_id, height_field_id, dpi_field_id, xcf_path, notes, sort_order, UNIQUE(design_id,instance_id))`

### `db/designs/designs_repo.py`

```python
fetch_all_designs(conn, category_id=None, set_id=None, name_q="") -> list
fetch_design(conn, design_id) -> row
insert_design(conn, name, item_category_id=None, notes="") -> int
update_design(conn, design_id, name, item_category_id=None, notes="")
delete_design(conn, design_id)

fetch_design_links_for_design(conn, design_id) -> list
fetch_dim_values(conn, link_id) -> dict
set_dim_value(conn, link_id, field_id, value_num=None, value_text=None, is_auto=False)
save_all_dim_values(conn, link_id, values: dict, auto_flags: dict = None)
recalc_auto_values(conn, link_id) -> dict[int, float]
fetch_full_design_data(conn, design_id) -> dict
# {id, name, category_name, notes, links: [{link_id, set_name, label, unit, fields: [...]}]}
```

---

### `db/designs/designs_sizes_repo.py`

```python
fetch_design_sizes(conn, design_id) -> list
fetch_design_size(conn, size_id) -> row
insert_design_size(conn, design_id, set_id, instance_id,
                   width_field_id=None, height_field_id=None,
                   xcf_path=None, notes="", sort_order=None,
                   dpi_field_id=None) -> int
update_design_size(conn, size_id, width_field_id=None, height_field_id=None,
                   xcf_path=None, notes="", dpi_field_id=None)
update_design_size_path(conn, size_id, xcf_path)
delete_design_size(conn, size_id)

fetch_canvas_size(conn, size_id) -> tuple[float|None, float|None]
fetch_canvas_dpi(conn, size_id) -> float | None
fetch_instances_for_set_with_values(conn, set_id) -> list
instance_already_used(conn, design_id, instance_id, exclude_size_id=None) -> bool
fetch_all_designs_summary(conn) -> list
```

---

### `db/designs/dimension_sets_repo.py` (Facade)

```python
# ── مجموعات المقاسات ──
fetch_all_dimension_sets(conn) -> list
fetch_dimension_set(conn, set_id) -> row
insert_dimension_set(conn, name, category_id=None, default_unit="cm", notes="") -> int
update_dimension_set(conn, set_id, name, category_id=None, default_unit="cm", notes="")
delete_dimension_set(conn, set_id)

# ── حقول المجموعة ──
fetch_fields_for_set(conn, set_id) -> list
fetch_all_fields_for_combo(conn, exclude_field_id=None) -> list
fetch_field(conn, field_id) -> row
insert_field(conn, set_id, name, label, unit="cm", field_type="number",
             required=True, sort_order=0) -> int
update_field(conn, field_id, name, label, unit="cm", field_type="number",
             required=True, sort_order=0)
delete_field(conn, field_id)
reorder_fields(conn, set_id, field_ids: list)

# ── اعتماديات الحقول ──
fetch_field_dep(conn, field_id) -> row | None
set_field_dep(conn, field_id, source_field_id, offset=0.0,
              notes="", source_set_id=None)
remove_field_dep(conn, field_id)
calc_auto_value(conn, field_id, link_id) -> float | None

# ── تصنيفات (re-export) ──
fetch_all_design_categories(conn) -> list
insert_design_category(conn, name, color="#1565c0", parent_id=None, notes="") -> int
update_design_category(conn, cat_id, name, color, parent_id=None, notes="")
delete_design_category(conn, cat_id)
build_category_tree(rows) -> list

# ── instances (re-export) ──
fetch_instances_for_set(conn, set_id) -> list
fetch_instance(conn, instance_id) -> row
insert_instance(conn, set_id, name="", notes="", sort_order=None) -> int
update_instance(conn, instance_id, name, notes="")
delete_instance(conn, instance_id)
duplicate_instance(conn, instance_id, new_name) -> int | None
fetch_instance_values(conn, instance_id) -> dict
save_instance_values(conn, instance_id, set_id, values: dict)
calc_instance_cross_auto(conn, field_id, instance_id) -> float | None
```

---

### `db/designs/design_item_categories_repo.py`

```python
fetch_all_item_categories(conn) -> list
fetch_all_item_categories_with_count(conn) -> list
fetch_item_category(conn, cat_id) -> row
fetch_item_category_descendants(conn, cat_id) -> list[int]
insert_item_category(conn, name, color="#7c3aed", parent_id=None, notes="") -> int
update_item_category(conn, cat_id, name, color, parent_id=None, notes="")
delete_item_category(conn, cat_id)
build_item_category_tree(rows) -> list[dict]
count_designs_per_category(conn) -> dict[int, int]
```

---

## DB — التكلفة

**جداول إضافية في erp.db:**
- `bom_scenarios(id, item_id→CASCADE, name, is_default, notes)`
- `machine_op_rows(id, op_id→machine_ops, label, value, count, sort_order)`
- `raw_variants(id, item_id→items CASCADE, name, pieces>0, notes)`

### `db/costing/bom_scenarios_repo.py`

```python
# ── السيناريوهات ──
fetch_scenarios(conn, item_id) -> list
fetch_scenario(conn, scenario_id) -> row
fetch_default_scenario(conn, item_id) -> row | None
insert_scenario(conn, item_id, name, is_default=False, notes="") -> int
update_scenario(conn, scenario_id, name, notes="")
set_default_scenario(conn, scenario_id)
delete_scenario(conn, scenario_id) -> bool  # يرفض لو آخر سيناريو
clone_scenario(conn, scenario_id, new_name) -> int

# ── BOM للسيناريو ──
fetch_bom_for_scenario(conn, scenario_id) -> list
replace_bom_for_scenario(conn, scenario_id, rows)
# rows: [(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id), ...]

invalidate_bom_cols_cache(conn=None)
```

---

### `db/costing/operations_repo.py`

```python
# ── الماكينات ──
fetch_all_machines(conn) -> list
fetch_machine(conn, machine_id) -> row
insert_machine(conn, name, rate_per_hour, rate_per_unit, category_id=None) -> int
update_machine(conn, machine_id, name, rate_per_hour, rate_per_unit, category_id=None)
count_machine_ops(conn, machine_id) -> int
delete_machine(conn, machine_id)  # CASCADE على machine_ops

# ── عمليات العمالة ──
fetch_all_labor_ops(conn) -> list
fetch_labor_op(conn, op_id) -> row
insert_labor_op(conn, name, minutes, category_id=None) -> int
update_labor_op(conn, op_id, name, minutes, category_id=None)
delete_labor_op(conn, op_id)

# ── عمليات التشغيل ──
fetch_all_machine_ops(conn) -> list
fetch_machine_op(conn, op_id) -> row
insert_machine_op(conn, machine_id, name, mode, value, category_id=None) -> int
# mode: "time" | "unit"
update_machine_op(conn, op_id, machine_id, name, mode, value, category_id=None)
delete_machine_op(conn, op_id)
```

---

### `db/costing/machine_op_rows_repo.py`

```python
fetch_op_rows(conn, op_id) -> list
fetch_op_row(conn, row_id) -> row
insert_op_row(conn, op_id, label="", value=0.0, count=1.0, sort_order=0) -> int
update_op_row(conn, row_id, label, value, count, sort_order=0)
delete_op_row(conn, row_id)
replace_op_rows(conn, op_id, rows: list[tuple])
# rows: [(label, value, count), ...]

calc_op_row_cost(conn, row_id) -> float
# mode="time": (value/60) × rate_per_hour
# mode="unit": value × rate_per_unit

calc_op_total_cost(conn, op_id) -> float
```

---

### `db/costing/raw_variants_repo.py`

```python
fetch_variants_for_item(conn, item_id) -> list
fetch_variant(conn, variant_id) -> row
insert_variant(conn, item_id, name, pieces, notes=None) -> int
update_variant(conn, variant_id, name, pieces, notes=None)
delete_variant(conn, variant_id)

calc_unit_cost_with_variant(item_row, variant_id, conn) -> float
# الأولوية: variant → price÷pieces | total_qty → price÷total_qty | price مباشرة
```

---

## DB — التسعير

**جداول في erp.db:**
- `pricing(id, item_id UNIQUE, margin, price)`

### `db/pricing/pricing_repo.py`

```python
fetch_all_pricing(conn, limit=500, offset=0) -> list
fetch_pricing_count(conn) -> int
fetch_all_pricing_paginated(conn, limit=200, offset=0,
                            category_id=None, search=None,
                            only_priced=False) -> list
fetch_pricing(conn, item_id) -> row | None

upsert_pricing(conn, item_id, margin, price)
# يتحقق أن item_id نوعه "final"
# Raises: ValueError لو غير موجود أو نوعه ليس final

delete_pricing(conn, item_id)
```

---

### `db/pricing/offers_repo.py`

```python
fetch_all_offers(conn) -> list
fetch_offer(conn, offer_id) -> row
insert_offer(conn, name, discount, notes="", category_id=None) -> int
update_offer(conn, offer_id, name, discount, notes="", category_id=None)
delete_offer(conn, offer_id)

fetch_offer_items(conn, offer_id) -> list
replace_offer_items(conn, offer_id, items: list[tuple])
# items: [(item_id, qty), ...]

calc_offer_summary(conn, offer_id) -> dict
# {offer_id, offer_name, discount, lines: [...], total_listed, sell_price,
#  total_cost, profit}
# كل line: {item_id, item_name, qty, unit_cost, unit_price,
#           line_cost, line_listed, has_pricing}
```

---

## DB — مشترك

### `db/shared/connection.py`

```python
get_central_connection() -> sqlite3.Connection

get_connection(db="erp") -> ProtectedConnection
# db: "erp" | "accounting" | "inventory" | "orders" | "designs"
# ⚠️ يرمي RuntimeError لو لا توجد شركة نشطة
# ⚠️ "costing" مُهمَل — استخدم "erp"

get_accounting_connection() -> ProtectedConnection
get_inventory_connection() -> ProtectedConnection

get_linked_connection(primary="inventory", attach=None) -> Connection
# connection مع ATTACH لـ DBs إضافية للـ JOIN
```

---

### `db/shared/json_utils.py`

```python
decode_json(data_str: str) -> dict        # JSON → dict | {} عند الفشل
encode_json(data: dict) -> str            # dict → JSON | "{}"
decode_json_list(data_str: str) -> list   # JSON → list | []
encode_json_list(data: list) -> str       # list → JSON | "[]"
```

---

### `db/shared/shared_items_bridge.py`

```python
SharedItemsBridge(company_id: int)

bridge.fetch_shared_items_for_type(shared_type) -> list
bridge.fetch_items_by_type_with_shared(item_type) -> list
bridge.fetch_shared_item_as_row(shared_item_id, shared_type=None) -> dict | None
bridge.update_shared_item(shared_item_id, name, data: dict)
bridge.link_shared_item(shared_item_id)
bridge.unlink_shared_item(shared_item_id)
bridge.is_linked(shared_item_id) -> bool
bridge.batch_link(shared_item_ids: list)
bridge.batch_unlink(shared_item_ids: list)
bridge.calc_shared_raw_unit_price(shared_item_id) -> float

get_bridge() -> SharedItemsBridge | None

# re-exports:
is_shared_id(item_id) -> bool
extract_shared_id(item_id) -> int | None
```

---

## ملاحظات مهمة

**1. ترتيب الإنشاء:** `categories` يجب أن يُنشأ أولاً في schema.

**2. العناصر المشتركة:** IDs بصيغة `"shared:{n}"` (string) — تحقق دائماً بـ `is_shared_id()`.

**3. الـ connections:** لا تُغلق `ProtectedConnection` مباشرة — اتركها للـ `company_state`. فقط `get_central_connection()` تحتاج `.close()`.

**4. BOM columns cache:** استدعي `invalidate_bom_cols_cache(conn)` بعد أي migration يضيف أعمدة لجدول bom.

**5. SQLite type affinity:** جدول `settings` يخزن كل القيم كـ TEXT — استخدم `float(get_setting(...))` عند الحاجة.

**6. الـ accounting.db:** تحقق من `_verify_conn_is_accounting()` قبل أي seed أو write لتجنب الكتابة على erp.db بالخطأ.

**7. الـ WACC:** حساب `avg_cost` في المخزن تلقائي في `record_inventory_move()` — لا تحسبه يدوياً.