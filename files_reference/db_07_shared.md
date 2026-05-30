# دليل الكود — DB (7): أدوات مشتركة

> `db/shared/` — الاتصالات، JSON، جسر العناصر المشتركة، الأصناف، التصنيفات، الإعدادات.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [connection](#connection) | `db/shared/connection.py` |
| [json_utils](#json_utils) | `db/shared/json_utils.py` |
| [shared_items_bridge](#shared_items_bridge) | `db/shared/shared_items_bridge.py` |
| [items_repo](#items_repo) | `db/shared/items_repo.py` |
| [categories_repo](#categories_repo) | `db/shared/categories_repo.py` |
| [settings_repo](#settings_repo) | `db/shared/settings_repo.py` |

---

## connection

### `db/shared/connection.py`

```python
get_central_connection() -> sqlite3.Connection

get_connection(db="erp") -> ProtectedConnection
# db: "erp" | "accounting" | "inventory" | "orders" | "designs"
# ⚠️ يرمي RuntimeError لو لا توجد شركة نشطة
# "costing" مُهمَل [إصلاح 10] → DeprecationWarning + يُحوَّل لـ "erp"
```

> ⚠️ **[T-03]** `get_costing_connection()` محذوفة — ImportError واضح.
> البديل: `company_state.get_erp_conn()` أو `get_connection("erp")`

```python
get_accounting_connection() -> ProtectedConnection
get_inventory_connection() -> ProtectedConnection

get_linked_connection(primary="inventory", attach=None) -> sqlite3.Connection
# connection مع ATTACH لـ DBs إضافية للـ JOIN
```

---

## json_utils

### `db/shared/json_utils.py`

```python
decode_json(data_str: str) -> dict        # JSON → dict | {} عند الفشل
encode_json(data: dict) -> str            # dict → JSON | "{}"
decode_json_list(data_str: str) -> list   # JSON → list | []
encode_json_list(data: list) -> str       # list → JSON | "[]"
# [تحسين 13] مُستخدمة في categories_repo لـ template_fields
```

---

## shared_items_bridge

### `db/shared/shared_items_bridge.py`

```python
SharedItemsBridge(company_id: int)
# [إصلاح 33] يستخدم decode_json/encode_json من json_utils
# [A-02] is_shared_id و extract_shared_id مُعادان تصديرهما من items_repo

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

# re-exports من items_repo [A-02]:
is_shared_id(item_id) -> bool
extract_shared_id(item_id) -> int | None
```

---

## items_repo

### `db/shared/items_repo.py`

#### Central Connection Cache

```python
_get_central_conn_cached() -> Connection
# [تحسين 8] connection مشترك مرتبط بـ company_id — لا فتح/غلق متكرر
invalidate_central_conn_cache()
# يُستدعى عند تغيير الشركة النشطة
```

#### Shared ID Utilities — [A-02] المصدر الوحيد

```python
is_shared_id(item_id) -> bool
extract_shared_id(item_id) -> int | None
# "shared:42" → 42
```

#### CRUD

```python
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
```

#### BOM

```python
fetch_bom(conn, parent_id) -> list
insert_bom_row(conn, parent_id, child_type, child_id, qty,
               waste_pct=0.0, variant_id=None)
delete_bom_row(conn, parent_id, child_type, child_id)
replace_bom(conn, parent_id, rows: list[tuple])
# rows: [(child_type, child_id, qty, waste_pct, variant_id), ...]

fetch_orphan_bom_rows(conn, parent_id) -> list[dict]
delete_orphan_bom_rows(conn, parent_id) -> int
fetch_products_with_orphan(conn, child_type, child_id) -> list[int]
cleanup_empty_products_after_orphan_fix(conn, parent_ids: list) -> list[int]
```

#### Cache

```python
invalidate_bom_cols_cache(conn=None)
# استدعه بعد أي migration يضيف أعمدة لجدول bom
invalidate_central_conn_cache()
```

#### Shared Fetching

```python
fetch_shared_for_types(company_id=None, types: list=None) -> dict
# [تحسين 11] batch query — {type: [items]}
```

---

## categories_repo

### `db/shared/categories_repo.py`

```python
fetch_all_categories(conn, scope=None) -> list
fetch_categories_by_scope(conn, scope) -> list
fetch_category(conn, cat_id) -> row

fetch_descendants(conn, cat_id) -> list[int]
# [تحسين 5] SQLite Recursive CTE — O(1) query
# Fallback تلقائي للـ while loop لو CTE غير مدعوم

insert_category(conn, name, scope="all", color="#607d8b", parent_id=None,
                template_fields=None, default_unit="mm") -> int
# [تحسين 13] يستخدم encode_json_list من json_utils

update_category(conn, cat_id, name, scope, color, parent_id=None,
                template_fields=None, default_unit="mm")
# يتحقق من circular reference تلقائياً

delete_category(conn, cat_id)
count_category_items(conn, cat_id) -> dict
# {"عناصر": n, "عمليات عمالة": n, "عمليات تشغيل": n, "ماكينات": n}

build_tree(rows) -> list[dict]
# [إصلاح 5] آمن من KeyError عبر _row_to_dict()
# كل node: {id, name, scope, color, parent_id, children:[...]}

get_template_fields(conn, cat_id) -> list[dict]
set_template_fields(conn, cat_id, fields: list[dict])
apply_template_to_dimension_set(conn_erp, conn_design, cat_id, set_id) -> int
```

**الـ scopes المتاحة:** `all | raw | semi | final | labor | machine | pricing | design`

> ⚠️ `categories` يجب أن يُنشأ أولاً في schema [إصلاح 4].

---

## settings_repo

### `db/shared/settings_repo.py`

```python
get_setting(conn, key: str, default=None) -> str | None
set_setting(conn, key: str, value)
```

> ⚠️ كل القيم مُخزَّنة كـ TEXT — استخدم `float(get_setting(...))` عند الحاجة.

---

## ملاحظات عامة DB

**1. ترتيب الإنشاء:** `categories` يجب أن يُنشأ أولاً في schema [إصلاح 4].

**2. العناصر المشتركة:** IDs بصيغة `"shared:{n}"` (string) — تحقق دائماً بـ `is_shared_id()` من `db.shared.items_repo` [A-02].

**3. الـ connections:** لا تُغلق `ProtectedConnection` مباشرة — اتركها للـ `company_state`. فقط `get_central_connection()` تحتاج `.close()`.

**4. BOM columns cache:** استدعِ `invalidate_bom_cols_cache(conn)` بعد أي migration يضيف أعمدة لجدول bom.

**5. SQLite type affinity:** جدول `settings` يخزن كل القيم كـ TEXT — استخدم `float(get_setting(...))` عند الحاجة [إصلاح 5].

**6. الـ accounting.db:** تحقق من `_verify_conn_is_accounting()` قبل أي seed أو write لتجنب الكتابة على `erp.db` بالخطأ [إصلاح 9 + 11 + Q-01].

**7. الـ WACC:** حساب `avg_cost` في المخزن تلقائي في `record_inventory_move()` — لا تحسبه يدوياً.

**8. Thread Safety:** `CompanyState.set_active()` آمن للـ threads عبر `_invalidate_pending` Event [C-03]. استخدم `company_state.wait_for_invalidate()` من AppState قبل قراءة الـ cache.

**9. Central Connection Cache:** `_get_central_conn_cached()` في `items_repo` يُقلّص فتح/غلق connections المتكرر. يُبطَل تلقائياً عند تغيير الشركة [تحسين 8].

**10. Migration Framework (orders.db):** كل migration يجب أن يكون idempotent. يُسجَّل في `schema_migrations` ويتخطى المُطبَّق [تحسين 25].