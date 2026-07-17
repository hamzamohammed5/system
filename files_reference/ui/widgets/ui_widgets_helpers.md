# دليل الكود — UI / Widgets: Helpers

> `ui/widgets/helpers/` — أدوات مساعدة مرئية قابلة لإعادة الاستخدام (اختيار لون حالياً).
>
> ⚠️ **[تصحيح تسمية/تقسيم]** كان `ColorPickerWidget` (`helpers/color_picker.py`)
> موثّقاً سابقاً داخل `ui_widgets_components.md` رغم أن مساره الفعلي
> `ui/widgets/helpers/` وليس `ui/widgets/components/` — مخالفة لقاعدة "مرجع
> واحد = مسار واحد". تم فصله هنا ليغطي `ui/widgets/helpers/` فقط.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [ColorPicker](#colorpicker) | `helpers/color_picker.py` |

---

## ColorPicker

### `ui/widgets/helpers/color_picker.py`

**الغرض:** widget مدمج لاختيار لون (hex) — مربع معاينة اللون الحالي + زر
يفتح `QColorDialog` عند الضغط.

**Imports:**
```python
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QColorDialog
from PyQt5.QtCore    import pyqtSignal
from PyQt5.QtGui     import QColor

from ..components.button import make_btn
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.constants import SPACING_SM, COLOR_PICKER_PREVIEW_SIZE, COLOR_PICKER_PREVIEW_RADIUS
```

**من يستدعي هذا الملف:** `ui/widgets/managers/category.py` (`CategoryForm`)
يستورد ويستخدم `ColorPickerWidget` مباشرة (`from ..helpers.color_picker import
ColorPickerWidget`) لاختيار لون التصنيف — مرجع: `ui_widgets_managers.md`.

---

### `ColorPickerWidget(QWidget, WidgetMixin)`

```python
ColorPickerWidget(default: str = "", btn_text: str = "", parent=None)
```

- **Class-level attribute:** `color_changed = pyqtSignal(str)` — يُطلق عند تغيير اللون (hex string).
- `__init__`: يحفظ `_color = default`, `_btn_text = btn_text`. يستدعي `self._build()` ثم `_init_widget_mixin(theme=True, font=False, lang=True, data=False)` ثم `_refresh_style()` + `_refresh_lang()`.

**`_build()` — بناء الواجهة:**
```python
# QHBoxLayout: [مربع معاينة (QLabel ثابت الحجم)] [زر "اختر لون" (make_btn)] [stretch]
# self._preview: QLabel بحجم ثابت COLOR_PICKER_PREVIEW_SIZE × نفسه
#   → self._apply_preview() تُستدعى فوراً لضبط الستايل الأولي
# self._btn: make_btn("", "normal") — النص الفعلي يُضبط لاحقاً في _refresh_lang()
#   → btn.clicked.connect(self._pick)
```

**`_refresh_style(*_)`:**
```python
# يستدعي self._apply_preview() فقط — يعيد رسم مربع المعاينة بألوان الثيم الحالية
```

**`_refresh_lang(*_)`:**
```python
# label = self._btn_text if self._btn_text else tr("color_picker_btn")
# self._btn.setText(label)
```

**`_apply_preview()` — منطق رسم مربع المعاينة:**
```python
# color = self._color if self._color else _C['color_picker_default']
# self._preview.setStyleSheet(
#     f"background:{color}; border-radius:{COLOR_PICKER_PREVIEW_RADIUS}px;"
#     f" border:1px solid {_C['border_light']};"
# )
```

**`_pick()` — يُستدعى عند الضغط على الزر:**
```python
# color = self._color if self._color else _C['color_picker_default']
# col = QColorDialog.getColor(QColor(color), self, tr("color_picker_title"))
# لو col.isValid():
#     self._color = col.name()
#     self._apply_preview()
#     self.color_changed.emit(self._color)
```

**API عام:**
```python
.current_color() -> str
# يرجع self._color

.set_color(color: str)
# يضبط self._color = color ثم يستدعي self._apply_preview() (بدون إطلاق color_changed)
```

---

## ملاحظات عامة

- `ColorPickerWidget` يعتمد على `_C['color_picker_default']` و `_C['border_light']` كقيم افتراضية للون ولون الحدود — لا ألوان hardcoded داخل الملف.
- `set_color()` لا يُطلق `color_changed` (تحديث برمجي صامت)، بينما `_pick()` (تفاعل المستخدم) يُطلقه دائماً — فرق مقصود بين التحديث الداخلي والتفاعل الفعلي.
- الزر (`self._btn`) يُبنى بدون نص في `_build()` ويُملأ لاحقاً حصراً عبر `_refresh_lang()` — لا نص مباشر مكتوب في `_build()` نفسها، لضمان الترجمة الصحيحة من أول رسم.

---

## علاقات الملفات

- `color_picker.py` هو الملف الوحيد في هذا المسار — لا علاقات داخلية (نفس المسار) لتوثيقها.
- يستورد `make_btn` من `components/button.py` (مرجع: `ui_widgets_components.md`) — تبعية على مسار مختلف تماماً رغم القرب الوظيفي.
- يستورد `WidgetMixin` من `core/widget_mixin.py` و `tr` من `core/i18n.py` (مرجع: `ui_widgets_core.md`).
- يُستخدم من `managers/category.py` (`CategoryForm`, مرجع: `ui_widgets_managers.md`) — العلاقة الوحيدة المؤكدة من المرفقات الحالية لملف يستدعي هذا الـ widget.
