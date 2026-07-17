# دليل الكود — UI / Main Window Helper

> `ui/main_window_helper/` — مكونات الـ Sidebar والـ Navigation.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [_sidebar](#_sidebar) | `ui/main_window_helper/_sidebar.py` |
| [_nav_button](#_nav_button) | `ui/main_window_helper/_nav_button.py` |
| [_section_label](#_section_label) | `ui/main_window_helper/_section_label.py` |
| [_toggle_button](#_toggle_button) | `ui/main_window_helper/_toggle_button.py` |

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
كل هذه الثوابت مُعرَّفة الآن في `ui/constants_data/constants_general.py` (راجع `ui_constants_data.md`) — لا يُعاد تعريفها هنا، فقط تُستورد.

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
- **[تحديث]** لم يعد النص/الـ tooltip hardcoded بالعربي — أصبح عبر مفاتيح `tr()` (`sidebar_collapse_icon`, `sidebar_expand_icon`, `sidebar_collapse_tip`, `sidebar_expand_tip`) في `ui/i18n/*_data/*_general.py`، ما يجعله يدعم الإنجليزية تلقائياً.
---

## علاقات الملفات

- `_sidebar.py` يستورد ويستخدم مباشرة: `_SectionLabel` (من `_section_label.py`)، `_NavButton` (من `_nav_button.py`)، `_ToggleButton` (من `_toggle_button.py`) — هو المُنسِّق (orchestrator) الذي يبني كل العناصر الفرعية.
- `_sidebar.py` يستورد `CompanySelector` من `..tabs.companies.company_selector` (خارج نطاق هذا المرجع).
- **نمط مشترك بين الأربعة ملفات:** كل الكلاسات ترث `WidgetMixin` (من `ui.widgets.core.widget_mixin`) وتستدعي `_init_widget_mixin(...)` في `__init__` — هذا يجعلها تستقبل تلقائياً `bus.theme_changed` (عبر `_refresh_style`) و/أو `bus.language_changed` (عبر `_refresh_lang`) بدل الاعتماد على استدعاء يدوي من الخارج. `_sidebar.py` و`_nav_button.py` و`_section_label.py` يعطّلون `lang`/`data` (`lang=False, data=False`) لأنهم لا يحتاجون تحديث لغة مباشر أو بيانات؛ `_toggle_button.py` يترك `lang=True` (الافتراضي) لأن نصه يعتمد على `tr()`.
- كل الملفات تستورد ثوابت من `ui.constants` (المُجمِّع — راجع `ui_constants_data.md` للقيم الفعلية) وألوان من `ui.theme._C` (محلياً داخل دوال `_refresh_style`).
- `ui/main_window.py` يستورد `_Sidebar` فقط من هذا المسار (راجع `ui_root.md`) — لا يتعامل مباشرة مع `_NavButton`/`_SectionLabel`/`_ToggleButton`.
- `_sidebar.refresh_all_buttons()` هو نقطة التكامل الرئيسية بين هذا المسار و`MainWindow._on_nav()` (بعد إغلاق `SettingsDialog`).
