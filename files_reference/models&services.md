# دليل الكود — Models & Services

> مرجع سريع لملفات `models/` و `services/`.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Models — الحسابات](#models--الحسابات) | `costing_base`, `costing_ops`, `costing` |
| [Services — مشترك](#services--مشترك) | `item_service`, `category_service` |
| [Services — التكلفة](#services--التكلفة) | `product_service`, `scenario_service`, `labor_op_service`, `machine_service`, `machine_op_rows_service`, `variant_service`, `catalog_service`, `bulk_replace_service`, `bom_tree_service` |
| [Services — الطلبات](#services--الطلبات) | `order_service` |
| [Services — المحاسبة](#services--المحاسبة) | `journal_service` |

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

## Services — مشترك

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

svc.get_usage_count(item_id) -> int
# يشمل كل child_types: raw, semi, labor_op, machine_op

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

## Services — التكلفة

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
- `.to_tuple() -> tuple` — `(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)`

---

### `services/costing/scenario_service.py`

```python
ScenarioService(conn)

# ── قراءة ──
svc.list(item_id) -> list[ScenarioResult]
svc.get(scenario_id) -> ScenarioResult | None
svc.get_default(item_id) -> ScenarioResult | None
svc.get_bom(scenario_id) -> list[BomRowResult]

# ── كتابة ──
svc.create(item_id, name, is_default=False) -> int
svc.rename(scenario_id, name)
svc.set_default(scenario_id)
svc.clone(scenario_id, new_name) -> int
svc.delete(scenario_id) -> bool  # يرفض لو آخر سيناريو
svc.replace_bom(scenario_id, rows: list)
# rows: [(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id), ...]

# ── مساعدات ──
svc.ensure_default(item_id) -> int
# يتأكد من وجود default scenario — ينشئ "سيناريو 1" لو مفيش

svc.calc_cost(scenario_id) -> float
# يحسب التكلفة الكاملة للسيناريو
```

**`ScenarioResult`:** `id, item_id, name, is_default, notes`
- `.from_row(row) -> ScenarioResult`

**`BomRowResult`:** `child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id`
- `.from_row(row) -> BomRowResult`

---

### `services/costing/labor_op_service.py`

```python
LaborOpService(conn)

svc.list() -> list[LaborOpResult]
svc.get(op_id) -> LaborOpResult | None

svc.add(name, minutes, category_id=None) -> int
svc.update(op_id, name, minutes, category_id=None)
svc.delete(op_id)

svc.calc_cost(op_id) -> float
# يستدعي models.costing_ops.calc_labor_op_cost داخلياً
```

**`LaborOpResult`:** `id, name, minutes, category_id, category_name`
- `.from_row(row) -> LaborOpResult` — classmethod يقبل dict أو sqlite3.Row

---

### `services/costing/machine_service.py`

```python
MachineService(conn)

svc.list() -> list[MachineResult]
svc.get(machine_id) -> MachineResult | None

svc.add(name, rate_per_hour, rate_per_unit, category_id=None) -> int
svc.update(machine_id, name, rate_per_hour, rate_per_unit, category_id=None)
svc.delete(machine_id)
```

**`MachineResult`:** `id, name, rate_per_hour, rate_per_unit, category_id, category_name`
- `.from_row(row) -> MachineResult` — classmethod يقبل dict أو sqlite3.Row
- `.mode -> str` — property: `"time"` لو `rate_per_hour > 0`، وإلا `"unit"`

```python
MachineOpService(conn)

svc.list() -> list[MachineOpResult]
svc.get(op_id) -> MachineOpResult | None

svc.add(machine_id, name, mode, value, category_id=None) -> int
# mode: "time" | "unit"
svc.update(op_id, machine_id, name, mode, value, category_id=None)
svc.delete(op_id)

svc.calc_cost(op_id, row_id=None) -> float
# row_id محدد: تكلفة صف واحد | row_id=None: مجموع كل الصفوف
# يستدعي models.costing_ops.calc_machine_op_cost داخلياً
```

**`MachineOpResult`:** `id, name, machine_id, machine_name, mode, value, category_id, category_name`
- `.from_row(row) -> MachineOpResult` — classmethod يقبل dict أو sqlite3.Row

---

### `services/costing/machine_op_rows_service.py`

```python
MachineOpRowsService(conn)

# ── قراءة ──
svc.list(op_id) -> list[OpRowResult]
svc.get(row_id) -> OpRowResult | None

# ── كتابة ──
svc.add(op_id, label="", value=0.0, count=1.0, sort_order=0) -> int
svc.update(row_id, label, value, count, sort_order=0)
svc.delete(row_id, op_id) -> bool  # يرفض لو آخر صف في العملية
svc.replace(op_id, rows: list)
# rows: [(label, value, count), ...]

# ── حساب ──
svc.calc_row_cost(row_id) -> float
# mode="time": (value/60) × rate_per_hour
# mode="unit": value × rate_per_unit

svc.calc_total_cost(op_id) -> float
# مجموع تكلفة كل الصفوف
```

**`OpRowResult`:** `id, op_id, label, value, count, sort_order`
- `.from_row(row) -> OpRowResult`

---

### `services/costing/variant_service.py`

```python
VariantService(conn)

# ── قراءة ──
svc.list(item_id) -> list[VariantResult]
svc.get(variant_id) -> VariantResult | None

# ── كتابة ──
svc.add(item_id, name, pieces, notes=None) -> int
# Raises: ValueError لو name فارغ أو pieces <= 0

svc.update(variant_id, name, pieces, notes=None)
# Raises: ValueError لو name فارغ أو pieces <= 0

svc.delete(variant_id)

# ── حساب ──
svc.calc_unit_cost(variant_id, item_price) -> float
# = item_price ÷ pieces
```

**`VariantResult`:** `id, item_id, name, pieces, notes`
- `.from_row(row) -> VariantResult`
- `.calc_unit_cost(item_price) -> float` — سعر الوحدة = السعر ÷ عدد القطع

---

### `services/costing/catalog_service.py`

```python
CatalogService(conn, central_conn=None)
# central_conn اختياري — يُحسّن الأداء عند استدعاءات متعددة

svc.build() -> dict
# يبني الـ catalog الكامل لكل الأنواع:
# {
#   "raw":        [(id, name, category_name, price, total_qty), ...],
#   "semi":       [(id, name, category_name, price, None), ...],
#   "final":      [(id, name, category_name, price, None), ...],
#   "labor_op":   [(id, name, category_name, minutes), ...],
#   "machine_op": [(id, name, category_name, mode, machine_name), ...],
# }

svc.build_raw() -> list         # خامات محلية + مشتركة
svc.build_semi() -> list        # نصف مصنع محلي فقط
svc.build_final() -> list       # منتج نهائي محلي فقط
svc.build_labor_ops() -> list   # عمليات عمالة محلية + مشتركة
svc.build_machine_ops() -> list # عمليات تشغيل محلية + مشتركة
```

**ملاحظة:** العناصر المشتركة تأتي بـ `id = "shared:{n}"` وتصنيف `"🔗 مشترك"`.

---

### `services/costing/bulk_replace_service.py`

```python
BulkReplaceService(conn)

svc.apply(
    child_type:   str,
    old_child_id: int,
    new_child_id: int | None,
    product_rows: list[tuple[int, float]],  # [(product_id, qty), ...]
    uniform_qty:  float | None = None,
    do_replace:   bool = True,
    do_qty:       bool = True,
) -> tuple[int, list[str]]
# يرجع (عدد_المحدَّثين, قائمة_أخطاء)
# uniform_qty=None → يستخدم qty من product_rows لكل منتج
# do_replace=False → يبقي child_id كما هو (تعديل qty فقط)
# do_qty=False     → يبقي qty كما هو (استبدال العنصر فقط)

svc.get_element_name(child_type, child_id) -> str
# يرجع اسم العنصر من الجدول المناسب (items / labor_ops / machine_ops)

svc.fetch_candidates(child_type, exclude_id) -> list[tuple[int, str, str]]
# عناصر بديلة من نفس النوع بدون العنصر الحالي
# list of (id, name, category_name)

svc.fetch_affected_products(child_type, child_id) -> list[dict]
# المنتجات التي تستخدم العنصر في BOM
# كل dict: {id, name, type, qty, category_id, category_name, cost}
```

**ملاحظة:** `fetch_candidates` و`fetch_affected_products` يعتمدان داخلياً على `ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py`.

---

### `services/costing/bom_tree_service.py`

```python
BomTreeService(conn)

# ── قراءة ──
svc.get_scenarios(item_id) -> list[ScenarioInfo]
svc.get_bom_for_scenario(scenario_id) -> list[BomComponentRow]
# يتعامل تلقائياً مع schemas مختلفة (مع/بدون waste_pct, variant_id, machine_op_row_id)

svc.get_sub_bom(item_id) -> list[BomComponentRow]
# BOM الفرعي للنصف مصنع — يستخدم default scenario أو أول سيناريو

svc.get_default_scenario_id(item_id) -> int | None

# ── حذف ──
svc.delete_component(scenario_id, child_type, child_id)
svc.delete_bom_row(parent_id, child_type, child_id)

# ── مساعدات ──
svc.invalidate_columns_cache()
# يُصفَّر cache أعمدة BOM — يُستدعى بعد migration
```

**`ScenarioInfo`:** `id, item_id, name, is_default`
- `.from_row(row) -> ScenarioInfo`

**`BomComponentRow`:** `child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id`
- `.from_dict(d) -> BomComponentRow`

**ملاحظة:** يخزّن نتيجة `PRAGMA table_info(bom)` في cache داخلي لتجنب تكرار الاستعلام.

---

## Services — الطلبات

### `services/orders/order_service.py`

```python
OrderService(conn, erp_conn=None)
# erp_conn اختياري — لربط المنتجات وإثراء OrderItem تلقائياً

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

**دالة مساعدة:**
```python
resolve_product_info(erp_conn, product_id) -> dict | None
# {"name": str, "price": float} أو None لو غير موجود
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

## Services — المحاسبة

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

**1. الـ bus events:** استخدم `bus.company_data_changed.emit(cid)` بدل `bus.data_changed.emit()` — أكثر دقة وأفضل أداءً.

**2. `_C` dictionary:** لا تُعدّل مباشرة — استخدم `apply_theme(colors)` فقط.

**3. `tr()` function:** تقبل مفاتيح الترجمة أو نصوص عربية مباشرة — تحول `"حفظ"` تلقائياً لـ `"save"`.

**4. `BulkReplaceService.fetch_candidates`:** يعتمد على `bulk_replace_helpers` في الـ UI layer — انتبه لهذا الـ coupling عند نقل الـ service لبيئة بدون UI.

**5. `BomTreeService` و cache الأعمدة:** استدعي `invalidate_columns_cache()` بعد أي migration يضيف أعمدة لجدول bom، أو أنشئ instance جديد من الـ service.

**6. `CatalogService` والعناصر المشتركة:** تعتمد على `company_state.is_ready` — تأكد من وجود شركة نشطة قبل استدعاء `build()`.

**7. `ScenarioService.calc_cost`:** يحسب التكلفة مباشرة من BOM الخاص بالسيناريو بدون المرور بـ `calc_product_cost` في models — مناسب للمقارنة بين سيناريوهات متعددة.