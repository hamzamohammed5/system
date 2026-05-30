# دليل الكود — UI / Widgets (1): App Settings & Events

> الجزء الأول من مرجع مكونات الواجهة — إعدادات التطبيق، الحالة، الأحداث، الثيم، الترجمة.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [App Settings](#app-settings) | `app_settings`, `app_state` |
| [Events](#events) | `events` |
| [Theme](#theme) | `themes/theme_manager` |
| [i18n](#i18n) | `widgets/core/i18n` |
| [Core Utilities](#core-utilities) | `widgets/core/__init__`, `widgets/core/colors`, `widgets/core/events`, `widgets/core/conn`, `widgets/core/guard` |

---

## App Settings

### `ui/app_settings.py`

**ثوابت:**
- `DEFAULT_FONT_SIZE = 11`
- `MIN_FONT_SIZE = 8`
- `MAX_FONT_SIZE = 20`
- `SIDEBAR_EXPANDED_WIDTH = 224`
- `SIDEBAR_COLLAPSED_WIDTH = 56`
- `CONTENT_MIN_WIDTH = 820`
- `WINDOW_DEFAULT_W = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH`

**`_C`** — dict ألوان التطبيق الحالية (يتغير مع الثيم).

المفاتيح الكاملة:
```python
# Backgrounds
"bg_page", "bg_surface", "bg_surface_2", "bg_hover", "bg_active", "bg_input"
# Borders
"border", "border_med", "border_focus", "border_strong"
# Text
"text_primary", "text_sec", "text_muted", "text_disabled"
# Accent
"accent", "accent_hover", "accent_light", "accent_mid", "accent_text"
# Sidebar
"sidebar_bg", "sidebar_text", "sidebar_muted", "sidebar_hover",
"sidebar_active", "sidebar_border"
# States
"danger", "danger_bg", "danger_border"
"success", "success_bg", "success_border"
"warning", "warning_bg", "warning_border"
"info", "info_bg", "info_border"
# Tabs
"tab_active", "tab_indicator"
# Purple — للـ machine_op rows
"purple", "purple_bg", "purple_border"
# Orange — للـ filters والـ warnings الثانوية
"orange", "orange_bg", "orange_border"
```

```python
get_font_size() -> int
# [تحسين 43] يقرأ من _module_font_size أولاً (module-level cache)
# ثم AppState.font_size() مع حفظ النتيجة في الـ cache
# لا DB call إذا كان الـ cache سليم

set_font_size(size: int)
# يحدث module cache + AppState + DB

fs(base: int, delta: int = 0) -> int
# حجم خط نسبي — الحد الأدنى 7 دائماً
# مثال: fs(11, +2) = 13

apply_font(app: QApplication, size=None)
# يبني stylesheet + يُطبّقه على الـ app
# يمسح الـ cache أولاً لو size اختلف

apply_theme(theme_colors: dict, app: QApplication = None)
# [themes] يُحدّث _C بألوان الثيم الجديد (يقبل مفاتيح موجودة + جديدة)
# يمسح كل الـ caches (stylesheet + button)
# يُطبّق stylesheet الجديد على الـ app فوراً
# يُستدعى من ThemeManager.set_theme() — لا تستدعه مباشرة من الـ UI
# مثال:
#   apply_theme({"accent": "#5B8DB8", "bg_page": "#0F0F0F", ...})

get_theme_color(key: str, fallback: str = "#000000") -> str
# يرجع لون من _C بأمان مع fallback
# مثال: color = get_theme_color("accent", "#1565c0")

invalidate_stylesheet_cache()
# يمسح _ss_cache + يُعيد حساب _current_theme_hash
# [تحسين 43] يمسح _module_font_size أيضاً (يُجبر إعادة القراءة من AppState)
# يُستدعى عند تغيير الخط أو الثيم أو الشركة

_set_module_font_cache(size: int | None)
# يُحدّث _module_font_size مباشرة — للاستخدام الداخلي
```

**Stylesheet cache:** `_ss_cache` — key هو `(font_size, theme_hash)`.
يُبنى الـ stylesheet مرة واحدة لكل مجموعة (حجم خط + ثيم) ثم يُعاد استخدامه.

**Theme hash:** `_current_theme_hash` — يُحسب من `hash(tuple(sorted(_C.items())))`.
يُعاد حسابه عند استدعاء `invalidate_stylesheet_cache()`.

---

### `ui/app_state.py`

```python
AppState.font_size() -> int
# يحمّل من DB مرة واحدة فقط ثم يُعيد من الـ cache

AppState.on_font_changed(size: int)
# يحدّث _font_size cache
# [تحسين 43] يُزامن _module_font_size في app_settings عبر _set_module_font_cache
# يُبطل button stylesheet cache

AppState.invalidate()
# يمسح _font_size = None
# يستدعي invalidate_stylesheet_cache() الكامل من app_settings
# [تحسين 37] يشمل stylesheet cache + theme hash + module font cache
# مهم عند تغيير الشركة النشطة — يُستدعى من MainWindow._on_company_changed()

DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20
```

---

## Events

### `ui/events.py`

```python
bus = _EventBus()
bus.data_changed          # pyqtSignal() — إشعار عام (للتوافق مع الكود القديم)
bus.company_data_changed  # pyqtSignal(int) — مقيّد بـ company_id (الأفضل للاستخدام الجديد)
bus.font_changed          # pyqtSignal(int)
bus.theme_changed         # pyqtSignal(str) — "light" | "dark"
bus.language_changed      # pyqtSignal(str) — "ar" | "en"
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

## Theme

### `ui/themes/theme_manager.py` — `theme_manager`

```python
theme_manager.current_theme -> str  # "light" | "dark"
theme_manager.is_dark -> bool

theme_manager.set_theme(theme_name: str, save: bool = True)
# يُحدّث _current_theme
# يستدعي apply_theme() من app_settings (يُحدّث _C + يمسح cache + يُطبّق stylesheet)
# يُطلق bus.theme_changed تلقائياً بعد التطبيق
# يحفظ في DB لو save=True

theme_manager.load_from_db()
# يحمّل الثيم المحفوظ + يطبّقه بدون save — يُستدعى عند بدء التطبيق

theme_manager.get_available_themes() -> list[{key, name, active}]
```

**الثيمات المُعرَّفة في `ui/themes/theme_manager.py`:**

```python
THEMES: dict = {
    "light": _LIGHT_THEME,   # Warm Neutral — خلفية بيضاء دافئة (الافتراضي)
    "dark":  _DARK_THEME,    # خلفية داكنة للاستخدام الليلي
}

THEME_DISPLAY_NAMES: dict = {
    "light": "فاتح",
    "dark":  "داكن",
}
```

كل ثيم dict يحتوي على نفس مفاتيح `_C` في app_settings (شامل purple/orange).

**تدفق تغيير الثيم:**
```
SettingsDialog._save()
  → theme_manager.set_theme("dark")
    → apply_theme(colors)          # يُحدّث _C + يمسح cache + يُطبّق stylesheet
    → bus.theme_changed.emit("dark")
      → كل widget مشترك في _on_theme_changed يُعيد تطبيق styles
```

---

## i18n

### `ui/widgets/core/i18n.py` — `I18nManager` + `tr()`

المصدر الوحيد لنظام الترجمة. يحمّل الترجمات تلقائياً من `ui/i18n/ar.py` و`ui/i18n/en.py` عند الاستيراد عبر `_load_translations()`.

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str          # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang: str, save: bool = True)
# يُحدّث _language + يُطبّق direction + يحفظ في DB + يُطلق language_changed
i18n_manager.translate(key: str, lang=None, **kwargs) -> str
# fallback للعربية لو المفتاح ناقص في اللغة المطلوبة
i18n_manager.load_from_db()
# يحمّل اللغة المحفوظة + يُطبّق الاتجاه — يُستدعى عند بدء التطبيق
i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]
i18n_manager.add_translations(lang_code: str, translations: dict)
# يضيف/يحدث ترجمات برمجياً بدون تعديل الملفات

def tr(key: str, lang=None, **kwargs) -> str
# دالة الترجمة الرئيسية — تُرجع المفتاح نفسه لو غير موجود (fallback صامت)
# مثال: tr("save")                           → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X")   → "هل تريد حذف «X»؟"
# مثال: tr("showing_of", shown=5, total=100) → "5 / 100"
```

> **ملاحظة:** لا تمرر نصاً عربياً مباشرة لـ `tr()` — استخدم المفتاح المقابل دائماً.

**تدفق تغيير اللغة:**
```
SettingsDialog._save()
  → i18n_manager.set_language("en")   # يُحدّث + يُطبّق direction + يحفظ
  → bus.language_changed.emit("en")
    → كل widget مشترك في _on_language_changed يُحدّث النصوص بـ tr()
```

---

## Core Utilities

### `ui/widgets/core/__init__.py`

```python
from ui.widgets.core import get_font_size
# re-export من app_settings
```

---

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

### `ui/widgets/core/events.py`

```python
get_active_company_id() -> int | None
emit_company_data_changed()
# يُطلق bus.company_data_changed(cid) لو توجد شركة نشطة
# وإلا يُطلق bus.data_changed()
is_same_company(company_id: int) -> bool
```

---

### `ui/widgets/core/conn.py`

```python
# ── LiveConnMixin ──
# _conn_attr: str = "conn" — اسم الـ attribute الذي يحمل الـ connection
# ⚠️ لو subclass يستخدم self.erp_conn → حدد _conn_attr = "erp_conn"
# [إصلاح 3] _conn_cache: instance variable (object.__setattr__) — لا class variable مشترك
# [إصلاح 13] __init_subclass__ يُصدر تحذيراً لو _conn_attr مشبوه

  ._live_conn() -> Connection
  # 1. self.__dict__["_conn_cache"] لو سليم
  # 2. self.{_conn_attr} لو سليم
  # 3. company_state.get_erp_conn() كـ fallback
  # 4. RuntimeError واضحة لو كل شيء فشل — لا None صامتة
  ._invalidate_conn_cache()
  ._live_acc_conn() -> Connection

# ── SafeConnMixin ──
  ._init_safe_conn(conn, db_name="accounting")
  ._get_safe_conn() -> Connection      # RuntimeError لو فشل — لا None
  ._get_company_id() -> int | None
  ._should_respond_to_company(company_id, stored_attr="_company_id") -> bool

# ── DualConnMixin(SafeConnMixin) ──
  ._init_dual_conn(acc_conn, erp_conn, acc_db="accounting")
  ._get_erp_conn() -> Connection       # RuntimeError لو فشل — لا None
  ._on_dual_company_event(company_id) -> bool
```

---

### `ui/widgets/core/guard.py`

```python
@requires_company
def my_method(self): ...
# رسالة افتراضية: tr("select_company")

@requires_company(return_value=[])
def _load_rows(self) -> list: ...

@requires_company(return_value_factory=list)
def _load_rows(self) -> list: ...
# return_value_factory تتجنب mutable default sharing

@requires_company(message="رسالة مخصصة")
def my_method(self): ...

# يعرض التحذير عبر (بالترتيب):
# show_warning() → _warn() → _notif.show() → debug log
```