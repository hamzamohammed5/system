# دليل الكود — UI / Main Window

> `ui/main_window.py` + كل ملفات `ui/main_window_helper/*.py` (4 ملفات).
> النافذة الرئيسية للتطبيق (multi-company) وكل مكوّنات الـ Sidebar والـ Navigation التابعة لها.
>
> نفس مبدأ `ui_constants.md`/`ui_theme_manager.md`: `main_window.py` ملف جذري في `ui/*.py`
> وله مجلد فرعي مخصص (`ui/main_window_helper/`) يغطيه هذا المرجع بالكامل مع الملف الجذري نفسه.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [main_window](#main_window) | `ui/main_window.py` |
| [_sidebar](#_sidebar) | `ui/main_window_helper/_sidebar.py` |
| [_nav_button](#_nav_button) | `ui/main_window_helper/_nav_button.py` |
| [_section_label](#_section_label) | `ui/main_window_helper/_section_label.py` |
| [_toggle_button](#_toggle_button) | `ui/main_window_helper/_toggle_button.py` |

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
كل هذه الثوابت مُعرَّفة الآن في `ui/constants_data/constants_general.py` — راجع `ui_constants.md` لتفاصيلها؛ هنا فقط تُستورد.

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

### بناء الـ Sidebar (الترتيب كما يبنيه `_sidebar.py` — التفاصيل الكاملة أدناه في قسم `_sidebar`)
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

# 3. في _sidebar._build() — nav_sections (راجع قسم _sidebar أدناه):
(tr("nav_icon_my_key"), tr("nav_my_key"), "my_key", "")

# 4. أضف مفاتيح الترجمة المطلوبة (nav_my_key, nav_icon_my_key) في ar/en data files (راجع ui_i18n.md).

# _validate_index_map() يتحقق تلقائياً من التطابق عند كل _build_tabs()
```

---

## _sidebar

### `ui/main_window_helper/_sidebar.py` — `_Sidebar(ThemedFrame, WidgetMixin)`

**[تحديث]** يرث الآن من `ThemedFrame` (من `ui.widgets.panels.themed_inputs`) و `WidgetMixin` (من `ui.widgets.core.widget_mixin`) بدل `QFrame` عادي — يستقبل تحديث الثيم تلقائياً عبر `_refresh_style()`.

```python
_Sidebar(on_company_changed: callable, parent=None)
# ThemedFrame + WidgetMixin — الشريط الجانبي الرئيسي للتطبيق
# self._collapsed = False في البداية
# setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
# setSizePolicy(Fixed, Expanding)
# self._buttons: list = []، self._section_labels: list = []
# يستدعي self._build() ثم self._init_widget_mixin(lang=False, data=False) ثم self._refresh_style()

sidebar._refresh_style(*_)
# [WidgetMixin override] يُستدعى تلقائياً عند bus.theme_changed
# يعيد تطبيق: self (background+border-left)، _company_selector (لو موجود)،
#   _nav_scroll (QScrollArea + scrollbar stylesheet)، _div (الفاصل الأفقي)
# كل الألوان من _C الحالي (sidebar_bg, sidebar_border, border_med لخط الـ scrollbar)

sidebar.refresh_all_buttons()
# [تحسين 20] يُحدّث أحجام كل الأزرار عبر btn.refresh_sizes()
#             ثم يستدعي lbl._apply_style() على كل _SectionLabel
# يُستدعى من MainWindow._on_nav() بعد SettingsDialog
# القديم: كان يُحدّث الأزرار فقط ويتجاهل الـ section labels
# الجديد: يضمن أن الـ section labels تتحدث مع الأزرار عند تغيير حجم الخط

sidebar.get_buttons() -> list[_NavButton]
sidebar.get_company_selector() -> CompanySelector
```

**`_build(self)` — بناء الهيكل الكامل:**
- `QVBoxLayout` بلا margins/spacing.
- **Header:** `CompanySelector()` (من `..tabs.companies.company_selector`)، ارتفاع ثابت `SIDEBAR_COMPANY_H`، إشارته `company_changed` مربوطة بـ `self._on_company_changed`.
- **Nav Scroll:** `QScrollArea` (`setWidgetResizable(True)`, scrollbar أفقي معطّل دائماً، عمودي `AsNeeded`) يحتوي `nav_widget` بـ `QVBoxLayout` (margins/spacing = `SIDEBAR_NAV_MARGIN`/`SIDEBAR_NAV_SPACING`).
  - يبني `nav_sections` (قائمة من `(section_name, items)`) عبر استدعاءات `tr(...)` مباشرة عند البناء (وليس نصوص عربية مباشرة كما في النسخة القديمة).
  - لكل قسم: `_SectionLabel(section_name)` يُضاف لـ `self._section_labels`، ثم لكل item: `_NavButton(icon, label, badge)` مع `setProperty("nav_key", key)`, عرض `SIDEBAR_EXPANDED_WIDTH - NAV_BTN_W_OFFSET`, ارتفاع `NAV_BTN_H` — يُضاف لـ `self._buttons`.
  - `nav_lay.addSpacing(SPACING_XS)` ثم `addStretch()`.
- **Footer:** `QWidget` شفاف بـ `QVBoxLayout` (margins/spacing = `SIDEBAR_FOOTER_MARGIN_H/V`/`SIDEBAR_FOOTER_SPACING`):
  - `self._div = ThemedFrame()` (HLine، ارتفاع `SIDEBAR_DIVIDER_H`).
  - `shared_btn` (`nav_key="shared_items"`)، `btn_settings` (`nav_key="settings"`) — نفس الأبعاد كأزرار الـ nav.
  - `self._toggle_btn = _ToggleButton()` بعرض `SIDEBAR_EXPANDED_WIDTH`، مربوط بـ `self._on_toggle`.

**State الداخلي:**
```python
self._buttons: list         # كل _NavButton في الـ nav + footer
self._section_labels: list  # كل _SectionLabel (الإنتاج / المالية / العمل)
self._collapsed: bool       # حالة الطي الحالية
self._company_selector      # CompanySelector في الهيدر
self._nav_scroll             # QScrollArea المحتوي على الأزرار
self._div                    # ThemedFrame الفاصل الأفقي في الفوتر
self._toggle_btn             # _ToggleButton في الفوتر
```

**أقسام Nav الفعلية (كما تُبنى في `_build()`، القيم عبر `tr()` — القيم المعروضة بالعربي افتراضياً):**
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
tr("nav_icon_shared"), tr("nav_shared")     → nav_key="shared_items"
tr("nav_icon_settings"), tr("nav_settings") → nav_key="settings"
# + _ToggleButton
```

**`_on_toggle(self)` — Animation عند الطي/الفرد:**
```python
# self._collapsed = self._toggle_btn.toggle_state()
# target = SIDEBAR_COLLAPSED_WIDTH لو collapsed else SIDEBAR_EXPANDED_WIDTH
# يُشغّل QPropertyAnimation منفصلين على minimumWidth و maximumWidth (self._anim_min, self._anim_max)
# مدة SIDEBAR_ANIM_DURATION (200ms)، QEasingCurve.InOutCubic
# startValue = self.width()، endValue = target
# يُخفي/يُظهر _company_selector (setVisible(not collapsed))
# يستدعي btn.set_collapsed(collapsed) على كل self._buttons
# يستدعي lbl.set_collapsed(collapsed) على كل self._section_labels
# self._toggle_btn.setFixedWidth(target)
```

**`refresh_all_buttons()` — التدفق الكامل:**
```python
for btn in self._buttons:
    btn.refresh_sizes()
    if self._collapsed:
        btn.set_collapsed(True)

# [تحسين 20] تحديث section labels بعد الأزرار
for lbl in self._section_labels:
    lbl._apply_style()
```

---

## _nav_button

### `ui/main_window_helper/_nav_button.py` — `_NavButton(QPushButton, WidgetMixin)`

```python
_NavButton(icon: str, label: str, badge: str = "", parent=None)
# checkable=True، cursor=PointingHandCursor
# sizePolicy(Fixed, Fixed)
# self._icon, self._label, self._badge = icon, label, badge
# self._collapsed = False
# يستدعي self._build_content() ثم self._init_widget_mixin(lang=False, data=False) ثم self._refresh_style()

btn._build_content(self)
# QHBoxLayout: margins (NAV_LAYOUT_MARGIN_H, 0, NAV_LAYOUT_MARGIN_H, 0)، spacing NAV_LAYOUT_SPACING
# alignment: AlignVCenter
# self._ico_lbl = QLabel(icon)، عرض ثابت NAV_ICO_W، محاذاة وسط
# self._txt_lbl = QLabel(label)، محاذاة يمين+وسط رأسي، wordWrap=False
# self._badge_lbl = QLabel(badge)، visible=bool(badge)، محاذاة وسط
# ترتيب الإضافة: addWidget(_txt_lbl, stretch=1) → addWidget(_badge_lbl) → addWidget(_ico_lbl)

btn._refresh_style(*_)
# [WidgetMixin override] يُستدعى عند bus.theme_changed
# يعيد stylesheet لـ _ico_lbl و _txt_lbl (لون sidebar_text)
# يستدعي self._apply_badge_style()
# يستدعي self._update_style()

btn._apply_badge_style(self)
# [إصلاح ألوان] يُطبّق badge stylesheet من _C الحالي:
#   background: _C['danger']، color: _C['bg_input']  (بدل hardcoded "#C0392B"/"#FFF" سابقاً)
#   font-size: BADGE_FS، font-weight: 700
#   padding: NAV_BADGE_PAD_V/H، border-radius: NAV_BADGE_RADIUS
# يُستدعى من: _refresh_style() عند الثيم، refresh_sizes() عند تغيير حجم الخط

btn.set_badge(text: str)
# self._badge = text؛ يُحدّث النص والـ visibility (bool(text) and not self._collapsed)

btn.set_collapsed(collapsed: bool)
# collapsed=True  → عرض SIDEBAR_COLLAPSED_WIDTH، يُخفي _txt_lbl و_badge_lbl
#                   layout margins (0,0,0,0)، alignment AlignCenter
# collapsed=False → عرض SIDEBAR_EXPANDED_WIDTH - NAV_BTN_W_OFFSET، يُظهر النص (والـ badge لو موجود)
#                   layout margins (NAV_LAYOUT_MARGIN_H, 0, NAV_LAYOUT_MARGIN_H, 0)، alignment AlignVCenter

btn.setChecked(v: bool)
# super().setChecked(v) ثم self._update_style()

btn._update_style(self)
# لو isChecked(): خلفية sidebar_active + border-right accent (NAV_ACTIVE_BORDER_W) + bold
#                 لون الأيقونة accent_mid، لون النص sidebar_text bold
# لو غير checked: خلفية transparent + hover sidebar_hover
#                 لون الأيقونة sidebar_muted، لون النص sidebar_text (وزن عادي)
# كل الأحجام (NAV_ICO_FS, NAV_BTN_H, NAV_BTN_BORDER_RADIUS) من ui.constants

btn.refresh_sizes(self)
# base = get_font_size()
# font-size الأيقونة = fs(base, +4)pt، font-size النص = base pt
# الارتفاع = max(NAV_BTN_H, base*2 + NAV_BTN_HEIGHT_PAD)
# لو غير مطوي → setFixedWidth(SIDEBAR_EXPANDED_WIDTH - NAV_BTN_W_OFFSET)
# [إصلاح] يستدعي self._apply_badge_style() في النهاية — إعادة تطبيق ألوان الـ badge
#   لأن حجم الخط ممكن يتغير مع تغيير الثيم أيضاً
```

**هيكل المحتوى الداخلي (HBoxLayout — RTL):**
```
[ _txt_lbl (stretch=1) | _badge_lbl | _ico_lbl (NAV_ICO_W px) ]
```

**Imports المهمة:**
```python
from ui.font      import get_font_size, fs
from ui.constants import (
    SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH,
    NAV_BTN_H, NAV_BTN_W_OFFSET, NAV_ICO_W, NAV_ICO_FS,
    NAV_BTN_HEIGHT_PAD, BADGE_FS, NAV_LAYOUT_MARGIN_H, NAV_LAYOUT_SPACING,
    NAV_BTN_BORDER_RADIUS, NAV_ACTIVE_BORDER_W,
    NAV_BADGE_PAD_V, NAV_BADGE_PAD_H, NAV_BADGE_RADIUS,
)
from ui.widgets.core.widget_mixin import WidgetMixin
```
كل هذه الثوابت مُعرَّفة الآن في `ui/constants_data/constants_general.py` (راجع `ui_constants.md`) — لا يُعاد تعريفها هنا، فقط تُستورد.

---

## _section_label

### `ui/main_window_helper/_section_label.py` — `_SectionLabel(QLabel, WidgetMixin)`

**[تحديث]** أصبحت `WidgetMixin` بدل `QLabel` عادي — تستقبل تحديث الثيم تلقائياً عبر `_refresh_style()` (بخلاف السابق الذي كان يعتمد فقط على استدعاء يدوي).

```python
_SectionLabel(text: str, parent=None)
# QLabel(text.upper(), parent) + WidgetMixin
# عنوان قسم مُصغَّر (uppercase) داخل الـ sidebar
# يستدعي self._init_widget_mixin(lang=False, data=False) ثم self._refresh_style() في __init__

lbl._refresh_style(self, *_)
# [WidgetMixin override] يُستدعى تلقائياً عند bus.theme_changed
# يقرأ base = get_font_size() الحالي ويُعيد بناء الـ stylesheet كاملاً في كل استدعاء
# القيم من ui.constants: SECTION_LABEL_PAD_TOP/H/BOT، SECTION_LABEL_LTR_SPACING

lbl._apply_style = lbl._refresh_style   # alias! [توافق مع الكود القائم]
# تعريف صريح: _apply_style = _refresh_style (نفس الدالة بمرجعين)
# للتوافق مع استدعاء _sidebar.refresh_all_buttons() القديم الذي ينادي lbl._apply_style()

lbl.set_collapsed(collapsed: bool)
# self.setVisible(not collapsed)
```

**Style (يُحسب في كل استدعاء لـ `_refresh_style()`/`_apply_style()`):**
```python
base = get_font_size()   # يُقرأ في كل استدعاء — يعكس الحجم الحالي دائماً
# color:          _C['sidebar_muted']
# font-size:      fs(base, -2)pt
# font-weight:    700
# letter-spacing: SECTION_LABEL_LTR_SPACING (من ui.constants)
# padding:        SECTION_LABEL_PAD_TOP px SECTION_LABEL_PAD_H px SECTION_LABEL_PAD_BOT px SECTION_LABEL_PAD_H px
# background:     transparent
# border:         none
```

**Imports:**
```python
from ui.font import fs, get_font_size
from ui.constants import (
    SECTION_LABEL_PAD_TOP, SECTION_LABEL_PAD_H,
    SECTION_LABEL_PAD_BOT, SECTION_LABEL_LTR_SPACING,
)
from ui.widgets.core.widget_mixin import WidgetMixin
# ملاحظة: _C يُستورد محلياً (import from ui.theme) داخل _refresh_style() نفسها، وليس على مستوى الملف
```

**ملاحظات من التعليقات:**
- `[Refactor V3]` إصلاح imports: `ui.app_settings` → `ui.theme` + `ui.font`.
- `[Refactor V4]` تحويل `_SectionLabel` إلى `WidgetMixin` لتحديث تلقائي عند تغيير الثيم/الخط (بدل الاعتماد على استدعاء يدوي فقط).

---

## _toggle_button

### `ui/main_window_helper/_toggle_button.py` — `_ToggleButton(QPushButton, WidgetMixin)`

```python
_ToggleButton(parent=None)
# self._collapsed = False
# setFixedHeight(SIDEBAR_TOGGLE_H)، cursor=PointingHandCursor
# يستدعي self._init_widget_mixin(data=False) — يترك lang/theme مفعّلين (افتراضي True)
# ثم self._refresh_lang() و self._refresh_style() صراحة في __init__

btn._refresh_style(self, *_)
# [WidgetMixin override] يُستدعى تلقائياً عند bus.theme_changed
# background: transparent
# border-top: SIDEBAR_TOGGLE_BORDER_W px solid _C['sidebar_border']
# color: _C['sidebar_muted']، font-size: FS_SM pt (من ui.font)
# hover: background _C['sidebar_hover']، color _C['sidebar_text']

btn._refresh_lang(self, *_)
# [WidgetMixin override] يُستدعى تلقائياً عند bus.language_changed (ومن __init__ يدوياً)
# النص: tr('sidebar_collapse_icon') لو غير مطوي، else tr('sidebar_expand_icon')
# Tooltip: tr('sidebar_collapse_tip') لو غير مطوي، else tr('sidebar_expand_tip')
# يستورد tr من ui.widgets.core.i18n محلياً داخل الدالة

btn.toggle_state(self) -> bool
# self._collapsed = not self._collapsed
# يستدعي self._refresh_lang() لتحديث النص/الـ tooltip فوراً
# يرجع self._collapsed (الحالة الجديدة)
```

**Imports:**
```python
from ui.constants import SIDEBAR_TOGGLE_H, SIDEBAR_TOGGLE_BORDER_W
from ui.font import FS_SM
from ui.widgets.core.widget_mixin import WidgetMixin
# ملاحظة: _C يُستورد محلياً (from ui.theme import _C) داخل _refresh_style() فقط
```

**ملاحظات من التعليقات:**
- `[Refactor V3]` إصلاح imports: `ui.app_settings` → `ui.theme`.
- **[تحديث]** لم يعد النص/الـ tooltip hardcoded بالعربي — أصبح عبر مفاتيح `tr()` (`sidebar_collapse_icon`, `sidebar_expand_icon`, `sidebar_collapse_tip`, `sidebar_expand_tip`) في `ui/i18n/*_data/*_general.py` (راجع `ui_i18n.md`)، ما يجعله يدعم الإنجليزية تلقائياً.

---

## علاقات الملفات

- `ui/main_window.py` يستورد `_Sidebar` من `ui/main_window_helper/_sidebar.py` مباشرة — هو المستهلك الوحيد المتوقع لهذا المجلد الفرعي من خارجه.
- `_sidebar.py` يستورد ويستخدم مباشرة: `_SectionLabel` (من `_section_label.py`)، `_NavButton` (من `_nav_button.py`)، `_ToggleButton` (من `_toggle_button.py`) — هو المُنسِّق (orchestrator) الذي يبني كل العناصر الفرعية داخل `main_window_helper/`.
- `_sidebar.py` يستورد أيضاً `CompanySelector` من `..tabs.companies.company_selector` (خارج نطاق هذا المرجع).
- **نمط مشترك بين الأربعة ملفات الفرعية:** كل الكلاسات ترث `WidgetMixin` (من `ui.widgets.core.widget_mixin`) وتستدعي `_init_widget_mixin(...)` في `__init__` — هذا يجعلها تستقبل تلقائياً `bus.theme_changed` (عبر `_refresh_style`) و/أو `bus.language_changed` (عبر `_refresh_lang`) بدل الاعتماد على استدعاء يدوي من الخارج. `_sidebar.py` و`_nav_button.py` و`_section_label.py` يعطّلون `lang`/`data` (`lang=False, data=False`) لأنهم لا يحتاجون تحديث لغة مباشر أو بيانات؛ `_toggle_button.py` يترك `lang=True` (الافتراضي) لأن نصه يعتمد على `tr()`.
- كل الملفات (الجذري والأربعة الفرعية) تستورد ثوابت من `ui.constants` (المُجمِّع — راجع `ui_constants.md` للقيم الفعلية) وألوان من `ui.theme._C` (محلياً داخل دوال `_refresh_style`).
- `_sidebar.refresh_all_buttons()` هو نقطة التكامل الرئيسية بين `main_window_helper/` و`MainWindow._on_nav()` (بعد إغلاق `SettingsDialog`) — التسلسل: `MainWindow` → `_Sidebar.refresh_all_buttons()` → `_NavButton.refresh_sizes()` لكل زر → `_SectionLabel._apply_style()` لكل label.
- `MainWindow._on_company_changed()` يستدعي `AppState.invalidate()` (من `ui/app_state.py`، راجع `ui_root.md`) و`ui.theme._C` (راجع `ui_root.md`) — تبعية مباشرة على مرجعي `ui_root.md`.
- `MainWindow.__init__` يستدعي `ui.theme_manager` بشكل غير مباشر عبر تحميل الثيم عند بدء التطبيق (`theme_manager.load_from_db()` من `main.py`، خارج نطاق هذا المرجع) — راجع `ui_theme_manager.md`.
- `MainWindow` يعتمد على `services.companies.company_service.CompanyService` (خارج `ui/`) — `is_company_ready()`, `get_current_company_name()`, `refresh_connections()`, `get_central_conn_and_init()`.
- `MainWindow` يستورد كل الـ sections بشكل lazy (داخل دوال builder) من `ui/tabs/*_section.py` — لا imports علوية لتفادي دورات الاستيراد وتسريع بدء التشغيل.
- `MainWindow` يستورد أيضاً `NoCompanyScreen` (من `.tabs.companies.no_company_screen`)، `SettingsDialog` (من `ui.widgets.dialogs.settings_dialog`، محلي داخل `_on_nav`)، و`SharedItemsManagerDialog`/`SharedItemsService` (محلي داخل `_open_shared_items`) — كلها خارج نطاق هذا المرجع.

---

## من يستدعي ملفات هذا المرجع من خارجه

- `main.py` — ينشئ `MainWindow` مباشرة (نقطة الدخول الوحيدة)
- `ui/root.py` / `ui/app_state.py` — يُستدعيان من `MainWindow._on_company_changed()` عبر `AppState.invalidate()`
- `ui/theme.py` — يُستدعى من `MainWindow` عند `_refresh_style`
- `ui/tabs/companies/company_selector.py` — يُستورد في `_sidebar.py` (خارج هذا المرجع)
