# خطة Refactoring V3 — مُحدَّثة
> تنظيم معماري شامل — مبدأ Single Responsibility لكل ملف، بدون تكرار، imports صحيحة

---

## تغيير جوهري: ui/app_settings.py اتمسح

`ui/app_settings.py` اتمسح ومحتواه اتنقل للملفات دي:

| المُصدَّر | الملف الجديد |
|----------|-------------|
| `_C` | `ui/theme.py` |
| `get_font_size`, `fs` | `ui/font.py` |
| `SIDEBAR_EXPANDED_WIDTH`, `SIDEBAR_COLLAPSED_WIDTH`, `CONTENT_MIN_WIDTH`, `WINDOW_DEFAULT_W` | `ui/constants.py` |

### قاعدة الـ Import الموحدة (بعد التعديل)

```python
# ✅ صح — الـ imports الصحيحة الجديدة
from ui.theme    import _C
from ui.font     import get_font_size, fs
from ui.constants import SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH, CONTENT_MIN_WIDTH, WINDOW_DEFAULT_W

# ✅ صح — من نفس الـ package
from ..theme.styles import scroll_style, h_divider, splitter_style

# ✅ صح — من core
from ..core.colors import status_colors
from ..core.i18n   import tr
from ..utils.signals import blocked_signals

# ❌ خاطئ — ملف اتمسح
from ui.app_settings import _C, fs, get_font_size

# ❌ خاطئ — relative قديمة
from ...font  import fs, get_font_size
from ...theme import _C

# ❌ خاطئ — مسار خاطئ للـ styles
from ..styles import splitter_style   # الصح: from ..theme.styles import

# ❌ خاطئ — ملف مش موجود
from ..utils.ui_utils import blocked_signals   # الصح: from ..utils.signals import

# ❌ خاطئ — builders.py اتدمج في tables.py
from ..tables.builders import make_splitter_table_guarded
from ..tables.items    import auto_fit_columns
# الصح:
from ..tables.tables import make_splitter_table_guarded, auto_fit_columns
```

---

## المشاكل المكتشفة

### 1. ملفات بأكتر من وظيفة واحدة

| الملف | الوظائف الموجودة | المشكلة |
|-------|-----------------|---------|
| `ui/widgets/theme/styles.py` | stylesheet generators + dividers + scroll wrapper + card styles + tab styles + label styles | ملف ضخم جداً |
| `ui/widgets/components/stat_row.py` | BadgeLabel + StatCard + StatusChip + StatItem + _StatCard + StatRow + StatusCard + دوال | 7 classes في ملف واحد |
| `ui/widgets/components/headers.py` | SectionHeader + PageHeader + DetailHeader + ListHeader + SearchBar + StatusBar | 6 components مختلفة |
| `ui/widgets/components/label.py` | InfoRow + ModeLabel + AmountLabel + DebitCreditDisplay + BalanceDisplay + ProgressBar + MultiProgressBar | مزيج أنواع مختلفة |
| `ui/widgets/panels/form_parts.py` | label builders + row builders + spin fields + FormGroup + ResultBadge + ModeBadge + InlinePreview + CrudButtonsBar | كل أدوات الفورمات |
| `ui/widgets/tables/tables.py` | أدوات الخلايا + builders + fit functions | دمج صح لكن ممكن تقسيم |
| `ui/widgets/mixins/data_mixins.py` | RefreshableMixin + RebuildMixin + SelectionMixin | 3 mixins مختلفة |
| `ui/widgets/combo/unit.py` | UnitCombo widget + load/save/add/remove units + cache | widget + business logic + data access |

---

### 2. وظائف متوزعة على أكتر من ملف

| الوظيفة | الملفات | المشكلة |
|---------|---------|---------|
| Tooltip utilities | `utils/tooltip.py` + `tables/flexible.py` (refresh_tooltips) | نفس الوظيفة في مكانين |
| ModeLabel | معرّفة في `components/label.py` + re-export في `panels/form_parts.py` | re-export غير ضروري |
| CrudSection | `base/section.py` (BaseSection) + `panels/crud_section.py` (CrudSection) | كود مكرر شبه مطابق |

---

### 3. مشاكل الـ Imports (الأهم والأعلى أولوية)

| الملف | المشكلة | التصحيح |
|-------|---------|---------|
| `button.py` | `from ui.app_settings import _C, fs` — ملف اتمسح | `from ui.theme import _C` + `from ui.font import fs, get_font_size` |
| `styles.py` | `from ui.app_settings import _C, fs` — ملف اتمسح | `from ui.theme import _C` + `from ui.font import fs, get_font_size` |
| `_nav_button.py` | `from ui.app_settings import get_font_size, _C, SIDEBAR_*` | `from ui.theme import _C` + `from ui.font import get_font_size` + `from ui.constants import SIDEBAR_*` |
| `_section_label.py` | `from ui.app_settings import _C, fs, get_font_size` | split across `ui.theme`, `ui.font` |
| `_toggle_button.py` | `from ui.app_settings import _C` | `from ui.theme import _C` |
| `notification.py` | `from ui.app_settings import _C, fs, get_font_size` | split |
| `spinner.py` | `from ui.app_settings import _C, fs` + `from ui.app_settings import get_font_size` | split |
| `stat_row.py` | `from ui.app_settings import _C, fs` + `from ui.app_settings import get_font_size` | split |
| `headers.py` | `from ui.app_settings import _C, fs` + `from ui.app_settings import get_font_size` | split |
| `label.py` | `from ui.app_settings import _C, fs` + `from ui.app_settings import get_font_size` | split |
| `action_toolbar.py` | يستورد من `..theme.styles` — OK |  |
| `component_row/ui.py` | `from ui.app_settings import _C, fs, get_font_size` | split |
| `date_range.py` | `from ui.app_settings import _C, fs, get_font_size` | split |
| `forms/inputs.py` | `from ui.app_settings import _C, fs` | split |
| `panels/form_parts.py` | `from ui.theme import _C` + `from ui.font import get_font_size, fs` | هذا صح فعلاً — لا تغيير |
| `panels/state.py` | `from ...font import fs, get_font_size` + `from ...theme import _C` | `from ui.font import` + `from ui.theme import` |
| `panels/detail_section.py` | `from ...font import fs, get_font_size` + `from ...theme import _C` | `from ui.font import` + `from ui.theme import` |
| `panels/layout_widgets.py` | `from ...font import fs, get_font_size` + `from ...theme import _C` + `from ..styles import` | split + `from ..theme.styles import` |
| `panels/data_table.py` | `from ..tables.tables import` + `from ..styles import` | `from ..theme.styles import` |
| `panels/crud_section.py` | `from ..styles import splitter_style` | `from ..theme.styles import splitter_style` |
| `panels/filter.py` | `from ..utils.ui_utils import blocked_signals` | `from ..utils.signals import blocked_signals` |
| `base/detail_panel.py` | `from ..tables.builders import` | `from ..tables.tables import` |
| `base/list_panel.py` | `from ..tables.builders import` + `from ..tables.items import` | `from ..tables.tables import` |
| `managers/category.py` | `from ui.widgets.core.events import emit_company_data_changed` | OK — موجود |
| `combo/category.py` | `from ..core.conn import LiveConnMixin` | OK |
| `combo/unit.py` | `from ..utils.signals import blocked_signals` | OK |

---

## التغييرات المطلوبة

---

### تغيير 1 — تصحيح كل الـ imports المكسورة (أعلى أولوية)

#### Pattern التصحيح الموحد:

```python
# بدل:
from ui.app_settings import _C, fs, get_font_size

# يصبح:
from ui.theme import _C
from ui.font  import get_font_size, fs
```

```python
# بدل:
from ui.app_settings import _C, SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH

# يصبح:
from ui.theme    import _C
from ui.constants import SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH
```

```python
# بدل:
from ...font  import fs, get_font_size
from ...theme import _C

# يصبح:
from ui.font  import fs, get_font_size
from ui.theme import _C
```

```python
# بدل:
from ..styles import splitter_style

# يصبح:
from ..theme.styles import splitter_style
```

```python
# بدل:
from ..utils.ui_utils import blocked_signals

# يصبح:
from ..utils.signals import blocked_signals
```

```python
# بدل (builders.py و items.py اتدمجوا في tables.py):
from ..tables.builders import make_splitter_table_guarded, fit_splitter_table, ROW_HEIGHT_LARGE
from ..tables.items    import auto_fit_columns

# يصبح:
from ..tables.tables import make_splitter_table_guarded, fit_splitter_table, ROW_HEIGHT_LARGE, auto_fit_columns
```

---

### تغيير 2 — تقسيم `ui/widgets/theme/styles.py`

يبقى re-export فقط، والمحتوى يتنقل لملفات منفصلة:

```
ui/widgets/theme/
├── styles.py          ← re-export للتوافق فقط
├── input_styles.py    ← input_style, spinbox_style, search_input_style
├── table_styles.py    ← table_style, splitter_style, ROW_HEIGHT_*
├── card_styles.py     ← card_style, status_card_style, group_box_style
├── label_styles.py    ← status_label_style, muted_label_style, section_title_style, icon_btn_style, link_btn_style
├── layout_styles.py   ← tab_style, scroll_style, filter_bar_style, toolbar_style, tree_style, list_style
└── builders.py        ← h_divider, v_divider, wrap_in_scroll
```

---

### تغيير 3 — تقسيم `ui/widgets/components/headers.py`

```
ui/widgets/components/
├── headers.py          ← re-export للتوافق فقط
├── headers_list.py     ← ListHeader + SearchBar + StatusBar
└── headers_page.py     ← SectionHeader + PageHeader + DetailHeader
```

---

### تغيير 4 — تقسيم `ui/widgets/components/label.py`

```
ui/widgets/components/
├── label.py          ← InfoRow + ModeLabel فقط
├── amount_label.py   ← AmountLabel + DebitCreditDisplay + BalanceDisplay + format_amount + amount_color + dr_cr_color
└── progress.py       ← ProgressBar + MultiProgressBar
```

---

### تغيير 5 — تقسيم `ui/widgets/components/stat_row.py`

```
ui/widgets/components/
├── badge.py          ← BadgeLabel
├── stat_card.py      ← StatCard + StatItem + _StatCard + StatRow + make_stat_row + stat_card_pair + make_stat_card_simple
├── status_chip.py    ← StatusChip + StatusCard + make_status_chip
└── stat_row.py       ← re-export للتوافق فقط
```

---

### تغيير 6 — تقسيم `ui/widgets/panels/form_parts.py`

```
ui/widgets/panels/
├── form_labels.py    ← form_label, required_label, hint_label, section_title, separator_line
├── form_fields.py    ← spin_field, int_spin_field, labeled_widget, field_row, labeled_row, make_form_layout
├── form_group.py     ← FormGroup
├── form_badges.py    ← ResultBadge, ModeBadge, InlinePreview, make_preview_label
├── form_buttons.py   ← CrudButtonsBar
└── form_parts.py     ← re-export للتوافق فقط
```

---

### تغيير 7 — تحويل `CrudSection` لـ alias

```python
# ui/widgets/panels/crud_section.py — يصبح:
from ui.widgets.base.section import BaseSection as CrudSection  # noqa: F401
__all__ = ["CrudSection"]
```

---

### تغيير 8 — توحيد Tooltip utilities

```python
# ui/widgets/utils/tooltip.py — يضاف:
def refresh_tooltips(table: QTableWidget):
    """alias لـ apply_table_tooltips للتوافق."""
    apply_table_tooltips(table)

# ui/widgets/tables/flexible.py — يُحذف refresh_tooltips ويستورد:
from ..utils.tooltip import refresh_tooltips  # noqa: F401
```

---

### تغيير 9 — تقسيم `ui/widgets/mixins/data_mixins.py`

```
ui/widgets/mixins/
├── refresh_mixin.py   ← RefreshableMixin
├── rebuild_mixin.py   ← RebuildMixin
├── selection_mixin.py ← SelectionMixin
└── data_mixins.py     ← re-export للتوافق فقط
```

---

### تغيير 10 — فصل Business Logic في `combo/unit.py`

```
ui/widgets/combo/
├── unit.py           ← UnitCombo + make_unit_combo فقط
└── unit_service.py   ← load_units, save_units, add_unit, remove_unit, reset_units_to_default, get_last_unit, set_last_unit, cache management
```

---

## ترتيب التنفيذ

```
المرحلة 1 — تصحيح imports المكسورة (الأعلى أولوية — لازم تتعمل الأول):
  الموجة أ — ملفات بيستوردوا من ui.app_settings المحذوف:
    1.  ui/widgets/components/button.py
    2.  ui/widgets/theme/styles.py
    3.  ui/main_window_helper/_nav_button.py
    4.  ui/main_window_helper/_section_label.py
    5.  ui/main_window_helper/_toggle_button.py
    6.  ui/widgets/components/notification.py
    7.  ui/widgets/components/spinner.py
    8.  ui/widgets/components/stat_row.py
    9.  ui/widgets/components/headers.py
    10. ui/widgets/components/label.py
    11. ui/widgets/components/component_row/ui.py
    12. ui/widgets/utils/date_range.py
    13. ui/widgets/forms/inputs.py

  الموجة ب — ملفات بـ relative imports قديمة أو مسارات خاطئة:
    14. ui/widgets/panels/state.py         (from ...font/theme → from ui.font/theme)
    15. ui/widgets/panels/detail_section.py
    16. ui/widgets/panels/layout_widgets.py  (+ from ..styles → from ..theme.styles)
    17. ui/widgets/panels/data_table.py      (from ..styles → from ..theme.styles)
    18. ui/widgets/panels/crud_section.py    (from ..styles → from ..theme.styles)
    19. ui/widgets/panels/filter.py          (from ..utils.ui_utils → from ..utils.signals)
    20. ui/widgets/panels/form_parts.py      (from ui.theme / ui.font — OK فعلاً، لا تغيير)
    21. ui/widgets/base/detail_panel.py      (from ..tables.builders → from ..tables.tables)
    22. ui/widgets/base/list_panel.py        (from ..tables.builders + items → from ..tables.tables)

المرحلة 2 — تحويل CrudSection لـ alias:
    23. ui/widgets/panels/crud_section.py

المرحلة 3 — توحيد Tooltip:
    24. ui/widgets/utils/tooltip.py  (أضف refresh_tooltips)
    25. ui/widgets/tables/flexible.py  (احذف refresh_tooltips، استورد من tooltip)

المرحلة 4 — فصل unit_service.py:
    26. ui/widgets/combo/unit_service.py  (جديد)
    27. ui/widgets/combo/unit.py  (يستورد من unit_service)

المرحلة 5 — تقسيم data_mixins.py:
    28. ui/widgets/mixins/refresh_mixin.py  (جديد)
    29. ui/widgets/mixins/rebuild_mixin.py  (جديد)
    30. ui/widgets/mixins/selection_mixin.py  (جديد)
    31. ui/widgets/mixins/data_mixins.py  (re-export)

المرحلة 6 — تقسيم form_parts.py:
    32. ui/widgets/panels/form_labels.py  (جديد)
    33. ui/widgets/panels/form_fields.py  (جديد)
    34. ui/widgets/panels/form_group.py   (جديد)
    35. ui/widgets/panels/form_badges.py  (جديد)
    36. ui/widgets/panels/form_buttons.py (جديد)
    37. ui/widgets/panels/form_parts.py   (re-export)

المرحلة 7 — تقسيم label.py:
    38. ui/widgets/components/amount_label.py  (جديد)
    39. ui/widgets/components/progress.py      (جديد)
    40. ui/widgets/components/label.py         (InfoRow + ModeLabel فقط)

المرحلة 8 — تقسيم stat_row.py:
    41. ui/widgets/components/badge.py       (جديد)
    42. ui/widgets/components/stat_card.py   (جديد)
    43. ui/widgets/components/status_chip.py (جديد)
    44. ui/widgets/components/stat_row.py    (re-export)

المرحلة 9 — تقسيم headers.py:
    45. ui/widgets/components/headers_list.py  (جديد)
    46. ui/widgets/components/headers_page.py  (جديد)
    47. ui/widgets/components/headers.py       (re-export)

المرحلة 10 — تقسيم styles.py (الأصعب):
    48. ui/widgets/theme/input_styles.py   (جديد)
    49. ui/widgets/theme/table_styles.py   (جديد)
    50. ui/widgets/theme/card_styles.py    (جديد)
    51. ui/widgets/theme/label_styles.py   (جديد)
    52. ui/widgets/theme/layout_styles.py  (جديد)
    53. ui/widgets/theme/builders.py       (جديد — h_divider, v_divider, wrap_in_scroll)
    54. ui/widgets/theme/styles.py         (re-export)
```

---

## البنية النهائية للملفات

```
ui/widgets/
├── theme/
│   ├── styles.py          ← re-export فقط
│   ├── input_styles.py
│   ├── table_styles.py
│   ├── card_styles.py
│   ├── label_styles.py
│   ├── layout_styles.py
│   └── builders.py        ← h_divider, v_divider, wrap_in_scroll
│
├── components/
│   ├── button.py           ✅ (بعد إصلاح import)
│   ├── label.py            ← InfoRow + ModeLabel
│   ├── amount_label.py     (جديد)
│   ├── progress.py         (جديد)
│   ├── badge.py            (جديد)
│   ├── stat_card.py        (جديد)
│   ├── status_chip.py      (جديد)
│   ├── stat_row.py         ← re-export
│   ├── notification.py     ✅ (بعد إصلاح import)
│   ├── spinner.py          ✅ (بعد إصلاح import)
│   ├── action_toolbar.py   ✅
│   ├── headers_list.py     (جديد)
│   ├── headers_page.py     (جديد)
│   └── headers.py          ← re-export
│
├── panels/
│   ├── form_labels.py      (جديد)
│   ├── form_fields.py      (جديد)
│   ├── form_group.py       (جديد)
│   ├── form_badges.py      (جديد)
│   ├── form_buttons.py     (جديد)
│   ├── form_parts.py       ← re-export
│   ├── state.py            ✅ (بعد إصلاح import)
│   ├── detail_section.py   ✅ (بعد إصلاح import)
│   ├── data_table.py       ✅ (بعد إصلاح import)
│   ├── layout_widgets.py   ✅ (بعد إصلاح import)
│   └── crud_section.py     ← alias من BaseSection
│
├── mixins/
│   ├── bus.py              ✅
│   ├── refresh_mixin.py    (جديد)
│   ├── rebuild_mixin.py    (جديد)
│   ├── selection_mixin.py  (جديد)
│   ├── data_mixins.py      ← re-export
│   ├── form_mixins.py      ✅
│   ├── shared_ops.py       ✅
│   └── service.py          ✅
│
├── combo/
│   ├── unit.py             ← widget فقط
│   ├── unit_service.py     (جديد — business logic)
│   └── category.py         ✅
│
├── utils/
│   ├── tooltip.py          ✅ (+ refresh_tooltips)
│   ├── signals.py          ✅
│   ├── no_wheel.py         ✅
│   ├── flow_layout.py      ✅
│   ├── splitter.py         ✅
│   ├── date_range.py       ✅ (بعد إصلاح import)
│   └── searchable_combo.py ✅
│
├── tables/
│   ├── tables.py           ✅
│   └── flexible.py         ✅ (بعد حذف refresh_tooltips)
│
├── base/
│   ├── section.py          ✅ (المصدر الوحيد)
│   ├── list_panel.py       ✅ (بعد إصلاح import)
│   ├── detail_panel.py     ✅ (بعد إصلاح import)
│   ├── crud_form.py        ✅
│   └── tab_section.py      ✅
│
└── core/
    ├── conn.py             ✅
    ├── events.py           ✅
    ├── colors.py           ✅
    ├── guard.py            ✅
    ├── i18n.py             ✅
    └── __init__.py         ✅
```

---

## ملاحظات مهمة

1. **المرحلة 1 لازم تتنفذ الأول** — كل الملفات اللي بتستورد من `ui.app_settings` مكسورة دلوقتي.
2. **كل تغيير هيكلي** يستلزم إبقاء الملف القديم كـ re-export للتوافق مع الكود الموجود.
3. **`filter.py`** فيه `from ..utils.ui_utils import blocked_signals` — ده `ImportError` مباشر، أعلى أولوية.
4. **`crud_section.py`** كوده مكرر بالكامل تقريباً مع `BaseSection` — يصبح alias فقط.
5. **`form_parts.py`** فيه `from ui.theme import _C` و`from ui.font import` — ده صح فعلاً، لا تغيير مطلوب.