# دليل الكود — DB: الطلبات (db/orders/) — نسخة محدَّثة

> جداول `orders.db` — العملاء، الطلبات، بنود الطلبات، سجل الحالة.
> كذلك `catalog_repo.py` الذي يقرأ من `erp.db` (المنتجات المسعّرة والعروض للكتالوج).
> **الملفات الفعلية:** `orders_schema.py`, `customers_repo.py`, `orders_repo.py`, `catalog_repo.py`
> **آخر تحديث:** يعكس الكود الفعلي في السياق.

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [orders_schema.py](#orders_schemapy) | إنشاء جداول orders.db + Migration Framework |
| [customers_repo.py](#customers_repopy) | CRUD العملاء وجهات الاتصال |
| [orders_repo.py](#orders_repopy) | CRUD الطلبات وبنودها |
| [catalog_repo.py](#catalog_repopy) | قراءة كتالوج المنتجات المسعّرة والعروض من erp.db |

---

## orders_schema.py

```python
get_orders_connection() -> sqlite3.Connection
# isolation_level=None (autocommit), FK=ON, WAL mode

create_orders_tables(conn)
# ينشئ الجداول + indexes + يُشغّل _run_migrations()
```

**هيكل الجداول الكامل:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `customers` | `id, code UNIQUE, name, customer_type DEFAULT 'individual' CHECK('individual'\|'company'), phone, phone2, email, address, city, notes, is_active DEFAULT 1, created_at, updated_at` |
| `customer_contacts` | `id, customer_id→CASCADE, name, role, phone, email, notes` |
| `orders` | `id, order_number UNIQUE, customer_id→RESTRICT, order_type DEFAULT 'new' CHECK('new'\|'reorder'\|'custom'), status DEFAULT 'pending' CHECK(7 حالات), priority DEFAULT 'normal' CHECK(4 أولويات), order_date, due_date, delivery_date, total_amount, discount, net_amount, paid_amount, notes, internal_notes, reference_order→SET NULL, created_by DEFAULT 'system', created_at, updated_at` |
| `order_items` | `id, order_id→CASCADE, item_name, description, quantity DEFAULT 1 CHECK(>0), unit DEFAULT 'قطعة', unit_price, discount_pct, total_price, design_ref, notes, sort_order` |
| `order_status_log` | `id, order_id→CASCADE, old_status, new_status TEXT NULL (يقبل NULL للملاحظات الإدارية [C-04]), notes, changed_by DEFAULT 'system', changed_at` |
| `schema_migrations` | `id, name UNIQUE, applied_at` |

**حالات الطلب المسموحة في CHECK:**
`'pending' | 'confirmed' | 'in_progress' | 'ready' | 'delivered' | 'cancelled' | 'on_hold'`

**أولويات الطلب:**
`'low' | 'normal' | 'high' | 'urgent'`

**الـ Indexes:**
```sql
idx_orders_customer    ON orders(customer_id)
idx_orders_status      ON orders(status)
idx_orders_date        ON orders(order_date)
idx_order_items_order  ON order_items(order_id)
idx_status_log_order   ON order_status_log(order_id)
idx_customers_code     ON customers(code)
idx_orders_priority    ON orders(priority)  -- من migration m004
```

---

## Migration Framework [تحسين 25]

### دوال الإطار

```python
_ensure_migrations_table(conn)
# CREATE TABLE IF NOT EXISTS schema_migrations (id, name UNIQUE, applied_at)

_is_applied(conn, name: str) -> bool
# SELECT 1 FROM schema_migrations WHERE name=?
# [Q-02] لو فشل INSERT لكن نجح fn() → يُعاد تطبيقه في التشغيل التالي (مقبول)

_mark_applied(conn, name: str)
# INSERT OR IGNORE INTO schema_migrations (name) VALUES (?)

_apply_migration(conn, name: str, fn)
# لو مطبَّق مسبقاً → يتخطاه صامتاً
# لو فشل → logger.warning ويكمل (لا يوقف التطبيق)

_run_migrations(conn)
# يُنشئ جدول schema_migrations أولاً
# لو فشل الإنشاء → logger.warning + يرجع (لا migrations)
# يُطبّق كل migration في _MIGRATIONS بالترتيب
```

### الـ Migrations المُعرَّفة

| الاسم | الوصف | idempotent كيف؟ |
|-------|-------|----------------|
| `m001_add_internal_notes` | يضيف `internal_notes TEXT` لـ `orders` | `_column_exists()` |
| `m002_add_customers_phone2` | يضيف `phone2 TEXT` لـ `customers` | `_column_exists()` |
| `m003_add_orders_priority` | يضيف `priority TEXT DEFAULT 'normal'` لـ `orders` | `_column_exists()` |
| `m004_add_idx_orders_priority` | يضيف index على `priority` | `CREATE INDEX IF NOT EXISTS` |
| `m005_add_customer_contacts_role` | يضيف `role TEXT` لـ `customer_contacts` | `_column_exists()` |

**[Q-02] قاعدة idempotent — كل migration يجب أن يكون آمناً للتطبيق مرتين:**
```python
def _m006_my_migration(conn):
    if _table_exists(conn, "orders") and not _column_exists(conn, "orders", "my_col"):
        conn.execute("ALTER TABLE orders ADD COLUMN my_col TEXT")
        conn.commit()
```

**إضافة migration جديد:**
```python
# 1. عرّف الدالة بعد _m005_...
def _m006_description(conn):
    if not _column_exists(conn, "table_name", "col_name"):
        conn.execute("ALTER TABLE table_name ADD COLUMN col_name TEXT")
        conn.commit()

# 2. أضفها لـ _MIGRATIONS بالترتيب الصحيح
_MIGRATIONS = [
    ...,
    ("m006_description", _m006_description),
]
```

**[Q-02] سلوك الـ framework عند الفشل:**
- إذا فشل `_ensure_migrations_table` → لا migrations تُطبَّق (مع warning)
- إذا فشل migration معين → يُسجَّل warning ويُتخطى (الباقي يكمل)
- إذا نجح migration لكن فشل `_mark_applied` → يُعاد تطبيقه في التشغيل التالي (مقبول لأن كل migration idempotent)

---

## customers_repo.py

### توليد الكود التلقائي

```python
_next_customer_code(conn) -> str
# [إصلاح 15] GLOB 'CUS-[0-9]*' بدل LIKE 'CUS-%'
# يمنع تكرار CUS-0001 عند وجود كودات بصيغة غير رقمية كـ "CUS-abc"
# CAST على لاحقة رقمية مضمونة → لا يُعيد 0 بصمت
# MAX + 1 → نتيجة: "CUS-0001", "CUS-0002", ...
```

### قراءة العملاء

```python
fetch_all_customers(conn, active_only: bool = False) -> list
# مع orders_count من LEFT JOIN orders | ORDER BY name
# الأعمدة: id, code, name, customer_type, phone, phone2, email,
#           city, is_active, created_at, updated_at, orders_count

fetch_customer(conn, customer_id: int) -> row
# كل الأعمدة بما فيها address و notes

search_customers(conn, query: str, limit: int = 20) -> list
# يبحث في: name, code, phone, phone2 بـ LIKE
# is_active=1 فقط
# الأعمدة: id, code, name, customer_type, phone, city, is_active

fetch_customer_stats(conn, customer_id: int) -> dict
# {total_orders, delivered, cancelled, active,
#  total_value, total_paid, last_order_date}
```

### كتابة العملاء

```python
insert_customer(conn, name: str,
                customer_type: str = 'individual',
                phone: str = '', phone2: str = '',
                email: str = '', address: str = '',
                city: str = '', notes: str = '') -> int
# يولد code تلقائياً بـ _next_customer_code() [إصلاح 15]

update_customer(conn, customer_id: int, name: str,
                customer_type: str = 'individual',
                phone: str = '', phone2: str = '',
                email: str = '', address: str = '',
                city: str = '', notes: str = '',
                is_active: int = 1)
# updated_at=datetime('now') تلقائياً

delete_customer(conn, customer_id: int) -> bool
# يرفض لو في طلبات مرتبطة → يرجع False
# يرجع True لو نجح الحذف

toggle_customer_active(conn, customer_id: int)
# UPDATE SET is_active = 1 - is_active
```

### جهات الاتصال

```python
fetch_contacts(conn, customer_id: int) -> list
# id, name, role, phone, email, notes | ORDER BY id

insert_contact(conn, customer_id: int, name: str,
               role: str = '', phone: str = '',
               email: str = '', notes: str = '') -> int

update_contact(conn, contact_id: int, name: str,
               role: str = '', phone: str = '',
               email: str = '', notes: str = '')

delete_contact(conn, contact_id: int)
```

---

## orders_repo.py

### توليد رقم الطلب

```python
_next_order_number(conn) -> str
# [إصلاح 16] GLOB 'ORD-YYYY-[0-9]*' بدل LIKE للتحقق من الصيغة الرقمية
# يأخذ السنة الحالية من datetime.date.today().year
# صيغة الناتج: "ORD-2025-0001" — يعيد من 0001 كل سنة جديدة
```

### قراءة الطلبات

```python
fetch_all_orders(conn,
                 status: str = None,
                 customer_id: int = None,
                 order_type: str = None,
                 date_from: str = None,
                 date_to: str = None,
                 search: str = None) -> list
# search: يبحث في order_number, customer name, customer code
# مع: customer_name, customer_code, customer_phone من JOIN customers
# مع: ref_order_number من LEFT JOIN orders (reference_order)
# ORDER BY o.created_at DESC

fetch_order(conn, order_id: int) -> row
# كل الأعمدة + customer data (name, code, phone, city) + ref_order_number

fetch_customer_orders(conn, customer_id: int) -> list
# id, order_number, order_type, status, priority,
# order_date, due_date, net_amount, paid_amount
# ORDER BY created_at DESC

fetch_order_basic(conn, order_id: int) -> row
# [مضاف] نسخة خفيفة من fetch_order — بدون JOIN على customers/orders
# مخصصة لاستخدامات service الداخلية التي تحتاج فقط
#   id, order_number, status, customer_id, paid_amount, net_amount
# (تحقق، حذف، انتقال حالة) دون تحميل بيانات العميل الكاملة
```

### كتابة الطلبات

```python
insert_order(conn, customer_id: int,
             order_type: str = 'new',
             status: str = 'pending',
             priority: str = 'normal',
             order_date: str = None,      # None → today
             due_date: str = None,
             total_amount: float = 0,
             discount: float = 0,
             paid_amount: float = 0,
             notes: str = '',
             internal_notes: str = '',
             reference_order: int = None,
             created_by: str = 'system') -> int
# [تحسين 22] يتحقق من: وجود العميل + is_active=1
# Raises: ValueError لو العميل غير موجود أو غير نشط
# net_amount = total_amount - discount (تلقائياً)
# يُسجَّل في order_status_log تلقائياً بعد الإنشاء

update_order(conn, order_id: int,
             priority: str = 'normal',
             due_date: str = None,
             total_amount: float = 0,
             discount: float = 0,
             paid_amount: float = 0,
             notes: str = '',
             internal_notes: str = '',
             customer_id: int = None,
             changed_by: str = 'system') -> bool
# [C-04] customer_id اختياري:
#   None (افتراضي) → لا يُغيِّر العميل الحالي — backward-compatible
#   قيمة صحيحة → تحقق من وجود العميل و is_active=1 ثم يُغيِّره
#   تغيير العميل يُسجَّل في order_status_log كملاحظة (new_status=NULL)
# Raises: ValueError لو العميل الجديد غير موجود أو غير نشط
# Returns: True لو نجح | False لو الطلب غير موجود

change_order_status(conn, order_id: int,
                    new_status: str,
                    notes: str = '',
                    changed_by: str = 'system') -> bool
# لو new_status='delivered' → delivery_date = today تلقائياً
# يُسجَّل في order_status_log

cancel_order(conn, order_id: int,
             reason: str = '',
             changed_by: str = 'system') -> bool
# اختصار لـ change_order_status(..., 'cancelled')

reorder(conn, original_order_id: int,
        notes: str = '',
        created_by: str = 'system') -> int | None
# ينسخ كل بنود الطلب الأصلي
# order_type='reorder' | reference_order=original_order_id
# يُعيد حساب total بـ _recalc_order_total()
# يرجع None لو الطلب الأصلي غير موجود

delete_order(conn, order_id: int) -> bool
# يرفض لو status ليس 'pending' أو 'cancelled'
# [تحسين 21] يرفض لو paid_amount > 0
# يرجع False لأي من هذه الحالات
```

### بنود الطلب

```python
fetch_order_items(conn, order_id: int) -> list
# id, order_id, item_name, description, quantity, unit,
# unit_price, discount_pct, total_price, design_ref, notes, sort_order
# ORDER BY sort_order, id

insert_order_item(conn, order_id: int,
                  item_name: str,
                  description: str = '',
                  quantity: float = 1,
                  unit: str = 'قطعة',
                  unit_price: float = 0,
                  discount_pct: float = 0,
                  design_ref: str = '',
                  notes: str = '',
                  sort_order: int = None) -> int
# total_price = quantity × unit_price × (1 - discount_pct/100)
# sort_order=None → COUNT(order_id) تلقائياً
# يستدعي _recalc_order_total() بعد الإضافة

update_order_item(conn, item_id: int, item_name: str,
                  description: str = '', quantity: float = 1,
                  unit: str = 'قطعة', unit_price: float = 0,
                  discount_pct: float = 0,
                  design_ref: str = '', notes: str = '')
# يعيد حساب total_price | يستدعي _recalc_order_total()

delete_order_items_by_order(conn, order_id: int) -> None
# [مضاف] يحذف كل بنود طلب معيّن دفعة واحدة (DELETE WHERE order_id=?)
# نُقلت من OrderService.update() الذي كان يُنفِّذ SQL خام مباشرة
# قبل إعادة إدراج البنود المُحدَّثة
# ملاحظة: لا تستدعي _recalc_order_total عمداً — الـ caller يُعيد
# إدراج البنود الجديدة بعدها مباشرة، و insert_order_item يُعيد
# الحساب تلقائياً بنفسه

delete_order_item(conn, item_id: int)
# يستدعي _recalc_order_total() بعد الحذف

_recalc_order_total(conn, order_id: int)
# داخلية — تُعيد حساب total_amount و net_amount من SUM(total_price)
# net_amount = total_amount - discount
```

### سجل الحالة والملخص

```python
_log_status(conn, order_id: int, old_status, new_status,
            notes: str = '', changed_by: str = 'system')
# new_status=None مسموح للملاحظات الإدارية [C-04] كتغيير العميل
# يستدعي conn.commit() بعد INSERT

fetch_status_log(conn, order_id: int) -> list
# id, old_status, new_status (قد يكون NULL [C-04]),
# notes, changed_by, changed_at
# ORDER BY changed_at ASC

fetch_orders_summary(conn) -> dict
# {total, pending, confirmed, in_progress, ready,
#  delivered, cancelled, on_hold, urgent,
#  total_value (SUM net_amount), total_paid (SUM paid_amount)}

fetch_orders_summary_for_customer(conn, customer_id: int) -> dict
# [مضاف] فلترة بعميل — نُقلت من OrderService.get_summary(customer_id=...)
# (كانت SQL خام) إلى الـ repo — يحافظ على مبدأ الطبقات
# {total, amount (SUM net_amount), pending, in_prog, done, cancelled}
# WHERE customer_id=?

fetch_orders_summary_all(conn) -> dict
# [مضاف] نفس أعمدة fetch_orders_summary_for_customer لكن بدون فلترة
# {total, amount, pending, in_prog, done, cancelled}
```

---

## انتقالات الحالة

الانتقالات مُعرَّفة في `services/orders/order_service.py` — الـ repo لا يُطبّقها.

```
pending  → confirmed | in_progress | cancelled | on_hold
confirmed → in_progress | cancelled | on_hold
in_progress → ready | cancelled | on_hold
ready → delivered | cancelled
delivered → (لا انتقالات)
cancelled → pending
on_hold → pending | confirmed | in_progress
```

**الحالات التي تمنع الحذف:**
`in_progress | ready | delivered`

---

## catalog_repo.py

**المسار الكامل:** `db/orders/catalog_repo.py`

**الغرض:** يقرأ كتالوج المنتجات المسعّرة (نهائي/نصف مصنع) والعروض من `erp.db` (وليس `orders.db`) — لعرضها عند بناء طلب جديد.

> **[مضاف حديثاً]** كان هذا الملف في الأصل `db_fetcher` منفصل داخل `ui/tabs/orders/order_form/_products_fetcher.py`، نُقل إلى `db/orders` لأنه ينفذ SQL خام (JOIN على `items/pricing/categories/offers`)، مما يخالف مبدأ الطبقات:
> `widgets -> tabs/UI -> services -> repos (db) -> schema`
> UI لا يجب أن يعرف SQL أو يفتح اتصال قاعدة بيانات بنفسه.

**جداول erp المستخدمة (قراءة فقط):** `items(id, name, type, category_id)`, `pricing(item_id, price)`, `categories(id, name, color)`, `offers(id, name, discount, category_id)`, `offer_items(offer_id, item_id, qty)`.

### المنتجات المسعّرة

```python
fetch_priced_products(conn) -> list[dict]
# يجلب المنتجات (type IN ('final','semi')) JOIN pricing (INNER JOIN — فقط المسعّرة)
# LEFT JOIN categories
# ORDER BY COALESCE(category_name, 'ω') ASC, name ASC  (بلا تصنيف في الآخر)
# كل عنصر: {id, name, type, category_id, category_name, category_color, price}

fetch_priced_product_by_id(conn, product_id: int) -> dict | None
# [مضاف] يجلب منتجاً واحداً بمعرفه: {id, name, price}
# LEFT JOIN pricing (وليس INNER) — price قد يكون None لو غير مُسعَّر
# [تعديل هيكلي] نُقلت من services/orders/order_service.py حيث كانت
# resolve_product_info تنفذ SQL خام مباشرة على erp_conn، متخطّية طبقة الـ repo
```

### العروض

```python
fetch_offers(conn) -> list[dict]
# id, name, discount, category_name (LEFT JOIN categories) | ORDER BY name

fetch_offer_lines(conn, offer_id: int) -> list[dict]
# item_id, qty, item_name, price (LEFT JOIN pricing)
# JOIN items | WHERE offer_id=?
```

---

## ملاحظات مهمة

- `delete_customer` يرفض الحذف لو العميل له طلبات — استخدم `toggle_customer_active` بدلاً منه.
- `insert_order` يتحقق من `is_active=1` للعميل [تحسين 22] — لا يُنشئ طلباً لعميل معطّل.
- `update_order` يدعم تغيير العميل عبر `customer_id` اختياري [C-04] — `None` = لا تغيير.
- `delete_order` يرفض لو `paid_amount > 0` [تحسين 21] — يمنع حذف طلبات لها مدفوعات.
- `order_status_log.new_status` يقبل NULL [C-04] للأحداث الإدارية كتغيير العميل.
- `_next_order_number` يُعيد الترقيم من 0001 كل سنة جديدة.
- كل الـ migrations يجب أن تكون idempotent [Q-02].
- `customer_contacts.role` أُضيف عبر migration m005 — قد يكون NULL في قواعد بيانات قديمة.
- `catalog_repo.py` مختلف عن باقي ملفات `db/orders/` — يقرأ من `erp.db` (كتالوج المنتجات) وليس `orders.db`، ولا يحتوي أي عمليات كتابة (قراءة فقط).