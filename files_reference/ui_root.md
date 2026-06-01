# دليل الكود — UI / Root: Constants, Font, State, Events, Theme, Main Window

> الملفات الجذرية في `ui/` — ثوابت، خط، حالة، أحداث، ثيم، النافذة الرئيسية.
> `ui/constants.py`, `ui/font.py`, `ui/app_state.py`, `ui/events.py`,
> `ui/theme.py`, `ui/theme_manager.py`, `ui/main_window.py`

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [constants](#constants) | `ui/constants.py` |
| [font](#font) | `ui/font.py` |
| [app_state](#app_state) | `ui/app_state.py` |
| [events](#events) | `ui/events.py` |
| [theme](#theme) | `ui/theme.py` |
| [theme_manager](#theme_manager) | `ui/theme_manager.py` |
| [main_window](#main_window) | `ui/main_window.py` |

---

## constants

### `ui/constants.py`

المصدر الوحيد لكل الثوابت — لا يستورد من أي ملف آخر في `ui/`.

```python
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20

SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56

CONTENT_MIN_WIDTH = 820
WINDOW_DEFAULT_W  = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH  # 1044
```

---

## font

### `ui/font.py`

```python
get_font_size() -> int
# يقرأ من _module_font_size أولاً (module-level cache [تحسين 43])
# إن لم يوجد → AppState.font_size() ثم يُخزّن في الـ cache

set_font_size(size: int)
# يُقيّد بـ [MIN_FONT_SIZE, MAX_FONT_SIZE]
# يُحدّث: _module_font_size → AppState.on_font_changed() → DB

fs(base: int, delta: int = 0) -> int
# حجم خط نسبي — الحد الأدنى MIN_FONT_SIZE دائماً

apply_font(app: QApplication, size: int = None)
# يُطبّق حجم الخط على الـ app عبر build_stylesheet()
# يُحدّث الـ cache + AppState

_set_module_font_cache(size: int | None)
# للاستخدام الداخلي — يُعيد ضبط الـ module-level cache
```

---

## app_state

### `ui/app_state.py` — `AppState`

Cache مركزي لإعدادات التطبيق — كل الـ attributes كـ class-level (لا instance).

```python
AppState.font_size() -> int
# يحمّل من DB مرة واحدة ثم يرجع من الـ cache (_font_size)

AppState.on_font_changed(size: int)
# يُقيّد بـ [MIN_FONT_SIZE, MAX_FONT_SIZE]
# يُحدّث _font_size + _module_font_size في font.py
# يُبطل button stylesheet cache

AppState.invalidate()
# يمسح _font_size = None
# يستدعي invalidate_stylesheet_cache() الكامل (theme.py)
# يُستدعى من MainWindow._on_company_changed()
```

**تسلسل القراءة:**
```
get_font_size()
  → _module_font_size (module cache, أسرع)
  → AppState.font_size()
    → _font_size (class cache)
    → _load_font_size_from_db()
      → DB → settings["font_size"]
      → fallback: DEFAULT_FONT_SIZE
```

---

## events

### `ui/events.py`

```python
bus = _EventBus()   # QObject singleton

bus.data_changed          # pyqtSignal()     — إشعار عام (للتوافق القديم)
bus.company_data_changed  # pyqtSignal(int)  — مقيّد بـ company_id (الأفضل)
bus.font_changed          # pyqtSignal(int)  — عند تغيير حجم الخط
bus.theme_changed         # pyqtSignal(str)  — "light" | "dark"
bus.language_changed      # pyqtSignal(str)  — "ar" | "en"
```

**الاستخدام الصحيح:**
```python
# ✅ الصح
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()

# ❌ للتوافق القديم فقط
from ui.events import bus
bus.data_changed.emit()
```

---

## theme

### `ui/theme.py`

```python
_C: dict   # dict الألوان النشطة — يُملأ من _LIGHT_THEME عند الـ import الأول

apply_theme(theme_colors: dict, app: QApplication = None)
# يُحدّث _C + يمسح كل الـ caches + يُطبّق stylesheet على الـ app
# يُستدعى من ThemeManager.set_theme() — لا تستدعه مباشرة

get_theme_color(key: str, fallback: str = "#000000") -> str
# يرجع لون من _C بأمان مع fallback

build_stylesheet(base: int) -> str
# cache key = (font_size, theme_hash)
# يبني الـ stylesheet الكامل مقسّماً على دوال مساعدة

invalidate_stylesheet_cache()
# يمسح _ss_cache + _module_font_size + يُعيد حساب _current_theme_hash
```

**أقسام الـ stylesheet:**
`base_reset`, `message_box`, `dialog`, `typography`, `groupbox`,
`buttons`, `inputs`, `combobox`, `tables`, `tree`, `tabs`, `scrollbars`, `misc`

**مفاتيح `_C` الكاملة:**
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
# Purple / Orange
"purple", "purple_bg", "purple_border"
"orange", "orange_bg", "orange_border"
# Waste
"waste_zero_bg", "waste_zero_border", "waste_zero_color"
"waste_high_bg", "waste_high_border"
"waste_medium_bg", "waste_medium_border"
"waste_low_bg", "waste_low_border"
# Input states
"input_error_bg", "input_error_border"
"input_positive_bg", "input_positive_border", "input_positive_color"
# Card fallback
"card_fallback_bg", "card_fallback_border"
```

---

## theme_manager

### `ui/theme_manager.py`

المصدر الوحيد لتعريف الألوان — كل الثيمات هنا.

```python
_LIGHT_THEME: dict   # Warm Neutral (الافتراضي)
_DARK_THEME:  dict

THEMES: dict = {"light": _LIGHT_THEME, "dark": _DARK_THEME}
THEME_DISPLAY_NAMES: dict = {"light": "فاتح", "dark": "داكن"}

CARD_PALETTES: dict   # lookup tables لألوان البطاقات حسب الثيم
# {"light": {color: (bg, border), ...}, "dark": {...}}

theme_manager = ThemeManager()   # Singleton
```

```python
theme_manager.current_theme -> str   # "light" | "dark"
theme_manager.is_dark -> bool

theme_manager.set_theme(theme_name: str, save: bool = True)
# يُحدّث _current_theme → apply_theme() → يحفظ في DB → يُطلق bus.theme_changed

theme_manager.load_from_db()
# يحمّل الثيم المحفوظ + يطبّقه — يُستدعى عند بدء التطبيق

theme_manager.get_available_themes() -> list[{key, name, active}]
```

**تدفق تغيير الثيم:**
```
SettingsDialog._save()
  → theme_manager.set_theme("dark")
    → apply_theme(colors)          # يُحدّث _C + يمسح cache
    → _save_to_db()
    → bus.theme_changed.emit("dark")
```

---

## main_window

### `ui/main_window.py` — `MainWindow`

```python
MainWindow(app: QApplication)
# resize: WINDOW_DEFAULT_W × 820
# setLayoutDirection: Qt.RightToLeft
# setMinimumSize: (SIDEBAR_COLLAPSED_WIDTH + 400, 500)
```

**هيكل الـ Stack:**
```python
index 0 → NoCompanyScreen
index 1 → CostingSection    ("حساب التكلفة")
index 2 → PricingSection    ("التسعير")
index 3 → AccountingTab     ("الحسابات")
index 4 → InventoryTab      ("المخزن")
index 5 → DesignSection     ("التصميمات")
index 6 → OrdersSection     ("الطلبات")
```

**index_map للـ Navigation:**
```python
{
    "costing":    1,
    "pricing":    2,
    "accounting": 3,
    "inventory":  4,
    "design":     5,
    "orders":     6,
}
```

**سلوكيات خاصة:**
```python
# "settings"     → SettingsDialog (لا يغير الـ stack)
#                  ثم sidebar.refresh_all_buttons()
# "shared_items" → SharedItemsManagerDialog مباشرة

def _on_company_changed(company_id: int):
    AppState.invalidate()   # مسح font_size cache
    self._refresh_tabs()
    bus.company_data_changed.emit(company_id)
```

**حماية من فشل الـ import:**
```python
_try_build_section(builder_fn, section_name) -> QWidget
# يرجع placeholder مع رسالة خطأ واضحة لو فشل ImportError أو أي Exception

_make_placeholder_tab(section_name, error="") -> QWidget
# يعرض: أيقونة 🚧 + عنوان + رسالة الخطأ
```

**دورة حياة الـ tabs:**
```python
_build_tabs()
# يُدمّر tabs القديمة لو موجودة (_destroy_tabs)
# يجلب conn من company_state.get_erp_conn()
# يبني كل section بـ _try_build_section()
# يُشغّل _validate_index_map() للتحقق

_destroy_tabs()
# bus.blockSignals(True) أثناء الإزالة
# يُزيل كل widgets من index 1 فصاعداً
# يستدعي company_state.refresh_connections() بعد الإزالة

_validate_index_map()
# assert على كل index في index_map < stack.count()
```

**إضافة Tab جديدة:**
```python
# 1. في _build_tabs():
def _build_my_section():
    from ui.tabs.my_section import MySection
    return MySection(conn_fn=lambda: conn)
_builders.append((_build_my_section, "اسم القسم"))

# 2. في index_map:
"my_key": N   # N = موقع الـ section في _builders + 1

# 3. في _sidebar._build():
("🔑", "اسم القسم", "my_key", "")

# 4. في _validate_index_map():
# يُضاف تلقائياً لو موجود في index_map
```