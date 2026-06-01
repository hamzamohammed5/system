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

```python
get_active_company_id() -> int | None
# يرجع company_state.company_id لو is_ready وإلا None
# يُعيد None عند أي exception — try/except شامل

emit_company_data_changed()
# لو cid is not None → bus.company_data_changed.emit(cid)
# لو None → bus.data_changed.emit()
# يُسجّل warning عند أي exception

is_same_company(company_id: int) -> bool
# يتحقق لو company_id == get_active_company_id()
```

**الاستخدام الصحيح:**
```python
# ✅ الصح — مقيّد بالشركة
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()

# ❌ تجنّب — للتوافق القديم فقط
from ui.events import bus
bus.data_changed.emit()
```

---

## Core — Conn

### `ui/widgets/core/conn.py`

#### دوال مساعدة داخلية

```python
_test_conn(conn) -> bool
# يختبر الاتصال بـ SELECT 1
# يرجع False لو conn=None أو رمى exception

_conn_null_error(class_name: str, method: str, db: str = "erp") -> RuntimeError
# يبني RuntimeError موحدة مع رسالة واضحة
```

#### LiveConnMixin

```python
# _conn_attr: str = "conn"   (اسم الـ attribute الذي يحمل الـ connection)
# _conn_cache: يُخزَّن بـ object.__setattr__ (instance variable)

._live_conn() -> Connection
# 1. self.__dict__["_conn_cache"] لو سليم — fast path بدون SELECT 1
# 2. self.{_conn_attr} لو سليم
# 3. company_state.get_erp_conn() كـ fallback + يُحدّث self.conn + الـ cache
# 4. RuntimeError واضحة (عبر _conn_null_error) لو كل شيء فشل
# ملاحظة: لا SELECT 1 في hot path — يعتمد على وجود الـ cache مباشرة

._invalidate_conn_cache()
# object.__setattr__(self, "_conn_cache", None)

._live_acc_conn() -> Connection
# accounting connection — نفس منطق _live_conn()
# fallback عبر get_accounting_connection()
# Raises: RuntimeError عبر _conn_null_error لو فشل
```

**`__init_subclass__` — تحذير تلقائي:**
```python
# يفحص __annotations__ + __dict__ بحثاً عن أسماء تحتوي "conn" أو "connection"
# لو وجد ولم يُحدَّث _conn_attr → UserWarning
# يتجاهل الأسماء التي تبدأ بـ "_"
# يتجاهل لو "_conn_attr" موجود أصلاً في cls.__dict__
```

#### SafeConnMixin

```python
._init_safe_conn(conn, db_name: str = "accounting")
# يُهيّئ __safe_conn و __safe_db_name

._get_safe_conn() -> Connection
# إعادة اتصال تلقائية لو فشل الـ connection
# db_name == "erp"  → company_state.get_erp_conn() مباشرة (public API)
# db_name != "erp"  → يجرب company_state._get_conn(db_name) كـ fallback
#                     لو لم يُعطِ نتيجة سليمة → يجرب get_erp_conn() كـ last resort مع warning
# Raises: RuntimeError عبر _conn_null_error لو كل شيء فشل

._get_company_id() -> int | None   # static method
._should_respond_to_company(company_id, stored_attr="_company_id") -> bool
# لو stored = None → يضبطه من company_id الواصل ويرجع True
```

**ملاحظة [إصلاح شرط مستحيل]:**
```python
# القديم في else branch كان يحتوي:
#   if get_fn and self.__safe_db_name == "erp":  ← مستحيل دائماً False في else
# الجديد: منطق مباشر بدون الشرط الزائد
# يستخدم _get_conn كـ fallback (private API — مع warning) للأنواع غير erp
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
- `SafeConnMixin._get_safe_conn` يستخدم `get_erp_conn()` (public API) — إصلاح الشرط المستحيل القديم موثّق في الكود.
- كل الـ mixins ترمي `RuntimeError` واضحة بدل إرجاع `None` صامت.
- لا تستخدم `_test_conn` في hot paths — overhead غير ضروري.

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

**أولوية عرض التحذير (بالترتيب):**
`show_warning()` → `_warn()` → `_notif.show()` → debug log صامت

**ملاحظات داخلية:**
- `_SENTINEL = object()` — موجود في الكود كـ sentinel داخلي، لا يُستخدم خارج الملف.
- `_default_msg()` تستخدم `tr("select_company")` — تدعم الترجمة تلقائياً، مع fallback `"اختر شركة نشطة أولاً"` لو فشل الـ import.
- `_wrap()` تستخدم `functools.wraps(fn)` للحفاظ على metadata الدالة الأصلية.

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
# يحمّل اللغة المحفوظة + يُطبّق الاتجاه — يُستدعى عند بدء التطبيق

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
# يحفظ "ui_language" في settings عبر get_connection() + set_setting()
# محاط بـ try/except — لا يرمي exception
```

> ⚠️ لا تمرر نصاً عربياً مباشرة لـ `tr()` — استخدم المفتاح المقابل دائماً.
> للمزيد → راجع `i18n_reference.md`