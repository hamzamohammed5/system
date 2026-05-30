# دليل الكود — UI / Root: App Settings, State, Events, Theme

> الملفات الجذرية في `ui/` — إعدادات التطبيق، الحالة، الأحداث، الثيم.
> `ui/app_settings.py`, `ui/app_state.py`, `ui/events.py`,
> `ui/main_window.py`, `ui/settings_dialog.py`, `ui/themes/theme_manager.py`

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [app_settings](#app_settings) | `ui/app_settings.py` |
| [app_state](#app_state) | `ui/app_state.py` |
| [events](#events) | `ui/events.py` |
| [theme_manager](#theme_manager) | `ui/themes/theme_manager.py` |
| [main_window](#main_window) | `ui/main_window.py` |
| [settings_dialog](#settings_dialog) | `ui/settings_dialog.py` |

---

## app_settings

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

مفاتيح `_C` الكاملة:
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
# Purple
"purple", "purple_bg", "purple_border"
# Orange
"orange", "orange_bg", "orange_border"
```

```python
get_font_size() -> int
# [تحسين 43] يقرأ من _module_font_size أولاً ثم AppState.font_size()

set_font_size(size: int)
# يحدث module cache + AppState + DB

fs(base: int, delta: int = 0) -> int
# حجم خط نسبي — الحد الأدنى 7 دائماً

apply_font(app: QApplication, size=None)
# يبني stylesheet + يُطبّقه على الـ app

apply_theme(theme_colors: dict, app: QApplication = None)
# يُحدّث _C بألوان الثيم الجديد
# يمسح كل الـ caches (stylesheet + button)
# يُطبّق stylesheet الجديد على الـ app فوراً
# يُستدعى من ThemeManager.set_theme() — لا تستدعه مباشرة من الـ UI

get_theme_color(key: str, fallback: str = "#000000") -> str
# يرجع لون من _C بأمان مع fallback

invalidate_stylesheet_cache()
# يمسح _ss_cache + _module_font_size + يُعيد حساب _current_theme_hash

_set_module_font_cache(size: int | None)
# للاستخدام الداخلي فقط
```

**Stylesheet cache:** key هو `(font_size, theme_hash)` — يُبنى مرة واحدة لكل مجموعة.

---

## app_state

### `ui/app_state.py`

```python
AppState.font_size() -> int
# يحمّل من DB مرة واحدة ثم يُعيد من الـ cache

AppState.on_font_changed(size: int)
# يحدّث _font_size cache + يُزامن _module_font_size في app_settings
# يُبطل button stylesheet cache

AppState.invalidate()
# يمسح _font_size = None
# يستدعي invalidate_stylesheet_cache() الكامل
# مهم عند تغيير الشركة — يُستدعى من MainWindow._on_company_changed()

DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20
```

---

## events

### `ui/events.py`

```python
bus = _EventBus()
bus.data_changed          # pyqtSignal() — إشعار عام (للتوافق مع الكود القديم)
bus.company_data_changed  # pyqtSignal(int) — مقيّد بـ company_id (الأفضل)
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

## theme_manager

### `ui/themes/theme_manager.py`

```python
theme_manager.current_theme -> str  # "light" | "dark"
theme_manager.is_dark -> bool

theme_manager.set_theme(theme_name: str, save: bool = True)
# يُحدّث _current_theme
# يستدعي apply_theme() من app_settings
# يُطلق bus.theme_changed تلقائياً

theme_manager.load_from_db()
# يحمّل الثيم المحفوظ + يطبّقه — يُستدعى عند بدء التطبيق

theme_manager.get_available_themes() -> list[{key, name, active}]
```

**الثيمات المُعرَّفة:**
```python
THEMES: dict = {
    "light": _LIGHT_THEME,   # Warm Neutral (الافتراضي)
    "dark":  _DARK_THEME,
}
THEME_DISPLAY_NAMES: dict = {
    "light": "فاتح",
    "dark":  "داكن",
}
```

**تدفق تغيير الثيم:**
```
SettingsDialog._save()
  → theme_manager.set_theme("dark")
    → apply_theme(colors)          # يُحدّث _C + يمسح cache
    → bus.theme_changed.emit("dark")
```

---

## main_window

### `ui/main_window.py`

```python
MainWindow(app: QApplication)
# resize: WINDOW_DEFAULT_W × 820
# setLayoutDirection: Qt.RightToLeft
# setMinimumSize: (SIDEBAR_COLLAPSED_WIDTH + 400, 500)
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
# index 0 → NoCompanyScreen
```

**سلوكيات خاصة:**
```python
# "settings"     → SettingsDialog (لا يغير الـ stack index)
# "shared_items" → SharedItemsManagerDialog مباشرة

def _on_company_changed(company_id: int):
    AppState.invalidate()
    self._refresh_tabs()
    bus.company_data_changed.emit(company_id)
```

**حماية من فشل الـ import:**
```python
_try_build_section(builder_fn, section_name) -> QWidget
# يرجع placeholder مع رسالة خطأ واضحة لو فشل الـ import

_make_placeholder_tab(section_name, error="") -> QWidget
```

**إضافة Tab جديدة:**
```python
# في MainWindow._build_tabs():
def _build_my_section():
    from ui.tabs.my_section import MySection
    return MySection(conn_fn=lambda: conn)

_builders.append((_build_my_section, tr("my_section_name")))

# في index_map:
"my_key": N

# في _sidebar._build():
("🔑", tr("my_section_name"), "my_key", "")
```

---

## settings_dialog

### `ui/settings_dialog.py`

```python
SettingsDialog(app: QApplication, parent=None)
# تبويبات: الخط | المظهر | اللغة | الوحدات | GIMP
```

**التبويبات:**

| التبويب | المحتوى |
|---------|---------|
| 🔤 الخط | Slider لحجم الخط (8-20) + معاينة نصية |
| 🎨 المظهر | Radio buttons: فاتح / داكن |
| 🌐 اللغة | Radio buttons: العربية / English |
| 📏 الوحدات | قائمة وحدات القياس + إضافة/حذف/استعادة |
| 🖼️ GIMP | مسار ملف GIMP التنفيذي |

**حفظ (`_save`):**
```python
# حجم الخط:
set_font_size(size)
apply_font(app, size)
bus.font_changed.emit(size)

# الثيم:
theme_manager.set_theme(selected_theme, save=True)
# → يُطلق bus.theme_changed تلقائياً

# اللغة:
i18n_manager.set_language(selected_lang, save=True)
app.setLayoutDirection(i18n_manager.qt_direction)
bus.language_changed.emit(selected_lang)

# GIMP path:
set_setting(conn, "gimp_path", path)
```

**مساعدات داخلية:**
```python
_get_settings_conn_and_status() -> tuple[conn, has_company]
# [A-05] يقرأ company_state.is_ready مرة واحدة فقط
# يرجع (conn, True) | (None, False)

_get_settings_conn() -> conn | None
# للتوافق مع الكود القديم

_has_active_company() -> bool
# للتوافق مع الكود القديم
```