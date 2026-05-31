# خطة Refactoring الكاملة — `ui/` + `ui/widgets/`

> **الهدف:** كل ملف مسؤول عن حاجة واحدة بالظبط، مفيش تكرار، مفيش كود قديم، مفيش folder بملف واحد بس.

---

## القواعد العامة للخطة

1. **مفيش ملف deprecated** — يُحذف أو يُدمج فوراً
2. **مفيش تكرار** — ثابت أو دالة في مكان واحد فقط
3. **مفيش folder بملف واحد** — الملف ينتقل لأقرب مكان منطقي
4. **مفيش re-export بلا قيمة** — `__init__.py` إما فيه منطق حقيقي أو يتحذف
5. **كل ملف = مسؤولية واحدة واضحة**

---

## الجزء الأول — `ui/` (الملفات الجذرية)

### البنية الحالية vs المقترحة

```
ui/ (الحالي)                    ui/ (المقترح)
────────────────────────────    ────────────────────────────
app_settings.py  ← فوضى        constants.py        ← جديد
app_state.py     ← تكرار       font.py             ← جديد
events.py        ← deprecated  theme.py            ← جديد
main_window.py                  events.py           ← معدّل
settings_dialog.py              app_state.py        ← معدّل
themes/                         main_window.py      ← معدّل
  theme_manager.py              settings_dialog.py  ← معدّل
                                themes/
                                  theme_manager.py  ← بدون تغيير
```

---

### `ui/constants.py` — **جديد**
**مسؤوليته:** كل الثوابت الثابتة للتطبيق في مكان واحد.

```python
DEFAULT_FONT_SIZE       = 11
MIN_FONT_SIZE           = 8
MAX_FONT_SIZE           = 20
SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56
CONTENT_MIN_WIDTH       = 820
WINDOW_DEFAULT_W        = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH
```

**يُحذف من:** `app_settings.py` و `app_state.py` (مكررة فيهم).

---

### `ui/font.py` — **جديد**
**مسؤوليته:** كل حاجة ليها علاقة بحجم الخط فقط.

```python
get_font_size() -> int
set_font_size(size: int)
fs(base: int, delta: int = 0) -> int
apply_font(app: QApplication, size=None)
```

**إصلاح `fs()`:**
```python
# قبل (خطأ — hardcoded):
return max(base + delta, 7)

# بعد (صح):
from ui.constants import MIN_FONT_SIZE
return max(base + delta, MIN_FONT_SIZE)
```

**يُنقل من:** `app_settings.py`.

---

### `ui/theme.py` — **جديد**
**مسؤوليته:** الألوان الحالية `_C` وكل عمليات الثيم فقط.

```python
_C: dict
apply_theme(theme_colors, app=None)
get_theme_color(key, fallback) -> str
invalidate_stylesheet_cache()
```

**إصلاح `invalidate_stylesheet_cache()`:**
```python
# قبل: بتحسب hash جواها (خطأ منطقي)
# بعد: تمسح فقط — الـ hash يتحسب lazy في أول طلب بعدها
def invalidate_stylesheet_cache():
    _ss_cache.clear()
    _module_font_size = None
```

**يُنقل من:** `app_settings.py`.

---

### `ui/events.py` — **تعديل**
**مسؤوليته:** الـ Event Bus فقط.

**يُحذف:** `bus.data_changed` نهائياً (deprecated).

```python
# قبل الحذف — grep في كل الـ codebase:
# grep -r "bus.data_changed\|data_changed.emit" --include="*.py"
# كل استخدام يتحول لـ emit_company_data_changed()

# النتيجة النهائية — 4 signals فقط:
bus.company_data_changed  # pyqtSignal(int)
bus.font_changed          # pyqtSignal(int)
bus.theme_changed         # pyqtSignal(str)
bus.language_changed      # pyqtSignal(str)
```

---

### `ui/app_state.py` — **تعديل**
**مسؤوليته:** cache الخط + invalidate عند تغيير الشركة.

```python
# يُحذف (مكرر):
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20

# يُضاف:
from ui.constants import DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE
```

---

### `ui/app_settings.py` — **يتحول لـ facade مؤقت ثم يُحذف**

بعد إنشاء `constants.py` + `font.py` + `theme.py` يتحول لـ re-export فقط:

```python
# app_settings.py — facade مؤقت، يُحذف بعد تحديث كل الـ imports
from ui.constants import *
from ui.theme    import _C, apply_theme, get_theme_color, invalidate_stylesheet_cache
from ui.font     import get_font_size, set_font_size, fs, apply_font
```

---

### `ui/settings_dialog.py` — **تعديل**

```python
# يُحذف (deprecated):
def _get_settings_conn(self):        ...   # استخدم _get_settings_conn_and_status
def _has_active_company(self):       ...   # استخدم _get_settings_conn_and_status

# كل استخدام داخلي يتحول لـ:
conn, has_company = self._get_settings_conn_and_status()
```

---

### `ui/main_window.py` — **تعديل**

**إضافة 1 — validation للـ index_map:**
```python
def _validate_index_map(self):
    stack_count = self._stack.count()
    for key, idx in self._index_map.items():
        assert idx < stack_count, f"index_map['{key}'] = {idx} خارج الـ stack ({stack_count})"
# يُستدعى مرة واحدة بعد _build_tabs()
```

**إضافة 2 — error guard في `_on_company_changed`:**
```python
def _on_company_changed(self, company_id: int):
    try:
        AppState.invalidate()
        self._refresh_tabs()
    except Exception as e:
        print(f"[ERROR] _on_company_changed: {e}")
        return
    bus.company_data_changed.emit(company_id)
```

---

## الجزء الثاني — `ui/widgets/`

### البنية الحالية vs المقترحة

```
ui/widgets/ (الحالي)             ui/widgets/ (المقترح)
──────────────────────────────   ──────────────────────────────
core/                            core/
  __init__.py  ← re-export بس     __init__.py  ← يُحذف
  colors.py                        colors.py
  conn.py                          conn.py
  events.py                        events.py
  guard.py                         guard.py
  i18n.py      ← re-export بس     (يُحذف — import مباشر من ui.widgets.core.i18n)

components/                      components/
  button.py                        button.py
  label.py                         label.py
  headers.py                       headers.py
  notification.py                  notification.py
  spinner.py                       spinner.py
  stat_row.py                      stat_row.py
  action_toolbar.py ← صغير جداً   (يُدمج في headers.py)

base/                            base/
  list_panel.py                    list_panel.py
  detail_panel.py                  detail_panel.py
  section.py                       section.py
  tab_section.py                   tab_section.py
  crud_form.py                     crud_form.py
                                   shared_list_panel.py  ← ينتقل من widgets/shared/

panels/                          panels/
  state.py                         state.py
  filter.py                        filter.py
  detail_section.py                detail_section.py
  data_table.py                    data_table.py
  form_parts.py                    form_parts.py
  collapsible_card.py ← صغير      layout_widgets.py  ← دمج card_grid + collapsible_card
  card_grid.py        ← صغير      (يُحذف الملفان)
  crud_section.py     ← deprecated (يُحذف نهائياً)

mixins/                          mixins/
  bus.py                           bus.py
  shared_ops.py                    shared_ops.py
  refresh.py   ← صغير             data_mixins.py  ← دمج: refresh + rebuild + select
  rebuild.py   ← صغير             form_mixins.py  ← دمج: edit + validate
  select.py    ← صغير             service.py      ← يبقى منفرداً (له منطق DB)
  edit.py      ← صغير             (تُحذف الملفات الأصلية الـ 5)
  validate.py  ← صغير
  service.py

tables/                          tables/
  builders.py                      tables.py      ← دمج: builders + items
  items.py                         flexible.py    ← يبقى منفرداً
  flexible.py

theme/         ← folder لملف 1  styles.py  ← ينتقل لـ widgets/ مباشرة
  styles.py                        (يُحذف الـ folder)

forms/         ← folder لملف 1  form_inputs.py  ← ينتقل لـ widgets/ مباشرة
  inputs.py                        (يُحذف الـ folder)

utils/                           utils/
  signals.py   ← دالة واحدة      ui_utils.py  ← دمج: signals + tooltip + flow_layout
  tooltip.py   ← دالتين           splitter.py
  flow_layout.py ← class واحدة   date_range.py
  splitter.py                      searchable_combo.py
  date_range.py                    no_wheel.py
  searchable_combo.py
  no_wheel.py

combo/                           combo/
  unit.py                          unit.py
  category.py                      category.py

dialogs/                         dialogs/
  shell.py                         dialogs_base.py  ← دمج: shell + base
  base.py                          message.py
  message.py                       confirm.py
  confirm.py                       (يُحذف shell.py + base.py المنفردان)

helpers/       ← folder لملف 1  (يُحذف الـ folder)
  color_picker.py                  color_picker.py  ← ينتقل لـ components/

managers/      ← folder لملف 1  (يُحذف الـ folder)
  category.py                      category_manager.py  ← ينتقل لـ widgets/ مباشرة

shared/        ← folder لملف 1  (يُحذف الـ folder)
  list_panel_with_shared.py        → ينتقل لـ base/shared_list_panel.py

component_row/                   component_row/
  widget.py                        widget.py
  ui.py                            ui.py
  op_rows.py                       op_rows.py
  variants.py                      variants.py
```

---

## تفاصيل الدمجات

---


### دمج 2: `tables/` — 3 ملفات → 2 ملفات

#### `tables/tables.py` — **جديد (دمج builders + items)**
**مسؤوليته:** كل أدوات بناء الجداول العادية.

```python
# من builders.py:
make_table(...)
make_compact_table(...)
make_list_table(...)
make_fixed_table(...)
make_splitter_table(...)
fit_splitter_table(...)
ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48

# من items.py:
make_item(...)
bold_item(...)
colored_item(...)
center_item(...)
muted_item(...)
insert_row(...)
set_row_bg(...)
apply_row_height(...)
calc_width(...)
auto_fit_columns(...)
apply_tooltips(...)
```

**يُحذف:** `builders.py`, `items.py`
**يبقى:** `flexible.py` منفرداً (منطق مختلف تماماً — delegates + tree)

---

### دمج 3: `panels/` — يُحذف `crud_section.py` + دمج بطاقتين

#### `panels/crud_section.py` — **يُحذف نهائياً**
```python
# كل import قديم:
from ui.widgets.panels.crud_section import CrudSection
# يتحول لـ:
from ui.widgets.base.section import BaseSection as CrudSection
# أو مباشرة:
from ui.widgets.base.section import BaseSection
```

#### `panels/layout_widgets.py` — **جديد (دمج card_grid + collapsible_card)**
**مسؤوليته:** Widgets تنظيم Layout مش عرض بيانات.

```python
# من collapsible_card.py:
class CollapsibleCard(QWidget):
    ...

# من card_grid.py:
class CardGrid(QWidget):
    ...
```

**يُحذف:** `collapsible_card.py`, `card_grid.py`

---

### دمج 4: `dialogs/` — shell + base → ملف واحد

#### `dialogs/dialogs_base.py` — **جديد (دمج shell + base)**
**مسؤوليته:** الـ base classes للـ dialogs.

```python
# من shell.py:
class DialogShell(QDialog):
    ...

# من base.py (يرث من DialogShell):
class BaseDialog(DialogShell):
    ...
```

**يُحذف:** `shell.py`, `base.py`
**يبقى:** `message.py`, `confirm.py` منفردين (مسؤوليات مختلفة)

---

### دمج 5: `utils/` — 3 ملفات صغيرة → ملف واحد

#### `utils/ui_utils.py` — **جديد (دمج signals + tooltip + flow_layout)**
**مسؤوليته:** أدوات UI مساعدة صغيرة ليس ليها مكان أوضح.

```python
# من signals.py:
@contextmanager
def blocked_signals(*widgets): ...

# من tooltip.py:
def apply_table_tooltips(table, cols=None): ...
def apply_tree_tooltips(tree, item=None, cols=None, recursive=True): ...

# من flow_layout.py:
class FlowLayout(QLayout): ...
```

**يُحذف:** `signals.py`, `tooltip.py`, `flow_layout.py`
**يبقى منفرداً:** `splitter.py`, `date_range.py`, `searchable_combo.py`, `no_wheel.py`

---

### نقل 1: Folders بملف واحد → يُنقل الملف ويُحذف الـ Folder

| من | إلى | الـ Folder |
|----|-----|-----------|
| `theme/styles.py` | `widgets/styles.py` | يُحذف `theme/` |
| `forms/inputs.py` | `widgets/form_inputs.py` | يُحذف `forms/` |
| `helpers/color_picker.py` | `components/color_picker.py` | يُحذف `helpers/` |
| `managers/category.py` | `widgets/category_manager.py` | يُحذف `managers/` |
| `shared/list_panel_with_shared.py` | `base/shared_list_panel.py` | يُحذف `shared/` |

---

### نقل 2: `core/__init__.py` + `core/i18n.py`

**`core/__init__.py`** — يُحذف لأنه re-export لدالة واحدة فقط.
```python
# كل import من core/__init__:
from ui.widgets.core import get_font_size
# يتحول لـ:
from ui.font import get_font_size
```

**`core/i18n.py`** — يُحذف لأنه re-export من `ui/i18n` بدون إضافة.
```python
# كل import من core/i18n:
from ui.widgets.core.i18n import tr, i18n_manager
# يبقى كما هو لأن core/i18n هو المصدر الفعلي مش re-export
# → راجع: لو core/i18n فيه منطق حقيقي يبقى → يُدمج في i18n مباشرة
```

---

### `components/action_toolbar.py` → يُدمج في `components/headers.py`

`ActionToolbar` بتُستخدم حصرياً من `DetailHeader` في `headers.py`.
المنطقي إنها تبقى في نفس الملف.

```python
# headers.py يضم:
class ActionToolbar(QWidget): ...   # ينتقل من action_toolbar.py
class SearchBar(QWidget): ...
class StatusBar(QWidget): ...
class DetailHeader(QWidget): ...    # استخدامها الوحيد لـ ActionToolbar
class ListHeader(QWidget): ...
# ... إلخ
```

**يُحذف:** `action_toolbar.py`

---

## البنية النهائية الكاملة

```
ui/
├── constants.py              ← جديد: كل الثوابت
├── font.py                   ← جديد: إدارة الخط
├── theme.py                  ← جديد: الألوان والثيم
├── events.py                 ← معدّل: حُذف data_changed
├── app_state.py              ← معدّل: حُذفت الثوابت المكررة
├── app_settings.py           ← facade مؤقت ثم يُحذف
├── main_window.py            ← معدّل: validation + error guard
├── settings_dialog.py        ← معدّل: حُذفت الدوال deprecated
└── themes/
    └── theme_manager.py      ← بدون تغيير

ui/widgets/
├── styles.py                 ← نُقل من theme/styles.py
├── form_inputs.py            ← نُقل من forms/inputs.py
├── category_manager.py       ← نُقل من managers/category.py
│
├── core/
│   ├── colors.py             ← بدون تغيير
│   ├── conn.py               ← بدون تغيير
│   ├── events.py             ← بدون تغيير
│   ├── guard.py              ← بدون تغيير
│   └── i18n.py               ← يُراجع: دمج أو إبقاء
│
├── components/
│   ├── button.py             ← بدون تغيير
│   ├── label.py              ← بدون تغيير
│   ├── headers.py            ← معدّل: يضم ActionToolbar
│   ├── notification.py       ← بدون تغيير
│   ├── spinner.py            ← بدون تغيير
│   ├── stat_row.py           ← بدون تغيير
│   └── color_picker.py       ← نُقل من helpers/
│
├── base/
│   ├── list_panel.py         ← بدون تغيير
│   ├── detail_panel.py       ← بدون تغيير
│   ├── section.py            ← بدون تغيير
│   ├── tab_section.py        ← بدون تغيير
│   ├── crud_form.py          ← بدون تغيير
│   └── shared_list_panel.py  ← نُقل من shared/
│
├── panels/
│   ├── state.py              ← بدون تغيير
│   ├── filter.py             ← بدون تغيير
│   ├── detail_section.py     ← بدون تغيير
│   ├── data_table.py         ← بدون تغيير
│   ├── form_parts.py         ← بدون تغيير
│   └── layout_widgets.py     ← جديد: دمج card_grid + collapsible_card
│
├── mixins/
│   ├── bus.py                ← بدون تغيير
│   ├── shared_ops.py         ← بدون تغيير
│   ├── service.py            ← بدون تغيير
│   ├── data_mixins.py        ← جديد: دمج refresh + rebuild + select
│   └── form_mixins.py        ← جديد: دمج edit + validate
│
├── tables/
│   ├── tables.py             ← جديد: دمج builders + items
│   └── flexible.py           ← بدون تغيير
│
├── utils/
│   ├── ui_utils.py           ← جديد: دمج signals + tooltip + flow_layout
│   ├── splitter.py           ← بدون تغيير
│   ├── date_range.py         ← بدون تغيير
│   ├── searchable_combo.py   ← بدون تغيير
│   └── no_wheel.py           ← بدون تغيير
│
├── combo/
│   ├── unit.py               ← بدون تغيير
│   └── category.py           ← بدون تغيير
│
├── dialogs/
│   ├── dialogs_base.py       ← جديد: دمج shell + base
│   ├── message.py            ← بدون تغيير
│   └── confirm.py            ← بدون تغيير
│
└── component_row/
    ├── widget.py             ← بدون تغيير
    ├── ui.py                 ← بدون تغيير
    ├── op_rows.py            ← بدون تغيير
    └── variants.py           ← بدون تغيير
```

---

## ترتيب التنفيذ (الأمان أولاً)

| # | الخطوة | الخطر | ملاحظة |
|---|--------|-------|--------|
| 1 | إنشاء `ui/constants.py` | صفر | ملف جديد فقط |
| 2 | تعديل `ui/app_state.py` — حذف الثوابت | محلي | |
| 3 | إنشاء `ui/font.py` + إصلاح `fs()` | محلي | |
| 4 | إنشاء `ui/theme.py` + إصلاح invalidate | محلي | |
| 5 | تحويل `ui/app_settings.py` لـ facade | صفر | لا يكسر imports |
| 6 | تنظيف `ui/settings_dialog.py` | محلي | |
| 7 | تعديل `ui/main_window.py` | محلي | |
| 8 | دمج `mixins/` — إنشاء data_mixins + form_mixins | grep أولاً | |
| 9 | دمج `tables/` — إنشاء tables.py | grep أولاً | |
| 10 | دمج `panels/layout_widgets.py` | grep أولاً | |
| 11 | دمج `dialogs/dialogs_base.py` | grep أولاً | |
| 12 | دمج `utils/ui_utils.py` | grep أولاً | |
| 13 | نقل الملفات من folders المنفردة | grep أولاً | |
| 14 | نقل `action_toolbar` → `headers.py` | grep أولاً | |
| 15 | حذف `panels/crud_section.py` | grep أولاً | |
| 16 | grep وتحديث `bus.data_changed` في كل الـ codebase | الأخطر | |
| 17 | حذف `ui/app_settings.py` facade | بعد تحديث كل imports | |

> ⚠️ **كل خطوة من 8 لـ 17** تحتاج grep أولاً لتحديث كل الـ imports قبل حذف الملف القديم.

---

## ملخص الأرقام

| | قبل | بعد | فرق |
|---|-----|-----|-----|
| ملفات `ui/` الجذرية | 5 | 7 (منظمة) | +2 تخصص |
| ملفات `mixins/` | 8 | 5 | **-3** |
| ملفات `tables/` | 3 | 2 | **-1** |
| ملفات `panels/` | 8 | 6 | **-2** |
| ملفات `utils/` | 7 | 5 | **-2** |
| ملفات `dialogs/` | 4 | 3 | **-1** |
| Folders بملف واحد | 4 | 0 | **-4** |
| ملفات deprecated | 3+ | 0 | **-3+** |
| **الإجمالي** | **~55** | **~42** | **-13 ملف** |