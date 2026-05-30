# دليل الكود — DB (2): ERP (erp.db)

> جداول `erp.db` — التكلفة، الأصناف، التصنيفات، الإعدادات.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [schema](#schema) | `db/costing/schema.py` |
| [items_repo](#items_repo) | `db/shared/items_repo.py` |
| [categories_repo](#categories_repo) | `db/shared/categories_repo.py` |
| [settings_repo](#settings_repo) | `db/shared/settings_repo.py` |

---

## schema

### `db/costing/schema.py`

```python
init_db()
# يُهيئ companies.db فقط الآن

_init_erp_db(conn)
# يُهيئ erp.db — ينشئ: categories, items, machines, labor_ops,
#   machine_ops, bom, settings
```

**القيم الافتراضية في `settings` (كلها TEXT):**

| المفتاح | القيمة |
|---------|--------|
| `monthly_salary` | 3000 |
| `working_days` | 25 |
| `holiday_days` | 4 |
| `working_hours_day` | 8 |
| `overhead_factor` | 1.10 |
| `font_size` | 11 |

**جداول erp.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `categories` | `id, name, scope, color, parent_id, template_fields, default_unit` |
| `items` | `id, name, type["raw"\|"semi"\|"final"], price, total_qty, category_id` |
| `machines` | `id, name, rate_per_hour, rate_per_unit, category_id` |
| `labor_ops` | `id, name, minutes, category_id` |
| `machine_ops` | `id, machine_id, name, mode["time"\|"unit"], value, category_id` |
| `bom` | `id, parent_id, child_type, child_id, qty, child_name, waste_pct?, variant_id?, machine_op_row_id?, scenario_id?` |
| `settings` | `key TEXT PK, value TEXT` ← value كـ TEXT (ليس REAL) |

> ⚠️ `settings` يخزن كل القيم كـ TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.

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