# دليل الكود — DB (1): قاعدة البيانات المركزية — نسخة محدَّثة

> `companies.db` — الشركات، الحالة، العناصر المشتركة.
> **آخر تحديث:** يعكس الكود الفعلي في السياق — يُستخدم بدلاً من `db_01_companies.md`

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [companies_schema](#companies_schemapy) | `db/companies/companies_schema.py` |
| [companies_repo](#companies_repopy) | `db/companies/companies_repo.py` |
| [company_state](#company_statepy) | `db/companies/company_state.py` |
| [shared_items_repo](#shared_items_repopy) | `db/companies/shared_items_repo.py` |

---

## companies_schema.py

**المسارات:**
```python
_BASE_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "..")
CENTRAL_DB = os.path.join(_BASE_DIR, "companies.db")
DATA_DIR   = os.path.join(_BASE_DIR, "company_data")
```

```python
get_central_connection() -> sqlite3.Connection
# isolation_level=None, row_factory=sqlite3.Row
# PRAGMA foreign_keys=ON, journal_mode=WAL

get_company_dir(company_id: int) -> str
get_company_db_path(company_id: int, db_name: str) -> str
# db_name: "erp" | "accounting" | "inventory" | "orders" | "designs"
ensure_company_dir(company_id: int) -> str
# os.makedirs(path, exist_ok=True)

create_central_tables(conn)
# ينشئ: companies, shared_items, company_shared_links
# ثم يُطبق _migrate_central(conn)
```

**جداول companies.db:**
```sql
companies (id, name UNIQUE, short_name, logo_path, color DEFAULT '#1565c0',
           is_active DEFAULT 1, notes, created_at, updated_at)

shared_items (id, name, shared_type CHECK('raw'|'machine'|'labor_op'|'machine_op'),
              data TEXT DEFAULT '{}', created_at, updated_at)

company_shared_links (id, shared_item_id→shared_items CASCADE,
                      company_id→companies CASCADE, linked_at,
                      UNIQUE(shared_item_id, company_id))
```

**دوال migration داخلية:**
```python
_col_exists(conn, table, col) -> bool
_table_exists(conn, table) -> bool

_migrate_central(conn)
# يتحقق من:
#   has_source = وجود عمود source_company_id في shared_items
#   has_data_col = وجود عمود data في shared_items
# لو النموذج القديم (has_source=True, has_data_col=False) → _migrate_old_shared_items()
# يضيف عمود data لو ناقص
# يضيف عمود updated_at لو ناقص

_migrate_old_shared_items(conn)
# [إصلاح 19 v2] try/finally مع fk_disabled flag:
#   fk_disabled = False   ← يتتبع هل أوقفنا FK فعلاً
#   try:
#     PRAGMA FK=OFF; fk_disabled=True
#     CREATE _shared_items_new (بدون source_company_id، مع data='{}')
#     نقل البيانات القديمة
#     CREATE _links_new (بدون local_item_id, is_synced)
#     نقل الروابط (DISTINCT shared_item_id, company_id)
#     DROP القديمة + RENAME الجديدة
#     commit
#   except: logger.warning + cleanup محاولة
#   finally:
#     if fk_disabled:
#       try: PRAGMA FK=ON
#       except: logger.critical(...)  ← CRITICAL: FK معطلة = بيانات غير متسقة
```

---

## companies_repo.py

### CRUD — الشركات

```python
fetch_all_companies(conn, active_only: bool = False) -> list
# id, name, short_name, logo_path, color, is_active, notes, created_at, updated_at
# ORDER BY name

fetch_company(conn, company_id: int) -> row

insert_company(conn, name, short_name="", color="#1565c0", notes="") -> int
# 1. INSERT INTO companies
# 2. ensure_company_dir(company_id)
# 3. _init_company_databases(company_id)

update_company(conn, company_id, name, short_name="",
               color="#1565c0", notes="", is_active=1)
# updated_at=datetime('now') تلقائياً

delete_company(conn, company_id) -> bool
# يحذف من companies.db فقط — ملفات DB تبقى على الديسك للأمان

toggle_company_active(conn, company_id)
# UPDATE SET is_active = 1 - is_active
```

### تهيئة قواعد بيانات الشركة الجديدة

```python
_init_company_databases(company_id: int)
# يفتح connection مؤقت لكل DB ويُغلقه في finally:
#
# erp.db        → from db.costing.schema import _init_erp_db
# accounting.db → from db.accounting.accounting_schema import create_accounting_tables
# inventory.db  → from db.inventory.inventory_schema import create_inventory_tables
# orders.db     → from db.orders.orders_schema import create_orders_tables
# designs.db    → from db.designs.design_schema import create_designs_tables
#
# كل connection: isolation_level=None, FK=ON, WAL mode
```

### العناصر المشتركة (دوال فعلية)

```python
publish_item_as_shared(central_conn, source_company_id, source_item_id,
                        shared_type, name, notes="") -> int
# shared_type: "raw" | "machine" | "labor_op" | "machine_op"
# لو الاسم موجود (case-insensitive) → يربط فقط ويرجع الـ ID
# لو جديد:
#   data = _default_data(shared_type)
#   data["source_company_id"] = source_company_id
#   insert_shared_item → link_company

link_shared_item_to_company(central_conn, erp_conn,
                             shared_item_id, target_company_id) -> int
# is_company_linked أولاً → link_company لو غير مرتبط
# يرجع shared_item_id (بدون نسخ محلية في النموذج الجديد)

unlink_shared_item(central_conn, shared_item_id, company_id)
delete_shared_item(central_conn, shared_item_id)
sync_shared_item(central_conn, source_erp_conn, shared_item_id)
# no-op للتوافق القديم
```

**الدوال المحذوفة [T-01]:**
```python
# fetch_all_shared_items      → ImportError واضح
# fetch_shared_items_for_company → ImportError واضح
# الاستخدام الصحيح:
from db.companies.shared_items_repo import (
    fetch_all_shared_items,
    fetch_shared_items_for_company,
)
```

---

## company_state.py

### ProtectedConnection

Wrapper على `sqlite3.Connection` يمنع الإغلاق العرضي ويعيد الاتصال تلقائياً.

**التهيئة الداخلية (object.__setattr__ لتجاوز proxy):**
```python
object.__setattr__(self, '_path', path)   # مسار الـ DB
object.__setattr__(self, '_raw', None)    # الـ connection الفعلي
object.__setattr__(self, '_lock', threading.Lock())
```

**`_get_raw()` — Fast Path [إصلاح 4]:**
```python
# لو _raw is not None → يرجعه مباشرة (بدون SELECT 1 في hot path)
# لو _raw is None → Lock → double-check → _open()
# Raises: OperationalError مع رسالة واضحة لو فشل إعادة الاتصال
```

**`_reconnect_after_error()`:**
```python
# يُغلق _raw القديم ثم يضبطه None ثم يستدعي _open()
# يُستدعى من execute/executemany/executescript عند خطأ "closed"/"unable to open"/"disk i/o"
```

**`path_matches(expected_path: str) -> bool` — [تحسين 42]:**
```python
# مقارنة سريعة O(1) بدون PRAGMA:
# os.path.normcase(os.path.realpath(stored)) == os.path.normcase(os.path.realpath(expected))
```

**`validate(expected_path: str) -> bool`:**
```python
# PRAGMA database_list → row[2] → normcase/realpath comparison
# للاستخدام الصريح فقط — لا تستخدم في hot path
```

**`__getattr__ / __setattr__`:**
```python
# __getattr__: أسماء تبدأ بـ _ → AttributeError | غيرها → getattr(_get_raw(), name)
# __setattr__: أسماء تبدأ بـ _ → object.__setattr__ | غيرها → setattr(_get_raw(), name, value)
```

**Methods:**
```python
conn.execute(sql, params=())       # reconnect تلقائي لو "closed/unable to open/disk i/o"
conn.executemany(sql, seq)         # نفس المنطق
conn.executescript(script)         # نفس المنطق
conn.cursor()                      # _get_raw().cursor()
conn.commit() / conn.rollback()
conn.close()                       # ← no-op: لا يُغلق فعلياً
conn.real_close()                  # الإغلاق الحقيقي داخل Lock
conn.path_matches(path) -> bool   # [تحسين 42] سريعة
conn.validate(path) -> bool        # PRAGMA (بطيئة)
# context manager: __enter__ يرجع self | __exit__ pass
```

### CompanyState (Singleton)

```python
company_state = CompanyState()   # module-level singleton
```

**Properties:**
```python
company_state.company_id    -> int | None
company_state.company_name  -> str
company_state.company_color -> str   # default "#1565c0"
company_state.is_ready      -> bool  # company_id is not None
```

**`set_active(company_id, name="", color="#1565c0")` — [C-03]:**
```python
# داخل _state_lock:
#   لو نفس الشركة → يحدّث name/color فقط → return (بدون مسح connections)
#   _invalidate_pending.set()          ← يُشعر threads أن الانتقال بدأ
#   _close_raw_connections_unsafe()    ← يُغلق كل connections
#   _connections.clear()
#   تحديث _company_id/name/color
# خارج lock:
#   AppState.invalidate()
# في finally:
#   _invalidate_pending.clear()        ← الانتقال انتهى

# مثال: company_state.wait_for_invalidate(timeout=1.0)
#   ينتظر انتهاء set_active لو جارٍ (للـ multi-threaded)
```

**`_get_conn(db_name: str) -> ProtectedConnection` — [تحسين 42]:**
```python
# داخل _state_lock:
#   1. conn = _connections.get(db_name)
#   2. expected_path = get_company_db_path(company_id, db_name)
#   3. لو conn موجود:
#      path_matches(expected_path) → True: يرجعه (بدون PRAGMA)
#      path_matches → False: real_close() + del من dict
#   4. لو الملف غير موجود → FileNotFoundError واضحة
#   5. ProtectedConnection(expected_path) → يُضاف للـ dict
```

**Methods:**
```python
company_state.set_active(company_id, name="", color="#1565c0")
company_state.clear()                      # يُغلق كل connections + يُعيد ضبط state
company_state.get_erp_conn()           -> ProtectedConnection
company_state.get_accounting_conn()    -> ProtectedConnection
company_state.get_inventory_conn()     -> ProtectedConnection
company_state.get_orders_conn()        -> ProtectedConnection
company_state.get_designs_conn()       -> ProtectedConnection
company_state.wait_for_invalidate(timeout=1.0)   # [C-03] Thread safety
company_state.refresh_connections()              # يُغلق connections بدون مسح dict
company_state.close_conn(db_name: str)           # يُزيل من dict + real_close()
```

**Thread Safety [C-03]:**
```python
_state_lock: threading.Lock         # يحمي _company_id, _connections, ...
_invalidate_pending: threading.Event
# مرفوع = جارٍ تحديث الشركة / cache لم يُبطَل بعد
# منزول = الحالة مستقرة ويمكن القراءة
# في single-threaded PyQt → لا مشكلة عملية
# يحمي عند استخدام QThread مع DB access
```

---

## shared_items_repo.py

### الـ Imports

```python
# [إصلاح 33] يستورد من json_utils مباشرة بدل تعريف محلي
from db.shared.json_utils import decode_json, encode_json
_decode = decode_json   # alias للتوافق الداخلي
_encode = encode_json   # alias للتوافق الداخلي
```

### البيانات الافتراضية

```python
_default_data(shared_type: str) -> dict
# "raw"        → {"price": 0.0, "total_qty": None}
# "machine"    → {"rate_per_hour": 0.0, "rate_per_unit": 0.0}
# "labor_op"   → {"minutes": 0.0}
# "machine_op" → {"mode": "time", "value": 0.0, "machine_name": "",
#                  "rate_per_hour": 0.0, "rate_per_unit": 0.0}
# أي نوع آخر  → {}
```

### CRUD — shared_items

```python
fetch_all_shared_items(conn, shared_type: str = None) -> list
# لو shared_type محدد → WHERE shared_type=?
# ORDER BY name
# الأعمدة: id, name, shared_type, data, updated_at

fetch_shared_item(conn, item_id: int) -> row

insert_shared_item(conn, name, shared_type, data: dict = None) -> int
# data=None → _default_data(shared_type)
# يُشفِّر data بـ encode_json قبل الحفظ

update_shared_item(conn, item_id, name, data: dict)
# updated_at=datetime('now') تلقائياً

delete_shared_item(conn, item_id)
# CASCADE على company_shared_links
```

### CRUD — company_shared_links

```python
fetch_linked_companies(conn, shared_item_id: int) -> list
# id, name, color, linked_at من companies JOIN ORDER BY c.name

fetch_shared_items_for_company(conn, company_id: int,
                                shared_type: str = None) -> list
# مع shared_type filter اختياري ORDER BY s.name

is_company_linked(conn, shared_item_id: int, company_id: int) -> bool

link_company(conn, shared_item_id: int, company_id: int)
# INSERT OR IGNORE — آمن من التكرار

unlink_company(conn, shared_item_id: int, company_id: int)

set_linked_companies(conn, shared_item_id: int, company_ids: list)
# DELETE كل الروابط الحالية → INSERT الجديدة
```

### قراءة بيانات العنصر كـ dict جاهز

```python
get_item_data(conn, shared_item_id: int) -> dict
# decode_json(row["data"]) أو {} لو العنصر غير موجود

get_item_as_raw(conn, shared_item_id: int) -> dict | None
# {id, name, type:"raw", price, total_qty,
#  category_id:None, category_name:"🔗 مشترك",
#  is_shared:True, shared_id:shared_item_id}

get_item_as_machine(conn, shared_item_id: int) -> dict | None
# {id, name, rate_per_hour, rate_per_unit,
#  category_id:None, category_name:"🔗 مشترك",
#  is_shared:True, shared_id:shared_item_id}

get_item_as_labor_op(conn, shared_item_id: int) -> dict | None
# {id, name, minutes,
#  category_id:None, category_name:"🔗 مشترك",
#  is_shared:True, shared_id:shared_item_id}
```

> ⚠️ `get_item_as_machine_op` **غير موجودة** — استخدم `get_item_data(conn, id)` مباشرة.

---

## ملاحظات عامة

- لا تُغلق `ProtectedConnection` مباشرة — اتركها للـ `company_state`. فقط `get_central_connection()` تحتاج `.close()`.
- `ProtectedConnection._path` يُتيح `path_matches()` سريعة O(1) بدون PRAGMA [تحسين 42].
- `_get_raw()` fast-path لا يُجري SELECT 1 [إصلاح 4].
- `set_active()` آمن للـ threads عبر `_state_lock` + `_invalidate_pending` [C-03].
- `_migrate_old_shared_items` يضمن PRAGMA FK=ON عبر finally + fk_disabled flag [إصلاح 19 v2].
- `refresh_connections()` تُغلق connections بدون مسح dict — تُعاد فتحها عند الطلب التالي.
- `get_item_as_machine_op` **غير موجودة** في shared_items_repo.
- `[إصلاح 33]` يستورد decode/encode JSON من `db.shared.json_utils` مباشرة.