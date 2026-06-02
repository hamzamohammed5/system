# دليل الكود — Services التكلفة

> `services/costing/` — المنتجات، السيناريوهات، العمالة، الماكينات، المتغيرات، الكتالوج، الاستبدال الشامل، BOM tree.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [product_service](#product_service) | `services/costing/product_service.py` |
| [scenario_service](#scenario_service) | `services/costing/scenario_service.py` |
| [labor_op_service](#labor_op_service) | `services/costing/labor_op_service.py` |
| [machine_service](#machine_service) | `services/costing/machine_service.py` |
| [machine_op_rows_service](#machine_op_rows_service) | `services/costing/machine_op_rows_service.py` |
| [variant_service](#variant_service) | `services/costing/variant_service.py` |
| [catalog_service](#catalog_service) | `services/costing/catalog_service.py` |
| [bulk_replace_service](#bulk_replace_service) | `services/costing/bulk_replace_service.py` |
| [bom_tree_service](#bom_tree_service) | `services/costing/bom_tree_service.py` |

---

## product_service

### `services/costing/product_service.py`

```python
ProductService(conn)

svc.save(product_data: dict, components: list[BomComponent],
         scenario_id=None, scenario_name="سيناريو 1") -> ProductSaveResult
# product_data: {id?, name, type["semi"|"final"], price, category_id?}
# [C-02 / A-03] _save_bom يستخدم replace_bom_for_scenario — migration-safe
# يُطبّق BomComponent.to_tuple() لتوحيد الصيغة
# ProductSaveResult: product_id, scenario_id, is_new, bom_count
# Raises: ValueError لو name فارغ أو components فارغة

svc.calculate_cost(product_id, scenario_id=None) -> CostResult
# [C-01] يستخدم calc_product_cost
# CostResult: product_id, product_name, total_cost, breakdown

svc.get_orphan_components(product_id) -> list[OrphanComponent]
svc.fix_orphans(product_id) -> int
svc.clone(product_id, new_name) -> int
# Raises: ValueError لو new_name فارغ أو product غير موجود
svc.delete(product_id)
```

**`BomComponent`:** `child_type, child_id, qty, waste_pct=0, variant_id=None, machine_op_row_id=None`
- `.to_tuple() -> tuple` — `(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)`

**`_resolve_scenario(product_id, scenario_id, scenario_name, is_new) -> int`:**
```python
# لو scenario_id محدد → يرجعه مباشرة
# لو None → يحاول جلب fetch_default_scenario
# لو مفيش default → ينشئ سيناريو جديد باسم scenario_name
```

**`_save_bom(scenario_id, components)` — [C-02 / A-03]:**
```python
# يستخدم replace_bom_for_scenario() من bom_scenarios_repo
# يحوّل كل component بـ comp.to_tuple()
# الـ repo يتعامل مع وجود/غياب variant_id و machine_op_row_id
# لا خطر من OperationalError على قواعد بيانات قديمة
```

**`clone()` — ملاحظة:**
```python
# ينسخ default scenario فقط
# يستخدم fetch_bom_for_scenario + replace_bom_for_scenario مباشرة
# لو فشل نسخ BOM → warning log بدون exception (الـ product ينشأ بدون BOM)
# يتحقق من وجود "variant_id" و "machine_op_row_id" في row.keys() قبل الوصول
```

**Imports المستخدمة (top-level):**
```python
from db.shared.items_repo import (
    insert_item, update_item, fetch_item, delete_item,
    fetch_bom, fetch_orphan_bom_rows, delete_orphan_bom_rows,
)
from db.costing.bom_scenarios_repo import (
    fetch_scenarios, fetch_default_scenario, insert_scenario,
    fetch_bom_for_scenario,       # [إصلاح] كان اسمه fetch_scenario_bom خطأ
    replace_bom_for_scenario,     # [C-02 / A-03]
)
```

---

## scenario_service

### `services/costing/scenario_service.py`

```python
ScenarioService(conn)
```

#### قراءة

```python
svc.list(item_id) -> list[ScenarioResult]
svc.get(scenario_id) -> ScenarioResult | None
svc.get_default(item_id) -> ScenarioResult | None
svc.get_bom(scenario_id) -> list[BomRowResult]
```

#### كتابة

```python
svc.create(item_id, name, is_default=False) -> int
svc.rename(scenario_id, name)
svc.set_default(scenario_id)
svc.clone(scenario_id, new_name) -> int
svc.delete(scenario_id) -> bool  # يرفض لو آخر سيناريو
svc.replace_bom(scenario_id, rows: list)
# rows: [(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id), ...]
```

#### مساعدات

```python
svc.ensure_default(item_id) -> int
# يتأكد من وجود default scenario — ينشئ "سيناريو 1" لو مفيش

svc.calc_cost(scenario_id) -> float
# يحسب التكلفة الكاملة للسيناريو مباشرة من BOM
# يستخدم: get_bom() + fetch_item, calc_cost (models), calc_labor_op_cost, calc_machine_op_cost
# يمرر row.machine_op_row_id لـ calc_machine_op_cost
# يرجع 0.0 عند أي exception
# منقول من ScenarioComparisonWidget._calc_scenario_cost إلى service layer
```

**`ScenarioResult`:** `id, item_id, name, is_default, notes`
- `.from_row(row) -> ScenarioResult` — يقبل dict أو sqlite3.Row

**`BomRowResult`:** `child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id`
- `.from_row(row) -> BomRowResult` — يقبل dict أو sqlite3.Row

---

## labor_op_service

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
- `.from_row(row) -> LaborOpResult` — يقبل dict أو sqlite3.Row

---

## machine_service

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
- `.from_row(row) -> MachineResult` — يقبل dict أو sqlite3.Row
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
- `.from_row(row) -> MachineOpResult` — يقبل dict أو sqlite3.Row

---

## machine_op_rows_service

### `services/costing/machine_op_rows_service.py`

```python
MachineOpRowsService(conn)
```

#### قراءة

```python
svc.list(op_id) -> list[OpRowResult]
svc.get(row_id) -> OpRowResult | None
```

#### كتابة

```python
svc.add(op_id, label="", value=0.0, count=1.0, sort_order=0) -> int
svc.update(row_id, label, value, count, sort_order=0)
svc.delete(row_id, op_id) -> bool  # يرفض لو آخر صف في العملية
svc.replace(op_id, rows: list)
# rows: [(label, value, count), ...]
```

#### حساب

```python
svc.calc_row_cost(row_id) -> float
# يستدعي get_op_row_cost() — يرجع 0.0 عند أي exception

svc.calc_total_cost(op_id) -> float
# مجموع تكلفة كل الصفوف — يستدعي calc_op_total_cost من repo
```

**دوال مساعدة مستقلة (للاستخدام المباشر من op_rows.py):**
```python
get_op_rows(conn, op_id) -> list   # list of dicts — يستدعي fetch_op_rows ثم dict(r)
get_op_row_cost(conn, row_id) -> float   # يستدعي calc_op_row_cost من repo، يرجع 0.0 عند exception
```

**`OpRowResult`:** `id, op_id, label, value, count, sort_order`
- `.from_row(row) -> OpRowResult`

---

## variant_service

### `services/costing/variant_service.py`

```python
VariantService(conn)
```

#### قراءة

```python
svc.list(item_id) -> list[VariantResult]
svc.get(variant_id) -> VariantResult | None
```

#### كتابة

```python
svc.add(item_id, name, pieces, notes=None) -> int
# Raises: ValueError لو name فارغ أو pieces <= 0

svc.update(variant_id, name, pieces, notes=None)
# Raises: ValueError لو name فارغ أو pieces <= 0

svc.delete(variant_id)
```

#### حساب

```python
svc.calc_unit_cost(variant_id, item_price) -> float
# = item_price ÷ pieces (يستدعي v.calc_unit_cost(item_price))
```

**دوال مساعدة مستقلة (للاستخدام المباشر من variants.py):**
```python
get_variants_for_item(conn, item_id) -> list   # list of dicts
get_variant_unit_cost(conn, variant_id, item_id) -> float | None
# يجلب variant من repo → price من SQL مباشر → price / pieces
# يرجع None لو variant غير موجود أو pieces <= 0 أو price <= 0
get_item_price(conn, item_id) -> float
# SELECT price FROM items WHERE id=? مباشرة، يرجع 0.0 عند الفشل
```

**`VariantResult`:** `id, item_id, name, pieces, notes`
- `.from_row(row) -> VariantResult`
- `.calc_unit_cost(item_price) -> float` — يرجع `item_price` لو `pieces <= 0 أو item_price <= 0`

---

## catalog_service

### `services/costing/catalog_service.py`

```python
CatalogService(conn, central_conn=None)
# central_conn اختياري — يُحسّن الأداء عند استدعاءات متعددة

svc.build() -> dict
# يبني الـ catalog الكامل:
# {
#   "raw":        [(id, name, category_name, price, total_qty), ...],
#   "semi":       [(id, name, category_name, price, None), ...],
#   "final":      [(id, name, category_name, price, None), ...],
#   "labor_op":   [(id, name, category_name, minutes), ...],
#   "machine_op": [(id, name, category_name, mode, machine_name), ...],
# }

svc.build_raw() -> list         # خامات محلية + مشتركة
svc.build_semi() -> list        # نصف مصنع محلي فقط (price=0.0, total_qty=None)
svc.build_final() -> list       # منتج نهائي محلي فقط (price=0.0, total_qty=None)
svc.build_labor_ops() -> list   # عمليات عمالة محلية + مشتركة
svc.build_machine_ops() -> list # عمليات تشغيل محلية + مشتركة
```

**`_fetch_shared(shared_type)` — الشبكة الداخلية:**
```python
# لو self._central_conn متاح → يستخدمه مباشرة (لا يُغلقه)
# لو لا → يفتح get_central_connection() وهو مسؤول عن إغلاقه في finally
# يستخدم json.loads مباشرة (ليس json_utils)
# يطبع خطأ على stderr عند الفشل (لا يرمي exception)
# يتحقق من company_state.is_ready قبل الاتصال
# يرجع [] لو الشركة غير نشطة أو أي خطأ
```

**ثابت:**
```python
SHARED_CATEGORY = "🔗 مشترك"   # اسم تصنيف العناصر المشتركة
```

> **ملاحظة:** العناصر المشتركة تأتي بـ `id = "shared:{n}"` وتصنيف `"🔗 مشترك"`.
> تعتمد على `company_state.is_ready` — تأكد من وجود شركة نشطة قبل استدعاء `build()`.

---

## bulk_replace_service

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
```

**منطق `apply()` الداخلي:**
```python
# يستدعي fetch_bom ثم replace_bom من items_repo (بدون سيناريوهات)
# يتكرر على كل صف BOM:
#   (child_type_b, child_id, qty, waste_pct) ← 4 عناصر فقط
# لو child_type_b == child_type و child_id == old_child_id:
#   final_cid = new_child_id لو do_replace، وإلا child_id
#   أولوية الكمية: uniform_qty → row_qty (لو do_qty) → qty الأصلي
# خطأ في منتج واحد → يُسجَّل في errors ويكمل على الباقين
# رسالة الخطأ: "• {item_name}: {exception}"
```

> ⚠️ **ملاحظة:** يستخدم `fetch_bom/replace_bom` من `items_repo` (بدون سيناريوهات) — لدعم السيناريوهات استخدم `replace_bom_for_scenario` مباشرة.

```python
svc.get_element_name(child_type, child_id) -> str
# يرجع اسم العنصر من الجدول المناسب (items / labor_ops / machine_ops)
# SQL مباشر بدون import
# يرجع f"ID:{child_id}" لو لم يجد

svc.fetch_candidates(child_type, exclude_id) -> list[tuple[int, str, str]]
# عناصر بديلة من نفس النوع بدون العنصر الحالي
# list of (id, name, category_name)
# يعتمد على bulk_replace_helpers في UI layer

svc.fetch_affected_products(child_type, child_id) -> list[dict]
# المنتجات التي تستخدم العنصر في BOM
# كل dict: {id, name, type, qty, category_id, category_name, cost}
```

> ⚠️ `fetch_candidates` و`fetch_affected_products` يعتمدان على `ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py` — انتبه لهذا الـ coupling عند نقل الـ service لبيئة بدون UI.

---

## bom_tree_service

### `services/costing/bom_tree_service.py`

```python
BomTreeService(conn)
```

#### قراءة

```python
svc.get_scenarios(item_id) -> list[ScenarioInfo]
svc.get_bom_for_scenario(scenario_id) -> list[BomComponentRow]
# يتعامل تلقائياً مع schemas مختلفة (مع/بدون waste_pct, variant_id, machine_op_row_id)
# يستخدم PRAGMA table_info مرة واحدة ثم يخزّن في cache (_bom_cols)
# لو الـ query رجعت فارغة → يُجرّب _fallback_bom
# يبني SQL ديناميكياً حسب الأعمدة الموجودة:
#   has_row_id + has_variant + has_waste → SQL كامل
#   has_row_id + has_waste فقط → variant_id = NULL
#   has_waste فقط → variant_id = NULL, machine_op_row_id = NULL
#   لا شيء → 0 as waste_pct, NULLs

svc.get_sub_bom(item_id) -> list[BomComponentRow]
# BOM الفرعي للنصف مصنع — يستخدم default scenario أو أول سيناريو

svc.get_default_scenario_id(item_id) -> int | None
# public method — يُعيد تصدير _get_default_scenario_id
```

#### حذف

```python
svc.delete_component(scenario_id, child_type, child_id)
# DELETE FROM bom WHERE scenario_id=? AND child_type=? AND child_id=?
# + commit

svc.delete_bom_row(parent_id, child_type, child_id)
# يستدعي delete_bom_row من db.shared.items_repo
```

#### مساعدات

```python
svc.invalidate_columns_cache()
# يُصفَّر cache أعمدة BOM (_bom_cols = None)
# يُستدعى بعد migration

svc._get_bom_columns() -> set
# PRAGMA table_info(bom) + cache في self._bom_cols
# يرجع set() عند أي exception

svc._get_default_scenario_id(item_id) -> int | None
# يجرب is_default=1 أولاً، ثم أول سيناريو ORDER BY id

svc._fallback_bom(scenario_id) -> list[BomComponentRow]
# يجلب item_id من bom_scenarios ثم يستدعي fetch_bom القديم
# يدعم rows كـ tuple (4 عناصر) أو sqlite3.Row
# يتحقق من isinstance(r, tuple) لاختيار طريقة القراءة
```

**`ScenarioInfo`:** `id, item_id, name, is_default`
- `.from_row(row) -> ScenarioInfo` — يقبل dict أو sqlite3.Row

**`BomComponentRow`:** `child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id`
- `.from_dict(d) -> BomComponentRow`

> **ملاحظة:** يخزّن نتيجة `PRAGMA table_info(bom)` في cache داخلي (`_bom_cols`) — استدعِ `invalidate_columns_cache()` بعد أي migration يضيف أعمدة لجدول bom، أو أنشئ instance جديد من الـ service.