# دليل الكود — DB (1): قاعدة البيانات المركزية

> `companies.db` — الشركات، الحالة، العناصر المشتركة.
> **آخر تحديث:** يعكس الكود الفعلي في السياق بالكامل.

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
```python
_BASE_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "..")
CENTRAL_DB = os.path.join(_BASE_DIR, "companies.db")
DATA_DIR   = os.path.join(_BASE_DIR, "company_data")
```

```python
get_central_connection() -> sqlite3.Connection
# isolation_level=None, foreign_keys=ON, journal_mode=WAL

get_company_dir(company_id: int) -> str
# os.path.join(DATA_DIR, str(company_id))

get_company_db_path(company_id: int, db_name: str) -> str
# db_name: "erp" | "accounting" | "inventory" | "orders" | "designs"

ensure_company_dir(company_id: int) -> str
# os.makedirs(path, exist_ok=True)

create_central_tables(conn)
# ينشئ: companies, shared_items, company_shared_links
# ثم يُطبّق _migrate_central()
```

**جداول companies.db:**

```sql
CREATE TABLE IF NOT EXISTS companies (
    id, name UNIQUE, short_name, logo_path,
    color DEFAULT '#1565c0', is_active DEFAULT 1,
    notes, created_at, updated_at
)

CREATE TABLE IF NOT EXISTS shared_items (
    id, name, shared_type CHECK('raw'|'machine'|'labor_op'|'machine_op'),
    data TEXT DEFAULT '{}', created_at, updated_at
)

CREATE TABLE IF NOT EXISTS company_shared_links (
    id, shared_item_id→shared_items CASCADE,
    company_id→companies CASCADE,
    linked_at, UNIQUE(shared_item_id, company_id)
)
```

**Migration آمن — `_migrate_central(conn)`:**
يتعامل مع قواعد البيانات القديمة التي كان فيها `source_company_id` في `shared_items` بدل `data` JSON.

يتحقق من:
- `has_source` = وجود عمود `source_company_id` في `shared_items`
- `has_data_col` = وجود عمود `data` في `shared_items`

لو النموذج القديم موجود (`has_source=True` و `has_data_col=False`) → يستدعي `_migrate_old_shared_items(conn)`.

**`_migrate_old_shared_items(conn)` — [إصلاح 19 v2]:**
```python
# بنية try/finally مزدوجة لضمان إعادة تفعيل PRAGMA foreign_keys = ON
#
# fk_disabled: bool = False   ← flag لتتبع هل أوقفنا FK فعلاً
#
# try:
#   conn.execute("PRAGMA foreign_keys = OFF")
#   fk_disabled = True
#   
#   # إنشاء _shared_items_new (بدون source_company_id، مع data JSON)
#   # نقل البيانات القديمة مع data='{}'
#   # إنشاء _links_new (بدون local_item_id و is_synced)
#   # نقل الروابط القديمة (DISTINCT shared_item_id, company_id)
#   # استبدال الجداول بـ DROP + RENAME
#   conn.commit()
#
# except Exception as e:
#   logger.warning(...)
#   try: cleanup _shared_items_new و _links_new
#   except: logger.warning(cleanup_err)
#
# finally:
#   if fk_disabled:   ← الشرط يمنع تفعيل FK لم نُعطّله أصلاً
#     try:
#       conn.execute("PRAGMA foreign_keys = ON")
#     except Exception as fk_err:
#       logger.critical(...)   ← CRITICAL: FK معطلة = بيانات غير متسقة
#
# ملاحظة: PRAGMA foreign_keys هو session-level لا transaction-level
```

**مساعدات داخلية:**
```python
_col_exists(conn, table, col) -> bool
# PRAGMA table_info(table) + any(r["name"] == col)

_table_exists(conn, table) -> bool
# SELECT name FROM sqlite_master WHERE type='table' AND name=?
```

---

## companies_repo

### `db/companies/companies_repo.py`

```python
fetch_all_companies(conn, active_only=False) -> list
# id, name, short_name, logo_path, color, is_active, notes, created_at, updated_at
# لو active_only=True → WHERE is_active = 1

fetch_company(conn, company_id: int) -> row

insert_company(conn, name, short_name="", color="#1565c0", notes="") -> int
# ينشئ شركة + ensure_company_dir() + _init_company_databases()

update_company(conn, company_id, name, short_name="", color="#1565c0",
               notes="", is_active=1)
# updated_at=datetime('now') تلقائياً

delete_company(conn, company_id) -> bool
# يحذف من companies.db فقط — الملفات تبقى على الديسك للأمان

toggle_company_active(conn, company_id)
# UPDATE SET is_active = 1 - is_active
```

#### تهيئة قواعد بيانات الشركة

```python
_init_company_databases(company_id: int)
# يفتح connections مؤقتة تُغلق في finally لكل DB:
#   erp        → _init_erp_db(conn)         (من db.costing.schema)
#   accounting → create_accounting_tables(conn)
#   inventory  → create_inventory_tables(conn)
#   orders     → create_orders_tables(conn)
#   designs    → create_designs_tables(conn)
#
# كل connection يُفتح بـ:
#   isolation_level=None, foreign_keys=ON, journal_mode=WAL
# كل connection يُغلق في finally بعد التهيئة
```

#### العناصر المشتركة

```python
publish_item_as_shared(central_conn, source_company_id, source_item_id,
                       shared_type, name, notes="") -> int
# shared_type: "raw" | "machine" | "labor_op" | "machine_op"
# لو الاسم موجود مسبقاً (case-insensitive) → يربطه بالشركة فقط
# لو جديد:
#   data = _default_data(shared_type)
#   data["source_company_id"] = source_company_id  ← في الـ JSON
#   يُنشئ shared_item جديد ثم يربطه

link_shared_item_to_company(central_conn, erp_conn,
                             shared_item_id, target_company_id) -> int
# يتحقق من is_company_linked قبل الربط — يمنع التكرار
# يرجع shared_item_id مباشرة (النموذج الجديد بدون نسخ محلية)

unlink_shared_item(central_conn, shared_item_id, company_id)
delete_shared_item(central_conn, shared_item_id)

sync_shared_item(central_conn, source_erp_conn, shared_item_id)
# no-op — للتوافق مع الكود القديم
# البيانات تُقرأ مباشرة من companies.db في النموذج الجديد
```

> ⚠️ **الدوال المحذوفة [T-01] — ImportError واضح:**
> - `fetch_all_shared_items` → استورد من `db.companies.shared_items_repo`
> - `fetch_shared_items_for_company` → استورد من `db.companies.shared_items_repo`

---

## company_state

### `db/companies/company_state.py`

#### `ProtectedConnection`

Wrapper على `sqlite3.Connection` يمنع الإغلاق العرضي ويعيد الاتصال تلقائياً.

```python
ProtectedConnection(path: str)
# __init__ يستخدم object.__setattr__ لتخزين الـ private attributes:
#   object.__setattr__(self, '_path', path)
#   object.__setattr__(self, '_raw', None)
#   object.__setattr__(self, '_lock', threading.Lock())
# هذا يتجاوز __setattr__ المخصص الذي يُحوّل الـ non-_ attributes للـ raw connection
```

**`_get_raw()` — Fast Path [إصلاح 4]:**
```python
# لو _raw is not None → يرجعه مباشرة (بدون SELECT 1)
# لو _raw is None → يدخل lock → يُعيد فحص _raw → يستدعي _open()
# Slow path (reconnect) فقط لو _raw = None — لا overhead في الحالة الطبيعية
```

**`__getattr__` / `__setattr__`:**
```python
# __getattr__: الأسماء التي تبدأ بـ _ → raise AttributeError
#              غيرها → getattr(self._get_raw(), name)
# __setattr__: الأسماء التي تبدأ بـ _ → object.__setattr__(self, name, value)
#              غيرها → setattr(self._get_raw(), name, value)
```

**`execute(sql, params=())`:**
```python
# reconnect تلقائي لو ظهر في رسالة الخطأ: "closed", "unable to open", "disk i/o"
# نفس المنطق في executemany و executescript
```

**Methods الكاملة:**
```python
conn.execute(sql, params=())
conn.executemany(sql, seq)
conn.executescript(script)
conn.cursor()
conn.commit() / conn.rollback()
conn.close()       # no-op — الإغلاق العرضي ممنوع
conn.real_close()  # الإغلاق الحقيقي الفعلي (داخل lock)

conn.path_matches(expected_path) -> bool
# [تحسين 42] مقارنة سريعة بدون PRAGMA:
#   os.path.normcase(os.path.realpath(stored)) == os.path.normcase(os.path.realpath(expected))
#   يقرأ _path المخزون مباشرة

conn.validate(expected_path) -> bool
# تحقق صريح عبر PRAGMA database_list
# للاستخدام الصريح فقط (ليس في hot path)
```

#### `CompanyState` (Singleton)

```python
company_state = CompanyState()   # module-level singleton

# Properties (read-only)
company_state.company_id    -> int | None
company_state.company_name  -> str
company_state.company_color -> str   # default "#1565c0"
company_state.is_ready      -> bool  # company_id is not None
```

**`set_active(company_id, name="", color="#1565c0")` — [C-03]:**
```python
# داخل _state_lock:
#   1. لو نفس الشركة → يحدث الاسم واللون فقط → return (لا مسح connections)
#   2. _invalidate_pending.set()   ← يُشعر threads أن الانتقال بدأ
#   3. _close_raw_connections_unsafe()
#   4. _connections.clear()
#   5. تحديث _company_id / _company_name / _company_color
#
# خارج lock:
#   6. AppState.invalidate()
#
# في finally:
#   7. _invalidate_pending.clear()  ← الانتقال انتهى
```

**`_get_conn(db_name)` — [تحسين 42]:**
```python
# داخل _state_lock:
#   1. conn = _connections.get(db_name)
#   2. expected_path = get_company_db_path(company_id, db_name)
#   3. لو conn موجود:
#      - path_matches(expected_path) → True: يرجعه (بدون PRAGMA)
#      - path_matches → False: يُغلق القديم + يحذفه من dict
#   4. لو الملف غير موجود → FileNotFoundError واضحة
#   5. ينشئ ProtectedConnection جديد + يضيفه للـ dict
```

**Methods الكاملة:**
```python
company_state.set_active(company_id, name="", color="#1565c0")
company_state.clear()                    # يُغلق كل connections + يُعيد ضبط state
company_state.get_erp_conn()         -> ProtectedConnection
company_state.get_accounting_conn()  -> ProtectedConnection
company_state.get_inventory_conn()   -> ProtectedConnection
company_state.get_orders_conn()      -> ProtectedConnection
company_state.get_designs_conn()     -> ProtectedConnection
company_state.wait_for_invalidate(timeout=1.0)   # [C-03] ينتظر انتهاء set_active
company_state.refresh_connections()              # يُغلق connections بدون مسح dict
company_state.close_conn(db_name: str)           # يُزيل من dict + real_close
```

**Thread Safety [C-03]:**
```python
_state_lock: threading.Lock          # يحمي _company_id, _connections, ...
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

# مساعدات JSON — [إصلاح 33] من json_utils مباشرة
from db.shared.json_utils import decode_json, encode_json
_decode = decode_json    # alias للتوافق مع الكود الداخلي القديم
_encode = encode_json    # alias للتوافق مع الكود الداخلي القديم

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
# لو shared_type محدد → فلتر على shared_type
# ORDER BY name

fetch_shared_item(conn, item_id) -> row
# id, name, shared_type, data, updated_at

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

> ⚠️ `get_item_as_machine_op` غير موجودة — استخدم `get_item_data` مباشرة لـ machine_op.

---

## ملاحظات

- لا تُغلق `ProtectedConnection` مباشرة — اتركها للـ `company_state`. فقط `get_central_connection()` تحتاج `.close()`.
- `ProtectedConnection` يستخدم `object.__setattr__` في `__init__` لتخزين `_path`, `_raw`, `_lock` كـ object attributes مباشرة.
- `CompanyState.set_active()` آمن للـ threads عبر `_state_lock` + `_invalidate_pending` Event [C-03].
- `ProtectedConnection._path` يُتيح `path_matches()` سريعة بدون PRAGMA overhead [تحسين 42].
- `_get_raw()` fast-path لا يُجري SELECT 1 — يعتمد على وجود `_raw` مباشرة [إصلاح 4].
- `_migrate_old_shared_items` يضمن إعادة تفعيل `PRAGMA foreign_keys = ON` عبر `finally` + `fk_disabled` flag [إصلاح 19 v2].
- `refresh_connections()` تُغلق connections بدون مسح dict — الـ connections تُعاد فتحها عند الطلب التالي.
- `get_item_as_machine_op` غير موجودة في `shared_items_repo` — استخدم `get_item_data` مباشرة.
- `[إصلاح 33]` `shared_items_repo` يستورد `decode_json/encode_json` من `db.shared.json_utils` مباشرة بدل تعريف `_decode/_encode` محلية.