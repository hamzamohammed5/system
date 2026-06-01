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

svc.get_tree(scope=None) -> list[CategoryNode]
svc.add(name, scope, color, parent_id=None) -> int
svc.update(cat_id, name, scope, color, parent_id=None)

svc.get_delete_preview(cat_id) -> DeletePreview | None
# DeletePreview.child_count, .item_count, .warning_text()

svc.delete_cascade(cat_id) -> int  # يرجع عدد التصنيفات المحذوفة
```

**`CategoryNode`:** `id, name, color, scope, parent_id, children`