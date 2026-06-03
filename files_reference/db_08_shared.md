# دليل الكود — DB: المشترك (db/shared/)

> `db/shared/` — الأدوات المشتركة: الاتصالات، الأصناف، التصنيفات، الإعدادات، JSON، جسر العناصر المشتركة.
> **الملفات الفعلية:** `connection.py`, `items_repo.py`, `categories_repo.py`, `settings_repo.py`, `json_utils.py`, `shared_items_bridge.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [connection.py](#connectionpy) | إدارة اتصالات قواعد البيانات |
| [items_repo.py](#items_repopy) | CRUD الأصناف والـ BOM |
| [categories_repo.py](#categories_repopy) | CRUD التصنيفات |
| [settings_repo.py](#settings_repopy) | قراءة/كتابة الإعدادات |
| [json_utils.py](#json_utilspy) | دوال JSON المشتركة |
| [shared_items_bridge.py](#shared_items_bridgepy) | جسر العناصر المشتركة |

---

## connection.py

**المسارات:**
```python
_BASE_DIR  = os.path.join(os.path.dirname(__file__), "..", "..")
CENTRAL_DB = os.path.join(_BASE_DIR, "companies.db")
```

**`_make_conn(path: str) -> sqlite3.Connection`** — دالة داخلية:
```python
# row_factory=sqlite3.Row, isolation_level=None
# PRAGMA foreign_keys=ON, journal_mode=WAL
```

```python
get_central_connection() -> sqlite3.Connection
# connection لـ companies.db عبر _make_conn

get_connection(db: str = "erp") -> sqlite3.Connection
# db: "erp" | "accounting" | "inventory" | "orders" | "designs"
# يستدعي company_state._get_conn(db_name)
# Raises: RuntimeError لو لا توجد شركة نشطة

get_accounting_connection() -> sqlite3.Connection
# اختصار → get_connection("accounting")

get_inventory_connection() -> sqlite3.Connection
# اختصار → get_connection("inventory")

get_linked_connection(primary: str = "inventory",
                      attach: list[str] = None) -> sqlite3.Connection
# يفتح connection جديد (_make_conn) للـ primary DB
# ثم ATTACH لكل DB في attach list
# "costing"/"erp" → كلاهما يُحوَّل لـ "erp"
```

**[إصلاح 10] `get_connection("costing")`:**
```python
# يُصدر DeprecationWarning ثم يُحوَّل لـ "erp"
# الرسالة: "get_connection('costing') مُهمَل — استخدم get_connection('erp') ..."
```

**[T-03] `get_costing_connection()` محذوفة:**
```python
# كانت تُصدر DeprecationWarning — محذوفة الآن
# الكود الذي يستوردها → ImportError واضح
# البديل: company_state.get_erp_conn() أو get_connection("erp")
```

> ⚠️ `get_linked_connection()` يفتح connection جديد في كل استدعاء — لا تستدعه كثيراً. احفظ النتيجة في متغير.

---

## items_repo.py

### Central Connection Cache — [تحسين 8]

```python
_central_conn_cache: dict = {"conn": None, "company_id": None}

_get_central_conn_cached() -> sqlite3.Connection
# يستخدم SELECT 1 للتحقق من صلاحية الـ cache
# لو cached_conn is not None AND cached_cid == current_cid:
#   → cached_conn.execute("SELECT 1") — لو نجح يرجعه
#   → لو فشل (مات) → ينشئ جديد
# غير ذلك → get_central_connection() → يُحدِّث الـ cache

invalidate_central_conn_cache()
# يُغلق الـ connection القديم ويُصفِّر الـ cache
# استدعه عند تغيير الشركة النشطة
```

### BOM Columns Cache

```python
_bom_cols_cache: dict[str, set] = {}
# key: db_path من PRAGMA database_list أو str(id(conn)) كـ fallback

_get_bom_cols(conn) -> set
invalidate_bom_cols_cache(conn=None)
# conn=None → clear() | conn → pop(path, None)
```

### Shared ID Utilities — [A-02] المصدر الوحيد

```python
is_shared_id(item_id) -> bool
# isinstance(item_id, str) AND str(item_id).startswith("shared:")

extract_shared_id(item_id) -> int | None
# "shared:42" → 42 | أي صيغة أخرى → None
```

> ⚠️ **المصدر الوحيد** — `shared_items_bridge.py` يُعيد تصديرهما من هنا.

### Items

```python
fetch_all_items(conn) -> list
# SELECT id, name, type, price, total_qty ORDER BY name

fetch_items_by_type(conn, item_type: str) -> list
# مع category_id, category_name من LEFT JOIN categories WHERE type=? ORDER BY i.name

fetch_items_by_type_with_shared(conn, item_type: str, company_id: int = None) -> list
# يدمج المحلي + المشترك
# المحلي: is_shared=False, shared_item_id=None
# المشترك: id="shared:{n}", is_shared=True

fetch_item(conn, item_id) -> row | _SharedItemRow | None
# لو is_shared_id(item_id) → _fetch_shared_item_as_row(extract_shared_id)
# لو int → SELECT من items JOIN categories WHERE id=?
```

**`_SharedItemRow` — يحاكي sqlite3.Row:**
```python
class _SharedItemRow:
    # __getitem__(key)  → self._data.get(key)
    # __getattr__(key)  → self._data.get(key) مع debug log لو غير موجود
    # keys()            → self._data.keys()
    # get(key, default) → self._data.get(key, default)
```

**`_shared_row_to_item(row, item_type: str) -> dict`:**
```python
# [إصلاح 33] يستخدم decode_json من json_utils
# base: {id, shared_item_id, name, type, category_id:None,
#         category_name:"🔗 مشترك", is_shared:True, total_qty:None}
# حسب item_type:
#   raw        → price, total_qty
#   machine    → rate_per_hour, rate_per_unit, price=0.0
#   labor_op   → minutes, price=0.0
#   machine_op → mode, value, machine_name, rate_per_hour, rate_per_unit, price=0.0
#   غيرها     → price=0.0
```

**`fetch_shared_for_types(company_id=None, types: list = None) -> dict`:**
```python
# [تحسين 11] batch query لأنواع متعددة في connection واحد
# [تحسين 8]  يستخدم _get_central_conn_cached() — لا يُغلق الـ connection
# لو company_id=None → يقرأ من company_state
# يرجع: {type: [item_dict, ...]}
```

### BOM

```python
fetch_bom(conn, parent_id: int) -> list
# لو "variant_id" في cols → يجلبه | وإلا → بدونه
# دائماً: COALESCE(waste_pct, 0) as waste_pct | ORDER BY id

insert_bom_row(conn, parent_id, child_type, child_id, qty,
               waste_pct=0.0, variant_id=None)

delete_bom_row(conn, parent_id, child_type, child_id)

replace_bom(conn, parent_id: int, rows: list[tuple])
# rows: [(child_type, child_id, qty, waste_pct?, variant_id?), ...]
# DELETE parent_id → INSERT الجديد
```

### Orphans

```python
fetch_orphan_bom_rows(conn, parent_id: int) -> list[dict]
# يرجع: [{child_type, child_id, child_name, qty, waste_pct}, ...]

delete_orphan_bom_rows(conn, parent_id: int) -> int
fetch_products_with_orphan(conn, child_type, child_id) -> list[int]
cleanup_empty_products_after_orphan_fix(conn, parent_ids: list[int]) -> list[int]
```

### كتابة الأصناف

```python
insert_item(conn, name, item_type, price=0, category_id=None, total_qty=None) -> int
update_item(conn, item_id, name, price, category_id=None, total_qty=None)
delete_item(conn, item_id)
update_item_category(conn, item_id, category_id: int | None)
```

---

## categories_repo.py

### الثوابت

```python
SCOPES = {
    "all": "الكل", "raw": "الخامات", "semi": "نصف مصنع",
    "final": "منتج نهائي", "labor": "العمالة",
    "machine": "التشغيل", "pricing": "التسعير",
    "design": "مجموعات المقاسات",
}

PRESET_COLORS = [
    "#e53935", "#d81b60", "#8e24aa", "#1e88e5",
    "#00897b", "#43a047", "#f4511e", "#6d4c41",
    "#546e7a", "#1565c0",
]
```

### القراءة

```python
fetch_all_categories(conn, scope: str = None) -> list
# لو scope محدد → WHERE scope='all' OR scope=?
# لو بدون scope → كل التصنيفات
# مع parent_name من LEFT JOIN | ORDER BY parent_id NULLS FIRST, name

fetch_categories_by_scope(conn, scope: str) -> list
# تصنيفات scope محدد فقط — بدون scope='all'
# يجلب أيضاً: template_fields, default_unit

fetch_category(conn, cat_id: int) -> row
# id, name, scope, color, parent_id, template_fields, default_unit

fetch_descendants(conn, cat_id: int) -> list[int]
# [تحسين 5] SQLite Recursive CTE — O(1) query واحدة
# يرجع IDs كل الأبناء والأحفاد + التصنيف نفسه
# Fallback تلقائي لـ _fetch_descendants_fallback لو الـ CTE فشل
```

### الكتابة

```python
insert_category(conn, name, scope="all", color="#607d8b",
                parent_id=None, template_fields: list = None,
                default_unit="mm") -> int
# [تحسين 13] encode_json_list لـ template_fields

update_category(conn, cat_id, name, scope, color,
                parent_id=None, template_fields: list = None, default_unit="mm")
# يتحقق من circular reference → Raises ValueError

delete_category(conn, cat_id)
```

### عمليات مساعدة

```python
count_category_items(conn, cat_id: int) -> dict
# {"عناصر": n, "عمليات عمالة": n, "عمليات تشغيل": n, "ماكينات": n}

build_tree(rows) -> list[dict]
# [إصلاح 5] يستخدم _row_to_dict() الآمنة
# [{id, name, scope, color, parent_id, children: [...]}, ...]
```

### Template Fields — [تحسين 13]

```python
get_template_fields(conn, cat_id: int) -> list[dict]
# decode_json_list(row["template_fields"]) → [] لو NULL

set_template_fields(conn, cat_id: int, fields: list[dict])

apply_template_to_dimension_set(conn_erp, conn_design, cat_id, set_id) -> int
# يجلب template_fields من erp.db ويُضيفها لـ dimension_fields في designs.db
# يرجع عدد الحقول المُضافة
```

---

## settings_repo.py

```python
get_setting(conn, key: str, default=None)
# SELECT value FROM settings WHERE key=?
# يرجع row["value"] كـ TEXT أو default لو غير موجود
# ⚠️ يرجع النص كما هو — استخدم float() عند قراءة الأرقام

set_setting(conn, key: str, value)
# INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
```

**مثال:**
```python
salary = float(get_setting(conn, "monthly_salary", 3000.0))
theme  = get_setting(conn, "ui_theme", "light")
```

---

## json_utils.py

```python
from db.shared.json_utils import decode_json, encode_json
from db.shared.json_utils import decode_json_list, encode_json_list

decode_json(data_str: str) -> dict
# يرجع {} عند: None، نص فارغ، JSON غير صالح، أو نتيجة ليست dict

encode_json(data: dict) -> str
# يرجع '{}' لو data ليس dict أو عند أي خطأ
# json.dumps(data, ensure_ascii=False)

decode_json_list(data_str: str) -> list
# يرجع [] عند: None، نص فارغ، JSON غير صالح، أو نتيجة ليست list
# [تحسين 13] مُستخدمة في categories_repo.py لـ template_fields

encode_json_list(data: list) -> str
# يرجع '[]' لو data ليست list أو عند أي خطأ
```

> ⚠️ لا تستخدم `json.loads/dumps` مباشرة في الملفات الأخرى — استورد من هنا دائماً [إصلاح 33].

---

## shared_items_bridge.py

### الـ Imports الفعلية

```python
from db.shared.json_utils import decode_json, encode_json        # [إصلاح 33]
from db.shared.items_repo import is_shared_id, extract_shared_id # [A-02]
```

### SharedItemsBridge

```python
class SharedItemsBridge:
    SHARED_CATEGORY_NAME = "🔗 مشترك"
    SHARED_ICON          = "🔗"

    def __init__(self, company_id: int):
        self.company_id = company_id
```

**دوال الاتصال الداخلية:**
```python
._get_central_conn(self) -> sqlite3.Connection
# get_central_connection() — يفتح جديد في كل استدعاء (للكتابة فقط)

._get_erp_conn(self) -> ProtectedConnection
# [إصلاح 6] يتحقق من company_state.is_ready أولاً
# Raises: RuntimeError لو لا توجد شركة نشطة
```

**نمط `_conn` الداخلي:**
```python
# معظم methods تقبل _conn=None
# owned = _conn is None
# conn  = _conn or self._get_central_conn()
# try: ... finally: if owned: conn.close()
```

### جلب العناصر المشتركة

```python
.fetch_shared_items_for_type(shared_type: str, _conn=None) -> list
# SELECT من company_shared_links JOIN shared_items WHERE company_id=? AND shared_type=?

.fetch_items_by_type_with_shared(item_type: str) -> list
.fetch_all_with_shared(item_type: str) -> list  # alias

.fetch_shared_item_as_row(shared_item_id: int,
                           shared_type=None, _conn=None) -> dict | None
```

**`_row_to_item(row, data: dict, shared_type: str) -> dict`:**
```python
# base: {id:"shared:{n}", shared_item_id, name, type,
#         category_id:None, category_name:"🔗 مشترك", is_shared:True, updated_at}
# raw        → price, total_qty
# machine    → rate_per_hour, rate_per_unit
# labor_op   → minutes
# machine_op → mode, value, machine_name, rate_per_hour, rate_per_unit
```

### تحديث / ربط / فك ربط

```python
.update_shared_item(shared_item_id, name, data: dict, _conn=None)
.link_shared_item(shared_item_id, _conn=None)
.unlink_shared_item(shared_item_id, _conn=None)
.is_linked(shared_item_id, _conn=None) -> bool
.batch_link(shared_item_ids: list[int])
.batch_unlink(shared_item_ids: list[int])
```

### حساب التكلفة

```python
.calc_shared_raw_unit_price(shared_item_id, _conn=None) -> float
# لو total_qty > 0: price / total_qty | وإلا: price
```

### Singleton helper

```python
get_bridge() -> SharedItemsBridge | None
# يرجع None لو company_state.is_ready=False
```

### إعادة التصدير — [A-02]

```python
__all__ = ["SharedItemsBridge", "get_bridge", "is_shared_id", "extract_shared_id"]
# is_shared_id و extract_shared_id مصدرهما items_repo.py
```

---

## ملاحظات عامة

- `is_shared_id` و `extract_shared_id`: **المصدر الأصلي في `items_repo.py`** — `shared_items_bridge.py` يُعيد تصديرهما فقط [A-02].
- `json_utils`: كل الملفات تستورد منه — لا تعرِّف `_decode/_encode` محلياً [إصلاح 33].
- `_get_central_conn_cached()`: يستخدم SELECT 1 للتحقق، بخلاف `ProtectedConnection` التي تتحقق بـ fast path [تحسين 8].
- `get_costing_connection()` **محذوفة** → ImportError [T-03].
- `get_connection("costing")` **مُهمَل** → DeprecationWarning + يُحوَّل لـ "erp" [إصلاح 10].
- `fetch_descendants`: Recursive CTE = O(1) مع fallback تلقائي [تحسين 5].
- `build_tree`: يستخدم `_row_to_dict()` الآمنة [إصلاح 5].