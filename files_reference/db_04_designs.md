# دليل الكود — DB: التصميمات (db/designs/) — من الكود الفعلي

> يعكس هذا الملف الكود الفعلي في السياق.
> الملفات: `design_schema.py`, `designs_repo.py`, `designs_sizes_repo.py`,
> `dimension_sets_repo.py`, `design_categories_repo.py`,
> `design_item_categories_repo.py`, `dimension_instances_repo.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [design_schema.py](#design_schemapy) | إنشاء جداول designs.db + migration |
| [designs_repo.py](#designs_repopy) | CRUD التصميمات وقيم الأبعاد |
| [designs_sizes_repo.py](#designs_sizes_repopy) | ربط التصميمات بالمقاسات الفعلية |
| [dimension_sets_repo.py](#dimension_sets_repopy) | Facade: مجموعات المقاسات + حقولها |
| [design_categories_repo.py](#design_categories_repopy) | تصنيفات مجموعات المقاسات |
| [design_item_categories_repo.py](#design_item_categories_repopy) | تصنيفات التصميمات + عداد |
| [dimension_instances_repo.py](#dimension_instances_repopy) | Instances وقيمها + Legacy |

---

## design_schema.py

```python
DESIGNS_DB_PATH = os.path.join(_BASE_DIR, "designs.db")

get_designs_connection() -> sqlite3.Connection
# isolation_level=None, row_factory=sqlite3.Row, FK=ON, WAL

create_designs_tables(conn)
# ينشئ كل الجداول + يُشغّل _run_migrations()

_run_migrations(conn)
# [إصلاح 7+12] يضيف dpi_field_id لـ design_sizes لو ناقص
# idempotent — لو العمود موجود → لا شيء
# لو فشل ALTER → logger.warning ويكمل (لا crash)
```

**دوال المساعدة:**
```python
_column_exists(conn, table: str, column: str) -> bool
# PRAGMA table_info(table) → يبحث في name

_table_exists(conn, table: str) -> bool
# SELECT name FROM sqlite_master WHERE type='table' AND name=?
```

**هيكل الجداول الكامل:**

```sql
design_categories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    color     TEXT    NOT NULL DEFAULT '#1565c0',
    parent_id INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
    notes     TEXT
)

design_item_categories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    color     TEXT    NOT NULL DEFAULT '#7c3aed',
    parent_id INTEGER REFERENCES design_item_categories(id) ON DELETE SET NULL,
    notes     TEXT
)

dimension_sets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    category_id  INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
    default_unit TEXT    NOT NULL DEFAULT 'cm',
    notes        TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
)

dimension_fields (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id     INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    label      TEXT    NOT NULL,
    unit       TEXT    NOT NULL DEFAULT 'cm',
    field_type TEXT    NOT NULL DEFAULT 'number'
               CHECK(field_type IN ('number','text')),
    required   INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0
)

dimension_field_deps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
    source_field_id INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
    source_set_id   INTEGER REFERENCES dimension_sets(id) ON DELETE SET NULL,
    offset          REAL    NOT NULL DEFAULT 0,
    notes           TEXT,
    UNIQUE(field_id)    -- حقل واحد = اعتمادية واحدة فقط
)

dimension_set_instances (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id     INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes      TEXT,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
)

dimension_set_values (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id      INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE CASCADE,
    field_id    INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
    instance_id INTEGER REFERENCES dimension_set_instances(id) ON DELETE CASCADE,
    value_num   REAL,
    value_text  TEXT,
    UNIQUE(instance_id, field_id)
)

designs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT    NOT NULL,
    category_id      INTEGER REFERENCES design_categories(id) ON DELETE SET NULL,
    item_category_id INTEGER REFERENCES design_item_categories(id) ON DELETE SET NULL,
    notes            TEXT,
    preview_image    TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
)

design_sizes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    design_id       INTEGER NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
    set_id          INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE RESTRICT,
    instance_id     INTEGER NOT NULL REFERENCES dimension_set_instances(id) ON DELETE RESTRICT,
    width_field_id  INTEGER REFERENCES dimension_fields(id) ON DELETE SET NULL,
    height_field_id INTEGER REFERENCES dimension_fields(id) ON DELETE SET NULL,
    dpi_field_id    INTEGER REFERENCES dimension_fields(id) ON DELETE SET NULL,  -- [إصلاح 7]
    xcf_path        TEXT,
    notes           TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(design_id, instance_id)
)

design_dimensions (                -- Legacy: ربط قديم
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    design_id  INTEGER NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
    set_id     INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE RESTRICT,
    label      TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0
)

design_dim_values (                -- Legacy: قيم الربط القديم
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id    INTEGER NOT NULL REFERENCES design_dimensions(id) ON DELETE CASCADE,
    field_id   INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
    value_num  REAL,
    value_text TEXT,
    is_auto    INTEGER NOT NULL DEFAULT 0,
    UNIQUE(link_id, field_id)
)
```

**التمييز بين نوعَي التصنيفات:**
- `design_categories` → تصنيف مجموعات المقاسات (`dimension_sets`)
- `design_item_categories` → تصنيف التصميمات نفسها (`designs`)

---

## designs_repo.py

**ملاحظة:** في `fetch_all_designs`، `category_id` يُفلتر على `item_category_id` (تصنيف التصميم المستقل).

### CRUD التصميمات

```python
fetch_all_designs(conn, category_id: int = None,
                  set_id: int = None, name_q: str = "") -> list
# category_id هنا = item_category_id
# لو set_id محدد → JOIN design_dimensions WHERE set_id=?
# مع: category_name, category_color من LEFT JOIN design_item_categories
# ORDER BY d.updated_at DESC, d.name

fetch_design(conn, design_id: int) -> row
# مع: category_name, category_color من LEFT JOIN

insert_design(conn, name: str, item_category_id: int = None,
              notes: str = "") -> int

update_design(conn, design_id: int, name: str,
              item_category_id: int = None, notes: str = "")
# updated_at=datetime('now') تلقائياً

delete_design(conn, design_id: int)
# CASCADE على design_sizes + design_dimensions
```

### ربط التصميم بالمقاسات (design_dimensions) — Legacy

```python
fetch_design_links(conn, design_id: int) -> list
# كل الروابط مع set_name, default_unit, category_name

fetch_design_links_for_design(conn, design_id: int) -> list
# WHERE dd.design_id = ? مع set_name, default_unit

fetch_link(conn, link_id: int) -> row

add_design_link(conn, design_id: int, set_id: int,
                label: str = "", sort_order: int = 0) -> int

remove_design_link(conn, link_id: int)

update_design_link_label(conn, link_id: int, label: str)
```

### قيم الحقول (design_dim_values)

```python
fetch_dim_values(conn, link_id: int) -> dict
# {field_id: {"value_num": float|None, "value_text": str|None, "is_auto": int}}

set_dim_value(conn, link_id: int, field_id: int,
              value_num: float = None, value_text: str = None,
              is_auto: bool = False)
# INSERT OR REPLACE ON CONFLICT UPDATE

save_all_dim_values(conn, link_id: int,
                    values: dict[int, float | str],
                    auto_flags: dict[int, bool] = None)
# يُفرّق بين float (value_num) و str (value_text) تلقائياً

recalc_auto_values(conn, link_id: int) -> dict[int, float]
# يُعيد حساب القيم التلقائية للحقول المرتبطة بـ dependencies
# يستدعي calc_auto_value من dimension_sets_repo
# يرجع {field_id: computed_value}

fetch_full_design_data(conn, design_id: int) -> dict
# {id, name, category_name, notes,
#  links: [{link_id, set_name, label, unit,
#            fields: [{id, label, unit, value, is_auto}]}]}
```

---

## designs_sizes_repo.py

### جلب المقاسات

```python
fetch_design_sizes(conn, design_id: int) -> list
# مع: set_name, instance_name, width_label, height_label, dpi_label
# من: JOIN dimension_sets, dimension_set_instances, dimension_fields (×3)
# ORDER BY sort_order, id

fetch_design_size(conn, size_id: int) -> row
# نفس الـ JOINs للصف الواحد
```

### CRUD

```python
insert_design_size(conn, design_id: int, set_id: int, instance_id: int,
                   width_field_id: int = None, height_field_id: int = None,
                   xcf_path: str = None, notes: str = "",
                   sort_order: int = None,
                   dpi_field_id: int = None) -> int
# sort_order=None → COUNT(design_id) تلقائياً

update_design_size(conn, size_id: int,
                   width_field_id: int = None, height_field_id: int = None,
                   xcf_path: str = None, notes: str = "",
                   dpi_field_id: int = None)

update_design_size_path(conn, size_id: int, xcf_path: str)
# تحديث مسار الملف فقط

delete_design_size(conn, size_id: int)
```

### مساعدات القيم والـ Instance

```python
fetch_canvas_size(conn, size_id: int) -> tuple[float | None, float | None]
# يرجع (width_val, height_val) من dimension_set_values
# يقرأ: instance_id + width_field_id/height_field_id من design_sizes
# يبحث في: dimension_set_values WHERE instance_id=? AND field_id=?

fetch_canvas_dpi(conn, size_id: int) -> float | None
# نفس المنطق لحقل DPI
# يرجع None لو dpi_field_id = NULL

fetch_instances_for_set_with_values(conn, set_id: int) -> list
# SELECT id, name, sort_order من dimension_set_instances
# ORDER BY sort_order, id — للـ combo

instance_already_used(conn, design_id: int, instance_id: int,
                       exclude_size_id: int = None) -> bool
# SELECT 1 FROM design_sizes WHERE design_id=? AND instance_id=?

fetch_all_designs_summary(conn) -> list
# كل التصميمات مع:
#   sizes_count = COUNT(ds.id)
#   files_count = SUM(CASE WHEN xcf_path IS NOT NULL AND xcf_path != '' THEN 1)
# يستخدم item_category_id (ليس category_id القديم)
```

---

## dimension_sets_repo.py — Facade [تحسين 46]

> يُعيد تصدير دوال من `design_categories_repo.py` و `dimension_instances_repo.py`.
> **منع Circular Imports:**
> - `design_categories_repo` يجب ألّا يستورد من `dimension_sets_repo`
> - `dimension_instances_repo` يجب ألّا يستورد من `dimension_sets_repo`
> - للتحقق: `python -c "import db.designs.dimension_sets_repo"`

### مجموعات المقاسات

```python
fetch_all_dimension_sets(conn) -> list
# مع category_name من LEFT JOIN design_categories ORDER BY ds.name
# الأعمدة: id, name, category_id, default_unit, notes, category_name

fetch_dimension_set(conn, set_id: int) -> row

insert_dimension_set(conn, name: str, category_id: int = None,
                      default_unit: str = "cm", notes: str = "") -> int

update_dimension_set(conn, set_id: int, name: str,
                      category_id: int = None, default_unit: str = "cm",
                      notes: str = "")

delete_dimension_set(conn, set_id: int)
```

### حقول المجموعة

```python
fetch_fields_for_set(conn, set_id: int) -> list
# مع معلومات dependency: source_field_id, source_set_id,
#   dep_offset, source_label, source_set_name
# ORDER BY sort_order, id

fetch_all_fields_for_combo(conn, exclude_field_id: int = None) -> list
# الحقول الرقمية فقط (field_type='number') مجمّعة للـ comboboxes
# مع: set_name, cat_id, cat_name
# ORDER BY cat_name, set_name, sort_order, id

fetch_field(conn, field_id: int) -> row

insert_field(conn, set_id: int, name: str, label: str,
             unit: str = "cm", field_type: str = "number",
             required: bool = True, sort_order: int = 0) -> int

update_field(conn, field_id: int, name: str, label: str,
             unit: str = "cm", field_type: str = "number",
             required: bool = True, sort_order: int = 0)

delete_field(conn, field_id: int)

reorder_fields(conn, set_id: int, field_ids: list)
# UPDATE dimension_fields SET sort_order=i WHERE id=fid AND set_id=set_id
```

### اعتماديات الحقول (مع دعم cross-set)

```python
fetch_field_dep(conn, field_id: int) -> row | None
# id, field_id, source_field_id, source_set_id, offset, notes

set_field_dep(conn, field_id: int, source_field_id: int,
              offset: float = 0.0, notes: str = "",
              source_set_id: int = None)
# DELETE القديم → INSERT الجديد (UNIQUE على field_id)

remove_field_dep(conn, field_id: int)

calc_auto_value(conn, field_id: int, link_id: int) -> float | None
# يحسب القيمة التلقائية في وضع التصميم (design_dim_values)
# لو source_set_id is None → نفس المجموعة (نفس link_id)
# لو source_set_id محدد → يبحث عن link في نفس design_id لذلك المجموعة
# يرجع: float(source_value) + offset | None لو القيمة غير موجودة
```

---

## design_categories_repo.py

> تصنيفات مجموعات المقاسات (`dimension_sets`) — مختلفة عن `design_item_categories`.

```python
fetch_all_design_categories(conn) -> list
# مع parent_name من LEFT JOIN ORDER BY parent_id NULLS FIRST, name

fetch_design_category(conn, cat_id: int) -> row

fetch_category_descendants(conn, cat_id: int) -> list[int]
# while loop مع individual queries لكل مستوى
# يرجع: [cat_id] + كل IDs الأبناء والأحفاد

insert_design_category(conn, name: str, color: str = "#1565c0",
                         parent_id: int = None, notes: str = "") -> int

update_design_category(conn, cat_id: int, name: str,
                         color: str, parent_id: int = None, notes: str = "")

delete_design_category(conn, cat_id: int)

build_category_tree(rows) -> list[dict]
# [{id, name, color, parent_id, children: [...]}, ...]
```

---

## design_item_categories_repo.py

> تصنيفات التصميمات نفسها (`designs`) — مختلفة عن `design_categories`.
> **[P-03]:** `fetch_all_item_categories_with_count` = query واحدة بدل اثنتين.

```python
fetch_all_item_categories(conn) -> list
# بدون عدد التصميمات — للتوافق القديم

fetch_all_item_categories_with_count(conn) -> list
# [P-03] يدمج designs_count في نفس JOIN
# كل صف: id, name, color, parent_id, notes, parent_name, designs_count
# designs_count = عدد التصميمات المباشرة فقط (غير متداخلة)
#
# مثال الاستخدام (الأفضل):
#   cats = fetch_all_item_categories_with_count(conn)
#   for cat in cats:
#       print(cat["designs_count"])

fetch_item_category(conn, cat_id: int) -> row

fetch_item_category_descendants(conn, cat_id: int) -> list[int]
# while loop — يرجع [cat_id] + كل الأبناء

insert_item_category(conn, name: str, color: str = "#7c3aed",
                      parent_id: int = None, notes: str = "") -> int

update_item_category(conn, cat_id: int, name: str,
                      color: str, parent_id: int = None, notes: str = "")
# يتحقق من circular reference → Raises ValueError

delete_item_category(conn, cat_id: int)

build_item_category_tree(rows) -> list[dict]
# يعمل مع كلا الدالتَين (مع/بدون designs_count)
# {id, name, color, parent_id, designs_count (0 إذا غير موجود), children: []}

count_designs_per_category(conn) -> dict[int, int]
# للتوافق القديم → {category_id: count}
# الكود الجديد يستخدم fetch_all_item_categories_with_count
```

---

## dimension_instances_repo.py

### CRUD — Instances

```python
fetch_instances_for_set(conn, set_id: int) -> list
# ORDER BY sort_order, id
# الأعمدة: id, set_id, name, sort_order, notes, created_at

fetch_instance(conn, instance_id: int) -> row

insert_instance(conn, set_id: int, name: str = "",
                notes: str = "", sort_order: int = None) -> int
# sort_order=None → COUNT(set_id) تلقائياً

update_instance(conn, instance_id: int, name: str, notes: str = "")

delete_instance(conn, instance_id: int)

duplicate_instance(conn, instance_id: int, new_name: str) -> int | None
# ينسخ instance مع كل قيمه (dimension_set_values)
# مفيد لإنشاء مقاس مشابه بسرعة
# يرجع None لو source غير موجود
```

### قيم Instance

```python
fetch_instance_values(conn, instance_id: int) -> dict
# {field_id: {"value_num": float|None, "value_text": str}}

save_instance_values(conn, instance_id: int, set_id: int,
                      values: dict) -> None
# values: {field_id: float | None}
# INSERT OR REPLACE ON CONFLICT UPDATE value_num

calc_instance_cross_auto(conn, field_id: int,
                          instance_id: int) -> float | None
# يحسب القيمة التلقائية بدعم cross-set:
# لو source_set_id is None → نفس instance → يبحث في dimension_set_values
# لو source_set_id محدد → أول instance في المجموعة المصدر
# يرجع: float(source_value) + offset | None لو غير موجودة
```

### Legacy — للتوافق مع الكود القديم

```python
fetch_standalone_values(conn, set_id: int) -> dict
# يرجع قيم أول instance للمجموعة (Legacy)

save_standalone_value(conn, set_id: int, field_id: int,
                       value_num: float = None, value_text: str = None)
# يحفظ في أول instance — ينشئ instance تلقائياً لو مفيش

fetch_source_set_values(conn, source_set_id: int) -> dict
# {field_id: {"value_num", "value_text", "label", "unit"}}
# يجلب من أول instance للمجموعة المصدر

calc_standalone_cross_auto(conn, field_id: int,
                            current_set_id: int) -> float | None
# يستخدم أول instance للمجموعة الحالية

get_source_ref(conn, field_id: int, current_set_id: int) -> dict | None
# بيانات المصدر لعرض reference label في الـ UI
# {source_val, result, set_name, offset} أو None
```

---

## ملاحظات مهمة

- `dpi_field_id` يُضاف تلقائياً على قواعد البيانات القديمة عبر `_run_migrations()` [إصلاح 7+12].
- `design_categories` ≠ `design_item_categories` — تمييز أساسي في النظام.
- `dimension_sets_repo` هو الـ Facade — استورد منه للتوافق مع الكود القديم.
- `fetch_all_designs_summary` يستخدم `item_category_id` (ليس `category_id`).
- `fetch_all_item_categories_with_count` أفضل من استدعاء دالتَين منفصلتَين [P-03].
- `calc_auto_value` و `calc_instance_cross_auto` منفصلتان: الأولى لـ design_dim_values (Legacy)، الثانية لـ dimension_set_values (الجديد).