# دليل الكود — Models & Services

> مرجع سريع لملفات `models/` و `services/`.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Models — الحسابات](#models--الحسابات) | `costing_base`, `costing_ops`, `costing` |
| [Services](#services) | `item_service`, `category_service`, `product_service`, `order_service`, `journal_service` |

---

## Models — الحسابات

### `models/costing_base.py`

```python
calc_worker_hourly_rate(conn) -> float
# = (monthly_salary ÷ net_hours) × overhead_factor
# net_hours = (working_days - holiday_days) × working_hours_day

raw_unit_price(item_row) -> float
# لو total_qty > 0: price ÷ total_qty | وإلا: price

effective_qty(qty, waste_pct) -> float
# = qty × (1 + waste_pct/100)
```

---

### `models/costing_ops.py`

```python
calc_labor_op_cost(conn, op_id) -> float
# = (minutes ÷ 60) × calc_worker_hourly_rate

calc_machine_op_cost(conn, op_id, row_id=None) -> float
# row_id محدد: تكلفة صف واحد فقط
# row_id=None: مجموع كل الصفوف
# Fallback لو مفيش صفوف:
#   mode="time" → (value/60) × rate_per_hour
#   mode="unit" → value × rate_per_unit
```

---

### `models/costing.py`

```python
calc_cost(conn, item_id, _visited=None, central_conn=None) -> float
# التكلفة الكاملة للمنتج (default scenario)
# يدعم item_id كـ int (محلي) أو "shared:{n}" (مشترك)
# central_conn اختياري — يُحسّن الأداء عند استدعاءات متعددة

calc_product_cost(conn, product_id, scenario_id=None, central_conn=None) -> tuple[float, dict]
# (total_cost, breakdown)
# breakdown: {raw, labor, machine, semi, total}
# scenario_id=None → يستخدم الـ default scenario

calc_cost_breakdown(conn, item_id, central_conn=None) -> dict
# {materials, labor, machine, total}
# للتوافق مع الكود القديم
```

**أنواع العناصر المدعومة في BOM:**

| النوع | الحساب |
|-------|--------|
| `raw` | `raw_unit_price` أو `variant_price` |
| `semi` | `calc_cost` متكرر (مع حماية من الحلقات) |
| `labor_op` | `calc_labor_op_cost` |
| `machine_op` | `calc_machine_op_cost` |

---

## Services

### `services/shared/item_service.py`

```python
ItemService(conn)

svc.validate(name, price) -> list[ItemValidationError]
svc.get(item_id) -> ItemResult | None
svc.list_by_type(item_type) -> list[ItemResult]

svc.add(name, price, item_type, category_id=None, total_qty=None) -> int
svc.update(item_id, name, price, category_id=None, total_qty=None)

svc.get_delete_preview(item_id) -> DeletePreview | None
# DeletePreview.usage_count — عدد المنتجات التي تستخدمه في BOM
# DeletePreview.can_delete() -> bool

svc.delete(item_id) -> bool  # يرفض لو مستخدم في BOM
svc.force_delete(item_id)    # يحذف حتى لو مستخدم
```

**`ItemResult`:** `id, name, price, item_type, category_id, total_qty`

---

### `services/shared/category_service.py`

```python
CategoryService(conn)

svc.get_tree(scope=None) -> list[CategoryNode]
svc.add(name, scope, color, parent_id=None) -> int
svc.update(cat_id, name, scope, color, parent_id=None)

svc.get_delete_preview(cat_id) -> DeletePreview | None
# DeletePreview.child_count, .item_count, .warning_text()

svc.delete_cascade(cat_id) -> int  # يرجع عدد التصنيفات المحذوفة
```

**`CategoryNode`:** `id, name, color, scope, parent_id, children`

---

### `services/costing/product_service.py`

```python
ProductService(conn)

svc.save(product_data: dict, components: list[BomComponent],
         scenario_id=None, scenario_name="سيناريو 1") -> ProductSaveResult
# product_data: {id?, name, type["semi"|"final"], price, category_id?}
# ProductSaveResult: product_id, scenario_id, is_new, bom_count

svc.calculate_cost(product_id, scenario_id=None) -> CostResult
# CostResult: product_id, product_name, total_cost, breakdown

svc.get_orphan_components(product_id) -> list[OrphanComponent]
svc.fix_orphans(product_id) -> int
svc.clone(product_id, new_name) -> int
svc.delete(product_id)
```

**`BomComponent`:** `child_type, child_id, qty, waste_pct=0, variant_id=None, machine_op_row_id=None`

---

### `services/orders/order_service.py`

```python
OrderService(conn, erp_conn=None)

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
- `.resolved_name() -> str`

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
# EntryResult: entry_id, is_new, total_dr, total_cr, lines_count

svc.update_entry(entry_id, entry_data, lines) -> EntryResult
svc.reverse_entry(entry_id, note="") -> EntryResult
svc.get_delete_preview(entry_id) -> DeletePreview | None
svc.delete(entry_id) -> bool
```

**`JournalLine`:** `account_id, dr=0.0, cr=0.0, note=""`
- `.is_valid() -> bool`
- `.amount() -> float`
- `.side() -> "dr" | "cr"`

---

## مثال: إنشاء قيد محاسبي

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

---

## ملاحظات مهمة

**1. الـ bus events:** استخدم `bus.company_data_changed.emit(cid)` بدل `bus.data_changed.emit()` — أكثر دقة وأفضل أداءً.

**2. `_C` dictionary:** لا تُعدّل مباشرة — استخدم `apply_theme(colors)` فقط.

**3. `tr()` function:** تقبل مفاتيح الترجمة أو نصوص عربية مباشرة — تحول `"حفظ"` تلقائياً لـ `"save"`.