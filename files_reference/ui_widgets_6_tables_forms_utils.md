# دليل الكود — UI / Widgets (6): Tables, Forms & Utils

> الجزء السادس — جداول، فورمات، وأدوات مساعدة متنوعة.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [Tables](#tables) | `tables/tables.py` |
| [Tables — Flexible](#tables--flexible) | `tables/flexible.py` |
| [Theme Styles — Table](#theme-styles--table) | `theme/table_styles.py` |
| [Theme Styles — Input](#theme-styles--input) | `theme/input_styles.py` |
| [Theme Styles — Label](#theme-styles--label) | `theme/label_styles.py` |
| [Theme Styles — Card](#theme-styles--card) | `theme/card_styles.py` |
| [Theme Styles — Layout](#theme-styles--layout) | `theme/layout_styles.py` |
| [Theme Builders](#theme-builders) | `theme/builders.py` |
| [Forms — Inputs](#forms--inputs) | `forms/inputs.py` |
| [Forms — Labels](#forms--labels) | `panels/form_labels.py` |
| [Forms — Fields](#forms--fields) | `panels/form_fields.py` |
| [Forms — Badges](#forms--badges) | `panels/form_badges.py` |
| [Forms — Buttons Bar](#forms--buttons-bar) | `panels/form_buttons.py` |
| [Forms — Group](#forms--group) | `panels/form_group.py` |
| [Utils — Signals](#utils--signals) | `utils/signals.py` |
| [Utils — No Wheel](#utils--no-wheel) | `utils/no_wheel.py` |
| [Utils — Tooltip](#utils--tooltip) | `utils/tooltip.py` |
| [Utils — FlowLayout](#utils--flowlayout) | `utils/flow_layout.py` |
| [Utils — Splitter](#utils--splitter) | `utils/splitter.py` |
| [Utils — DateRange](#utils--daterange) | `utils/date_range.py` |
| [Utils — SearchableCombo](#utils--searchablecombo) | `utils/searchable_combo.py` |
| [Combos](#combos) | `combo/unit.py`, `combo/unit_service.py`, `combo/category.py` |
| [Dialogs](#dialogs) | `dialogs/dialogs_base.py`, `dialogs/message.py`, `dialogs/confirm.py` |

---

## Tables

### `ui/widgets/tables/tables.py`

> **ملاحظة:** دُمج `tables/builders.py` و `tables/items.py` في هذا الملف الواحد.

```python
# ── أدوات خلايا الجداول ──
make_item(text="", user_data=None, align=None, tooltip=None) -> QTableWidgetItem
bold_item(text, color=None, align=None, user_data=None, tooltip=None) -> QTableWidgetItem
colored_item(text, color, align=None, user_data=None, tooltip=None) -> QTableWidgetItem
center_item(text, color=None, bold=False, user_data=None) -> QTableWidgetItem
muted_item(text: str) -> QTableWidgetItem   # لون _C['text_muted']

insert_row(table, height=ROW_HEIGHT_NORMAL) -> int
set_row_bg(table, row, color)
apply_row_height(table, height=ROW_HEIGHT_NORMAL)
calc_width(table, extra_pad=4) -> int
auto_fit_columns(table, fixed_cols=None, stretch_col=-1, min_width=40, max_width=300)
apply_tooltips(table, cols=None)

# ── بناء الجداول ──
make_table(columns, stretch_col=-1, col_widths=None,
           max_height=None, min_height=100,
           row_height=ROW_HEIGHT_NORMAL) -> QTableWidget

make_compact_table(columns, stretch_col=-1, col_widths=None,
                   max_height=200) -> QTableWidget

make_list_table(columns, stretch_col=-1, col_widths=None) -> QTableWidget
# border:none, border-radius:0

make_fixed_table(columns, col_widths: dict, max_height=None,
                 min_height=60, row_height=ROW_HEIGHT_NORMAL) -> QTableWidget

make_splitter_table(columns, ..., extra_pad=20) -> tuple[QSplitter, QTableWidget]
make_splitter_table_guarded(columns, ...) -> tuple[QSplitter, QTableWidget, SplitterScrollGuard]

fit_splitter_table(splitter, table, extra_pad=20, delay_ms=0)
# المصدر الوحيد لمنطق ضبط عرض الـ splitter حسب عرض الجدول

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48
```

---

## Tables — Flexible

### `ui/widgets/tables/flexible.py`

```python
make_flexible_table(columns, stretch_col=-1, wrap_cols=None,
                    min_row_height=32) -> QTableWidget

set_flexible_columns(table, wrap_cols=None, min_row_height=32)

FlexItem(text="", tooltip=None) -> QTableWidgetItem

WrapDelegate(parent=None, min_row_height=28, padding=6)
AutoTooltipDelegate(parent=None)

FlexibleTreeWidget(parent=None)
  .setWrapColumn(col: int)
  .addFlexibleItem(parent_item, texts: list, tooltips: list = None) -> QTreeWidgetItem

# لا يُعيد تصدير refresh_tooltips — استورد مباشرة:
# from ui.widgets.utils.tooltip import refresh_tooltips
```

---

## Theme Styles — Table

### `ui/widgets/theme/table_styles.py`

```python
table_style(variant="normal") -> str   # "normal" | "compact" | "large"
splitter_style() -> str       # المصدر الوحيد — لا تكرار

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48
```

---

## Theme Styles — Input

### `ui/widgets/theme/input_styles.py`

```python
input_style(height=32, error=False) -> str
# [إصلاح] error colors من _C["input_error_bg/border"] بدل hardcoded

spinbox_style(height=32, positive=False, widget="QDoubleSpinBox") -> str
# [إصلاح] positive colors من _C["input_positive_*"] بدل hardcoded

search_input_style(height=34) -> str
```

---

## Theme Styles — Label

### `ui/widgets/theme/label_styles.py`

```python
status_label_style(status="info", font_offset=0) -> str
muted_label_style(font_offset=-1) -> str
section_title_style(color=None, font_offset=0) -> str
icon_btn_style(color="#aaa", hover_color="#e53935") -> str
link_btn_style(color=None) -> str
```

---

## Theme Styles — Card

### `ui/widgets/theme/card_styles.py`

```python
card_style(bg=None, border=None, radius=10) -> str
status_card_style(status="info", radius=8) -> str
group_box_style(accent=None) -> str
```

---

## Theme Styles — Layout

### `ui/widgets/theme/layout_styles.py`

```python
tab_style(accent=None, size="normal") -> str   # "normal" | "inner" | "small"
scroll_style(width=6) -> str       # المصدر الوحيد
filter_bar_style() -> str
toolbar_style() -> str
tree_style() -> str
list_style() -> str
```

---

## Theme Builders

### `ui/widgets/theme/builders.py`

```python
h_divider(color=None, height=1) -> QFrame
v_divider(color=None, width=1, margin_v=4) -> QFrame
wrap_in_scroll(widget: QWidget, min_height=0, horizontal=False) -> QScrollArea
```

---

## Forms — Inputs

### `ui/widgets/forms/inputs.py`

```python
AmountSpinBox(max_=999_999_999, dec=2, min_=0, height=32, currency="")
# يغير لون الـ spinbox تلقائياً لو القيمة > 0 (positive=True → أخضر)

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
  .btn_add, .btn_save, .btn_cancel -> QPushButton
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

## Utils — Signals

### `ui/widgets/utils/signals.py`

```python
@contextmanager
blocked_signals(*widgets)
# يوقف signals لواحد أو أكثر من الـ widgets ثم يعيدها تلقائياً
# مثال: with blocked_signals(self.cmb_a, self.cmb_b): ...
```

---

## Utils — No Wheel

### `ui/widgets/utils/no_wheel.py`

```python
install_no_wheel_filter(app: QApplication)
# يمنع عجلة الماوس من تغيير قيمة QComboBox / QAbstractSpinBox / QSlider
# Shift+Wheel → يُمرِّر للـ horizontal scrollbar
install_shift_wheel_filter = install_no_wheel_filter   # alias

NoWheelCombo(QComboBox)
NoWheelSpin(QSpinBox)
NoWheelDouble(QDoubleSpinBox)
NoWheelDate(QDateEdit)
NoWheelSlider(QSlider)
```

---

## Utils — Tooltip

### `ui/widgets/utils/tooltip.py`

```python
apply_table_tooltips(table: QTableWidget, cols: list[int] | None = None)
apply_tree_tooltips(tree: QTreeWidget, item=None, cols=None, recursive=True)
refresh_tooltips = apply_table_tooltips   # alias موحد
```

---

## Utils — FlowLayout

### `ui/widgets/utils/flow_layout.py`

```python
FlowLayout(parent=None, h_spacing=6, v_spacing=4)
# hasHeightForWidth() = True — يدعم dynamic height
```

---

## Utils — Splitter

### `ui/widgets/utils/splitter.py`

```python
fit_list_panel(splitter, list_index, table, min_w=280, max_w=620, extra_pad=24) -> int
fit_list_panel_delayed(splitter, list_index, table, delay_ms=0, min_w=280, max_w=620)

SmartSplitter(orientation=Qt.Horizontal)
  .set_list_widget(widget, list_table, list_index=0, min_w=280, max_w=620)
  .fit_now() -> int
  .fit_delayed(delay_ms=50)

SplitterScrollGuard(splitter, table, table_index=0, extra_pad=20, parent=None)
# يمنع الـ splitter من التوسع أكثر من عرض الجدول
  .refresh()

_SplitterScrollGuard = SplitterScrollGuard   # alias
```

---

## Utils — DateRange

### `ui/widgets/utils/date_range.py`

```python
DateRangeFilter(default_from: QDate = None, default_to: QDate = None,
                width=115, height=30, show_presets=False)
# Signals: range_changed
  .in_range(date_str: str) -> bool
  .reset()
  .from_date -> QDate
  .to_date -> QDate
  .set_from(date: QDate)
  .set_to(date: QDate)
  .dt_from -> QDateEdit
  .dt_to   -> QDateEdit
```

---

## Utils — SearchableCombo

### `ui/widgets/utils/searchable_combo.py`

```python
SearchableCombo()
# _ComboFilterProxy مُحسَّن بـ setFilterFixedString للنص الفارغ [P-05]
# debounce داخلي 120ms
# Signals: item_selected(data)
  .populate(items: list)
  # items: [(display_text, user_data, is_separator), ...]
  # الـ separators المتتالية بدون عناصر بينها تُتجاهَل (pending_sep pattern)
  .clear_items()
  .current_data()
  .get_selected_id() -> int | None
  .set_selection(user_data)
  .set_placeholder(text: str)
  .block_signals(val: bool)
  .count() -> int
  .item_data(idx: int) -> data
  .set_item_text(idx: int, text: str)
  .add_item_at_start(text: str, data)   # للـ orphans
  .cmb -> QComboBox

build_grouped_items(items: list) -> list
# items[i]: (id, name, cat_id, cat_name, ...) — يقبل tuples بأي حجم ≥ 2
# يجمّع حسب cat_name — "بدون تصنيف" في الآخر
```

---

## Combos

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

### `ui/widgets/combo/category.py`

```python
CategoryCombo(conn, scope="all")
# يستمع لـ bus.data_changed + bus.company_data_changed
# يستخدم blocked_signals() داخلياً
  .refresh()
  .get_category() -> int | None
  .set_category(cat_id)

populate_category_combo(combo: QComboBox, conn, scope="all",
                        all_label="— الكل —")
```

---

## Dialogs

### `ui/widgets/dialogs/dialogs_base.py`

> **ملاحظة:** دُمج `dialogs/shell.py` و `dialogs/base.py` في هذا الملف.

```python
# ── DialogShell (كان في shell.py) ──
DialogShell(parent=None, title="", icon="📋", subtitle="",
            accent=None, min_width=380, min_height=0)
# RTL + modal تلقائي
# هيدر gradient من accent إلى accent + "cc" (~80% opacity)
# accent افتراضي من _C['accent']
  .body_layout -> QVBoxLayout
  .btn_layout -> QHBoxLayout
  ._accent -> str

# ── BaseDialog (كان في base.py) ──
BaseDialog(parent=None, title="", icon="📋", subtitle="",
           min_size=(500, 400), accent=None, show_btns=True)
# زر OK يُعدَّل لونه لو accent مختلف عن _C['accent']
def _build_content(lay: QVBoxLayout)   # Override
def _on_accept()                        # Override — افتراضياً: self.accept()
  .set_ok_enabled(enabled: bool)
  .set_ok_text(text: str)
```

---

### `ui/widgets/dialogs/message.py`

```python
# نصوص الأزرار من tr(): tr("ok") | tr("yes") | tr("no")
msg_question(parent, title: str, text: str) -> bool
msg_info(parent, title: str, text: str)
msg_warning(parent, title: str, text: str)
msg_critical(parent, title: str, text: str)
```

---

### `ui/widgets/dialogs/confirm.py`

```python
# نصوص من tr(): tr("confirm") | tr("cancel") | tr("delete") | tr("save")
confirm_delete(parent, item_name: str, extra_msg: str = "") -> bool
confirm_action(parent, title, message, icon="❓", confirm_text="",
               cancel_text="", danger=False, accent=None) -> bool
confirm_save(parent, item_name: str = "", extra_msg: str = "") -> bool
# accent=_C["success"]
```