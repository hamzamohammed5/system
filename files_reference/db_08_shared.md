# دليل الكود — DB: المشترك (db/shared/)

> `db/shared/` — الأدوات المشتركة بين كل قواعد البيانات: الاتصالات، الأصناف، التصنيفات، الإعدادات، JSON، جسر العناصر المشتركة.

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

### `db/shared/connection.py`

```python
get_central_connection() -> sqlite3.Connection
# Connection لقاعدة بيانات الشركات المركزية (companies.db)
# isolation_level=None, foreign_keys=ON, journal_mode=WAL

get_connection(db: str = "erp") -> sqlite3.Connection
# يرجع connection للشركة النشطة
# db: "erp" | "accounting" | "inventory" | "orders" | "designs"
# [إصلاح 10] get_connection("costing") يُصدر DeprecationWarning → يُحوَّل لـ "erp"
# Raises: RuntimeError لو لا توجد شركة نشطة

get_accounting_connection() -> sqlite3.Connection
# اختصار → accounting.db للشركة النشطة

get_inventory_connection() -> sqlite3.Connection
# اختصار → inventory.db للشركة النشطة

get_linked_connection(primary: str = "inventory",
                      attach: list[str] = None) -> sqlite3.Connection
# يرجع connection مع ATTACH لقواعد بيانات إضافية
# يُستخدم لـ JOIN بين قواعد البيانات المختلفة
# primary="costing" أو "erp" → كلاهما يُحوَّل لـ "erp"
```

> ⚠️ **[T-03] `get_costing_connection()` محذوفة** — استخدم `company_state.get_erp_conn()` أو `get_connection("erp")`.
> ⚠️ `get_connection("costing")` يُصدر `DeprecationWarning` — حدّث الكود لاستخدام `"erp"`.

---

## items_repo.py

### `db/shared/items_repo.py`

#### Central Connection Cache — [تحسين 8]

```python
invalidate_central_conn_cache()
# يُبطل الـ central connection cache
# استدعه عند تغيير الشركة النشطة
# يُغلق الـ connection القديم قبل المسح
```

#### BOM Columns Cache

```python
invalidate_bom_cols_cache(conn=None)
# conn=None → يمسح كل الـ cache
# conn=<connection> → يمسح cache هذا الملف فقط
# استدعه بعد أي migration يضيف أعمدة لجدول bom
```

#### Shared ID Utilities — [A-02] المصدر الوحيد

```python
is_shared_id(item_id) -> bool
# يتحقق هل الـ ID يُشير لعنصر مشترك
# العناصر المشتركة تبدأ بـ "shared:" مثل "shared:42"

extract_shared_id(item_id) -> int | None
# يستخرج الـ integer ID من "shared:42" → 42
# يرجع None لو الصيغة غير صحيحة
```

> ⚠️ `is_shared_id` و `extract_shared_id` مُعادتا تصديرهما من `shared_items_bridge.py` للتوافق القديم — المصدر الأصلي هنا فقط.

#### Items

```python
fetch_all_items(conn) -> list
# id, name, type, price, total_qty — ORDER BY name

fetch_items_by_type(conn, item_type: str) -> list
# مع category_id و category_name من JOIN
# item_type: "raw" | "semi" | "final"

fetch_items_by_type_with_shared(conn, item_type, company_id=None) -> list
# يدمج العناصر المحلية مع المشتركة
# العناصر المحلية: is_shared=False, shared_item_id=None
# العناصر المشتركة: id="shared:{n}", is_shared=True

fetch_item(conn, item_id) -> row | None
# يدعم item_id كـ int (محلي) أو "shared:{n}" (مشترك)
# للمشترك: يرجع _SharedItemRow مع نفس الـ interface

insert_item(conn, name, item_type, price=0,
            category_id=None, total_qty=None) -> int

update_item(conn, item_id, name, price,
            category_id=None, total_qty=None)

delete_item(conn, item_id)

update_item_category(conn, item_id, category_id: int | None)
```

#### BOM

```python
fetch_bom(conn, parent_id: int) -> list
# يتعامل مع وجود/غياب عمود variant_id تلقائياً

insert_bom_row(conn, parent_id, child_type, child_id,
               qty, waste_pct=0.0, variant_id=None)
# child_type: "raw" | "semi" | "labor_op" | "machine_op"

delete_bom_row(conn, parent_id, child_type, child_id)

replace_bom(conn, parent_id, rows: list[tuple])
# rows: [(child_type, child_id, qty, waste_pct?, variant_id?), ...]
# يمسح القديم ويكتب الجديد دفعة واحدة
```

#### Orphans

```python
fetch_orphan_bom_rows(conn, parent_id) -> list[dict]
# يجيب المكونات التي عنصرها اتحذف من الـ DB
# {child_type, child_id, child_name, qty, waste_pct}

delete_orphan_bom_rows(conn, parent_id) -> int
# يحذف كل الـ orphans ويرجع عددها

fetch_products_with_orphan(conn, child_type, child_id) -> list[int]
# المنتجات التي تحتوي على عنصر معين في BOM

cleanup_empty_products_after_orphan_fix(conn, parent_ids: list) -> list[int]
# يحذف المنتجات الفارغة بعد إصلاح الـ orphans
# يرجع IDs المنتجات المحذوفة
```

#### Shared Items Fetching — [تحسين 11] + [تحسين 8]

```python
fetch_shared_for_types(company_id=None, types: list = None) -> dict
# [تحسين 11] يجيب العناصر المشتركة لأكثر من نوع في connection واحد
# [تحسين 8] يستخدم _get_central_conn_cached() بدل فتح/غلق متكرر
# يرجع: {type: [item_dict, ...]}
# العناصر المشتركة بـ id="shared:{n}"
```

---

## categories_repo.py

### `db/shared/categories_repo.py`

```python
SCOPES = {
    "all": "الكل", "raw": "الخامات", "semi": "نصف مصنع",
    "final": "منتج نهائي", "labor": "العمالة",
    "machine": "التشغيل", "pricing": "التسعير", "design": "مجموعات المقاسات",
}

PRESET_COLORS = [...]   # 10 ألوان جاهزة للاستخدام
```

#### قراءة

```python
fetch_all_categories(conn, scope: str = None) -> list
# لو scope محدد: يرجع scope="all" + scope=? معاً
# لو بدون scope: كل التصنيفات
# مع parent_name من JOIN

fetch_categories_by_scope(conn, scope: str) -> list
# تصنيفات scope محدد فقط — بدون تصنيفات "all"
# مع template_fields و default_unit

fetch_category(conn, cat_id) -> row
# id, name, scope, color, parent_id, template_fields, default_unit

fetch_descendants(conn, cat_id) -> list[int]
# [تحسين 5] SQLite Recursive CTE — O(1) query بدل O(عمق الشجرة)
# يرجع IDs كل الأبناء والأحفاد + cat_id نفسه
# Fallback تلقائي للـ while loop لو الـ CTE غير مدعوم
```

#### كتابة

```python
insert_category(conn, name, scope="all", color="#607d8b",
                parent_id=None, template_fields=None,
                default_unit="mm") -> int
# [تحسين 13] يستخدم encode_json_list من json_utils لـ template_fields

update_category(conn, cat_id, name, scope, color,
                parent_id=None, template_fields=None, default_unit="mm")
# يتحقق من circular reference تلقائياً
# [تحسين 13] encode_json_list لـ template_fields

delete_category(conn, cat_id)

count_category_items(conn, cat_id) -> dict
# يبحث في: items, labor_ops, machine_ops, machines
# يشمل كل الأحفاد عبر fetch_descendants()
# يرجع: {"عناصر": n, "عمليات عمالة": n, "عمليات تشغيل": n, "ماكينات": n}
```

#### بناء الشجرة

```python
build_tree(rows) -> list[dict]
# [إصلاح 5] يستخدم _row_to_dict() الآمنة بدل [] المباشر
# يرجع شجرة هرمية: [{id, name, scope, color, parent_id, children: [...]}, ...]
```

#### Template Fields

```python
get_template_fields(conn, cat_id) -> list[dict]
# [تحسين 13] يستخدم decode_json_list من json_utils

set_template_fields(conn, cat_id, fields: list[dict])
# [تحسين 13] encode_json_list

apply_template_to_dimension_set(conn_erp, conn_design, cat_id, set_id) -> int
# يُطبّق حقول القالب على مجموعة مقاسات
# يتجنب إضافة حقل موجود مسبقاً
# يرجع عدد الحقول المضافة
```

---

## settings_repo.py

### `db/shared/settings_repo.py`

```python
get_setting(conn, key: str, default=None)
# يقرأ قيمة من جدول settings
# يرجع النص كما هو من DB، أو default لو المفتاح مش موجود
# ملاحظة: القيم مُخزَّنة كـ TEXT — استخدم float() عند قراءة الأرقام

set_setting(conn, key: str, value)
# INSERT OR REPLACE INTO settings
```

**مثال استخدام:**
```python
salary = float(get_setting(conn, "monthly_salary", 3000.0))
theme  = get_setting(conn, "ui_theme", "light")
```

---

## json_utils.py

### `db/shared/json_utils.py`

دوال JSON مشتركة — المصدر الوحيد بدل `json.loads/dumps` المكرر في الملفات.

```python
decode_json(data_str: str) -> dict
# يحول نص JSON إلى dict بشكل آمن
# يرجع {} عند: None، نص فارغ، JSON غير صالح، أو نتيجة ليست dict

encode_json(data: dict) -> str
# يحول dict إلى نص JSON مع دعم العربية (ensure_ascii=False)
# يرجع '{}' عند أي خطأ أو لو data ليس dict

decode_json_list(data_str: str) -> list
# [تحسين 13] يحول نص JSON إلى list بشكل آمن
# يرجع [] عند: None، نص فارغ، JSON غير صالح، أو نتيجة ليست list
# يُستخدم في categories_repo.py لـ template_fields

encode_json_list(data: list) -> str
# [تحسين 13] يحول list إلى نص JSON مع دعم العربية
# يرجع '[]' عند أي خطأ أو لو data ليست list
```

**الاستخدام:**
```python
from db.shared.json_utils import decode_json, encode_json
from db.shared.json_utils import decode_json_list, encode_json_list

# dict
data = decode_json(row["data"])          # آمن — يرجع {} لو NULL
json_str = encode_json({"price": 50.0})

# list
fields = decode_json_list(row["template_fields"])   # آمن — يرجع [] لو NULL
fields_json = encode_json_list([{"name": "width"}])
```

> ⚠️ لا تستخدم `json.loads/dumps` مباشرة في الملفات الأخرى — استورد من هنا دائماً لضمان معالجة الأخطاء الموحدة.

---

## shared_items_bridge.py

### `db/shared/shared_items_bridge.py`

جسر العناصر المشتركة — يقرأ من `companies.db` مباشرة ويدمجها مع `erp.db`.

```python
SharedItemsBridge(company_id: int)
# SHARED_CATEGORY_NAME = "🔗 مشترك"
# SHARED_ICON = "🔗"
```

#### جلب العناصر المشتركة

```python
bridge.fetch_shared_items_for_type(shared_type: str, _conn=None) -> list
# shared_type: "raw" | "machine" | "labor_op" | "machine_op"
# يرجع list of dicts مع id="shared:{n}"

bridge.fetch_items_by_type_with_shared(item_type: str) -> list
# يدمج المحلي + المشترك

bridge.fetch_all_with_shared(item_type: str) -> list
# alias لـ fetch_items_by_type_with_shared
```

#### جلب عنصر واحد

```python
bridge.fetch_shared_item_as_row(shared_item_id, shared_type=None,
                                 _conn=None) -> dict | None
# يرجع dict مع نفس الـ interface كـ عنصر محلي
```

#### تعديل

```python
bridge.update_shared_item(shared_item_id, name, data: dict, _conn=None)
# updated_at=datetime('now') تلقائياً
```

#### ربط / فك ربط

```python
bridge.link_shared_item(shared_item_id, _conn=None)
bridge.unlink_shared_item(shared_item_id, _conn=None)
bridge.is_linked(shared_item_id, _conn=None) -> bool

bridge.batch_link(shared_item_ids: list[int])
bridge.batch_unlink(shared_item_ids: list[int])
```

#### حساب تكلفة

```python
bridge.calc_shared_raw_unit_price(shared_item_id, _conn=None) -> float
# price ÷ total_qty لو total_qty > 0 | وإلا price
```

#### Singleton helper

```python
get_bridge() -> SharedItemsBridge | None
# يرجع None لو لا توجد شركة نشطة
# يستخدم company_state.company_id تلقائياً
```

#### إعادة تصدير — [A-02]

```python
# هذه الدوال مُعادة تصديرها من items_repo (المصدر الأصلي):
from db.shared.shared_items_bridge import is_shared_id, extract_shared_id
# للكود الجديد: استورد مباشرة من db.shared.items_repo
```

---

## ملاحظات عامة

- **`is_shared_id` و `extract_shared_id`**: المصدر الأصلي في `items_repo.py` — `shared_items_bridge.py` يُعيد تصديرهما فقط للتوافق.
- **`json_utils`**: كل الملفات الأخرى (`shared_items_repo.py`, `shared_items_bridge.py`) تستورد منه بدل تعريف `_decode/_encode` محلية.
- **Central Connection Cache** في `items_repo.py`: connection مشترك مرتبط بالـ company_id النشط — يُبطَل تلقائياً عند تغيير الشركة عبر `invalidate_central_conn_cache()`.
- **`get_connection("costing")`** مُهمَل — استخدم `"erp"` أو `company_state.get_erp_conn()`.
- لا تستدعِ `get_linked_connection()` كثيراً — كل استدعاء يفتح connection جديد. احفظه في متغير.