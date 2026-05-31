# تقرير المراجعة الشاملة — استكمال هيكلة النظام

## الهدف
```
widgets/ (base classes) → tabs/UI ──→ services/ ──→ repos/ (db/) ← schema/
```

---

## أولاً: ما اكتمل بالفعل في الكود الحالي

- `op_rows.py` — `_determine_target_id` بـ `is not None` ✅
- `list_panel.py` — `_timer.stop()` في `refresh()` ✅
- `widget.py` — إخفاء `lbl_variant_cost` في `_on_type_changed` ✅
- `conn.py` — `DualConnMixin._get_erp_conn` يستخدم `get_erp_conn()` ✅

---

## ثانياً: إصلاحات مطلوبة

---

### 🔴 1. `forms/inputs.py` — استيراد من ملف محذوف + استيراد مكرر

**الملف:** `ui/widgets/forms/inputs.py` (doc 32)

**المشكلتان:**

```python
# السطر الحالي — خطأ (theme/styles.py محذوف بعد Refactor V3)
from ..theme.styles import input_style as _input_style, spinbox_style as _spinbox_style

# السطر الحالي — مكرر مع `from ui.font import get_font_size` أعلاه
from ..core import get_font_size as _get_font_size
```

**الإصلاح:**
```python
# صح
from ..theme.input_styles import input_style as _input_style, spinbox_style as _spinbox_style
# حذف السطر الثاني بالكامل
```

---

### 🟠 2. `core/conn.py` — `SafeConnMixin._get_safe_conn` تستخدم private API

**الملف:** `ui/widgets/core/conn.py` (doc 76)

**الكود الحالي:**
```python
def _get_safe_conn(self):
    # ...
    if self.__safe_db_name == "erp":
        new_conn = company_state.get_erp_conn()  # ← هذا صح
    else:
        get_fn = getattr(company_state, "get_erp_conn", None)
        if get_fn and self.__safe_db_name == "erp":   # ← شرط مستحيل! self.__safe_db_name == "erp" تحقق بالفعل في الـ if أعلاه
            new_conn = get_fn()
        else:
            _get = getattr(company_state, "_get_conn", None)   # ← private API
            new_conn = _get(self.__safe_db_name) if _get else None
```

**المشكلة:** الـ `else` branch يحتوي على:
- شرط مستحيل (`self.__safe_db_name == "erp"` تحقق بالفعل أعلاه)
- استخدام `_get_conn` الـ private API كـ fallback

**الإصلاح:**
```python
def _get_safe_conn(self):
    if _test_conn(self.__safe_conn):
        return self.__safe_conn

    logger.debug("%s._get_safe_conn: reconnecting", type(self).__name__)
    try:
        from db.companies.company_state import company_state
        if self.__safe_db_name == "erp":
            new_conn = company_state.get_erp_conn()
        else:
            # لأنواع DB الأخرى (accounting, etc.) — نحاول _get_conn كـ fallback
            # لأن public API غير متاح لكل أنواع DB
            _get = getattr(company_state, "_get_conn", None)
            new_conn = _get(self.__safe_db_name) if _get else None
            if new_conn is None:
                logger.warning(
                    "%s._get_safe_conn: no public API for db '%s', trying erp fallback",
                    type(self).__name__, self.__safe_db_name
                )
                new_conn = company_state.get_erp_conn()

        if _test_conn(new_conn):
            self.__safe_conn = new_conn
            return new_conn
    except Exception as e:
        logger.warning("%s._get_safe_conn: reconnect failed: %s",
                       type(self).__name__, e)

    raise _conn_null_error(
        type(self).__name__, "_get_safe_conn", self.__safe_db_name
    )
```

---

### 🟡 3. `dialogs/settings_dialog.py` — استيراد من re-export بدل المصدر

**الملف:** `ui/widgets/dialogs/settings_dialog.py` (doc 15)

**الكود الحالي:**
```python
from ui.widgets.combo.unit import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)
```

`combo/unit.py` يُعيد تصدير هذه الدوال من `unit_service.py`. الاستيراد يجب أن يكون من المصدر مباشرة.

**الإصلاح:**
```python
from ui.widgets.combo.unit_service import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)
```

---

### 🟡 4. `tables/flexible.py` — re-export غير مطلوب

**الملف:** `ui/widgets/tables/flexible.py` (doc 12)

**الكود الحالي:**
```python
from ..utils.tooltip import refresh_tooltips  # noqa: F401
```

هذا السطر يُعيد تصدير `refresh_tooltips` من `utils/tooltip.py`. أي مستخدم يستوردها من `flexible.py` يعتمد على re-export غير مباشر.

**الإصلاح:** حذف السطر. كل من يحتاج `refresh_tooltips` يستورد مباشرة:
```python
from ui.widgets.utils.tooltip import refresh_tooltips
```

---

### 🟠 5. `core/colors.py` — circular import مخفي

**الملف:** `ui/widgets/core/colors.py` (doc 58)

**المشكلة:** `status_colors()` تعمل lazy import من `ui.app_settings`:
```python
def status_colors(level: str) -> dict[str, str]:
    from ui.app_settings import _C   # ← lazy import داخل الدالة
```

لكن `ui/theme.py` يستورد من `ui.theme_manager` الذي يستورد من `ui.theme`. هذه الدوائر محمية بالـ lazy import، لكن `ui.app_settings` غير موجود كملف منفصل في المستندات — `_C` معرّف في `ui/theme.py` وليس `ui/app_settings`.

**التأثير:** لو `ui.app_settings` هو alias أو re-export من `ui.theme`، فكل استدعاء لـ `status_colors()` يستورد من مكانين مختلفين يشيران لنفس الشيء.

**الإصلاح:** توحيد الاستيراد:
```python
def status_colors(level: str) -> dict[str, str]:
    from ui.theme import _C  # المصدر الوحيد الصحيح
```

---

### 🟠 6. `mixins/service.py` — إنشاء instance جديد في كل استدعاء بدون تحذير

**الملف:** `ui/widgets/mixins/service.py` (doc 6)

**المشكلة:** التعليق يقول "هذا مقصود" لكن الكود لا يُحذّر لو استُدعيت الـ property عشر مرات في method واحدة:
```python
@property
def _item_service(self):
    from services.shared.item_service import ItemService
    return ItemService(self.conn)  # instance جديد في كل استدعاء
```

**التوصية:** إضافة تحذير في الـ docstring وإضافة helper للحالات التي تحتاج instance واحد:
```python
@property
def _item_service(self):
    """
    يُعيد instance جديد في كل استدعاء — مقصود لتجنب stale connection.
    لو تحتاج استدعاءات متعددة في نفس الـ method، احفظ في متغير:
        svc = self._item_service
        svc.add(...)
        svc.list_by_type(...)
    """
    from services.shared.item_service import ItemService
    return ItemService(self.conn)
```

---

### 🟡 7. `combo/category.py` — lambda تُنشئ closure قد تُسبب memory leak

**الملف:** `ui/widgets/combo/category.py` (doc 17)

**الكود الحالي:**
```python
bus.company_data_changed.connect(
    lambda _: self.refresh(), Qt.UniqueConnection
)
```

Lambda تحمل reference لـ `self` مما يمنع garbage collection للـ widget بعد حذفه. الـ `UniqueConnection` يحمي من التكرار لكن لا يحل مشكلة الـ dangling reference.

**الإصلاح:**
```python
import weakref

_weak = weakref.ref(self)
def _on_company_changed(_cid: int):
    obj = _weak()
    if obj is not None:
        obj.refresh()

bus.company_data_changed.connect(_on_company_changed, Qt.UniqueConnection)
```

---

## ثالثاً: انتهاكات الهيكلة المطلوبة

### الهيكل المستهدف:
```
widgets/ (base classes) → tabs/UI ──→ services/ ──→ repos/ (db/) ← schema/
```

---

### 🔴 8. `component_row/variants.py` — يستورد من `db/` مباشرة بدون المرور بـ `services/`

**الملف:** `ui/widgets/components/component_row/variants.py` (doc 4)

```python
def _fetch_variants(self, item_id: int) -> list:
    from db.costing.raw_variants_repo import fetch_variants_for_item  # ← db مباشرة
    conn = self._get_conn()
    return fetch_variants_for_item(conn, item_id)

def _calc_variant_unit_cost(self, variant_id, item_id):
    from db.costing.raw_variants_repo import fetch_variant  # ← db مباشرة
    conn = self._get_conn()
    var = fetch_variant(conn, variant_id)
```

وأيضاً استعلام SQL مباشر:
```python
def _get_item_price(self, item_id: int) -> float:
    row = conn.execute(
        "SELECT price FROM items WHERE id=?", (item_id,)  # ← SQL مباشر في widget!
    ).fetchone()
```

**الانتهاك:** widget تستورد من `db/` مباشرة وتكتب SQL. يجب المرور بـ `services/`.

**الإصلاح المطلوب:** إنشاء `services/costing/variant_service.py` يحتوي على:
- `get_variants_for_item(conn, item_id) -> list`
- `get_variant_unit_cost(conn, variant_id, item_id) -> float | None`
- `get_item_price(conn, item_id) -> float`

ثم `variants.py` يستورد من الـ service فقط.

---

### 🔴 9. `component_row/op_rows.py` — يستورد من `db/` مباشرة

**الملف:** `ui/widgets/components/component_row/op_rows.py` (doc 70)

```python
def _fetch_op_rows(self, op_id: int) -> list:
    from db.costing.machine_op_rows_repo import fetch_op_rows  # ← db مباشرة

def _calc_row_cost(self, row_id: int) -> float:
    from db.costing.machine_op_rows_repo import calc_op_row_cost  # ← db مباشرة
```

**الإصلاح المطلوب:** إنشاء أو توسيع `services/costing/machine_op_service.py` بـ:
- `get_op_rows(conn, op_id) -> list`
- `get_op_row_cost(conn, row_id) -> float`

---

### 🔴 10. `managers/category.py` — يستورد من `db/` مباشرة

**الملف:** `ui/widgets/managers/category.py` (doc 9)

```python
from db.shared.categories_repo import (
    fetch_all_categories, fetch_category, insert_category,
    update_category, delete_category, count_category_items,
    build_tree, fetch_descendants,
)
```

الـ widget يستورد 8 دوال من `db/` مباشرة رغم وجود `CategoryService` في `services/`.

**الوضع الحالي:** الكود يستخدم بعض الدوال مباشرة وبعضها عبر `CategoryService`:
```python
# مباشر (خطأ)
rows = fetch_all_categories(conn, self.scope)
item = fetch_category(conn, cat_id)
excluded = set(fetch_descendants(conn, exclude_id))
counts = count_category_items(conn, node["id"])

# عبر service (صح)
CategoryService(conn).add(...)
CategoryService(conn).update(...)
CategoryService(conn).delete_cascade(cat_id)
```

**الإصلاح المطلوب:** نقل `fetch_all_categories`, `fetch_category`, `fetch_descendants`, `count_category_items`, `build_tree` إلى `CategoryService` كـ methods، ثم استبدال الاستدعاءات المباشرة بـ service calls.

---

### 🔴 11. `combo/category.py` — يستورد من `db/` مباشرة

**الملف:** `ui/widgets/combo/category.py` (doc 17)

```python
from db.shared.categories_repo import fetch_all_categories, build_tree
```

**الإصلاح:** استيراد من `services/shared/category_service.py` أو إنشاء `CategoryService.get_all_tree(conn, scope)`.

---

### 🔴 12. `panels/filter.py` — يستورد من `combo/category.py` بدل `services/`

**الملف:** `ui/widgets/panels/filter.py` (doc 42)

```python
from ..combo.category import populate_category_combo
```

`populate_category_combo` نفسها تستورد من `db/` مباشرة. الـ filter panel يعتمد على widget آخر يعتمد على db — سلسلة غير مباشرة.

**الإصلاح:** `populate_category_combo` يجب أن تستورد من `services/` أو تُنقل لـ service مباشرة.

---

### 🟠 13. `shared/list_panel_with_shared.py` — FILTER_SCOPE ثابت "all" بدل استخدام SHARED_TYPE

**الملف:** `ui/widgets/shared/list_panel_with_shared.py` (doc 48)

```python
FILTER_SCOPE: str = "all"  # ← كل subclass تُعرّف SHARED_TYPE لكن FILTER_SCOPE لا يستخدمه
```

كل subclass تُعرّف `SHARED_TYPE = "raw"` مثلاً، لكن الـ filter يعرض كل التصنيفات بدل تصنيفات النوع المحدد.

**الإصلاح:**
```python
def _build_filter(self) -> "FilterToolbar | None":
    scope = getattr(self, "SHARED_TYPE", self.FILTER_SCOPE)
    toolbar = FilterToolbar(
        conn=self.conn,
        scope=scope,  # ← استخدام SHARED_TYPE بدل FILTER_SCOPE الثابت
        ...
    )
```

---

### 🟠 14. `base/tab_section.py` يستورد `get_connection` من `db/shared/connection` مباشرة

**الملف:** `ui/widgets/base/tab_section.py` (doc 14)

```python
from db.shared.connection import get_connection
# ...
self.conn = (conn_fn or get_connection)()
```

هذا مقبول كـ bootstrap للـ section، لكن يجب توثيقه كاستثناء من القاعدة.

---

## رابعاً: ملفات في مسار غير منطقي

### 15. `panels/form_badges.py`, `form_labels.py`, `form_fields.py`, `form_group.py`, `form_buttons.py`

هذه ملفات **components** لكنها في مجلد `panels/`. المسار المنطقي هو `components/forms/` أو `forms/`.

**التأثير:** لا يُسبب أخطاء لكن يُربك من يبحث عن مكوّن معين.

**التوصية:** نقل تدريجي عند الـ refactor القادم.

---

### 16. `forms/inputs.py` في مجلد `forms/` لكن يحتوي على input widgets عامة

`AmountSpinBox`, `DateField`, `StyledComboBox` هي widgets عامة وليست مرتبطة بالفورمات فقط. المسار المنطقي `components/inputs.py` أو `widgets/inputs.py`.

---

## خامساً: ملخص الأولويات

| # | الملف | النوع | الأولوية | التأثير |
|---|-------|-------|----------|---------|
| 1 | `forms/inputs.py` | Import خاطئ | 🔴 فوري | RuntimeError |
| 2 | `core/conn.py` | Logic خاطئ | 🔴 فوري | شرط مستحيل في else |
| 3 | `component_row/variants.py` | انتهاك هيكلة | 🔴 هيكلة | SQL في widget |
| 4 | `component_row/op_rows.py` | انتهاك هيكلة | 🔴 هيكلة | db import في widget |
| 5 | `managers/category.py` | انتهاك هيكلة | 🔴 هيكلة | 8 db imports مباشرة |
| 6 | `combo/category.py` | انتهاك هيكلة | 🔴 هيكلة | db import في widget |
| 7 | `core/colors.py` | Import مشبوه | 🟠 مهم | `ui.app_settings` غير موجود |
| 8 | `dialogs/settings_dialog.py` | Import re-export | 🟡 تنظيمي | يعمل لكن غير مباشر |
| 9 | `tables/flexible.py` | Re-export | 🟡 تنظيمي | يعمل لكن غير مباشر |
| 10 | `combo/category.py` | Memory leak | 🟠 مهم | lambda تحمل self |
| 11 | `shared/list_panel_with_shared.py` | FILTER_SCOPE خاطئ | 🟠 منطقي | فلتر بتصنيفات خاطئة |
| 12 | `mixins/service.py` | توثيق ناقص | 🟡 تنظيمي | لا يُسبب خطأ |

---

## سادساً: الخطوات التالية لاستكمال الهيكلة

### المرحلة 1 — إصلاح الاستيرادات الخاطئة (فوري)
1. `forms/inputs.py`: تغيير مسار import
2. `core/conn.py`: إصلاح الشرط المستحيل في `_get_safe_conn`
3. `dialogs/settings_dialog.py`: استيراد من `unit_service` مباشرة
4. `tables/flexible.py`: حذف سطر re-export
5. `core/colors.py`: التحقق من `ui.app_settings` وتوحيده مع `ui.theme`

### المرحلة 2 — نقل منطق الـ DB إلى services (هيكلة)
1. إنشاء `services/costing/variant_service.py`
2. إنشاء/توسيع `services/costing/machine_op_service.py`
3. توسيع `services/shared/category_service.py` بإضافة:
   - `get_all_categories(conn, scope) -> list`
   - `get_all_tree(conn, scope) -> list`
   - `get_descendants(conn, cat_id) -> set`
   - `count_items(conn, cat_id) -> dict`
4. تحديث الـ widgets لاستخدام الـ services الجديدة

### المرحلة 3 — إصلاح الـ memory leak وتحسين الكود
1. `combo/category.py`: استبدال lambda بـ weakref
2. `shared/list_panel_with_shared.py`: استخدام SHARED_TYPE في الفلتر
3. توثيق `mixins/service.py`