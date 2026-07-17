# دليل الكود — DB: التصميمات (db/designs/) — نسخة محدَّثة

> يعكس هذا الملف الكود الفعلي الموجود في السياق.
> **الملفات:** `design_schema.py`, `designs_repo.py`, `designs_sizes_repo.py`,
> `dimension_sets_repo.py`, `design_categories_repo.py`,
> `design_item_categories_repo.py`, `dimension_instances_repo.py`
> **آخر تحديث:** يعكس الكود الفعلي في السياق.

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [design_schema.py](#design_schemapy) | إنشاء جداول designs.db + migration |
| [designs_repo.py](#designs_repopy) | CRUD التصميمات وقيم الأبعاد |
| [designs_sizes_repo.py](#designs_sizes_repopy) | ربط التصميمات بالمقاسات الفعلية |
| [dimension_sets_repo.py](#dimension_sets_repopy) | Facade: مجموعات المقاسات + حقولها + اعتماديات |
| [design_categories_repo.py](#design_categories_repopy) | تصنيفات مجموعات المقاسات |
| [design_item_categories_repo.py](#design_item_categories_repopy) | تصنيفات التصميمات + عداد [P-03] |
| [dimension_instances_repo.py](#dimension_instances_repopy) | Instances وقيمها + Legacy |

---

## التمييز الأساسي بين نوعَي التصنيفات

| الجدول | يُصنِّف | يُستخدم في |
|--------|---------|-----------|
| `design_categories` | مجموعات المقاسات (`dimension_sets`) | اختيار التصنيف عند إنشاء dimension_set |
| `design_item_categories` | التصميمات نفسها (`designs`) | عرض وفلترة التصميمات في الـ UI |

---

## design_schema.py

```python
DESIGNS_DB_PATH = os.path.join(_BASE_DIR, "designs.db")

get_designs_connection() -> sqlite3.Connection
# isolation_level=None, row_factory=sqlite3.Row, FK=ON, WAL

create_designs_tables(conn)
# ينشئ كل الجداول ثم يستدعي _run_migrations()

_run_migrations(conn)
# [إصلاح 7+12] يضيف dpi_field_id لـ design_sizes لو ناقص
# idempotent: لو العمود موجود → لا شيء يحدث
# لو فشل ALTER → logger.warning ويكمل (لا crash)
```

**دوال المساعدة:**
```python
_column_exists(conn, table: str, column: str) -> bool
# PRAGMA table_info(table) → يبحث في r["name"]

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
    UNIQUE(field_id)   -- حقل واحد = اعتمادية واحدة فقط
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

-- Legacy: ربط قديم بين التصميمات والمجموعات
design_dimensions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    design_id  INTEGER NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
    set_id     INTEGER NOT NULL REFERENCES dimension_sets(id) ON DELETE RESTRICT,
    label      TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0
)

-- Legacy: قيم حقول الربط القديم
design_dim_values (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id    INTEGER NOT NULL REFERENCES design_dimensions(id) ON DELETE CASCADE,
    field_id   INTEGER NOT NULL REFERENCES dimension_fields(id) ON DELETE CASCADE,
    value_num  REAL,
    value_text TEXT,
    is_auto    INTEGER NOT NULL DEFAULT 0,
    UNIQUE(link_id, field_id)
)
```

---

## designs_repo.py

**ملاحظة:** في `fetch_all_designs`، `category_id` يُفلتر على `item_category_id` (تصنيف التصميم المستقل) وليس `category_id` (تصنيف مجموعة المقاسات).

### CRUD التصميمات

```python
fetch_all_designs(conn, category_id: int = None,
                  set_id: int = None,
                  name_q: str = '') -> list
# category_id هنا = item_category_id (تصنيف التصميم)
# لو set_id محدد → JOIN design_dimensions WHERE set_id=?
# مع: category_name, category_color من LEFT JOIN design_item_categories
# ORDER BY d.updated_at DESC, d.name

fetch_design(conn, design_id: int) -> row
# مع category_name, category_color من LEFT JOIN design_item_categories

insert_design(conn, name: str,
              item_category_id: int = None,
              notes: str = '') -> int

update_design(conn, design_id: int, name: str,
              item_category_id: int = None,
              notes: str = '')
# updated_at=datetime('now') تلقائياً

delete_design(conn, design_id: int)
# CASCADE على: design_sizes, design_dimensions (وقيمهما)
```

### ربط التصميم بالمقاسات — Legacy (design_dimensions)

```python
fetch_design_links(conn, design_id: int) -> list
# كل الروابط للتصميم مع set_name, default_unit, category_name

fetch_design_links_for_design(conn, design_id: int) -> list
# WHERE dd.design_id=? مع set_name, default_unit

fetch_link(conn, link_id: int) -> row
# id, design_id, set_id, label, sort_order

add_design_link(conn, design_id: int, set_id: int,
                label: str = '', sort_order: int = 0) -> int

remove_design_link(conn, link_id: int)

update_design_link_label(conn, link_id: int, label: str)
```

### قيم الحقول (design_dim_values) — Legacy

```python
fetch_dim_values(conn, link_id: int) -> dict
# {field_id: {"value_num": float|None, "value_text": str|None, "is_auto": int}}

set_dim_value(conn, link_id: int, field_id: int,
              value_num: float = None, value_text: str = None,
              is_auto: bool = False)
# INSERT OR REPLACE ... ON CONFLICT DO UPDATE

save_all_dim_values(conn, link_id: int,
                    values: dict[int, float | str],
                    auto_flags: dict[int, bool] = None)
# يُفرّق بين float (value_num) و str (value_text) تلقائياً

recalc_auto_values(conn, link_id: int) -> dict[int, float]
# يعيد حساب القيم التلقائية للحقول بـ dependencies
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
# مع: set_name (dimension_sets), instance_name (dimension_set_instances)
#     width_label, height_label, dpi_label (dimension_fields × 3)
# ORDER BY sort_order, id

fetch_design_size(conn, size_id: int) -> row
# نفس الـ JOINs للصف الواحد
```

### CRUD

```python
insert_design_size(conn, design_id: int, set_id: int, instance_id: int,
                   width_field_id: int = None,
                   height_field_id: int = None,
                   xcf_path: str = None,
                   notes: str = '',
                   sort_order: int = None,
                   dpi_field_id: int = None) -> int
# sort_order=None → COUNT(design_id) تلقائياً
# UNIQUE(design_id, instance_id) — لا يمكن إضافة نفس instance مرتين لنفس التصميم

update_design_size(conn, size_id: int,
                   width_field_id: int = None,
                   height_field_id: int = None,
                   xcf_path: str = None,
                   notes: str = '',
                   dpi_field_id: int = None)

update_design_size_path(conn, size_id: int, xcf_path: str)
# تحديث مسار ملف XCF فقط

delete_design_size(conn, size_id: int)
```

### مساعدات القيم والـ Instance

```python
fetch_canvas_size(conn, size_id: int) -> tuple[float | None, float | None]
# يرجع (width_val, height_val) من dimension_set_values
# المسار: design_sizes → instance_id + width/height_field_id
#          → dimension_set_values WHERE instance_id=? AND field_id=?
# يرجع (None, None) لو الحقول غير محددة أو القيم ناقصة

fetch_canvas_dpi(conn, size_id: int) -> float | None
# نفس المنطق لحقل DPI
# يرجع None لو dpi_field_id = NULL أو القيمة غير موجودة

fetch_instances_for_set_with_values(conn, set_id: int) -> list
# SELECT id, name, sort_order FROM dimension_set_instances
# WHERE set_id=? ORDER BY sort_order, id
# للـ combo — بدون قيم الحقول (الاسم فقط)

instance_already_used(conn, design_id: int, instance_id: int,
                       exclude_size_id: int = None) -> bool
# هل هذا الـ instance مضاف مسبقاً لهذا التصميم؟
# مع استثناء size_id محدد (للتحقق عند التعديل)
```

### ملخص كل التصميمات

```python
fetch_all_designs_summary(conn) -> list
# ⚠️ هذه الدالة موجودة في designs_sizes_repo.py (ليس designs_repo.py)
# كل التصميمات مع:
#   category_name من LEFT JOIN design_item_categories (يستخدم item_category_id)
#   sizes_count = COUNT(design_sizes.id)
#   files_count = COUNT WHEN xcf_path IS NOT NULL AND != ''
# الأعمدة: id, name, notes, created_at, updated_at,
#           category_name, sizes_count, files_count
# ORDER BY d.updated_at DESC, d.name
```

---

## dimension_sets_repo.py — Facade [تحسين 46]

يُعيد تصدير دوال من `design_categories_repo.py` و `dimension_instances_repo.py`.

**قاعدة منع Circular Imports:**
```
dimension_sets_repo  ←  design_categories_repo   (آمن ✓)
dimension_sets_repo  ←  dimension_instances_repo  (آمن ✓)
design_categories_repo   ← يجب ألّا يستورد من dimension_sets_repo
dimension_instances_repo ← يجب ألّا يستورد من dimension_sets_repo
```

**للتحقق الدوري:**
```bash
python -c "import db.designs.dimension_sets_repo"
```

### مجموعات المقاسات (dimension_sets)

```python
fetch_all_dimension_sets(conn) -> list
# مع category_name من LEFT JOIN design_categories | ORDER BY ds.name
# الأعمدة: id, name, category_id, default_unit, notes, category_name

fetch_dimension_set(conn, set_id: int) -> row

insert_dimension_set(conn, name: str,
                      category_id: int = None,
                      default_unit: str = 'cm',
                      notes: str = '') -> int

update_dimension_set(conn, set_id: int, name: str,
                      category_id: int = None,
                      default_unit: str = 'cm',
                      notes: str = '')

delete_dimension_set(conn, set_id: int)
# RESTRICT على design_sizes — يرفض الحذف لو مربوط بمقاسات
```

### حقول المجموعة (dimension_fields)

```python
fetch_fields_for_set(conn, set_id: int) -> list
# كل حقول المجموعة مع معلومات الاعتمادية (dimension_field_deps)
# مع: source_label (label الحقل المصدر), source_set_name
# ORDER BY sort_order, id

fetch_all_fields_for_combo(conn, exclude_field_id: int = None) -> list
# الحقول الرقمية فقط (field_type='number') مجمّعة للـ comboboxes
# مع: field_label, set_id, set_name, cat_id, cat_name
# ORDER BY cat_name, set_name, sort_order, id

fetch_field(conn, field_id: int) -> row
# id, set_id, name, label, unit, field_type, required, sort_order

insert_field(conn, set_id: int, name: str, label: str,
             unit: str = 'cm',
             field_type: str = 'number',
             required: bool = True,
             sort_order: int = 0) -> int

update_field(conn, field_id: int, name: str, label: str,
             unit: str = 'cm',
             field_type: str = 'number',
             required: bool = True,
             sort_order: int = 0)

delete_field(conn, field_id: int)
# CASCADE على dimension_set_values و dimension_field_deps

reorder_fields(conn, set_id: int, field_ids: list)
# يُعيد ترتيب الحقول: UPDATE SET sort_order=i WHERE id=fid AND set_id=set_id
```

### اعتماديات الحقول (dimension_field_deps) — دعم cross-set

```python
fetch_field_dep(conn, field_id: int) -> row | None
# id, field_id, source_field_id, source_set_id, offset, notes
# UNIQUE(field_id) → حقل واحد = اعتمادية واحدة فقط

set_field_dep(conn, field_id: int, source_field_id: int,
              offset: float = 0.0, notes: str = '',
              source_set_id: int = None)
# DELETE القديم ثم INSERT الجديد

remove_field_dep(conn, field_id: int)
# DELETE FROM dimension_field_deps WHERE field_id=?

calc_auto_value(conn, field_id: int, link_id: int) -> float | None
# يحسب القيمة التلقائية في وضع design_dim_values (Legacy)
# لو source_set_id is None → نفس link_id
# لو source_set_id محدد (cross-set) → يبحث عن link في نفس design_id للمجموعة المصدر
# يرجع: float(source_value) + offset | None لو غير موجودة
```

---

## design_categories_repo.py

> تصنيفات مجموعات المقاسات (`dimension_sets`).

```python
fetch_all_design_categories(conn) -> list
# مع parent_name من LEFT JOIN | ORDER BY parent_id NULLS FIRST, name

fetch_design_category(conn, cat_id: int) -> row

fetch_category_descendants(conn, cat_id: int) -> list[int]
# while loop + individual queries لكل مستوى
# يرجع: [cat_id] + كل IDs الأبناء والأحفاد

insert_design_category(conn, name: str, color: str = '#1565c0',
                         parent_id: int = None, notes: str = '') -> int

update_design_category(conn, cat_id: int, name: str,
                         color: str, parent_id: int = None,
                         notes: str = '')

delete_design_category(conn, cat_id: int)

build_category_tree(rows) -> list[dict]
# [{id, name, color, parent_id, children: [...]}, ...]
```

---

## design_item_categories_repo.py

> تصنيفات التصميمات نفسها (`designs`).
> **[P-03]:** `fetch_all_item_categories_with_count` = query واحدة بدل اثنتين.

```python
fetch_all_item_categories(conn) -> list
# بدون عدد التصميمات — للتوافق القديم
# الأعمدة: id, name, color, parent_id, notes, parent_name

fetch_all_item_categories_with_count(conn) -> list
# [P-03] يدمج designs_count في نفس JOIN — query واحدة
# الأعمدة: id, name, color, parent_id, notes, parent_name, designs_count
# designs_count = عدد التصميمات المباشرة فقط (غير متداخلة)

fetch_item_category(conn, cat_id: int) -> row

fetch_item_category_descendants(conn, cat_id: int) -> list[int]
# while loop — يرجع [cat_id] + كل الأبناء والأحفاد

insert_item_category(conn, name: str, color: str = '#7c3aed',
                      parent_id: int = None, notes: str = '') -> int

update_item_category(conn, cat_id: int, name: str, color: str,
                      parent_id: int = None, notes: str = '')
# يتحقق من circular reference → Raises ValueError لو parent في الأبناء

delete_item_category(conn, cat_id: int)

build_item_category_tree(rows) -> list[dict]
# يعمل مع fetch_all_item_categories و fetch_all_item_categories_with_count
# {id, name, color, parent_id, designs_count (0 إذا غير موجود), children: []}

count_designs_per_category(conn) -> dict[int, int]
# للتوافق القديم → {category_id: count}
# الكود الجديد يستخدم fetch_all_item_categories_with_count
```

---

## dimension_instances_repo.py

### CRUD — Instances (dimension_set_instances)

```python
fetch_instances_for_set(conn, set_id: int) -> list
# id, set_id, name, sort_order, notes, created_at
# ORDER BY sort_order, id

fetch_instance(conn, instance_id: int) -> row

insert_instance(conn, set_id: int, name: str = '',
                notes: str = '', sort_order: int = None) -> int
# sort_order=None → COUNT(set_id) تلقائياً

update_instance(conn, instance_id: int, name: str, notes: str = '')

delete_instance(conn, instance_id: int)
# CASCADE على dimension_set_values

duplicate_instance(conn, instance_id: int, new_name: str) -> int | None
# ينسخ instance مع كل قيمه من dimension_set_values
# يرجع new_id | None لو source غير موجود
```

### قيم Instance (dimension_set_values)

```python
fetch_instance_values(conn, instance_id: int) -> dict
# {field_id: {"value_num": float|None, "value_text": str}}

save_instance_values(conn, instance_id: int, set_id: int,
                      values: dict) -> None
# values: {field_id: float | None}
# INSERT ... ON CONFLICT(instance_id, field_id) DO UPDATE SET value_num

calc_instance_cross_auto(conn, field_id: int,
                          instance_id: int) -> float | None
# يحسب القيمة التلقائية بدعم cross-set:
#   source_set_id is None → نفس instance_id
#   source_set_id محدد → أول instance في المجموعة المصدر (ORDER BY sort_order, id)
# يرجع: float(source_value) + offset | None
```

### Legacy — للتوافق مع الكود القديم

```python
fetch_standalone_values(conn, set_id: int) -> dict
# يرجع قيم أول instance للمجموعة (Legacy API)

save_standalone_value(conn, set_id: int, field_id: int,
                       value_num: float = None, value_text: str = None)
# ينشئ instance تلقائياً لو مفيش

fetch_source_set_values(conn, source_set_id: int) -> dict
# {field_id: {"value_num", "value_text", "label", "unit"}}
# من أول instance للمجموعة المصدر

calc_standalone_cross_auto(conn, field_id: int,
                            current_set_id: int) -> float | None
# يستخدم أول instance للمجموعة الحالية

get_source_ref(conn, field_id: int, current_set_id: int) -> dict | None
# {source_val, result, set_name, offset} لعرض reference label في الـ UI
# يرجع None لو لا توجد اعتمادية أو القيمة المصدر غير موجودة
```

---

## ملاحظات مهمة

- `dpi_field_id` يُضاف تلقائياً على قواعد البيانات القديمة عبر `_run_migrations()` [إصلاح 7+12].
- **`fetch_all_designs_summary` موجودة في `designs_sizes_repo.py`** (وليس `designs_repo.py`) — تستخدم `item_category_id` وليس `category_id`.
- `fetch_all_item_categories_with_count` أفضل أداءً من استدعاء دالتَين منفصلتَين [P-03].
- `dimension_sets_repo` هو الـ Facade — استورد منه للتوافق مع الكود القديم.
- `calc_auto_value` (من dimension_sets_repo) ← لـ `design_dim_values` (Legacy).
- `calc_instance_cross_auto` (من dimension_instances_repo) ← لـ `dimension_set_values` (الجديد).
- `design_categories` ≠ `design_item_categories` — تمييز أساسي لا يجب الخلط بينهما.
- `dimension_sets_repo` يُعيد تصدير دوال الـ Categories والـ Instances للتوافق القديم.
---

## من يستخدم هذا المسار (db/designs/) من خارجه

- `services/design/design_service.py` — المستهلك الرئيسي لـ `designs_repo.py`
- `services/design/design_size_service.py` — يستورد `designs_repo.py` و `dimension_sets_repo.py`
- `services/design/dimension_set_service.py` — يستورد `dimension_sets_repo.py` و `dimension_instances_repo.py` و `design_categories_repo.py`
- `services/design/__init__.py` — factory functions تستخدم الثلاثة services أعلاه
- `services/orders/order_catalog_service.py` — يذكر نمط `get_designs_conn_and_init()` كمصدر إلهام (لا استيراد فعلي)
