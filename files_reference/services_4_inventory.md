# دليل الكود — Service المخزون

> `services/inventory/` — خدمة المخزون.
> لـ `db/inventory/inventory_schema.py` و `db/orders/orders_schema.py` → راجع `db_04_inventory_orders.md`

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [inventory_service](#inventory_service) | `services/inventory/inventory_service.py` |

---

## inventory_service

### `services/inventory/inventory_service.py`

طبقة خدمة المخزون — تُغلّف `db/inventory/inventory_repo.py` مع fallback لـ SQL مباشر لو الـ repo لم يُنشأ بعد.

```python
InventoryService(conn)
```

#### قراءة العناصر

```python
svc.list_items(category_id=None, item_type=None, search="") -> list[dict]
# كل عنصر يحتوي: id, name, item_type, unit, price,
#   category_id, category_name, min_stock,
#   current_stock, avg_unit_cost

svc.get_item(item_id: int) -> dict | None

svc.get_current_stock(item_id: int) -> float
# يحسب الرصيد = SUM(in) - SUM(out)
```

#### الحركات

```python
svc.list_movements(item_id=None, movement_type=None,
                   date_from=None, date_to=None,
                   limit=500) -> list[dict]
# كل حركة: id, item_id, item_name, movement_type,
#   quantity, unit_cost, total_cost, date, reference, notes

svc.record_inbound(item_id, quantity, unit_cost=0.0,
                   date=None, reference="", notes="") -> int
# Raises: ValueError لو quantity <= 0

svc.record_outbound(item_id, quantity, unit_cost=0.0,
                    date=None, reference="", notes="") -> int
# Raises: ValueError لو quantity <= 0
# Raises: ValueError لو quantity > current_stock

svc.delete_movement(movement_id: int) -> bool
```

#### التقارير

```python
svc.get_report(category_id=None, item_type=None) -> InventoryReport
# InventoryReport:
#   items           : list
#   total_items     : int
#   total_value     : float   # SUM(current_stock × avg_unit_cost)
#   low_stock_count : int
#   low_stock_items : list

svc.get_item_summary(item_id: int) -> dict
# {total_in, total_out, current_stock, avg_unit_cost, movements}

svc.get_low_stock_items() -> list[dict]
svc.update_min_stock(item_id: int, min_stock: float) -> bool
```

**`InventoryReport` dataclass:**
```python
@dataclass
class InventoryReport:
    items           : list   = field(default_factory=list)
    total_items     : int    = 0
    total_value     : float  = 0.0
    low_stock_count : int    = 0
    low_stock_items : list   = field(default_factory=list)
```

**ملاحظات التصميم:**
- الـ service يحاول أولاً استدعاء `inventory_repo` — لو الدالة غير موجودة يُنفِّذ SQL مباشراً كـ fallback.
- `movement_type`: `"in"` | `"out"` (مختلف عن `inventory_repo` الذي يدعم `"adjust"` أيضاً).
- الـ SQL الداخلي يعمل على جدول `inventory_movements` — تأكد من اسم الجدول في الـ schema.

> ⚠️ لو الـ schema الفعلي يستخدم `inventory_repo` مكتملاً، اعتمد عليه مباشرة للدقة الكاملة. استخدم `InventoryService` كـ facade موحّد للـ UI.