# دليل الكود — DB (4): المخزن والطلبات

> `inventory.db` و `orders.db` — أصناف المخزن، الحركات، الطلبات، العملاء.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [هيكل جداول inventory.db](#هيكل-جداول-inventorydb) | — |
| [inventory_repo](#inventory_repo) | `db/inventory/inventory_repo.py` |
| [هيكل جداول orders.db](#هيكل-جداول-ordersdb) | — |
| [customers_repo](#customers_repo) | `db/orders/customers_repo.py` |
| [orders_repo](#orders_repo) | `db/orders/orders_repo.py` |

---

## هيكل جداول inventory.db

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `inventory_categories` | `id, name, color, notes` |
| `inventory_items` | `id, name, unit, category_id, qty_on_hand, qty_min, avg_cost, costing_item_id, account_code, notes` |
| `inventory_moves` | `id, inventory_id→CASCADE, move_type["in"\|"out"\|"adjust"], qty, unit_cost, total_cost, date, ref_entry_id, ref_entry_no, notes` |

---

## inventory_repo

### `db/inventory/inventory_repo.py`

#### تصنيفات

```python
fetch_all_inv_categories(conn) -> list
insert_inv_category(conn, name, color="#607d8b", notes=None) -> int
delete_inv_category(conn, cat_id)
```

#### أصناف

```python
fetch_all_inventory(conn) -> list         # مع total_value = qty × avg_cost
fetch_inventory_item(conn, inv_id) -> row
insert_inventory_item(conn, name, unit="قطعة", qty_min=0,
                      account_code="114", category_id=None,
                      costing_item_id=None, notes=None) -> int
update_inventory_item(conn, inv_id, name, unit, qty_min,
                      account_code="114", category_id=None, notes=None)
delete_inventory_item(conn, inv_id)
```

#### حركات

```python
fetch_inventory_moves(conn, inv_id) -> list
fetch_recent_moves(conn, move_type=None, limit=100) -> list

record_inventory_move(conn, inv_id, move_type, qty, unit_cost, date,
                      notes=None, ref_entry_id=None, ref_entry_no=None) -> int
```

**سلوك `record_inventory_move` حسب النوع:**

| `move_type` | السلوك |
|-------------|--------|
| `"in"` | يحسب `avg_cost` الجديد بـ WACC |
| `"out"` | يتحقق من الكمية الكافية — `ValueError` لو تجاوز الرصيد |
| `"adjust"` | يضع `qty` مباشرة — `ValueError` لو `qty` سالبة [تحسين 20] |

> ⚠️ حساب `avg_cost` تلقائي في `record_inventory_move()` — لا تحسبه يدوياً.

---

## هيكل جداول orders.db

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `customers` | `id, code UNIQUE, name, customer_type["individual"\|"company"], phone, phone2, email, address, city, notes, is_active` |
| `customer_contacts` | `id, customer_id→CASCADE, name, role, phone, email, notes` |
| `orders` | `id, order_number UNIQUE, customer_id→RESTRICT, order_type, status, priority, order_date, due_date, total_amount, discount, net_amount, paid_amount, notes, internal_notes` |
| `order_items` | `id, order_id→CASCADE, item_name, quantity, unit, unit_price, discount_pct, total_price, sort_order, ...` |
| `order_status_log` | `id, order_id→CASCADE, old_status, new_status, notes, changed_by, changed_at` |
| `schema_migrations` | `id, name UNIQUE, applied_at` ← [تحسين 25] |

**حالات الطلب:**
```
pending → confirmed → in_progress → ready → delivered
                 ↘ cancelled ↗        ↘ on_hold ↗
```

---

## customers_repo

### `db/orders/customers_repo.py`

```python
fetch_all_customers(conn, active_only=False) -> list   # مع orders_count
fetch_customer(conn, customer_id) -> row
search_customers(conn, query, limit=20) -> list
fetch_customer_stats(conn, customer_id) -> dict
# {total_orders, delivered, cancelled, active, total_value, total_paid, last_order_date}

insert_customer(conn, name, customer_type="individual", phone="",
                phone2="", email="", address="", city="", notes="") -> int
# [إصلاح 15] يولد code بـ GLOB بدل LIKE — آمن من تكرار CUS-0001

update_customer(conn, customer_id, name, ..., is_active=1)
delete_customer(conn, customer_id) -> bool   # يرفض لو في طلبات مرتبطة
toggle_customer_active(conn, customer_id)
```

#### جهات الاتصال

```python
fetch_contacts(conn, customer_id) -> list
insert_contact(conn, customer_id, name, role="", phone="", email="", notes="") -> int
update_contact(conn, contact_id, name, ...)
delete_contact(conn, contact_id)
```

---

## orders_repo

### `db/orders/orders_repo.py`

#### قراءة

```python
fetch_all_orders(conn, status=None, customer_id=None, order_type=None,
                 date_from=None, date_to=None, search=None) -> list
fetch_order(conn, order_id) -> row
fetch_customer_orders(conn, customer_id) -> list
```

#### كتابة

```python
insert_order(conn, customer_id, order_type="new", status="pending",
             priority="normal", order_date=None, due_date=None,
             total_amount=0, discount=0, paid_amount=0,
             notes="", internal_notes="", reference_order=None,
             created_by="system") -> int
# [تحسين 22] يتحقق من وجود العميل وكونه نشطاً
# [إصلاح 16] _next_order_number بـ GLOB بدل LIKE

update_order(conn, order_id, priority="normal", due_date=None,
             total_amount=0, discount=0, paid_amount=0, notes="",
             internal_notes="", customer_id=None, changed_by="system") -> bool
# [C-04] customer_id اختياري — None = لا تغيير

change_order_status(conn, order_id, new_status, notes="", changed_by="system") -> bool
cancel_order(conn, order_id, reason="", changed_by="system") -> bool
reorder(conn, original_order_id, notes="", created_by="system") -> int
# ينسخ الطلب القديم كطلب جديد من نوع "reorder"

delete_order(conn, order_id) -> bool
# [تحسين 21] يرفض لو paid_amount > 0
# يرفض لو status ليس pending/cancelled
```

#### بنود الطلب

```python
fetch_order_items(conn, order_id) -> list
insert_order_item(conn, order_id, item_name, description="",
                  quantity=1, unit="قطعة", unit_price=0,
                  discount_pct=0, design_ref="", notes="",
                  sort_order=None) -> int
update_order_item(conn, item_id, item_name, ...)
delete_order_item(conn, item_id)
```

#### سجل الحالة والملخص

```python
fetch_status_log(conn, order_id) -> list
fetch_orders_summary(conn) -> dict
# {total, pending, confirmed, in_progress, ready, delivered,
#  cancelled, urgent, total_value, total_paid}
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

> ⚠️ Migration Framework (orders.db): كل migration في `_MIGRATIONS` يجب أن يكون idempotent. يُسجَّل في `schema_migrations` ويتخطى المُطبَّق [تحسين 25].