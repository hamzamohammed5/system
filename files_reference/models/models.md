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

```python
calc_worker_hourly_rate(conn) -> float
# = (monthly_salary ÷ net_hours) × overhead_factor
# net_hours = (working_days - holiday_days) × working_hours_day
# يقرأ من settings عبر get_setting() — كل القيم TEXT تُحوَّل لـ float

raw_unit_price(item_row) -> float
# لو total_qty > 0: price ÷ total_qty | وإلا: price

effective_qty(qty, waste_pct) -> float
# = qty × (1 + waste_pct/100)
```

---

## costing_ops

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

## costing

### `models/costing.py`

```python
calc_cost(conn, item_id, _visited=None, central_conn=None) -> float
# التكلفة الكاملة للمنتج (default scenario)
# يدعم item_id كـ int (محلي) أو "shared:{n}" (مشترك)
# central_conn اختياري — [P-02b] يُحسّن الأداء عند استدعاءات متعددة

calc_product_cost(conn, product_id, scenario_id=None, central_conn=None) -> tuple[float, dict]
# [C-01 / E-01] يحسب تكلفة المنتج مع تفاصيل
# (total_cost, breakdown)
# breakdown: {raw, labor, machine, semi, total}
# scenario_id=None → يستخدم الـ default scenario

calc_cost_breakdown(conn, item_id, central_conn=None) -> dict
# {materials, labor, machine, total}
# للتوافق مع الكود القديم
```

#### أنواع العناصر المدعومة في BOM

| النوع | الحساب |
|-------|--------|
| `raw` | `raw_unit_price` أو `variant_price` |
| `semi` | `calc_cost` متكرر (مع حماية من الحلقات عبر `_visited`) |
| `labor_op` | `calc_labor_op_cost` |
| `machine_op` | `calc_machine_op_cost` |

#### دعم العناصر المشتركة

| النوع المشترك | الحساب |
|---------------|--------|
| `raw` | `_shared_raw_unit_price` من companies.db |
| `labor_op` | `_shared_labor_op_cost` — المعدل من erp.db |
| `machine_op` | `_shared_machine_op_cost` من companies.db |

#### [P-02] Central Connection Cache

```python
_get_central_conn_cached()
# connection مشترك بدل فتح/غلق في كل استدعاء

_central_conn_override
# thread-local store للـ caller-provided connection
```