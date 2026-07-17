# دليل الكود — UI / Root: Constants, Font, State, Theme, Main Window

> الملفات الجذرية في `ui/` — ثوابت (مُجمِّع)، خط، حالة، ثيم، النافذة الرئيسية.
> `ui/constants.py`, `ui/font.py`, `ui/app_state.py`, 
> `ui/theme.py`, `ui/main_window.py`
>
> ⚠️ `ui/constants.py` و `ui/theme_manager.py` أصبحا **مُجمِّعات (aggregator packages)**
> لا تحتوي منطقاً فعلياً — المحتوى التفصيلي مذكور في مرجعين منفصلين:
> - ثوابت الدومينات الفعلية → **`ui_constants_data.md`** (`ui/constants_data/*.py`)
> - ألوان الثيمات الفعلية → **`ui_theme_manager_data.md`** (`ui/theme_manager.py` + `ui/theme_manager_data/*.py`)

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [constants](#constants) | `ui/constants.py` (مُجمِّع فقط) |
| [font](#font) | `ui/font.py` |
| [app_state](#app_state) | `ui/app_state.py` |
| [theme](#theme) | `ui/theme.py` |
| [theme_manager](#theme_manager) | إشارة → `ui_theme_manager_data.md` |
| [main_window](#main_window) | `ui/main_window.py` |

---

## constants

### `ui/constants.py`

**[تحديث]** لم يعد يحتوي أي ثوابت مباشرة — أصبح **مُجمِّعاً فقط (aggregator)** يجمع كل ملفات `ui/constants_data/` بنفس واجهة الاستيراد القديمة (`from ui.constants import X` يستمر بالعمل).

```python
from ui.constants_data.constants_general import *
from ui.constants_data.constants_accounting import *
from ui.constants_data.constants_costing import *
from ui.constants_data.constants_design import *
from ui.constants_data.constants_inventory import *
from ui.constants_data.constants_orders import *
from ui.constants_data.constants_companies import *
```

**لا imports خارجية أخرى، ولا منطق.** كل الثوابت الفعلية (`DEFAULT_FONT_SIZE`, `MIN_FONT_SIZE`, `MAX_FONT_SIZE`, `SIDEBAR_EXPANDED_WIDTH`, `WINDOW_DEFAULT_W`, ...إلخ) موجودة الآن في `ui/constants_data/constants_general.py` وبقية ملفات الدومين — راجع **`ui_constants_data.md`** لتفاصيلها الكاملة (كل الثوابت مقسّمة حسب الدومين: general, accounting, costing, design, inventory, orders, companies).

**من يستدعي هذا الملف:** كل ملفات `ui/` تقريباً (عبر `from ui.constants import CONST_NAME`) — الاستيراد لا يزال يعمل بنفس الشكل رغم إعادة الهيكلة الداخلية.

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

**[تحديث] تسلسل القراءة الكامل — الآن عبر `FontService` وسيط (لا DB مباشرة من AppState):**
```
ui/font.py  →  AppState  →  FontService  →  settings_repo  →  DB

get_font_size()
  → _module_font_size (module cache، أسرع — لا I/O)
  → AppState.font_size()
    → _font_size (class cache)
    → AppState._load_font_size() → services.shared.font_service.FontService.load()
      → settings_repo → DB
      → fallback: DEFAULT_FONT_SIZE (try/except على مستوى AppState._load_font_size)
```

**القاعدة الذهبية (موثّقة بالتعليق في الملف):** كل طبقة تكلّم الطبقة اللي تحتها مباشرة فقط —
`font.py` يكلّم `AppState` فقط (لا يعرف `FontService` ولا `DB`)، و`AppState` يكلّم `FontService` فقط (لا يعرف `settings_repo` ولا `DB`)، و`FontService` هو الوحيد الذي يعرف `settings_repo`/`DB`. أي تغيير مستقبلي في طريقة التخزين (مثلاً online/offline) يحدث في `FontService` فقط.

**ثوابت أحجام خط إضافية في `font.py` (module-level، ثابتة لا تتغير بإعدادات المستخدم):**
```python
FS_XS   = 10   # تلميحات صغيرة جداً
FS_SM   = 11   # تسميات ثانوية، وحدات
FS_BASE = 12   # نص أساسي، أزرار، حقول إدخال
FS_MD   = 13   # رؤوس أقسام ونوافذ
FS_LG   = 14   # رؤوس أكبر، أيقونات تفاعلية
FS_XL   = 16   # عناوين رئيسية كبيرة
```
الفرق عن `get_font_size()`: هذه ثوابت لا تتغير مع إعدادات المستخدم (للـ stylesheet الثابت)، بينما `get_font_size()`/`fs()` ديناميكية وتُستخدم في `build_stylesheet()` أو أي مكان يجب أن يعكس تفضيل المستخدم.

---

## app_state

### `ui/app_state.py` — `AppState`

Cache مركزي لإعدادات التطبيق — كل الـ attributes كـ class-level (لا instance). **لا يتواصل مع DB أو `settings_repo` مباشرة أبداً — كل القراءة/الكتابة تمر عبر `FontService`.**

```python
_font_size: int | None = None   # class-level cache
```

```python
AppState.font_size() -> int
# يرجع من cls._font_size لو موجود
# لو None → يستدعي cls._load_font_size() ويخزّن النتيجة

AppState.on_font_changed(size: int)
# يُقيّد بـ [MIN_FONT_SIZE, MAX_FONT_SIZE]
# 1. cls._font_size = size
# 2. يستدعي _set_module_font_cache(size) من ui.font (داخل try/except)
# 3. يستدعي FontService.save(size) من services.shared.font_service (داخل try/except، logger.debug لو فشل)
# 4. يستدعي cls._invalidate_button_cache()
# 5. logger.debug تأكيدي بالقيمة الجديدة

AppState.invalidate()
# cls._font_size = None
# يستدعي invalidate_stylesheet_cache() من ui.theme (داخل try/except)
# fallback لو فشل: يستدعي cls._invalidate_button_cache() مباشرة + logger.debug بالخطأ
# logger.debug تأكيدي "cache cleared"
# يُستدعى من MainWindow._on_company_changed() عند تغيير الشركة النشطة

AppState._load_font_size() -> int   # classmethod — داخلي
# يستدعي FontService.load() من services.shared.font_service (داخل try/except)
# fallback: DEFAULT_FONT_SIZE عند أي exception (مع logger.debug)
# لا يتواصل مع DB مباشرة — الوسيط الوحيد هو FontService

AppState._invalidate_button_cache()   # classmethod — داخلي
# يستدعي invalidate_stylesheet_cache() من ui.widgets.components.button (داخل try/except، logger.debug لو فشل)
```

**من يستدعي هذا الملف:** `ui/font.py` (عبر `get_font_size()`/`set_font_size()`)، `ui/main_window.py` (`_on_company_changed`).

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
# يستدعي invalidate_stylesheet_cache() من ui.widgets.components.button صراحةً (try/except)
# يُطبّق stylesheet على app (أو QApplication.instance() لو app=None)
# [إصلاح ثيم — مركزي] بعد setStyleSheet العام، يمر على كل topLevelWidgets()
#   ويستدعي refresh_table_styles(win) من ui.widgets.tables.tables على كل واحدة
#   لأن أي QTableWidget له stylesheet محلي مباشر (self.table.setStyleSheet(table_style()))
#   لا يتحدث تلقائياً مع QApplication.setStyleSheet() — الحل المركزي يغطي كل الجداول
#   دفعة واحدة بدل الاعتماد على كل widget يعمل refresh بنفسه
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

**مفاتيح `_C`:** العدد كبير جداً (أكثر من 100 مفتاح تغطي: خلفيات، حدود، نصوص، accent، sidebar، حالات success/danger/warning/info، محاسبة (journal/badge/t_account/acc_type)، مستثمرين، audit log، مخزون، تصميمات، BOM scenarios، إلخ). **القائمة الكاملة بقيمها لكل ثيم (light/dark) موجودة في `ui_theme_manager_data.md`** — `theme.py` نفسه لا يعرّف أي مفتاح؛ فقط يقرأها من `_LIGHT_THEME`/`_DARK_THEME` عبر `_C.update()`.

---

## theme_manager

### `ui/theme_manager.py`

**[تحديث]** لم يعد ملفاً واحداً بمنطق مباشر — أصبح **حزمة (package) مُقسَّمة** تحافظ على نفس واجهة الاستيراد القديمة (`from ui.theme_manager import theme_manager, THEMES, ...`).

**للتفاصيل الكاملة (محتوى `_LIGHT_THEME`, `_DARK_THEME`, `CARD_PALETTES`, وكلاس `ThemeManager` بكل methods) راجع المرجع المنفصل: `ui_theme_manager_data.md`.**

ملخص سريع للبنية (بدون تفصيل — التفصيل في المرجع الآخر):
```python
# ui/theme_manager.py يجمّع فقط:
from ui.theme_manager_data._light_theme import _LIGHT_THEME
from ui.theme_manager_data._dark_theme import _DARK_THEME
from ui.theme_manager_data._registry import THEMES, THEME_DISPLAY_NAME_KEYS
from ui.theme_manager_data._card_palettes import CARD_PALETTES
from ui.theme_manager_data._manager import ThemeManager

theme_manager = ThemeManager()   # Singleton — يُستخدم في كل التطبيق
```

**من يستدعي هذا الملف:** `ui/theme.py` (يستورد `_LIGHT_THEME` لملء `_C` الافتراضي)، `SettingsDialog` (لتبديل الثيم)، `main.py` عند بدء التطبيق (`theme_manager.load_from_db()`).

---

## main_window

### `ui/main_window.py`

**الغرض:** النافذة الرئيسية للتطبيق (multi-company). يبني الـ sidebar + stack من الـ sections، ويدير التنقل والتبديل بين الشركات.

**[تحديث جذري]** الإصدار الحالي (v13) يختلف جوهرياً عن الإصدار القديم:
- **لا يوجد `conn_fn` ولا `company_state`** — كل section تفتح اتصال DB الخاص بها بنفسها من الداخل (لا تمرير closure).
- `_try_build_section` أصبحت **بلا try/except فعلي** (معطّلة عمداً — الكود القديم بها موجود كـ تعليق commented-out)، فهي الآن مجرد استدعاء مباشر لـ `builder_fn()`. أي استثناء الآن **ينفجر فعلياً** ولا يتحول لـ placeholder.
- `_make_placeholder_tab` ما زالت موجودة لكنها **لا تُستخدم فعلياً حالياً** لأن `_try_build_section` لا تستدعيها (الكود التعامل معها معطّل بـ comment).

**الـ imports المهمة:**
```python
from ui.widgets.panels.themed_inputs import ThemedFrame
from ui.font import get_font_size, fs
from ui.theme import _C
from ui.widgets.core.events import bus, emit_company_data_changed
from ui.widgets.core.i18n import tr
from .main_window_helper._sidebar import _Sidebar
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    WINDOW_DEFAULT_W, SIDEBAR_COLLAPSED_WIDTH, CONTENT_MIN_WIDTH,
    WINDOW_DEFAULT_H, WINDOW_MIN_H, WINDOW_MIN_CONTENT_W, V_DIVIDER_WIDTH,
)
```

### `_INDEX_MAP` (module-level dict)
```python
_INDEX_MAP: dict[str, int] = {
    "costing": 1, "pricing": 2, "accounting": 3,
    "inventory": 4, "design": 5, "orders": 6,
}
```
عدد العناصر يجب أن يطابق عدد الـ `_builders` في `_build_tabs()` (index يبدأ من 1؛ index 0 دائماً `NoCompanyScreen`).

### دوال top-level مستقلة

**`_make_placeholder_tab(section_name: str, error: str = "") -> QWidget`**
- ينشئ `QWidget` بخلفية `_C['bg_page']` وlayout عمودي مُوسَّط.
- يعرض: label أيقونة (`tr('placeholder_icon')`) بحجم `fs(base, +8)`، ثم label عنوان (`section_name`) بحجم `fs(base, +2)` bold، ثم label فرعي (رسالة الخطأ أو `tr("under_development")`) بحجم `fs(base, -1)` مع `setWordWrap(True)`.
- **[ملاحظة]** موجودة كـ fallback احتياطي فقط — لا تُستدعى فعلياً في التدفق الحالي لأن `_try_build_section` لا تستخدم try/except.

**`_try_build_section(builder_fn, section_name: str) -> QWidget`**
- **حالياً:** `return builder_fn()` مباشرة — بلا حماية.
- الكود الأصلي (معطّل بـ triple-quote/comment) كان يلف الاستدعاء بـ try/except: `ImportError` → placeholder برسالة `f"ImportError: {e}"`، `Exception` عام → placeholder برسالة `f"خطأ: {e}"`. هذا السلوك القديم غير فعّال الآن.

### `MainWindow(QMainWindow, WidgetMixin)`

**`__init__(self, app)`**
- يضبط `self._app`, `self._tabs_built = False`, `self._accounting = None`.
- `setWindowTitle(tr("app_title"))`, `resize(WINDOW_DEFAULT_W, WINDOW_DEFAULT_H)`.
- `setLayoutDirection(Qt.RightToLeft)`.
- `setMinimumSize(SIDEBAR_COLLAPSED_WIDTH + WINDOW_MIN_CONTENT_W, WINDOW_MIN_H)`.
- يستدعي `self._build()`.
- **[إصلاح خلفية فاتحة بعد تبديل الثيم]** يستدعي `self._init_widget_mixin(theme=True, font=False, lang=False, data=False)` — بخلاف قبل، `MainWindow` أصبحت ترث `WidgetMixin` فعلياً حتى تستقبل `bus.theme_changed` وتُحدّث الـ stylesheets المبنية مباشرة داخلها (لأن هذه العناصر لا تتبع أي widget له `WidgetMixin` خاص بها).

**`_refresh_style(self, *_)`** — override قياسي من `WidgetMixin`، يُستدعى تلقائياً عند `bus.theme_changed`:
- يعيد `setStyleSheet` على: `self._central` (`bg_page`)، `self._stack` (`bg_page`)، `self._v_sep` (`border`)، و`self._content_scroll` (stylesheet كامل لـ QScrollArea + scrollbar أفقي).

**`_build(self)`**
- ينشئ `central = QWidget()` مع `setAttribute(Qt.WA_StyledBackground, True)` و`setStyleSheet(bg_page)` — **[إصلاح خلفية بيضاء عامة]** موثّق بالتعليق: بدون هذا، `QWidget` بلا stylesheet يرث خلفية النظام الافتراضية (أبيض) بدل لون الثيم.
- `QHBoxLayout` بلا margins/spacing: `self._sidebar` (`_Sidebar(on_company_changed=self._on_company_changed)`) → فاصل عمودي `ThemedFrame` (VLine، عرض `V_DIVIDER_WIDTH`) → `self._content_scroll` (`QScrollArea`, stretch=1).
- `self._stack = QStackedWidget()` بحد أدنى عرض `CONTENT_MIN_WIDTH`، يُضاف داخل `_content_scroll`.
- index 0 من الـ stack = `NoCompanyScreen()` (من `.tabs.companies.no_company_screen`)، وإشارته `open_manager` مربوطة بفتح `company_selector._open_manager()`.
- يربط كل زر sidebar بـ `self._on_nav(btn)`.
- لو `CompanyService.is_company_ready()` (من `services.companies.company_service`) → يستدعي `self._build_tabs()` فوراً.

### دورة حياة الـ Tabs

**`_build_tabs(self)`**
- لو `self._tabs_built` → يستدعي `self._destroy_tabs()` أولاً.
- يعرّف 6 دوال builder داخلية (closures) بلا أي `conn_fn` — كل واحدة تستورد الـ section class وتبنيها **بدون تمرير أي اتصال DB**:
  ```python
  def _build_costing():    from ui.tabs.costing_section import CostingSection; return CostingSection()
  def _build_pricing():    from ui.tabs.pricing_section import PricingSection; return PricingSection()
  def _build_accounting(): from ui.tabs.accounting_section import AccountingTab; return AccountingTab()
  def _build_inventory():  from ui.tabs.inventory_section import InventoryTab; return InventoryTab()
  def _build_design():     from ui.tabs.design_section import DesignSection; return DesignSection()
  def _build_orders():     from ui.tabs.orders_section import OrdersSection; return OrdersSection()
  ```
- الترتيب في `_builders` list يطابق `_INDEX_MAP` بالضبط (costing, pricing, accounting, inventory, design, orders).
- لكل `(builder_fn, name)` يستدعي `_try_build_section(builder_fn, name)` ويضيف الناتج لـ `self._stack`.
- يحفظ مرجع `AccountingTab` في `self._accounting` لو الـ widget عنده `refresh_for_company` (عبر `hasattr`).
- لو `stack.count() > 1` → `setCurrentIndex(_INDEX_MAP["costing"])` ويُفعّل أول زر sidebar (`setChecked(True)`).
- يستدعي `self._validate_index_map()`، ثم `self._tabs_built = True`.

**`_validate_index_map(self)`**
- لكل `key, idx` في `_INDEX_MAP`: `assert idx < self._stack.count()` — برسالة توضح المفتاح والقيمة المتوقعة لو فشل.

**`_destroy_tabs(self)`**
- `bus.blockSignals(True)` أثناء الإزالة.
- حلقة `while self._stack.count() > 1`: يزيل كل widget من index 1 فصاعداً، `w.hide()` + `w.deleteLater()` داخل try/except.
- `QApplication.processEvents()`، ثم `bus.blockSignals(False)`.
- يستدعي `CompanyService.refresh_connections()` (من `services.companies.company_service`) داخل try/except — يُسجَّل تحذير `logger.warning` لو فشل.
- يُعيد `self._accounting = None` و `self._tabs_built = False`.

**`_refresh_tabs(self)`** — wrapper مباشر: `= self._build_tabs()`.

### الأحداث (Events)

**`_on_company_changed(self, company_id: int)`**
1. `AppState.invalidate()` — مسح `font_size` cache (من `ui.app_state`).
2. يستدعي `CompanyService.get_current_company_name()` ويضبط `setWindowTitle(tr("app_title_company", name=...))`، ثم `self._refresh_tabs()` — داخل try/except، لو فشل يُسجَّل `logger.error` ويتوقف (`return`) بدون إطلاق `emit_company_data_changed`.
3. لو نجح كل شيء → يستدعي `emit_company_data_changed()` (دالة helper من `ui.widgets.core.events`، تتحقق من `is_ready` داخلياً بدل استدعاء `bus.emit` مباشرة).

**`_on_nav(self, clicked_btn)`**
- يُلغي تحديد كل الأزرار الأخرى، يُفعّل `clicked_btn`.
- يقرأ `key = clicked_btn.property("nav_key")`.
- **`key == "settings"`:** `setChecked(False)` على الزر → يفتح `SettingsDialog(self._app, parent=self).exec_()` → بعدها `self._sidebar.refresh_all_buttons()` (تحديث الأزرار + section labels لو تغيّر حجم الخط) → `return` (لا يُغيّر الـ stack).
- **`key == "shared_items"`:** `setChecked(False)` → `self._open_shared_items()` → `return`.
- لو `not self._tabs_built` → `self._stack.setCurrentIndex(0)` (شاشة "لا شركة") → `return`.
- خلاف ذلك، لو `key in _INDEX_MAP` وكان `idx < stack.count()` → `setCurrentIndex(idx)`.

**`_open_shared_items(self)`**
- يستدعي `CompanyService.get_central_conn_and_init()` للحصول على اتصال DB المركزي.
- ينشئ `SharedItemsService(central)` (يهيّئ جداول shared_items عند الإنشاء فقط — لا يُستخدم المرجع بعدها مباشرة).
- ينشئ ويعرض `SharedItemsManagerDialog(central, parent=self)` كـ modal (`exec_()`)، بعد ربط إشارته `items_changed` بـ `emit_company_data_changed`.
- يُغلق `central.close()` بعد إغلاق الـ dialog.

### هيكل الـ Stack (بدون تغيير)
```python
index 0 → NoCompanyScreen
index 1 → CostingSection    ("nav_costing")
index 2 → PricingSection    ("nav_pricing")
index 3 → AccountingTab     ("nav_accounting")
index 4 → InventoryTab      ("nav_inventory")
index 5 → DesignSection     ("nav_design")
index 6 → OrdersSection     ("nav_orders")
```

### بناء الـ Sidebar (تفاصيلها الكاملة في `ui_main_window_helper.md` — هنا الترتيب فقط كما يبنيه `_sidebar.py`)
```python
nav_sections = [
    (tr("nav_section_production"), [
        (tr("nav_icon_costing"), tr("nav_costing"), "costing", ""),
        (tr("nav_icon_pricing"), tr("nav_pricing"), "pricing", ""),
    ]),
    (tr("nav_section_finance"), [
        (tr("nav_icon_accounting"), tr("nav_accounting"), "accounting", ""),
        (tr("nav_icon_inventory"), tr("nav_inventory"), "inventory", ""),
    ]),
    (tr("nav_section_work"), [
        (tr("nav_icon_design"), tr("nav_design"), "design", ""),
        (tr("nav_icon_orders"), tr("nav_orders"), "orders", ""),
    ]),
]
# Footer (بعد divider):
shared_btn:  nav_key="shared_items"
btn_settings: nav_key="settings"
# + _ToggleButton
```

### إضافة Tab جديدة
```python
# 1. في MainWindow._build_tabs() — أضف builder function بلا أي conn_fn:
def _build_my_section():
    from ui.tabs.my_section import MySection
    return MySection()
_builders.append((_build_my_section, tr("nav_my_key")))

# 2. أضف المفتاح في _INDEX_MAP (module-level):
"my_key": N   # N = ترتيب الإضافة في _builders (بعد آخر index حالي)

# 3. في _sidebar._build() — nav_sections (راجع ui_main_window_helper.md):
(tr("nav_icon_my_key"), tr("nav_my_key"), "my_key", "")

# 4. أضف مفاتيح الترجمة المطلوبة (nav_my_key, nav_icon_my_key) في ar/en data files.

# _validate_index_map() يتحقق تلقائياً من التطابق عند كل _build_tabs()
```

---

## علاقات الملفات

- `ui/main_window.py` يستورد `_Sidebar` من `ui/main_window_helper/_sidebar.py` (راجع `ui_main_window_helper.md`).
- `ui/main_window.py` يستورد `_C` من `ui/theme.py`، ويستورد ثوابت من `ui/constants.py` (المُجمِّع → `ui_constants_data.md`).
- `ui/theme.py` يستورد `_LIGHT_THEME` من `ui/theme_manager.py` (المُجمِّع → `ui_theme_manager_data.md`) عند أول import فقط، لملء `_C` الافتراضي.
- `ui/theme.py` لا يستورد من `ui/font.py` مباشرة في التعريف لكنه يستخدم `MIN_FONT_SIZE`/`MAX_FONT_SIZE` من `ui/constants.py`، ويستدعي `_set_module_font_cache(None)` من `ui/font.py` داخل `invalidate_stylesheet_cache()`.
- `ui/font.py` يستورد من `ui/app_state.py` (`AppState.font_size()`, `AppState.on_font_changed()`) — لا يتواصل مع DB أو `FontService` مباشرة.
- `ui/app_state.py` يستورد من `services.shared.font_service.FontService` (خارج `ui/`) ومن `ui/theme.py` (`invalidate_stylesheet_cache`) ومن `ui/widgets/components/button.py` (`invalidate_stylesheet_cache`).
- **نمط الـ Layering المشترك بين `font.py` و`app_state.py`:** كل طبقة تعرف فقط الطبقة التي تحتها مباشرة (`font.py → AppState → FontService → settings_repo → DB`) — لا قفزات في السلسلة.
- `ui/main_window.py` يعتمد على `services.companies.company_service.CompanyService` (خارج `ui/`) بدل `company_state` القديم — `is_company_ready()`, `get_current_company_name()`, `refresh_connections()`, `get_central_conn_and_init()`.
- `ui/main_window.py` يستورد كل الـ sections بشكل lazy (داخل دوال builder) من `ui/tabs/*_section.py` — لا imports علوية لتفادي دورات الاستيراد وتسريع بدء التشغيل.
