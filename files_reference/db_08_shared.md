# دليل الكود — DB: المشترك (db/shared/) — نسخة محدَّثة

> `db/shared/` — الأدوات المشتركة: الاتصالات، الأصناف، التصنيفات، الإعدادات، JSON، جسر العناصر المشتركة.
> **آخر تحديث:** يعكس الكود الفعلي المُرفَق — يُستخدم بدلاً من `db_08_shared.md`

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
# [تحسين 8] connection مشترك cached بدل فتح/غلق في كل استدعاء
#
# منطق التحقق من صلاحية الـ cache:
#   1. لو cached_conn is not None AND cached_cid == current_cid:
#      → cached_conn.execute("SELECT 1") — لو نجح يرجعه
#      → لو فشل (مات) → ينشئ جديد
#   2. غير ذلك → get_central_connection() → يُحدِّث الـ cache
#
# مقبول لأن: read-only + single-threaded (PyQt) + يُبطَل عند تغيير الشركة
# ملاحظة: يستخدم SELECT 1 للتحقق من الاتصال (بخلاف ProtectedConnection)

invalidate_central_conn_cache()
# [تحسين 8] يُغلق الـ connection القديم ويُصفِّر الـ cache
# استدعه عند تغيير الشركة النشطة
```

### BOM Columns Cache

```python
_bom_cols_cache: dict[str, set] = {}
# key: db_path من PRAGMA database_list أو str(id(conn)) كـ fallback

_get_bom_cols(conn) -> set
# PRAGMA database_list → path → cache lookup أو PRAGMA table_info(bom)

invalidate_bom_cols_cache(conn=None)
# conn=None → clear() | conn → pop(path, None)
# استدعه بعد أي migration يُضيف أعمدة لجدول bom
```

### Shared ID Utilities — [A-02] المصدر الوحيد

```python
is_shared_id(item_id) -> bool
# isinstance(item_id, str) AND str(item_id).startswith("shared:")
# مثال: is_shared_id("shared:42") → True | is_shared_id(42) → False

extract_shared_id(item_id) -> int | None
# "shared:42" → 42 | أي صيغة أخرى → None
# int(str(item_id).split(":")[1]) مع try/except
```

> ⚠️ **المصدر الوحيد لهذه الدوال** — `shared_items_bridge.py` يُعيد تصديرهما من هنا.
> الكود الجديد يستورد مباشرة من `db.shared.items_repo`.

### Items

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
# المشترك: id="shared:{n}", is_shared=True (عبر _fetch_shared_for_type)

fetch_item(conn, item_id) -> row | _SharedItemRow | None
# لو is_shared_id(item_id) → _fetch_shared_item_as_row(extract_shared_id)
# لو int → SELECT من items JOIN categories WHERE id=?
```

**`_fetch_shared_item_as_row(shared_item_id: int) -> _SharedItemRow | None`:**
```python
# [تحسين 8] يستخدم _get_central_conn_cached() بدل فتح جديد
# لو الـ cache تلف → _central_conn_cache["conn"] = None + يرجع None
# يبني _SharedItemRow مع: id="shared:{n}", name, type, price, total_qty, ...
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
# لو company_state.is_ready=False → يرجع {type: [] for type in types}
# لو الـ cache تلف → _central_conn_cache["conn"] = None
# يرجع: {type: [item_dict, ...]}
```

### BOM

```python
fetch_bom(conn, parent_id: int) -> list
# لو "variant_id" في cols → يجلبه | وإلا → بدونه
# دائماً: COALESCE(waste_pct, 0) as waste_pct
# ORDER BY id

insert_bom_row(conn, parent_id, child_type, child_id, qty,
               waste_pct=0.0, variant_id=None)
# يستخدم _get_bom_cols() للتحقق من variant_id
# يستدعي _resolve_name() تلقائياً

delete_bom_row(conn, parent_id, child_type, child_id)
# DELETE WHERE parent_id=? AND child_type=? AND child_id=?

replace_bom(conn, parent_id: int, rows: list[tuple])
# rows: [(child_type, child_id, qty, waste_pct?, variant_id?), ...]
# DELETE parent_id → INSERT الجديد
# يتحقق من "variant_id" في cols مرة واحدة قبل loop
```

**ملاحظة هامة عن `replace_bom`:**
```python
# يتعامل مع: (child_type, child_id, qty) كحد أدنى
# waste_pct:  float(row[3]) لو len(row) > 3 and row[3] is not None else 0.0
# variant_id: int(row[4])   لو len(row) > 4 and row[4] is not None else None
```

### Orphans

```python
fetch_orphan_bom_rows(conn, parent_id: int) -> list[dict]
# يتحقق من وجود كل child_id في جدوله:
#   raw/semi     → items
#   labor_op     → labor_ops
#   machine_op   → machine_ops
#   غيره         → exists=True (لا يُعامَل كـ orphan)
# يرجع: [{child_type, child_id, child_name, qty, waste_pct}, ...]

delete_orphan_bom_rows(conn, parent_id: int) -> int
# يستدعي fetch_orphan_bom_rows ثم يحذف كل orphan
# يرجع عدد الصفوف المحذوفة

fetch_products_with_orphan(conn, child_type, child_id) -> list[int]
# SELECT DISTINCT parent_id FROM bom WHERE child_type=? AND child_id=?

cleanup_empty_products_after_orphan_fix(conn, parent_ids: list[int]) -> list[int]
# يحذف المنتجات التي أصبح BOM-ها فارغاً (semi/final فقط)
# يرجع IDs المحذوفة
```

### كتابة الأصناف

```python
insert_item(conn, name, item_type, price=0,
            category_id=None, total_qty=None) -> int

update_item(conn, item_id, name, price,
            category_id=None, total_qty=None)

delete_item(conn, item_id)

update_item_category(conn, item_id, category_id: int | None)
# UPDATE items SET category_id=? WHERE id=?
```

**`_resolve_name(conn, child_type, child_id) -> str | None`** — داخلية:
```python
# raw/semi    → items | labor_op → labor_ops | machine_op → machine_ops
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
# [تحسين 5] SQLite Recursive CTE — O(1) query واحدة:
#   WITH RECURSIVE descendants AS (
#     SELECT id FROM categories WHERE id=?
#     UNION ALL
#     SELECT c.id FROM categories c JOIN descendants d ON c.parent_id=d.id
#   )
#   SELECT id FROM descendants
# يرجع IDs كل الأبناء والأحفاد + التصنيف نفسه
# Fallback تلقائي لـ _fetch_descendants_fallback لو الـ CTE فشل
```

**`_fetch_descendants_fallback(conn, cat_id) -> list[int]`:**
```python
# النسخة القديمة: while loop + individual queries (O(عمق الشجرة))
# تُستخدم فقط لو الـ CTE غير مدعوم (نادر جداً)
```

### الكتابة

```python
insert_category(conn, name, scope="all", color="#607d8b",
                parent_id=None, template_fields: list = None,
                default_unit="mm") -> int
# [تحسين 13] encode_json_list لـ template_fields بدل json.dumps

update_category(conn, cat_id, name, scope, color,
                parent_id=None, template_fields: list = None,
                default_unit="mm")
# يتحقق من circular reference: parent_id in fetch_descendants(cat_id)
# Raises: ValueError "لا يمكن جعل تصنيف فرعياً لأحد أبنائه"
# [تحسين 13] encode_json_list لـ template_fields

delete_category(conn, cat_id)
# DELETE FROM categories WHERE id=?
# cascade على الأبناء (SET NULL في الـ schema)
```

### عمليات مساعدة

```python
count_category_items(conn, cat_id: int) -> dict
# يجلب descendants أولاً ثم COUNT لكل جدول:
# {"عناصر": n, "عمليات عمالة": n, "عمليات تشغيل": n, "ماكينات": n}
# يستعلم: items, labor_ops, machine_ops, machines
# لو الجدول غير موجود → 0 (try/except)

build_tree(rows) -> list[dict]
# [{id, name, scope, color, parent_id, children: [...]}, ...]
# [إصلاح 5] يستخدم _row_to_dict() الآمنة

_row_to_dict(r) -> dict
# [إصلاح 5] يستخدم r.keys() للتحقق من وجود الأعمدة قبل الوصول
# scope:     افتراضي "all"     لو غير موجود
# color:     افتراضي "#607d8b" لو غير موجود
# parent_id: افتراضي None      لو غير موجود
# children:  [] دائماً
```

### Template Fields — [تحسين 13]

```python
get_template_fields(conn, cat_id: int) -> list[dict]
# decode_json_list(row["template_fields"]) → [] لو NULL أو فارغ

set_template_fields(conn, cat_id: int, fields: list[dict])
# encode_json_list(fields) → UPDATE categories

apply_template_to_dimension_set(conn_erp, conn_design,
                                 cat_id: int, set_id: int) -> int
# يجلب template_fields من erp.db (conn_erp)
# يقرأ الأسماء الموجودة في dimension_fields لتجنب التكرار
# يُضيف فقط الحقول الغير موجودة
# يرجع عدد الحقول المُضافة
# كل field: {name, label, unit, field_type, required, sort_order}
```

---

## settings_repo.py

```python
get_setting(conn, key: str, default=None)
# SELECT value FROM settings WHERE key=?
# يرجع row["value"] كـ TEXT أو default لو غير موجود
# ملاحظة: يرجع النص كما هو — استخدم float() عند قراءة الأرقام

set_setting(conn, key: str, value)
# INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
# commit تلقائي
```

**مثال صحيح:**
```python
salary = float(get_setting(conn, "monthly_salary", 3000.0))
theme  = get_setting(conn, "ui_theme", "light")
```

---

## json_utils.py

**الـ imports الصحيحة:**
```python
from db.shared.json_utils import decode_json, encode_json
from db.shared.json_utils import decode_json_list, encode_json_list
```

### دوال dict

```python
decode_json(data_str: str) -> dict
# يرجع {} عند: None، نص فارغ، JSON غير صالح، أو نتيجة ليست dict
# json.loads ثم isinstance(result, dict)

encode_json(data: dict) -> str
# يرجع '{}' لو data ليس dict أو عند أي خطأ
# json.dumps(data, ensure_ascii=False)
```

### دوال list — [تحسين 13]

```python
decode_json_list(data_str: str) -> list
# يرجع [] عند: None، نص فارغ، JSON غير صالح، أو نتيجة ليست list
# مُستخدمة في categories_repo.py لـ template_fields

encode_json_list(data: list) -> str
# يرجع '[]' لو data ليست list أو عند أي خطأ
# json.dumps(data, ensure_ascii=False)
# مُستخدمة في categories_repo.py لـ template_fields
```

**لماذا هذا الملف؟** [إصلاح 33]
```python
# قبل: كل ملف يعرِّف _decode/_encode محلياً → كود مكرر
# بعد: مصدر واحد — أي bug يُصلَح هنا يُطبَّق على الكل تلقائياً
# المستخدمون: shared_items_repo.py, shared_items_bridge.py,
#              items_repo.py, categories_repo.py
```

> ⚠️ لا تستخدم `json.loads/dumps` مباشرة في الملفات الأخرى — استورد من هنا دائماً.

---

## shared_items_bridge.py

### الـ Imports الفعلية

```python
from db.shared.json_utils import decode_json, encode_json   # [إصلاح 33]
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
# get_central_connection() — يفتح جديد في كل استدعاء
# ⚠️ يُستخدم للكتابة فقط (update/link/unlink)
# للقراءة يستخدم items_repo._get_central_conn_cached()

._get_erp_conn(self) -> ProtectedConnection
# [إصلاح 6] يتحقق من company_state.is_ready أولاً
# Raises: RuntimeError لو لا توجد شركة نشطة
```

**نمط `_conn` الداخلي:**
```python
# معظم methods تقبل _conn=None (اختياري للـ caller)
# owned = _conn is None
# conn  = _conn or self._get_central_conn()
# try: ... finally: if owned: conn.close()
```

### جلب العناصر المشتركة

```python
.fetch_shared_items_for_type(shared_type: str, _conn=None) -> list
# SELECT من company_shared_links JOIN shared_items
# WHERE company_id=? AND shared_type=? ORDER BY s.name
# يستدعي _row_to_item لكل صف
# يرجع [] لو exception (+ print الخطأ)

.fetch_items_by_type_with_shared(item_type: str) -> list
# fetch_items_by_type(erp) + fetch_shared_items_for_type
# يرجع قائمة مدمجة

.fetch_all_with_shared(item_type: str) -> list
# alias لـ fetch_items_by_type_with_shared

.fetch_shared_item_as_row(shared_item_id: int,
                           shared_type=None, _conn=None) -> dict | None
# SELECT من shared_items WHERE id=?
# يرجع None لو غير موجود أو exception
```

**`_row_to_item(row, data: dict, shared_type: str) -> dict`:**
```python
# base: {id:"shared:{n}", shared_item_id, name, type, category_id:None,
#         category_name:"🔗 مشترك", is_shared:True, updated_at}
# حسب shared_type:
#   raw        → price, total_qty
#   machine    → rate_per_hour, rate_per_unit
#   labor_op   → minutes
#   machine_op → mode, value, machine_name, rate_per_hour, rate_per_unit
```

**الفرق عن `items_repo._shared_row_to_item`:**
```python
# Bridge._row_to_item:  يحتوي updated_at، لا يضيف price=0.0 لغير raw
# items_repo._shared_row_to_item: يضيف price=0.0 لكل الأنواع، يحتوي total_qty=None
```

### تحديث عنصر مشترك

```python
.update_shared_item(shared_item_id, name, data: dict, _conn=None)
# UPDATE shared_items SET name=?, data=?, updated_at=datetime('now') WHERE id=?
# encode_json(data) للحفظ
```

### ربط / فك ربط

```python
.link_shared_item(shared_item_id, _conn=None)
# INSERT OR IGNORE INTO company_shared_links

.unlink_shared_item(shared_item_id, _conn=None)
# DELETE FROM company_shared_links WHERE shared_item_id=? AND company_id=?

.is_linked(shared_item_id, _conn=None) -> bool
# SELECT 1 — يرجع False لو exception

.batch_link(shared_item_ids: list[int])
# يفتح central connection واحد → loop INSERT OR IGNORE → commit → close

.batch_unlink(shared_item_ids: list[int])
# يفتح central connection واحد → loop DELETE → commit → close
```

### حساب التكلفة

```python
.calc_shared_raw_unit_price(shared_item_id, _conn=None) -> float
# fetch_shared_item_as_row ثم:
#   لو total_qty > 0: price / total_qty
#   وإلا: price
# يرجع 0.0 لو العنصر غير موجود
```

### Singleton helper

```python
get_bridge() -> SharedItemsBridge | None
# يرجع None لو company_state.is_ready=False أو أي exception
# SharedItemsBridge(company_state.company_id)
```

### إعادة التصدير — [A-02]

```python
# __all__ يُعيد تصدير:
from db.shared.shared_items_bridge import is_shared_id, extract_shared_id
# للتوافق مع الكود القديم — المصدر الأصلي في items_repo.py
```

---

## ملاحظات عامة

- `is_shared_id` و `extract_shared_id`: **المصدر الأصلي في `items_repo.py`** — `shared_items_bridge.py` يُعيد تصديرهما فقط [A-02].
- `json_utils`: كل الملفات تستورد منه — لا تعرِّف `_decode/_encode` محلياً [إصلاح 33].
- `_get_central_conn_cached()`: cached connection مشترك لـ `fetch_shared_for_types` و `_fetch_shared_item_as_row` — لا يُغلق إلا في `invalidate_central_conn_cache()` [تحسين 8].
- `get_costing_connection()` **محذوفة** — استخدم `get_erp_conn()` أو `get_connection("erp")` [T-03].
- `get_connection("costing")` **مُهمَل** — يُصدر DeprecationWarning ويُحوَّل لـ "erp" [إصلاح 10].
- `fetch_descendants`: Recursive CTE = O(1) query مع fallback تلقائي للـ while loop [تحسين 5].
- `build_tree`: يستخدم `_row_to_dict()` الآمنة بدل `[]` المباشر لتجنب KeyError [إصلاح 5].
- `get_linked_connection()` يفتح connection جديد في كل استدعاء — لا تستدعه متكرراً.
- `_SharedItemRow.__getattr__` يُسجِّل debug log لو key غير موجود بدل رمي AttributeError صامت.
- `insert_category/update_category`: `template_fields` تُمرَّر كـ `list` وتُشفَّر داخلياً بـ `encode_json_list` [تحسين 13].

---

## الفروق عن db_08_shared.md القديم

| الموضوع | القديم | الفعلي |
|---------|--------|--------|
| `_get_central_conn_cached` | مذكور بدون تفاصيل الـ SELECT 1 | يستخدم SELECT 1 للتحقق من الاتصال |
| `_SharedItemRow` | غير مذكور | class كامل مع `__getitem__`, `__getattr__`, `keys`, `get` |
| `_shared_row_to_item` | غير مذكور | دالة داخلية تُضيف price=0.0 لغير raw |
| `fetch_bom` في `items_repo` | يذكر variant_id فقط | لا يجلب `machine_op_row_id` — هذا في `bom_scenarios_repo` |
| `replace_bom` | يذكر 5 عناصر | يتعامل مع tuple بـ 3 عناصر كحد أدنى |
| `fetch_all_categories` sort | غير مذكور | `ORDER BY parent_id NULLS FIRST, name` |
| `fetch_categories_by_scope` | مذكور بدون أعمدة إضافية | يجلب أيضاً `template_fields`, `default_unit` |
| `get_costing_connection` | DeprecationWarning | **محذوفة** → ImportError |
| Bridge vs items_repo للـ shared | غير واضح | Bridge._row_to_item يحتوي updated_at ولا يضيف price=0.0 |