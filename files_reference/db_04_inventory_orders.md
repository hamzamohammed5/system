# دليل الكود — DB (4): المخزن والطلبات

> `inventory.db` و `orders.db` — schema، أصناف المخزن، الحركات، الطلبات، العملاء.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [inventory_schema](#inventory_schema) | `db/inventory/inventory_schema.py` |
| [هيكل جداول inventory.db](#هيكل-جداول-inventorydb) | — |
| [inventory_repo](#inventory_repo) | `db/inventory/inventory_repo.py` |
| [orders_schema](#orders_schema) | `db/orders/orders_schema.py` |
| [هيكل جداول orders.db](#هيكل-جداول-ordersdb) | — |
| [customers_repo](#customers_repo) | `db/orders/customers_repo.py` |
| [orders_repo](#orders_repo) | `db/orders/orders_repo.py` |

---

## inventory_schema

### `db/inventory/inventory_schema.py`

```python
create_inventory_tables(conn)
# ينشئ في inventory.db:
#   inventory_categories — تصنيفات المخزن
#   inventory_items      — أصناف المخزن
#   inventory_moves      — حركات المخزن
# يستخدم executescript() + commit()
```

---

## هيكل جداول inventory.db

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `inventory_categories` | `id, name, color DEFAULT "#607d8b", notes` |
| `inventory_items` | `id, name, unit DEFAULT "قطعة", category_id→SET NULL, qty_on_hand DEFAULT 0, qty_min DEFAULT 0, avg_cost DEFAULT 0, costing_item_id, account_code DEFAULT "114", notes, created_at` |
| `inventory_moves` | `id, inventory_id→CASCADE, move_type CHECK("in"\|"out"\|"adjust"), qty, unit_cost DEFAULT 0, total_cost DEFAULT 0, date, ref_entry_id, ref_entry_no, notes, created_at` |

**ربط المخزن بالمحاسبة:**
- `ref_entry_id` → يُشير لـ `journal_entries.id` في `accounting.db` (بدون FK عبر DBs)
- `ref_entry_no` → رقم القيد للعرض فقط
- `account_code` → كود الحساب في `accounting.db` (افتراضي `"114"`)
- `costing_item_id` → ربط اختياري بـ `items` في `erp.db`

---

## inventory_repo

### `db/inventory/inventory_repo.py`

#### تصنيفات

```python
fetch_all_inv_categories(conn) -> list
# id, name, color, notes — ORDER BY name

insert_inv_category(conn, name, color="#607d8b", notes=None) -> int
delete_inv_category(conn, cat_id)
```

#### أصناف

```python
fetch_all_inventory(conn) -> list
# مع total_value = qty_on_hand × avg_cost
# مع category_name و category_color من JOIN

fetch_inventory_item(conn, inv_id) -> row
# SELECT * FROM inventory_items

insert_inventory_item(conn, name, unit="قطعة", qty_min=0,
                      account_code="114", category_id=None,
                      costing_item_id=None, notes=None) -> int

update_inventory_item(conn, inv_id, name, unit, qty_min,
                      account_code="114", category_id=None, notes=None)

delete_inventory_item(conn, inv_id)
# CASCADE على inventory_moves
```

#### حركات

```python
fetch_inventory_moves(conn, inv_id) -> list
# ORDER BY date DESC, id DESC

fetch_recent_moves(conn, move_type=None, limit=100) -> list
# مع item_name و unit من JOIN
# move_type=None → كل الأنواع

record_inventory_move(conn, inv_id, move_type, qty, unit_cost, date,
                      notes=None, ref_entry_id=None, ref_entry_no=None) -> int
```

**سلوك `record_inventory_move` حسب النوع:**

| `move_type` | السلوك |
|-------------|--------|
| `"in"` | يحسب `avg_cost` الجديد بـ WACC: `(old_qty × old_avg + total_cost) / new_qty` |
| `"out"` | يتحقق `qty <= old_qty + 0.0001` — ValueError لو تجاوز | `unit_cost = old_avg` |
| `"adjust"` | يضع `qty` مباشرة كـ qty_on_hand — **[تحسين 20] ValueError لو `qty < 0`** |

> ⚠️ حساب `avg_cost` تلقائي في `record_inventory_move()` — لا تحسبه يدوياً.
> ⚠️ للتعديل لكمية أقل في `adjust`: استخدم `move_type="out"` بدلاً من كمية سالبة.

---

## orders_schema

### `db/orders/orders_schema.py`

```python
create_orders_tables(conn)
# ينشئ الجداول + indexes + يُشغّل _run_migrations()

get_orders_connection() -> sqlite3.Connection
# isolation_level=None, foreign_keys=ON, journal_mode=WAL
```

**Migration Framework [تحسين 25]:**

```python
_ensure_migrations_table(conn)
# CREATE TABLE IF NOT EXISTS schema_migrations (id, name UNIQUE, applied_at)

_is_applied(conn, name: str) -> bool
# يتحقق من schema_migrations — يرجع False لو الجدول غير موجود

_mark_applied(conn, name: str)
# INSERT OR IGNORE INTO schema_migrations

_apply_migration(conn, name: str, fn)
# لو مطبَّق مسبقاً → يتخطاه
# لو فشل → يُسجّل warning ويكمل — لا يوقف التطبيق

_run_migrations(conn)
# يُطبّق كل _MIGRATIONS بالترتيب
# لو فشل _ensure_migrations_table → warning + return (لا migrations)
```

**الـ Migrations المُعرَّفة:**

| الاسم | الوصف | idempotent |
|-------|-------|-----------|
| `m001_add_internal_notes` | يضيف `internal_notes TEXT` لـ `orders` | ✓ _column_exists |
| `m002_add_customers_phone2` | يضيف `phone2 TEXT` لـ `customers` | ✓ _column_exists |
| `m003_add_orders_priority` | يضيف `priority TEXT DEFAULT "normal"` لـ `orders` | ✓ _column_exists |
| `m004_add_idx_orders_priority` | يضيف index على `priority` | ✓ IF NOT EXISTS |
| `m005_add_customer_contacts_role` | يضيف `role TEXT` لـ `customer_contacts` | ✓ _column_exists |

**إضافة migration جديد:**
```python
def _m006_my_migration(conn):
    # يجب أن يكون idempotent (IF NOT EXISTS, _column_exists, OR IGNORE)
    if not _column_exists(conn, "orders", "my_col"):
        conn.execute("ALTER TABLE orders ADD COLUMN my_col TEXT")
        conn.commit()

_MIGRATIONS = [
    ...,
    ("m006_my_migration", _m006_my_migration),
]
```

> ⚠️ [Q-02] كل migration يجب أن يكون **idempotent** — لو نجح لكن فشل `_mark_applied` (نادر جداً)، سيُعاد تطبيقه في التشغيل التالي.

---

## هيكل جداول orders.db

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `customers` | `id, code UNIQUE, name, customer_type DEFAULT "individual", phone, phone2, email, address, city, notes, is_active DEFAULT 1` |
| `customer_contacts` | `id, customer_id→CASCADE, name, role, phone, email, notes` |
| `orders` | `id, order_number UNIQUE, customer_id→RESTRICT, order_type DEFAULT "new", status DEFAULT "pending", priority DEFAULT "normal", order_date DEFAULT date("now"), due_date, delivery_date, total_amount, discount, net_amount, paid_amount, notes, internal_notes, reference_order→SET NULL` |
| `order_items` | `id, order_id→CASCADE, item_name, description, quantity DEFAULT 1 CHECK(>0), unit DEFAULT "قطعة", unit_price DEFAULT 0, discount_pct DEFAULT 0, total_price DEFAULT 0, design_ref, notes, sort_order DEFAULT 0` |
| `order_status_log` | `id, order_id→CASCADE, old_status, new_status, notes, changed_by DEFAULT "system", changed_at` |
| `schema_migrations` | `id, name UNIQUE, applied_at` [تحسين 25] |

**الـ Indexes:**
`idx_orders_customer`, `idx_orders_status`, `idx_orders_date`,
`idx_order_items_order`, `idx_status_log_order`, `idx_customers_code`,
`idx_orders_priority` (من migration m004)

**حالات الطلب:**
```
pending → confirmed → in_progress → ready → delivered
        ↘ on_hold ↗              ↘ on_hold ↗
                    ↘ cancelled ↗
cancelled → pending (فقط)
on_hold → pending | confirmed | in_progress
```

---

## customers_repo

### `db/orders/customers_repo.py`

```python
fetch_all_customers(conn, active_only=False) -> list
# مع orders_count من LEFT JOIN
# GROUP BY c.id ORDER BY c.name

fetch_customer(conn, customer_id) -> row
# كل الأعمدة بما فيها address و notes

search_customers(conn, query, limit=20) -> list
# يبحث في: name, code, phone, phone2
# is_active=1 فقط

fetch_customer_stats(conn, customer_id) -> dict
# {total_orders, delivered, cancelled, active,
#  total_value, total_paid, last_order_date}
```

```python
insert_customer(conn, name, customer_type="individual", phone="",
                phone2="", email="", address="", city="", notes="") -> int
# [إصلاح 15] يولد code بـ GLOB 'CUS-[0-9]*' بدل LIKE 'CUS-%'
# يمنع تكرار CUS-0001 عند وجود كودات بصيغة غير رقمية

update_customer(conn, customer_id, name, customer_type="individual",
                phone="", phone2="", email="", address="",
                city="", notes="", is_active=1)
# updated_at=datetime('now') تلقائياً

delete_customer(conn, customer_id) -> bool
# يرفض لو في طلبات مرتبطة (orders_count > 0)
# يرجع True لو نجح، False لو رُفض

toggle_customer_active(conn, customer_id)
# is_active = 1 - is_active
```

#### جهات الاتصال

```python
fetch_contacts(conn, customer_id) -> list   # ORDER BY id
insert_contact(conn, customer_id, name, role="", phone="",
               email="", notes="") -> int
update_contact(conn, contact_id, name, role="", phone="",
               email="", notes="")
delete_contact(conn, contact_id)
```

---

## orders_repo

### `db/orders/orders_repo.py`

#### قراءة

```python
fetch_all_orders(conn, status=None, customer_id=None,
                 order_type=None, date_from=None, date_to=None,
                 search=None) -> list
# search: يبحث في order_number, customer name, customer code
# مع customer_id, customer_name, customer_code, customer_phone
# مع ref_order_number من self JOIN

fetch_order(conn, order_id) -> row
# كل الأعمدة + customer data + ref_order_number

fetch_customer_orders(conn, customer_id) -> list
# ORDER BY created_at DESC
```

#### كتابة

```python
insert_order(conn, customer_id, order_type="new", status="pending",
             priority="normal", order_date=None, due_date=None,
             total_amount=0, discount=0, paid_amount=0,
             notes="", internal_notes="", reference_order=None,
             created_by="system") -> int
# [تحسين 22] يتحقق من وجود العميل و is_active=1
# [إصلاح 16] _next_order_number بـ GLOB 'ORD-YYYY-[0-9]*' بدل LIKE
# net_amount = total_amount - discount
# order_date الافتراضي: today
# يُسجّل في order_status_log بـ _log_status()

update_order(conn, order_id, priority="normal", due_date=None,
             total_amount=0, discount=0, paid_amount=0,
             notes="", internal_notes="",
             customer_id=None, changed_by="system") -> bool
# [C-04] customer_id اختياري:
#   None → لا تغيير في العميل (backward-compatible)
#   قيمة → تحقق من الوجود و is_active + تحديث + تسجيل في status_log
# يرجع False لو الطلب غير موجود

change_order_status(conn, order_id, new_status, notes="",
                    changed_by="system") -> bool
# لو new_status="delivered" → delivery_date = today
# يُسجّل في order_status_log

cancel_order(conn, order_id, reason="", changed_by="system") -> bool
# اختصار لـ change_order_status(..., "cancelled")

reorder(conn, original_order_id, notes="", created_by="system") -> int | None
# ينسخ بنود الطلب الأصلي — order_type="reorder"
# يستدعي _recalc_order_total بعد نسخ البنود

delete_order(conn, order_id) -> bool
# يرفض لو status ليس "pending" أو "cancelled"
# [تحسين 21] يرفض لو paid_amount > 0
```

#### بنود الطلب

```python
fetch_order_items(conn, order_id) -> list   # ORDER BY sort_order, id

insert_order_item(conn, order_id, item_name, description="",
                  quantity=1, unit="قطعة", unit_price=0,
                  discount_pct=0, design_ref="", notes="",
                  sort_order=None) -> int
# total_price = quantity × unit_price × (1 - discount_pct/100)
# sort_order الافتراضي = COUNT(order_items WHERE order_id)
# يستدعي _recalc_order_total() بعد الإضافة

update_order_item(conn, item_id, item_name, ...)
# يستدعي _recalc_order_total() بعد التعديل

delete_order_item(conn, item_id)
# يستدعي _recalc_order_total() بعد الحذف

_recalc_order_total(conn, order_id)
# يُعيد حساب total_amount = SUM(total_price)
# net_amount = total_amount - discount
```

#### سجل الحالة والملخص

```python
_log_status(conn, order_id, old_status, new_status, notes="",
            changed_by="system")
# new_status=None مسموح للملاحظات الإدارية (مثل تغيير العميل)

fetch_status_log(conn, order_id) -> list   # ORDER BY changed_at ASC

fetch_orders_summary(conn) -> dict
# {total, pending, confirmed, in_progress, ready, delivered,
#  cancelled, on_hold, urgent, total_value, total_paid}
```

#### الانتقالات المسموح بها

| من | إلى |
|----|-----|
| `pending` | confirmed, in_progress, cancelled, on_hold |
| `confirmed` | in_progress, cancelled, on_hold |
| `in_progress` | ready, cancelled, on_hold |
| `ready` | delivered, cancelled |
| `delivered` | — |
| `cancelled` | pending |
| `on_hold` | pending, confirmed, in_progress |

> ⚠️ الانتقالات مُعرَّفة في `services/orders/order_service.py` — الـ repo لا يُطبّقها، الـ service هو المسؤول.