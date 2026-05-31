# خطة إعادة الهيكلة الشاملة — Refactor Plan V4

**الهدف:** ضمان مبدأ Single Source of Truth — كل وظيفة في مكان واحد فقط، بدون تكرار، وكل import يشير للمصدر الصح.

---

## البنية النهائية المستهدفة

```
ui/
├── events.py                          ← bus + كل الـ signals (مصدر واحد)
├── theme.py                           ← _C + apply_theme (مصدر واحد)
├── theme_manager.py                   ← ThemeManager + تعريف الألوان
├── font.py                            ← get_font_size, set_font_size, fs
├── constants.py                       ← ثوابت التطبيق
├── app_state.py                       ← cache الإعدادات
├── i18n/
│   ├── ar.py                          ← القاموس العربي
│   └── en.py                          ← القاموس الإنجليزي
└── widgets/
    ├── core/
    │   ├── __init__.py                ← re-export من ui.font
    │   ├── colors.py                  ← card_colors, status_colors, waste_*
    │   ├── conn.py                    ← LiveConnMixin, SafeConnMixin, DualConnMixin
    │   ├── events.py                  ← helpers: emit_company_data_changed
    │   ├── guard.py                   ← requires_company decorator
    │   └── i18n.py                    ← I18nManager + tr()
    ├── theme/
    │   ├── builders.py                ← h_divider, v_divider, wrap_in_scroll
    │   ├── card_styles.py             ← card_style, status_card_style, group_box_style
    │   ├── input_styles.py            ← input_style, spinbox_style, search_input_style
    │   ├── label_styles.py            ← status_label_style, muted_label_style, ...
    │   ├── layout_styles.py           ← tab_style, scroll_style, tree_style, ...
    │   └── table_styles.py            ← table_style, splitter_style, ROW_HEIGHT_*
    ├── components/
    │   ├── action_toolbar.py          ← ActionToolbar
    │   ├── amount_label.py            ← AmountLabel, DebitCreditDisplay, BalanceDisplay [المصدر]
    │   ├── badge.py                   ← BadgeLabel [المصدر]
    │   ├── button.py                  ← make_btn, refresh_visible_buttons
    │   ├── headers_list.py            ← SearchBar, StatusBar, ListHeader
    │   ├── headers_page.py            ← SectionHeader, PageHeader, DetailHeader
    │   ├── label.py                   ← InfoRow, ModeLabel + re-exports [موحَّد]
    │   ├── notification.py            ← NotificationBar, BaseWarningBar
    │   ├── progress.py                ← ProgressBar, MultiProgressBar [المصدر]
    │   ├── spinner.py                 ← LoadingSpinner, LoadingOverlay, LoadingButton
    │   ├── stat_card.py               ← StatItem, StatCard, StatRow, ...
    │   └── status_chip.py             ← StatusChip, StatusCard
    ├── dialogs/
    │   ├── confirm.py                 ← ConfirmDialog, confirm_delete, ...
    │   ├── dialogs_base.py            ← DialogShell, BaseDialog [المصدر الوحيد]
    │   ├── message.py                 ← MessageDialog, msg_*
    │   └── settings_dialog.py
    ├── mixins/
    │   ├── bus.py                     ← BusConnectedMixin
    │   ├── edit.py                    ← re-export من form_mixins [للتوافق]
    │   ├── form_mixins.py             ← EditModeMixin, FormValidationMixin [المصدر]
    │   ├── rebuild_mixin.py           ← RebuildMixin
    │   ├── refresh_mixin.py           ← RefreshableMixin
    │   ├── selection_mixin.py         ← SelectionMixin
    │   ├── service.py                 ← ServiceMixin
    │   ├── shared_ops.py              ← SharedOpsMixin
    │   └── validate.py                ← re-export من form_mixins [للتوافق]
    ├── tables/
    │   ├── flexible.py                ← WrapDelegate, FlexItem, make_flexible_table
    │   └── tables.py                  ← make_table, make_splitter_table, ROW_HEIGHT_* [المصدر]
    ├── utils/
    │   ├── date_range.py
    │   ├── flow_layout.py
    │   ├── no_wheel.py
    │   ├── searchable_combo.py
    │   ├── signals.py                 ← blocked_signals
    │   ├── splitter.py                ← SmartSplitter, SplitterScrollGuard
    │   └── tooltip.py
    ├── base/
    │   ├── crud_form.py
    │   ├── detail_panel.py
    │   ├── list_panel.py
    │   ├── section.py
    │   └── tab_section.py
    ├── panels/
    │   ├── data_table.py
    │   ├── detail_section.py
    │   ├── filter.py
    │   ├── form_badges.py
    │   ├── form_buttons.py
    │   ├── form_fields.py
    │   ├── form_group.py
    │   ├── form_labels.py
    │   ├── layout_widgets.py
    │   └── state.py
    ├── combo/
    │   ├── category.py
    │   ├── unit.py
    │   └── unit_service.py
    ├── forms/
    │   └── inputs.py
    ├── managers/
    │   └── category.py
    └── shared/
        └── list_panel_with_shared.py
```

---

## المراحل

---

## المرحلة 1 — إصلاح الأعطال الحرجة
**الهدف:** التطبيق يشتغل. لا SyntaxError، لا ImportError.
**العدد:** 4 ملفات
**الوقت المقدر:** سريع

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 1.1 | `ui/events.py` | `data_changed` signal ناقص | أضف `data_changed = pyqtSignal()` |
| 1.2 | `ui/widgets/dialogs/confirm.py` | `from .shell import` → مكسور | غيّر لـ `from .dialogs_base import` |
| 1.3 | `ui/widgets/dialogs/message.py` | `from .shell import` → مكسور | غيّر لـ `from .dialogs_base import` |
| 1.4 | `ui/widgets/components/action_toolbar.py` | سطرَي import مدمجان | افصلهم على سطرين |

---

## المرحلة 2 — إصلاح Imports الـ Refactor
**الهدف:** كل import يشير للمكان الصح بعد تقسيم الملفات.
**العدد:** 5 ملفات
**الوقت المقدر:** متوسط

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 2.1 | `ui/widgets/utils/splitter.py` | `from ..tables.items import calc_width` | `from ..tables.tables import calc_width` |
| 2.2 | `ui/widgets/base/detail_panel.py` | `from ..theme.styles import scroll_style` | `from ..theme.layout_styles import scroll_style` |
| 2.3 | `ui/widgets/panels/detail_section.py` | `from ..components.headers import SectionHeader` | `from ..components.headers_page import SectionHeader` |
| 2.4 | `ui/widgets/base/crud_form.py` | `from ui.widgets.mixins.edit import EditModeMixin` | `from ui.widgets.mixins.form_mixins import EditModeMixin` |
| 2.5 | `ui/widgets/components/headers_page.py` | `from .stat_row import BadgeLabel` | `from .badge import BadgeLabel` |

---

## المرحلة 3 — إصلاح Imports المتوسطة
**الهدف:** توحيد كل الـ imports الغامضة.
**العدد:** 2 ملفات

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 3.1 | `ui/widgets/core/__init__.py` | `from ui.app_settings import get_font_size` | `from ui.font import get_font_size` |
| 3.2 | `ui/widgets/tables/tables.py` | `from ..styles import ROW_HEIGHT_*` | `from ..theme.table_styles import ROW_HEIGHT_*` |

---

## المرحلة 4 — توحيد ملفات التكرار الصريح
**الهدف:** كل كلاس/دالة في مكان واحد فقط.
**العدد:** 3 ملفات تُعدَّل + 2 ملفات compatibility shims تُنشأ

### 4.1 — توحيد Label Widgets

**المشكلة:** `ProgressBar` و`MultiProgressBar` مكررتان في `label.py` و`progress.py`. كذلك `AmountLabel` وأخواتها في `label.py` و`amount_label.py`.

**الحل:**
- `progress.py` ← **المصدر الوحيد** لـ `ProgressBar, MultiProgressBar`
- `amount_label.py` ← **المصدر الوحيد** لـ `AmountLabel, DebitCreditDisplay, BalanceDisplay, format_amount, amount_color, dr_cr_color`
- `label.py` ← يحذف التعريفات المكررة ويستبدلها بـ re-exports

**label.py بعد التعديل:**
```python
# label.py — يحتفظ فقط بـ: InfoRow, ModeLabel
# ويعمل re-export للباقي للتوافق مع الكود القديم

from .progress     import ProgressBar, MultiProgressBar       # noqa: F401
from .amount_label import (                                   # noqa: F401
    AmountLabel, DebitCreditDisplay, BalanceDisplay,
    format_amount, amount_color, dr_cr_color,
)
```

### 4.2 — إنشاء ملفات التوافق للـ Mixins المحذوفة

**المشكلة:** `edit.py` و`validate.py` محذوفان لكن يُستورد منهما.

**الحل:** إنشاء ملفين compatibility shims:

**`ui/widgets/mixins/edit.py`:**
```python
# Compatibility shim — المصدر الحقيقي: form_mixins.py
from .form_mixins import EditModeMixin  # noqa: F401
```

**`ui/widgets/mixins/validate.py`:**
```python
# Compatibility shim — المصدر الحقيقي: form_mixins.py
from .form_mixins import FormValidationMixin  # noqa: F401
```

### 4.3 — إنشاء ملف التوافق لـ stat_row

**المشكلة:** `stat_row.py` محذوف لكن `headers_page.py` يستورد منه.

**الحل:** إما تعديل `headers_page.py` لـ `from .badge import BadgeLabel` (تم في المرحلة 2.5)، أو إنشاء shim.

---

## المرحلة 5 — إصلاح مشكلة STYLE_ORPHAN الـ Stale
**الهدف:** ألوان الـ orphan rows تتحدث مع تغيير الثيم.

**الملف:** `ui/widgets/components/component_row/ui.py`

**الحل:** استبدال الثابت بدالة:
```python
# قبل
STYLE_ORPHAN = _orphan_style()  # stale

# بعد — يُقرأ عند كل استخدام
def get_orphan_style() -> str:
    return _orphan_style()
```

وفي `widget.py`:
```python
self.setStyleSheet(get_orphan_style())
```

---

## المرحلة 6 — إصلاح BusConnectedMixin (أول إشعار مفقود)
**الملف:** `ui/widgets/mixins/bus.py`

**الإصلاح:**
```python
def _on_company_data_changed(self, company_id: int):
    if self._cached_company_id is None:
        self._cached_company_id = self._get_active_company_id()

    # لو الـ cache لا يزال None → اضبطه وتابع (لا تُتجاهل)
    if self._cached_company_id is None:
        self._cached_company_id = company_id
    elif company_id != self._cached_company_id:
        logger.debug(...)
        return

    self._refresh_guard = True
    self._on_data_changed()
    QTimer.singleShot(0, self._clear_refresh_guard)
```

---

## جدول تتبع التنفيذ

| المرحلة | الملف | الحالة |
|---------|-------|--------|
| 1.1 | `ui/events.py` | ⬜ |
| 1.2 | `ui/widgets/dialogs/confirm.py` | ⬜ |
| 1.3 | `ui/widgets/dialogs/message.py` | ⬜ |
| 1.4 | `ui/widgets/components/action_toolbar.py` | ⬜ |
| 2.1 | `ui/widgets/utils/splitter.py` | ⬜ |
| 2.2 | `ui/widgets/base/detail_panel.py` | ⬜ |
| 2.3 | `ui/widgets/panels/detail_section.py` | ⬜ |
| 2.4 | `ui/widgets/base/crud_form.py` | ⬜ |
| 2.5 | `ui/widgets/components/headers_page.py` | ⬜ |
| 3.1 | `ui/widgets/core/__init__.py` | ⬜ |
| 3.2 | `ui/widgets/tables/tables.py` | ⬜ |
| 4.1 | `ui/widgets/components/label.py` | ⬜ |
| 4.2 | `ui/widgets/mixins/edit.py` (shim جديد) | ⬜ |
| 4.2 | `ui/widgets/mixins/validate.py` (shim جديد) | ⬜ |
| 5.1 | `ui/widgets/components/component_row/ui.py` | ⬜ |
| 6.1 | `ui/widgets/mixins/bus.py` | ⬜ |

**الإجمالي:** 16 ملف (14 تعديل + 2 إنشاء جديد)

---

## قواعد لا تُكسر بعد هذا الـ Refactor

1. **`ui/events.py`** — المصدر الوحيد للـ bus وكل الـ signals
2. **`ui/widgets/dialogs/dialogs_base.py`** — المصدر الوحيد لـ `DialogShell` و`BaseDialog`
3. **`ui/widgets/mixins/form_mixins.py`** — المصدر الوحيد لـ `EditModeMixin` و`FormValidationMixin`
4. **`ui/widgets/components/progress.py`** — المصدر الوحيد لـ `ProgressBar`
5. **`ui/widgets/components/amount_label.py`** — المصدر الوحيد لـ `AmountLabel` وأخواتها
6. **`ui/widgets/tables/tables.py`** — المصدر الوحيد لـ `ROW_HEIGHT_*` وبناة الجداول
7. **`ui/widgets/theme/layout_styles.py`** — المصدر الوحيد لـ `scroll_style`
8. **`ui/widgets/components/badge.py`** — المصدر الوحيد لـ `BadgeLabel`
9. **`ui/widgets/components/headers_page.py`** — المصدر الوحيد لـ `SectionHeader`