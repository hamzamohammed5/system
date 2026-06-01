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

طبقة خدمة المخزون — تُغلّف `db/inventory/inventory_repo.py` مع fallback لـ SQL مضمّن لضمان عمل الـ service حتى لو الـ repo لم يُنشأ بعد.

```python
InventoryService(conn)
```

#### استراتيجية الـ Fallback

```python
# كل method تجرب import من inventory_repo أولاً
# لو (ImportError أو AttributeError) → تُنفّذ SQL مضمّناً مباشرة
# لو Exception أخرى → logger.error + يرجع قيمة افتراضية آمنة
```

#### قراءة العناصر

```python
svc.list_items(category_id=None, item_type=None, search="") -> list[dict]
# يحاول fetch_items_with_stock من repo
# Fallback SQL: _SQL_ITEMS_WITH_STOCK مع فلاتر ديناميكية
# كل عنصر: id, name, item_type, unit, price,
#   category_id, category_name, min_stock,
#   current_stock (SUM in - out), avg_unit_cost (AVG unit_cost WHERE in > 0)

svc.get_item(item_id: int) -> dict | None
# يحاول fetch_item_with_stock من repo
# Fallback: يبحث في _list_items_sql (كل العناصر)

svc.get_current_stock(item_id: int) -> float
# SQL مباشر دائماً (لا repo fallback):
# SUM(CASE WHEN 'in' THEN qty WHEN 'out' THEN -qty ELSE 0)
# من inventory_movements WHERE item_id=?
```

#### الحركات

```python
svc.list_movements(item_id=None, movement_type=None,
                   date_from=None, date_to=None,
                   limit=500) -> list[dict]
# يحاول fetch_movements من repo
# Fallback SQL: _SQL_MOVEMENTS مع فلاتر ديناميكية + ORDER BY date DESC, id DESC
# كل حركة: id, item_id, item_name, movement_type,
#   quantity, unit_cost, total_cost (qty*unit_cost), date, reference, notes

svc.record_inbound(item_id, quantity, unit_cost=0.0,
                   date=None, reference="", notes="") -> int
# Raises: ValueError لو quantity <= 0
# يستدعي _record_movement(item_id, "in", ...)

svc.record_outbound(item_id, quantity, unit_cost=0.0,
                    date=None, reference="", notes="") -> int
# Raises: ValueError لو quantity <= 0
# Raises: ValueError لو quantity > current_stock
# يستدعي _record_movement(item_id, "out", ...)

svc.delete_movement(movement_id: int) -> bool
# يحاول delete_movement من repo
# Fallback: DELETE FROM inventory_movements WHERE id=?
# يرجع False عند الفشل
```

**`_record_movement(item_id, movement_type, quantity, unit_cost, date, reference, notes)`:**
```python
# date=None → datetime.date.today().isoformat()
# يحاول insert_movement من repo
# Fallback: INSERT INTO inventory_movements (...) مباشر + last_insert_rowid()
```

#### التقارير

```python
svc.get_report(category_id=None, item_type=None) -> InventoryReport
# يستدعي list_items ثم يحسب:
#   total_value = SUM(current_stock * avg_unit_cost)
#   low_stock_list = العناصر التي min_stock > 0 و current_stock <= min_stock

svc.get_item_summary(item_id: int) -> dict
# يحاول fetch_item_summary من repo
# Fallback SQL: SUM/AVG من inventory_movements في query واحدة
# {total_in, total_out, current_stock, avg_unit_cost, movements}

svc.get_low_stock_items() -> list[dict]
# يحاول fetch_low_stock_items من repo
# Fallback: list_items ثم يفلتر min_stock > 0 و current_stock <= min_stock

svc.update_min_stock(item_id: int, min_stock: float) -> bool
# يحاول update_item_min_stock من repo
# Fallback: UPDATE items SET min_stock=? WHERE id=?
# يرجع False عند الفشل
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

**SQL الداخلي المضمّن:**
```python
_SQL_ITEMS_WITH_STOCK   # يعمل على: items JOIN categories + subquery من inventory_movements
_SQL_MOVEMENTS          # يعمل على: inventory_movements JOIN items
# ملاحظة: يستخدم جدول inventory_movements (ليس inventory_moves)
```

**ملاحظات التصميم:**
- `movement_type`: `"in"` | `"out"` — الـ SQL الداخلي لا يدعم `"adjust"`.
- الـ SQL الداخلي يعمل على جدول `inventory_movements` — تأكد من اسم الجدول في الـ schema.
- `get_current_stock` يستخدم SQL مباشر دائماً (لا fallback لـ repo) لضمان الدقة.
- `record_outbound` يتحقق من الرصيد الحالي قبل التسجيل.

> ⚠️ لو الـ schema الفعلي يستخدم `inventory_repo` مكتملاً، اعتمد عليه مباشرة للدقة الكاملة. استخدم `InventoryService` كـ facade موحّد للـ UI.