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
svc.get(item_id) -> ItemResult | None
svc.list_by_type(item_type) -> list[ItemResult]

svc.add(name, price, item_type, category_id=None, total_qty=None) -> int
svc.update(item_id, name, price, category_id=None, total_qty=None)

svc.get_delete_preview(item_id) -> DeletePreview | None
# DeletePreview.usage_count — عدد المنتجات التي تستخدمه في BOM
# DeletePreview.can_delete() -> bool

svc.get_usage_count(item_id) -> int
# [تحسين 18] يشمل كل child_types: raw, semi, labor_op, machine_op

svc.delete(item_id) -> bool  # يرفض لو مستخدم في BOM
svc.force_delete(item_id)    # يحذف حتى لو مستخدم
```

**`ItemResult`:** `id, name, price, item_type, category_id, total_qty`

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
# مطلوبة من managers/category.py و combo/category.py

svc.build_tree(rows: list) -> list
# يبني هيكل شجري من list of dicts
# rows: نتيجة get_all() — يرجع list of dicts مع "children" key

svc.get_one(cat_id: int) -> dict | None
# يرجع تصنيف واحد بالـ id كـ dict
# مطلوبة من managers/category.py (load_for_edit)

svc.get_descendants(cat_id: int) -> set
# يرجع set من IDs كل الأبناء والأحفاد
# مطلوبة من managers/category.py (exclude في parent combo)

svc.count_items(cat_id: int) -> dict
# يرجع dict بعدد العناصر المرتبطة بالتصنيف
# مطلوبة من managers/category.py (_add_items)

svc.get_tree(scope: str = None) -> list[CategoryNode]
# يرجع شجرة التصنيفات كـ dataclasses (للكود القديم)
```

#### كتابة

```python
svc.add(name, scope, color, parent_id=None) -> int
svc.update(cat_id, name, scope, color, parent_id=None)
```

#### حذف

```python
svc.get_delete_preview(cat_id) -> DeletePreview | None
# DeletePreview.child_count, .item_count, .warning_text()

svc.delete_cascade(cat_id) -> int  # يرجع عدد التصنيفات المحذوفة
```

**`CategoryNode`:** `id, name, color, scope, parent_id, children`

**`DeletePreview`:**
```python
# cat_name    : str
# child_count : int
# item_counts : dict   # {"عناصر": n, "ماكينات": n, ...}
# .item_count -> int   # مجموع كل الأعداد
# .warning_text() -> str
```