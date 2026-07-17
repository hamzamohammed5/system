# دليل الكود — Services التصميم (services/design/)

> `services/design/` — التصميمات وتصنيفاتها، مقاسات التصميم، ومجموعات المقاسات (dimension sets) وحقولها.
> **الملفات الفعلية:** `__init__.py`, `design_service.py`, `design_size_service.py`, `dimension_set_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [__init__.py](#__init__py) | Factory مركزية — نقطة الدخول الوحيدة من tabs/widgets + bootstrapping اتصال designs.db |
| [design_service.py](#design_servicepy) | DesignService — CRUD التصميمات وتصنيفات العناصر (design_item_categories) |
| [design_size_service.py](#design_size_servicepy) | DesignSizeService — CRUD مقاسات التصميم وربطها بمجموعات المقاسات |
| [dimension_set_service.py](#dimension_set_servicepy) | DimensionSetService — CRUD مجموعات المقاسات، حقولها، اعتمادياتها، وinstances |

---

## __init__.py

### `services/design/__init__.py`

**الغرض:** Factory مركزية لخدمات التصميم — نقطة الدخول الوحيدة من `tabs/widgets`. بدل أن يبني كل widget `DesignService(conn)` بنفسه، تستخدم الـ factory هنا لضمان نفس الـ instance لنفس الـ connection، وعدم الانكسار لو الشركة النشطة اتغيّرت (`conn` جديد). كما يوفّر bootstrapping لاتصال `designs.db`.

**Imports (top-level):**
```python
from .design_service import DesignService
from .design_size_service import DesignSizeService
from .dimension_set_service import DimensionSetService
from db.designs.design_schema import get_designs_connection, create_designs_tables
```

**من يستدعي هذا الملف:** متوقع من `ui/tabs/design/*` عموماً (`designs_tab.py`, `dimension_sets_tab.py`, وكل الـ widgets تحت `ui/tabs/design/designs/` و`ui/tabs/design/dimension_sets/`) حسب `system_arch.txt` وحسب توثيق الملف نفسه — لكن محتواها غير مرفق. **`services/orders/order_service.py`** يستخدم نمطاً مطابقاً تماماً (`get_orders_conn_and_init`) ويذكر هذا الملف صراحة كمصدر النمط ("نفس نمط `get_designs_conn_and_init()` في `services/design/__init__.py`").

### Cache داخلي — module-level

```python
_design_service_instance:        DesignService | None = None
_design_size_service_instance:   DesignSizeService | None = None
_dimension_set_service_instance: DimensionSetService | None = None
```

**ملاحظة تصميم موثّقة صراحة في الكود:** استُخدم متغير مفرد بدل `dict` مفتوح بـ `id(conn)` عمداً — لأنه في أي لحظة توجد شركة نشطة واحدة فقط (`company_state.company_id`)؛ استخدام `dict` بمفتاح `id(conn)` كان سيتراكم فيه مرجع دائم لكل `conn` قديم (حتى بعد إغلاق الشركة) → **memory leak** طول عمر التطبيق. المتغير المفرد يستبدل نفسه تلقائياً عند تغيّر الـ `conn`، فلا يبقى أي مرجع قديم يمنع الـ garbage collector.

### دوال top-level مستقلة (Factory)

- **`get_design_service(conn) -> DesignService`**: يرجع `DesignService` واحد للـ `conn` الحالي. نفس الـ `conn` → نفس الـ instance (بدون إعادة بناء، مقارنة عبر `is not conn`). `conn` مختلف (شركة جديدة) → instance جديد يستبدل القديم تلقائياً (`global _design_service_instance`).
- **`get_design_size_service(conn) -> DesignSizeService`**: نفس المنطق بالضبط لـ `DesignSizeService`.
- **`get_dimension_set_service(conn) -> DimensionSetService`**: نفس المنطق بالضبط لـ `DimensionSetService`.

### دالة top-level مستقلة (Bootstrapping)

- **`get_designs_conn_and_init()`**: يفتح اتصال `designs.db` (`get_designs_connection()`) وينشئ/يهيّئ جداوله إن لم تكن موجودة (`create_designs_tables(conn)`)، ثم يرجع الاتصال. **[إضافة] موثّق في الكود:** غُلِّفت `get_designs_connection` + `create_designs_tables` هنا عشان `tabs/design_section.py` لا يستدعي `db.designs.design_schema` مباشرة (كسر هيكلي: `tabs → repos/db` بتجاوز `services`). القاعدة المعمارية المحفوظة: `tabs/ → services/design.get_designs_conn_and_init() → db.designs.design_schema`. دالة bootstrapping بحتة (فتح اتصال + تهيئة جداول)، وليست عملية بيانات — لذلك مكانها هنا وليس داخل كل service مستقل.

**ملاحظات مهمة من التعليقات:**
- هذا الملف هو **مصدر النمط الموثّق** الذي يُستشهد به في ملفات أخرى من المشروع (مثل `services/orders/order_service.py`) عند إضافة bootstrapping مشابه لدومينات أخرى.

---

## design_service.py

### `services/design/design_service.py`

**الغرض:** Service layer للتصميمات (`designs`) وتصنيفات العناصر الخاصة بها (`design_item_categories`) — يغطي عمليات CRUD الأساسية بالإضافة لاستعلام تصفية/عرض متقدم (grid) مع أول ملف XCF لكل تصميم.

**Imports (top-level):**
```python
from db.designs.designs_repo import (
    fetch_all_designs, fetch_design, insert_design, update_design, delete_design,
)
from db.designs.design_item_categories_repo import (
    fetch_all_item_categories, fetch_item_category,
    insert_item_category, update_item_category, delete_item_category,
    build_item_category_tree, fetch_item_category_descendants,
    count_designs_per_category,
)
```

**من يستدعي هذا الملف:** عبر الـ factory `services/design/__init__.py.get_design_service(conn)` فقط (النمط الموصى به) — لا يُبنى مباشرة كـ `DesignService(conn)` من `tabs/` حسب توثيق `__init__.py`. متوقع من `ui/tabs/design/designs_tab.py` وملفات `ui/tabs/design/designs/*` حسب `system_arch.txt` — لكن محتواها غير مرفق.

### Class: `DesignService`
لا يرث من شيء.

```python
DesignService(conn)
```
- `self.conn = conn`.

**Methods — Designs:**
- **`list_designs(self, category_id=None, set_id=None, name_q="")`**: عبر `fetch_all_designs(conn, category_id, set_id, name_q)`.
- **`get_design(self, did)`**: عبر `fetch_design`.
- **`create_design(self, name, cat_id=None, notes="")`**: عبر `insert_design`.
- **`update_design(self, did, name, cat_id=None, notes="")`**: عبر `update_design` من الـ repo.
- **`delete_design(self, did)`**: عبر `delete_design` من الـ repo.

**Methods — Item Categories (تصنيفات عناصر التصميم):**
- **`list_item_categories(self)`**: عبر `fetch_all_item_categories`.
- **`get_item_category(self, cid)`**: عبر `fetch_item_category`.
- **`create_item_category(self, name, color, parent_id=None)`**: عبر `insert_item_category`.
- **`update_item_category(self, cid, name, color, parent_id=None)`**: عبر `update_item_category` من الـ repo.
- **`delete_item_category(self, cid)`**: عبر `delete_item_category` من الـ repo.
- **`build_tree(self, rows)`**: عبر `build_item_category_tree`.
- **`get_descendants(self, cid)`**: عبر `fetch_item_category_descendants`.
- **`count_designs_per_category(self)`**: عبر `count_designs_per_category` من الـ repo.

**Methods — Listing / Grid (فلترة متقدمة مع أول ملف XCF):**
- **`list_designs_filtered(self, name_q="", category_id=None, set_id=None)`**: استعلام `SQL` مبني ديناميكياً (لا يمر عبر `designs_repo` — الاستعلام مكتوب مباشرة هنا) يجلب تصميمات مع: اسم التصنيف ولونه (`LEFT JOIN design_item_categories`)، عدد المقاسات (`COUNT(DISTINCT ds.id)`)، عدد الملفات المرفوعة (`SUM(CASE WHEN xcf_path...)`), وأول `xcf_path` متاح.
  - **منطق `first_xcf_sql` الداخلي**: لو `set_id` محدد → أولوية لملف XCF من نفس المجموعة (`ds2.set_id = set_id_int`) مع `COALESCE` إلى fallback لأول ملف عموماً (`ds3`) لو لم يوجد ملف بهذه المجموعة تحديداً. لو `set_id` غير محدد → أول ملف عموماً فقط (بدون فلترة مجموعة).
  - **فلاتر WHERE**: `name_q` → `d.name LIKE '%name_q%'`. `category_id` → يحاول `fetch_item_category_descendants` لتضمين التصنيفات الفرعية (`IN (...)`)، وعند الفشل fallback إلى `d.item_category_id = category_id` مباشرة (بدون تفرعات). `set_id` → `EXISTS` subquery على `design_sizes`.
  - `GROUP BY d.id ORDER BY d.updated_at DESC, d.name`.
- **`get_first_xcf_for_design(self, design_id, set_id=None)`**: يجيب مسار XCF المناسب — لو `set_id` محدد: يبحث أولاً عن ملف بنفس المجموعة (`ORDER BY sort_order, id LIMIT 1`)؛ لو لم يجد، **fallback**: يبحث عن أول ملف موجود عموماً بغض النظر عن المجموعة. يرجع `None` لو لا يوجد ملف على الإطلاق.

**ملاحظات مهمة من التعليقات:**
- `list_designs_filtered` هو الاستعلام الوحيد في هذا الملف الذي يبني SQL كاملاً بنفسه (بدل تفويضه لـ `designs_repo`) — بسبب التعقيد الديناميكي (فلاتر متعددة اختيارية + `first_xcf_sql` المتغير حسب `set_id`).

---

## design_size_service.py

### `services/design/design_size_service.py`

**الغرض:** Service layer لمقاسات التصميم (`design_sizes`) — CRUD المقاسات، مسارات ملفات XCF، أبعاد الكانفاس ودقتها، وربط المقاس بمجموعة مقاسات (`dimension_set`) و`instance` محدد منها.

**Imports (top-level):**
```python
from db.designs.designs_sizes_repo import (
    fetch_design_sizes, fetch_design_size,
    insert_design_size, update_design_size, delete_design_size,
    update_design_size_path, fetch_canvas_size, fetch_canvas_dpi,
    fetch_instances_for_set_with_values, instance_already_used,
)
from db.designs.dimension_sets_repo import fetch_all_dimension_sets, fetch_fields_for_set
```

**من يستدعي هذا الملف:** عبر الـ factory `services/design/__init__.py.get_design_size_service(conn)`. متوقع من `ui/tabs/design/designs/_size_card.py`, `_size_dialog.py`, `size_card/helper.py` حسب `system_arch.txt` — لكن محتواها غير مرفق.

### Class: `DesignSizeService`
لا يرث من شيء.

```python
DesignSizeService(conn)
```
- `self.conn = conn`.

**Methods — المقاسات:**
- **`list_sizes(self, design_id)`**: عبر `fetch_design_sizes`.
- **`get_size(self, size_id)`**: عبر `fetch_design_size`.
- **`create_size(self, design_id, set_id, instance_id, width_field_id=None, height_field_id=None, xcf_path=None, notes="", dpi_field_id=None)`**: عبر `insert_design_size` — يربط المقاس بمجموعة (`set_id`) و`instance` منها، بالإضافة لحقول العرض/الارتفاع/الدقة الاختيارية.
- **`update_size(self, size_id, width_field_id, height_field_id, xcf_path, notes, dpi_field_id=None)`**: عبر `update_design_size` من الـ repo.
- **`update_path(self, size_id, path)`**: يحدّث مسار ملف XCF فقط — عبر `update_design_size_path`.
- **`delete_size(self, size_id)`**: عبر `delete_design_size` من الـ repo.

**Methods — الكانفاس:**
- **`get_canvas_size(self, size_id)`**: عبر `fetch_canvas_size`.
- **`get_canvas_dpi(self, size_id)`**: عبر `fetch_canvas_dpi`.

**Methods — مجموعات المقاسات (facade جزئي على dimension_sets_repo):**
- **`list_all_sets(self)`**: عبر `fetch_all_dimension_sets`.
- **`list_fields_for_set(self, set_id)`**: عبر `fetch_fields_for_set`.
- **`list_instances_for_set(self, set_id)`**: عبر `fetch_instances_for_set_with_values` — **من `dimension_instances_repo` عبر `designs_sizes_repo`** (الدالة مستوردة أصلاً من `db.designs.designs_sizes_repo`، وليس من `dimension_instances_repo` مباشرة، رغم أن اسمها يوحي بذلك).
- **`is_instance_used(self, design_id, instance_id, exclude_size_id=None)`**: يتحقق هل الـ `instance` مستخدم بالفعل في مقاس آخر لنفس التصميم — عبر `instance_already_used`.

**Methods — قراءة قيم مباشرة (SQL مباشر):**
- **`get_set_default_unit(self, set_id) -> str`**: `SELECT default_unit FROM dimension_sets WHERE id=?` — يرجع `"cm"` لو لا توجد قيمة محفوظة.
- **`get_field_value(self, instance_id, field_id)`**: `SELECT value_num FROM dimension_set_values WHERE instance_id=? AND field_id=?` — يرجع `None` لو لا يوجد صف.

**ملاحظات مهمة من التعليقات:**
- هذا الملف يخلط بين استدعاء دوال `repo` جاهزة واستعلامات SQL مباشرة بسيطة (`get_set_default_unit`, `get_field_value`) لقراءة قيمة واحدة — نمط مشابه لـ `dimension_set_service.py` (راجع أدناه).

---

## dimension_set_service.py

### `services/design/dimension_set_service.py`

**الغرض:** Service layer الأشمل في هذا المسار — يغطي مجموعات المقاسات (`dimension_sets`) وحقولها (`dimension_fields`)، اعتمادياتها (`field_dep` — حقل يعتمد قيمته على حقل آخر بإزاحة معينة)، تصنيفات التصميم (`design_categories`)، و**instances** (نسخ فعلية من مجموعة مقاسات بقيم محددة).

**Imports (top-level):**
```python
from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets, fetch_dimension_set,
    insert_dimension_set, update_dimension_set, delete_dimension_set,
    fetch_fields_for_set, fetch_field,
    insert_field, update_field, delete_field, reorder_fields,
    fetch_field_dep, set_field_dep, remove_field_dep,
    fetch_all_design_categories, fetch_design_category,
    insert_design_category, update_design_category, delete_design_category,
    build_category_tree, fetch_category_descendants,
)
from db.designs.dimension_instances_repo import (
    fetch_instances_for_set, fetch_instance,
    insert_instance, update_instance, delete_instance, duplicate_instance,
    fetch_instance_values, save_instance_values, calc_instance_cross_auto,
)
```

**من يستدعي هذا الملف:** عبر الـ factory `services/design/__init__.py.get_dimension_set_service(conn)`. متوقع من `ui/tabs/design/dimension_sets_tab.py` وملفات `ui/tabs/design/dimension_sets/*` (`_categories_panel.py`, `_field_dialog.py`, `_fields_panel.py`, `_groups_panel.py`, `_sets_panel.py`, `_source_picker_dialog.py`, `_values_panel.py`, `values_panel/*`) حسب `system_arch.txt` — لكن محتواها غير مرفق.

### Class: `DimensionSetService`
لا يرث من شيء. **أشمل class في هذا المسار — يغطي 4 كيانات مختلفة** (Sets, Fields, Categories, Instances).

```python
DimensionSetService(conn)
```
- `self.conn = conn`.

**Methods — Sets (مجموعات المقاسات):**
- **`list_sets(self)`**: عبر `fetch_all_dimension_sets`.
- **`get_set(self, sid)`**: عبر `fetch_dimension_set`.
- **`create_set(self, name, cat_id, unit, notes)`**: عبر `insert_dimension_set`.
- **`update_set(self, sid, name, cat_id, unit, notes)`**: عبر `update_dimension_set` من الـ repo.
- **`delete_set(self, sid)`**: عبر `delete_dimension_set` من الـ repo.
- **`count_designs_for_set(self, sid) -> int`**: **SQL مباشر** — `SELECT COUNT(*) FROM design_sizes WHERE set_id=?`.
- **`count_fields_for_set(self, sid) -> int`**: **SQL مباشر** — `SELECT COUNT(*) FROM dimension_fields WHERE set_id=?`.
- **`count_instances_for_set(self, sid) -> int`**: **SQL مباشر** — `SELECT COUNT(*) FROM dimension_set_instances WHERE set_id=?`.

**Methods — Fields (حقول المجموعة):**
- **`list_fields(self, set_id)`**: عبر `fetch_fields_for_set`.
- **`get_field(self, fid)`**: عبر `fetch_field`.
- **`create_field(self, set_id, name, label, unit, ftype, required, sort_order)`**: عبر `insert_field`.
- **`update_field(self, fid, name, label, unit, ftype, required, sort_order)`**: عبر `update_field` من الـ repo.
- **`delete_field(self, fid)`**: عبر `delete_field` من الـ repo.
- **`reorder_fields(self, set_id, ids)`**: يعيد ترتيب الحقول — عبر `reorder_fields` من الـ repo.

**Methods — Field Dependencies (اعتماديات الحقول):**
- **`get_field_dep(self, fid)`**: عبر `fetch_field_dep`.
- **`set_field_dep(self, fid, src_fid, offset, notes, src_set_id=None)`**: يربط حقلاً بحقل مصدر (قد يكون من مجموعة أخرى عبر `src_set_id` اختياري) مع إزاحة (`offset`) وملاحظات — عبر `set_field_dep`.
- **`remove_field_dep(self, fid)`**: عبر `remove_field_dep` من الـ repo.

**Methods — Categories (تصنيفات التصميم — مختلفة عن `design_item_categories` في `design_service.py`):**
- **`list_categories(self)`**: عبر `fetch_all_design_categories`.
- **`get_category(self, cid)`**: عبر `fetch_design_category`.
- **`create_category(self, name, color, parent_id)`**: عبر `insert_design_category`.
- **`update_category(self, cid, name, color, parent_id)`**: عبر `update_design_category` من الـ repo.
- **`delete_category(self, cid)`**: عبر `delete_design_category` من الـ repo.
- **`build_tree(self, rows)`**: عبر `build_category_tree`.
- **`get_descendants(self, cid)`**: عبر `fetch_category_descendants`.
- **`count_sets_in_category(self, cid) -> int`**: **SQL مباشر** — `SELECT COUNT(*) FROM dimension_sets WHERE category_id=?`.

**Methods — Instances (نسخ فعلية من مجموعة بقيم محددة):**
- **`list_instances(self, set_id)`**: عبر `fetch_instances_for_set`.
- **`get_instance(self, iid)`**: عبر `fetch_instance`.
- **`create_instance(self, set_id, name)`**: عبر `insert_instance`.
- **`update_instance(self, iid, name)`**: عبر `update_instance` من الـ repo.
- **`delete_instance(self, iid)`**: عبر `delete_instance` من الـ repo.
- **`duplicate_instance(self, iid, new_name)`**: ينسخ `instance` موجود باسم جديد — عبر `duplicate_instance`.
- **`get_instance_values(self, iid)`**: عبر `fetch_instance_values`.
- **`save_instance_values(self, iid, set_id, values)`**: عبر `save_instance_values` من الـ repo.
- **`calc_cross_auto(self, field_id, instance_id)`**: يحسب قيمة حقل تلقائياً بناءً على اعتماديته المتقاطعة (cross-field) — عبر `calc_instance_cross_auto`.
- **`get_source_instance_value(self, source_instance_id, source_field_id)`**: **SQL مباشر** — `SELECT value_num FROM dimension_set_values WHERE instance_id=? AND field_id=?`. يرجع `float(value_num)` أو `None` لو لا توجد قيمة.

**Methods — مساعدة:**
- **`get_set_name(self, set_id) -> str`**: **SQL مباشر** — `SELECT name FROM dimension_sets WHERE id=?`. يرجع `f"#{set_id}"` كـ fallback لو المجموعة غير موجودة.

**ملاحظات مهمة من التعليقات:**
- الملف يخلط بكثافة بين استدعاء دوال `repo` واستعلامات SQL مباشرة بسيطة (عدّ سجلات، قراءة قيمة واحدة) — 6 دوال SQL مباشرة من إجمالي ~27 method، كلها استعلامات قراءة بسيطة (`COUNT` أو `SELECT` عمود واحد) وليست منطق أعمال معقد.
- **تحذير تسمية محتمل:** توجد `Categories` هنا (`design_categories` جدول) مختلفة عن `Item Categories` في `design_service.py` (`design_item_categories` جدول) — كيانان مختلفان بأسماء methods متشابهة (`list_categories`/`list_item_categories`) في نفس المسار عبر ملفين مختلفين.

---

## علاقات الملفات

- **`__init__.py` يستورد الثلاثة الآخرين مباشرة** (`DesignService`, `DesignSizeService`, `DimensionSetService`) ليبني الـ factory functions حولهم — هذه هي العلاقة الوحيدة الفعلية بين ملفات هذا المسار على مستوى الكود.
- لا يوجد استيراد متبادل بين `design_service.py`, `design_size_service.py`, و`dimension_set_service.py` أنفسهم — كل واحد مستقل ويُستهلك فقط عبر الـ factory في `__init__.py`.
- **نمط مشترك:** الثلاثة classes (`DesignService`, `DesignSizeService`, `DimensionSetService`) تتبع نفس نمط constructor بسيط: `Service(conn)` مع `self.conn = conn` (وليس `self._conn` كما في بعض ملفات `services/` الأخرى — لاحظ غياب الـ underscore هنا تحديداً).
- **نمط مشترك آخر:** الثلاثة تخلط بين تفويض العمليات لدوال `repo` واستعلامات SQL مباشرة بسيطة (عدّ/قراءة قيمة واحدة) مباشرة داخل الـ service نفسه — بعكس النمط الأكثر صرامة في بعض ملفات `services/accounting/` مثلاً حيث كل SQL معقد ينتقل لـ `repo`.
- تبعية خارج هذا المسار:
  - `__init__.py` يعتمد على `db/designs/design_schema.py` (`get_designs_connection`, `create_designs_tables`).
  - `design_service.py` يعتمد على `db/designs/designs_repo.py` و`db/designs/design_item_categories_repo.py`.
  - `design_size_service.py` يعتمد على `db/designs/designs_sizes_repo.py` و`db/designs/dimension_sets_repo.py`.
  - `dimension_set_service.py` يعتمد على `db/designs/dimension_sets_repo.py` و`db/designs/dimension_instances_repo.py`.
- لا يوجد ملف مرجعي آخر معروف من المرفقات الحالية يستورد من هذا المسار مباشرة — لكن `services/orders/order_service.py` (مسار مختلف تماماً) يستشهد بنمط `get_designs_conn_and_init()` كمصدر إلهام لدالة `get_orders_conn_and_init()` الخاصة به (راجع `services_orders.md`)، دون استيراد فعلي.
