# دليل الكود — DB (5): التصميمات (designs.db)

> جداول `designs.db` — التصميمات، المقاسات، مجموعات الأبعاد، التصنيفات.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [هيكل الجداول](#هيكل-الجداول) | — |
| [designs_repo](#designs_repo) | `db/designs/designs_repo.py` |
| [designs_sizes_repo](#designs_sizes_repo) | `db/designs/designs_sizes_repo.py` |
| [dimension_sets_repo](#dimension_sets_repo) | `db/designs/dimension_sets_repo.py` (Facade) |
| [design_item_categories_repo](#design_item_categories_repo) | `db/designs/design_item_categories_repo.py` |

---

## هيكل الجداول

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `design_categories` | `id, name, color, parent_id, notes` |
| `design_item_categories` | `id, name, color, parent_id, notes` |
| `dimension_sets` | `id, name, category_id, default_unit, notes` |
| `dimension_fields` | `id, set_id→CASCADE, name, label, unit, field_type["number"\|"text"], required, sort_order` |
| `dimension_field_deps` | `id, field_id UNIQUE, source_field_id, source_set_id, offset, notes` |
| `dimension_set_instances` | `id, set_id→CASCADE, name, sort_order, notes` |
| `dimension_set_values` | `id, set_id, field_id, instance_id→CASCADE, value_num, value_text, UNIQUE(instance_id,field_id)` |
| `designs` | `id, name, category_id, item_category_id, notes, preview_image, created_at, updated_at` |
| `design_sizes` | `id, design_id→CASCADE, set_id, instance_id, width_field_id, height_field_id, dpi_field_id, xcf_path, notes, sort_order, UNIQUE(design_id,instance_id)` |

> **ملاحظة:** `dpi_field_id` يُضاف تلقائياً عبر `_run_migrations()` على قواعد البيانات القديمة [إصلاح 7 + 12].

---

## designs_repo

### `db/designs/designs_repo.py`

```python
fetch_all_designs(conn, category_id=None, set_id=None, name_q="") -> list
# category_id هنا = item_category_id
fetch_design(conn, design_id) -> row
insert_design(conn, name, item_category_id=None, notes="") -> int
update_design(conn, design_id, name, item_category_id=None, notes="")
delete_design(conn, design_id)

fetch_design_links_for_design(conn, design_id) -> list
fetch_dim_values(conn, link_id) -> dict
set_dim_value(conn, link_id, field_id, value_num=None, value_text=None, is_auto=False)
save_all_dim_values(conn, link_id, values: dict, auto_flags: dict = None)
recalc_auto_values(conn, link_id) -> dict[int, float]
fetch_full_design_data(conn, design_id) -> dict
# {id, name, category_name, notes,
#  links: [{link_id, set_name, label, unit, fields: [...]}]}
```

---

## designs_sizes_repo

### `db/designs/designs_sizes_repo.py`

```python
fetch_design_sizes(conn, design_id) -> list
fetch_design_size(conn, size_id) -> row
insert_design_size(conn, design_id, set_id, instance_id,
                   width_field_id=None, height_field_id=None,
                   xcf_path=None, notes="", sort_order=None,
                   dpi_field_id=None) -> int
update_design_size(conn, size_id, width_field_id=None, height_field_id=None,
                   xcf_path=None, notes="", dpi_field_id=None)
update_design_size_path(conn, size_id, xcf_path)
delete_design_size(conn, size_id)

fetch_canvas_size(conn, size_id) -> tuple[float|None, float|None]
fetch_canvas_dpi(conn, size_id) -> float | None
fetch_instances_for_set_with_values(conn, set_id) -> list
instance_already_used(conn, design_id, instance_id, exclude_size_id=None) -> bool
fetch_all_designs_summary(conn) -> list
```

---

## dimension_sets_repo

### `db/designs/dimension_sets_repo.py` — Facade

> **ملاحظة [تحسين 46]:** الملف مقسَّم داخلياً إلى 3 ملفات:
> - `design_categories_repo.py` — تصنيفات مجموعات المقاسات
> - `dimension_sets_repo.py` — هذا الـ Facade + المجموعات + الحقول
> - `dimension_instances_repo.py` — Instances + قيمها

#### مجموعات المقاسات

```python
fetch_all_dimension_sets(conn) -> list
fetch_dimension_set(conn, set_id) -> row
insert_dimension_set(conn, name, category_id=None, default_unit="cm", notes="") -> int
update_dimension_set(conn, set_id, name, category_id=None, default_unit="cm", notes="")
delete_dimension_set(conn, set_id)
```

#### حقول المجموعة

```python
fetch_fields_for_set(conn, set_id) -> list
fetch_all_fields_for_combo(conn, exclude_field_id=None) -> list
fetch_field(conn, field_id) -> row
insert_field(conn, set_id, name, label, unit="cm", field_type="number",
             required=True, sort_order=0) -> int
update_field(conn, field_id, name, label, unit="cm", field_type="number",
             required=True, sort_order=0)
delete_field(conn, field_id)
reorder_fields(conn, set_id, field_ids: list)
```

#### اعتماديات الحقول

```python
fetch_field_dep(conn, field_id) -> row | None
set_field_dep(conn, field_id, source_field_id, offset=0.0,
              notes="", source_set_id=None)
remove_field_dep(conn, field_id)
calc_auto_value(conn, field_id, link_id) -> float | None
```

#### تصنيفات (re-export من design_categories_repo)

```python
fetch_all_design_categories(conn) -> list
insert_design_category(conn, name, color="#1565c0", parent_id=None, notes="") -> int
update_design_category(conn, cat_id, name, color, parent_id=None, notes="")
delete_design_category(conn, cat_id)
build_category_tree(rows) -> list
```

#### Instances (re-export من dimension_instances_repo)

```python
fetch_instances_for_set(conn, set_id) -> list
fetch_instance(conn, instance_id) -> row
insert_instance(conn, set_id, name="", notes="", sort_order=None) -> int
update_instance(conn, instance_id, name, notes="")
delete_instance(conn, instance_id)
duplicate_instance(conn, instance_id, new_name) -> int | None
fetch_instance_values(conn, instance_id) -> dict
save_instance_values(conn, instance_id, set_id, values: dict)
calc_instance_cross_auto(conn, field_id, instance_id) -> float | None
```

#### Legacy (من dimension_instances_repo)

```python
fetch_standalone_values(conn, set_id) -> dict
save_standalone_value(conn, set_id, field_id, value_num=None, value_text=None)
fetch_source_set_values(conn, source_set_id) -> dict
calc_standalone_cross_auto(conn, field_id, current_set_id) -> float | None
get_source_ref(conn, field_id, current_set_id) -> dict | None
```

---

## design_item_categories_repo

### `db/designs/design_item_categories_repo.py`

```python
fetch_all_item_categories(conn) -> list
fetch_all_item_categories_with_count(conn) -> list
# [P-03] query واحدة تدمج عدد التصميمات (بدل query-ين)
fetch_item_category(conn, cat_id) -> row
fetch_item_category_descendants(conn, cat_id) -> list[int]
insert_item_category(conn, name, color="#7c3aed", parent_id=None, notes="") -> int
update_item_category(conn, cat_id, name, color, parent_id=None, notes="")
delete_item_category(conn, cat_id)
build_item_category_tree(rows) -> list[dict]
count_designs_per_category(conn) -> dict[int, int]
# للتوافق مع الكود القديم — الكود الجديد يستخدم fetch_all_item_categories_with_count
```