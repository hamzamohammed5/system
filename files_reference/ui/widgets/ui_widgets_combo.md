# دليل الكود — UI / Widgets: Combo

> `ui/widgets/combo/` — قوائم اختيار (QComboBox) موحّدة: وحدات القياس والتصنيفات.
>
> ⚠️ **[تصحيح تسمية/تقسيم]** هذا الملف كان مدموجاً سابقاً مع `panels/` و
> `forms/` في ملف واحد (`ui_widgets_panels.md`) — مخالفة لقاعدة "مرجع واحد
> = مسار واحد". تم فصله هنا ليغطي `ui/widgets/combo/` فقط.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Combos — Unit](#combos--unit) | `combo/unit.py` |
| [Combos — Category](#combos--category) | `combo/category.py` |

---

## Combos — Unit

### `ui/widgets/combo/unit.py`

**الغرض:** `QComboBox` موحّد لاختيار وحدة القياس، مع تحميل من الإعدادات،
حفظ آخر اختيار تلقائياً، و fallback للوحدات الافتراضية.

> ⚠️ **[تصحيح مسار]** منطق الـ business logic (`load_units`, `add_unit`, ...)
> **ليس** في `ui/widgets/combo/unit_service.py` — هذا الملف غير موجود ضمن
> `ui/widgets/`. المصدر الفعلي هو `services/shared/unit_service.py`
> (خارج نطاق هذا المرجع — يُغطّى في `services_shared.md`). هذا الملف
> (`combo/unit.py`) يحتوي فقط على الـ widget + `make_unit_combo`.

**Imports:**
```python
from PyQt5.QtCore import pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedComboBox
from ..utils.signals import blocked_signals
from services.shared.unit_service import (
    load_units, invalidate_units_cache,
    get_last_unit, set_last_unit,
    _default_units,
)
```

**من يستدعي هذا الملف:** `ui/widgets/dialogs/settings_dialog.py` يستورد
دوال الـ service (`load_units`, `add_unit`, `remove_unit`,
`reset_units_to_default`, `_default_units`, `_DEFAULT_UNIT_KEYS`) مباشرة
من `services/shared/unit_service.py` — لا يستورد من `combo/unit.py` نفسه؛
غير محدد بثقة أي ملف آخر يستدعي `UnitCombo`/`make_unit_combo` من المرفقات
الحالية.

---

### `UnitCombo(ThemedComboBox)`

```python
UnitCombo(conn, last_key: str = None, current: str = None, parent=None)
```
- يرث من `ThemedComboBox` مباشرة — **لا** `WidgetMixin` منفصل (يعتمد على أن `ThemedComboBox` نفسها بالفعل `WidgetMixin`).
- **Class-level attribute:** `unit_changed = pyqtSignal(str)`.
- `__init__`: يحفظ `_conn`, `_last_key`. يستدعي `self._populate()`. لو `current` مُمرَّر → `self.set_unit(current)`. وإلا لو `last_key` مُمرَّر → `self.set_unit(get_last_unit(conn, last_key))`. يربط `currentIndexChanged.connect(self._on_changed)`.
- `._populate()`: يحفظ `prev = self.currentData()`. داخل `blocked_signals(self)`: `self.clear()` ثم لكل `(val, label)` من `load_units(self._conn)` → `self.addItem(label, val)`. بعد الخروج من الـ context manager: لو `prev` موجود → `self.set_unit(prev)` لإعادة الاختيار السابق.
- `.refresh()`: "يعيد تحميل الوحدات بعد تغيير من الإعدادات" — يستدعي `invalidate_units_cache(self._conn)` ثم `self._populate()`.
- `.current_unit() -> str`: يرجع `self.currentData() or "cm"`.
- `.set_unit(unit: str)`: يبحث عن `unit` بين كل الـ items (`itemData(i) == unit`) ويضبط `setCurrentIndex(i)`. لو لم يجد وكان هناك عناصر (`self.count()`) → `setCurrentIndex(0)` كـ fallback.
- `._on_changed(_)`: يستدعي `self.current_unit()`. لو `self._last_key` و `self._conn` موجودان → `set_last_unit(self._conn, self._last_key, unit)` (حفظ آخر اختيار). ثم `self.unit_changed.emit(unit)`.

---

### `make_unit_combo(conn=None, current="cm", last_key=None) -> ThemedComboBox`

- لو `conn is not None` → يبني `UnitCombo(conn, last_key=last_key, current=current)`.
- لو `conn is None` → يبني `ThemedComboBox` عادي (بدون DB) ويملأه مباشرة من `_default_units()`.
- في الحالتين: بعد البناء، يمر على كل الـ items ويضبط `setCurrentIndex` ليطابق `current` (بحث `itemData(i) == current` ثم `break`).

---

## Combos — Category

### `ui/widgets/combo/category.py`

**الغرض:** `QComboBox` للتصنيفات الهرمية مع تحديث تلقائي عند تغيير بيانات
الشركة النشطة أو اللغة.

**Imports:**
```python
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor
from ui.widgets.panels.themed_inputs import ThemedComboBox
from ..core.conn              import LiveConnMixin
from ..utils.signals          import blocked_signals
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n     import tr
```

**من يستدعي هذا الملف:** `populate_category_combo()` مُستخدمة مباشرة من
`ui/widgets/panels/filter.py` (`FilterToolbar._reload_categories`) و من
`ui/widgets/managers/category.py` (`CategoryForm._refresh_parent_combo`)
— كلاهما يستوردها من هذا الملف بدل بناء منطق التصنيفات الهرمية بأنفسهم.

---

### `populate_category_combo(combo, conn, scope="all", all_label=None) -> None`

- دالة مستقلة (top-level) — تُستخدم من `CategoryCombo` وأي widget آخر يحتاج ملء combo بالتصنيفات.
- `all_label=None` → يُستخدم `tr('filter_all')` تلقائياً.
- لو `all_label` غير فارغ (بعد الحل الافتراضي) → يُضاف كأول خيار: `combo.addItem(all_label, None)` ثم `combo.setItemData(0, QColor(_C['bg_input']), Qt.BackgroundRole)`.
- **[إصلاح هيكلة]** يستخدم `CategoryService` بدل استيراد `db/` مباشرة:
  ```python
  from services.shared.category_service import CategoryService
  svc   = CategoryService(conn)
  rows  = svc.get_all(scope)
  nodes = svc.build_tree(rows)
  ```
- أي استثناء أثناء الجلب → `return` بصمت (لا عناصر تُضاف بعد `all_label`).
- يستدعي `_add_nodes(combo, nodes, depth=0)` لبناء الشجرة.

### `_add_nodes(combo, nodes: list, depth: int) -> None`

- دالة داخلية recursive تبني عناصر التصنيفات الهرمية داخل الـ combo.
- `indent = "    " * depth` | `arrow = tr('tree_node_arrow')` لو `depth > 0` وإلا `""`.
- لكل عقدة: `combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])`.
- لون النص (`Qt.ForegroundRole`) = `QColor(node["color"])`.
- لون الخلفية (`Qt.BackgroundRole`) = `QColor(_C['bg_input'])` صراحةً — **[إصلاح خلفية سوداء عند الاختيار]** بعض توليفات Qt/Windows ترسم خلفية التحديد بمحرك الرسم الأصلي للنظام متجاهلة الـ QSS، فيتعارض مع `ForegroundRole` المخصص ويظهر تباين غامق تقريباً أسود؛ تحديد خلفية فاتحة ثابتة يمنع الاعتماد على أي رسم افتراضي غير متوقع.
- لو `node["children"]` موجودة → استدعاء recursive بـ `depth + 1`.

---

### `CategoryCombo(ThemedComboBox, LiveConnMixin, WidgetMixin)`

```python
CategoryCombo(conn, scope: str = "all", parent=None)
```
- **[إصلاح 2]** يسمع لـ `bus.company_data_changed` فقط — `bus.data_changed` القديم محذوف تماماً (لم يعد يوجد signal منفصل غير مقيّد بالشركة).
- `__init__`: يحفظ `self.conn`, `self.scope`. يستدعي `self.refresh()` فوراً، **ثم** `self._init_widget_mixin(theme=False, font=False, lang=True, data=True)`.
- **[WidgetMixin]** الربط بالـ bus بالكامل عبر `_init_widget_mixin` — لا `weakref` يدوي منفصل ولا slot مخصص؛ الـ mixin يدير الـ `weakref` و `Qt.UniqueConnection` داخلياً بالكامل (استبدل النمط اليدوي القديم بالكامل).
- `lang=True` مطلوبة لأن `populate_category_combo`/`_add_nodes` تستخدمان `tr()` (`filter_all` + `tree_node_arrow`) — فالكومبو يجب أن يتحدث عند تغيير اللغة.
- `theme=False, font=False` — الكومبو لا يحتاج إعادة رسم ستايل خاص به عند تغيير الثيم (يعتمد على ستايل `ThemedComboBox` الأساسي).

**Methods:**
```python
._refresh_data(company_id=None)   # [WidgetMixin hook] = self.refresh()
._refresh_lang(*_)                # [WidgetMixin hook] = self.refresh()

.refresh()
# 1. self._live_conn() (من LiveConnMixin) — لو فشل (Exception) → return بصمت
# 2. prev = self.currentData()
# 3. داخل blocked_signals(self): self.clear() ثم populate_category_combo(self, conn, self.scope)
# 4. يمر على كل العناصر ويعيد اختيار prev لو لا يزال موجوداً (itemData(i) == prev)

.get_category() -> int | None
# = self.currentData()

.set_category(cat_id)
# يبحث عن cat_id بين العناصر ويضبط setCurrentIndex
# لو لم يجد → setCurrentIndex(0) (fallback)
```

---

## ملاحظات عامة

- كلا الملفين (`unit.py`, `category.py`) يعتمدان على `ThemedComboBox` من
  `panels/themed_inputs.py` كأساس، بدل `QComboBox` الخام.
- `category.py` هو الوحيد من الاثنين الذي يرث `WidgetMixin` صراحةً ويشترك
  في أحداث الـ bus؛ `unit.py` (`UnitCombo`) يعتمد ضمنياً على أن
  `ThemedComboBox` نفسها بالفعل `WidgetMixin` لكن لا يستدعي
  `_init_widget_mixin` بنفسه ولا يوفر `_refresh_data`/`_refresh_lang` —
  التحديث في `UnitCombo` يتم يدوياً عبر `.refresh()` فقط، وليس تلقائياً
  عند أحداث الـ bus.

---

## علاقات الملفات

- `combo/unit.py` يستورد دوال من `services/shared/unit_service.py` (خارج نطاق هذا المرجع — يُغطّى في `services_shared.md`)، و `blocked_signals` من `utils/signals.py` (مرجع: `ui_widgets_utils.md`).
- `combo/category.py` يستورد `LiveConnMixin` من `core/conn.py` (مرجع: `ui_widgets_core.md`)، `CategoryService` من `services/shared/category_service.py` (خارج النطاق)، و `blocked_signals` من `utils/signals.py`.
- كلاهما يستورد `ThemedComboBox` من `panels/themed_inputs.py` (مرجع: `ui_widgets_panels.md`).
- `combo/category.py` (`populate_category_combo`) يُستخدم من ملفات خارج هذا المسار: `panels/filter.py` و `managers/category.py`.
