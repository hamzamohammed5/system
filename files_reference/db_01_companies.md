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
- `CENTRAL_DB` — مسار `companies.db` (3 مستويات فوق الملف)
- `DATA_DIR` — مجلد `company_data` بجانب `companies.db`

```python
get_central_connection() -> sqlite3.Connection
# isolation_level=None, foreign_keys=ON, journal_mode=WAL

get_company_dir(company_id: int) -> str
get_company_db_path(company_id: int, db_name: str) -> str
# db_name: "erp" | "accounting" | "inventory" | "orders" | "designs"

ensure_company_dir(company_id: int) -> str
# يُنشئ المجلد بـ os.makedirs(exist_ok=True)

create_central_tables(conn)
# ينشئ: companies, shared_items, company_shared_links
# ثم يُطبّق _migrate_central()
```

**Migration آمن — `_migrate_central(conn)`:**
يتعامل مع قواعد البيانات القديمة التي كان فيها `source_company_id` بدل `data` JSON.

**`_migrate_old_shared_items(conn)` — [إصلاح 19 v2]:**
```python
# بنية try/finally مزدوجة لضمان إعادة تفعيل PRAGMA foreign_keys = ON
# fk_disabled flag يتتبع هل أوقفنا FK فعلاً
# الـ finally الخارجي مسؤول فقط عن PRAGMA foreign_keys = ON
# لو فشل إعادة تفعيل FK → يُسجَّل CRITICAL log
```

**مساعدات داخلية:**
```python
_col_exists(conn, table, col) -> bool
_table_exists(conn, table) -> bool
```

---

## companies_repo

### `db/companies/companies_repo.py`

```python
fetch_all_companies(conn, active_only=False) -> list
# كل row: id, name, short_name, logo_path, color, is_active, notes, created_at, updated_at

fetch_company(conn, company_id: int) -> row

insert_company(conn, name, short_name="", color="#1565c0", notes="") -> int
# ينشئ شركة + ensure_company_dir() + _init_company_databases()
# يُهيئ: erp.db, accounting.db, inventory.db, orders.db, designs.db

update_company(conn, company_id, name, short_name="", color="#1565c0",
               notes="", is_active=1)
# updated_at=datetime('now') تلقائياً

delete_company(conn, company_id) -> bool
# يحذف من companies.db فقط — الملفات تبقى على الديسك للأمان

toggle_company_active(conn, company_id)
# 1 - is_active (toggle)
```

#### تهيئة قواعد بيانات الشركة

```python
_init_company_databases(company_id: int)
# connections مؤقتة تُغلق في finally لكل DB
# erp        → _init_erp_db(conn)
# accounting → create_accounting_tables(conn)
# inventory  → create_inventory_tables(conn)
# orders     → create_orders_tables(conn)
# designs    → create_designs_tables(conn)
```

#### العناصر المشتركة

```python
publish_item_as_shared(central_conn, source_company_id, source_item_id,
                       shared_type, name, notes="") -> int
# shared_type: "raw" | "machine" | "labor_op" | "machine_op"
# لو الاسم موجود مسبقاً → يربطه بالشركة فقط بدل إنشاء جديد
# data يحتوي source_company_id في الـ JSON

link_shared_item_to_company(central_conn, erp_conn,
                             shared_item_id, target_company_id) -> int
# يتحقق من is_company_linked قبل الربط — يمنع التكرار

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
يخزّن `_path` كـ instance attribute للقراءة السريعة بدون PRAGMA [تحسين 42].

```python
ProtectedConnection(path: str)
# يستخدم object.__setattr__ لتخزين الـ private attributes
# _path, _raw, _lock كـ object attributes مباشرة

conn.execute(sql, params=())
# reconnect تلقائي لو ظهر: "closed", "unable to open", "disk i/o"
conn.executemany(sql, seq)
conn.executescript(script)
conn.cursor()
conn.commit() / conn.rollback()
conn.close()       # no-op — الإغلاق العرضي ممنوع
conn.real_close()  # الإغلاق الحقيقي الفعلي
conn.path_matches(expected_path) -> bool
# مقارنة سريعة بدون PRAGMA — os.path.normcase + realpath
conn.validate(expected_path) -> bool
# تحقق صريح عبر PRAGMA database_list — للاستخدام الصريح فقط
```

**`_get_raw()` — Fast Path [إصلاح 4]:**
```python
# يرجع الـ connection مباشرة لو موجود بدون SELECT 1
# Slow path (reconnect) فقط لو _raw = None
```

**`__getattr__` / `__setattr__`:**
الأسماء التي تبدأ بـ `_` → `object.__getattribute__/setattr`، غيرها → تمر للـ raw connection.

#### `CompanyState` (Singleton)

```python
company_state = CompanyState()   # module-level singleton

# Properties (read-only)
company_state.company_id    -> int | None
company_state.company_name  -> str
company_state.company_color -> str   # default "#1565c0"
company_state.is_ready      -> bool  # company_id is not None

# Methods
company_state.set_active(company_id, name="", color="#1565c0")
# [C-03] ترتيب آمن للـ threads:
#   1. داخل _state_lock: رفع _invalidate_pending + تغيير الشركة
#   2. خارج الـ lock: AppState.invalidate()
#   3. بعد invalidate: إنزال _invalidate_pending
# لو نفس الشركة → يحدث الاسم واللون فقط بدون مسح connections

company_state.clear()
# يُغلق كل connections ويُعيد ضبط كل الـ state

company_state.get_erp_conn()         -> ProtectedConnection
company_state.get_accounting_conn()  -> ProtectedConnection
company_state.get_inventory_conn()   -> ProtectedConnection
company_state.get_orders_conn()      -> ProtectedConnection
company_state.get_designs_conn()     -> ProtectedConnection
# كلهم يستدعون _get_conn(db_name)

company_state.wait_for_invalidate(timeout=1.0)
# [C-03] ينتظر انتهاء set_active() — للاستخدام من AppState قبل قراءة cache
# fail-safe: لو لم ينتهِ خلال timeout نكمل بدون انتظار

company_state.refresh_connections()
# يُغلق كل connections الحالية (بدون مسح الـ dict)

company_state.close_conn(db_name: str)
# يُغلق connection بعينه ويُزيله من الـ dict
```

**`_get_conn(db_name)` — [تحسين 42]:**
```python
# يستخدم path_matches() بدل validate() في hot path
# لو المسار تغير → يُغلق القديم وينشئ جديد
# لو الملف غير موجود → FileNotFoundError واضحة
```

**Thread Safety [C-03]:**
```python
_invalidate_pending: threading.Event
# مرفوع = جارٍ تحديث الشركة / cache لم يُبطَل بعد
# منزول = الحالة مستقرة ويمكن القراءة
# في التطبيقات single-threaded (PyQt main thread) لا يُشكّل مشكلة عملية
```

---

## shared_items_repo

### `db/companies/shared_items_repo.py`

```python
create_shared_items_tables(conn)
# ينشئ: shared_items, company_shared_links

# مساعدات JSON — [إصلاح 33] من json_utils
_decode = decode_json    # للتوافق مع الكود الداخلي القديم
_encode = encode_json

_default_data(shared_type: str) -> dict
# "raw"        → {"price": 0.0, "total_qty": None}
# "machine"    → {"rate_per_hour": 0.0, "rate_per_unit": 0.0}
# "labor_op"   → {"minutes": 0.0}
# "machine_op" → {"mode": "time", "value": 0.0, "machine_name": "",
#                  "rate_per_hour": 0.0, "rate_per_unit": 0.0}
```

#### CRUD — shared_items

```python
fetch_all_shared_items(conn, shared_type=None) -> list
fetch_shared_item(conn, item_id) -> row
insert_shared_item(conn, name, shared_type, data=None) -> int
# data=None → يستخدم _default_data(shared_type)
# data مُشفَّر بـ encode_json قبل الحفظ
update_shared_item(conn, item_id, name, data: dict)
# updated_at=datetime('now') تلقائياً
delete_shared_item(conn, item_id)
```

#### CRUD — company_shared_links

```python
fetch_linked_companies(conn, shared_item_id) -> list
# يرجع: id, name, color, linked_at من companies JOIN

fetch_shared_items_for_company(conn, company_id, shared_type=None) -> list

is_company_linked(conn, shared_item_id, company_id) -> bool
link_company(conn, shared_item_id, company_id)
# INSERT OR IGNORE — آمن من التكرار
unlink_company(conn, shared_item_id, company_id)
set_linked_companies(conn, shared_item_id, company_ids: list)
# يحذف كل الروابط الحالية ثم يضيف الجديدة
```

#### قراءة بيانات العنصر كـ dict جاهزة

```python
get_item_data(conn, shared_item_id) -> dict
# يُعيد decode_json(row["data"])

get_item_as_raw(conn, shared_item_id) -> dict | None
# {id, name, type:"raw", price, total_qty, category_id:None,
#  category_name:"🔗 مشترك", is_shared:True, shared_id}

get_item_as_machine(conn, shared_item_id) -> dict | None
# {id, name, rate_per_hour, rate_per_unit, category_id:None,
#  category_name:"🔗 مشترك", is_shared:True, shared_id}

get_item_as_labor_op(conn, shared_item_id) -> dict | None
# {id, name, minutes, category_id:None,
#  category_name:"🔗 مشترك", is_shared:True, shared_id}
```

---

## ملاحظات

- لا تُغلق `ProtectedConnection` مباشرة — اتركها للـ `company_state`. فقط `get_central_connection()` تحتاج `.close()`.
- `CompanyState.set_active()` آمن للـ threads عبر `_invalidate_pending` Event [C-03].
- `ProtectedConnection._path` يُتيح مقارنة سريعة بدون PRAGMA overhead [تحسين 42].
- `_migrate_old_shared_items` يضمن إعادة تفعيل `PRAGMA foreign_keys = ON` حتى لو فشل الـ migration [إصلاح 19 v2].
- `get_item_as_machine_op` غير موجودة في `shared_items_repo` — استخدم `get_item_data` مباشرة لـ machine_op.