# دليل الكود — Service المخزون — نسخة محدَّثة

> `services/inventory/` — خدمة المخزون.
> **آخر تحديث:** يعكس الكود الفعلي في السياق.

> ⚠️ **تحذير مهم:** `InventoryService` يستخدم جدول `inventory_movements`
> بينما `inventory_repo.py` يستخدم `inventory_moves`.
> للوصول للبيانات الفعلية استخدم `inventory_repo.py` مباشرة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [inventory_service](#inventory_service) | `services/inventory/inventory_service.py` |
| [الاستخدام الصحيح](#الاستخدام-الصحيح) | متى تستخدم الـ Service ومتى تستخدم الـ Repo مباشرة |

---

## inventory_service

### `services/inventory/inventory_service.py`

طبقة خدمة المخزون — تُغلّف `db/inventory/inventory_repo.py` مع fallback لـ SQL مضمّن.

```python
InventoryService(conn)
```

### استراتيجية الـ Fallback

```python
# كل method تجرب import من inventory_repo أولاً
# لو (ImportError أو AttributeError) → SQL مضمَّن مباشرة
# لو Exception أخرى → logger.error + يرجع قيمة افتراضية آمنة
```

### قراءة العناصر

```python
svc.list_items(category_id=None, item_type=None, search='') -> list[dict]
# يحاول fetch_items_with_stock من repo
# Fallback SQL: _SQL_ITEMS_WITH_STOCK مع فلاتر ديناميكية
# كل عنصر dict:
#   id, name, item_type, unit, price,
#   category_id, category_name, min_stock,
#   current_stock (SUM in - out),
#   avg_unit_cost (AVG unit_cost WHERE type='in')

svc.get_item(item_id: int) -> dict | None
# يحاول fetch_item_with_stock من repo
# Fallback: يبحث في list_items الكاملة

svc.get_current_stock(item_id: int) -> float
# SQL مباشر دائماً (لا fallback لـ repo):
# SUM(CASE WHEN 'in' THEN qty WHEN 'out' THEN -qty ELSE 0)
# FROM inventory_movements WHERE item_id=?
```

### الحركات

```python
svc.list_movements(item_id=None, movement_type=None,
                   date_from=None, date_to=None,
                   limit=500) -> list[dict]
# يحاول fetch_movements من repo
# Fallback SQL: _SQL_MOVEMENTS مع فلاتر + ORDER BY date DESC, id DESC
# كل حركة dict:
#   id, item_id, item_name, movement_type,
#   quantity, unit_cost, total_cost (qty×unit_cost), date, reference, notes

svc.record_inbound(item_id: int, quantity: float,
                   unit_cost: float = 0.0,
                   date: str = None,
                   reference: str = '',
                   notes: str = '') -> int
# Raises: ValueError لو quantity <= 0
# يستدعي _record_movement(item_id, 'in', ...)

svc.record_outbound(item_id: int, quantity: float,
                    unit_cost: float = 0.0,
                    date: str = None,
                    reference: str = '',
                    notes: str = '') -> int
# Raises: ValueError لو quantity <= 0
# Raises: ValueError لو quantity > current_stock (بالعربية)
# يستدعي _record_movement(item_id, 'out', ...)

svc.delete_movement(movement_id: int) -> bool
# يحاول delete_movement من repo
# Fallback: DELETE FROM inventory_movements WHERE id=?
# يرجع False عند الفشل (لا يرمي exception)
```

**`_record_movement(item_id, movement_type, quantity, unit_cost, date, reference, notes)` — داخلية:**
```python
# date=None → datetime.date.today().isoformat()
# يحاول insert_movement من repo
# Fallback: INSERT INTO inventory_movements (...) + last_insert_rowid()
# لو فشل كل شيء → يرمي Exception (لا يبتلع الخطأ)
```

### التقارير

```python
svc.get_report(category_id=None, item_type=None) -> InventoryReport
# يستدعي list_items ثم يحسب:
#   total_value = SUM(current_stock × avg_unit_cost)
#   low_stock_list = العناصر التي min_stock > 0 و current_stock <= min_stock

svc.get_item_summary(item_id: int) -> dict
# يحاول fetch_item_summary من repo
# Fallback SQL: SUM/AVG من inventory_movements في query واحدة
# {total_in, total_out, current_stock, avg_unit_cost, movements}

svc.get_low_stock_items() -> list[dict]
# يحاول fetch_low_stock_items من repo
# Fallback: list_items ثم يفلتر: min_stock > 0 و current_stock <= min_stock

svc.update_min_stock(item_id: int, min_stock: float) -> bool
# يحاول update_item_min_stock من repo
# Fallback: UPDATE items SET min_stock=? WHERE id=?
# يرجع False عند الفشل
```

**`InventoryReport` dataclass:**
```python
@dataclass
class InventoryReport:
    items           : list  = field(default_factory=list)
    total_items     : int   = 0
    total_value     : float = 0.0
    low_stock_count : int   = 0
    low_stock_items : list  = field(default_factory=list)
```

### SQL الداخلي المضمَّن

```python
_SQL_ITEMS_WITH_STOCK
# يعمل على: items LEFT JOIN categories
#          + subquery من inventory_movements
# الأعمدة: id, name, item_type, unit, price,
#           category_id, category_name, min_stock,
#           current_stock, avg_unit_cost

_SQL_MOVEMENTS
# يعمل على: inventory_movements JOIN items
# الأعمدة: id, item_id, item_name, movement_type,
#           quantity, unit_cost,
#           total_cost (qty×unit_cost),
#           date, reference, notes
```

---

## الاستخدام الصحيح

### متى تستخدم InventoryService

```python
# ✅ للـ UI panels التي تحتاج تقارير وإحصائيات:
from services.inventory.inventory_service import InventoryService
svc = InventoryService(conn)
report = svc.get_report()
low_stock = svc.get_low_stock_items()
```

### متى تستخدم inventory_repo مباشرة

```python
# ✅ للعمليات الفعلية على البيانات (أكثر دقة):
from db.inventory.inventory_repo import (
    fetch_all_inventory,
    fetch_inventory_item,
    insert_inventory_item,
    update_inventory_item,
    delete_inventory_item,
    fetch_inventory_moves,
    fetch_recent_moves,
    record_inventory_move,
    fetch_all_inv_categories,
    insert_inv_category,
    delete_inv_category,
)

# تسجيل حركة وارد:
move_id = record_inventory_move(
    conn, inv_id=5,
    move_type='in',
    qty=100, unit_cost=25.0,
    date='2026-01-15',
    notes='شراء دفعة جديدة',
    ref_entry_id=entry_id,
    ref_entry_no='JE-00042'
)

# تسجيل حركة صادر:
record_inventory_move(
    conn, inv_id=5,
    move_type='out',
    qty=10, unit_cost=0,  # unit_cost يُحسب تلقائياً من avg_cost
    date='2026-01-16'
)

# تسوية جرد:
record_inventory_move(
    conn, inv_id=5,
    move_type='adjust',
    qty=85,  # الرصيد الجديد الكامل — ليس فرقاً
    unit_cost=0,
    date='2026-01-20',
    notes='جرد ربع سنوي'
)
```

### ربط المخزن بالمحاسبة

```python
# استخدام purchase_inventory لتسجيل شراء متكامل:
from db.accounting.accounting_inventory_repo import purchase_inventory

entry_id, move_id = purchase_inventory(
    inv_conn=inv_conn,
    acc_conn=acc_conn,
    inv_id=5,
    qty=100,
    unit_cost=25.0,
    date='2026-01-15',
    payment_account_id=211,  # حساب الدفع (مثلاً النقدية)
    notes='شراء خامات'
)
# يُنشئ قيد محاسبي (DR: مخزون / CR: نقدية)
# ويسجل حركة وارد في المخزون
```

---

## ملاحظات التصميم

- **جدول الحركات:** `inventory_movements` في InventoryService و `inventory_moves` في inventory_repo — تناقض موجود. استخدم `inventory_repo` للدقة.
- **movement_type في InventoryService:** `'in'` و `'out'` فقط — لا يدعم `'adjust'` في SQL الداخلي.
- **movement_type في inventory_repo:** `'in'` | `'out'` | `'adjust'` مدعومة كاملاً.
- **get_current_stock:** يستخدم SQL مباشر دائماً لضمان الدقة.
- **record_outbound:** يتحقق من الرصيد الحالي — يرمي ValueError بالعربية لو تجاوز.
- **delete_movement:** يرجع `False` عند الفشل (لا يرمي exception).
- **logger.error:** يُسجَّل عند كل فشل في كل method.