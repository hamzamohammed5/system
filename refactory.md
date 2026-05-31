# تقرير مراجعة الكود — UI Widgets

---

## ملخص تنفيذي

بعد المراجعة الشاملة لجميع الملفات الـ 82 المقدمة، تم رصد المشاكل التالية مصنفةً حسب الخطورة.

---

## 🔴 مشاكل خطيرة (Critical)

### 1. `variants.py` — استدعاء دالة غير موجودة بالاسم الصحيح

**الملف:** `ui/widgets/components/component_row/variants.py`

**المشكلة:** الدالة `_is_variant_deleted()` تستدعي `self._is_widget_deleted(self.cmb_variant)` وهذا صحيح، لكن `_load_variants()` تستدعي `self._is_variant_deleted()` **بينما في `widget.py` يُستدعى `_load_variants(item_id, initial_variant_id=vid)` بمعامل اسمي `initial_variant_id`** في `_schedule_deferred_loads`، في حين أن التعريف في `variants.py` هو `_load_variants(self, item_id: int, selected_variant_id: int = None)`.

```python
# في widget.py السطر:
s._load_variants(cid, initial_variant_id=vid)   # ← initial_variant_id غير موجود

# التعريف الفعلي في variants.py:
def _load_variants(self, item_id: int, selected_variant_id: int = None):
```

**الخطأ:** `TypeError: _load_variants() got an unexpected keyword argument 'initial_variant_id'`

**الإصلاح:** تغيير الاستدعاء في `widget.py` إلى:
```python
s._load_variants(cid, vid)
# أو
s._load_variants(cid, selected_variant_id=vid)
```

---

### 2. `widget.py` — STYLE_ORPHAN قيمة stale تُستخدم مباشرة

**الملف:** `ui/widgets/components/component_row/widget.py` + `ui.py`

**المشكلة:** في `ui.py` يوجد تعليق صريح:
```python
# للتوافق مع أي كود قديم يستخدم STYLE_ORPHAN مباشرة — يُحسب عند أول import
STYLE_ORPHAN = _orphan_style()
```
لكن `widget.py` يستورد ويستخدم `STYLE_ORPHAN` الثابت:
```python
from .ui import (
    build_row_ui, update_waste_style,
    COMPONENT_TYPES, STYLE_NORMAL, STYLE_ORPHAN,
)
# ...
self.setStyleSheet(STYLE_ORPHAN)   # ← قيمة stale لا تتحدث مع الثيم
```
بينما `ui.py` يوفر `get_orphan_style()` لهذا الغرض تحديداً.

**الإصلاح:**
```python
# في widget.py — _mark_orphan:
self.setStyleSheet(get_orphan_style())
```
واستيراد `get_orphan_style` بدل `STYLE_ORPHAN`.

---

### 3. `filter.py` — استيراد خاطئ للموديول

**الملف:** `ui/widgets/panels/filter.py`

**المشكلة:** الملف يستورد من `...font` و `...theme` بـ relative imports بعمق ثلاث نقاط:
```python
from ...font import fs, get_font_size
from ...theme import _C
```
لكن موقع الملف هو `ui/widgets/panels/filter.py` أي عمق نسبي يصل لـ `ui/` فقط، وليس فوقها. في حين أن بقية الملفات مثل `notification.py` تستورد:
```python
from ui.theme import _C
from ui.font  import fs, get_font_size
```
والملف نفسه يستورد من `..utils.signals` (عمقان) بشكل صحيح. الـ `...` الثلاثة تعني الصعود لـ `ui/` ثم خارجها وهو خطأ يُسبب `ImportError`.

**الإصلاح:**
```python
from ui.font  import fs, get_font_size
from ui.theme import _C
```

---

### 4. `form_fields.py` — استيراد من مسار غير موجود

**الملف:** `ui/widgets/panels/form_fields.py`

**المشكلة:**
```python
from ..theme.styles import spinbox_style
```
لكن `spinbox_style` موجودة في `ui/widgets/theme/input_styles.py` وليس `theme/styles.py` (الذي لم يعد موجوداً بعد الـ Refactor V3). هذا سيُسبب `ImportError`.

**الإصلاح:**
```python
from ..theme.input_styles import spinbox_style
```

---

### 5. `layout_widgets.py` — استيراد من مسار محذوف

**الملف:** `ui/widgets/panels/layout_widgets.py`

**المشكلة:**
```python
from ..theme.card_styles import card_style
```
الملف `card_styles.py` موجود في `ui/widgets/theme/card_styles.py`، والاستيراد نسبي من `panels/` يجب أن يكون `..theme.card_styles` — هذا يبدو صحيحاً. **لكن** الملف أيضاً يستورد:
```python
from ...font import fs, get_font_size
from ...theme import _C
```
نفس مشكلة `filter.py` — ثلاث نقاط خاطئة.

**الإصلاح:**
```python
from ui.font  import fs, get_font_size
from ui.theme import _C
```

---

## 🟠 مشاكل متوسطة (Medium)

### 6. `widget.py` — bus connection لا يستجيب لـ `company_data_changed`

**الملف:** `ui/widgets/components/component_row/widget.py`

**المشكلة:** `_connect_bus()` تربط فقط بـ `bus.data_changed`:
```python
bus.data_changed.connect(self._bus_slot)
```
لكن باقي الـ codebase انتقل لاستخدام `bus.company_data_changed` كما هو موضح في `combo/category.py`:
```python
bus.company_data_changed.connect(lambda _: self.refresh())
```
وفي `BusConnectedMixin` يتم الربط بالاثنين. `ComponentRow` يفوته تحديثات `company_data_changed`.

**الإصلاح:** إضافة ربط بـ `bus.company_data_changed` في `_connect_bus()` و`_disconnect_bus()`.

---

### 7. `op_rows.py` — `_schedule_deferred_loads` تستخدم `self` بدل `s`

**الملف:** `ui/widgets/components/component_row/widget.py`

**المشكلة:** في `_schedule_deferred_loads`:
```python
def _timer_variants():
    s = weak()
    if s is None or self._is_widget_deleted():  # ← self بدل s!
        return
    s._load_variants(cid, initial_variant_id=vid)
```
الشرط `self._is_widget_deleted()` يستخدم `self` القوي وليس `s` الضعيف، مما يُبطل الفائدة من `weakref`. بالإضافة لمشكلة `initial_variant_id` المذكورة في النقطة 1.

**الإصلاح:**
```python
if s is None or s._is_widget_deleted():
    return
s._load_variants(cid, vid)
```

---

### 8. `shared_ops.py` — استيراد `emit_company_data_changed` لكن `data_changed` لا تُطلق

**الملف:** `ui/widgets/mixins/shared_ops.py`

**المشكلة:** الملف يستورد ويستخدم `emit_company_data_changed` في `_edit_shared_item` و`_edit_published_item`، لكن `_publish_item` **لا تستدعيها بعد نجاح النشر**، مما يعني أن الـ UI لن يتحدث بعد عملية النشر.

```python
def _publish_item(self, row, shared_type, item_data, parent=None):
    # ...
    PublishAsSharedDialog(...).exec_()
    central.close()
    # ← مفقود: emit_company_data_changed()
```

**الإصلاح:** إضافة `emit_company_data_changed()` بعد `central.close()` في `_publish_item`.

---

### 9. `crud_form.py` — استخدام `bus.data_changed` القديم بدون company filter

**الملف:** `ui/widgets/base/crud_form.py`

**المشكلة:**
```python
bus.data_changed.emit()
```
يُطلق في `_on_add` و`_on_save` الإشعار العام بدون `company_id`، بينما المعيار الجديد هو `emit_company_data_changed()`. هذا يسبب تحديثاً لكل الـ widgets في كل الشركات.

**الإصلاح:** استبدال `bus.data_changed.emit()` بـ:
```python
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()
```

---

### 10. `tab_section.py` — re-import غير ضروري لـ `get_connection`

**الملف:** `ui/widgets/base/tab_section.py`

**المشكلة:**
```python
from db.shared.connection import get_connection
# ...
self.conn = (conn_fn or get_connection)()
```
`get_connection` يُستورد في أعلى الملف ويُستخدم كـ fallback، وهذا منطقي. لكن المشكلة أن `_is_owned_connection` تستورد `company_state` داخلها:
```python
def _is_owned_connection(conn) -> bool:
    from db.companies.company_state import company_state
    shared = company_state._get_conn("erp")
```
`company_state._get_conn` هي دالة **خاصة (private)** (بادئة `_`)، ويجب استخدام `company_state.get_erp_conn()` بدلاً منها للـ API العام.

**الإصلاح:**
```python
shared = company_state.get_erp_conn()
```

---

### 11. `detail_panel.py` — `CONNECT_BUS = False` افتراضياً مع توثيق مضلل

**الملف:** `ui/widgets/base/detail_panel.py`

**المشكلة:**
```python
CONNECT_BUS: bool = False
# ...
if self.CONNECT_BUS:
    self._connect_bus(data=True, theme=True, lang=True)
```
التوثيق يذكر أن `CONNECT_BUS` اختياري، لكن الـ Panel لا يستجيب لتغييرات البيانات بشكل افتراضي. الـ subclasses التي تنسى تعيين `CONNECT_BUS = True` ستظل صامتة أمام أي تغيير. هذا ليس خطأً صريحاً لكنه ثغرة تصميمية تُسبب أخطاء صعبة الاكتشاف.

**التوصية:** إضافة تحذير في `__init_subclass__` أو تغيير الافتراضي لـ `True`.

---

### 12. `list_panel.py` — `_filter_toolbar.reload()` بعد `_load_rows()` قد يُسبب تحديثاً مزدوجاً

**الملف:** `ui/widgets/base/list_panel.py`

**المشكلة:**
```python
def refresh(self):
    self._all_rows = self._load_rows()
    if self._filter_toolbar and self.conn:
        self._filter_toolbar.reload(self.conn)   # ← يُطلق filter_changed
    self._apply_filter()                          # ← يُطلق _apply_filter مرة أخرى
```
`_filter_toolbar.reload()` يُعيد تحميل التصنيفات وقد يُطلق `filter_changed` signal الذي يبدأ `_timer.start()` → `_apply_filter()`. ثم `refresh()` تستدعي `_apply_filter()` مباشرة. النتيجة: `_apply_filter` قد تُنفذ مرتين.

**الإصلاح:** استخدام `blocked_signals` أو فصل تحميل التصنيفات عن الـ filter signal.

---

## 🟡 مشاكل بسيطة (Minor)

### 13. وظيفة `refresh_tooltips` موزعة على ملفين

**الملفات:** `ui/widgets/utils/tooltip.py` + `ui/widgets/tables/flexible.py`

**الحالة:** `flexible.py` يستورد `refresh_tooltips` من `tooltip.py`:
```python
from ..utils.tooltip import refresh_tooltips  # noqa: F401
```
هذا صحيح نظرياً، لكن الاستيراد بـ `noqa: F401` يعني أنه re-export لاستخدام خارجي. أي كود يستورد من `flexible.py` يحصل على `refresh_tooltips` بالصدفة، مما يعني وظيفة واحدة لها مسارين للاستيراد.

**التوصية:** إزالة الـ re-export من `flexible.py` وتوجيه كل المستخدمين لـ `tooltip.py` مباشرة.

---

### 14. `combo/category.py` — ربط bus داخل `__init__` بدون حماية من التكرار

**الملف:** `ui/widgets/combo/category.py`

**المشكلة:**
```python
bus.data_changed.connect(self.refresh)
bus.company_data_changed.connect(lambda _: self.refresh())
```
لا يوجد `Qt.UniqueConnection` ولا حماية من التكرار. لو أُنشئ instance جديد وأُضيف القديم لـ layout جديدة دون حذفه، كلاهما سيستجيب.

**التوصية:** إضافة `Qt.UniqueConnection` أو ربط في `closeEvent`.

---

### 15. `app_settings.py` — مرجع غير موجود في الكود

**ملاحظة:** عدة ملفات تذكر في تعليقاتها `from ui.app_settings import _C` كـ import قديم تم إصلاحه، لكن لا يوجد ملف `ui/app_settings.py` في الملفات المقدمة. إذا كان هذا الملف موجوداً في المشروع ويُصدّر `_C`، فهو يُسبب ارتباكاً في المصدر الوحيد للألوان. يجب التأكد من حذفه أو أنه مجرد re-export من `ui/theme.py`.

---

### 16. `searchable_combo.py` — `_select_first_real()` تتجاهل `__orphan__`

**الملف:** `ui/widgets/utils/searchable_combo.py`

**المشكلة:**
```python
def _select_first_real(self):
    for i in range(self._proxy_model.rowCount()):
        data = proxy_index.data(Qt.UserRole)
        if (data and data != _SEP and isinstance(data, tuple) and
                data[0] not in ("__sep__", "__orphan__")):
            self.cmb.setCurrentIndex(i)
            return
```
العناصر الـ `orphan` تُضاف في `populate()` قبل باقي العناصر:
```python
grouped.append((self._orphan.display(), ("__orphan__", selected_id), False))
```
لكن `_select_first_real()` تتخطاها وتختار أول عنصر حقيقي. في حالة وجود orphan فقط (كل العناصر محذوفة)، لن يتم اختيار أي عنصر وستبقى الـ combo فارغة بصرياً. هذا سلوك مقصود لكنه قد يُفاجئ المستخدم.

**التوصية:** توثيق هذا السلوك أو معالجة الحالة التي يكون فيها كل العناصر orphans.

---

### 17. `widget.py` — `_on_catalog_changed` تُعيد ضبط `_pinned_type` بشرط غريب

**الملف:** `ui/widgets/components/component_row/widget.py`

**المشكلة:**
```python
def _on_catalog_changed(self):
    valid_types = {k for k, _ in COMPONENT_TYPES}
    if self._pinned_type not in valid_types:
        from_combo = self.cmb_type.currentData()
        if from_combo in valid_types:
            self._pinned_type = from_combo
        else:
            return
```
`_pinned_type` يُعيَّن في كل `_on_type_changed` من قيم `COMPONENT_TYPES` الثابتة، لذا لا يمكن نظرياً أن يكون خارج `valid_types` إلا إذا كان None في البداية. هذا الشرط الدفاعي يُضيف تعقيداً غير ضروري.

---

### 18. `conn.py` — `__init_subclass__` لا تفعل شيئاً فعلياً

**الملف:** `ui/widgets/core/conn.py`

**المشكلة:**
```python
def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    # تحقق بسيط: لو الـ subclass يُعرِّف _conn_attr فلا حاجة للتحذير
    # لو لم يُعرِّفه → يرث القيمة الافتراضية "conn" وهذا مقبول
```
الـ docstring يعد بإصدار تحذيرات لكن التطبيق الفعلي **فارغ تماماً** — لا يفعل سوى استدعاء `super()`. التوثيق مضلل.

**الإصلاح:** إما حذف التعليق والـ docstring المضلل، أو تطبيق التحقق الفعلي.

---

### 19. `data_table.py` — `end_fill` منطق العد خاطئ

**الملف:** `ui/widgets/panels/data_table.py`

**المشكلة:**
```python
def end_fill(self, shown: int = None):
    total   = self.table.rowCount()
    visible = shown if shown is not None else total

    has_data          = visible > 0
    is_filtered_empty = (not has_data) and (total > 0)
```
لو `shown=0` و `total=5`، فـ `is_filtered_empty = True` وهذا صحيح. لكن المشكلة: `total` يُحسب من **الصفوف الموجودة في الجدول** بعد `begin_fill/insert_row`، مما يعني أن `total` يعكس عدد الصفوف المُدرجة فعلاً وليس إجمالي البيانات قبل الفلترة. النتيجة: لو أدرجت 3 صفوف فقط (بعد فلترة من 10)، سيكون `total=3` و`shown=None` → `visible=3` → لن تظهر رسالة "لا نتائج" أبداً حتى لو كانت هناك نتائج مخفية.

---

### 20. `components/button.py` — `invalidate_stylesheet_cache` تُستدعى مرتين عند تغيير الثيم

**الملفات:** `ui/theme.py` + `ui/widgets/components/button.py`

**المشكلة:**
```python
# في theme.py -> apply_theme():
invalidate_stylesheet_cache()   # ← يمسح cache الـ theme

try:
    from ui.widgets.components.button import invalidate_stylesheet_cache as inv_btn
    inv_btn()   # ← يمسح cache الأزرار
```
ثم `AppState.on_font_changed` تستدعي:
```python
cls._invalidate_button_cache()   # ← يمسح cache الأزرار مرة أخرى!
```
وعند تغيير الثيم يُستدعى `apply_theme` ثم قد يُستدعى `AppState.on_font_changed` أيضاً، مما يُسبب مسح مزدوجاً. لا يُسبب خطأً لكنه overhead.

---

## 📋 ملفات تحتاج مراجعة مسارها

| الملف | المشكلة |
|-------|---------|
| `ui/widgets/panels/filter.py` | استيراد `...font` و`...theme` بثلاث نقاط خاطئة |
| `ui/widgets/panels/layout_widgets.py` | نفس المشكلة |
| `ui/widgets/panels/form_fields.py` | `from ..theme.styles import spinbox_style` — المسار غير موجود |

---

## 📊 ملخص الإصلاحات المطلوبة

| الأولوية | العدد | الوصف |
|----------|-------|-------|
| 🔴 خطيرة (تُسبب crash/ImportError) | 5 | يجب إصلاحها فوراً |
| 🟠 متوسطة (سلوك خاطئ صامت) | 7 | يجب إصلاحها |
| 🟡 بسيطة (جودة الكود) | 8 | يُوصى بإصلاحها |

---

## الإصلاحات السريعة (Quick Fixes)

### الإصلاح 1 — `widget.py` سطر `_schedule_deferred_loads`
```python
# قبل
s._load_variants(cid, initial_variant_id=vid)
# بعد
s._load_variants(cid, vid)

# قبل
if s is None or self._is_widget_deleted():
# بعد
if s is None or s._is_widget_deleted():
```

### الإصلاح 2 — `widget.py` استخدام `get_orphan_style()`
```python
# في imports:
from .ui import (
    build_row_ui, update_waste_style,
    COMPONENT_TYPES, STYLE_NORMAL, get_orphan_style,
)

# في _mark_orphan:
self.setStyleSheet(get_orphan_style())
```

### الإصلاح 3 — `filter.py` و `layout_widgets.py`
```python
# استبدال
from ...font import fs, get_font_size
from ...theme import _C
# بـ
from ui.font  import fs, get_font_size
from ui.theme import _C
```

### الإصلاح 4 — `form_fields.py`
```python
# استبدال
from ..theme.styles import spinbox_style
# بـ
from ..theme.input_styles import spinbox_style
```

### الإصلاح 5 — `shared_ops.py` إضافة emit في `_publish_item`
```python
def _publish_item(self, row, shared_type, item_data, parent=None):
    # ... الكود الموجود ...
    PublishAsSharedDialog(...).exec_()
    central.close()
    emit_company_data_changed()   # ← إضافة هذا السطر
```

### الإصلاح 6 — `tab_section.py`
```python
# استبدال
shared = company_state._get_conn("erp")
# بـ
shared = company_state.get_erp_conn()
```

### الإصلاح 7 — `crud_form.py`
```python
# استبدال
bus.data_changed.emit()
# بـ
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()
```