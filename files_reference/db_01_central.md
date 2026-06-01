# دليل الكود — DB (1): قاعدة البيانات المركزية

> `companies.db` — الشركات، الحالة، العناصر المشتركة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [companies_schema](#companies_schema) | `db/companies/companies_schema.py` |
| [companies_repo](#companies_repo) | `db/companies/companies_repo.py` |
| [company_state](#company_state) | `db/companies/company_state.py` |
| [shared_items_repo](#shared_items_repo) | `db/companies/shared_items_repo.py` |

---

## companies_schema

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
# ثم يُطبّق _migrate_central()
```

---

## companies_repo

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

> ⚠️ **الدوال المحذوفة [T-01] — ImportError واضح:**
> - `fetch_all_shared_items` → استورد من `db.companies.shared_items_repo`
> - `fetch_shared_items_for_company` → استورد من `db.companies.shared_items_repo`

---

## company_state

### `db/companies/company_state.py`

#### `ProtectedConnection`

Wrapper على `sqlite3.Connection` يمنع الإغلاق العرضي ويعيد الاتصال تلقائياً.
يخزّن `_path` كـ instance attribute للقراءة السريعة بدون PRAGMA.

```python
ProtectedConnection(path: str)

conn.execute(sql, params=())
conn.executemany(sql, seq)
conn.executescript(script)
conn.commit() / conn.rollback()
conn.close()       # no-op
conn.real_close()  # الإغلاق الحقيقي
conn.path_matches(expected_path) -> bool  # مقارنة سريعة بدون PRAGMA
conn.validate(expected_path) -> bool       # تحقق صريح عبر PRAGMA
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
# [C-03] thread-safe عبر _invalidate_pending Event
company_state.clear()

company_state.get_erp_conn()         -> ProtectedConnection
company_state.get_accounting_conn()  -> ProtectedConnection
company_state.get_inventory_conn()   -> ProtectedConnection
company_state.get_orders_conn()      -> ProtectedConnection
company_state.get_designs_conn()     -> ProtectedConnection

company_state.wait_for_invalidate(timeout=1.0)
# [C-03] ينتظر انتهاء set_active() — للاستخدام من AppState
```

---

## shared_items_repo

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

## ملاحظات

- لا تُغلق `ProtectedConnection` مباشرة — اتركها للـ `company_state`. فقط `get_central_connection()` تحتاج `.close()`.
- `CompanyState.set_active()` آمن للـ threads عبر `_invalidate_pending` Event [C-03].
- `ProtectedConnection._path` يُتيح مقارنة سريعة بدون PRAGMA overhead.