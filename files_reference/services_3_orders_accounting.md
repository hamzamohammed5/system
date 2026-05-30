# دليل الكود — Models & Services (4): Services الطلبات والمحاسبة + أمثلة

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
svc.update(order_id, customer_id, items, notes="")
svc.change_status(order_id, new_status, note="") -> OrderStatusChange
svc.get_allowed_transitions(order_id) -> list[str]

svc.get_delete_preview(order_id) -> DeletePreview | None
svc.delete(order_id) -> bool

svc.get_summary(customer_id=None) -> OrderSummary
# OrderSummary: total_orders, total_amount, pending_count, in_progress, done_count, cancelled

svc.add_customer(name, phone="", notes="") -> int
svc.update_customer(customer_id, name, phone="", notes="")
svc.get_customer_summary(customer_id) -> OrderSummary
```

**`OrderItem`:** `product_id, qty, unit_price, notes="", item_name=""`
- `.total() -> float`
- `.resolved_name() -> str` — يرجع `item_name` أو `"منتج #{product_id}"` كـ fallback

**دالة مساعدة:**

```python
resolve_product_info(erp_conn, product_id) -> dict | None
# {"name": str, "price": float} أو None لو غير موجود
# [E-06] لجلب اسم وسعر المنتج من erp.db
# erp_conn=None → يرجع None بأمان (لا exception)
```

**الانتقالات المسموح بها:**

| من | إلى |
|----|-----|
| `pending` | confirmed, in_progress, cancelled, on_hold |
| `confirmed` | in_progress, cancelled, on_hold |
| `in_progress` | ready, cancelled, on_hold |
| `ready` | delivered, cancelled |
| `delivered` | — |
| `cancelled` | pending |
| `on_hold` | pending, confirmed, in_progress |

---

## journal_service

### `services/accounting/journal_service.py`

```python
JournalService(conn)

svc.check_balance(lines: list[JournalLine]) -> BalanceCheck
# BalanceCheck.is_balanced, .diff, .error_text()

svc.validate_lines(lines) -> list[str]

svc.get_account_balance(account_id, date_from=None, date_to=None) -> AccountBalance
# AccountBalance: account_id, account_name, total_dr, total_cr
# AccountBalance.balance -> float | .side -> "dr" | "cr"

svc.post_entry(entry_data: dict, lines: list[JournalLine]) -> EntryResult
# entry_data: {date, description, ref?, entry_type?, notes?}
# [إصلاح 35] يستخدم insert_entry + add_entry_lines (الأسماء الفعلية)
# EntryResult: entry_id, is_new, total_dr, total_cr, lines_count

svc.update_entry(entry_id, entry_data, lines) -> EntryResult
# [إصلاح 35] يحذف الصفوف القديمة ويكتب الجديدة مباشرة
svc.reverse_entry(entry_id, note="") -> EntryResult
svc.get_delete_preview(entry_id) -> DeletePreview | None
svc.delete(entry_id) -> bool
# [إصلاح 35] يستخدم delete_entry (الاسم الفعلي)
```

**`JournalLine`:** `account_id, dr=0.0, cr=0.0, note=""`
- `.is_valid() -> bool`
- `.amount() -> float`
- `.side() -> "dr" | "cr"`

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

**1. bus events:** استخدم `emit_company_data_changed()` من `ui.widgets.core.events` بدل `bus.data_changed.emit()`.

**2. `_C` dictionary:** لا تُعدّل مباشرة — استخدم `apply_theme(colors)` فقط.

**3. `tr()` function:** تقبل مفاتيح الترجمة فقط — لا تمرر نصاً عربياً مباشرة.

**4. `BulkReplaceService.fetch_candidates`:** يعتمد على `bulk_replace_helpers` في الـ UI layer — انتبه لهذا الـ coupling عند نقل الـ service لبيئة بدون UI.

**5. `BomTreeService` و cache الأعمدة:** استدعِ `invalidate_columns_cache()` بعد أي migration يضيف أعمدة لجدول bom، أو أنشئ instance جديد من الـ service.

**6. `CatalogService` والعناصر المشتركة:** تعتمد على `company_state.is_ready` — تأكد من وجود شركة نشطة قبل استدعاء `build()`.

**7. `ScenarioService.calc_cost`:** يحسب التكلفة مباشرة من BOM بدون المرور بـ `calc_product_cost` — مناسب للمقارنة بين سيناريوهات متعددة.

**8. `settings` values:** كل قيم الإعدادات مُخزَّنة كـ TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.

**9. `OrderService` مع `erp_conn`:** [E-06] `erp_conn` اختياري تماماً — بدونه يعمل الـ service بالسلوك القديم. مع `erp_conn` يُثري البنود تلقائياً لكن لا يرفض لو المنتج غير موجود (يُسجّل warning فقط).