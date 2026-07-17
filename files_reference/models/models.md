# دليل الكود — Models — حسابات التكلفة

> `models/` — حسابات التكلفة الأساسية.
 
---

## فهرس

| القسم | الملفات |
|-------|---------|
| [costing_base](#costing_base) | `models/costing_base.py` |
| [costing_ops](#costing_ops) | `models/costing_ops.py` |
| [costing](#costing) | `models/costing.py` |

---

## costing_base

### `models/costing_base.py`

**الغرض:** الحسابات الأساسية المشتركة: أجر العامل بالساعة، سعر وحدة الخامة، الكمية الفعلية مع الهادر.

**Imports الخارجية:**
```python
from db.shared.settings_repo import get_setting
```

**من يستدعي هذا الملف:** `models/costing.py` و `models/costing_ops.py` (استيراد مباشر لكل الدوال الثلاث).

**دوال top-level:**

```python
calc_worker_hourly_rate(conn) -> float
```
- يقرأ من `settings` عبر `get_setting()`: `monthly_salary` (افتراضي 3000.0)، `working_days` (افتراضي 25.0)، `holiday_days` (افتراضي 4.0)، `working_hours_day` (افتراضي 8.0)، `overhead_factor` (افتراضي 1.10).
- `net_hours = max(working_days - holiday_days, 1) × max(working_hours_day, 1)` — الحد الأدنى 1 لتفادي القسمة على صفر.
- يرجع `(salary / net_hours) × overhead` إذا `net_hours` غير صفري، وإلا `0.0`.

```python
raw_unit_price(item_row) -> float
```
- `item_row` عنصر يحتوي `price` و `total_qty` (dict أو `sqlite3.Row`).
- لو `total_qty` محددة وأكبر من صفر → `price ÷ total_qty`.
- غير ذلك → `price` مباشرة.

```python
effective_qty(qty, waste_pct) -> float
```
- الكمية الفعلية بعد إضافة نسبة الهادر: `qty × (1 + waste_pct/100)` لو `waste_pct > 0`، وإلا `qty` كما هي.

---

## costing_ops

### `models/costing_ops.py`

**الغرض:** تكلفة عمليات العمالة والتشغيل. تكلفة عمليات التشغيل تُحسب من صفوف `machine_op_rows` (مجموع الصفوف)؛ لو مفيش صفوف يستخدم fallback على `value` في `machine_ops` (السلوك القديم).

**Imports الخارجية:**
```python
from db.costing.operations_repo import fetch_labor_op, fetch_machine_op
from models.costing_base import calc_worker_hourly_rate
# استيراد داخلي (lazy, داخل الدالة نفسها) عند الحاجة:
from db.costing.machine_op_rows_repo import calc_op_total_cost, calc_op_row_cost, fetch_op_rows
```

**من يستدعي هذا الملف:** `models/costing.py`، `services/costing/labor_op_service.py`، `services/costing/machine_service.py` (عبر `MachineOpService.calc_cost`)، `services/costing/scenario_service.py`، `services/costing/bom_tree_service.py`.

**دوال top-level:**

```python
calc_labor_op_cost(conn, op_id: int) -> float
```
- يجلب عملية العمالة عبر `fetch_labor_op`؛ يرجع `0.0` لو لم توجد.
- `(minutes / 60.0) × calc_worker_hourly_rate(conn)`.

```python
calc_machine_op_cost(conn, op_id: int, row_id: int = None) -> float
```
- يجلب عملية التشغيل عبر `fetch_machine_op`؛ يرجع `0.0` لو لم توجد.
- يحاول (داخل `try/except`) استيراد `machine_op_rows_repo` وجلب صفوف العملية عبر `fetch_op_rows`:
  - لو `row_id` محدد وفيه صفوف → يرجع تكلفة ذلك الصف فقط عبر `calc_op_row_cost`.
  - لو `row_id=None` وفيه صفوف → يرجع مجموع كل الصفوف عبر `calc_op_total_cost`.
- **Fallback** (لو مفيش صفوف أو حصل استثناء في الاستيراد/الاستعلام): يستخدم القيمة القديمة في `machine_ops` نفسها:
  - `mode == "time"` → `(value / 60.0) × rate_per_hour`.
  - غير ذلك (`mode == "unit"`) → `value × rate_per_unit`.

**ملاحظات مهمة من الكود:** الـ docstring في أعلى الملف يوضّح صراحة أن هذا التصميم مقصود (BOM-per-row) مع الحفاظ على التوافق الخلفي (fallback) لقواعد البيانات القديمة التي لا تحتوي صفوف `machine_op_rows`.

---

## costing

### `models/costing.py`

**الغرض:** Facade يُعيد تصدير الدوال الأساسية من `costing_base`/`costing_ops` ويضيف `calc_cost` و `calc_product_cost` و `calc_cost_breakdown` مع دعم كامل للعناصر المشتركة بين الشركات (IDs بالشكل `"shared:{n}"`) وللـ BOM متعدد السيناريوهات.

**Imports الخارجية:**
```python
from models.costing_base import calc_worker_hourly_rate, raw_unit_price, effective_qty
from models.costing_ops import calc_labor_op_cost, calc_machine_op_cost
from db.shared.items_repo import (
    fetch_item, fetch_bom, is_shared_id, extract_shared_id,
    _get_central_conn_cached,   # [P-02] cached connection بدل فتح/غلق متكرر
)
# استيراد داخلي (lazy) في _get_shared_data:
from db.shared.json_utils import decode_json
```

**من يستدعي هذا الملف:** `services/costing/product_service.py` (`calc_product_cost` في `calculate_cost`)، `services/costing/bulk_replace_service.py` (`calc_cost` في `fetch_affected_products`)، `services/costing/scenario_service.py` (`calc_cost` في `calc_cost` الخاص بالسيناريو)، `services/costing/bom_tree_service.py` (`calc_cost` في `get_node_data`)، `services/pricing/offers_service.py` (`calc_cost` في `get_item_cost`).

### Module-level state

```python
_central_conn_override: dict = {"conn": None}
```
- **[P-02b]** مخزن بسيط على مستوى الموديول (single-threaded safe لأن التطبيق PyQt أحادي الخيط) يسمح للـ caller بتمرير `central_conn` صريح إلى `calc_cost` / `calc_product_cost` / `calc_cost_breakdown`، بحيث تستخدمه كل استدعاءات `_get_shared_data` الداخلية بدل الاتصال الافتراضي المُخزَّن (`_get_central_conn_cached()`). يُستعاد للقيمة السابقة دائماً في `finally` حتى عند حدوث خطأ — لمنع تسرّب الحالة بين الاستدعاءات المتداخلة.

### دوال top-level (مساعدة/داخلية)

```python
_get_variant_id(row) -> int | None
_get_machine_op_row_id(row) -> int | None
```
- استخراج آمن لعمود `variant_id` / `machine_op_row_id` من صف قد لا يحتوي هذه الأعمدة (يلتقط `IndexError`/`KeyError` ويرجع `None`).

```python
_raw_cost_with_variant(conn, item_row, variant_id) -> float
```
- لو `variant_id` محدد: يجلب `pieces` من جدول `raw_variants` مباشرة بـ SQL، ولو `pieces > 0` يرجع `item_row["price"] / pieces`.
- غير ذلك → `raw_unit_price(item_row)` العادية.

```python
_get_shared_data(shared_item_id: int) -> dict
```
- يجلب بيانات عنصر مشترك من `companies.db` (`shared_items` table، عمودي `shared_type` و `data` بصيغة JSON عبر `decode_json`).
- **[P-02b]** يستخدم `_central_conn_override["conn"]` أولاً لو نشط، وإلا `_get_central_conn_cached()`.
- يرجع `{}` عند أي استثناء (لا يرمي).

```python
_shared_raw_unit_price(shared_item_id) -> float
_shared_labor_op_cost(conn, shared_item_id) -> float
_shared_machine_op_cost(shared_item_id) -> float
```
- نفس منطق الحساب المحلي (`raw_unit_price` / `calc_worker_hourly_rate` / fallback الـ time-or-unit) لكن مصدر البيانات `_get_shared_data()` بدل الجداول المحلية.

```python
_col_exists(conn, table, col) -> bool
```
- فحص وجود عمود عبر `PRAGMA table_info` — يرجع `False` عند أي استثناء.

```python
_fetch_bom_for_scenario_id(conn, scenario_id) -> list
_fetch_bom_default(conn, item_id) -> list
_fetch_bom_by_scenario(conn, item_id, scenario_id) -> list
_fetch_bom_fallback(conn, item_id) -> list
```
- مجموعة دوال جلب BOM تتعامل مع الفروقات بين قواعد بيانات قد تحتوي أو لا تحتوي أعمدة `variant_id`/`machine_op_row_id` (migration-safe عبر `_col_exists`):
  - `_fetch_bom_for_scenario_id`: SQL ديناميكي حسب الأعمدة الموجودة، مرتب بـ `scenario_id`.
  - `_fetch_bom_default`: يجلب الـ `default scenario` (أو أول سيناريو) للـ `item_id` ثم يستدعي `_fetch_bom_for_scenario_id`؛ لو فشل كل شيء → `_fetch_bom_fallback`.
  - `_fetch_bom_by_scenario`: **[C-01/E-01]** نقطة الدخول التي تفرّق بين `scenario_id` محدد صراحة (يتحقق أنه ينتمي لنفس `item_id`) أو `None` (يرجع لـ `_fetch_bom_default`).
  - `_fetch_bom_fallback`: يستعلم مباشرة بـ `parent_id=?` (نظام BOM القديم بدون scenarios)، وإلا يستدعي `fetch_bom` من `items_repo` كملاذ أخير.

```python
_calc_child_cost(conn, child_type, child_id, variant_id=None, machine_op_row_id=None, _visited=None) -> float
```
- نقطة موحّدة لحساب تكلفة أي `child_id` سواء محلي (`int`) أو مشترك (`str` بصيغة `"shared:{n}"`، يُكتشف عبر `is_shared_id`).
- للعناصر المشتركة: يوجّه حسب `child_type` (`raw`/`semi` → `_shared_raw_unit_price`، `labor_op` → `_shared_labor_op_cost`، `machine_op` → `_shared_machine_op_cost`).
- للعناصر المحلية: `raw` → `_raw_cost_with_variant`، `semi` → استدعاء متكرر لـ `calc_cost` (مع تمرير نسخة من `_visited`)، `labor_op` → `calc_labor_op_cost`، `machine_op` → `calc_machine_op_cost(row_id=machine_op_row_id)`.

### دوال top-level (عامة)

```python
calc_cost(conn, item_id, _visited=None, central_conn=None) -> float
```
- التكلفة الكاملة لمنتج/خامة باستخدام الـ **default scenario**. يدعم `item_id` كـ `int` محلي أو `str "shared:{n}"` مشترك.
- **[P-02b]** يضبط `_central_conn_override["conn"]` مؤقتاً لو `central_conn` مُمرَّر، وينفّذ الحساب الفعلي عبر `_calc_cost_impl` داخل `try/finally` لضمان استعادة القيمة السابقة دائماً.

```python
_calc_cost_impl(conn, item_id, _visited=None) -> float
```
- التنفيذ الفعلي: لو `item_id` مشترك → `_shared_raw_unit_price` مباشرة. لو محلي: يحمي من الحلقات عبر `_visited` (set من IDs)، لو `type == "raw"` → `raw_unit_price`، وإلا يتكرر على صفوف `_fetch_bom_default` ويجمع `unit_cost × effective_qty(qty, waste_pct)` لكل صف عبر `_calc_child_cost`.

```python
calc_product_cost(conn, product_id, scenario_id=None, central_conn=None) -> tuple[float, dict]
```
- **[C-01/E-01]** يحسب تكلفة منتج مع تفصيل بـ 4 فئات، بدعم `scenario_id` صريح (`None` = default). يستخدم نفس آلية `_central_conn_override` كـ `calc_cost`، وينفّذ الحساب عبر `_calc_product_cost_impl`.

```python
_calc_product_cost_impl(conn, product_id, scenario_id) -> tuple[float, dict]
```
- لو `item["type"] == "raw"` → يرجع `raw_unit_price` مباشرة مع breakdown كله في `"raw"`.
- غير ذلك: يجلب BOM عبر `_fetch_bom_by_scenario`، يهيّئ `visited = {product_id}`، ويجمع كل صف في الفئة المناسبة (`raw`/`labor`/`machine`/`semi`) بحساب `unit_cost × effective_qty`.
- يرجع `(total, breakdown)` حيث `breakdown = {raw, labor, machine, semi, total}`.

```python
calc_cost_breakdown(conn, item_id, central_conn=None) -> dict
```
- تفصيل التكلفة بصيغة **قديمة متوافقة**: `{materials, labor, machine, total}` (يدمج `raw`+`semi` تحت `materials`). يستخدم `_fetch_bom_default` (الـ default scenario فقط، بدون دعم `scenario_id` صريح). لنفس آلية `_central_conn_override` عبر `_calc_cost_breakdown_impl`.

### أنواع العناصر المدعومة في BOM

| النوع | الحساب المحلي | الحساب المشترك |
|-------|--------|--------|
| `raw` | `_raw_cost_with_variant` (يدعم `variant_id`) | `_shared_raw_unit_price` من `companies.db` |
| `semi` | `calc_cost` متكرر (حماية من الحلقات عبر `_visited`) | `_shared_raw_unit_price` (نفس منطق raw) |
| `labor_op` | `calc_labor_op_cost` | `_shared_labor_op_cost` — المعدل من `erp.db` المحلي |
| `machine_op` | `calc_machine_op_cost(row_id=machine_op_row_id)` | `_shared_machine_op_cost` من `companies.db` |

### `__all__`
```python
__all__ = [
    "calc_worker_hourly_rate", "raw_unit_price", "effective_qty",   # re-export من costing_base
    "calc_labor_op_cost", "calc_machine_op_cost",                    # re-export من costing_ops
    "calc_cost", "calc_product_cost", "calc_cost_breakdown",         # دوال هذا الملف
]
```

### ملاحظات مهمة من التعليقات
- **[C-01/E-01]** `calc_product_cost` أُضيفت لدعم `scenario_id` صريح وترجع `(total, breakdown)` بدل `float` واحدة — تُستخدم من `ProductService.calculate_cost`.
- **[P-02]** `_get_shared_data` تستخدم `_get_central_conn_cached()` بدل فتح/غلق اتصال `companies.db` في كل استدعاء (تحسين أداء).
- **[P-02b]** إضافة `central_conn` اختياري لـ `calc_cost`/`calc_product_cost`/`calc_cost_breakdown` — مفيد خصوصاً في `offers_repo.calc_offer_summary` (اتصال واحد لكل عرض بدل فتح اتصال منفصل لكل منتج)، وفي الاختبارات، وسيناريوهات تعدد الشركات. مُطبَّق عبر thread-local-style override بسيط (`_central_conn_override` dict) لأن التطبيق أحادي الخيط.

---

## علاقات الملفات

- `models/costing.py` يستورد من `models/costing_base.py` (كل الدوال الثلاث) و `models/costing_ops.py` (`calc_labor_op_cost`, `calc_machine_op_cost`) — وهو الواجهة الموحّدة (facade) التي يُفترض أن تستخدمها بقية الطبقات بدل استيراد `costing_base`/`costing_ops` مباشرة لحسابات الـ BOM الكاملة.
- `models/costing_ops.py` يستورد `calc_worker_hourly_rate` من `models/costing_base.py` فقط.
- `models/costing_base.py` لا يعتمد على أي ملف آخر داخل `models/` — هو القاعدة الأدنى في هذه الحزمة.
- تبعية خارج هذا المسار: الثلاثة يعتمدون على `db/shared/items_repo.py`، `db/shared/settings_repo.py`، `db/costing/operations_repo.py`، `db/costing/machine_op_rows_repo.py`، و `db/shared/json_utils.py` (تفصيلها في المرجع الخاص بـ `db/`).
- يُستخدم هذا المسار بكثافة من `services/costing/*` و `services/pricing/offers_service.py` (راجع `services_costing.md` و `services_pricing.md`).