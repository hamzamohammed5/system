# دليل الكود — Services المشتركة

> `services/shared/` — خدمات الأصناف والتصنيفات المشتركة بين كل الوحدات.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [item_service](#item_service) | `services/shared/item_service.py` |
| [category_service](#category_service) | `services/shared/category_service.py` |

---

## item_service

### `services/shared/item_service.py`

```python
ItemService(conn)

svc.validate(name, price) -> list[ItemValidationError]
# يتحقق: name.strip() غير فارغ، price >= 0 (السالب ممنوع)

svc.get(item_id) -> ItemResult | None
svc.list_by_type(item_type) -> list[ItemResult]

svc.add(name, price, item_type, category_id=None, total_qty=None) -> int
# يستدعي validate() أولاً — يرمي ValueError لو فشل
svc.update(item_id, name, price, category_id=None, total_qty=None)
# يستدعي validate() أولاً — يرمي ValueError لو فشل

svc.get_delete_preview(item_id) -> DeletePreview | None
# DeletePreview.usage_count — عدد المنتجات التي تستخدمه في BOM
# DeletePreview.can_delete() -> bool

svc.get_usage_count(item_id) -> int
# [تحسين 18] يشمل كل child_types: raw, semi, labor_op, machine_op
# SELECT COUNT(DISTINCT parent_id) FROM bom WHERE child_id=? AND child_type IN (...)

svc.delete(item_id) -> bool
# يرفض ويرجع False لو مستخدم في BOM (preview.can_delete() = False)
svc.force_delete(item_id)    # يحذف حتى لو مستخدم
```

**`ItemResult`:** `id, name, price, item_type, category_id, total_qty`

**`ItemValidationError`:** `field, message`

**`DeletePreview`:** `item_name, usage_count`
- `.can_delete() -> bool` — `usage_count == 0`
- `.warning_text() -> str`

**Imports (top-level):**
```python
from db.shared.items_repo import (
    fetch_item, fetch_items_by_type,
    insert_item, update_item, delete_item,
)
```

---

## category_service

### `services/shared/category_service.py`

```python
CategoryService(conn)
```

#### قراءة

```python
svc.get_all(scope: str = "all") -> list
# يرجع كل التصنيفات كـ list of dicts
# يستدعي fetch_all_categories ثم [dict(r) for r in rows]
# مطلوبة من managers/category.py و combo/category.py

svc.build_tree(rows: list) -> list
# يبني هيكل شجري من list of dicts
# rows: نتيجة get_all() — يُمرِّرها لـ build_tree من categories_repo
# يرجع list of dicts مع "children" key
# مطلوبة من managers/category.py و combo/category.py

svc.get_one(cat_id: int) -> dict | None
# يرجع تصنيف واحد بالـ id كـ dict
# مطلوبة من managers/category.py (load_for_edit)

svc.get_descendants(cat_id: int) -> set
# يرجع set من IDs كل الأبناء والأحفاد
# يستدعي fetch_descendants ثم set(...)
# مطلوبة من managers/category.py (exclude في parent combo)

svc.count_items(cat_id: int) -> dict
# يرجع dict بعدد العناصر المرتبطة بالتصنيف
# مطلوبة من managers/category.py (_add_items)

svc.get_tree(scope: str = None) -> list[CategoryNode]
# يرجع شجرة التصنيفات كـ dataclasses (للكود القديم)
# يستدعي get_all + build_tree + _to_node داخلياً
```

#### كتابة

```python
svc.add(name, scope, color, parent_id=None) -> int
# Raises: ValueError لو name.strip() فارغ
svc.update(cat_id, name, scope, color, parent_id=None)
# Raises: ValueError لو name.strip() فارغ
```

#### حذف

```python
svc.get_delete_preview(cat_id) -> DeletePreview | None
# DeletePreview.cat_name, .child_count, .item_counts, .item_count, .warning_text()
# child_count = len(descendants) - 1  (يطرح التصنيف نفسه)

svc.delete_cascade(cat_id) -> int  # يرجع عدد التصنيفات المحذوفة
# يجلب descendants → يحذف بالترتيب العكسي (sorted reverse=True)
```

**`CategoryNode`:** `id, name, color, scope, parent_id, children`

**`DeletePreview`:**
```python
# cat_name    : str
# child_count : int
# item_counts : dict   # {"عناصر": n, "ماكينات": n, ...}
# .item_count -> int   # مجموع كل الأعداد عبر sum(item_counts.values())
# .warning_text() -> str
```

**Imports (top-level):**
```python
from db.shared.categories_repo import (
    fetch_category, fetch_descendants, fetch_all_categories,
    insert_category, update_category, delete_category,
    count_category_items, build_tree,
)
```