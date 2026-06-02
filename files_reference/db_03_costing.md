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
#   [إصلاح 5] لا يُغيّر نوع عمود settings.value مباشرة
#             (SQLite يدعم type affinity — TEXT يقبل كل القيم)

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
| `bom_scenarios` | `id, item_id→CASCADE, name, is_default, notes, created_at` |
| `machine_op_rows` | `id, op_id→machine_ops, label, value, count CHECK(>0), sort_order` |
| `raw_variants` | `id, item_id→items CASCADE, name, pieces REAL NOT NULL CHECK(>0), notes` |

> ⚠️ **ترتيب الإنشاء مهم [إصلاح 4]:** `categories` يُنشأ أولاً لأن بقية الجداول تحتوي `REFERENCES categories(id)`.
> ⚠️ جدول `bom` الأساسي لا يحتوي `waste_pct`, `variant_id`, `machine_op_row_id`, `scenario_id` — تُضاف عبر migrations. استخدم `_get_bom_cols(conn)` للتحقق.

---

## bom_scenarios_repo.py

#### BOM columns cache — [إصلاح 8] موحد مع items_repo

```python
_bom_cols_cache: dict[str, set] = {}
# key: db_path (من PRAGMA database_list أو str(id(conn)) كـ fallback)

_get_bom_cols(conn) -> set
# يجلب أعمدة جدول bom مع cache بمفتاح db_path:
#   1. يحاول PRAGMA database_list للحصول على db_path
#   2. لو path موجود في cache → يرجعه مباشرة
#   3. وإلا → PRAGMA table_info(bom) + يُخزّن في cache

invalidate_bom_cols_cache(conn=None)
# استدعه بعد أي migration يضيف أعمدة لجدول bom
# conn=None → يمسح _bom_cols_cache.clear() كاملاً
# conn=<connection> → يمسح cache هذا الملف فقط (_bom_cols_cache.pop(path, None))

_col_exists(conn, table, col) -> bool
# لو table == "bom" → يستخدم _get_bom_cols() المُخزَّن في cache
# غيره → PRAGMA table_info(table) مباشرة

_resolve_name(conn, child_type, child_id) -> str | None
# يجلب اسم العنصر حسب النوع:
#   "raw" | "semi" → SELECT name FROM items WHERE id=?
#   "labor_op"     → SELECT name FROM labor_ops WHERE id=?
#   "machine_op"   → SELECT name FROM machine_ops WHERE id=?
```

#### السيناريوهات

```python
fetch_scenarios(conn, item_id) -> list
# SELECT id, item_id, name, is_default, notes, created_at
# ORDER BY id

fetch_scenario(conn, scenario_id) -> row
fetch_default_scenario(conn, item_id) -> row | None
# يرجع السيناريو بـ is_default=1 أولاً
# لو مفيش → يرجع أول سيناريو ORDER BY id LIMIT 1

insert_scenario(conn, item_id, name, is_default=False, notes="") -> int
# لو is_default=True → UPDATE bom_scenarios SET is_default=0 WHERE item_id=? أولاً
# ثم INSERT جديد

update_scenario(conn, scenario_id, name, notes="")
set_default_scenario(conn, scenario_id)
# يُعيد ضبط is_default=0 على كل سيناريوهات item_id
# ثم يضبط is_default=1 على السيناريو المحدد

delete_scenario(conn, scenario_id) -> bool
# يرفض (يرجع False) لو آخر سيناريو للمنتج
# يحذف بنود BOM أولاً: DELETE FROM bom WHERE scenario_id=?
# ثم يحذف السيناريو نفسه
# لو كان is_default=True → يُعيّن أول سيناريو متبقٍ كـ default

clone_scenario(conn, scenario_id, new_name) -> int
# يجلب السيناريو + بنوده
# ينشئ سيناريو جديد (is_default=False)
# ينسخ كل بنود BOM بـ _insert_bom_row
# يستخدم r.keys() لاكتشاف variant_id و machine_op_row_id بأمان
```

#### BOM للسيناريو

```python
fetch_bom_for_scenario(conn, scenario_id) -> list
# يستخدم _get_bom_cols() مع cache — يتعامل مع وجود/غياب الأعمدة:
#
#   has_row_id + has_variant:
#     SELECT child_type, child_id, qty, COALESCE(waste_pct,0),
#            variant_id, machine_op_row_id
#     WHERE scenario_id=?
#
#   has_row_id فقط:
#     NULL as variant_id, machine_op_row_id
#
#   has_variant فقط:
#     variant_id, NULL as machine_op_row_id
#
#   لا شيء:
#     NULL as variant_id, NULL as machine_op_row_id

replace_bom_for_scenario(conn, scenario_id, rows)
# rows: [(child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id), ...]
# يحذف القديم: DELETE FROM bom WHERE scenario_id=?
# ينشئ الجديد بـ _insert_bom_row لكل صف
# waste_pct: float(row[3]) لو len(row) > 3 وإلا 0.0
# variant_id: row[4] لو len(row) > 4 وإلا None
# machine_op_row_id: row[5] لو len(row) > 5 وإلا None
```

**`_insert_bom_row(conn, parent_id, child_type, child_id, qty, child_name,
                   waste_pct, variant_id, machine_op_row_id, scenario_id)`:**
```python
# INSERT آمن في جدول bom — يتعامل مع وجود/غياب الأعمدة
# يستخدم _get_bom_cols() مع cache [إصلاح 8]
# لو child_name=None → يستدعي _resolve_name()
#
# يختار الـ INSERT المناسب حسب الأعمدة الموجودة:
#   has_variant + has_row_id + has_scenario → INSERT كامل (9 أعمدة)
#   has_row_id + has_scenario              → بدون variant_id
#   has_variant + has_scenario             → بدون machine_op_row_id
#   has_row_id فقط                         → بدون scenario_id و variant_id
#   has_scenario فقط                       → بدون machine_op_row_id و variant_id
#   لا شيء                                 → INSERT بسيط (6 أعمدة)
```

---

## machine_op_rows_repo.py

كل عملية تشغيل (machine_op) ممكن يكون ليها أكثر من صف.

**صيغة التكلفة:**
```
تكلفة الصف = (value × rate_per_hour ÷ 60) ÷ count   [لو mode=time]
           = (value × rate_per_unit)         ÷ count   [لو mode=unit]
```

```python
fetch_op_rows(conn, op_id) -> list
# SELECT id, op_id, label, value, count, sort_order
# ORDER BY sort_order, id

fetch_op_row(conn, row_id) -> row

insert_op_row(conn, op_id, label="", value=0.0, count=1.0, sort_order=0) -> int
# count يُقيَّد بـ max(count, 0.0001) لمنع القسمة على صفر

update_op_row(conn, row_id, label, value, count, sort_order=0)
# نفس قيد count: max(count, 0.0001)

delete_op_row(conn, row_id)

replace_op_rows(conn, op_id, rows: list[tuple])
# rows: [(label, value, count), ...]
# يحذف القديم: DELETE FROM machine_op_rows WHERE op_id=?
# ينشئ الجديد بـ enumerate لـ sort_order
# كل count يُقيَّد بـ max(count, 0.0001)

calc_op_row_cost(conn, row_id) -> float
# يجلب الصف + بيانات الماكينة عبر:
#   SELECT mo.mode, m.rate_per_hour, m.rate_per_unit
#   FROM machine_ops mo JOIN machines m ON m.id = mo.machine_id
#   WHERE mo.id = row["op_id"]
# mode="time":  (value/60.0) × rate_per_hour / count
# mode="unit":  (value × rate_per_unit) / count
# يرجع 0.0 لو الصف أو بيانات الماكينة غير موجودة

calc_op_total_cost(conn, op_id) -> float
# مجموع calc_op_row_cost لكل الصفوف
# يرجع 0.0 لو لا يوجد صفوف
```

---

## operations_repo.py

#### الماكينات

```python
fetch_all_machines(conn) -> list
# مع category_id و category_name من LEFT JOIN categories
# ORDER BY m.name

fetch_machine(conn, machine_id) -> row
# نفس الأعمدة مع category_name

insert_machine(conn, name, rate_per_hour, rate_per_unit, category_id=None) -> int
update_machine(conn, machine_id, name, rate_per_hour, rate_per_unit, category_id=None)

count_machine_ops(conn, machine_id) -> int
# [تحسين 19] للتحقق قبل الحذف
# SELECT COUNT(*) AS c FROM machine_ops WHERE machine_id=?
# يرجع row["c"] أو 0
#
# استخدمه في الـ UI:
#   ops_count = count_machine_ops(conn, machine_id)
#   if ops_count > 0:
#       → أظهر تأكيداً يُخبر المستخدم بعدد العمليات المتأثرة
#
# السبب: schema يحتوي CASCADE DELETE صامت على machine_ops
#   machine_ops.machine_id → REFERENCES machines(id) ON DELETE CASCADE
#   → حذف الماكينة يحذف كل عمليات تشغيلها بصمت

delete_machine(conn, machine_id)
# CASCADE على machine_ops — استدعِ count_machine_ops() أولاً في الـ UI
```

#### عمليات العمالة

```python
fetch_all_labor_ops(conn) -> list
# مع category_name من LEFT JOIN categories
# ORDER BY lo.name

fetch_labor_op(conn, op_id) -> row

insert_labor_op(conn, name, minutes, category_id=None) -> int
update_labor_op(conn, op_id, name, minutes, category_id=None)
delete_labor_op(conn, op_id)
```

#### عمليات التشغيل

```python
fetch_all_machine_ops(conn) -> list
# مع machine_name, rate_per_hour, rate_per_unit من JOIN machines
# مع category_name من LEFT JOIN categories
# ORDER BY mo.name

fetch_machine_op(conn, op_id) -> row

insert_machine_op(conn, machine_id, name, mode, value, category_id=None) -> int
# mode: "time" | "unit"

update_machine_op(conn, op_id, machine_id, name, mode, value, category_id=None)
delete_machine_op(conn, op_id)
```

---

## raw_variants_repo.py

كل خامة ممكن يكون ليها variants — كل variant بيعبر عن عدد القطع اللي بتنتجها من الخامة.

**مثال:**
```
خامة "قماش" سعرها 100 جنيه:
  variant "قميص كبير"  → pieces = 2  → تكلفة الوحدة = 100 ÷ 2 = 50 ج
  variant "قميص صغير" → pieces = 3  → تكلفة الوحدة = 100 ÷ 3 = 33.33 ج
```

```python
fetch_variants_for_item(conn, item_id) -> list
# SELECT id, item_id, name, pieces, notes
# ORDER BY name

fetch_variant(conn, variant_id) -> row
# SELECT id, item_id, name, pieces, notes

insert_variant(conn, item_id, name, pieces, notes=None) -> int
# pieces: REAL CHECK(pieces > 0) على مستوى الـ schema

update_variant(conn, variant_id, name, pieces, notes=None)
delete_variant(conn, variant_id)

calc_unit_cost_with_variant(item_row, variant_id, conn) -> float
# الأولوية:
#   1. variant_id is not None:
#      var = fetch_variant(conn, variant_id)
#      لو var و float(var["pieces"]) > 0 → price / float(var["pieces"])
#   2. fallback للسلوك الحالي:
#      raw_unit_price(item_row)  ← يتعامل مع total_qty
#
# raw_unit_price منطقها:
#   لو total_qty > 0 → price ÷ total_qty
#   وإلا → price مباشرة
```

---

## ملاحظات

- `settings.value` عمود TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.
- القيم الافتراضية في `settings` تُدرج بـ `INSERT OR IGNORE` — لا تُعيد كتابة قيم موجودة.
- استدعِ `invalidate_bom_cols_cache(conn)` بعد أي migration يضيف أعمدة لجدول bom.
- استدعِ `count_machine_ops()` قبل حذف الماكينة لتحذير المستخدم من CASCADE الصامت.
- `_insert_bom_row` يختار الـ INSERT المناسب ديناميكياً حسب أعمدة bom — آمن لقواعد البيانات القديمة.
- `insert_op_row` و `update_op_row` و `replace_op_rows` تُقيّد count بـ max(count, 0.0001) لمنع القسمة على صفر.
- ترتيب الإنشاء في schema.py: categories أولاً [إصلاح 4]، ثم بقية الجداول.