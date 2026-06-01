# دليل الكود — DB: التكلفة (db/costing/)

> جداول `erp.db` الخاصة بالتكلفة — Schema، السيناريوهات، صفوف العمليات، المتغيرات.

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [schema.py](#schemapy) | إنشاء وتهيئة erp.db |
| [bom_scenarios_repo.py](#bom_scenarios_repopy) | سيناريوهات BOM |
| [machine_op_rows_repo.py](#machine_op_rows_repopy) | صفوف عمليات التشغيل |
| [operations_repo.py](#operations_repopy) | الماكينات وعمليات العمالة والتشغيل |
| [raw_variants_repo.py](#raw_variants_repopy) | متغيرات الخامات |

---

## schema.py

```python
_init_erp_db(conn)
# يُهيئ erp.db من connection جاهز
# يُستدعى من companies_repo._init_company_databases() عند إنشاء شركة جديدة

_migrate_erp_db(conn)
# Migrations آمنة للشركات الموجودة:
#   [إصلاح 3] يضيف total_qty لجدول items لو ناقص
#   [إصلاح 4] يُنشئ جدول categories لو ناقص

init_db()
# للتوافق القديم فقط — يُهيئ companies.db المركزية
```

**القيم الافتراضية في `settings` (كلها TEXT):**

| المفتاح | القيمة الافتراضية |
|---------|-----------------|
| `monthly_salary` | `"3000.0"` |
| `working_days` | `"25.0"` |
| `holiday_days` | `"4.0"` |
| `working_hours_day` | `"8.0"` |
| `overhead_factor` | `"1.10"` |
| `font_size` | `"11.0"` |

> ⚠️ القيم تُدرج بـ `INSERT OR IGNORE` — لن تُعيد كتابة قيم موجودة.

**جداول erp.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `categories` | `id, name, scope DEFAULT "all", color DEFAULT "#607d8b", parent_id→SET NULL, template_fields TEXT, default_unit DEFAULT "mm"` |
| `items` | `id, name, type CHECK("raw"\|"semi"\|"final"), price DEFAULT 0, total_qty REAL, category_id→SET NULL` |
| `machines` | `id, name, rate_per_hour DEFAULT 0, rate_per_unit DEFAULT 0, category_id→SET NULL` |
| `labor_ops` | `id, name, minutes DEFAULT 0, category_id→SET NULL` |
| `machine_ops` | `id, machine_id→CASCADE, name, mode CHECK("time"\|"unit"), value DEFAULT 0, category_id→SET NULL` |
| `bom` | `id, parent_id→CASCADE, child_type CHECK("raw"\|"semi"\|"labor_op"\|"machine_op"), child_id, qty DEFAULT 1, child_name TEXT` |
| `settings` | `key TEXT PRIMARY KEY, value TEXT NOT NULL DEFAULT ""` |
| `bom_scenarios` | `id, item_id→CASCADE, name, is_default, notes` |
| `machine_op_rows` | `id, op_id→machine_ops, label, value, count, sort_order` |
| `raw_variants` | `id, item_id→items CASCADE, name, pieces>0, notes` |

> ⚠️ **ترتيب الإنشاء مهم [إصلاح 4]:** `categories` يُنشأ أولاً.
> ⚠️ جدول `bom` الأساسي لا يحتوي `waste_pct`, `variant_id`, `machine_op_row_id`, `scenario_id` — تُضاف عبر migrations. استخدم `_get_bom_cols(conn)` للتحقق.

---

## bom_scenarios_repo.py

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
# يرجع الـ default — لو مفيش يرجع أول سيناريو
insert_scenario(conn, item_id, name, is_default=False, notes="") -> int
update_scenario(conn, scenario_id, name, notes="")
set_default_scenario(conn, scenario_id)
delete_scenario(conn, scenario_id) -> bool
# يرفض لو آخر سيناريو
clone_scenario(conn, scenario_id, new_name) -> int
```

#### BOM للسيناريو

```python
fetch_bom_for_scenario(conn, scenario_id) -> list
# يستخدم _get_bom_cols() مع cache — يتعامل مع وجود/غياب الأعمدة

replace_bom_for_scenario(conn, scenario_id, rows)
# rows: [(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id), ...]
```

---

## machine_op_rows_repo.py

كل عملية تشغيل (machine_op) ممكن يكون ليها أكثر من صف.
تكلفة الصف = `(value × rate_per_hour ÷ 60) ÷ count` [لو mode=time]
            = `(value × rate_per_unit) ÷ count` [لو mode=unit]

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

## operations_repo.py

#### الماكينات

```python
fetch_all_machines(conn) -> list
fetch_machine(conn, machine_id) -> row
insert_machine(conn, name, rate_per_hour, rate_per_unit, category_id=None) -> int
update_machine(conn, machine_id, name, rate_per_hour, rate_per_unit, category_id=None)

count_machine_ops(conn, machine_id) -> int
# [تحسين 19] للتحقق قبل الحذف — CASCADE صامت على machine_ops
# استدعه في الـ UI قبل حذف الماكينة وأظهر تأكيداً للمستخدم

delete_machine(conn, machine_id)
# CASCADE على machine_ops — استدعِ count_machine_ops() أولاً
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

## raw_variants_repo.py

كل خامة ممكن يكون ليها variants — كل variant بيعبر عن عدد القطع اللي بتنتجها من الخامة.

```python
fetch_variants_for_item(conn, item_id) -> list
fetch_variant(conn, variant_id) -> row
insert_variant(conn, item_id, name, pieces, notes=None) -> int
update_variant(conn, variant_id, name, pieces, notes=None)
delete_variant(conn, variant_id)

calc_unit_cost_with_variant(item_row, variant_id, conn) -> float
# الأولوية:
# 1. variant_id محدد → price ÷ pieces
# 2. total_qty محددة → price ÷ total_qty
# 3. السعر مباشرة
```

---

## ملاحظات

- `settings.value` عمود TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.
- استدعِ `invalidate_bom_cols_cache(conn)` بعد أي migration يضيف أعمدة لجدول bom.
- استدعِ `count_machine_ops()` قبل حذف الماكينة لتحذير المستخدم من CASCADE الصامت.