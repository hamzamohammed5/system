# دليل الكود — UI / Widgets (1): Core Utilities

> `ui/widgets/core/` — الأدوات الأساسية المشتركة بين كل الـ widgets.
> لـ app_settings, app_state, events, theme → راجع `ui_widgets_ui_root.md`
> لـ i18n → راجع `i18n_reference.md`

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [Core — __init__](#core--init) | `widgets/core/__init__.py` |
| [Core — Colors](#core--colors) | `widgets/core/colors.py` |
| [Core — Events](#core--events) | `widgets/core/events.py` |
| [Core — Conn](#core--conn) | `widgets/core/conn.py` |
| [Core — Guard](#core--guard) | `widgets/core/guard.py` |
| [Core — i18n](#core--i18n) | `widgets/core/i18n.py` |

---

## Core — __init__

### `ui/widgets/core/__init__.py`

```python
from ui.widgets.core import get_font_size
# re-export من app_settings
```

---

## Core — Colors

### `ui/widgets/core/colors.py`

```python
card_colors(color: str) -> tuple[str, str]
# (bg, border) من CARD_PALETTE — fallback: ("#f5f5f5", "#e0e0e0")

status_colors(level: str) -> dict[str, str]
# يبني الـ map من _C في كل استدعاء — لا dict ثابت
# هذا يضمن التزامن التلقائي مع تغييرات الثيم
# level: "success" | "warning" | "danger" | "info" | "neutral" | "primary" | "purple" | "orange"
# يرجع: {"fg": str, "bg": str, "border": str}
# purple/orange: من _C.get() مع fallback آمن
# ملاحظة: الـ import داخل الدالة (lazy) مقصود لتجنب circular imports

waste_level(pct: float) -> str   # "high" | "medium" | "low" | "zero"
waste_colors(pct: float) -> tuple[str, str]

WASTE_COLORS = {"high": ("#ffcdd2","#e53935"), "medium": ("#ffe0b2","#f57c00"),
                "low": ("#fff8e1","#ffe082")}
WASTE_ZERO_BG = "#f5f5f5" | WASTE_ZERO_BORDER = "#e0e0e0"
WASTE_ZERO_COLOR = "#999" | WASTE_TEXT_COLOR = "#e65100"
```

---

## Core — Events

### `ui/widgets/core/events.py`

```python
get_active_company_id() -> int | None
emit_company_data_changed()
# يُطلق bus.company_data_changed(cid) لو توجد شركة نشطة
# وإلا يُطلق bus.data_changed()
is_same_company(company_id: int) -> bool
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
# _conn_attr: str = "conn"
# _conn_cache: instance variable (object.__setattr__)

  ._live_conn() -> Connection
  # 1. self.__dict__["_conn_cache"] لو سليم
  # 2. self.{_conn_attr} لو سليم
  # 3. company_state.get_erp_conn() كـ fallback
  # 4. RuntimeError واضحة لو كل شيء فشل
  ._invalidate_conn_cache()
  ._live_acc_conn() -> Connection

# ── SafeConnMixin ──
  ._init_safe_conn(conn, db_name="accounting")
  ._get_safe_conn() -> Connection
  ._get_company_id() -> int | None
  ._should_respond_to_company(company_id, stored_attr="_company_id") -> bool

# ── DualConnMixin(SafeConnMixin) ──
  ._init_dual_conn(acc_conn, erp_conn, acc_db="accounting")
  ._get_erp_conn() -> Connection
  ._on_dual_company_event(company_id) -> bool
```

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

# يعرض التحذير عبر (بالترتيب):
# show_warning() → _warn() → _notif.show() → debug log
```

---

## Core — i18n

### `ui/widgets/core/i18n.py` — `I18nManager` + `tr()`

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str          # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
i18n_manager.translate(key, lang=None, **kwargs) -> str
i18n_manager.load_from_db()
i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]
i18n_manager.add_translations(lang_code, translations: dict)

def tr(key: str, lang=None, **kwargs) -> str
# دالة الترجمة الرئيسية — تُرجع المفتاح نفسه لو غير موجود (fallback صامت)
# مثال: tr("save")                           → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X")   → "هل تريد حذف «X»؟"
```

> **ملاحظة:** لا تمرر نصاً عربياً مباشرة لـ `tr()` — استخدم المفتاح المقابل دائماً.
> للمزيد عن إضافة مفاتيح جديدة → راجع `i18n_reference.md`