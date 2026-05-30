# دليل الكود — DB (6): التكلفة والتسعير

> جداول إضافية في `erp.db` — السيناريوهات، صفوف العمليات، المتغيرات، التسعير، العروض.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [هيكل الجداول الإضافية](#هيكل-الجداول-الإضافية) | — |
| [bom_scenarios_repo](#bom_scenarios_repo) | `db/costing/bom_scenarios_repo.py` |
| [operations_repo](#operations_repo) | `db/costing/operations_repo.py` |
| [machine_op_rows_repo](#machine_op_rows_repo) | `db/costing/machine_op_rows_repo.py` |
| [raw_variants_repo](#raw_variants_repo) | `db/costing/raw_variants_repo.py` |
| [pricing_repo](#pricing_repo) | `db/pricing/pricing_repo.py` |
| [offers_repo](#offers_repo) | `db/pricing/offers_repo.py` |

---

## هيكل الجداول الإضافية

جداول إضافية في `erp.db`:

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `bom_scenarios` | `id, item_id→CASCADE, name, is_default, notes` |
| `machine_op_rows` | `id, op_id→machine_ops, label, value, count, sort_order` |
| `raw_variants` | `id, item_id→items CASCADE, name, pieces>0, notes` |

جداول `erp.db` للتسعير:

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `pricing` | `id, item_id UNIQUE, margin, price` |

---

## bom_scenarios_repo

### `db/costing/bom_scenarios_repo.py`

#### BOM columns cache — [إصلاح 8] موحد مع items_repo

```python
invalidate_bom_cols_cache(conn=None)
# استدعه بعد أي migration يضيف أعمدة لجدول bom
```

#### السيناريوهات

```python
fetch_scenarios(conn, item_id) -> list
fetch_scenario(conn, scenario_id) -> row
fetch_default_scenario(conn, item_id) -> row | None
insert_scenario(conn, item_id, name, is_default=False, notes="") -> int
update_scenario(conn, scenario_id, name, notes="")
set_default_scenario(conn, scenario_id)
delete_scenario(conn, scenario_id) -> bool  # يرفض لو آخر سيناريو
clone_scenario(conn, scenario_id, new_name) -> int
```

#### BOM للسيناريو

```python
fetch_bom_for_scenario(conn, scenario_id) -> list
replace_bom_for_scenario(conn, scenario_id, rows)
# rows: [(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id), ...]
```

---

## operations_repo

### `db/costing/operations_repo.py`

#### الماكينات

```python
fetch_all_machines(conn) -> list
fetch_machine(conn, machine_id) -> row
insert_machine(conn, name, rate_per_hour, rate_per_unit, category_id=None) -> int
update_machine(conn, machine_id, name, rate_per_hour, rate_per_unit, category_id=None)
count_machine_ops(conn, machine_id) -> int
# [تحسين 19] للتحقق قبل الحذف — CASCADE صامت على machine_ops
delete_machine(conn, machine_id)  # CASCADE على machine_ops
```

#### عمليات العمالة

```python
fetch_all_labor_ops(conn) -> list
fetch_labor_op(conn, op_id) -> row
insert_labor_op(conn, name, minutes, category_id=None) -> int
update_labor_op(conn, op_id, name, minutes, category_id=None)
delete_labor_op(conn, op_id)
```

#### عمليات التشغيل

```python
fetch_all_machine_ops(conn) -> list
fetch_machine_op(conn, op_id) -> row
insert_machine_op(conn, machine_id, name, mode, value, category_id=None) -> int
# mode: "time" | "unit"
update_machine_op(conn, op_id, machine_id, name, mode, value, category_id=None)
delete_machine_op(conn, op_id)
```

---

## machine_op_rows_repo

### `db/costing/machine_op_rows_repo.py`

```python
fetch_op_rows(conn, op_id) -> list
fetch_op_row(conn, row_id) -> row
insert_op_row(conn, op_id, label="", value=0.0, count=1.0, sort_order=0) -> int
update_op_row(conn, row_id, label, value, count, sort_order=0)
delete_op_row(conn, row_id)
replace_op_rows(conn, op_id, rows: list[tuple])
# rows: [(label, value, count), ...]

calc_op_row_cost(conn, row_id) -> float
# mode="time": (value/60) × rate_per_hour / count
# mode="unit": (value × rate_per_unit) / count

calc_op_total_cost(conn, op_id) -> float
# مجموع تكاليف كل الصفوف
```

---

## raw_variants_repo

### `db/costing/raw_variants_repo.py`

```python
fetch_variants_for_item(conn, item_id) -> list
fetch_variant(conn, variant_id) -> row
insert_variant(conn, item_id, name, pieces, notes=None) -> int
update_variant(conn, variant_id, name, pieces, notes=None)
delete_variant(conn, variant_id)

calc_unit_cost_with_variant(item_row, variant_id, conn) -> float
# الأولوية: variant → price÷pieces | total_qty → price÷total_qty | price مباشرة
```

---

## pricing_repo

### `db/pricing/pricing_repo.py`

```python
fetch_all_pricing(conn, limit=500, offset=0) -> list
# [تحسين 23b] يدعم pagination

fetch_pricing_count(conn) -> int
# [تحسين 23b] إجمالي المنتجات النهائية

fetch_all_pricing_paginated(conn, limit=200, offset=0,
                            category_id=None, search=None,
                            only_priced=False) -> list
# [تحسين 23b] pagination كاملة مع فلترة

fetch_pricing(conn, item_id) -> row | None

upsert_pricing(conn, item_id, margin, price)
# [تحسين 23] يتحقق أن item_id نوعه "final"
# Raises: ValueError لو غير موجود أو نوعه ليس final

delete_pricing(conn, item_id)
```

---

## offers_repo

### `db/pricing/offers_repo.py`

```python
fetch_all_offers(conn) -> list
fetch_offer(conn, offer_id) -> row
insert_offer(conn, name, discount, notes="", category_id=None) -> int
update_offer(conn, offer_id, name, discount, notes="", category_id=None)
delete_offer(conn, offer_id)

fetch_offer_items(conn, offer_id) -> list
replace_offer_items(conn, offer_id, items: list[tuple])
# items: [(item_id, qty), ...]

calc_offer_summary(conn, offer_id) -> dict
# [تحسين 14] cost_cache — كل item_id يُحسب مرة واحدة
# [P-02] central_conn مشترك لكل الحسابات — لا فتح/غلق متكرر
# {offer_id, offer_name, discount, lines: [...], total_listed, sell_price,
#  total_cost, profit}
# كل line: {item_id, item_name, qty, unit_cost, unit_price,
#           line_cost, line_listed, has_pricing}
```