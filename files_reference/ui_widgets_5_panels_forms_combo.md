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
| [CrudSection (alias)](#crudsection-alias) | `panels/crud_section.py` |
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

---

## FilterToolbar

### `ui/widgets/panels/filter.py`

```python
FilterToolbar(conn=None, scope="all", show_category=True,
              show_date=False, placeholder="بحث...", show_presets=False)
# [إصلاح 14] يستمع لـ bus.company_data_changed — يُعيد تحميل التصنيفات تلقائياً
# [تحسين 16] reload() يُحدّث self._conn ثم يُعيد تحميل التصنيفات
# Signals: filter_changed

toolbar.name_query -> str
toolbar.category_id
toolbar.in_date_range(date_str: str) -> bool
toolbar.match(name, cat_id, date_str="") -> bool
toolbar.set_count(shown: int, total: int)
toolbar.reload(conn=None)
toolbar.reset()
```

---

## DetailSection

### `ui/widgets/panels/detail_section.py`

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
# [إصلاح 7] يفرق بين 3 حالات:
#   total=0         → empty state "لا توجد بيانات"
#   total>0,shown>0 → يعرض الجدول
#   total>0,shown=0 → empty state "لا توجد نتائج" (icon=🔍)

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

```python
AmountSpinBox(max_=999_999_999, dec=2, min_=0, height=32, currency="")
# يغير لون الـ spinbox تلقائياً لو القيمة > 0

DateField(date=None, height=32, width=None)
  .date_str() -> str
  .set_date_str(s: str)

StyledComboBox(height=32)

LabeledInput(label, widget, unit="", spacing=8, label_width=None)
  .widget -> QWidget

RequiredLineEdit(placeholder="", height=32)
  .validate() -> bool
  .text_stripped() -> str
  .clear_error()

NotesLineEdit(placeholder="ملاحظات اختيارية...", height=30)
```

---

## Forms — Labels

### `ui/widgets/panels/form_labels.py`

```python
form_label(text, color=None) -> QLabel
required_label(text) -> QLabel     # علامة * بلون _C["danger"]
hint_label(text, color=None) -> QLabel
section_title(text, color=None, icon="") -> QLabel
separator_line() -> QFrame
```

---

## Forms — Fields

### `ui/widgets/panels/form_fields.py`

```python
spin_field(max_=999999, dec=2, min_=0, min_height=30) -> QDoubleSpinBox
int_spin_field(max_=9999, min_=0, min_height=30) -> QSpinBox
labeled_widget(widget, unit, unit_color=None, spacing=6) -> QWidget
field_row(label_text, widget, required=False, hint="") -> tuple[QLabel, QWidget]
labeled_row(label_text, *widgets, spacing=6) -> QWidget
make_form_layout(...) -> QFormLayout
```

---

## Forms — Badges

### `ui/widgets/panels/form_badges.py`

```python
make_preview_label(text="─", status="info") -> QLabel

ResultBadge(text="─", color=None, status="success")
  .set_value(text, color=None)
  .set_status(status: str)
  .reset()

ModeBadge(text="─", color="blue")
# color: "blue" | "orange" | "green" | "red" | "purple"
  .set_mode(text, color=None)
  .reset()

InlinePreview(label="النتيجة:", color=None, status="success")
  .set_value(text: str)
  .reset()
```

---

## Forms — Buttons Bar

### `ui/widgets/panels/form_buttons.py`

```python
CrudButtonsBar(add_text="", save_text="", cancel_text="", show_mode=True)
# نصوص الأزرار من tr() لو فارغة
# يشترك في bus.language_changed لتحديث نصوص الأزرار تلقائياً
# Signals: add_clicked, save_clicked, cancel_clicked
  .btn_add / btn_save / btn_cancel -> QPushButton
  .lbl_mode -> QLabel
  .set_mode_text(text: str)
```

---

## Forms — Group

### `ui/widgets/panels/form_group.py`

```python
FormGroup(title="", accent=None)
# accent افتراضي من _C["accent"]
  .add_row(label: str, widget: QWidget)
  .add_label_row(label_widget: QWidget)
  .add_separator()
  .form -> QFormLayout
```

---

## CrudSection (alias)

### `ui/widgets/panels/crud_section.py`

```python
from ui.widgets.panels.crud_section import CrudSection
# مطابق تماماً لـ BaseSection — راجع ui_widgets_2_base.md للتفاصيل
```

---

## Combos — Unit

### `ui/widgets/combo/unit_service.py` — Business Logic

```python
load_units(conn, force=False) -> list
save_units(conn, units: list)
add_unit(conn, value: str, label: str) -> bool
remove_unit(conn, value: str) -> bool
get_all_units(conn) -> list
reset_units_to_default(conn)
invalidate_units_cache(conn=None)
get_last_unit(conn, key, fallback="cm") -> str
set_last_unit(conn, key, unit)

_DEFAULT_UNITS = [
    ("px","px — بكسل"), ("mm","mm — مليمتر"),
    ("cm","cm — سنتيمتر"), ("m","m  — متر"),
    ("inch","inch — بوصة"),
]
```

### `ui/widgets/combo/unit.py` — Widget

```python
UnitCombo(conn, last_key=None, current=None)
# يستخدم blocked_signals() داخلياً
# Signals: unit_changed(str)
  .current_unit() -> str
  .set_unit(unit: str)
  .refresh()

make_unit_combo(conn=None, current="cm", last_key=None) -> QComboBox
```

---

## Combos — Category

### `ui/widgets/combo/category.py`

```python
CategoryCombo(conn, scope="all")
# يستمع لـ bus.data_changed + bus.company_data_changed
# يستخدم blocked_signals() + weakref لمنع memory leak
# يستخدم CategoryService بدل db import مباشر
  .refresh()
  .get_category() -> int | None
  .set_category(cat_id)

populate_category_combo(combo: QComboBox, conn, scope="all",
                        all_label="— الكل —")
# تُستخدم من CategoryCombo وأي widget آخر
```