# دليل الكود — Services المشتركة (services/shared/)

> `services/shared/` — خدمات الأصناف والتصنيفات المشتركة بين كل الوحدات.
> **الملفات الفعلية:** `item_service.py`, `category_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [item_service.py](#item_servicepy) | ItemService — CRUD الأصناف مع validation |
| [category_service.py](#category_servicepy) | CategoryService — CRUD التصنيفات مع شجرة هرمية |

---

## item_service.py

### Imports (top-level)

```python
from db.shared.items_repo import (
    fetch_item, fetch_items_by_type,
    insert_item, update_item, delete_item,
)
```

### Dataclasses

```python
@dataclass
class ItemValidationError:
    field   : str
    message : str

@dataclass
class ItemResult:
    id          : int
    name        : str
    price       : float
    item_type   : str
    category_id : int | None
    total_qty   : float | None

@dataclass
class DeletePreview:
    item_name  : str
    usage_count: int
    # can_delete() → usage_count == 0
    # warning_text() → رسالة تحذير لو usage_count > 0
```

### ItemService

```python
ItemService(conn)

# Validation
svc.validate(name, price) -> list[ItemValidationError]
# name.strip() غير فارغ + price >= 0

# قراءة
svc.get(item_id) -> ItemResult | None
svc.list_by_type(item_type) -> list[ItemResult]

# كتابة
svc.add(name, price, item_type, category_id=None, total_qty=None) -> int
# يستدعي validate() أولاً — Raises ValueError لو فشل

svc.update(item_id, name, price, category_id=None, total_qty=None)
# يستدعي validate() أولاً — Raises ValueError لو فشل

# حذف
svc.get_delete_preview(item_id) -> DeletePreview | None
svc.get_usage_count(item_id) -> int
svc.delete(item_id) -> bool   # False لو مستخدم في BOM
svc.force_delete(item_id)     # يحذف حتى لو مستخدم — للحالات الاستثنائية
```

**`get_usage_count` — [تحسين 18]:**
```python
# يشمل كل child_types:
SELECT COUNT(DISTINCT parent_id) FROM bom
WHERE child_id=? AND child_type IN ('raw','semi','labor_op','machine_op')
# القديم: كان يبحث في ('raw','semi') فقط
```

---

## category_service.py

### Imports (top-level)

```python
from db.shared.categories_repo import (
    fetch_category, fetch_descendants, fetch_all_categories,
    insert_category, update_category, delete_category,
    count_category_items, build_tree,
)
```

### Dataclasses

```python
@dataclass
class DeletePreview:
    cat_name    : str
    child_count : int
    item_counts : dict  # {"عناصر": n, "ماكينات": n, ...}
    # item_count → sum(item_counts.values())
    # warning_text() → رسالة تحذير

@dataclass
class CategoryNode:
    id, name, color, scope, parent_id : ...
    children : list[CategoryNode]
```

### CategoryService

```python
CategoryService(conn)
```

#### دوال القراءة (مطلوبة من managers/category.py و combo/category.py)

```python
svc.get_all(scope: str = "all") -> list
# يرجع list of dicts — يستدعي fetch_all_categories ثم [dict(r) for r in rows]

svc.build_tree(rows: list) -> list
# يبني هيكل شجري من list of dicts
# يمرر rows لـ build_tree من categories_repo

svc.get_one(cat_id: int) -> dict | None
# يرجع تصنيف واحد بالـ id كـ dict

svc.get_descendants(cat_id: int) -> set
# يرجع set من IDs كل الأبناء والأحفاد
# يستدعي fetch_descendants ثم set(...)

svc.count_items(cat_id: int) -> dict
# {"عناصر": n, "عمليات عمالة": n, ...}
```

#### الكتابة

```python
svc.add(name, scope, color, parent_id=None) -> int
# Raises: ValueError لو name.strip() فارغ

svc.update(cat_id, name, scope, color, parent_id=None)
# Raises: ValueError لو name.strip() فارغ
```

#### الحذف

```python
svc.get_delete_preview(cat_id) -> DeletePreview | None
# child_count = len(descendants) - 1  (يطرح التصنيف نفسه)

svc.delete_cascade(cat_id) -> int
# يحذف التصنيف وكل أبنائه بالترتيب العكسي
# يرجع عدد التصنيفات المحذوفة
```

#### Legacy

```python
svc.get_tree(scope: str = None) -> list[CategoryNode]
# يرجع شجرة التصنيفات كـ dataclasses (للكود القديم)
# يستدعي get_all + build_tree + _to_node داخلياً
```

---

## ملاحظات

- `get_usage_count` يفحص جدول `bom` في `erp.db` — تأكد أن `conn` هو `erp_conn` [تحسين 18].
- `delete_cascade` يحذف بالترتيب العكسي `sorted(descendants, reverse=True)` لتجنب FK violations.
- `get_all` + `build_tree` هما الزوج المستخدم في `managers/category.py` و `combo/category.py`.