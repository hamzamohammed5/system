# دليل الكود — DB: الطبقة المشتركة (db/shared/) — نسخة من الكود الفعلي

> يعكس هذا الملف الكود الفعلي الموجود في السياق.
> الملفات: `connection.py`, `items_repo.py`, `categories_repo.py`,
> `settings_repo.py`, `json_utils.py`, `shared_items_bridge.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [connection.py](#connectionpy) | إدارة اتصالات قواعد البيانات |
| [items_repo.py](#items_repopy) | CRUD الأصناف والـ BOM + العناصر المشتركة |
| [categories_repo.py](#categories_repopy) | CRUD التصنيفات + Template Fields |
| [settings_repo.py](#settings_repopy) | قراءة/كتابة الإعدادات |
| [json_utils.py](#json_utilspy) | دوال JSON المشتركة |
| [shared_items_bridge.py](#shared_items_bridgepy) | جسر العناصر المشتركة |

---

## connection.py

```python
_BASE_DIR  = os.path.join(os.path.dirname(__file__), "..", "..")
CENTRAL_DB = os.path.join(_BASE_DIR, "companies.db")
```

```python
def _make_conn(path: str) -> sqlite3.Connection:
    # row_factory=sqlite3.Row, isolation_level=None
    # PRAGMA foreign_keys=ON, journal_mode=WAL

get_central_connection() -> sqlite3.Connection
# يفتح companies.db عبر _make_conn

get_connection(db: str = "erp") -> sqlite3.Connection
# db: "erp" | "accounting" | "inventory" | "orders" | "designs"
# يستدعي company_state._get_conn(db_name)
# Raises: RuntimeError لو لا توجد شركة نشطة
# [إصلاح 10] "costing" → DeprecationWarning ثم يُحوَّل لـ "erp"

get_accounting_connection() -> sqlite3.Connection
# اختصار → get_connection("accounting")

get_inventory_connection() -> sqlite3.Connection
# اختصار → get_connection("inventory")

get_linked_connection(primary: str = "inventory",
                      attach: list[str] = None) -> sqlite3.Connection
# يفتح connection جديد (_make_conn) لـ primary
# ثم ATTACH لكل DB في attach
# "costing"/"erp" → كلاهما يُحوَّل لـ "erp"
```

**[T-03] `get_costing_connection()` محذوفة:**
```python
# استورادها → ImportError واضح يساعد في تحديد الكود القديم
# البديل: company_state.get_erp_conn() أو get_connection("erp")
```

> ⚠️ `get_linked_connection()` يفتح connection جديد في كل استدعاء — احفظ النتيجة.

---

## items_repo.py

### Central Connection Cache — [تحسين 8]

```python
_central_conn_cache: dict = {"conn": None, "company_id": None}

_get_central_conn_cached() -> sqlite3.Connection
# لو cache صالح (SELECT 1 نجح + نفس company_id) → يُعيده
# لو مات أو تغيرت الشركة → get_central_connection() جديد + تحديث cache
# مشاركة آمنة: central DB للقراءة فقط، single-threaded PyQt

invalidate_central_conn_cache()
# يُغلق القديم + يُصفِّر cache
# استدعه عند تغيير الشركة النشطة
```

### BOM Columns Cache

```python
_bom_cols_cache: dict[str, set] = {}
# key: db_path من PRAGMA database_list أو str(id(conn)) كـ fallback

_get_bom_cols(conn) -> set
# PRAGMA table_info(bom) + cache بمفتاح db_path

invalidate_bom_cols_cache(conn=None)
# conn=None → _bom_cols_cache.clear()
# conn=<conn> → pop(path, None)
# استدعه بعد أي migration يضيف أعمدة لـ bom
```

### Shared ID Utilities — [A-02] المصدر الوحيد

```python
is_shared_id(item_id) -> bool
# isinstance(item_id, str) AND str(item_id).startswith("shared:")
# مثال: is_shared_id("shared:42") → True | is_shared_id(42) → False

extract_shared_id(item_id) -> int | None
# "shared:42" → 42 | أي صيغة أخرى أو exception → None
```

> ⚠️ **المصدر الوحيد** — `shared_items_bridge.py` يُعيد تصديرهما من هنا دون إعادة تعريف.

### Items — قراءة

```python
fetch_all_items(conn) -> list
# SELECT id, name, type, price, total_qty ORDER BY name

fetch_items_by_type(conn, item_type: str) -> list
# مع category_id, category_name من LEFT JOIN categories
# WHERE type=? ORDER BY i.name

fetch_items_by_type_with_shared(conn, item_type: str,
                                 company_id: int = None) -> list
# يدمج المحلي + المشترك
# المحلي: is_shared=False, shared_item_id=None
# المشترك: id="shared:{n}", is_shared=True, category_name="🔗 مشترك"

fetch_item(conn, item_id) -> row | _SharedItemRow | None
# لو is_shared_id(item_id) → _fetch_shared_item_as_row(extract_shared_id)
# لو int → SELECT من items JOIN categories WHERE id=?
```

**`_SharedItemRow` — يحاكي sqlite3.Row:**
```python
# __getitem__(key)  → self._data.get(key)
# __getattr__(key)  → self._data.get(key) مع debug log لو غير موجود
# keys()            → self._data.keys()
# get(key, default) → self._data.get(key, default)
```

**`fetch_shared_for_types(company_id=None, types: list = None) -> dict`:**
```python
# [تحسين 11] batch query لأنواع متعددة في connection واحد
# [تحسين 8]  يستخدم _get_central_conn_cached() — لا يُغلق الـ connection
# لو company_id=None → يقرأ من company_state
# SELECT من company_shared_links JOIN shared_items WHERE company_id=? AND type IN (...)
# يرجع: {type_str: [item_dict, ...]}
# عند فشل cache → _central_conn_cache["conn"] = None (للتعافي في الاستدعاء التالي)
```

**`_shared_row_to_item(row, item_type: str) -> dict`:**
```python
# [إصلاح 33] يستخدم decode_json من json_utils (لا json.loads محلي)
# base: {id:"shared:{n}", shared_item_id, name, type,
#         category_id:None, category_name:"🔗 مشترك",
#         is_shared:True, total_qty:None}
# حسب item_type:
#   "raw"        → price, total_qty
#   "machine"    → rate_per_hour, rate_per_unit, price=0.0
#   "labor_op"   → minutes, price=0.0
#   "machine_op" → mode, value, machine_name, rate_per_hour, rate_per_unit, price=0.0
#   غيرها        → price=0.0
```

### Items — كتابة

```python
insert_item(conn, name: str, item_type: str, price: float = 0,
            category_id: int = None, total_qty: float = None) -> int

update_item(conn, item_id: int, name: str, price: float,
            category_id: int = None, total_qty: float = None)

delete_item(conn, item_id: int)

update_item_category(conn, item_id: int, category_id: int | None)
# UPDATE items SET category_id=? WHERE id=?
```

### BOM

```python
fetch_bom(conn, parent_id: int) -> list
# لو "variant_id" في _get_bom_cols → يجلبه | وإلا → بدونه
# دائماً: COALESCE(waste_pct, 0) as waste_pct | ORDER BY id

insert_bom_row(conn, parent_id: int, child_type: str, child_id: int,
               qty: float, waste_pct: float = 0.0,
               variant_id: int = None)
# يُحدِّد child_name تلقائياً من الجداول المناسبة

delete_bom_row(conn, parent_id: int, child_type: str, child_id: int)

replace_bom(conn, parent_id: int, rows: list[tuple])
# rows: [(child_type, child_id, qty, waste_pct?, variant_id?), ...]
# DELETE parent_id → INSERT الجديد بشكل آمن حسب الأعمدة الموجودة
```

### Orphans

```python
fetch_orphan_bom_rows(conn, parent_id: int) -> list[dict]
# [{child_type, child_id, child_name, qty, waste_pct}, ...]
# يتحقق من وجود كل child في الجدول المناسب

delete_orphan_bom_rows(conn, parent_id: int) -> int
# يحذف الـ orphans ويرجع عددها

fetch_products_with_orphan(conn, child_type: str, child_id: int) -> list[int]
# DISTINCT parent_ids من bom

cleanup_empty_products_after_orphan_fix(conn, parent_ids: list[int]) -> list[int]
# يحذف المنتجات التي أصبح BOMها فارغاً بعد إصلاح الـ orphans
# يرجع IDs المنتجات المحذوفة
```

---

## categories_repo.py

> **[إصلاح 5]:** `build_tree` تستخدم `_row_to_dict()` الآمنة.
> **[تحسين 5]:** `fetch_descendants` تستخدم SQLite Recursive CTE.
> **[تحسين 13]:** `encode_json_list/decode_json_list` لـ `template_fields`.

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
# تصنيفات scope محدد فقط (بدون 'all')
# يجلب أيضاً: template_fields, default_unit

fetch_category(conn, cat_id: int) -> row
# id, name, scope, color, parent_id, template_fields, default_unit

fetch_descendants(conn, cat_id: int) -> list[int]
# [تحسين 5] SQLite Recursive CTE — O(1) query واحدة
# يرجع IDs: التصنيف نفسه + كل أبنائه وأحفاده
# Fallback تلقائي لـ _fetch_descendants_fallback لو CTE فشل
# _fetch_descendants_fallback: while loop + individual queries لكل مستوى
```

### الكتابة

```python
insert_category(conn, name: str, scope: str = "all",
                color: str = "#607d8b",
                parent_id: int = None,
                template_fields: list = None,
                default_unit: str = "mm") -> int
# [تحسين 13] encode_json_list لـ template_fields

update_category(conn, cat_id: int, name: str, scope: str,
                color: str, parent_id: int = None,
                template_fields: list = None,
                default_unit: str = "mm")
# يتحقق من circular reference: parent_id ∈ fetch_descendants(cat_id) → ValueError
# [تحسين 13] encode_json_list لـ template_fields

delete_category(conn, cat_id: int)
```

### المساعدات

```python
count_category_items(conn, cat_id: int) -> dict
# يجمع كل أبناء cat_id أولاً (fetch_descendants)
# {"عناصر": n, "عمليات عمالة": n, "عمليات تشغيل": n, "ماكينات": n}
# يبحث في: items, labor_ops, machine_ops, machines

def _row_to_dict(r) -> dict:
    # [إصلاح 5] آمنة — تستخدم .get() وتتحقق من available keys
    # يمنع KeyError عند query قديمة أو migration ناقص
    # {id, name, scope, color, parent_id, children: []}

def build_tree(rows) -> list[dict]:
    # [إصلاح 5] يستخدم _row_to_dict() الآمنة
    # يبني شجرة هرمية من قائمة مسطحة
    # [{id, name, scope, color, parent_id, children: [...]}, ...]
```

### Template Fields — [تحسين 13]

```python
get_template_fields(conn, cat_id: int) -> list[dict]
# decode_json_list(row["template_fields"]) → [] لو NULL أو JSON فاسد

set_template_fields(conn, cat_id: int, fields: list[dict])
# encode_json_list(fields) → UPDATE categories SET template_fields=?

apply_template_to_dimension_set(conn_erp, conn_design,
                                  cat_id: int, set_id: int) -> int
# يجلب template_fields من erp.db (conn_erp)
# يُضيف الحقول الجديدة فقط (يتحقق من existing بالاسم) لـ designs.db (conn_design)
# يرجع عدد الحقول المُضافة
# يتجاهل: الحقول بدون name أو الحقول الموجودة مسبقاً
```

---

## settings_repo.py

```python
get_setting(conn, key: str, default=None)
# SELECT value FROM settings WHERE key=?
# يرجع row["value"] كـ TEXT | default لو المفتاح غير موجود

set_setting(conn, key: str, value)
# INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
# يستدعي conn.commit()
```

**ملاحظة مهمة:**
```python
# القيم مُخزَّنة كـ TEXT دائماً
# استخدم التحويل عند القراءة:
salary = float(get_setting(conn, "monthly_salary", 3000.0))
theme  = get_setting(conn, "ui_theme", "light")
lang   = get_setting(conn, "ui_language", "ar")
```

---

## json_utils.py

> **[إصلاح 33]:** مركزة الكود المكرر — كل الملفات تستورد من هنا.
> **[تحسين 13]:** `decode_json_list/encode_json_list` مُستخدمتان في `categories_repo.py`.

```python
from db.shared.json_utils import decode_json, encode_json
from db.shared.json_utils import decode_json_list, encode_json_list

def decode_json(data_str: str) -> dict:
    # يرجع {} عند: None، نص فارغ، JSON غير صالح، النتيجة ليست dict
    # try: json.loads → isinstance(result, dict) → return result
    # except any → return {}

def encode_json(data: dict) -> str:
    # يرجع '{}' لو data ليس dict أو عند أي خطأ
    # json.dumps(data, ensure_ascii=False)

def decode_json_list(data_str: str) -> list:
    # يرجع [] عند: None، نص فارغ، JSON غير صالح، النتيجة ليست list
    # [تحسين 13] مُستخدمة في categories_repo.py لـ template_fields

def encode_json_list(data: list) -> str:
    # يرجع '[]' لو data ليست list أو عند أي خطأ
    # json.dumps(data, ensure_ascii=False)
```

> ⚠️ لا تستخدم `json.loads/dumps` مباشرة في ملفات أخرى — استورد من هنا [إصلاح 33].

---

## shared_items_bridge.py

> **[إصلاح 6]:** `_get_erp_conn()` يتحقق من `is_ready`.
> **[إصلاح 33]:** يستخدم `decode_json/encode_json` من `json_utils`.
> **[A-02]:** `is_shared_id/extract_shared_id` مُستوردتان من `items_repo` لا مُعرَّفتان هنا.

### الـ Imports الفعلية

```python
from db.shared.json_utils import decode_json, encode_json
from db.shared.items_repo import is_shared_id, extract_shared_id  # [A-02]
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
# get_central_connection() — يفتح جديد في كل استدعاء (للكتابة)

._get_erp_conn(self) -> ProtectedConnection
# [إصلاح 6] يتحقق أولاً: company_state.is_ready
# Raises: RuntimeError("SharedItemsBridge: لا توجد شركة نشطة") لو False
```

**نمط `_conn` الداخلي (معظم methods):**
```python
def some_method(self, ..., _conn=None):
    owned = _conn is None
    conn  = _conn or self._get_central_conn()
    try:
        # العملية
    except ...:
        return default_value
    finally:
        if owned: conn.close()
```

### جلب العناصر المشتركة

```python
.fetch_shared_items_for_type(shared_type: str, _conn=None) -> list
# SELECT من company_shared_links JOIN shared_items
# WHERE company_id=? AND shared_type=? ORDER BY s.name
# يستخدم _row_to_item() لكل صف

.fetch_items_by_type_with_shared(item_type: str) -> list
.fetch_all_with_shared(item_type: str) -> list   # alias

.fetch_shared_item_as_row(shared_item_id: int,
                           shared_type=None, _conn=None) -> dict | None
```

**`_row_to_item(row, data: dict, shared_type: str) -> dict`:**
```python
# base: {id:"shared:{n}", shared_item_id, name, type,
#         category_id:None, category_name:"🔗 مشترك",
#         is_shared:True, updated_at}
# "raw"        → price, total_qty
# "machine"    → rate_per_hour, rate_per_unit
# "labor_op"   → minutes
# "machine_op" → mode, value, machine_name, rate_per_hour, rate_per_unit
```

### تحديث / ربط / فك ربط

```python
.update_shared_item(shared_item_id: int, name: str, data: dict, _conn=None)
# UPDATE shared_items SET name=?, data=encode_json(data), updated_at=datetime('now')

.link_shared_item(shared_item_id: int, _conn=None)
# INSERT OR IGNORE INTO company_shared_links

.unlink_shared_item(shared_item_id: int, _conn=None)
# DELETE FROM company_shared_links WHERE shared_item_id=? AND company_id=?

.is_linked(shared_item_id: int, _conn=None) -> bool

.batch_link(shared_item_ids: list[int])
.batch_unlink(shared_item_ids: list[int])
# يفتح connection واحد لكل الـ batch ثم يُغلقه
```

### حساب التكلفة

```python
.calc_shared_raw_unit_price(shared_item_id: int, _conn=None) -> float
# لو total_qty is not None and float(total_qty) > 0 → price / total_qty
# وإلا → price
# يرجع 0.0 لو العنصر غير موجود
```

### Singleton Helper

```python
def get_bridge() -> SharedItemsBridge | None:
    # يرجع None لو company_state.is_ready=False أو أي exception
    # يرجع SharedItemsBridge(company_state.company_id) لو جاهز
```

### إعادة التصدير — [A-02]

```python
__all__ = ["SharedItemsBridge", "get_bridge", "is_shared_id", "extract_shared_id"]
# is_shared_id و extract_shared_id مصدرهما items_repo.py فقط
```

---

## ملاحظات عامة

- `is_shared_id` و `extract_shared_id`: المصدر الأصلي `items_repo.py` — `shared_items_bridge.py` يُعيد تصديرهما فقط [A-02].
- `json_utils`: كل الملفات تستورد منه — لا تُعرِّف `_decode/_encode` محلياً [إصلاح 33].
- `_get_central_conn_cached()`: يستخدم SELECT 1 للتحقق — مختلف عن `ProtectedConnection` [تحسين 8].
- `get_costing_connection()` محذوفة → ImportError واضح [T-03].
- `get_connection("costing")` مُهمَل → DeprecationWarning + يُحوَّل لـ "erp" [إصلاح 10].
- `fetch_descendants`: Recursive CTE = O(1) مع fallback تلقائي [تحسين 5].
- `build_tree`: يستخدم `_row_to_dict()` الآمنة [إصلاح 5].
- `apply_template_to_dimension_set` يحتاج connection-ين: `conn_erp` لـ erp.db و `conn_design` لـ designs.db.