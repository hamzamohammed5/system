# دليل الكود — DB: التكلفة (db/costing/) — نسخة محدَّثة

> جداول `erp.db` الخاصة بالتكلفة.
> **آخر تحديث:** يعكس الكود الفعلي في السياق — يُستخدم بدلاً من `db_03_costing.md`

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
# يُستدعى من companies_repo._init_company_databases()

_migrate_erp_db(conn)
# Migrations آمنة للشركات الموجودة

init_db()
# للتوافق القديم فقط — يُهيئ companies.db المركزية بدون erp.db
```

**ترتيب إنشاء الجداول في `_init_erp_db` ([إصلاح 4]):**
```
1. categories  ← أولاً لأن الجداول التالية تُحيل إليه
2. items
3. machines
4. labor_ops
5. machine_ops
6. bom
7. settings    (TEXT column — [إصلاح 5])
```

**جداول erp.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `categories` | id, name, scope DEFAULT "all", color DEFAULT "#607d8b", parent_id→SET NULL, template_fields TEXT, default_unit DEFAULT "mm" |
| `items` | id, name, type CHECK("raw"\|"semi"\|"final"), price DEFAULT 0, total_qty REAL ([إصلاح 3]), category_id→SET NULL |
| `machines` | id, name, rate_per_hour DEFAULT 0, rate_per_unit DEFAULT 0, category_id→SET NULL |
| `labor_ops` | id, name, minutes DEFAULT 0, category_id→SET NULL |
| `machine_ops` | id, machine_id→CASCADE, name, mode CHECK("time"\|"unit"), value DEFAULT 0, category_id→SET NULL |
| `bom` | id, parent_id→CASCADE, child_type CHECK(4 أنواع), child_id, qty DEFAULT 1, child_name TEXT |
| `settings` | key TEXT PRIMARY KEY, value TEXT DEFAULT "" ([إصلاح 5]) |

**القيم الافتراضية في `settings` (كلها TEXT):**

| المفتاح | القيمة |
|---------|--------|
| `monthly_salary` | `"3000.0"` |
| `working_days` | `"25.0"` |
| `holiday_days` | `"4.0"` |
| `working_hours_day` | `"8.0"` |
| `overhead_factor` | `"1.10"` |
| `font_size` | `"11.0"` |

> ⚠️ تُدرج بـ `INSERT OR IGNORE` — لن تُعيد كتابة قيم موجودة.
> ⚠️ القيم TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.

**`_migrate_erp_db(conn)` — تحققات إضافة:**
```python
# [إصلاح 4] categories لو ناقصة → CREATE TABLE
# [إصلاح 3] total_qty في items لو ناقص → ALTER TABLE items ADD COLUMN total_qty REAL
# [إصلاح 5] settings.value لا يحتاج تغيير نوع — SQLite type affinity يتعامل معه
```

**جدول `bom` الأساسي لا يحتوي:**
`waste_pct`, `variant_id`, `machine_op_row_id`, `scenario_id`
→ تُضاف عبر migrations. استخدم `_get_bom_cols(conn)` للتحقق دائماً.

---

## bom_scenarios_repo.py

### BOM columns cache — [إصلاح 8]

```python
_bom_cols_cache: dict[str, set] = {}
# key: db_path من PRAGMA database_list أو str(id(conn)) كـ fallback

_get_bom_cols(conn) -> set
# يُعيد أعمدة جدول bom مع cache بمفتاح db_path
# [إصلاح 8] موحَّد مع items_repo — نفس strategy

invalidate_bom_cols_cache(conn=None)
# conn=None → _bom_cols_cache.clear()
# conn=<conn> → _bom_cols_cache.pop(path, None)
# يُستدعى بعد أي migration يضيف أعمدة

_col_exists(conn, table, col) -> bool
# table=="bom" → _get_bom_cols() | غيره → PRAGMA table_info مباشرة

_resolve_name(conn, child_type, child_id) -> str | None
# "raw"|"semi" → items | "labor_op" → labor_ops | "machine_op" → machine_ops
```

### السيناريوهات — CRUD

```python
fetch_scenarios(conn, item_id: int) -> list
# SELECT id, item_id, name, is_default, notes, created_at ORDER BY id

fetch_scenario(conn, scenario_id: int) -> row
fetch_default_scenario(conn, item_id: int) -> row | None
# is_default=1 أولاً → fallback: أول سيناريو ORDER BY id

insert_scenario(conn, item_id, name, is_default=False, notes="") -> int
# لو is_default=True → UPDATE بقية السيناريوهات SET is_default=0

update_scenario(conn, scenario_id, name, notes="")
set_default_scenario(conn, scenario_id)

delete_scenario(conn, scenario_id) -> bool
# يرجع False لو آخر سيناريو
# يحذف: bom WHERE scenario_id=? أولاً ثم السيناريو نفسه
# لو is_default → يُعيَّن أول متبقٍ كـ default

clone_scenario(conn, scenario_id, new_name) -> int
# ينسخ مع كل بنود BOM
# يتحقق من "variant_id" و "machine_op_row_id" في r.keys() بأمان
```

### BOM للسيناريو

```python
fetch_bom_for_scenario(conn, scenario_id: int) -> list
# يستخدم _get_bom_cols() — يختار SELECT حسب الأعمدة الموجودة:
# has_row_id + has_variant → كامل
# has_row_id فقط          → NULL as variant_id
# has_variant فقط         → NULL as machine_op_row_id
# لا شيء                  → NULL as variant_id, NULL as machine_op_row_id
# دائماً: COALESCE(waste_pct,0) as waste_pct

replace_bom_for_scenario(conn, scenario_id: int, rows)
# rows: [(child_type, child_id, qty, waste_pct?, variant_id?, machine_op_row_id?), ...]
# DELETE FROM bom WHERE scenario_id=? → _insert_bom_row لكل صف
```

**`_insert_bom_row(conn, parent_id, child_type, child_id, qty, child_name,
                   waste_pct, variant_id, machine_op_row_id, scenario_id)`:**
```python
# INSERT آمن — يختار الأعمدة حسب _get_bom_cols():
# has_variant + has_row_id + has_scenario → 9 أعمدة
# has_row_id + has_scenario              → 8 أعمدة (بدون variant_id)
# has_variant + has_scenario             → 8 أعمدة (بدون machine_op_row_id)
# has_row_id فقط                         → 7 أعمدة
# has_scenario فقط                       → 7 أعمدة
# لا شيء                                 → 6 أعمدة (الأساسية فقط)
# لو child_name=None → يستدعي _resolve_name()
```

---

## machine_op_rows_repo.py

**جدول:** `machine_op_rows (id, op_id→machine_ops, label, value, count, sort_order)`

**صيغة التكلفة:**
```
mode="time": (value / 60.0) × rate_per_hour / max(count, 0.0001)
mode="unit": (value × rate_per_unit)         / max(count, 0.0001)
```

```python
fetch_op_rows(conn, op_id: int) -> list
# ORDER BY sort_order, id
# الأعمدة: id, op_id, label, value, count, sort_order

fetch_op_row(conn, row_id: int) -> row

insert_op_row(conn, op_id, label="", value=0.0,
              count=1.0, sort_order=0) -> int
# count = max(count, 0.0001) ← يمنع القسمة على صفر

update_op_row(conn, row_id, label, value, count, sort_order=0)
# count = max(count, 0.0001)

delete_op_row(conn, row_id: int)

replace_op_rows(conn, op_id: int, rows: list[tuple])
# rows: [(label, value, count), ...]
# DELETE القديم → INSERT الجديد مع enumerate لـ sort_order
# كل count = max(count, 0.0001)

calc_op_row_cost(conn, row_id: int) -> float
# يجلب الصف + بيانات الماكينة عبر JOIN:
#   SELECT mo.mode, m.rate_per_hour, m.rate_per_unit
#   FROM machine_ops mo JOIN machines m ON m.id = mo.machine_id
#   WHERE mo.id = row["op_id"]
# يرجع 0.0 لو الصف أو بيانات الماكينة غير موجودة

calc_op_total_cost(conn, op_id: int) -> float
# مجموع calc_op_row_cost لكل الصفوف
# يرجع 0.0 لو لا يوجد صفوف
```

---

## operations_repo.py

### الماكينات

```python
fetch_all_machines(conn) -> list
# مع category_id, category_name من LEFT JOIN ORDER BY m.name
# الأعمدة: id, name, rate_per_hour, rate_per_unit, category_id, category_name

fetch_machine(conn, machine_id: int) -> row

insert_machine(conn, name, rate_per_hour, rate_per_unit,
               category_id=None) -> int
update_machine(conn, machine_id, name, rate_per_hour, rate_per_unit,
               category_id=None)

count_machine_ops(conn, machine_id: int) -> int
# [تحسين 19] SELECT COUNT(*) FROM machine_ops WHERE machine_id=?
# استخدمه في الـ UI قبل حذف الماكينة لتحذير المستخدم
# السبب: machine_ops.machine_id→CASCADE يحذف كل العمليات بصمت

delete_machine(conn, machine_id: int)
# CASCADE على machine_ops — استدعِ count_machine_ops() أولاً في الـ UI
```

**نمط UI الموصى به قبل الحذف:**
```python
ops_count = count_machine_ops(conn, machine_id)
if ops_count > 0:
    # أظهر تأكيد للمستخدم يذكر عدد العمليات المتأثرة
    pass
```

### عمليات العمالة

```python
fetch_all_labor_ops(conn) -> list
# مع category_name من LEFT JOIN ORDER BY lo.name
# الأعمدة: id, name, minutes, category_id, category_name

fetch_labor_op(conn, op_id: int) -> row

insert_labor_op(conn, name, minutes, category_id=None) -> int
update_labor_op(conn, op_id, name, minutes, category_id=None)
delete_labor_op(conn, op_id: int)
```

### عمليات التشغيل

```python
fetch_all_machine_ops(conn) -> list
# مع machine_name, rate_per_hour, rate_per_unit من JOIN
# مع category_name من LEFT JOIN ORDER BY mo.name
# الأعمدة: id, name, mode, value, machine_id, category_id,
#           machine_name, rate_per_hour, rate_per_unit, category_name

fetch_machine_op(conn, op_id: int) -> row

insert_machine_op(conn, machine_id, name, mode, value,
                  category_id=None) -> int
# mode: "time" | "unit"

update_machine_op(conn, op_id, machine_id, name, mode, value,
                  category_id=None)
delete_machine_op(conn, op_id: int)
```

---

## raw_variants_repo.py

**جدول:** `raw_variants (id, item_id→items CASCADE, name, pieces REAL CHECK(>0), notes)`

**المنطق:** خامة واحدة → عدة variants → كل variant = عدد القطع التي تُنتجها الخامة.
```
مثال: قماش 100ج → variant "قميص كبير" pieces=2 → تكلفة الوحدة=50ج
                 → variant "قميص صغير" pieces=3 → تكلفة الوحدة=33.33ج
```

```python
create_raw_variants_table(conn)
# CREATE TABLE IF NOT EXISTS raw_variants (...)

fetch_variants_for_item(conn, item_id: int) -> list
# SELECT id, item_id, name, pieces, notes ORDER BY name

fetch_variant(conn, variant_id: int) -> row
# SELECT id, item_id, name, pieces, notes

insert_variant(conn, item_id, name, pieces, notes=None) -> int
update_variant(conn, variant_id, name, pieces, notes=None)
delete_variant(conn, variant_id: int)

calc_unit_cost_with_variant(item_row, variant_id: int | None, conn) -> float
# الأولوية:
#   1. variant_id is not None:
#      var = fetch_variant(conn, variant_id)
#      لو var و float(var["pieces"]) > 0 → price / float(var["pieces"])
#   2. fallback: raw_unit_price(item_row) من models.costing_base
#      (لو total_qty > 0: price ÷ total_qty | وإلا: price)
```

---

## ملاحظات

- `settings.value` = TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.
- جدول `bom` الأساسي بدون `waste_pct/variant_id/machine_op_row_id/scenario_id` — تُضاف عبر migrations.
- استدعِ `invalidate_bom_cols_cache(conn)` بعد أي migration يُضيف أعمدة لـ bom.
- استدعِ `count_machine_ops()` قبل حذف الماكينة لتحذير المستخدم من CASCADE الصامت [تحسين 19].
- ترتيب إنشاء الجداول: categories أولاً [إصلاح 4].
- `_insert_bom_row` يختار INSERT ديناميكياً — آمن لقواعد البيانات القديمة.
- `insert_op_row/update_op_row/replace_op_rows` تُقيَّد count بـ max(count, 0.0001).