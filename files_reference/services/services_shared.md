# دليل الكود — Services المشتركة (services/shared/)

> `services/shared/` — خدمات الأصناف والتصنيفات والإعدادات المشتركة بين كل الوحدات.
> **الملفات الفعلية:** `item_service.py`, `category_service.py`, `font_service.py`, `language_service.py`, `settings_service.py`, `unit_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [item_service.py](#item_servicepy) | ItemService — CRUD الأصناف مع validation |
| [category_service.py](#category_servicepy) | CategoryService — CRUD التصنيفات مع شجرة هرمية |
| [font_service.py](#font_servicepy) | FontService — قراءة/كتابة حجم الخط (font_size) من/إلى DB |
| [language_service.py](#language_servicepy) | LanguageService — قراءة/كتابة لغة الواجهة (ui_language) من/إلى DB |
| [settings_service.py](#settings_servicepy) | SettingsService — قراءة/كتابة أي إعداد عام مشترك (مفتاح/قيمة عام) |
| [unit_service.py](#unit_servicepy) | وحدات القياس — دوال مستقلة (بدون class) مع caching بالـ db path |

---

## item_service.py

### Imports (top-level)

```python
from db.shared.items_repo import (
    fetch_item, fetch_items_by_type,
    insert_item, update_item, delete_item,
)
```

### Dataclasses

```python
@dataclass
class ItemValidationError:
    field   : str
    message : str

@dataclass
class ItemResult:
    id          : int
    name        : str
    price       : float
    item_type   : str
    category_id : int | None
    total_qty   : float | None

@dataclass
class DeletePreview:
    item_name  : str
    usage_count: int
    # can_delete() → usage_count == 0
    # warning_text() → رسالة تحذير لو usage_count > 0
```

### ItemService

```python
ItemService(conn)

# Validation
svc.validate(name, price) -> list[ItemValidationError]
# name.strip() غير فارغ + price >= 0

# قراءة
svc.get(item_id) -> ItemResult | None
svc.list_by_type(item_type) -> list[ItemResult]

# كتابة
svc.add(name, price, item_type, category_id=None, total_qty=None) -> int
# يستدعي validate() أولاً — Raises ValueError لو فشل

svc.update(item_id, name, price, category_id=None, total_qty=None)
# يستدعي validate() أولاً — Raises ValueError لو فشل

# حذف
svc.get_delete_preview(item_id) -> DeletePreview | None
svc.get_usage_count(item_id) -> int
svc.delete(item_id) -> bool   # False لو مستخدم في BOM
svc.force_delete(item_id)     # يحذف حتى لو مستخدم — للحالات الاستثنائية
```

**`get_usage_count` — [تحسين 18]:**
```python
# يشمل كل child_types:
SELECT COUNT(DISTINCT parent_id) FROM bom
WHERE child_id=? AND child_type IN ('raw','semi','labor_op','machine_op')
# القديم: كان يبحث في ('raw','semi') فقط
```

---

## category_service.py

### Imports (top-level)

```python
from db.shared.categories_repo import (
    fetch_category, fetch_descendants, fetch_all_categories,
    insert_category, update_category, delete_category,
    count_category_items, build_tree,
)
```

### Dataclasses

```python
@dataclass
class DeletePreview:
    cat_name    : str
    child_count : int
    item_counts : dict  # {"عناصر": n, "ماكينات": n, ...}
    # item_count → sum(item_counts.values())
    # warning_text() → رسالة تحذير

@dataclass
class CategoryNode:
    id, name, color, scope, parent_id : ...
    children : list[CategoryNode]
```

### CategoryService

```python
CategoryService(conn)
```

#### دوال القراءة (مطلوبة من managers/category.py و combo/category.py)

```python
svc.get_all(scope: str = "all") -> list
# يرجع list of dicts — يستدعي fetch_all_categories ثم [dict(r) for r in rows]

svc.build_tree(rows: list) -> list
# يبني هيكل شجري من list of dicts
# يمرر rows لـ build_tree من categories_repo

svc.get_one(cat_id: int) -> dict | None
# يرجع تصنيف واحد بالـ id كـ dict

svc.get_descendants(cat_id: int) -> set
# يرجع set من IDs كل الأبناء والأحفاد
# يستدعي fetch_descendants ثم set(...)

svc.count_items(cat_id: int) -> dict
# {"عناصر": n, "عمليات عمالة": n, ...}
```

#### الكتابة

```python
svc.add(name, scope, color, parent_id=None) -> int
# Raises: ValueError لو name.strip() فارغ

svc.update(cat_id, name, scope, color, parent_id=None)
# Raises: ValueError لو name.strip() فارغ
```

#### الحذف

```python
svc.get_delete_preview(cat_id) -> DeletePreview | None
# child_count = len(descendants) - 1  (يطرح التصنيف نفسه)

svc.delete_cascade(cat_id) -> int
# يحذف التصنيف وكل أبنائه بالترتيب العكسي
# يرجع عدد التصنيفات المحذوفة
```

#### Legacy

```python
svc.get_tree(scope: str = None) -> list[CategoryNode]
# يرجع شجرة التصنيفات كـ dataclasses (للكود القديم)
# يستدعي get_all + build_tree + _to_node داخلياً
```

---

## font_service.py

### `services/shared/font_service.py`

**الغرض:** الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات لقراءة وكتابة حجم الخط (`font_size`) — يحقق التسلسل `ui/font.py → ui/app_state.AppState → FontService → db/shared/settings_repo → DB`. طبقة الـ UI لا تعرف شيئاً عن DB أو `settings_repo` مباشرة.

**Imports (top-level):**
```python
from __future__ import annotations
import logging
from ui.constants import DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE
# استيراد داخلي (lazy) في كل classmethod:
from db.shared.settings_repo import get_setting, set_setting
```

**من يستدعي هذا الملف:** `ui/app_state.AppState` (موثّق صراحة في الكود كسلسلة الاستدعاء الكاملة) — لا يُستخدم هذا الملف مباشرةً من أي ملف آخر في `ui/`.

### Class: `FontService`
لا يرث من شيء. كل الـ methods **class-level** (`@classmethod`) — لا يوجد instance.

- `_SETTINGS_KEY = "font_size"` — ثابت class-level.

**Classmethods:**
- **`load(cls) -> int`**: يقرأ `font_size` من DB (يفتح اتصاله الخاص عبر `cls._get_conn()` ويغلقه ضمنياً حسب سياق try/except). لو المفتاح غير موجود (`raw is None`) → يحفظ `DEFAULT_FONT_SIZE` ويرجعه. لو القيمة خارج النطاق `[MIN_FONT_SIZE, MAX_FONT_SIZE]` → يحفظ `DEFAULT_FONT_SIZE` ويرجعه (مع `logger.debug` بالتفاصيل). لو فشل الاتصال بالكامل → يرجع `DEFAULT_FONT_SIZE` بصمت.
- **`save(cls, size: int) -> bool`**: يُقيّد `size` ضمن `[MIN_FONT_SIZE, MAX_FONT_SIZE]` أولاً (`max(MIN, min(MAX, size))`) كطبقة أمان إضافية — رغم أن التحقق الأساسي من النطاق يحدث في `AppState` قبل الاستدعاء. يكتب عبر `set_setting`. يرجع `True` عند النجاح، `False` بصمت عند أي فشل (اتصال أو كتابة).

**ملاحظات مهمة من التعليقات:**
- الملف يوثّق تسلسل الاستدعاء الكامل صراحة في docstring الـ class: `ui/font.py → AppState → FontService → db/shared/settings_repo → SQLite/DB`.

---

## language_service.py

### `services/shared/language_service.py`

**الغرض:** الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات لقراءة وكتابة لغة الواجهة (`ui_language`). **[إصلاح هيكلي] موثّق في الكود:** كان `ui/widgets/core/i18n.py` يستدعي `db.shared.settings_repo` مباشرة من داخل `widgets/` — كسر هيكلي (تجاوز لطبقة `services/`). هذا الملف يحل المشكلة بنفس نمط `item_service.get_gimp_path()`: إعداد مشترك غير مرتبط بشركة معينة، يفتح اتصاله الخاص عبر `db.shared.connection.get_connection()` ويغلقه فور الانتهاء.

**Imports (top-level):**
```python
from __future__ import annotations
import logging
from db.shared.connection import get_connection
from db.shared.settings_repo import get_setting, set_setting
```

**من يستدعي هذا الملف:** `I18nManager` حصراً (موثّق صراحة: "لا يُستخدم هذا الملف مباشرةً من أي ملف في `ui/` عدا `i18n.py`").

### Class: `LanguageService`
لا يرث من شيء. كل الـ methods **class-level** (`@classmethod`) — لا يوجد instance.

- `_SETTINGS_KEY = "ui_language"`, `_DEFAULT_LANG = "ar"` — ثوابت class-level.

**Classmethods:**
- **`load(cls) -> str`**: يفتح اتصاله عبر `get_connection()` ويغلقه في `finally`. يقرأ عبر `get_setting(conn, _SETTINGS_KEY, _DEFAULT_LANG)`؛ يرجع `lang or cls._DEFAULT_LANG`. يرجع `_DEFAULT_LANG` بصمت (مع `logger.debug`) عند أي استثناء.
- **`save(cls, lang: str) -> bool`**: يفتح اتصاله عبر `get_connection()` ويغلقه في `finally`. يكتب عبر `set_setting(conn, _SETTINGS_KEY, lang)`. يرجع `True` عند النجاح، `False` بصمت (مع `logger.debug`) عند أي فشل — لا يُوقف التطبيق.

---

## settings_service.py

### `services/shared/settings_service.py`

**الغرض:** الوسيط **العام** (وليس مخصصاً لمفتاح واحد) بين طبقة الـ UI وقاعدة البيانات لقراءة وكتابة أي إعداد مشترك (`settings`) غير مرتبط بشركة معينة. **[إصلاح هيكلي] موثّق في الكود:** كان `ui/widgets/dialogs/settings_dialog.py` يستدعي `db.shared.settings_repo` (`get_setting`/`set_setting`) مباشرة من داخل `widgets/` — كسر هيكلي. أي إعداد مشترك مستقبلي (غير الخط أو اللغة، اللذين لهما service مخصص فعلاً: `FontService`, `LanguageService`) يُقرأ ويُكتب من هنا بدل تكرار نفس نمط `get_connection`/`get_setting`/`set_setting` في كل مكان.

**Imports (top-level):**
```python
from __future__ import annotations
import logging
from db.shared.connection import get_connection
from db.shared.settings_repo import get_setting, set_setting
```

**من يستدعي هذا الملف:** `settings_dialog.py` أو أي UI آخر (موثّق صراحة في الكود). **ملاحظة موثّقة:** "لا يُستخدم مباشرةً من أي ملف في `db/` أو خارج `services/` أو `ui/`".

### Class: `SettingsService`
لا يرث من شيء. كل الـ methods **class-level** (`@classmethod`) — لا يوجد instance. نفس نمط `LanguageService`/`FontService` بالضبط (اتصال مستقل يُفتح ويُغلق فوراً).

**Classmethods:**
- **`get(cls, key: str, default=None)`**: يفتح اتصاله عبر `get_connection()` ويغلقه في `finally`. يقرأ عبر `get_setting(conn, key, default)`؛ يرجع `val if val is not None else default`. يرجع `default` بصمت (مع `logger.debug`) عند أي استثناء.
- **`set(cls, key: str, value) -> bool`**: يفتح اتصاله عبر `get_connection()` ويغلقه في `finally`. يكتب عبر `set_setting(conn, key, value)`. يرجع `True` عند النجاح، `False` بصمت (مع `logger.debug`) عند أي فشل.

---

## unit_service.py

### `services/shared/unit_service.py`

**الغرض:** Business logic لوحدات القياس — **دوال مستقلة (لا يوجد class)**، مفصولة عن الـ widget. **[إصلاح هيكلة] موثّق في الكود:** نُقل من `ui/widgets/combo/unit_service.py` إلى هنا — `widgets/` (base classes) ممنوعة تستدعي `repos/` (`db/`) مباشرة حسب الهيكلة المعمارية للمشروع؛ كان الملف القديم يستدعي `db.shared.settings_repo` مباشرة من داخل `widgets/` (كسر هيكلي). النقل لـ `services/shared/` يحل المشكلة لأن `services/` هي الطبقة الوحيدة المسموح لها تستدعي `repos/` (بنفس نمط `font_service.py`). مستخرج أصلاً من `combo/unit.py`.

**Imports (top-level):**
```python
import json
import logging
# استيراد داخلي (lazy) في كل دالة تلمس DB:
from db.shared.settings_repo import get_setting, set_setting
```

**من يستدعي هذا الملف:** غير محدد بثقة أي ملف UI مباشرة من المرفقات الحالية (متوقع من `ui/widgets/combo/unit.py` حسب اسم الملف القديم الذي نُقل منه — لكن محتواها غير مرفق).

### ثوابت module-level

```python
_UNITS_KEY = "custom_units"
_DEFAULT_UNIT_KEYS = ("px", "mm", "cm", "m", "inch")
# قيم الوحدات الافتراضية كمعرّفات داخلية فقط (بدون نص معروض) —
# تُستخدم في remove_unit للتحقق من كون الوحدة "افتراضية" أم لا

_units_cache: dict = {}
# cache: db_path (أو fallback id(conn)) → list[tuple[str, str]]
```

### دوال top-level مستقلة

- **`_default_units() -> list`**: **[i18n] موثّق في الكود:** الوحدات الافتراضية أصبحت دالة تُستدعى وقت الحاجة، بدل ثابت module-level كان يُحسب وقت الـ import (قبل تحميل اللغة) ولا يتحدّث بعدها أبداً عند تغيير اللغة. ترجع قائمة ثابتة من 5 tuples: `[("px","px"), ("mm","mm"), ("cm","cm"), ("m","m"), ("inch","inch")]`.
- **`_cache_key(conn) -> str`**: يرجع مسار قاعدة البيانات (`PRAGMA database_list`) كمفتاح cache. عند الفشل: fallback آمن بصيغة `f"_id_{id(conn)}"` (مع `logger.debug`).
- **`invalidate_units_cache(conn=None)`**: لو `conn is None` → يمسح الـ cache بالكامل (`_units_cache.clear()`). وإلا → يمسح مفتاح هذا الـ `conn` فقط عبر `_cache_key`. يُستدعى بعد تغيير الوحدات أو تغيير الشركة.
- **`load_units(conn, force: bool = False) -> list`**: يجلب قائمة الوحدات من `settings` مع cache حسب `_cache_key(conn)`. لو `force=False` والمفتاح موجود في الـ cache → يرجعه مباشرة. وإلا: يبدأ بـ `_default_units()` كقيمة أساسية، ثم يحاول قراءة `_UNITS_KEY` من `get_setting` وفكّ ترميزه بـ `json.loads` (لو موجود) — عند أي فشل يُبقي القيمة الافتراضية (`logger.debug`). يخزّن النتيجة في الـ cache قبل الإرجاع.
- **`save_units(conn, units: list)`**: يكتب `units` كـ JSON (`ensure_ascii=False`) عبر `set_setting`، ثم يستدعي `invalidate_units_cache(conn)`. عند الفشل: `logger.warning` بدون رفع استثناء.
- **`get_last_unit(conn, key: str, fallback: str = "cm") -> str`**: يقرأ `f"last_unit_{key}"` من `settings`؛ يرجع `fallback` لو القيمة فارغة أو حدث استثناء.
- **`set_last_unit(conn, key: str, unit: str)`**: يكتب `f"last_unit_{key}"` إلى `settings`. عند الفشل: `logger.debug` بدون رفع استثناء.
- **`add_unit(conn, value: str, label: str) -> bool`**: يُنظّف (`.strip().lower()` لـ `value`, `.strip()` لـ `label`)؛ يرجع `False` لو أي منهما فارغ بعد التنظيف. يجلب `load_units(conn)`، يرفض (`False`) لو `value` موجود بالفعل (بحث بالمقارنة على `u[0]`). وإلا يضيف `(value, label)` ويحفظ عبر `save_units`، يرجع `True`.
- **`remove_unit(conn, value: str) -> bool`**: يرفض (`False`) فوراً لو `value in _DEFAULT_UNIT_KEYS` (لا يمكن حذف الوحدات الافتراضية). يفلتر الوحدة من القائمة؛ لو لم يتغيّر طول القائمة (لم توجد أصلاً) → `False`. وإلا يحفظ ويرجع `True`.
- **`get_all_units(conn) -> list`**: alias مباشر لـ `load_units(conn)`.
- **`reset_units_to_default(conn)`**: يحفظ `_default_units()` (يستبدل كل الوحدات المخصصة بالقائمة الافتراضية).

**ملاحظات مهمة من التعليقات:**
- الـ cache على مستوى module-level (`_units_cache` عام، وليس داخل class) — مفتاحه ديناميكي حسب `db_path` لكل شركة نشطة، لذلك يدعم تعدد الشركات دون تصادم.

---

## ملاحظات

- `get_usage_count` يفحص جدول `bom` في `erp.db` — تأكد أن `conn` هو `erp_conn` [تحسين 18].
- `delete_cascade` يحذف بالترتيب العكسي `sorted(descendants, reverse=True)` لتجنب FK violations.
- `get_all` + `build_tree` هما الزوج المستخدم في `managers/category.py` و `combo/category.py`.
- **نمط مشترك بين `font_service.py`, `language_service.py`, `settings_service.py`:** الثلاثة تتبع نفس النمط بالضبط — كل الـ methods `@classmethod`، بدون instance، كل استدعاء يفتح اتصاله المستقل عبر `db.shared.connection.get_connection()` ويغلقه فوراً (لأن الإعدادات مشتركة وغير مرتبطة بـ `conn` الشركة النشطة)، ويبتلع كل الأخطاء بصمت (`logger.debug`) مع قيمة افتراضية آمنة عند الفشل. `settings_service.py` هو التعميم العام لنفس النمط الذي بدأ به `font_service.py` و`language_service.py` لمفتاح واحد محدد.
- **`unit_service.py` مختلف عن الثلاثة أعلاه:** لا يوجد class على الإطلاق — دوال مستقلة فقط، ويستقبل `conn` كمعامل صريح في كل دالة (وليس اتصالاً داخلياً مستقلاً)، لأنه يعمل على قاعدة بيانات الشركة النشطة (نفس `conn` الممرَّر من الـ widget) وليس على إعداد عام كوني.