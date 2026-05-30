# دليل الكود — Models & Services (5): Service المخزون + Schema الطلبات والمخزون

> `services/inventory/` — خدمة المخزون.
> إضافة تفاصيل `db/inventory/inventory_schema.py` و `db/orders/orders_schema.py`.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [inventory_service](#inventory_service) | `services/inventory/inventory_service.py` |
| [inventory_schema](#inventory_schema) | `db/inventory/inventory_schema.py` |
| [orders_schema](#orders_schema) | `db/orders/orders_schema.py` |

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
#   low_stock_items : list    # عناصر رصيدها <= min_stock

svc.get_item_summary(item_id: int) -> dict
# {total_in, total_out, current_stock, avg_unit_cost, movements}

svc.get_low_stock_items() -> list[dict]
# العناصر التي رصيدها <= min_stock (ويكون min_stock > 0)

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

- الـ service يحاول أولاً استدعاء `inventory_repo` — لو الدالة غير موجودة (`ImportError` أو `AttributeError`) يُنفِّذ SQL مباشراً كـ fallback.
- `movement_type` في هذا الـ service: `"in"` | `"out"` (مختلف عن `inventory_repo` الذي يستخدم `"in"` | `"out"` | `"adjust"`).
- الـ SQL الداخلي يعمل على جدول `inventory_movements` (وليس `inventory_moves` في `inventory_repo`) — تأكد من اسم الجدول في الـ schema الخاص بك.

> ⚠️ **تحذير:** `InventoryService` مُصمَّم كـ adapter مرن — لو الـ schema الفعلي يستخدم `inventory_repo` مكتملاً، اعتمد على `inventory_repo` مباشرة للدقة الكاملة. استخدم `InventoryService` كـ facade موحّد للـ UI.

---

## inventory_schema

### `db/inventory/inventory_schema.py`

```python
create_inventory_tables(conn)
# ينشئ في inventory.db:
#   inventory_categories — تصنيفات المخزن
#   inventory_items      — أصناف المخزن
#   inventory_moves      — حركات المخزن
```

**جداول inventory.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `inventory_categories` | `id, name, color, notes` |
| `inventory_items` | `id, name, unit, category_id→SET NULL, qty_on_hand, qty_min, avg_cost, costing_item_id, account_code DEFAULT "114", notes, created_at` |
| `inventory_moves` | `id, inventory_id→CASCADE, move_type["in"\|"out"\|"adjust"], qty, unit_cost, total_cost, date, ref_entry_id, ref_entry_no, notes, created_at` |

**ربط المخزن بالمحاسبة:**
- `ref_entry_id` → يُشير لـ `journal_entries.id` في `accounting.db` (بدون FK عبر DBs)
- `account_code` → كود الحساب في `accounting.db` للمخزون (افتراضي `"114"`)
- التحقق يتم يدوياً في `accounting_inventory_repo.purchase_inventory()`

---

## orders_schema

### `db/orders/orders_schema.py`

```python
create_orders_tables(conn)
# ينشئ في orders.db جداول + indexes + يُشغِّل _run_migrations()

get_orders_connection() -> sqlite3.Connection
# isolation_level=None, foreign_keys=ON, journal_mode=WAL
```

**Migration Framework [تحسين 25]:**

```python
_ensure_migrations_table(conn)
# ينشئ جدول schema_migrations لو غير موجود

_is_applied(conn, name: str) -> bool
_mark_applied(conn, name: str)
_apply_migration(conn, name: str, fn)
# يُطبّق migration واحد بأمان — يتخطاه لو مُطبَّق مسبقاً
# لو فشل → يُسجّل warning ويكمل (لا يوقف التطبيق)

_run_migrations(conn)
# يُطبّق كل الـ migrations في _MIGRATIONS بالترتيب
```

**الـ Migrations المُعرَّفة:**

| الاسم | الوصف |
|-------|-------|
| `m001_add_internal_notes` | يضيف `internal_notes` لـ `orders` |
| `m002_add_customers_phone2` | يضيف `phone2` لـ `customers` |
| `m003_add_orders_priority` | يضيف `priority` لـ `orders` |
| `m004_add_idx_orders_priority` | يضيف index على `priority` |
| `m005_add_customer_contacts_role` | يضيف `role` لـ `customer_contacts` |

**إضافة migration جديد:**
```python
# 1. عرّف دالة idempotent
def _m006_add_order_tags(conn):
    if not _column_exists(conn, "orders", "tags"):
        conn.execute("ALTER TABLE orders ADD COLUMN tags TEXT")
        conn.commit()

# 2. أضفها لقائمة _MIGRATIONS بالترتيب
_MIGRATIONS = [
    ...,
    ("m006_add_order_tags", _m006_add_order_tags),
]
```

> ⚠️ كل migration يجب أن يكون **idempotent** (آمن للتطبيق مرتين) — استخدم `IF NOT EXISTS`, `OR IGNORE`, `_column_exists()` للتحقق قبل التعديل. [Q-02]