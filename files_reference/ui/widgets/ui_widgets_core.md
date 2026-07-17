# دليل الكود — UI / Widgets (1): Core Utilities

> `ui/widgets/core/` — الأدوات الأساسية المشتركة بين كل الـ widgets.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Core — Colors](#core--colors) | `core/colors.py` |
| [Core — Events](#core--events) | `core/events.py` |
| [Core — Conn](#core--conn) | `core/conn.py` |
| [Core — Guard](#core--guard) | `core/guard.py` |
| [Core — i18n](#core--i18n) | `core/i18n.py` |
| [Core — WidgetMixin](#core--widgetmixin) | `core/widget_mixin.py` |

---

## Core — Colors

### `ui/widgets/core/colors.py`

كل الألوان تُقرأ من `_C` الحالي — لا hardcoded. المصدر الوحيد للألوان هو `ui/theme_manager.py`.

```python
card_colors(color: str) -> tuple[str, str]
# (bg, border) من CARD_PALETTES في theme_manager حسب الثيم الحالي
# يستورد theme_manager و CARD_PALETTES مباشرة
# fallback: (_C["card_fallback_bg"], _C["card_fallback_border"])

status_colors(level: str) -> dict[str, str]
# يبني الـ map من _C في كل استدعاء — يضمن التزامن مع الثيم
# level: "success" | "warning" | "danger" | "info" | "neutral" | "primary" | "purple" | "orange"
# يرجع: {"fg": str, "bg": str, "border": str}
# "neutral" هو الـ fallback لأي level غير معروف

waste_level(pct: float) -> str   # "high" | "medium" | "low" | "zero"
# pct >= 20 → "high" | pct >= 10 → "medium" | pct > 0 → "low" | else → "zero"

waste_colors(pct: float) -> tuple[str, str]   # (bg, border) حسب المستوى
# يستدعي waste_level() ثم يقرأ _C[f"waste_{level}_bg"] و _C[f"waste_{level}_border"]
# لو level == "zero" → يرجع (waste_zero_bg(), waste_zero_border())

waste_zero_bg() -> str     # _C["waste_zero_bg"]
waste_zero_border() -> str # _C["waste_zero_border"]
waste_zero_color() -> str  # _C["waste_zero_color"]
waste_text_color() -> str  # _C["orange"] — لون نص الهادر
```

---

## Core — Events

### `ui/widgets/core/events.py`

> ⚠️ `ui/events.py` محذوف — لا تستورد منه.
> ⚠️ `data_changed` signal محذوف — كل الإشعارات مقيّدة بـ `company_id`.

```python
get_active_company_id() -> int | None
# يرجع CompanyService.get_current_company_id() — عبر
#   from services.companies.company_service import CompanyService
# يُعيد None عند أي exception — try/except شامل (يُسجَّل عبر logger.debug)

emit_company_data_changed()
# لو cid is not None → bus.company_data_changed.emit(cid)
# لو None → لا يُطلق شيء (لا يوجد data_changed fallback)
# يُسجّل warning عند أي exception

is_same_company(company_id: int) -> bool
# يتحقق لو company_id == get_active_company_id()
```

**الـ bus signals المتاحة:**
```python
from ui.widgets.core.events import bus

bus.company_data_changed.connect(fn)   # fn(company_id: int)
bus.font_changed.connect(fn)           # fn(size: int)
bus.theme_changed.connect(fn)          # fn(theme_name: str)
bus.language_changed.connect(fn)       # fn(lang_code: str)
```

**الاستخدام الصحيح:**
```python
# ✅ الصح — emit مقيّد بالشركة
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()   # لو مفيش شركة نشطة لا يطلق شيء

# ✅ bus مباشرة للاشتراك
from ui.widgets.core.events import bus
bus.company_data_changed.connect(fn)

# ❌ محذوف — لا تستخدم
from ui.events import bus          # ui/events.py محذوف
bus.data_changed.emit()            # data_changed محذوف
```

---

## Core — Conn

### `ui/widgets/core/conn.py`

#### دوال مساعدة داخلية

```python
_test_conn(conn) -> bool
# يختبر الاتصال بـ SELECT 1
# يرجع False لو conn=None أو رمى exception
# ⚠️ لا تستخدمها في hot paths — overhead غير ضروري

_conn_null_error(class_name: str, method: str, db: str = "erp") -> RuntimeError
# يبني RuntimeError موحدة مع رسالة واضحة تحتوي class_name و method و db
```

#### LiveConnMixin

```python
# _conn_attr: str = "conn"   (اسم الـ attribute الذي يحمل الـ connection)
# _conn_cache: يُخزَّن بـ object.__setattr__ (instance variable مباشر)

._live_conn() -> Connection
# Hot path — لا SELECT 1:
#   1. self.__dict__["_conn_cache"] لو موجود → يرجعه مباشرة
#   2. self.{_conn_attr} لو سليم → يُخزّن في _conn_cache ويرجعه
#   3. CompanyService.get_active_erp_conn() كـ fallback (via
#      from services.companies.company_service import CompanyService):
#      → يُحدّث self.conn
#      → يُحدّث _conn_cache
#   4. RuntimeError واضحة عبر _conn_null_error لو كل شيء فشل

._invalidate_conn_cache()
# object.__setattr__(self, "_conn_cache", None)
# يُستدعى عند تغيير الشركة أو إعادة تهيئة الـ connection

._live_acc_conn() -> Connection
# نفس منطق _live_conn() لكن لـ accounting connection
# fallback عبر CompanyService.get_active_accounting_conn()
# Raises: RuntimeError عبر _conn_null_error لو فشل
```

**`__init_subclass__` — تحذير تلقائي:**
```python
# يفحص __annotations__ + __dict__ بحثاً عن أسماء تحتوي "conn" أو "connection"
# لو وجد ولم يُحدَّث _conn_attr → UserWarning تحذر المطور
# يتجاهل الأسماء التي تبدأ بـ "_"
# يتجاهل لو "_conn_attr" موجود أصلاً في cls.__dict__
# هدفه: اكتشاف الـ subclasses التي تُعرّف connection باسم مختلف بدون تحديث _conn_attr
```

#### SafeConnMixin

```python
._init_safe_conn(conn, db_name: str = "accounting")
# يُهيّئ __safe_conn و __safe_db_name (name-mangled للأمان)

._get_safe_conn() -> Connection
# إعادة اتصال تلقائية لو فشل الـ connection (self.__safe_conn) — عبر CompanyService فقط،
# لا استدعاء مباشر لـ company_state._get_conn (كان يُستخدم قديماً وأُزيل):
#
# _getters = {
#     "erp":        CompanyService.get_active_erp_conn,
#     "accounting": CompanyService.get_active_accounting_conn,
#     "inventory":  CompanyService.get_active_inventory_conn,
# }
# _getter = _getters.get(self.__safe_db_name)
#
#   لو _getter موجود → ينادى مباشرة (public API فقط)
#   لو db_name غير معروف لدى CompanyService → logger.warning + fallback لـ get_active_erp_conn()
#   لو النتيجة غير سليمة وdb_name != "erp" → محاولة أخيرة بـ get_active_erp_conn() مع logger.warning
#
# Raises: RuntimeError عبر _conn_null_error لو كل شيء فشل

._get_company_id() -> int | None   # static method
._should_respond_to_company(company_id, stored_attr="_company_id") -> bool
# لو stored = None → يضبطه من company_id الواصل ويرجع True (أول إشعار)
# لو stored = company_id → True (نفس الشركة)
# لو stored != company_id → False (شركة مختلفة)

._on_company_event_safe(company_id: int) -> bool
# نقطة الدخول الموحدة التي تستدعيها الـ widgets (_SmartLine, _JournalFilterBar,
# _JournalTreeTable, ...) عند bus.company_data_changed
# يتحقق أولاً أن الـ widget لم يُحذف من Qt (self.isVisible() داخل try/except RuntimeError)
# → لو محذوف: يرجع False فوراً
# ثم يُفوّض لـ _should_respond_to_company(company_id)
```

**[إصلاح شرط مستحيل في `_get_safe_conn`]:**
```python
# المشكلة القديمة:
#   في الـ else branch (db_name != "erp") كان يوجد:
#     if get_fn and self.__safe_db_name == "erp":   ← مستحيل دائماً False
#       ...
#   هذا الشرط لا يُنفَّذ أبداً لأننا داخل else من db_name == "erp"
#
# الحل الجديد:
#   منطق مباشر بدون الشرط الزائد:
#   - يستخدم _get_conn كـ fallback للأنواع غير erp
#   - يُسجّل warning عند استخدام private API
```

#### DualConnMixin(SafeConnMixin)

```python
._init_dual_conn(acc_conn, erp_conn, acc_db: str = "accounting")
# يستدعي _init_safe_conn(acc_conn, acc_db)
# يحفظ erp_conn في _erp_conn_ref
# يحفظ company_id من _get_company_id()

._get_erp_conn() -> Connection
# يستخدم get_erp_conn() (public API) بدل _get_conn("erp")
# Raises: RuntimeError عبر _conn_null_error لو فشل

._on_dual_company_event(company_id: int) -> bool
# = _should_respond_to_company(company_id)
```

**ملاحظات:**
- `LiveConnMixin.__init_subclass__` يُصدر `UserWarning` لو الـ subclass يُعرِّف اسم connection مختلف بدون تحديث `_conn_attr`.
- `SafeConnMixin._get_safe_conn` يستخدم `get_erp_conn()` (public API) للـ erp — إصلاح الشرط المستحيل القديم موثّق في الكود.
- كل الـ mixins ترمي `RuntimeError` واضحة بدل إرجاع `None` صامت.
- `_live_conn()` لا تستخدم SELECT 1 في hot path — تعتمد على وجود `_conn_cache` مباشرة.
- `_conn_cache` يُخزَّن بـ `object.__setattr__` لتجاوز `__setattr__` المخصص في الـ proxies.

---

## Core — Guard

### `ui/widgets/core/guard.py`

```python
@requires_company
def my_method(self): ...
# رسالة افتراضية: tr("select_company") عبر _default_msg()

@requires_company(return_value=[])
def _load_rows(self) -> list: ...

@requires_company(return_value_factory=list)
def _load_rows(self) -> list: ...
# return_value_factory يتجنب mutable default sharing
# يُستدعى بـ return_value_factory() عند التنفيذ

@requires_company(message="رسالة مخصصة")
def my_method(self): ...
```

**الـ decorator يقبل 4 أنماط:**
1. بدون أقواس: `@requires_company`
2. مع رسالة مخصصة: `@requires_company(message="...")`
3. مع قيمة افتراضية: `@requires_company(return_value=[])`
4. مع factory: `@requires_company(return_value_factory=list)`

**التوقيع الكامل:**
```python
requires_company(method=None, *,
                 message: str = "",
                 return_value = None,
                 return_value_factory: "type | None" = None)
```

**دوال داخلية:**
```python
_is_company_ready() -> bool
# يستدعي CompanyService.is_company_ready()
#   (from services.companies.company_service import CompanyService)
# أي exception → False (الاختيار الآمن)

_show_warning(widget, message: str)
# يفحص الـ widget بالترتيب ويستخدم أول طريقة متاحة:
#   1. widget.show_warning(message)   — BaseDetailPanel
#   2. widget._warn(message)          — FormValidationMixin
#   3. widget._notif.show(message, "warning")  — BaseCrudForm
#   4. logger.debug(...) صامت — لو مفيش طريقة معروفة
```

**أولوية عرض التحذير (بالترتيب):**
`show_warning()` → `_warn()` → `_notif.show()` → debug log صامت

**ملاحظات داخلية:**
- `_SENTINEL = object()` — sentinel داخلي، لا يُستخدم خارج الملف.
- `_default_msg()` تستخدم `tr("select_company")` — تدعم الترجمة تلقائياً، مع fallback `"اختر شركة نشطة أولاً"` لو فشل الـ import.
- `_wrap()` تستخدم `functools.wraps(fn)` للحفاظ على metadata الدالة الأصلية.
- يتحقق من `hasattr(widget, "show_warning")` قبل استدعائها (guard.py).

---

## Core — i18n

### `ui/widgets/core/i18n.py`

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str                    # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
# لو lang غير موجود في _TRANSLATIONS → يُعيّن "ar"
# يُحدّث _language + يُطبّق اتجاه Layout + يحفظ في DB + يُطلق language_changed

i18n_manager.translate(key, lang=None, **kwargs) -> str
# fallback للعربية لو المفتاح ناقص في اللغة المطلوبة
# يرجع key نفسه لو غير موجود في أي لغة
# يُطبّق .format(**kwargs) بأمان (try/except)

i18n_manager.load_from_db()
# يحمّل اللغة المحفوظة عبر LanguageService.load() (services/shared/language_service.py)
# + يُطبّق الاتجاه — يُستدعى عند بدء التطبيق

i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]

i18n_manager.add_translations(lang_code: str, translations: dict)
# يضيف/يحدث ترجمات برمجياً بدون تعديل الملفات
# لو lang_code جديد → يُنشئ dict فارغ أولاً

def tr(key: str, lang=None, **kwargs) -> str
# = i18n_manager.translate(key, lang, **kwargs)
```

**تحميل الترجمات:**
- `_load_translations()` تُستدعى تلقائياً عند module load
- تستخدم **absolute imports**: `from ui.i18n.ar import AR_STRINGS` و `from ui.i18n.en import EN_STRINGS`
- لو فشل الـ import → الـ dict يبقى فارغاً بدون exception (try/except)
- `_TRANSLATIONS` dict يحتوي `"ar": {}` و `"en": {}` — يُملأ من الملفات الخارجية فقط

**اتجاه اللغة:**
```python
_LANGUAGE_DIRECTION      = {"ar": "rtl", "en": "ltr"}
_LANGUAGE_DISPLAY_NAMES  = {"ar": "العربية", "en": "English"}
```

**`_apply_direction()` — داخلي:**
```python
# يستدعي QApplication.instance().setLayoutDirection(self.qt_direction)
# محاط بـ try/except — لا يرمي exception

_save_to_db()
# يحفظ اللغة عبر LanguageService.save(self._language)
#   (from services.shared.language_service import LanguageService)
# محاط بـ try/except — لا يرمي exception
```

> ⚠️ لا تمرر نصاً عربياً مباشرة لـ `tr()` — استخدم المفتاح المقابل دائماً.
> للمزيد → راجع `i18n_reference.md`

---

## Core — WidgetMixin

### `ui/widgets/core/widget_mixin.py`

> **الغرض:** mixin عام يربط أي `QWidget` تلقائياً بأحداث الـ bus (`theme_changed`, `font_changed`, `language_changed`, `company_data_changed`) بدون الحاجة لكتابة كود `weakref` وربط يدوي في كل widget. هذا هو المصدر الوحيد لهذا النمط في كل مشروع الـ widgets — كل الـ widgets تقريباً في `ui/widgets/*` ترث منه وتستدعي `self._init_widget_mixin(...)`.

```python
class WidgetMixin:
    _cached_company_id: int | None
    _widget_mixin_init: bool
    _widget_mixin_slots: list | None
```

#### `._init_widget_mixin(theme=True, font=True, lang=True, data=True) -> None`

- يُستدعى مرة واحدة في `__init__` بعد `super().__init__()`.
- **آمن للاستدعاء أكثر من مرة**: أول استدعاء يُهيّئ `_widget_mixin_slots` (list) و`_widget_mixin_bound` (set لتتبع الأحداث المرتبطة بالفعل). أي استدعاء تالٍ يربط فقط الأحداث الجديدة غير المربوطة سابقاً (فلترة عبر `_bound`) — يمنع الربط المضاعف عند استدعاء الأب والابن كليهما بمعاملات مختلفة.
- كل الربط يتم عبر **`weakref.ref(self)`** — لا يمنع الـ widget من الـ garbage collection.
- كل اتصال بـ signal يستخدم `Qt.UniqueConnection` لمنع التسجيل المضاعف.
- **`theme=True`** → يربط `bus.theme_changed` بحيث يستدعي `self._refresh_style()` عند التغيير.
- **`font=True`** → يربط `bus.font_changed` بنفس الطريقة (`_refresh_style()`) — slot منفصل عن theme لإمكانية التفريق مستقبلاً.
- **`lang=True`** → يربط `bus.language_changed` لاستدعاء `self._refresh_lang()`.
- **`data=True`** → يربط `bus.company_data_changed`:
  - يقرأ `company_state.company_id` مبدئياً في `_cached_company_id` (lazy init، آمن لو فشل).
  - عند وصول الإشعار: يتجاهله لو `company_id is None`، وإلا يُحدّث `_cached_company_id` ويستدعي `self._refresh_data(company_id)` — **بدون مقارنة بالشركة الحالية** (كل استقبال إشعار صالح يُنفَّذ)، مع `try/except` حول `_refresh_data` ويُسجّل الخطأ عبر `logger.error(..., exc_info=True)` دون إيقاف الـ UI.
- **حماية من widget محذوف (`sip.isdeleted`)**: كل الـ slots الداخلية تستدعي `_safe_obj()` أولاً — دالة تتحقق من `weakref` + `_is_deleted()` (تستخدم `sip.isdeleted`, أو `False` دائماً لو `sip` غير متاح) قبل استدعاء أي method على الـ widget، وتلتقط `RuntimeError` بصمت. هذا يمنع خطأ `"Could not parse stylesheet of object ... (0x...)"` الذي يحدث عندما يحاول Qt تطبيق stylesheet على widget تم حذفه من C++.

#### الدوال الافتراضية (Override في الـ subclass حسب الحاجة)

```python
._refresh_style(self, *_)
# افتراضياً: pass — Override لإعادة بناء stylesheet عند theme/font change

._refresh_lang(self, *_)
# افتراضياً: pass — Override لتحديث النصوص عند تغيير اللغة

._refresh_data(self, company_id: int | None = None)
# افتراضياً: pass — Override لإعادة تحميل بيانات DB عند company_data_changed
```

**نمط الاستخدام القياسي المتكرر في كل المشروع:**
```python
class MyWidget(QLabel, WidgetMixin):
    def __init__(self):
        super().__init__()
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=True, data=False)
        self._refresh_style()   # أول رسم يدوي — الـ mixin لا يستدعيه تلقائياً عند الإنشاء

    def _refresh_style(self, *_):
        self.setStyleSheet(f"color:{_C['text_primary']};")
```

**ملاحظات مهمة:**
- الـ mixin **لا** يستدعي `_refresh_style()`/`_refresh_lang()` تلقائياً عند أول إنشاء — على كل widget استدعاءها يدوياً بعد `_init_widget_mixin(...)` في `__init__`.
- `_cached_company_id` و `_widget_mixin_slots` و `_widget_mixin_init` هي **instance-level attributes** (تُضبط داخل `_init_widget_mixin` وليس على مستوى الـ class) لتفادي مشاركتها بين كل الـ instances.
- استيراد `bus` يتم بشكل lazy (داخل `_init_widget_mixin`) لتفادي circular imports عند تحميل الموديول.

---

## علاقات الملفات

- `widget_mixin.py` (`WidgetMixin`) و `events.py` (`bus`) هما نواة هذا المرجع — `widget_mixin.py` يستورد `bus` من `events.py` بشكل lazy داخل `_init_widget_mixin()`، وهذا الثنائي مُستخدم من **كل** widget تقريباً في `ui/widgets/*` (كل المراجع الأخرى تعتمد عليه).
- `conn.py` (`LiveConnMixin`, `SafeConnMixin`, `DualConnMixin`) و `guard.py` (`requires_company`) كلاهما يستورد `services.companies.company_service.CompanyService` بشكل lazy (خارج نطاق `ui/widgets/` — طبقة `services/`)، ولا يعتمدان على `widget_mixin.py` أو `events.py` مباشرة.
- `colors.py` (`card_colors`, `status_colors`, `waste_*`) يعتمد فقط على `ui/theme.py` (`_C`) و `ui/theme_manager.py` (`theme_manager`, `CARD_PALETTES`) — كلاهما خارج `ui/widgets/`؛ لا علاقة مباشرة مع باقي ملفات `core/`.
- `i18n.py` (`tr`, `i18n_manager`) مستقل تماماً عن باقي ملفات `core/` — يعتمد فقط على `ui/i18n/ar.py` و `ui/i18n/en.py` (خارج `ui/widgets/`) و اختيارياً `services/shared/language_service.py`.
- `guard.py` (`requires_company`) يستدعي `_show_warning()` التي تفحص وجود `show_warning`/`_warn`/`_notif` على الـ widget المستهدَف — علاقة استخدام مع `BaseDetailPanel` (`show_warning`, مرجع: `ui_widgets_base.md`) و `FormValidationMixin` (`_warn`, مرجع: `ui_widgets_mixins.md`) و `BaseCrudForm` (`_notif`, مرجع: `ui_widgets_base.md`) — بدون استيراد مباشر (فحص `hasattr` فقط، لا import).
- كل ملفات هذا المرجع تُستخدم من كل مسارات `ui/widgets/*` الأخرى تقريباً؛ العلاقة هنا أحادية الاتجاه دائماً (`core/` لا يستورد من أي مسار آخر داخل `ui/widgets/`).
---

## من يستدعي ملفات هذا المرجع من خارجه

- كل ملفات `ui/` بلا استثناء تقريباً تستورد من `core/`
- `WidgetMixin` (`core/widget_mixin.py`): كل class في `ui/widgets/` و`ui/tabs/` ترث منه
- `bus` (`core/events.py`): كل ملف يستجيب لتغيير الثيم/اللغة/البيانات يستخدمه
- `tr()` (`core/i18n.py`): كل ملف يعرض نصاً للمستخدم يستورده
- `LiveConnMixin` (`core/conn.py`): كل form/tab يحتاج اتصال ديناميكي بالشركة النشطة
- `emit_company_data_changed` (`core/events.py`): كل عملية حفظ/حذف في tab تستدعيه
- العلاقة أحادية الاتجاه تماماً: `core/` لا يستورد من أي مسار آخر داخل `ui/widgets/`
