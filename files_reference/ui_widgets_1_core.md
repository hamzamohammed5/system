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
# (bg, border) من CARD_PALETTES حسب الثيم الحالي
# fallback: (_C["card_fallback_bg"], _C["card_fallback_border"])

status_colors(level: str) -> dict[str, str]
# يبني الـ map من _C في كل استدعاء — يضمن التزامن مع الثيم
# level: "success" | "warning" | "danger" | "info" | "neutral" | "primary" | "purple" | "orange"
# يرجع: {"fg": str, "bg": str, "border": str}

waste_level(pct: float) -> str   # "high" | "medium" | "low" | "zero"
waste_colors(pct: float) -> tuple[str, str]   # (bg, border) حسب المستوى

waste_zero_bg() -> str
waste_zero_border() -> str
waste_zero_color() -> str
waste_text_color() -> str   # لون نص الهادر (orange من _C)
```

---

## Core — Events

### `ui/widgets/core/events.py`

```python
get_active_company_id() -> int | None
# يرجع company_id النشط أو None

emit_company_data_changed()
# يُطلق bus.company_data_changed(cid) لو توجد شركة نشطة
# وإلا يُطلق bus.data_changed()
# الاستخدام الصحيح — بدل bus.data_changed.emit() مباشرة

is_same_company(company_id: int) -> bool
# يتحقق لو company_id هو نفس الشركة النشطة
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
# يرجع True لو سليم، False لو conn=None أو رمى exception

_conn_null_error(class_name: str, method: str, db: str = "erp") -> RuntimeError
# يبني RuntimeError موحدة لحالة فشل الاتصال
# الرسالة تتضمن اسم الـ class والـ method واسم قاعدة البيانات
# تُستدعى من _live_conn() و _get_safe_conn() و _get_erp_conn()
```

#### LiveConnMixin

```python
# _conn_attr: str = "conn"   (اسم الـ attribute الذي يحمل الـ connection)
# _conn_cache: instance variable (يُخزَّن بـ object.__setattr__)

._live_conn() -> Connection
# 1. self.__dict__["_conn_cache"] لو سليم (بدون SELECT 1 — fast path)
# 2. self.{_conn_attr} لو سليم
# 3. company_state.get_erp_conn() كـ fallback
# 4. RuntimeError واضحة (عبر _conn_null_error) لو كل شيء فشل

._invalidate_conn_cache()
# يُعيد ضبط _conn_cache = None

._live_acc_conn() -> Connection
# accounting connection — نفس منطق _live_conn()
# Raises: RuntimeError عبر _conn_null_error لو فشل
```

**`__init_subclass__` — تحذير تلقائي:**
```python
# لو الـ subclass يُعرِّف اسم connection مختلف (مثل "db_conn") بدون تحديث _conn_attr
# يُصدر UserWarning تلقائياً عند تعريف الـ class
# مثال: _conn_attr = "db_conn"   ← أضف هذا لإيقاف التحذير
```

#### SafeConnMixin

```python
._init_safe_conn(conn, db_name: str = "accounting")
# يُهيّئ __safe_conn و __safe_db_name

._get_safe_conn() -> Connection
# إعادة اتصال تلقائية لو فشل الـ connection
# [إصلاح شرط مستحيل]: منطق الـ else branch أُصلح:
#   - db_name == "erp"   → get_erp_conn() مباشرة (public API)
#   - db_name != "erp"   → يجرب _get_conn() كـ fallback
#                           لو فشل → يسجل warning ويحاول erp كـ last resort
#   - القديم كان يحتوي شرطاً مستحيلاً (== "erp" داخل else != "erp")
# Raises: RuntimeError عبر _conn_null_error لو كل شيء فشل

._get_company_id() -> int | None   # static method
._should_respond_to_company(company_id, stored_attr="_company_id") -> bool
```

#### DualConnMixin(SafeConnMixin)

```python
# لأي widget يحتاج acc_conn + erp_conn معاً
._init_dual_conn(acc_conn, erp_conn, acc_db: str = "accounting")

._get_erp_conn() -> Connection
# [إصلاح private API] يستخدم get_erp_conn() (public) بدل _get_conn("erp")
# Raises: RuntimeError عبر _conn_null_error لو فشل

._on_dual_company_event(company_id: int) -> bool
```

**ملاحظات:**
- `LiveConnMixin.__init_subclass__` يُصدر `UserWarning` لو الـ subclass يُعرِّف اسم connection مختلف بدون تحديث `_conn_attr`.
- `SafeConnMixin._get_safe_conn` يستخدم `get_erp_conn()` (public API) بدل `_get_conn()` (private).
- كل الـ mixins ترمي `RuntimeError` واضحة (عبر `_conn_null_error`) بدل إرجاع `None` صامت عند فشل الاتصال.
- `_test_conn` تستخدم `SELECT 1` — لا تستخدمها في hot paths متكررة (مثل `_get_conn` في `ComponentRow` التي تتجنبها عمداً للأداء).

---

## Core — Guard

### `ui/widgets/core/guard.py`

```python
@requires_company
def my_method(self): ...
# رسالة افتراضية: tr("select_company")

@requires_company(return_value=[])
def _load_rows(self) -> list: ...

@requires_company(return_value_factory=list)
def _load_rows(self) -> list: ...
# return_value_factory يتجنب mutable default sharing

@requires_company(message="رسالة مخصصة")
def my_method(self): ...
```

**أولوية عرض التحذير (بالترتيب):**
`show_warning()` → `_warn()` → `_notif.show()` → debug log صامت

**ملاحظة:** `_default_msg()` تستخدم `tr("select_company")` — تدعم الترجمة تلقائياً.

---

## Core — i18n

### `ui/widgets/core/i18n.py`

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str                    # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
# يُحدّث _language + يُطبّق اتجاه Layout + يحفظ في DB + يُطلق language_changed

i18n_manager.translate(key, lang=None, **kwargs) -> str
# fallback للعربية لو المفتاح ناقص في اللغة المطلوبة

i18n_manager.load_from_db()
# يحمّل اللغة المحفوظة + يُطبّق الاتجاه — يُستدعى عند بدء التطبيق

i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]

i18n_manager.add_translations(lang_code: str, translations: dict)
# يضيف/يحدث ترجمات برمجياً بدون تعديل الملفات
# مفيد لـ plugins أو وحدات اختبار

def tr(key: str, lang=None, **kwargs) -> str
# دالة الترجمة الرئيسية
# تُرجع المفتاح نفسه لو غير موجود (fallback صامت)
# مثال: tr("save")                           → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X")   → "هل تريد حذف «X»؟"
```

**مصادر الترجمات:** `ui/i18n/ar.py` (AR_STRINGS) و `ui/i18n/en.py` (EN_STRINGS)

**تحميل الترجمات:**
- يُحمَّل تلقائياً من الملفين عند أول import لـ `i18n.py` عبر `_load_translations()`
- يستخدم absolute imports: `from ui.i18n.ar import AR_STRINGS`
- لو فشل الـ import → الـ dict يبقى فارغاً بدون exception

> ⚠️ لا تمرر نصاً عربياً مباشرة لـ `tr()` — استخدم المفتاح المقابل دائماً.
> للمزيد → راجع `i18n_reference.md`