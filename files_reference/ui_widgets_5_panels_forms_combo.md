# دليل الكود — UI / Widgets (5): Panels, Forms & Combos

> `ui/widgets/panels/` + `ui/widgets/forms/` + `ui/widgets/combo/`
> لوحات الواجهة، حقول الفورمات، وقوائم الاختيار.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [State (Empty State)](#state-empty-state) | `panels/state.py` |
| [FilterToolbar](#filtertoolbar) | `panels/filter.py` |
| [DetailSection](#detailsection) | `panels/detail_section.py` |
| [CollapsibleCard + CardGrid](#collapsiblecard--cardgrid) | `panels/layout_widgets.py` |
| [DataTableWidget](#datatablewidget) | `panels/data_table.py` |
| [Forms — Inputs](#forms--inputs) | `forms/inputs.py` |
| [Forms — Labels](#forms--labels) | `panels/form_labels.py` |
| [Forms — Fields](#forms--fields) | `panels/form_fields.py` |
| [Forms — Badges](#forms--badges) | `panels/form_badges.py` |
| [Forms — Buttons Bar](#forms--buttons-bar) | `panels/form_buttons.py` |
| [Forms — Group](#forms--group) | `panels/form_group.py` |
| [Combos — Unit](#combos--unit) | `combo/unit.py`, `combo/unit_service.py` |
| [Combos — Category](#combos--category) | `combo/category.py` |

---

## State (Empty State)

### `ui/widgets/panels/state.py`

```python
EmptyState(icon="📋", title="لا توجد بيانات", subtitle="",
           action_text="", style="dashed", color=None,
           min_height=80, expandable=False)
# style: "dashed" | "solid" | "plain"
# يحفظ _lbl_title reference للتحديث المباشر عند تغيير اللغة
# Signals: action_clicked
  .set_title(text: str)
  .title() -> str

EmptyPanelState(icon, title, subtitle, action_text, color, parent) -> EmptyState
# alias لـ EmptyState(expandable=True) — للتوافق القديم

set_table_empty_state(table: QTableWidget, message="لا توجد بيانات",
                      icon="📋", color=None)
# يضيف صفاً واحداً بـ span على كل الأعمدة

clear_table_empty_state(table: QTableWidget)
```

**Imports:**
```python
# [FIX] absolute imports بدل relative:
from ui.font  import fs, get_font_size
from ui.theme import _C
```

---

## FilterToolbar

### `ui/widgets/panels/filter.py`

```python
FilterToolbar(conn=None, scope="all", show_category=True,
              show_date=False, placeholder="بحث...", show_presets=False)
# [إصلاح 14] يستمع لـ bus.company_data_changed — يُعيد تحميل التصنيفات تلقائياً
# [تحسين 16] reload() يُحدّث self._conn ثم يُعيد تحميل التصنيفات
# Signals: filter_changed
```

**Imports:**
```python
# [FIX] absolute imports — ثلاث نقاط (relative) كانت تُسبب ImportError:
from ui.font  import fs, get_font_size
from ui.theme import _C
```

**`_on_company_changed(company_id)`:**
```python
# يقرأ company_state.get_erp_conn() ويُحدّث self._conn
# ثم يستدعي _reload_categories()
```

```python
toolbar.name_query -> str
toolbar.category_id
toolbar.in_date_range(date_str: str) -> bool
toolbar.match(name, cat_id, date_str="") -> bool
toolbar.set_count(shown: int, total: int)
toolbar.reload(conn=None)
# [تحسين 16] يُحدّث self._conn لو conn مُعطى، ثم يُعيد تحميل التصنيفات
toolbar.reset()
```

---

## DetailSection

### `ui/widgets/panels/detail_section.py`

**Import الصحيح:**
```python
# [إصلاح 2.3] المسار الصحيح:
from ..components.headers_page import SectionHeader
# (بدل from ..components.headers import SectionHeader المحذوف)
```

```python
DetailSection(title="", cols=1, compact=False)
  .add_row(label, value="─", color=None, bold=False, icon="") -> QLabel
  .add_separator()
  .set_data(data: dict, clear_missing: bool = False) -> dict[str, QLabel]
  # clear_missing=True: يُخفي الصفوف غير الموجودة في data الجديدة
  .clear_rows()
  .update_value(index, value, color=None)
  .value_label(index: int) -> QLabel | None
  .reset_values()
  .show_all_rows()

make_detail_row(label, value="─", color=None, bold=False) -> tuple[QLabel, QLabel]

TwoColDetails()
  .add(label, value="─", color=None, bold=False) -> QLabel
  .reset()
```

---

## CollapsibleCard + CardGrid

### `ui/widgets/panels/layout_widgets.py`

**Imports:**
```python
# [FIX] absolute imports — ثلاث نقاط (relative) كانت تُسبب ImportError:
from ui.font  import fs, get_font_size
from ui.theme import _C
```

```python
CollapsibleCard(title="", expanded=True, accent=None)
# Signals: toggled(bool)
# المحتوى في: card.content_layout (QVBoxLayout)
  .set_expanded(expanded: bool)
  .is_expanded -> bool

CardGrid(cols=4, spacing=10)
  .add_widget(widget: QWidget)
  .clear()

CardGrid.from_widgets(widgets: list, cols=4, spacing=10) -> CardGrid
```

---

## DataTableWidget

### `ui/widgets/panels/data_table.py`

```python
DataTableWidget(columns, stretch_col=-1, col_widths=None,
                title="", add_text="", search_placeholder="🔍  بحث...",
                row_height=ROW_HEIGHT_LARGE, empty_icon="📋",
                empty_title="لا توجد بيانات")
# Signals: add_clicked, search_changed(str), row_selected(int)
# [إصلاح 7] end_fill() تفرّق بين 3 حالات:
#   total=0         → empty state "لا توجد بيانات"    (_empty)
#   total>0,shown>0 → يعرض الجدول
#   total>0,shown=0 → empty state "لا توجد نتائج"     (_empty_filtered, icon=🔍)
```

**`end_fill(shown: int = None)`:**
```python
total   = self.table.rowCount()
visible = shown if shown is not None else total

has_data          = visible > 0
is_filtered_empty = (not has_data) and (total > 0)

self.table.setVisible(has_data)
self._empty.setVisible(not has_data and not is_filtered_empty)
self._empty_filtered.setVisible(is_filtered_empty)
```

```python
  .begin_fill()
  .insert_row() -> int
  .end_fill(shown: int = None)
  .selected_id() -> int | None
  .select_row_by_id(item_id: int)
  .add_header_action(text, callback=None, style="normal") -> QPushButton
  .search_text() -> str
  .clear_search()
  .set_add_enabled(enabled: bool)
  .header -> ListHeader
  .table -> QTableWidget
```

---

## Forms — Inputs

### `ui/widgets/forms/inputs.py`

> **[إصلاح 1]** المسار الصحيح:
> `from ..theme.input_styles import input_style, spinbox_style`
> (بدل `from ..theme.styles` المحذوف في Refactor V3)

```python
AmountSpinBox(max_=999_999_999, dec=2, min_=0, height=32, currency="")
# يغير لون الـ spinbox تلقائياً لو القيمة > 0 (spinbox_style positive=True)

DateField(date=None, height=32, width=None)
  .date_str() -> str
  .set_date_str(s: str)

StyledComboBox(height=32)

LabeledInput(label, widget, unit="", spacing=8, label_width=None)
  .widget -> QWidget

RequiredLineEdit(placeholder="", height=32)
  .validate() -> bool      # يضبط _error=True ويُركّز لو فارغ
  .text_stripped() -> str  # text().strip()
  .clear_error()

NotesLineEdit(placeholder="ملاحظات اختيارية...", height=30)
# تغير ستايل عند focus (italic → normal)
```

---

## Forms — Labels

### `ui/widgets/panels/form_labels.py`

```python
form_label(text, color=None) -> QLabel
# color افتراضي: _C['text_sec'] | font-weight: 600
# alignment: AlignRight | AlignVCenter

required_label(text) -> QLabel
# علامة * بلون _C["danger"] كـ RichText
# alignment: AlignRight | AlignVCenter

hint_label(text, color=None) -> QLabel
# color افتراضي: _C['text_muted'] | font-size: fs(base, -1)
# wordWrap: True

section_title(text, color=None, icon="") -> QLabel
# color افتراضي: _C['accent'] | font-weight: 700
# icon يُدمج: f"{icon}  {text}" لو icon غير فارغ

separator_line() -> QFrame
# QFrame.HLine | height: 1 | color: _C['border']
```

---

## Forms — Fields

### `ui/widgets/panels/form_fields.py`

**Import الصحيح:**
```python
# [FIX] المسار الصحيح:
from ..theme.input_styles import spinbox_style
# (بدل from ..theme.styles الذي لم يعد موجوداً بعد Refactor V3)
```

```python
spin_field(max_=999999, dec=2, min_=0, min_height=30) -> QDoubleSpinBox
# يُطبّق spinbox_style(min_height, widget="QDoubleSpinBox")

int_spin_field(max_=9999, min_=0, min_height=30) -> QSpinBox
# يُطبّق spinbox_style(min_height, widget="QSpinBox")

labeled_widget(widget, unit, unit_color=None, spacing=6) -> QWidget
# [widget] [unit_label] — unit_color افتراضي: _C['text_muted']
# يُضيف addStretch() في النهاية

field_row(label_text, widget, required=False, hint="") -> tuple[QLabel, QWidget]
# required=True → required_label() | False → form_label()
# hint → يُغلّف widget في QVBoxLayout مع hint_label أسفله
# يرجع (label, widget_or_container)

labeled_row(label_text, *widgets, spacing=6) -> QWidget
# [form_label] [widget1] [widget2] ... [stretch]
# يقبل strings كـ hint_label تلقائياً
# يتجاهل None في الـ widgets

make_form_layout(spacing=10,
                 label_align=Qt.AlignRight | Qt.AlignVCenter,
                 contents_margins=(12, 10, 12, 10)) -> QFormLayout
# FieldGrowthPolicy: ExpandingFieldsGrow
```

---

## Forms — Badges

### `ui/widgets/panels/form_badges.py`

```python
make_preview_label(text="─", status="info") -> QLabel
# يستخدم status_colors(status) من core/colors
# wordWrap: True | border-radius: 6px | padding: 8px 12px
# font-size: fs(base, -1)
```

#### `ResultBadge(QLabel)`

```python
ResultBadge(text="─", color=None, status="success", parent=None)
# color: لون نص مخصص — يُلغي fg من status_colors لو محدد
# status: "success" | "warning" | "danger" | "info" | ...
# border-radius: 4px | padding: 4px 8px | font-weight: bold
```

**API:**
```python
  .set_value(text: str, color: str = None)
  # لو color جديد ومختلف → يُعيد تطبيق _apply()

  .set_status(status: str)
  # لو status مختلف → يُعيد تطبيق _apply()

  .reset()
  # setText("─")
```

**منطق `_apply()`:**
```python
# لو _custom_color محدد:
#   color = _custom_color | bg/border من status_colors
# لو لا:
#   color = s['fg'] | bg/border من status_colors
```

#### `ModeBadge(QLabel)`

```python
ModeBadge(text="─", color="blue", parent=None)
# color: "blue" | "orange" | "green" | "red" | "purple"
# يُترجم color → status key:
#   "blue"   → "primary"
#   "orange" → "warning"
#   "green"  → "success"
#   "red"    → "danger"
#   "purple" → "purple"
# border-radius: 4px | padding: 3px 8px | font-weight: bold
# font-size: fs(base, -1)
```

**API:**
```python
  .set_mode(text: str, color: str = None)
  # لو color جديد ومختلف → يُعيد تطبيق _apply_style()

  .reset()
  # setText("─")
```

#### `InlinePreview(QWidget)`

```python
InlinePreview(label="النتيجة:", color=None, status="success", parent=None)
# Layout: [QLabel(label)] [ResultBadge("─")]  [stretch]
# label: color=_C['text_sec'] | font-weight: 600 | font-size: fs(base, -1)
# _lbl_value: ResultBadge داخلي
```

**API:**
```python
  .set_value(text: str)
  # يستدعي self._lbl_value.set_value(text)

  .reset()
  # يستدعي self._lbl_value.reset()
```

**مثال:**
```python
from ui.widgets.panels.form_badges import ResultBadge, ModeBadge, InlinePreview

# badge للنتيجة المحسوبة
badge = ResultBadge("─", status="success")
badge.set_value("250.00 ج", color=_C['success'])
badge.set_status("warning")   # يُغيّر الألوان
badge.reset()                 # يُعيد "─"

# badge للوضع الحالي
mode = ModeBadge("─", color="blue")
mode.set_mode("وضع التعديل", color="orange")

# عرض inline
preview = InlinePreview(label="التكلفة الكلية:", status="success")
preview.set_value("1,200.00 ج")
preview.reset()
```

---

## Forms — Buttons Bar

### `ui/widgets/panels/form_buttons.py`

```python
CrudButtonsBar(add_text="", save_text="", cancel_text="", show_mode=True, parent=None)
# نصوص الأزرار من tr() لو فارغة:
#   add_text    → tr("btn_add")
#   save_text   → tr("btn_save")
#   cancel_text → tr("btn_cancel")
# show_mode=True → يُظهر lbl_mode فوق الأزرار
# show_mode=False → lbl_mode يُنشأ لكن غير مرئي (للـ compatibility)
# يشترك في bus.language_changed بـ Qt.UniqueConnection لتحديث نصوص الأزرار
# Signals: add_clicked, save_clicked, cancel_clicked
```

**Attributes:**
```python
  .btn_add    -> QPushButton   # style: "primary"
  .btn_save   -> QPushButton   # style: "success"
  .btn_cancel -> QPushButton   # style: "ghost"
  .lbl_mode   -> QLabel        # دائماً موجود حتى لو show_mode=False
```

**API:**
```python
  .set_mode_text(text: str)
  # lbl_mode.setText(text)
```

**`_on_language_changed(lang_code)`:**
```python
# يُحدّث النصوص من tr() مباشرة — لا يُخزّن النصوص المخصصة:
self.btn_add.setText(tr("btn_add"))
self.btn_save.setText(tr("btn_save"))
self.btn_cancel.setText(tr("btn_cancel"))
```

**ملاحظة:** لو مررت `add_text` مخصص — سيُفقد عند تغيير اللغة. الـ mixin يُعيد دائماً `tr("btn_add")`.

**Layout الداخلي:**
```
QVBoxLayout:
  [lbl_mode]          ← لو show_mode=True
  QHBoxLayout:
    [btn_add] [btn_save] [btn_cancel] [stretch]
```

**`_connect_language_bus()`:**
```python
# try/except حول الاشتراك — لو فشل import bus لا يُوقف البناء
from ui.widgets.core.events import bus
bus.language_changed.connect(self._on_language_changed, Qt.UniqueConnection)
```

**مثال:**
```python
from ui.widgets.panels.form_buttons import CrudButtonsBar

bar = CrudButtonsBar(show_mode=True)
bar.add_clicked.connect(self._on_add)
bar.save_clicked.connect(self._on_save)
bar.cancel_clicked.connect(self._on_cancel)
bar.set_mode_text("─── تعديل: المنتج ───")

# مع نصوص مخصصة (تُفقد عند تغيير اللغة):
bar = CrudButtonsBar(add_text="➕ إضافة منتج", show_mode=False)
```

---

## Forms — Group

### `ui/widgets/panels/form_group.py`

```python
FormGroup(title="", accent=None, parent=None)
# يرث من QGroupBox
# accent افتراضي: _C["accent"]
# border-radius: 10px | margin-top: 10px | padding-top: 6px
# title position: top right (RTL)
```

**Layout الداخلي:**
```python
self.form = QFormLayout(self)
# spacing: 10
# labelAlignment: AlignRight | AlignVCenter
# contentsMargins: (12, 14, 12, 12)
```

**API:**
```python
  .add_row(label: str, widget: QWidget)
  # form.addRow(label, widget)

  .add_label_row(label_widget: QWidget)
  # form.addRow(label_widget) — بدون label نصي

  .add_separator()
  # يُضيف QFrame.HLine بارتفاع 1 بلون _C['border']
  # form.addRow(sep)

  .form -> QFormLayout   # الـ layout الداخلي للوصول المباشر
```

**`_apply_style()`:**
```python
# يُطبق QGroupBox stylesheet مع:
#   title color = self._accent
#   background = _C['bg_surface']
#   border = _C['border']
# يُستدعى في __init__ فقط — لا يُعيد التطبيق عند تغيير الثيم تلقائياً
```

**مثال:**
```python
from ui.widgets.panels.form_group import FormGroup

grp = FormGroup("بيانات المنتج", accent=_C['accent'])
grp.add_row("الاسم :", self.inp_name)
grp.add_row("السعر :", self.spin_price)
grp.add_separator()
grp.add_row("الفئة :", self.cmb_category)

# الوصول المباشر للـ form layout:
grp.form.setSpacing(12)
```

---

## Combos — Unit

### `ui/widgets/combo/unit_service.py` — Business Logic

```python
_UNITS_KEY     = "custom_units"
_DEFAULT_UNITS = [
    ("px","px — بكسل"), ("mm","mm — مليمتر"),
    ("cm","cm — سنتيمتر"), ("m","m  — متر"),
    ("inch","inch — بوصة"),
]

load_units(conn, force=False) -> list
save_units(conn, units: list)
add_unit(conn, value: str, label: str) -> bool
remove_unit(conn, value: str) -> bool
get_all_units(conn) -> list       # = load_units(conn)
reset_units_to_default(conn)
invalidate_units_cache(conn=None)
get_last_unit(conn, key, fallback="cm") -> str
set_last_unit(conn, key, unit)
```

### `ui/widgets/combo/unit.py` — Widget

```python
UnitCombo(conn, last_key=None, current=None)
# يستخدم blocked_signals() داخلياً عند الـ populate
# Signals: unit_changed(str)
  .current_unit() -> str    # currentData() or "cm"
  .set_unit(unit: str)
  .refresh()

make_unit_combo(conn=None, current="cm", last_key=None) -> QComboBox
# لو conn=None → يستخدم _DEFAULT_UNITS مباشرة بدون DB
```

---

## Combos — Category

### `ui/widgets/combo/category.py`

```python
CategoryCombo(conn, scope="all")
# يستمع لـ bus.company_data_changed فقط
# [FIX-14] Qt.UniqueConnection على كل ربط bus لمنع التسجيل المضاعف
# [إصلاح memory leak] يستخدم weakref للـ company_data_changed slot
#   self._company_data_slot = _on_company_data_changed  ← يحفظ مرجع الـ slot
# [إصلاح هيكلة] يستخدم CategoryService عبر populate_category_combo
  .refresh()
  .get_category() -> int | None
  .set_category(cat_id)
  # لو لم يجد → setCurrentIndex(0)

populate_category_combo(combo: QComboBox, conn, scope="all",
                        all_label="— الكل —")
# [إصلاح هيكلة] يستخدم CategoryService.get_all() + build_tree() داخلياً
# يُضيف all_label كأول خيار (data=None) لو all_label غير فارغ
# يُلوّن التصنيفات بألوانها عبر Qt.ForegroundRole
# الهرمية: depth=0 → لا indent | depth>0 → "    " * depth + "↳ "
```