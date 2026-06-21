## السياق

لدينا `WidgetMixin` في `ui/widgets/core/widget_mixin.py` يوفر ربطاً موحداً بـ bus events، بدلاً من كتابة weakref وconnection يدوياً في كل widget.

الـ Mixin يحل مشكلة `Could not parse stylesheet of object QPushButton(0x...)` عبر التحقق من `sip.isdeleted()` قبل أي استدعاء لـ `setStyleSheet`.

---

## المهمة

حوّل الـ widgets الموجودة في الملفات المرفقة لتستخدم `WidgetMixin`.

**نطاق التحويل (مهم):** المطلوب ليس فقط الـ widgets اللي بتعمل ربط يدوي مع bus events. أي widget يستخدم مباشرةً أحد APIs الآتية **داخل تعريفه نفسه** يدخل في النطاق ويجب تحويله، حتى لو لم يكن مشتركاً في أي bus signal أصلاً:

- ألوان الثيم (مثل `_C` من `ui/theme.py`)
- حجم الخط (مثل `get_font_size()` من `ui/font.py`)
- النصوص القابلة للترجمة (مثل `tr()` من `ui/widgets/core/i18n`)

هذا يشمل، على سبيل المثال، widget بيطبّق الـ style مرة واحدة بس جوا `__init__` ومش بيتحدث تاني عند تغيير الثيم أو الخط — هذه الحالة **تدخل في النطاق وتحتاج تحويل**، لأن الهدف هو ضمان أن أي widget يعتمد على هذه القيم سيتحدث تلقائياً عبر `WidgetMixin` بدل ما يفضل ثابت بعد أول رسم.

**خارج النطاق:** لو الاستخدام غير مباشر — أي الـ widget بيستدعي دالة في كلاس أو module تاني وهي اللي بتطبّق الستايل أو تجيب الترجمة — متبعش الاستدعاء ومتعدلش الكلاس الآخر؛ ركّز فقط على الكود المباشر جوا تعريف الـ widget نفسه.

إذا كان أحد الملفات المرفقة لا يستخدم أي من الأنظمة دي (لا bus events ولا theme/font/lang APIs) أصلاً، تجاهله ولا تعدّل فيه.

**ملاحظة مهمة:** عدّل الملفات المرفقة مباشرة — لا تكتب أي ملف من الصفر.

اتبع القواعد التالية بالترتيب:

---

## خطوات التحويل

### ١. تعديل تعريف الـ class

```python
# قبل
class MyWidget(QComboBox):

# بعد
from ui.widgets.core.widget_mixin import WidgetMixin

class MyWidget(QComboBox, WidgetMixin):
```

---

### ٢. استبدال الربط اليدوي (أو غياب الربط) في `__init__`

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

```python
# قبل — استخدام مباشر بدون أي اشتراك في bus (الستايل بيتطبق مرة واحدة بس)
class MyWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        from ui.theme import _C
        self.setStyleSheet(f"color: {_C['text_primary']};")

# بعد — نفس المبدأ: حتى مفيش bus.connect، لازم يتحول
from ui.widgets.core.widget_mixin import WidgetMixin

class MyWidget(QLabel, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget_mixin(theme=True)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(f"color: {_C['text_primary']};")
```

اختر الـ parameters المناسبة حسب احتياج الـ widget:

| Parameter | يُستخدم عندما... |
|-----------|-------------------|
| `theme=True` | الـ widget يستخدم ألوان الثيم (مثل `_C`) في أي مكان داخل تعريفه |
| `font=True`  | الـ widget يستخدم حجم الخط (مثل `get_font_size()`) داخل تعريفه |
| `lang=True`  | الـ widget يحتوي نصوصاً قابلة للترجمة (مثل `tr()`) داخل تعريفه |
| `data=True`  | الـ widget يجلب بيانات من قاعدة البيانات |

---

### ٣. تعريف الدوال المناسبة فقط (حسب الـ parameters المختارة)

```python
def _refresh_style(self, *_):
    # WidgetMixin يتحقق من sip.isdeleted تلقائياً قبل استدعاء هذه الدالة
    # لا داعي لـ try/except هنا إلا لو فيه منطق خاص إضافي
    from ui.theme import _C
    from ui.font import get_font_size
    base = get_font_size()
    self.setStyleSheet(f"color: {_C['text_primary']}; font-size: {base}pt;")

def _refresh_lang(self, *_):
    # فقط إذا كان lang=True
    from ui.widgets.core.i18n import tr
    self.setPlaceholderText(tr('search'))

def _refresh_data(self, company_id=None):
    # فقط إذا كان data=True
    from db.companies.company_state import company_state
    conn = company_state.get_erp_conn()
    # ... جلب البيانات وتحديث الـ widget
```

---

### ٤. حذف الكود القديم

احذف كل ما يلي إن وُجد:
- أي `weakref.ref(self)` مرتبط بالـ bus
- أي `bus.theme_changed.connect(...)` يدوي
- أي `bus.font_changed.connect(...)` يدوي
- أي `bus.language_changed.connect(...)` يدوي
- أي `bus.company_data_changed.connect(...)` يدوي
- أي استدعاء مباشر لـ `_C` أو `get_font_size()` أو `tr()` تم تطبيقه مرة واحدة بس في `__init__` بدون اشتراك — يُنقل داخل `_refresh_style` / `_refresh_lang` كما هو موضح في الخطوة ٢
- الـ imports غير المستخدمة بعد التحويل (مثل `import weakref`)
- أي `closeEvent` يفصل الـ slots يدوياً (غير ضروري لأن WidgetMixin يستخدم weakref تلقائياً)

---

## أخطاء يجب تجنبها

**خطأ ١ — ترتيب الاستدعاء:**
```python
# خطأ
self._refresh_style()
self._init_widget_mixin()

# صح
self._init_widget_mixin()
self._refresh_style()
```

**خطأ ٢ — تعريف متغيرات الحالة على مستوى الـ class:**
```python
# خطأ — هتتشارك بين كل الـ instances
class MyWidget(QWidget, WidgetMixin):
    _widget_mixin_init = False

# صح — WidgetMixin يضبطها تلقائياً على مستوى الـ instance
class MyWidget(QWidget, WidgetMixin):
    pass
```

**خطأ ٣ — وضع الـ style مباشرة في `__init__`:**
```python
# خطأ — الـ style هيتطبق مرة واحدة بس عند الإنشاء، ولن يتحدث مع الثيم
self.setStyleSheet(f"color: {_C['text_primary']}")

# صح — ضعه داخل _refresh_style ليتحدث تلقائياً مع تغيير الثيم
def _refresh_style(self, *_):
    self.setStyleSheet(f"color: {_C['text_primary']}")
```

**خطأ ٤ — تجاهل widget بسبب عدم وجود bus.connect:**
```python
# خطأ — "مفيش bus.connect إذن مش محتاج تحويل"
class MyWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        from ui.theme import _C
        self.setStyleSheet(f"color: {_C['text_primary']};")
    # ← تم تجاهله غلط لمجرد عدم وجود ربط يدوي بالـ bus

# صح — أي استخدام مباشر لـ _C / get_font_size / tr داخل تعريف الـ widget
# يدخل في نطاق التحويل، بغض النظر عن وجود bus.connect من عدمه
```

**خطأ ٥ — تتبّع الاستخدام غير المباشر:**
```python
# خطأ — الذهاب لتعديل StyleHelper لأن MyWidget يستدعيه
class MyWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        StyleHelper.apply(self)   # الستايل الفعلي معرف في كلاس تاني

# صح — هذا خارج النطاق؛ لا تعدّل StyleHelper ولا تتبع الاستدعاء،
# فقط الكود المباشر جوا تعريف الـ widget نفسه يدخل في التحويل
```

---

## مثال كامل (قبل وبعد)

```python
# ===== قبل التحويل =====
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


# ===== بعد التحويل =====
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

---

## ملاحظة إضافية بخصوص القيم الثابتة (Hardcoded Values)

إذا وجدت في أي ملف ألواناً أو نصوصاً أو خطوطاً مكتوبة مباشرة (hardcoded) بدلاً من استخدام:
- `font.py` لأحجام الخطوط
- `theme.py` للألوان
- `i18n` للنصوص القابلة للترجمة

**فلا تستبدلها تلقائياً.** بدلاً من ذلك، أخبرني بذلك أولاً، وسأرسل لك الملفات المرجعية (`font.py`, ملف الألوان, ملفات الترجمة) لتختار منها المفاتيح (keys) الصحيحة المطابقة للون أو النص الموجود، حتى يكون الكود الناتج نظيفاً ومتسقاً مع باقي المشروع.