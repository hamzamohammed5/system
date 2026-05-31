# خطة Refactoring V3
> تنظيم معماري شامل — مبدأ Single Responsibility لكل ملف، بدون تكرار، imports صحيحة

---

## المشاكل المكتشفة

### 1. ملفات بأكتر من وظيفة واحدة

| الملف | الوظائف الموجودة | المشكلة |
|-------|-----------------|---------|
| `ui/widgets/theme/styles.py` | stylesheet generators + dividers (h_divider/v_divider) + scroll wrapper + card styles + tab styles + label styles | ملف ضخم جداً — يجمع كل الـ stylesheets في مكان واحد بدون تقسيم منطقي |
| `ui/widgets/components/stat_row.py` | BadgeLabel + StatCard + StatusChip + StatItem + _StatCard + StatRow + StatusCard + دوال مساعدة | 7 classes في ملف واحد — بعضها مختلف وظيفياً |
| `ui/widgets/components/headers.py` | SectionHeader + PageHeader + DetailHeader + ListHeader + SearchBar + StatusBar | 6 components مختلفة في ملف واحد |
| `ui/widgets/components/label.py` | InfoRow + ModeLabel + AmountLabel + DebitCreditDisplay + BalanceDisplay + ProgressBar + MultiProgressBar + دوال تنسيق | مزيج من labels ومبالغ وـ progress bars |
| `ui/widgets/panels/form_parts.py` | label builders + row builders + spin fields + FormGroup + ResultBadge + ModeBadge + InlinePreview + CrudButtonsBar + ModeLabel import | كل أدوات الفورمات في ملف واحد |
| `ui/widgets/tables/tables.py` | أدوات الخلايا (make_item, bold_item...) + builders (make_table, make_list_table...) + fit functions | دمج builders و items في ملف واحد |
| `ui/widgets/panels/layout_widgets.py` | CardGrid + CollapsibleCard | مقبول — وظيفتان متقاربتان |
| `ui/widgets/panels/detail_section.py` | DetailSection + make_detail_row + TwoColDetails | مقبول — كلها عرض تفاصيل |
| `ui/widgets/mixins/data_mixins.py` | RefreshableMixin + RebuildMixin + SelectionMixin | 3 mixins مختلفة دُمجت في ملف واحد |
| `ui/widgets/mixins/form_mixins.py` | EditModeMixin + FormValidationMixin | مقبول — كلهم فورم |
| `ui/widgets/dialogs/dialogs_base.py` | DialogShell + BaseDialog | مقبول — base classes |
| `ui/widgets/core/conn.py` | LiveConnMixin + SafeConnMixin + DualConnMixin + دوال مساعدة | 3 connection strategies في ملف واحد — لكن مترابطة |
| `ui/widgets/combo/unit.py` | UnitCombo widget + load_units + save_units + add_unit + remove_unit + cache management | widget + business logic + data access في ملف واحد |
| `ui/widgets/combo/category.py` | CategoryCombo widget + populate_category_combo | مقبول — ملف صغير |

---

### 2. وظائف متوزعة على أكتر من ملف

| الوظيفة | الملفات | المشكلة |
|---------|---------|---------|
| **Tooltip utilities** | `ui/widgets/utils/tooltip.py` + `ui/widgets/tables/flexible.py` (refresh_tooltips) | نفس الوظيفة في مكانين |
| **Table empty state** | `ui/widgets/panels/state.py` (set_table_empty_state) + `ui/widgets/panels/data_table.py` (empty state logic) | منطق الـ empty state متوزع |
| **Connection helpers** | `ui/widgets/core/conn.py` + `ui/widgets/core/events.py` (get_active_company_id) | قراءة الـ connection/company موزعة |
| **Bus connection** | `ui/widgets/mixins/bus.py` + `ui/widgets/core/events.py` | emit_company_data_changed موجودة في events لكن bus logic في bus.py |
| **ModeLabel** | معرّفة في `ui/widgets/components/label.py` + مستوردة في `ui/widgets/panels/form_parts.py` كـ re-export | re-export غير ضروري |
| **CrudSection** | `ui/widgets/base/section.py` (BaseSection) + `ui/widgets/panels/crud_section.py` (CrudSection) | نفس الـ pattern في مكانين — BaseSection هي الـ base وCrudSection copy شبه مطابق |
| **Splitter style** | `ui/widgets/theme/styles.py` (splitter_style) + `ui/widgets/utils/splitter.py` (يستوردها) | مقبول — استخدام صح |
| **Filter logic** | `ui/widgets/panels/filter.py` + `ui/widgets/base/list_panel.py` (_match_date, _get_search_query) | جزء من الفلترة في list_panel والباقي في filter.py |

---

### 3. تكرار في المسؤوليات (Duplicate Responsibility)

| المشكلة | التفاصيل |
|---------|---------|
| **CrudSection vs BaseSection** | `BaseSection` في `base/section.py` و`CrudSection` في `panels/crud_section.py` — كلاهما نفس الـ layout (list + detail + optional form). CrudSection قديم يجب أن يصبح alias فقط |
| **EmptyPanelState vs EmptyState** | في `panels/state.py` — EmptyPanelState هي دالة تبني EmptyState، لكن الاسم مختلف يسبب confusion |
| **table_style في styles.py vs make_list_table في tables.py** | الـ stylesheet للجداول معرّف في styles.py لكن جزء منه يُعاد تعريفه في make_list_table |
| **scroll_style** | معرّفة في `theme/styles.py` وتُستخدم في أماكن كثيرة — هذا صح، لكن بعض الـ widgets تكتب scroll styles يدوياً |

---

### 4. مشاكل الـ Imports

| الملف | المشكلة | التصحيح |
|-------|---------|---------|
| `ui/widgets/panels/filter.py` | يستورد من `ui.theme` و`ui.font` مباشرة بدل `ui.app_settings` | استخدم `from ui.app_settings import _C, fs, get_font_size` |
| `ui/widgets/panels/filter.py` | يستورد `blocked_signals` من `..utils.ui_utils` — هذا الملف غير موجود في الكود المعروض | يجب أن يكون `from ..utils.signals import blocked_signals` |
| `ui/widgets/panels/filter.py` | يستورد `input_style` من `..styles` — لكن styles.py في `theme/styles.py` | يجب `from ..theme.styles import input_style` |
| `ui/widgets/panels/detail_section.py` | يستورد من `ui.theme` و`ui.font` | استخدم `from ui.app_settings import _C, fs, get_font_size` |
| `ui/widgets/panels/layout_widgets.py` | يستورد من `ui.theme` و`ui.font` + `from ..styles import` | استخدم `from ui.app_settings import` + `from ..theme.styles import` |
| `ui/widgets/panels/state.py` | يستورد من `ui.theme` و`ui.font` | استخدم `from ui.app_settings import _C, fs, get_font_size` |
| `ui/widgets/panels/data_table.py` | يستورد `from ..tables.tables import` و`from ..styles import` — لكن styles في `theme/styles` | `from ..theme.styles import` |
| `ui/widgets/panels/crud_section.py` | يستورد `from ..styles import splitter_style` | يجب `from ..theme.styles import splitter_style` |
| `ui/widgets/panels/form_parts.py` | يستورد من `ui.theme` و`ui.font` | استخدم `from ui.app_settings import` |
| `ui/widgets/base/detail_panel.py` | يستورد `from ..tables.builders import` — لكن builders.py اتدمج في `tables/tables.py` | يجب `from ..tables.tables import` |
| `ui/widgets/base/list_panel.py` | يستورد `from ..tables.builders import` — نفس المشكلة | يجب `from ..tables.tables import` |

---

## التغييرات المطلوبة

---

### تغيير 1 — تقسيم `ui/widgets/theme/styles.py`

**المشكلة:** ملف ضخم جداً يحتوي على كل أنواع الـ stylesheets.

**الحل:** تقسيمه حسب المسؤولية:

```
ui/widgets/theme/
├── styles.py          ← يفضل كـ entry point للـ re-exports فقط
├── input_styles.py    ← input_style, spinbox_style, search_input_style
├── table_styles.py    ← table_style, splitter_style, ROW_HEIGHT_*
├── card_styles.py     ← card_style, status_card_style, group_box_style
├── label_styles.py    ← status_label_style, muted_label_style, section_title_style, icon_btn_style, link_btn_style
├── layout_styles.py   ← tab_style, scroll_style, filter_bar_style, toolbar_style, tree_style, list_style
└── builders.py        ← h_divider, v_divider, wrap_in_scroll (دوال تبني widgets)
```

> **ملاحظة:** `styles.py` يبقى موجوداً ويعمل re-export لكل الدوال للتوافق مع الكود القديم:
> ```python
> from .input_styles import input_style, spinbox_style, search_input_style
> from .table_styles import table_style, splitter_style
> # ... إلخ
> ```

---

### تغيير 2 — تقسيم `ui/widgets/components/headers.py`

**المشكلة:** 6 components مختلفة في ملف واحد.

**الحل:**

```
ui/widgets/components/
├── headers/
│   ├── __init__.py         ← re-exports لكل الـ headers للتوافق
│   ├── section_header.py   ← SectionHeader فقط
│   ├── page_header.py      ← PageHeader فقط
│   ├── detail_header.py    ← DetailHeader فقط
│   ├── list_header.py      ← ListHeader + SearchBar (مترابطان)
│   └── status_bar.py       ← StatusBar فقط
```

> أو البديل الأبسط: تقسيم لملفين فقط:
> - `headers_list.py` ← ListHeader + SearchBar + StatusBar (للقوائم)
> - `headers_page.py` ← SectionHeader + PageHeader + DetailHeader (للصفحات)
> - `headers.py` يبقى كـ re-export للتوافق

---

### تغيير 3 — تقسيم `ui/widgets/components/label.py`

**المشكلة:** مزيج من أنواع مختلفة.

**الحل:**

```
ui/widgets/components/
├── label.py          ← InfoRow + ModeLabel فقط (labels بسيطة)
├── amount_label.py   ← AmountLabel + DebitCreditDisplay + BalanceDisplay + format_amount + amount_color + dr_cr_color
└── progress.py       ← ProgressBar + MultiProgressBar
```

---

### تغيير 4 — تقسيم `ui/widgets/components/stat_row.py`

**المشكلة:** 7 classes في ملف واحد.

**الحل:**

```
ui/widgets/components/
├── badge.py          ← BadgeLabel فقط (label بسيط)
├── stat_card.py      ← StatCard + StatItem + _StatCard + StatRow + make_stat_row + stat_card_pair + make_stat_card_simple
├── status_chip.py    ← StatusChip + StatusCard + make_status_chip
└── stat_row.py       ← يبقى كـ re-export للتوافق فقط
```

---

### تغيير 5 — تقسيم `ui/widgets/panels/form_parts.py`

**المشكلة:** كل أدوات الفورمات في ملف واحد.

**الحل:**

```
ui/widgets/panels/
├── form_labels.py    ← form_label, required_label, hint_label, section_title, separator_line
├── form_fields.py    ← spin_field, int_spin_field, labeled_widget, field_row, labeled_row, make_form_layout
├── form_group.py     ← FormGroup فقط
├── form_badges.py    ← ResultBadge + ModeBadge + InlinePreview + make_preview_label
├── form_buttons.py   ← CrudButtonsBar فقط
└── form_parts.py     ← re-export للتوافق + ModeLabel import
```

---

### تغيير 6 — حل تكرار CrudSection vs BaseSection

**المشكلة:** `BaseSection` و`CrudSection` نفس الـ pattern تقريباً.

**الحل:**

```python
# ui/widgets/panels/crud_section.py
# يصبح alias بحت للتوافق مع الكود القديم

from ui.widgets.base.section import BaseSection as CrudSection  # noqa: F401

__all__ = ["CrudSection"]
```

> `BaseSection` هي المصدر الوحيد، `CrudSection` alias فقط.

---

### تغيير 7 — توحيد Tooltip utilities

**المشكلة:** `refresh_tooltips` في `flexible.py` + `apply_table_tooltips` في `tooltip.py`.

**الحل:**

```python
# ui/widgets/utils/tooltip.py — يصبح المصدر الوحيد
# أضف refresh_tooltips هنا واحذفها من flexible.py

def refresh_tooltips(table: QTableWidget):
    """alias لـ apply_table_tooltips للتوافق مع الكود القديم."""
    apply_table_tooltips(table)
```

```python
# ui/widgets/tables/flexible.py
# احذف refresh_tooltips واستورد من tooltip.py
from ..utils.tooltip import refresh_tooltips  # noqa: F401
```

---

### تغيير 8 — تقسيم `ui/widgets/mixins/data_mixins.py`

**المشكلة:** 3 mixins مختلفة مدموجة.

**الحل:**

```
ui/widgets/mixins/
├── refresh_mixin.py   ← RefreshableMixin فقط
├── rebuild_mixin.py   ← RebuildMixin فقط
├── selection_mixin.py ← SelectionMixin فقط
└── data_mixins.py     ← re-export للتوافق فقط
```

---

### تغيير 9 — فصل Business Logic عن Widget في `combo/unit.py`

**المشكلة:** UnitCombo widget + كل الـ business logic في ملف واحد.

**الحل:**

```
ui/widgets/combo/
├── unit.py           ← UnitCombo widget + make_unit_combo فقط
└── unit_service.py   ← load_units, save_units, add_unit, remove_unit, reset_units_to_default, get_last_unit, set_last_unit, cache management
```

```python
# unit.py يستورد من unit_service.py
from .unit_service import load_units, save_units, get_last_unit, set_last_unit, invalidate_units_cache
```

---

### تغيير 10 — تصحيح الـ Imports الخاطئة

#### `ui/widgets/panels/filter.py`
```python
# قبل (خاطئ):
from ui.theme import _C
from ui.font  import get_font_size, fs
from ..utils.ui_utils   import blocked_signals
from ..styles           import input_style

# بعد (صح):
from ui.app_settings import _C, fs, get_font_size
from ..utils.signals import blocked_signals
from ..theme.styles  import input_style
```

#### `ui/widgets/panels/detail_section.py`
```python
# قبل (خاطئ):
from ui.theme import _C
from ui.font  import get_font_size, fs

# بعد (صح):
from ui.app_settings import _C, fs, get_font_size
```

#### `ui/widgets/panels/layout_widgets.py`
```python
# قبل (خاطئ):
from ui.theme import _C
from ui.font  import get_font_size, fs
from ..styles import h_divider, card_style

# بعد (صح):
from ui.app_settings import _C, fs, get_font_size
from ..theme.styles  import h_divider, card_style
```

#### `ui/widgets/panels/state.py`
```python
# قبل (خاطئ):
from ui.theme import _C
from ui.font  import get_font_size, fs

# بعد (صح):
from ui.app_settings import _C, fs, get_font_size
```

#### `ui/widgets/panels/data_table.py`
```python
# قبل (خاطئ):
from ..tables.tables import make_list_table, ROW_HEIGHT_LARGE
from ..tables.tables import auto_fit_columns
from ..styles        import (...)

# بعد (صح):
from ..tables.tables import make_list_table, ROW_HEIGHT_LARGE, auto_fit_columns
from ..theme.styles  import (...)
```

#### `ui/widgets/panels/crud_section.py`
```python
# قبل (خاطئ):
from ..styles import splitter_style

# بعد (صح):
from ..theme.styles import splitter_style
```

#### `ui/widgets/panels/form_parts.py`
```python
# قبل (خاطئ):
from ui.theme import _C
from ui.font  import get_font_size, fs

# بعد (صح):
from ui.app_settings import _C, fs, get_font_size
```

#### `ui/widgets/base/detail_panel.py`
```python
# قبل (خاطئ — builders.py اتدمج):
from ..tables.builders import (
    make_splitter_table_guarded,
    fit_splitter_table,
    ROW_HEIGHT_LARGE,
)

# بعد (صح):
from ..tables.tables import (
    make_splitter_table_guarded,
    fit_splitter_table,
    ROW_HEIGHT_LARGE,
)
```

#### `ui/widgets/base/list_panel.py`
```python
# قبل (خاطئ — builders.py اتدمج):
from ..tables.builders import (
    make_splitter_table_guarded,
    fit_splitter_table,
    ROW_HEIGHT_LARGE,
)
from ..tables.items import auto_fit_columns

# بعد (صح):
from ..tables.tables import (
    make_splitter_table_guarded,
    fit_splitter_table,
    ROW_HEIGHT_LARGE,
    auto_fit_columns,
)
```

---

## ترتيب التنفيذ (من الأسهل للأصعب)

```
المرحلة 1 — تصحيح الـ imports (لا تغيير في الهيكل):
  1. filter.py        ← blocked_signals + _C + input_style
  2. detail_section.py ← _C + font
  3. layout_widgets.py ← _C + font + styles
  4. state.py         ← _C + font
  5. data_table.py    ← styles path
  6. crud_section.py  ← styles path
  7. form_parts.py    ← _C + font
  8. detail_panel.py  ← builders → tables
  9. list_panel.py    ← builders + items → tables

المرحلة 2 — تحويل CrudSection لـ alias (سهل جداً):
  10. crud_section.py ← يصبح re-export من BaseSection

المرحلة 3 — توحيد Tooltip:
  11. نقل refresh_tooltips لـ tooltip.py + re-export من flexible.py

المرحلة 4 — فصل unit_service.py:
  12. إنشاء combo/unit_service.py
  13. تحديث combo/unit.py

المرحلة 5 — تقسيم data_mixins.py:
  14. إنشاء mixins/refresh_mixin.py
  15. إنشاء mixins/rebuild_mixin.py
  16. إنشاء mixins/selection_mixin.py
  17. data_mixins.py يصبح re-export

المرحلة 6 — تقسيم form_parts.py:
  18. form_labels.py
  19. form_fields.py
  20. form_group.py
  21. form_badges.py
  22. form_buttons.py
  23. form_parts.py يصبح re-export

المرحلة 7 — تقسيم label.py:
  24. amount_label.py
  25. progress.py
  26. label.py يبقى بـ InfoRow + ModeLabel

المرحلة 8 — تقسيم stat_row.py:
  27. badge.py
  28. stat_card.py
  29. status_chip.py
  30. stat_row.py يصبح re-export

المرحلة 9 — تقسيم headers.py:
  31. headers_list.py
  32. headers_page.py
  33. headers.py يصبح re-export

المرحلة 10 — تقسيم styles.py (الأصعب):
  34. input_styles.py
  35. table_styles.py
  36. card_styles.py
  37. label_styles.py
  38. layout_styles.py
  39. builders.py (dividers + wrap_in_scroll)
  40. styles.py يصبح re-export
```

---

## البنية النهائية

```
ui/widgets/
├── theme/
│   ├── styles.py          ← re-export فقط
│   ├── input_styles.py    ← input + spinbox + search
│   ├── table_styles.py    ← table + splitter + ROW_HEIGHTS
│   ├── card_styles.py     ← card + status_card + group_box
│   ├── label_styles.py    ← status_label + muted + section_title + icon_btn + link_btn
│   ├── layout_styles.py   ← tab + scroll + filter_bar + toolbar + tree + list
│   └── builders.py        ← h_divider + v_divider + wrap_in_scroll
│
├── components/
│   ├── button.py           ← make_btn فقط ✅
│   ├── label.py            ← InfoRow + ModeLabel
│   ├── amount_label.py     ← AmountLabel + DebitCreditDisplay + BalanceDisplay + helpers
│   ├── progress.py         ← ProgressBar + MultiProgressBar
│   ├── badge.py            ← BadgeLabel
│   ├── stat_card.py        ← StatCard + StatRow + helpers
│   ├── status_chip.py      ← StatusChip + StatusCard
│   ├── stat_row.py         ← re-export للتوافق
│   ├── notification.py     ← NotificationBar + BaseWarningBar ✅
│   ├── spinner.py          ← LoadingSpinner + LoadingOverlay + LoadingButton ✅
│   ├── action_toolbar.py   ← ActionToolbar ✅
│   ├── color_picker.py     ← ColorPickerWidget ✅ (في helpers/)
│   ├── headers/
│   │   ├── __init__.py     ← re-export
│   │   ├── list_header.py  ← ListHeader + SearchBar
│   │   ├── page_header.py  ← SectionHeader + PageHeader + DetailHeader
│   │   └── status_bar.py   ← StatusBar
│   └── headers.py          ← re-export للتوافق
│
├── panels/
│   ├── form_labels.py      ← form_label + required_label + hint_label + section_title + separator_line
│   ├── form_fields.py      ← spin_field + int_spin_field + labeled_widget + field_row + labeled_row + make_form_layout
│   ├── form_group.py       ← FormGroup
│   ├── form_badges.py      ← ResultBadge + ModeBadge + InlinePreview + make_preview_label
│   ├── form_buttons.py     ← CrudButtonsBar
│   ├── form_parts.py       ← re-export للتوافق
│   ├── state.py            ← EmptyState + helpers ✅
│   ├── detail_section.py   ← DetailSection + TwoColDetails ✅
│   ├── data_table.py       ← DataTableWidget ✅
│   ├── layout_widgets.py   ← CardGrid + CollapsibleCard ✅
│   └── crud_section.py     ← re-export من BaseSection
│
├── mixins/
│   ├── bus.py              ← BusConnectedMixin ✅
│   ├── refresh_mixin.py    ← RefreshableMixin
│   ├── rebuild_mixin.py    ← RebuildMixin
│   ├── selection_mixin.py  ← SelectionMixin
│   ├── data_mixins.py      ← re-export للتوافق
│   ├── form_mixins.py      ← EditModeMixin + FormValidationMixin ✅
│   ├── shared_ops.py       ← SharedOpsMixin ✅
│   └── service.py          ← ServiceMixin ✅
│
├── combo/
│   ├── unit.py             ← UnitCombo + make_unit_combo
│   ├── unit_service.py     ← load_units + save_units + add/remove/reset + cache
│   └── category.py         ← CategoryCombo + populate_category_combo ✅
│
├── utils/
│   ├── tooltip.py          ← apply_table_tooltips + apply_tree_tooltips + refresh_tooltips
│   ├── signals.py          ← blocked_signals ✅
│   ├── no_wheel.py         ← NoWheel* widgets ✅
│   ├── flow_layout.py      ← FlowLayout ✅
│   ├── splitter.py         ← SmartSplitter + SplitterScrollGuard + fit functions ✅
│   ├── date_range.py       ← DateRangeFilter ✅
│   └── searchable_combo.py ← SearchableCombo ✅
│
├── tables/
│   ├── tables.py           ← كل أدوات الجداول (بعد دمج builders + items) ✅
│   └── flexible.py         ← WrapDelegate + FlexibleTreeWidget (بدون refresh_tooltips)
│
├── base/
│   ├── section.py          ← BaseSection (المصدر الوحيد) ✅
│   ├── list_panel.py       ← BaseListPanel ✅
│   ├── detail_panel.py     ← BaseDetailPanel ✅
│   ├── crud_form.py        ← BaseCrudForm ✅
│   └── tab_section.py      ← TabSectionBase ✅
│
└── core/
    ├── conn.py             ← LiveConnMixin + SafeConnMixin + DualConnMixin ✅
    ├── events.py           ← emit_company_data_changed + helpers ✅
    ├── colors.py           ← card_colors + status_colors + waste_colors ✅
    ├── guard.py            ← requires_company decorator ✅
    ├── i18n.py             ← I18nManager + tr() ✅
    └── __init__.py         ← get_font_size re-export ✅
```

---

## قواعد Import الموحدة

بعد التغييرات، كل ملف يتبع هذه القاعدة:

```python
# ✅ صح — infrastructure من ui مباشرة:
from ui.app_settings import _C, fs, get_font_size

# ✅ صح — من نفس الـ package:
from ..theme.styles import scroll_style, h_divider

# ✅ صح — من core:
from ..core.colors import status_colors
from ..core.i18n   import tr

# ✅ صح — utils:
from ..utils.signals import blocked_signals

# ❌ خاطئ — لا تستورد مباشرة من ui.theme أو ui.font:
from ui.theme import _C        # ← استخدم ui.app_settings
from ui.font  import get_font_size  # ← استخدم ui.app_settings
```

---

## ملاحظات مهمة

1. **كل تغيير هيكلي يستلزم** إبقاء الملف القديم كـ re-export لتجنب كسر الكود الموجود.
2. **الأولوية للمرحلة 1** (تصحيح الـ imports) لأنها لا تغير الهيكل وتصلح مشاكل حقيقية.
3. **`filter.py`** فيه import خاطئ (`ui_utils`) ممكن يسبب `ImportError` — يجب تصحيحه فوراً.
4. **`crud_section.py`** يجب أن يصبح alias من BaseSection — الكود مكرر بالكامل تقريباً.