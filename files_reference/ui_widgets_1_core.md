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

```python
# ── LiveConnMixin ──
# _conn_attr: str = "conn"   (اسم الـ attribute الذي يحمل الـ connection)
# _conn_cache: instance variable

._live_conn() -> Connection
# 1. self.__dict__["_conn_cache"] لو سليم
# 2. self.{_conn_attr} لو سليم
# 3. company_state.get_erp_conn() كـ fallback
# 4. RuntimeError واضحة لو كل شيء فشل

._invalidate_conn_cache()
._live_acc_conn() -> Connection   # accounting connection

# ── SafeConnMixin ──
._init_safe_conn(conn, db_name="accounting")
._get_safe_conn() -> Connection
# إعادة اتصال تلقائية لو فشل الـ connection
._get_company_id() -> int | None
._should_respond_to_company(company_id, stored_attr="_company_id") -> bool

# ── DualConnMixin(SafeConnMixin) ──
# لأي widget يحتاج acc_conn + erp_conn معاً
._init_dual_conn(acc_conn, erp_conn, acc_db="accounting")
._get_erp_conn() -> Connection
._on_dual_company_event(company_id) -> bool
```

**ملاحظات:**
- `LiveConnMixin.__init_subclass__` يُصدر تحذيراً لو الـ subclass يُعرِّف اسم connection مختلف بدون تحديث `_conn_attr`.
- `SafeConnMixin._get_safe_conn` يستخدم `get_erp_conn()` (public API) بدل `_get_conn()` (private).
- كل الـ mixins ترمي `RuntimeError` واضحة بدل إرجاع `None` صامت عند فشل الاتصال.

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

@requires_company(message="رسالة مخصصة")
def my_method(self): ...
```

**أولوية عرض التحذير (بالترتيب):**
`show_warning()` → `_warn()` → `_notif.show()` → debug log صامت

---

## Core — i18n

### `ui/widgets/core/i18n.py`

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str                    # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
i18n_manager.translate(key, lang=None, **kwargs) -> str
i18n_manager.load_from_db()
i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]
i18n_manager.add_translations(lang_code, translations: dict)

def tr(key: str, lang=None, **kwargs) -> str
# دالة الترجمة الرئيسية
# تُرجع المفتاح نفسه لو غير موجود (fallback صامت)
# مثال: tr("save")                           → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X")   → "هل تريد حذف «X»؟"
```

**مصادر الترجمات:** `ui/i18n/ar.py` (AR_STRINGS) و `ui/i18n/en.py` (EN_STRINGS)

> ⚠️ لا تمرر نصاً عربياً مباشرة لـ `tr()` — استخدم المفتاح المقابل دائماً.
> للمزيد → راجع `i18n_reference.md`