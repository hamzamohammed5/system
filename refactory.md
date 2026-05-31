# تقرير المراجعة الشاملة للكود

---

## 1. Re-exports وتوزيع الوظائف على أكثر من ملف

### 1.1 `combo/unit.py` — re-export كامل من `unit_service.py`

**الملف:** `ui/widgets/combo/unit.py`

الملف يُعيد تصدير كل وظائف `unit_service.py` بـ `noqa: F401`:
```python
from .unit_service import (  # noqa: F401
    _DEFAULT_UNITS, _cache_key, invalidate_units_cache,
    load_units, save_units, get_last_unit, set_last_unit,
    add_unit, remove_unit, get_all_units, reset_units_to_default,
)
```
كل من يستورد `load_units` من `combo/unit.py` بدل `combo/unit_service.py` يعتمد على re-export غير مباشر.

**ملفات تستورد من المسار الخاطئ:**
- `dialogs/settings_dialog.py` يستورد `load_units, add_unit, remove_unit, reset_units_to_default, _DEFAULT_UNITS` من `ui.widgets.combo.unit` — وهو re-export وليس المصدر.

**الإصلاح:** `settings_dialog.py` يجب أن يستورد من `ui.widgets.combo.unit_service` مباشرة.

---

### 1.2 `tables/flexible.py` — re-export لـ `refresh_tooltips`

**الملف:** `ui/widgets/tables/flexible.py`

```python
from ..utils.tooltip import refresh_tooltips  # noqa: F401
```
`refresh_tooltips` معرّفة في `utils/tooltip.py` لكن `flexible.py` يُعيد تصديرها. أي كود يستورد من `flexible.py` يعتمد على re-export.

**الإصلاح:** حذف هذا السطر من `flexible.py`. كل مستخدمي `refresh_tooltips` يستوردون مباشرة من `utils/tooltip.py`.

---

### 1.3 `components/label.py` — re-export من `progress.py` و `amount_label.py`

**الملف:** `ui/widgets/components/label.py`

```python
from .progress    import ProgressBar, MultiProgressBar           # noqa: F401
from .amount_label import (                                       # noqa: F401
    AmountLabel, DebitCreditDisplay, BalanceDisplay,
    format_amount, amount_color, dr_cr_color,
)
```
ثلاثة ملفات تتقاسم وظيفة تُصدَّر من ملف رابع. المصادر الحقيقية هي `progress.py` و `amount_label.py` لكن الكود القديم يستورد من `label.py`.

**الإصلاح:** ليس عاجلاً (legacy compat)، لكن يجب توثيق أن `label.py` هو ملف compat وليس المصدر.

---

## 2. استدعاءات لملفات خاطئة (مسارات Import خاطئة)

### 2.1 `forms/inputs.py` — استيراد من مسارين مختلفين لنفس الدالة

**الملف:** `ui/widgets/forms/inputs.py`

```python
from ui.font  import fs, get_font_size
from ..core   import get_font_size as _get_font_size   # ← مكرر!
from ..theme.styles  import input_style as _input_style, spinbox_style as _spinbox_style
```

**مشكلتان:**
1. `get_font_size` تُستورد مرتين: من `ui.font` (مباشر) وأيضاً من `..core` (alias). الاستيراد من `..core` مجهول المصدر — `ui/widgets/core/__init__.py` يجب أن يُعيد تصديرها من مكان ما.
2. `from ..theme.styles import input_style, spinbox_style` — `theme/styles.py` محذوف بعد Refactor V3. يجب أن يكون `from ..theme.input_styles import input_style, spinbox_style`.

**الإصلاح:**
```python
from ui.font               import fs, get_font_size
from ..theme.input_styles  import input_style as _input_style, spinbox_style as _spinbox_style
# حذف: from ..core import get_font_size as _get_font_size
```

---

### 2.2 `widgets/mixins/service.py` — lazy imports داخل properties

**الملف:** `ui/widgets/mixins/service.py`

كل property تعمل lazy import:
```python
@property
def _item_service(self):
    from services.shared.item_service import ItemService
    return ItemService(self.conn)
```
هذا **مقصود** لكن يعني إنشاء instance جديد في كل وصول. التعليق في الملف يقول "هذا مقصود" لكن لا يوجد caching. إذا استُدعي `_item_service` عشر مرات في method واحدة ستُنشأ عشرة instances.

**توصية:** إضافة تعليق تحذيري أو cache اختياري:
```python
@property
def _item_service(self):
    from services.shared.item_service import ItemService
    return ItemService(self.conn)  # instance جديد في كل استدعاء — مقصود
```
(لا يحتاج إصلاح فوري إذا كان مقصوداً، لكن يحتاج توثيق أوضح.)

---

## 3. وظائف متقسمة على ملفين

### 3.1 `spinbox_style` — معرّفة في `input_styles.py` لكن `forms/inputs.py` تستوردها من مسار خاطئ

كما ذُكر في 2.1 — `forms/inputs.py` يستورد من `..theme.styles` المحذوف. الوظيفة موجودة في `input_styles.py` فقط.

---

### 3.2 `status_colors` — معرّفة في `core/colors.py` لكن تُستدعى من أماكن متعددة

**الملف:** `ui/widgets/core/colors.py`

`status_colors()` معرّفة هنا وتعمل lazy import من `ui.app_settings._C`. هذا صح، لكن بعض الملفات تستورد `_C` مباشرة وتبني ألوان status يدوياً بدل استخدام `status_colors()`. مثال في `notification.py`:
```python
cfg = status_colors(level)  # صح
```
لكن في `progress.py`:
```python
s_success = status_colors("success")
s_warning = status_colors("warning")
s_danger  = status_colors("danger")
```
هذا صح أيضاً. لا مشكلة هنا — المستخدمون يستخدمون الـ API المناسب.

---

## 4. ملفات في مسار غير منطقي

### 4.1 `ui/widgets/forms/inputs.py`

اسم المجلد `forms/` لكن الملف يحتوي على input **widgets** عامة (spinboxes, combos, date fields) وليس forms بالمعنى الكامل. الـ widgets الأخرى في `components/`. هذا تنظيمي، ليس خطأ وظيفياً.

---

### 4.2 `ui/widgets/panels/form_badges.py` و `form_labels.py` و `form_fields.py` و `form_group.py` و `form_buttons.py`

كل هذه الملفات في مجلد `panels/` لكنها في الحقيقة **مكونات** للفورمات. الموقع المنطقي لها هو `components/` أو `forms/`. هذا قرار تصميمي قديم، ليس خطأ وظيفياً.

---

## 5. أخطاء منطقية

### 5.1 `widget.py` — `_on_catalog_changed` لا تستدعي `_refresh_cost_label` عند تغيير النوع

**الملف:** `ui/widgets/components/component_row/widget.py`

```python
def _on_catalog_changed(self):
    # ...
    self._refresh_items()
    self._refresh_cost_label()  # ← يُستدعى
```

لكن `_on_type_changed` لا تستدعي `_refresh_cost_label`:
```python
def _on_type_changed(self, _):
    # ...
    self._fill_items(new_type, selected_id=None)
    self._update_total_qty_visibility(new_type)
    if new_type != "raw":
        self.total_qty_edit.clear()
        self._hide_variants()
    if new_type != "machine_op":
        self._hide_op_rows()
    # ← مفقود: self._refresh_cost_label() أو على الأقل إخفاء الـ label
```

عند تغيير النوع من "raw" لـ "semi"، تبقى `lbl_variant_cost` تعرض تكلفة الخامة القديمة حتى يتم refresh الـ catalog.

**الإصلاح:** في `_on_type_changed` بعد `_hide_variants()`:
```python
if new_type != "raw":
    self.total_qty_edit.clear()
    self._hide_variants()
    # إخفاء label التكلفة عند تغيير النوع
    if hasattr(self, "lbl_variant_cost"):
        self.lbl_variant_cost.setVisible(False)
```

---

### 5.2 `op_rows.py` — `_determine_target_id` أولوية خاطئة

**الملف:** `ui/widgets/components/component_row/op_rows.py`

```python
def _determine_target_id(self, selected_row_id: int = None) -> "int | None":
    return (
        selected_row_id
        or self._init_machine_op_row_id
        or self._pinned_op_row_id
    )
```

المشكلة: لو `selected_row_id = 0` (صفر)، الشرط `or` سيتخطاه ويذهب للقيمة التالية. هذا خطأ منطقي في Python — `0 or x` يُعطي `x`. لكن IDs في SQLite تبدأ من 1، فعلياً `0` لا يُستخدم كـ valid ID. لكن النمط نفسه خطر.

**توصية:** تغيير لـ `is not None` checks:
```python
def _determine_target_id(self, selected_row_id: int = None) -> "int | None":
    if selected_row_id is not None:
        return selected_row_id
    if self._init_machine_op_row_id is not None:
        return self._init_machine_op_row_id
    return self._pinned_op_row_id
```

---

### 5.3 `variants.py` — `_calc_variant_unit_cost` تُعيد قراءة الـ DB بعد قراءة أخرى

**الملف:** `ui/widgets/components/component_row/variants.py`

`_populate_variant_combo` تحسب `item_price` من `_get_item_price(item_id)` وتضعها في الـ label. ثم `_calc_variant_unit_cost` تُعيد استدعاء `_get_item_price` مرة أخرى داخلياً:

```python
def _calc_variant_unit_cost(self, variant_id, item_id):
    # ...
    item_price = self._get_item_price(item_id)  # ← query DB مرة ثانية
```

لو الـ price تغيّر بين الاستدعاءين (نادر لكن ممكن) ستكون قيمة الـ label مختلفة عن المحسوبة. الأهم: overhead query غير ضروري.

**توصية:** تمرير `item_price` كـ parameter بدل إعادة حسابه.

---

### 5.4 `BusConnectedMixin._on_company_data_changed` — `_cached_company_id` يُضبط قبل التحقق

**الملف:** `ui/widgets/mixins/bus.py`

```python
def _on_company_data_changed(self, company_id: int):
    if self._cached_company_id is None:
        self._cached_company_id = self._get_active_company_id()

    if self._cached_company_id is None:
        self._cached_company_id = company_id
        # لا نرجع — نتابع لتنفيذ التحديث

    elif company_id != self._cached_company_id:
        logger.debug(...)
        return

    self._refresh_guard = True
    self._on_data_changed()
```

**المشكلة المنطقية:** عند أول استدعاء مع `_cached_company_id = None`:
- نضبط `_cached_company_id = company_id` (من الإشعار)
- لا نرجع → ننفذ `_on_data_changed()` — **صح**

لكن في الاستدعاء الثاني بنفس `company_id`:
- `_cached_company_id == company_id` → الـ `elif` لا يُطبَّق → ننفذ `_on_data_changed()` — **صح**

في الاستدعاء الثاني بـ `company_id` مختلف:
- `elif company_id != self._cached_company_id` → نرجع — **صح**

المنطق سليم. لكن هناك حالة edge: لو widget يُنشأ بعد أن تغيرت الشركة وقبل أن يُستقبل أي إشعار، الـ `_cached_company_id` سيبقى None حتى أول إشعار. إذا كان أول إشعار لشركة مختلفة، سيُضبط `_cached_company_id` على الشركة الجديدة وسيُنفذ التحديث — وهو سلوك صح.

**لا مشكلة هنا.**

---

### 5.5 `list_panel.py` — `refresh()` يستدعي `_apply_filter()` مباشرة بعد `_filter_toolbar.reload()`

**الملف:** `ui/widgets/base/list_panel.py`

```python
def refresh(self):
    self._all_rows = self._load_rows()
    if self._filter_toolbar and self.conn:
        self._filter_toolbar.reload(self.conn)   # ← قد يُطلق filter_changed → _timer.start()
    self._apply_filter()                          # ← تنفيذ مباشر
```

`_filter_toolbar.reload()` يُعيد تحميل categories ويستدعي `_reload_categories()` التي تحذف وتُعيد ملء الـ combo. تغيير الـ combo يُطلق `currentIndexChanged` → `filter_changed` → `_timer.start()`. ثم `refresh()` تستدعي `_apply_filter()` مباشرة، والـ timer يُنفذ `_apply_filter()` مرة أخرى بعد 250ms.

**الإصلاح:**
```python
def refresh(self):
    self._all_rows = self._load_rows()
    if self._filter_toolbar and self.conn:
        self._timer.stop()                        # أوقف أي timer مُجدوَل
        self._filter_toolbar.reload(self.conn)
    self._apply_filter()
```

---

## 6. مشاكل import مخفية

### 6.1 `forms/inputs.py` — استيراد من `..core` بشكل غامض

```python
from ..core import get_font_size as _get_font_size
```

`ui/widgets/core/__init__.py` غير موجود في الملفات المقدمة. لو لم يكن هذا الملف يُعيد تصدير `get_font_size`، سيحدث `ImportError`. الإصلاح: استخدام `from ui.font import get_font_size` مباشرة وحذف هذا الاستيراد.

---

### 6.2 `forms/inputs.py` — استيراد من `..theme.styles` المحذوف

```python
from ..theme.styles import input_style as _input_style, spinbox_style as _spinbox_style
```

`theme/styles.py` محذوف. يجب:
```python
from ..theme.input_styles import input_style as _input_style, spinbox_style as _spinbox_style
```

---

### 6.3 `dialogs/settings_dialog.py` — استيراد من `combo.unit` (re-export) بدل `combo.unit_service`

```python
from ui.widgets.combo.unit import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)
```

هذه الدوال معرّفة في `unit_service.py` و`unit.py` يُعيد تصديرها. الاستيراد المباشر:
```python
from ui.widgets.combo.unit_service import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)
```

---

## 7. تناقضات التوثيق

### 7.1 `conn.py` — `SafeConnMixin._get_safe_conn` لا تزال تستخدم `company_state._get_conn`

**الملف:** `ui/widgets/core/conn.py` (النسخة الأصلية)

```python
def _get_safe_conn(self):
    # ...
    new_conn = company_state._get_conn(self.__safe_db_name)  # ← private API
```

تم إصلاح `tab_section.py` لاستخدام `get_erp_conn()` لكن `SafeConnMixin._get_safe_conn` و`DualConnMixin._get_erp_conn` لا يزالان يستخدمان `company_state._get_conn("erp")`.

**الإصلاح في `conn.py`:**
```python
# في _get_safe_conn:
new_conn = company_state.get_erp_conn()   # لو db_name == "erp"
# أو الاحتفاظ بـ _get_conn لو لا يوجد public API لكل أنواع الـ DB

# في DualConnMixin._get_erp_conn:
new = company_state.get_erp_conn()   # بدل _get_conn("erp")
```

---

### 7.2 `shared/list_panel_with_shared.py` — FILTER_SCOPE ليست ثابتة

**الملف:** `ui/widgets/shared/list_panel_with_shared.py`

```python
FILTER_SCOPE: str  = "all"
```

تُستخدم في `FilterToolbar` لتحديد نطاق التصنيفات. لكن كل subclass تُعرّف `SHARED_TYPE` ("raw"|"machine"|...) وهي أدق من "all". المنطقي تعيين `FILTER_SCOPE = self.SHARED_TYPE` لكن class variables لا تعتمد على class variables أخرى.

**توصية:** تغيير `_build_filter` في `BaseListPanel` ليستخدم `SHARED_TYPE` إذا كان موجوداً:
```python
scope = getattr(self, "SHARED_TYPE", self.FILTER_SCOPE)
```
أو إلزام الـ subclasses بتعريف `FILTER_SCOPE` صراحةً.

---

## 8. ملخص الإصلاحات المطلوبة بالأولوية

### 🔴 فورية (تُسبب runtime errors)

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 1 | `forms/inputs.py` | `from ..theme.styles import ...` — ملف محذوف | `from ..theme.input_styles import ...` |
| 2 | `forms/inputs.py` | `from ..core import get_font_size` — مصدر غامض | `from ui.font import get_font_size` وحذف الـ alias |

### 🟠 مهمة (سلوك خاطئ صامت)

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 3 | `core/conn.py` | `SafeConnMixin._get_safe_conn` و`DualConnMixin._get_erp_conn` يستخدمان private `_get_conn` | استبدال بـ `get_erp_conn()` |
| 4 | `component_row/op_rows.py` | `_determine_target_id` يستخدم `or` بدل `is not None` | استخدام explicit None checks |
| 5 | `base/list_panel.py` | `refresh()` يستدعي `_apply_filter()` مرتين | إيقاف الـ timer قبل `reload()` |
| 6 | `component_row/widget.py` | `_on_type_changed` لا تُخفي `lbl_variant_cost` | إضافة `lbl_variant_cost.setVisible(False)` |

### 🟡 تنظيمية (جودة الكود)

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 7 | `dialogs/settings_dialog.py` | يستورد من re-export `combo.unit` | الاستيراد من `combo.unit_service` مباشرة |
| 8 | `tables/flexible.py` | re-export لـ `refresh_tooltips` | حذف السطر |
| 9 | `component_row/variants.py` | `_calc_variant_unit_cost` تُعيد query الـ DB | تمرير `item_price` كـ parameter |

---

## الملفات التي تحتاج تعديلاً

1. `ui/widgets/forms/inputs.py` — إصلاحان (مسار import خاطئ + استيراد مكرر)
2. `ui/widgets/core/conn.py` — إصلاح private API في SafeConnMixin و DualConnMixin
3. `ui/widgets/components/component_row/op_rows.py` — `_determine_target_id`
4. `ui/widgets/base/list_panel.py` — `refresh()` double apply_filter
5. `ui/widgets/components/component_row/widget.py` — `_on_type_changed` variant cost label
6. `ui/widgets/dialogs/settings_dialog.py` — import من المصدر الصحيح
7. `ui/widgets/tables/flexible.py` — حذف re-export