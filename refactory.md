## السياق

لدينا `WidgetMixin` في `ui/widgets/core/widget_mixin.py` يوفر ربطاً موحداً بـ bus events
بدلاً من كتابة weakref وconnection يدوياً في كل widget.

الـ Mixin يحل مشكلة `Could not parse stylesheet of object QPushButton(0x...)` عبر
`sip.isdeleted()` قبل أي استدعاء لـ `setStyleSheet`.

---

## مهمتك

حوّل الـ widget في الملف المرفق عشان يستخدم `WidgetMixin` بدل ربط الـ bus يدوياً.
اتبع القواعد دي بالترتيب:

---

## قواعد التحويل

### ١. الـ class definition

```python
# قبل
class MyWidget(QComboBox):

# بعد
from ui.widgets.core.widget_mixin import WidgetMixin
class MyWidget(QComboBox, WidgetMixin):
```

---

### ٢. في `__init__` — استبدل كل ربط bus يدوي بـ `_init_widget_mixin`

```python
# قبل — ربط يدوي
_weak = weakref.ref(self)
def _slot(_=None):
    w = _weak()
    if w: w._apply_style()
bus.theme_changed.connect(_slot)
bus.font_changed.connect(_slot)
bus.language_changed.connect(self._on_lang)

# بعد — سطر واحد
self._init_widget_mixin(theme=True, font=True, lang=True)
self._refresh_style()   # أول رسم فوري
```

اختر الـ parameters حسب الاحتياج:

| parameter | متى تحدده |
|-----------|-----------|
| `theme=True` | لو الـ widget بيستجيب لتغيير الثيم |
| `font=True`  | لو الـ widget بيستجيب لتغيير حجم الخط |
| `lang=True`  | لو الـ widget فيه نصوص تتترجم |
| `data=True`  | لو الـ widget بيجيب بيانات من DB |

---

### ٣. عرّف الدوال المناسبة فقط

```python
def _refresh_style(self, *_):
    # الـ WidgetMixin بيتحقق من sip.isdeleted قبل ما ينادي الدالة دي
    # مش محتاج تضيف try/except هنا إلا لو فيه منطق خاص
    from ui.theme import _C
    from ui.font import get_font_size
    base = get_font_size()
    self.setStyleSheet(f"color: {_C['text_primary']}; font-size: {base}pt;")

def _refresh_lang(self, *_):
    # بس لو lang=True اتحددت
    from ui.widgets.core.i18n import tr
    self.setPlaceholderText(tr('search'))

def _refresh_data(self, company_id=None):
    # بس لو data=True اتحددت
    from db.companies.company_state import company_state
    conn = company_state.get_erp_conn()
    # ... جيب البيانات وحدّث الـ widget
```

---

### ٤. امسح الكود القديم

- احذف أي `weakref.ref(self)` مربوط بـ bus
- احذف أي `bus.theme_changed.connect(...)` يدوي
- احذف أي `bus.font_changed.connect(...)` يدوي
- احذف أي `bus.language_changed.connect(...)` يدوي
- احذف أي `bus.company_data_changed.connect(...)` يدوي
- احذف imports مش محتاجها بعد كده زي `import weakref`
- لو فيه `closeEvent` بيفصل slots يدوياً — احذفه، الـ WidgetMixin بيستخدم weakref فمش محتاج disconnect يدوي

---

## تحذيرات مهمة

**[خطأ ١]** لا تستدعي `_refresh_style` في `__init__` قبل `_init_widget_mixin`:

```python
# خطأ
self._refresh_style()
self._init_widget_mixin()

# صح
self._init_widget_mixin()
self._refresh_style()
```

**[خطأ ٢]** لا تعرّف `_widget_mixin_init` أو `_widget_mixin_slots` على الـ class:

```python
# خطأ — هيتشارك بين كل الـ instances
class MyWidget(QWidget, WidgetMixin):
    _widget_mixin_init = False

# صح — الـ WidgetMixin بيحطهم على الـ instance تلقائياً
class MyWidget(QWidget, WidgetMixin):
    pass
```

**[خطأ ٣]** لا تحط `setStyleSheet` في `__init__` مباشرة لو الـ widget بيتحدث مع الثيم:

```python
# خطأ — الـ style هيتطبق مرة واحدة بس عند الإنشاء
self.setStyleSheet(f"color: {_C['text_primary']}")

# صح — حطه في _refresh_style عشان يتحدث مع الثيم
def _refresh_style(self, *_):
    self.setStyleSheet(f"color: {_C['text_primary']}")
```

---

## مثال كامل

```python
# قبل التحويل
class StatusCombo(QComboBox):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._apply_style()
        import weakref
        _w = weakref.ref(self)
        def _restyle(_=None):
            w = _w()
            if w:
                try: w._apply_style()
                except RuntimeError: pass
        bus.theme_changed.connect(_restyle)
        bus.font_changed.connect(_restyle)

    def _apply_style(self):
        self.setStyleSheet(f"color:{_C['text_primary']};")


# بعد التحويل
from ui.widgets.core.widget_mixin import WidgetMixin

class StatusCombo(QComboBox, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._init_widget_mixin()   # theme + font افتراضياً
        self._refresh_style()       # أول رسم

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(f"color:{_C['text_primary']};")
```