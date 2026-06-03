# دليل الكود — DB: التصميمات (db/designs/)

> جداول `designs.db` — التصميمات، المقاسات، مجموعات الأبعاد، التصنيفات.
> **الملفات الفعلية:** `design_schema.py`, `designs_repo.py`, `designs_sizes_repo.py`, `dimension_sets_repo.py`, `design_categories_repo.py`, `design_item_categories_repo.py`, `dimension_instances_repo.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [design_schema.py](#design_schemapy) | إنشاء جداول designs.db |
| [designs_repo.py](#designs_repopy) | CRUD التصميمات وربطها بالمقاسات |
| [designs_sizes_repo.py](#designs_sizes_repopy) | ربط التصميمات بالمقاسات الفعلية |
| [dimension_sets_repo.py](#dimension_sets_repopy) | مجموعات المقاسات والحقول (Facade) |
| [design_categories_repo.py](#design_categories_repopy) | تصنيفات مجموعات المقاسات |
| [design_item_categories_repo.py](#design_item_categories_repopy) | تصنيفات التصميمات |
| [dimension_instances_repo.py](#dimension_instances_repopy) | Instances وقيمها |

---

## design_schema.py

```python
get_designs_connection() -> sqlite3.Connection
# isolation_level=None, FK=ON, WAL mode

create_designs_tables(conn)
# ينشئ كل الجداول + يُشغّل _run_migrations()

_run_migrations(conn)
# [إصلاح 7 + 12] يضيف dpi_field_id لـ design_sizes لو ناقص
# idempotent — آمن للاستدعاء المتكرر
# لو فشل ALTER → يُسجَّل warning ويكمل بدون crash
```

**هيكل الجداول:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `design_categories` | `id, name, color DEFAULT "#1565c0", parent_id→SET NULL, notes` |
| `design_item_categories` | `id, name, color DEFAULT "#7c3aed", parent_id→SET NULL, notes` |
| `dimension_sets` | `id, name, category_id→SET NULL, default_unit DEFAULT "cm", notes` |
| `dimension_fields` | `id, set_id→CASCADE, name, label, unit DEFAULT "cm", field_type["number"\|"text"], required DEFAULT 1, sort_order` |
| `dimension_field_deps` | `id, field_id UNIQUE→CASCADE, source_field_id→CASCADE, source_set_id→SET NULL, offset DEFAULT 0, notes` |
| `dimension_set_instances` | `id, set_id→CASCADE, name DEFAULT "", sort_order, notes` |
| `dimension_set_values` | `id, set_id, field_id→CASCADE, instance_id→CASCADE, value_num, value_text, UNIQUE(instance_id,field_id)` |
| `designs` | `id, name, category_id→SET NULL, item_category_id→SET NULL, notes, preview_image, created_at, updated_at` |
| `design_sizes` | `id, design_id→CASCADE, set_id→RESTRICT, instance_id→RESTRICT, width_field_id→SET NULL, height_field_id→SET NULL, dpi_field_id→SET NULL, xcf_path, notes, sort_order, UNIQUE(design_id,instance_id)` |
| `design_dimensions` | `id, design_id→CASCADE, set_id→RESTRICT, label, sort_order` |
| `design_dim_values` | `id, link_id→CASCADE, field_id→CASCADE, value_num, value_text, is_auto DEFAULT 0, UNIQUE(link_id,field_id)` |

---

## designs_repo.py

**ملاحظة:** `category_id` في `fetch_all_designs` = `item_category_id` (تصنيف التصميم المستقل، ليس تصنيف مجموعات المقاسات).

```python
fetch_all_designs(conn, category_id=None, set_id=None, name_q="") -> list
fetch_design(conn, design_id) -> row
insert_design(conn, name, item_category_id=None, notes="") -> int
update_design(conn, design_id, name, item_category_id=None, notes="")
# updated_at=datetime('now') تلقائياً
delete_design(conn, design_id)
```

### ربط التصميم بالمقاسات (design_dimensions) — Legacy

```python
fetch_design_links_for_design(conn, design_id) -> list
fetch_link(conn, link_id) -> row
add_design_link(conn, design_id, set_id, label="", sort_order=0) -> int
remove_design_link(conn, link_id)
update_design_link_label(conn, link_id, label)
```

### قيم الحقول (design_dim_values)

```python
fetch_dim_values(conn, link_id) -> dict
# {field_id: {"value_num", "value_text", "is_auto"}}

set_dim_value(conn, link_id, field_id, value_num=None, value_text=None, is_auto=False)
save_all_dim_values(conn, link_id, values: dict, auto_flags: dict = None)
recalc_auto_values(conn, link_id) -> dict[int, float]

fetch_full_design_data(conn, design_id) -> dict
# {id, name, category_name, notes,
#  links: [{link_id, set_name, label, unit, fields: [{id,label,unit,value,is_auto}]}]}
```

---

## designs_sizes_repo.py

```python
fetch_design_sizes(conn, design_id) -> list
# مع set_name, instance_name, width_label, height_label, dpi_label

fetch_design_size(conn, size_id) -> row

insert_design_size(conn, design_id, set_id, instance_id,
                   width_field_id=None, height_field_id=None,
                   xcf_path=None, notes="", sort_order=None,
                   dpi_field_id=None) -> int
# sort_order=None → COUNT(design_id) كـ قيمة تلقائية

update_design_size(conn, size_id, width_field_id=None, height_field_id=None,
                   xcf_path=None, notes="", dpi_field_id=None)

update_design_size_path(conn, size_id, xcf_path)
# تحديث مسار الملف فقط

delete_design_size(conn, size_id)

fetch_canvas_size(conn, size_id) -> tuple[float|None, float|None]
# يرجع (width_val, height_val) من قيم الـ instance

fetch_canvas_dpi(conn, size_id) -> float | None
# يرجع قيمة DPI من حقل الـ instance المحدد

fetch_instances_for_set_with_values(conn, set_id) -> list
# كل instances مجموعة مقاسات للـ combo

instance_already_used(conn, design_id, instance_id, exclude_size_id=None) -> bool

fetch_all_designs_summary(conn) -> list
# كل التصميمات مع sizes_count و files_count (xcf_path IS NOT NULL)
# يستخدم item_category_id بدل category_id
```

---

## dimension_sets_repo.py

> **Facade [تحسين 46]:** يُعيد تصدير الدوال من `design_categories_repo.py` و `dimension_instances_repo.py` للتوافق مع الكود القديم.

> ⚠️ منع Circular Imports:
> - `design_categories_repo` يجب ألّا يستورد من `dimension_sets_repo`
> - `dimension_instances_repo` يجب ألّا يستورد من `dimension_sets_repo`
> - للتحقق: `python -c "import db.designs.dimension_sets_repo"`

### مجموعات المقاسات

```python
fetch_all_dimension_sets(conn) -> list
# مع category_name من LEFT JOIN design_categories ORDER BY ds.name

fetch_dimension_set(conn, set_id) -> row
insert_dimension_set(conn, name, category_id=None, default_unit="cm", notes="") -> int
update_dimension_set(conn, set_id, name, category_id=None, default_unit="cm", notes="")
delete_dimension_set(conn, set_id)
```

### حقول المجموعة

```python
fetch_fields_for_set(conn, set_id) -> list
# مع معلومات الاعتمادية: source_field_id, source_set_id, dep_offset, source_label, source_set_name

fetch_all_fields_for_combo(conn, exclude_field_id=None) -> list
# الحقول الرقمية مجمّعة حسب المجموعة والتصنيف — للـ comboboxes
# WHERE field_type = 'number'

fetch_field(conn, field_id) -> row
insert_field(conn, set_id, name, label, unit="cm", field_type="number",
             required=True, sort_order=0) -> int
update_field(conn, field_id, name, label, unit="cm", field_type="number",
             required=True, sort_order=0)
delete_field(conn, field_id)
reorder_fields(conn, set_id, field_ids: list)
```

### اعتماديات الحقول

```python
fetch_field_dep(conn, field_id) -> row | None
# id, field_id, source_field_id, source_set_id, offset, notes

set_field_dep(conn, field_id, source_field_id, offset=0.0,
              notes="", source_set_id=None)
# DELETE القديم → INSERT الجديد

remove_field_dep(conn, field_id)

calc_auto_value(conn, field_id, link_id) -> float | None
# يحسب القيمة التلقائية في وضع التصميم (design_dim_values)
# يدعم cross-set dependencies عبر source_set_id
```

---

## design_categories_repo.py

تصنيفات مجموعات المقاسات (dimension_sets) — **مختلفة** عن `design_item_categories`.

```python
fetch_all_design_categories(conn) -> list
# مع parent_name من LEFT JOIN ORDER BY parent_id NULLS FIRST, name

fetch_design_category(conn, cat_id) -> row
fetch_category_descendants(conn, cat_id) -> list
# while loop + individual queries (ليس Recursive CTE)

insert_design_category(conn, name, color="#1565c0", parent_id=None, notes="") -> int
update_design_category(conn, cat_id, name, color, parent_id=None, notes="")
delete_design_category(conn, cat_id)
build_category_tree(rows) -> list
# [{id, name, color, parent_id, children: [...]}, ...]
```

---

## design_item_categories_repo.py

تصنيفات التصميمات نفسها (designs) — **مختلفة** عن `design_categories`.

```python
fetch_all_item_categories(conn) -> list
# بدون عدد التصميمات — للتوافق القديم

fetch_all_item_categories_with_count(conn) -> list
# [P-03] يدمج عدد التصميمات في نفس الـ JOIN — query واحدة
# كل صف: id, name, color, parent_id, notes, parent_name, designs_count

fetch_item_category(conn, cat_id) -> row
fetch_item_category_descendants(conn, cat_id) -> list[int]

insert_item_category(conn, name, color="#7c3aed", parent_id=None, notes="") -> int
update_item_category(conn, cat_id, name, color, parent_id=None, notes="")
# يتحقق من circular reference → Raises ValueError
delete_item_category(conn, cat_id)

build_item_category_tree(rows) -> list[dict]
# يعمل مع fetch_all_item_categories و fetch_all_item_categories_with_count

count_designs_per_category(conn) -> dict[int, int]
# للتوافق القديم — الكود الجديد يستخدم fetch_all_item_categories_with_count
```

---

## dimension_instances_repo.py

```python
# CRUD
fetch_instances_for_set(conn, set_id) -> list
fetch_instance(conn, instance_id) -> row
insert_instance(conn, set_id, name="", notes="", sort_order=None) -> int
update_instance(conn, instance_id, name, notes="")
delete_instance(conn, instance_id)
duplicate_instance(conn, instance_id, new_name) -> int | None
# ينسخ instance موجود مع كل قيمه — مفيد لإنشاء مقاس مشابه بسرعة

# قيم Instance
fetch_instance_values(conn, instance_id) -> dict
# {field_id: {"value_num", "value_text"}}
save_instance_values(conn, instance_id, set_id, values: dict)
calc_instance_cross_auto(conn, field_id, instance_id) -> float | None
# يدعم cross-set: source_set_id → يبحث عن أول instance في المجموعة المصدر

# Legacy (للتوافق مع الكود القديم)
fetch_standalone_values(conn, set_id) -> dict
# يرجع قيم أول instance للمجموعة
save_standalone_value(conn, set_id, field_id, value_num=None, value_text=None)
fetch_source_set_values(conn, source_set_id) -> dict
calc_standalone_cross_auto(conn, field_id, current_set_id) -> float | None
get_source_ref(conn, field_id, current_set_id) -> dict | None
```

---

## ملاحظات

- `dpi_field_id` يُضاف تلقائياً عبر `_run_migrations()` على قواعد البيانات القديمة [إصلاح 7 + 12].
- `design_categories` ≠ `design_item_categories`: الأول لتصنيف مجموعات المقاسات، الثاني لتصنيف التصميمات.
- `dimension_sets_repo` هو الـ Facade — استورد منه دائماً للتوافق مع الكود القديم.
- `fetch_all_designs_summary` يستخدم `item_category_id` بدل `category_id` القديم.
- `fetch_all_item_categories_with_count` أفضل من استدعاء `fetch_all_item_categories` + `count_designs_per_category` منفصلَين [P-03].