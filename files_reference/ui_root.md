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
# Module-level cache [تحسين 43]
_module_font_size: int | None = None

_set_module_font_cache(size: int | None)
# يُحدّث _module_font_size — للاستخدام الداخلي فقط
# يُستدعى من: get_font_size()، set_font_size()، apply_font()
#              AppState.on_font_changed()، invalidate_stylesheet_cache()

get_font_size() -> int
# 1. يقرأ من _module_font_size (module-level cache — الأسرع)
# 2. لو None → AppState.font_size() ثم يُخزّن في _module_font_size
# لا يقرأ من DB مباشرة أبداً

set_font_size(size: int)
# يُقيّد بـ [MIN_FONT_SIZE, MAX_FONT_SIZE]
# يُحدّث: _set_module_font_cache(size) → AppState.on_font_changed(size) → DB

fs(base: int, delta: int = 0) -> int
# حجم خط نسبي — الحد الأدنى MIN_FONT_SIZE دائماً
# = max(MIN_FONT_SIZE, base + delta)

apply_font(app: QApplication, size: int = None)
# يُطبّق حجم الخط على الـ app عبر build_stylesheet()
# size=None → يستخدم get_font_size()
# يُحدّث الـ cache + AppState + يُعيد بناء stylesheet
```

**تسلسل القراءة:**
```
get_font_size()
  → _module_font_size (module cache، أسرع)
  → AppState.font_size()
    → _font_size (class cache)
    → _load_font_size_from_db()
      → DB → settings["font_size"]
      → fallback: DEFAULT_FONT_SIZE
```

---

## app_state

### `ui/app_state.py` — `AppState`

Cache مركزي لإعدادات التطبيق — كل الـ attributes كـ class-level (لا instance).

```python
_font_size: int | None = None   # class-level cache
```

```python
AppState.font_size() -> int
# يحمّل من DB مرة واحدة ثم يرجع من الـ cache (_font_size)
# يستدعي _load_font_size_from_db() لو _font_size is None

AppState.on_font_changed(size: int)
# يُقيّد بـ [MIN_FONT_SIZE, MAX_FONT_SIZE]
# 1. يُحدّث cls._font_size = size
# 2. يستدعي _set_module_font_cache(size) من ui.font
# 3. يستدعي _invalidate_button_cache()

AppState.invalidate()
# يمسح cls._font_size = None
# يستدعي invalidate_stylesheet_cache() من ui.theme
# fallback لو فشل: يستدعي _invalidate_button_cache() مباشرة
# يُستدعى من MainWindow._on_company_changed() عند تغيير الشركة النشطة

AppState._load_font_size_from_db() -> int   # classmethod — داخلي
# يستخدم get_connection() من db.shared.connection
# لو raw = None → يكتب DEFAULT_FONT_SIZE ويرجعه
# لو القيمة خارج [MIN_FONT_SIZE, MAX_FONT_SIZE] → يُعيد ضبطها → DEFAULT
# يستخدم int(float(raw)) لتحويل النص
# fallback: DEFAULT_FONT_SIZE عند أي exception

AppState._invalidate_button_cache()   # classmethod — داخلي
# يستدعي invalidate_stylesheet_cache() من ui.widgets.components.button
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
           # عبر _init_default_theme() التي تستورد من theme_manager

_ss_cache: dict[tuple, str]   # cache key = (font_size, theme_hash)
_current_theme_hash: str      # يُحسب lazy عند الحاجة

_init_default_theme()
# يُملّي _C بـ _LIGHT_THEME من theme_manager عند أول import
# لا ألوان hardcoded في theme.py — كل الألوان من theme_manager.py

apply_theme(theme_colors: dict, app: QApplication = None)
# يُحدّث _C.update(theme_colors)
# يستدعي invalidate_stylesheet_cache()
# يستدعي invalidate_stylesheet_cache() من ui.widgets.components.button صراحةً
# يُطبّق stylesheet على app (أو QApplication.instance() لو app=None)
# يُستدعى من ThemeManager.set_theme() — لا تستدعه مباشرة

get_theme_color(key: str, fallback: str = "#000000") -> str
# يرجع لون من _C بأمان مع fallback

build_stylesheet(base: int) -> str
# cache key = (font_size, theme_hash) عبر _ss_cache dict
# يُقيّد base بـ [MIN_FONT_SIZE, MAX_FONT_SIZE] من ui.constants
# يبني الـ stylesheet الكامل مقسّماً على دوال مساعدة
# يُعيد النتيجة من الـ cache لو موجودة

invalidate_stylesheet_cache()
# يمسح _ss_cache.clear()
# يُعيد ضبط _current_theme_hash = ""
# يستدعي _set_module_font_cache(None) من ui.font
```

**`_compute_theme_hash()` / `_get_theme_hash()`:**
```python
# يحسب hash من tuple(sorted(_C.items()))
# lazy — يُحسب فقط لو _current_theme_hash فارغ
# يُستخدم كجزء من cache key في build_stylesheet
```

**أقسام الـ stylesheet (الدوال المساعدة):**
```python
_ss_base_reset      # QMainWindow، QWidget، * reset
_ss_message_box     # QMessageBox كامل
_ss_dialog          # QDialog كامل
_ss_typography      # QLabel وكل roles (section, card-title, card-value, badge, mode)
_ss_groupbox        # QGroupBox
_ss_buttons         # QPushButton كل الحالات (hover, pressed, disabled, checked)
_ss_inputs          # QLineEdit, QDoubleSpinBox, QSpinBox, QDateEdit, QTimeEdit
_ss_combobox        # QComboBox + QAbstractItemView
_ss_tables          # QTableWidget + QHeaderView
_ss_tree            # QTreeWidget + QHeaderView
_ss_tabs            # QTabWidget + QTabBar
_ss_scrollbars      # QScrollBar vertical + horizontal (لا parameters غير c)
_ss_misc            # QListWidget, QSplitter, QToolTip, QFrame, QScrollArea,
                    # QProgressBar, QCheckBox, QRadioButton, Sidebar nav overrides
```

**مفاتيح `_C` الكاملة (مُعرَّفة في `theme_manager.py`):**
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

CARD_PALETTES: dict
# {"light": {color_hex: (bg, border), ...}, "dark": {...}}
# نُقلت من colors.py — المصدر الوحيد لألوان البطاقات
# يُستخدم من colors.py في card_colors()

theme_manager = ThemeManager()   # Singleton
```

```python
theme_manager.current_theme -> str   # "light" | "dark"
theme_manager.is_dark -> bool

theme_manager.set_theme(theme_name: str, save: bool = True)
# لو theme_name غير موجود في THEMES → يُعيّن "light"
# لو نفس الثيم الحالي → يرجع بدون فعل شيء
# يُحدّث _current_theme → apply_theme(colors) → _save_to_db() → _emit_theme_changed()
# _emit_theme_changed() يُطلق bus.theme_changed أولاً ثم self.theme_changed

theme_manager.load_from_db()
# يحمّل الثيم المحفوظ + يطبّقه — يُستدعى عند بدء التطبيق
# يُطبّق apply_theme() بدون حفظ

theme_manager.get_available_themes() -> list[{key, name, active}]
```

**تدفق تغيير الثيم:**
```
SettingsDialog._save()
  → theme_manager.set_theme("dark")
    → apply_theme(colors)          # يُحدّث _C + يمسح cache + يُبطل button cache
    → _save_to_db()
    → _emit_theme_changed("dark")  # يُطلق bus.theme_changed
    → self.theme_changed.emit("dark")
```

---

## main_window

### `ui/main_window.py` — `MainWindow`

```python
MainWindow(app: QApplication)
# resize: WINDOW_DEFAULT_W × 820
# setLayoutDirection: Qt.RightToLeft
# setMinimumSize: (SIDEBAR_COLLAPSED_WIDTH + 400, 500)
# يبني الـ stack مع NoCompanyScreen عند index 0
# لو company_state.is_ready عند __init__ → يستدعي _build_tabs() فوراً
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

**سلوكيات `_on_nav()` الخاصة:**
```python
# "settings" → SettingsDialog(self._app, parent=self).exec_()
#              ثم self._sidebar.refresh_all_buttons()   ← يُحدّث الأزرار والـ labels
#              setChecked(False) على الزر المُضغط
#              لا يُغيّر الـ stack

# "shared_items" → self._open_shared_items()
#                  setChecked(False) على الزر المُضغط
#                  يفتح central DB + SharedItemsManagerDialog
#                  يربط items_changed بـ emit_company_data_changed
```

**`_on_company_changed(company_id: int)`:**
```python
# 1. AppState.invalidate()       — مسح font_size cache (كل شركة ممكن ليها إعداد مختلف)
# 2. setWindowTitle(company_name)
# 3. self._refresh_tabs()        — = _build_tabs()
# 4. bus.company_data_changed.emit(company_id)
```

**حماية من فشل الـ import:**
```python
_try_build_section(builder_fn, section_name) -> QWidget
# يلف builder_fn() في try/except
# ImportError → placeholder مع رسالة f"ImportError: {e}"
# Exception   → placeholder مع رسالة f"خطأ: {e}"
# يضمن أن فشل section واحد لا يمنع بقية الـ sections

_make_placeholder_tab(section_name: str, error: str = "") -> QWidget
# يعرض: أيقونة 🚧 + عنوان f"قسم {section_name}" + رسالة الخطأ أو "قيد التطوير"
# يقرأ get_font_size() الحالي لبناء الـ styles
```

**دورة حياة الـ tabs:**
```python
_build_tabs()
# لو _tabs_built → يستدعي _destroy_tabs() أولاً
# يجلب conn من company_state.get_erp_conn() — لو فشل conn = None
# يبني كل section بـ _try_build_section() مع closure: conn_fn=lambda: conn
# يذهب لـ index 1 (لو stack.count() > 1) ويُفعّل أول زر في الـ sidebar
# يُشغّل _validate_index_map() للتحقق من صحة الـ indices
# يضبط self._tabs_built = True

_validate_index_map()
# assert أن كل index في index_map < stack.count()
# يُثير AssertionError برسالة واضحة لو فشل

_destroy_tabs()
# bus.blockSignals(True) أثناء الإزالة
# يُزيل كل widgets من index 1 فصاعداً (يبقي index 0 = NoCompanyScreen)
# w.hide() + w.deleteLater() على كل widget — في try/except
# QApplication.processEvents()
# bus.blockSignals(False)
# يستدعي company_state.refresh_connections()  ← [إصلاح B]
# يُعيد ضبط self._accounting = None + self._tabs_built = False

_refresh_tabs()
# = self._build_tabs()  (wrapper مباشر)
```

**بناء الـ Sidebar (من `_sidebar.py`):**
```python
# nav_sections بالترتيب:
("الإنتاج", [
    ("📊", "حساب التكلفة", "costing",    ""),
    ("💰", "التسعير",       "pricing",    ""),
]),
("المالية", [
    ("🏦", "الحسابات",     "accounting", ""),
    ("📦", "المخزن",        "inventory",  ""),
]),
("العمل", [
    ("🎨", "التصميمات",    "design",     ""),
    ("📋", "الطلبات",       "orders",     ""),
]),
# Footer (بعد divider):
("🔗", "العناصر المشتركة", "shared_items", "")
("⚙️", "الإعدادات",        "settings",     "")
# + _ToggleButton
```

**إضافة Tab جديدة:**
```python
# 1. في _build_tabs() — أضف builder function + أضفه لـ _builders:
def _build_my_section():
    from ui.tabs.my_section import MySection
    return MySection(conn_fn=lambda: conn)
_builders.append((_build_my_section, "اسم القسم"))

# 2. في index_map:
"my_key": N   # N = موقع في _builders + 1

# 3. في _sidebar._build() — nav_sections:
("اسم القسم", [("🔑", "اسم القسم", "my_key", "")])

# _validate_index_map() يتحقق تلقائياً عند كل _build_tabs()
```