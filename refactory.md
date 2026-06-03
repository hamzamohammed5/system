# خطة تعديل ملفات المراجع

## سبب التعديل
دمج `ui/events.py` في `ui/widgets/core/events.py` مع:
1. حذف `data_changed` signal (لا يوجد حالة بدون company_id)
2. حذف `ui/events.py` كملف مستقل
3. المصدر الوحيد أصبح `ui.widgets.core.events`

---

## التغييرات بالترتيب

---

### 1. `ui_root.md` — قسم events

**المكان:** قسم `## events` → `ui/events.py`

**حذف بالكامل:**
```python
bus.data_changed          # pyqtSignal()     — إشعار عام (للتوافق القديم)
```

**تغيير الاستخدام الصحيح من:**
```python
# ✅ الصح
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()

# ❌ للتوافق القديم فقط
from ui.events import bus
bus.data_changed.emit()
```
**إلى:**
```python
# ✅ الصح — المصدر الوحيد
from ui.widgets.core.events import bus
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.events import get_active_company_id, is_same_company
```

**تغيير عنوان القسم من:**
```
### `ui/events.py`
```
**إلى:**
```
### `ui/widgets/core/events.py`  ← المصدر الوحيد
```

**حذف ملاحظة `ui/events.py` من الـ imports في main_window:**
- كل `from ui.events import bus` → `from ui.widgets.core.events import bus`

---

### 2. `ui_widgets_1_core.md` — قسم Core — Events

**المكان:** قسم `## Core — Events` → `ui/widgets/core/events.py`

**حذف من الـ signals:**
```python
bus.data_changed          # pyqtSignal()     — إشعار عام (للتوافق القديم)
```

**تغيير مثال الاستخدام من:**
```python
# ✅ الصح — مقيّد بالشركة
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()

# ❌ تجنّب — للتوافق القديم فقط
from ui.events import bus
bus.data_changed.emit()
```
**إلى:**
```python
# ✅ الاستخدام الصحيح
from ui.widgets.core.events import bus
from ui.widgets.core.events import emit_company_data_changed

# emit — لو مفيش شركة نشطة لا يطلق شيء
emit_company_data_changed()

# bus مباشرة
bus.company_data_changed.connect(fn)   # fn(company_id: int)
bus.font_changed.connect(fn)           # fn(size: int)
bus.theme_changed.connect(fn)          # fn(theme_name: str)
bus.language_changed.connect(fn)       # fn(lang_code: str)
```

**إضافة ملاحظة:**
```
⚠️ ui/events.py محذوف — لا تستورد منه.
⚠️ data_changed محذوف — كل الإشعارات مقيّدة بـ company_id.
```

---

### 3. `ui_widgets_2_base.md` — BaseCrudForm

**المكان:** قسم `BaseCrudForm` → `[FIX] استخدام emit_company_data_changed`

**الكود موجود صح بالفعل:**
```python
from ui.widgets.core.events import emit_company_data_changed
```
لا تغيير مطلوب هنا.

**لكن حذف أي إشارة لـ `bus.data_changed.emit()` في الـ منطق:**
```python
# حذف هذا السطر من الشرح:
# [FIX] بدل bus.data_changed.emit()
```
يتغير إلى:
```python
# emit_company_data_changed() — لو مفيش شركة نشطة لا يطلق شيء
```

---

### 4. `ui_widgets_7_mixins.md` — BusConnectedMixin

**المكان:** قسم `BusConnectedMixin` → `._connect_bus()`

**تغيير:**
```python
# قبل
data=True    → company_data_changed + data_changed
```
**إلى:**
```python
data=True    → company_data_changed
```

**حذف من منطق `_on_company_data_changed`:**
```python
# حذف
bus.data_changed
```

**تغيير:**
```python
# قبل
# لو None → bus.data_changed.emit()
```
**إلى:**
```python
# لو مفيش شركة نشطة → لا يطلق شيء
```

**تغيير الـ import في `SharedOpsMixin`:**
```python
# قبل (موجود صح)
from ui.widgets.core.events import emit_company_data_changed
```
لا تغيير مطلوب.

---

### 5. `ui_widgets_9_managers_shared.md` — CategoryManager + SharedItemsListPanel

**المكان:** كل مكان فيه إشارة لـ `bus.data_changed`

**تغيير:**
```python
# قبل
# يستمع لـ bus.data_changed + bus.language_changed
```
**إلى:**
```python
# يستمع لـ bus.company_data_changed + bus.language_changed
```

**تغيير في CategoryForm:**
```python
# قبل
# يُطلق emit_company_data_changed() بعد النجاح
```
لا تغيير — موجود صح بالفعل.

---

### 6. `services_3_orders_accounting.md` — ملاحظات مهمة

**المكان:** قسم `## ملاحظات مهمة` → النقطة 1

**تغيير من:**
```python
# 1. bus events: استخدم emit_company_data_changed() من ui.widgets.core.events
#    بدل bus.data_changed.emit()
```
**إلى:**
```python
# 1. bus events: استخدم دائماً emit_company_data_changed() من ui.widgets.core.events
#    data_changed محذوف — كل الإشعارات عبر company_data_changed
```

---

### 7. `ui_widgets_5_panels_forms_combo.md` — FilterToolbar + CategoryCombo

**المكان:** قسم FilterToolbar

**تغيير:**
```python
# قبل
# [إصلاح 14] يستمع لـ bus.company_data_changed — يُعيد تحميل التصنيفات تلقائياً
```
لا تغيير — موجود صح.

**المكان:** قسم CategoryCombo

**تغيير:**
```python
# قبل
# [إصلاح 2] يستمع لـ bus.data_changed + bus.company_data_changed
```
**إلى:**
```python
# يستمع لـ bus.company_data_changed فقط
```

---

## ملخص التغييرات

| الملف | نوع التغيير | عدد المواضع |
|-------|------------|------------|
| `ui_root.md` | حذف `data_changed` + تغيير مسار الاستيراد | 4 مواضع |
| `ui_widgets_1_core.md` | حذف `data_changed` + تحديث الأمثلة | 3 مواضع |
| `ui_widgets_2_base.md` | تنظيف إشارة `bus.data_changed.emit()` | 1 موضع |
| `ui_widgets_7_mixins.md` | حذف `data_changed` من `_connect_bus` | 2 موضع |
| `ui_widgets_9_managers_shared.md` | تغيير `data_changed` → `company_data_changed` | 1 موضع |
| `services_3_orders_accounting.md` | تحديث ملاحظة bus events | 1 موضع |
| `ui_widgets_5_panels_forms_combo.md` | تغيير CategoryCombo | 1 موضع |

**إجمالي: 13 موضع في 7 ملفات**