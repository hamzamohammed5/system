# دليل الكود — Services الطلبات والمحاسبة + أمثلة

> `services/orders/` و `services/accounting/` — الطلبات، القيود المحاسبية، وأمثلة عملية.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [order_service](#order_service) | `services/orders/order_service.py` |
| [journal_service](#journal_service) | `services/accounting/journal_service.py` |
| [أمثلة](#أمثلة) | — |
| [ملاحظات مهمة](#ملاحظات-مهمة) | — |

---

## order_service

### `services/orders/order_service.py`

```python
OrderService(conn, erp_conn=None)
# erp_conn اختياري — [E-06] لربط المنتجات وإثراء OrderItem تلقائياً:
#   - يتحقق من وجود product_id في items table
#   - يملأ item_name تلقائياً لو كان فارغاً
#   - يُسجّل warning لو unit_price = 0 وسعر المنتج موجود في DB

svc.create(customer_id, items: list[OrderItem], notes="") -> int
# [E-06] يُثري البنود بـ _validate_and_enrich_items() قبل الحفظ (لو erp_conn متاح)
# يتحقق من وجود العميل و is_active=1
# يحفظ product_id في order_items عبر insert_order_item(..., product_id=item.product_id)
# يحسب total = sum(i.total() for i in items)

svc.update(order_id, customer_id, items, notes="")
# يرفض لو status ليس "pending"
# [E-06] يُثري البنود بـ _validate_and_enrich_items() قبل الحفظ
# يحذف بنود الطلب القديمة بـ _delete_order_items() ثم يُضيف الجديدة
# يحفظ product_id في order_items عبر insert_order_item(..., product_id=item.product_id)

svc.change_status(order_id, new_status, note="") -> OrderStatusChange
svc.get_allowed_transitions(order_id) -> list[str]

svc.get_delete_preview(order_id) -> DeletePreview | None
svc.delete(order_id) -> bool

svc.get_summary(customer_id=None) -> OrderSummary
# يستعلم SQL مباشر:
#   COUNT(*) AS total
#   COALESCE(SUM(net_amount), 0) AS amount   ← يقرأ net_amount من الجدول
#   CASE WHEN status=... THEN 1 لكل حالة
# OrderSummary.total_amount = net_amount المجموع (وليس total_amount)
# WHERE customer_id=? لو customer_id محدد

svc.add_customer(name, phone="", notes="") -> int
svc.update_customer(customer_id, name, phone="", notes="")
# يقبل: name, phone, notes فقط — ليس customer_type أو phone2 أو email إلخ
# يستدعي update_customer من customers_repo
svc.get_customer_summary(customer_id) -> OrderSummary
```

**`OrderItem`:** `product_id, qty, unit_price, notes="", item_name=""`
- `.total() -> float` — `qty × unit_price`
- `.resolved_name() -> str` — يرجع `item_name.strip()` أو `"منتج #{product_id}"` كـ fallback

**`_validate_and_enrich_items(items)` — [E-06]:**
```python
# يُطبّق _enrich_item() على كل بند ويرجع القائمة المُثراة
# [إصلاح 8 محفوظ] اسم الدالة في الكود: _validate_and_enrich_items (وليس _enrich_items)
```

**`_enrich_item(item)` — [E-06]:**
```python
# لو erp_conn=None → يُعيد item كما هو
# يستدعي resolve_product_info(erp_conn, product_id)
# لو product غير موجود → warning log، يُعيد item كما هو
# لو item_name فارغ → ينشئ OrderItem جديد مع الاسم من DB
# لو unit_price=0 و price>0 → warning log (لا يُعدّل السعر تلقائياً)
```

**`_assert_customer_exists(customer_id)` — داخلي:**
```python
# SELECT id, is_active FROM customers WHERE id=?
# يرمي ValueError لو غير موجود أو is_active=0
```

**`_delete_order_items(order_id)` — داخلي:**
```python
# DELETE FROM order_items WHERE order_id=?
# يستدعي conn.commit()
```

**دالة مساعدة مستقلة:**

```python
resolve_product_info(erp_conn, product_id) -> dict | None
# {"name": str, "price": float} أو None لو غير موجود أو erp_conn=None
# SELECT name, price FROM items WHERE id=?
# [E-06] لجلب اسم وسعر المنتج من erp.db
# erp_conn=None أو product_id=None → يرجع None بأمان (لا exception)
```

**الانتقالات المسموح بها (`_ALLOWED_TRANSITIONS`):**

| من | إلى |
|----|-----|
| `pending` | confirmed, in_progress, cancelled, on_hold |
| `confirmed` | in_progress, cancelled, on_hold |
| `in_progress` | ready, cancelled, on_hold |
| `ready` | delivered, cancelled |
| `delivered` | — |
| `cancelled` | pending |
| `on_hold` | pending, confirmed, in_progress |

**الحالات التي تمنع الحذف (`_NO_DELETE_STATUSES`):**
`in_progress`, `ready`, `delivered`

---

## journal_service

### `services/accounting/journal_service.py`

```python
JournalService(conn)

svc.check_balance(lines: list[JournalLine]) -> BalanceCheck
# BalanceCheck.is_balanced, .diff, .error_text()

svc.validate_lines(lines) -> list[str]
# يتحقق من: وجود صفوف، account_id غير فارغ،
# مبالغ غير سالبة، dr أو cr (ليس الاثنين ولا الاثنين صفر)، التوازن الكلي

svc.get_account_balance(account_id, date_from=None, date_to=None) -> AccountBalance
# SQL مباشر: JOIN journal_lines + journal_entries + accounts
# WHERE jl.account_id = ? [AND je.date >= ?] [AND je.date <= ?]
# AccountBalance: account_id, account_name, total_dr, total_cr
# AccountBalance.balance -> float | .side -> "dr" | "cr"
# لو لا توجد حركات → يجلب اسم الحساب من accounts ويرجع أرصدة صفر

svc.post_entry(entry_data: dict, lines: list[JournalLine]) -> EntryResult
# entry_data: {date, description, ref?, entry_type?, notes?}
# [إصلاح 35] يستخدم insert_entry + add_entry_lines (الأسماء الفعلية)
# date=None → datetime.now().strftime("%Y-%m-%d")
# status="posted" دائماً
# يُحوَّل JournalLine → dict {account_id, debit, credit, description}
# EntryResult: entry_id, is_new=True, total_dr, total_cr, lines_count

svc.update_entry(entry_id, entry_data, lines) -> EntryResult
# يرفض لو status="reversed"
# [إصلاح 35] يُحدّث journal_entries بـ SQL مباشر (update_journal_entry غير موجودة في repo):
#   UPDATE journal_entries SET date=?, description=? WHERE id=?
# يستدعي _delete_entry_lines(entry_id) ثم add_entry_lines للجديدة
# EntryResult: entry_id, is_new=False, ...

svc.reverse_entry(entry_id, note="") -> EntryResult
# يجلب الصفوف بـ fetch_entry_lines (الاسم الفعلي)
# ينشئ قيد عكسي — debit/credit مُعكوسان
# يستدعي post_entry داخلياً
# يرجع EntryResult للقيد الجديد

svc.get_delete_preview(entry_id) -> DeletePreview | None
# يرفض (can_delete=False) لو status="reversed"

svc.delete(entry_id) -> bool
# [إصلاح 35] يستخدم delete_entry (الاسم الفعلي)
# يرجع False لو مقفول/معكوس
```

**`JournalLine`:** `account_id, dr=0.0, cr=0.0, note=""`
- `.is_valid() -> bool` — `(dr > 0) != (cr > 0)` — dr أو cr لكن ليس الاثنين
- `.amount() -> float` — يرجع dr لو dr > 0 وإلا cr
- `.side() -> "dr" | "cr"`

**`BalanceCheck`:** `total_dr, total_cr`
- `.is_balanced -> bool` — `abs(total_dr - total_cr) < 0.001`
- `.diff -> float`
- `.error_text() -> str | None`

**`EntryResult`:** `entry_id, is_new, total_dr, total_cr, lines_count`

**`DeletePreview` (للقيود):**
```python
# entry_id, entry_ref, is_posted, can_delete, reason
# .warning_text() -> str
```

**`AccountBalance`:** `account_id, account_name, total_dr, total_cr`
- `.balance -> float` — `total_dr - total_cr`
- `.side -> "dr" | "cr"`

**`_delete_entry_lines(entry_id)` — داخلي [إصلاح 35]:**
```python
# DELETE FROM journal_lines WHERE entry_id=?  + commit
# بديل عن delete_journal_lines الغير موجودة في repo
```

---

## أمثلة

### إنشاء قيد محاسبي

```python
from services.accounting.journal_service import JournalService, JournalLine

svc = JournalService(acc_conn)
result = svc.post_entry(
    {"date": "2025-01-01", "description": "قيد يدوي"},
    [
        JournalLine(account_id=10, dr=1000),
        JournalLine(account_id=20, cr=1000),
    ]
)
# result.entry_id, result.total_dr, result.total_cr
```

### إنشاء طلب مع ربط المنتجات

```python
from services.orders.order_service import OrderService, OrderItem
from db.companies.company_state import company_state

# مع ربط erp.db — يملأ item_name تلقائياً لو كان فارغاً
# ويحفظ product_id في order_items
svc = OrderService(orders_conn, erp_conn=company_state.get_erp_conn())
order_id = svc.create(
    customer_id=1,
    items=[
        OrderItem(product_id=5, qty=2, unit_price=150.0),
        OrderItem(product_id=8, qty=1, unit_price=300.0, item_name="منتج مخصص"),
    ],
    notes="طلب عاجل"
)

# بدون erp_conn — يعمل بنفس السلوك القديم
svc2 = OrderService(orders_conn)
order_id2 = svc2.create(customer_id=1, items=[...])
```

### تغيير حالة طلب

```python
from services.orders.order_service import OrderService

svc = OrderService(orders_conn)

# معرفة الانتقالات المسموحة
allowed = svc.get_allowed_transitions(order_id=1)
# مثلاً: ["confirmed", "in_progress", "cancelled", "on_hold"]

# تغيير الحالة
change = svc.change_status(order_id=1, new_status="confirmed", note="تم التأكيد")
# change.old_status, change.new_status, change.timestamp
```

### استبدال شامل في BOM

```python
from services.costing.bulk_replace_service import BulkReplaceService

svc = BulkReplaceService(conn)
affected = svc.fetch_affected_products("raw", child_id=5)
product_rows = [(p["id"], p["qty"]) for p in affected]

updated, errors = svc.apply(
    child_type="raw",
    old_child_id=5,
    new_child_id=7,
    product_rows=product_rows,
)
# updated: عدد المنتجات المحدَّثة | errors: رسائل الفشل
```

### حساب تكلفة عملية عمالة

```python
from services.costing.labor_op_service import LaborOpService

svc = LaborOpService(conn)
cost = svc.calc_cost(op_id=3)
op   = svc.get(op_id=3)
# op.minutes, op.category_name
```

### بناء catalog للـ ComponentRow

```python
from services.costing.catalog_service import CatalogService

svc = CatalogService(conn)
catalog = svc.build()
# catalog["raw"]        → خامات
# catalog["labor_op"]   → عمليات عمالة
# catalog["machine_op"] → عمليات تشغيل
```

### إدارة سيناريوهات BOM

```python
from services.costing.scenario_service import ScenarioService

svc = ScenarioService(conn)
default_id = svc.ensure_default(item_id=5)
cost = svc.calc_cost(default_id)
scenarios = svc.list(item_id=5)
clone_id = svc.clone(default_id, "سيناريو 2")
```

### جلب BOM tree مع دعم migration

```python
from services.costing.bom_tree_service import BomTreeService

svc = BomTreeService(conn)
scenarios = svc.get_scenarios(item_id=5)
bom = svc.get_bom_for_scenario(scenarios[0].id)
sub = svc.get_sub_bom(item_id=3)  # BOM النصف مصنع
```

---

## ملاحظات مهمة

**1. bus events:** استخدم دائماً `emit_company_data_changed()` من `ui.widgets.core.events` — `data_changed` محذوف، كل الإشعارات عبر `company_data_changed`.

**2. `_C` dictionary:** لا تُعدّل مباشرة — استخدم `apply_theme(colors)` فقط.

**3. `tr()` function:** تقبل مفاتيح الترجمة فقط — لا تمرر نصاً عربياً مباشرة.

**4. `BulkReplaceService.fetch_candidates`:** يعتمد على `bulk_replace_helpers` في الـ UI layer — انتبه لهذا الـ coupling عند نقل الـ service لبيئة بدون UI.

**5. `BomTreeService` و cache الأعمدة:** استدعِ `invalidate_columns_cache()` بعد أي migration يضيف أعمدة لجدول bom، أو أنشئ instance جديد من الـ service.

**6. `CatalogService` والعناصر المشتركة:** تعتمد على `company_state.is_ready` — تأكد من وجود شركة نشطة قبل استدعاء `build()`.

**7. `ScenarioService.calc_cost`:** يحسب التكلفة مباشرة من BOM بدون المرور بـ `calc_product_cost` — مناسب للمقارنة بين سيناريوهات متعددة. يمرر `machine_op_row_id` لـ `calc_machine_op_cost`.

**8. `settings` values:** كل قيم الإعدادات مُخزَّنة كـ TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.

**9. `OrderService` مع `erp_conn`:** [E-06] `erp_conn` اختياري تماماً — بدونه يعمل الـ service بالسلوك القديم. مع `erp_conn` يُثري البنود تلقائياً عبر `_validate_and_enrich_items()` → `_enrich_item()` لكن لا يرفض لو المنتج غير موجود (يُسجّل warning فقط). **لا يُعدّل unit_price تلقائياً** حتى لو كان صفراً.

**10. `order_items.product_id`:** [E-06] عمود `product_id` يُحفظ الآن في `order_items` عبر `insert_order_item(..., product_id=item.product_id)` — تأكد من تطبيق migration على قواعد البيانات القديمة لو لم يكن العمود موجوداً.

**11. `OrderSummary.total_amount`:** يُحسب من `SUM(net_amount)` في جدول `orders` (وليس `total_amount`) — يعكس المبلغ الصافي بعد الخصم.

**12. `OrderService.update_customer`:** تقبل `name, phone, notes` فقط — لا تدعم `customer_type, phone2, email, address, city`. للتحديث الكامل استخدم `update_customer` من `customers_repo` مباشرة.

**13. `JournalService.update_entry`:** يُحدّث `journal_entries` بـ SQL مباشر (لا توجد `update_journal_entry` في repo) ثم يحذف الصفوف القديمة ويُضيف الجديدة.

**14. `JournalService._delete_entry_lines`:** دالة مساعدة داخلية [إصلاح 35] — بديل عن `delete_journal_lines` الغير موجودة في repo. تستخدم DELETE المباشر على `journal_lines`.

**15. `BulkReplaceService.apply` والـ BOM:** يقرأ `(child_type, child_id, qty, waste_pct)` — 4 عناصر من `fetch_bom`. لدعم السيناريوهات يجب استخدام `replace_bom_for_scenario` مباشرة.