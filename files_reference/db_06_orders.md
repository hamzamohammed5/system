# دليل الكود — DB: الطلبات (db/orders/)

> جداول `orders.db` — العملاء، الطلبات، بنود الطلبات، سجل الحالة.

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [orders_schema.py](#orders_schemapy) | إنشاء جداول orders.db والـ migrations |
| [customers_repo.py](#customers_repopy) | CRUD العملاء وجهات الاتصال |
| [orders_repo.py](#orders_repopy) | CRUD الطلبات وبنودها |

---

## orders_schema.py

```python
create_orders_tables(conn)
# ينشئ الجداول + indexes + يُشغّل _run_migrations()

get_orders_connection() -> sqlite3.Connection
# isolation_level=None, foreign_keys=ON, journal_mode=WAL
```

**هيكل الجداول:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `customers` | `id, code UNIQUE, name, customer_type DEFAULT "individual", phone, phone2, email, address, city, notes, is_active DEFAULT 1` |
| `customer_contacts` | `id, customer_id→CASCADE, name, role, phone, email, notes` |
| `orders` | `id, order_number UNIQUE, customer_id→RESTRICT, order_type DEFAULT "new", status DEFAULT "pending", priority DEFAULT "normal", order_date, due_date, delivery_date, total_amount, discount, net_amount, paid_amount, notes, internal_notes, reference_order→SET NULL` |
| `order_items` | `id, order_id→CASCADE, item_name, description, quantity DEFAULT 1 CHECK(>0), unit DEFAULT "قطعة", unit_price, discount_pct, total_price, design_ref, notes, sort_order` |
| `order_status_log` | `id, order_id→CASCADE, old_status, new_status, notes, changed_by DEFAULT "system", changed_at` |
| `schema_migrations` | `id, name UNIQUE, applied_at` |

**الـ Indexes:**
`idx_orders_customer`, `idx_orders_status`, `idx_orders_date`,
`idx_order_items_order`, `idx_status_log_order`, `idx_customers_code`,
`idx_orders_priority` (من migration m004)

#### Migration Framework [تحسين 25]

```python
_ensure_migrations_table(conn)
_is_applied(conn, name: str) -> bool
_mark_applied(conn, name: str)
_apply_migration(conn, name: str, fn)
# لو مطبَّق مسبقاً → يتخطاه | لو فشل → warning ويكمل
_run_migrations(conn)
```

**الـ Migrations المُعرَّفة:**

| الاسم | الوصف |
|-------|-------|
| `m001_add_internal_notes` | يضيف `internal_notes TEXT` لـ `orders` |
| `m002_add_customers_phone2` | يضيف `phone2 TEXT` لـ `customers` |
| `m003_add_orders_priority` | يضيف `priority TEXT DEFAULT "normal"` لـ `orders` |
| `m004_add_idx_orders_priority` | يضيف index على `priority` |
| `m005_add_customer_contacts_role` | يضيف `role TEXT` لـ `customer_contacts` |

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

> ⚠️ [Q-02] كل migration يجب أن يكون **idempotent** — لو نجح لكن فشل `_mark_applied`، سيُعاد تطبيقه.

---

## customers_repo.py

#### جلب العملاء

```python
fetch_all_customers(conn, active_only=False) -> list
# مع orders_count من LEFT JOIN | ORDER BY name

fetch_customer(conn, customer_id) -> row
# كل الأعمدة بما فيها address و notes

search_customers(conn, query, limit=20) -> list
# يبحث في: name, code, phone, phone2 | is_active=1 فقط

fetch_customer_stats(conn, customer_id) -> dict
# {total_orders, delivered, cancelled, active,
#  total_value, total_paid, last_order_date}
```

#### كتابة العملاء

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

toggle_customer_active(conn, customer_id)
```

#### جهات الاتصال

```python
fetch_contacts(conn, customer_id) -> list
insert_contact(conn, customer_id, name, role="", phone="",
               email="", notes="") -> int
update_contact(conn, contact_id, name, role="", phone="",
               email="", notes="")
delete_contact(conn, contact_id)
```

---

## orders_repo.py

#### قراءة

```python
fetch_all_orders(conn, status=None, customer_id=None,
                 order_type=None, date_from=None, date_to=None,
                 search=None) -> list
# search: يبحث في order_number, customer name, customer code

fetch_order(conn, order_id) -> row
# كل الأعمدة + customer data + ref_order_number

fetch_customer_orders(conn, customer_id) -> list
```

#### كتابة الطلبات

```python
insert_order(conn, customer_id, order_type="new", status="pending",
             priority="normal", order_date=None, due_date=None,
             total_amount=0, discount=0, paid_amount=0,
             notes="", internal_notes="", reference_order=None,
             created_by="system") -> int
# [تحسين 22] يتحقق من وجود العميل و is_active=1
# [إصلاح 16] _next_order_number بـ GLOB 'ORD-YYYY-[0-9]*' بدل LIKE

update_order(conn, order_id, priority="normal", due_date=None,
             total_amount=0, discount=0, paid_amount=0,
             notes="", internal_notes="",
             customer_id=None, changed_by="system") -> bool
# [C-04] customer_id اختياري:
#   None → لا تغيير | قيمة → تحقق من الوجود و is_active + تحديث

change_order_status(conn, order_id, new_status, notes="",
                    changed_by="system") -> bool
# لو new_status="delivered" → delivery_date = today

cancel_order(conn, order_id, reason="", changed_by="system") -> bool
# اختصار لـ change_order_status(..., "cancelled")

reorder(conn, original_order_id, notes="", created_by="system") -> int | None
# ينسخ بنود الطلب الأصلي — order_type="reorder"

delete_order(conn, order_id) -> bool
# يرفض لو status ليس "pending" أو "cancelled"
# [تحسين 21] يرفض لو paid_amount > 0
```

#### بنود الطلب

```python
fetch_order_items(conn, order_id) -> list

insert_order_item(conn, order_id, item_name, description="",
                  quantity=1, unit="قطعة", unit_price=0,
                  discount_pct=0, design_ref="", notes="",
                  sort_order=None) -> int
# total_price = quantity × unit_price × (1 - discount_pct/100)
# يستدعي _recalc_order_total() بعد الإضافة

update_order_item(conn, item_id, item_name, ...)
# يستدعي _recalc_order_total() بعد التعديل

delete_order_item(conn, item_id)
# يستدعي _recalc_order_total() بعد الحذف
```

#### سجل الحالة والملخص

```python
fetch_status_log(conn, order_id) -> list   # ORDER BY changed_at ASC

fetch_orders_summary(conn) -> dict
# {total, pending, confirmed, in_progress, ready, delivered,
#  cancelled, on_hold, urgent, total_value, total_paid}
```

**حالات الطلب:**
```
pending → confirmed → in_progress → ready → delivered
        ↘ on_hold ↗              ↘ on_hold ↗
                    ↘ cancelled ↗
cancelled → pending (فقط)
```

> ⚠️ الانتقالات مُعرَّفة في `services/orders/order_service.py` — الـ repo لا يُطبّقها.

---

## ملاحظات

- `delete_customer` يرفض الحذف لو العميل له طلبات.
- `insert_order` يتحقق من `is_active=1` للعميل [تحسين 22].
- `update_order` يدعم تغيير العميل عبر `customer_id` اختياري [C-04].
- `delete_order` يرفض لو `paid_amount > 0` [تحسين 21].