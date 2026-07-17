# دليل الكود — UI / Widgets: Forms

> `ui/widgets/forms/` — حقول الفورمات المتقدمة (Amount, Date, Required, Notes).
>
> ⚠️ **[تصحيح تسمية/تقسيم]** هذا الملف كان مدموجاً سابقاً مع `panels/` و
> `combo/` في ملف واحد (`ui_widgets_panels.md`) — مخالفة لقاعدة "مرجع واحد
> = مسار واحد". تم فصله هنا ليغطي `ui/widgets/forms/` فقط.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Forms — Inputs](#forms--inputs) | `forms/inputs.py` |

---

## Forms — Inputs

### `ui/widgets/forms/inputs.py`

**الغرض:** مجموعة input widgets متقدمة موحّدة للتطبيق (مبالغ، تواريخ، حقول
إلزامية، ملاحظات) — كل واحد منها يتابع الثيم تلقائياً عبر `WidgetMixin`
بدل بناء stylesheet ثابت مرة واحدة وقت الإنشاء.

**Imports:**
```python
# [إصلاح 1] المسار الصحيح بعد Refactor V3:
from ..theme.input_styles import input_style as _input_style, spinbox_style as _spinbox_style
# (بدل from ..theme.styles المحذوف — theme/styles.py لم يعد موجوداً)

# [إصلاح 2] حذف from ..core import get_font_size as _get_font_size
# كان مكرراً مع from ui.font import get_font_size

from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox, ThemedDateEdit
```

**من يستدعي هذا الملف:** غير محدد بثقة من المرفقات الحالية (لا يوجد ملف آخر
في نفس الدفعة يستورد من `forms/inputs.py` صراحةً ظاهراً في الكود المرفق).

---

### `AmountSpinBox(QDoubleSpinBox, WidgetMixin)`

```python
AmountSpinBox(max_=AMOUNT_SPINBOX_MAX, dec=2, min_=0,
              height=INPUT_HEIGHT, currency="", parent=None)
```
- `__init__`: يضبط `setRange(min_, max_)`, `setDecimals(dec)`, `setMinimumHeight(height)`. لو `currency` غير فارغ → `setSuffix(f"  {currency}")`. يستدعي `_init_widget_mixin(theme=True, font=False)` ثم `_refresh_style()`. يربط `valueChanged.connect(self._refresh_style)` — كل تغيير في القيمة يُعيد رسم الستايل.
- `_refresh_style(*_)`: `setStyleSheet(_spinbox_style(self._h, positive=self.value() > 0))` — القيمة > 0 تُلوّن الحقل بألوان `input_positive_*` من `_C` (أخضر) تلقائياً.

---

### `DateField(ThemedDateEdit, WidgetMixin)`

```python
DateField(date: QDate = None, height=INPUT_HEIGHT, width=None, parent=None)
```
- `__init__`: يرث من `ThemedDateEdit` (تاريخ افتراضي = `QDate.currentDate()` لو `date=None`)، `setCalendarPopup(True)`, `setDisplayFormat("yyyy-MM-dd")`. لو `width` محدد → `setFixedWidth(width)`. يستدعي `_init_widget_mixin(theme=True, font=False)` ثم `_refresh_style()`.
- `_refresh_style(*_)`: يبني stylesheet لـ `QDateEdit` من `_input_style(self._h)` + قاعدة إضافية لـ `QDateEdit::drop-down` (بدون حدود، عرض `DROPDOWN_ARROW_W`).
- `.date_str() -> str`: يرجع `self.date().toString("yyyy-MM-dd")`.
- `.set_date_str(s: str)`: يحوّل النص لـ `QDate.fromString(s, "yyyy-MM-dd")` ويضبطه لو صالح (`isValid()`).

---

### `StyledComboBox(ThemedComboBox, WidgetMixin)`

```python
StyledComboBox(height=INPUT_HEIGHT, parent=None)
```
- `__init__`: `setMinimumHeight(height)` ثم `_init_widget_mixin(theme=True, font=False)` + `_refresh_style()`.
- `_refresh_style(*_)`: يبني stylesheet لـ `QComboBox` من `_input_style(self._h)` + قاعدة `::drop-down` + قاعدة `:disabled` (خلفية `bg_surface_2`، لون `text_disabled`).

---

### `LabeledInput(QWidget, WidgetMixin)`

```python
LabeledInput(label: str, widget: QWidget, unit: str = "",
             spacing=LABELED_INPUT_SPACING, label_width=None, parent=None)
```
- `__init__`: يحفظ `_widget`, `_label_text`, `_unit_text`, `_label_width`. يبني `QHBoxLayout`: label (محاذاة يمين، عرض ثابت لو `label_width` محدد) + `widget` (stretch=1) + label الوحدة (لو `unit` غير فارغ). يستدعي `_init_widget_mixin(theme=True, font=True)` + `_refresh_style()`.
- `_refresh_style(*_)`: يلوّن label الرئيسي بـ `_C['text_sec']` بخط bold (600)، ولون label الوحدة بـ `_C['text_muted']` بحجم أصغر (`fs(base,-1)`).
- `.widget -> QWidget` (property): يرجع `self._widget`.

---

### `RequiredLineEdit(ThemedLineEdit, WidgetMixin)`

```python
RequiredLineEdit(placeholder="", height=INPUT_HEIGHT, parent=None)
```
- `__init__`: `setPlaceholderText(placeholder)`, `setMinimumHeight(height)`. `self._error = False`. يستدعي `_init_widget_mixin(theme=True, font=False)` + `_refresh_style()`، ثم يربط `textChanged.connect(self._on_change)`.
- `_refresh_style(*_)`: `setStyleSheet(f"QLineEdit {{ {_input_style(self._h, self._error)} }}")` — `_input_style(error=True)` يحوّل الحدود/الخلفية لألوان `input_error_*` من `_C` (أحمر).
- `._on_change()`: لو `_error=True` والنص الحالي غير فارغ بعد `strip()` → يمسح حالة الخطأ (`_error=False`) ويعيد الرسم.
- `.validate() -> bool`: لو النص فارغ بعد `strip()` → يضبط `_error=True`، يعيد الرسم، `setFocus()`، يرجع `False`. وإلا يرجع `True`.
- `.text_stripped() -> str`: يرجع `self.text().strip()`.
- `.clear_error()`: يضبط `_error=False` ويعيد الرسم.

---

### `NotesLineEdit(ThemedLineEdit, WidgetMixin)`

```python
NotesLineEdit(placeholder="", height=NOTES_LINE_EDIT_HEIGHT, parent=None)
```
- `__init__`: يحفظ `_custom_placeholder`. `setMinimumHeight(height)`. يستدعي `_init_widget_mixin(theme=True, font=False, lang=True)` + `_refresh_style()` + `_refresh_lang()`.
- `_refresh_style(*_)`: stylesheet مخصص (وليس `_input_style` العام) — خلفية `bg_surface_2`، حدود `border`، خط `italic` بلون `text_sec` في الحالة العادية؛ عند `:focus` يتحول لحدود `border_med`، خلفية `bg_input`، خط عادي (غير italic)، لون `text_primary`. الهدف: مظهر "تلميحي" (placeholder-like) عند عدم التركيز يتحول لحقل عادي عند الكتابة.
- `_refresh_lang(*_)`: `setPlaceholderText(self._custom_placeholder if self._custom_placeholder else tr('notes_optional_placeholder'))`.

---

## ملاحظات عامة

- كل الكلاسات في هذا الملف تتبع نفس النمط: يرث من `Themed*` (أو `QDoubleSpinBox`/`QSpinBox` مباشرة) + `WidgetMixin`، مع `_refresh_style()` مبنية من دوال `theme/input_styles.py` (`input_style`, `spinbox_style`) بدل stylesheet ثابت وقت الإنشاء.
- **[إصلاح ثيم]** هذا هو سبب وجود الملف في هذا الشكل: كل الـ widgets هنا كانت قديماً تبني الـ stylesheet مرة واحدة بقيم `_C` وقت الإنشاء فقط، ولا تستمع لـ `bus.theme_changed` — بما أن `setStyleSheet` المحلي على الـ widget له أولوية أعلى من الـ global app stylesheet في Qt، كانت الألوان تتجمد على الثيم الذي بُني فيه الـ widget. الحل الموحّد: `WidgetMixin(theme=True)` لكل الكلاسات.

---

## علاقات الملفات

- `forms/inputs.py` يستورد `ThemedLineEdit`/`ThemedComboBox`/`ThemedDateEdit` من `panels/themed_inputs.py` (مرجع: `ui_widgets_panels.md`).
- يستورد `input_style`/`spinbox_style` من `theme/input_styles.py` (مرجع: `ui_widgets_theme.md`).
- لا اعتماد على `combo/` أو أي ملف آخر خارج `panels/themed_inputs.py` و `theme/input_styles.py`.
