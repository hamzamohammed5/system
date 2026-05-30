# دليل الكود — UI / Widgets (6): Tables, Forms & Utils

> الجزء السادس — جداول، فورمات، وأدوات مساعدة متنوعة.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [Tables — Builders](#tables--builders) | `tables/builders` |
| [Tables — Items](#tables--items) | `tables/items` |
| [Tables — Flexible](#tables--flexible) | `tables/flexible` |
| [Theme Styles](#theme-styles) | `theme/styles` |
| [Forms — Inputs](#forms--inputs) | `forms/inputs` |
| [Forms — Parts](#forms--parts) | `panels/form_parts` |
| [Utils — Signals](#utils--signals) | `utils/signals` |
| [Utils — No Wheel](#utils--no-wheel) | `utils/no_wheel` |
| [Utils — Tooltip](#utils--tooltip) | `utils/tooltip` |
| [Utils — FlowLayout](#utils--flowlayout) | `utils/flow_layout` |
| [Utils — Splitter](#utils--splitter) | `utils/splitter` |
| [Utils — DateRange](#utils--daterange) | `utils/date_range` |
| [Utils — SearchableCombo](#utils--searchablecombo) | `utils/searchable_combo` |
| [Combos](#combos) | `combo/unit`, `combo/category` |
| [Dialogs](#dialogs) | `dialogs/shell`, `dialogs/base`, `dialogs/message`, `dialogs/confirm` |

---

## Tables — Builders

### `ui/widgets/tables/builders.py`

```python
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

## Tables — Items

### `ui/widgets/tables/items.py`

```python
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

refresh_tooltips(table: QTableWidget)
```

---

## Theme Styles

### `ui/widgets/theme/styles.py`

> جميع الدوال تقرأ من `_C` وتعيد stylesheets محدثة — تتغير تلقائياً مع الثيم.

```python
# ── Inputs ──
input_style(height=32, error=False) -> str
spinbox_style(height=32, positive=False, widget="QDoubleSpinBox") -> str
search_input_style(height=34) -> str

# ── Tables ──
table_style(variant="normal") -> str   # "normal" | "compact" | "large"
splitter_style() -> str       # المصدر الوحيد — لا تكرار
scroll_style(width=6) -> str  # المصدر الوحيد

# ── Cards & Frames ──
card_style(bg=None, border=None, radius=10) -> str
status_card_style(status="info", radius=8) -> str
group_box_style(accent=None) -> str

# ── Tabs ──
tab_style(accent=None, size="normal") -> str   # "normal" | "inner" | "small"

# ── Misc ──
tree_style() -> str
list_style() -> str
filter_bar_style() -> str
toolbar_style() -> str
status_label_style(status="info", font_offset=0) -> str
muted_label_style(font_offset=-1) -> str
section_title_style(color=None, font_offset=0) -> str
icon_btn_style(color="#aaa", hover_color="#e53935") -> str
link_btn_style(color=None) -> str

# ── Dividers ──
h_divider(color=None, height=1) -> QFrame
v_divider(color=None, width=1, margin_v=4) -> QFrame

# ── Scroll ──
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
# يستخدم _C['bg_surface_2'] (عادي) و _C['bg_input'] (عند focus)
```

---

## Forms — Parts

### `ui/widgets/panels/form_parts.py`

```python
# ── Label builders ──
# كل الألوان من _C — تتغير مع الثيم
form_label(text, color=None) -> QLabel
required_label(text) -> QLabel     # علامة * بلون _C["danger"]
hint_label(text, color=None) -> QLabel
section_title(text, color=None, icon="") -> QLabel
separator_line() -> QFrame

# ── Row builders ──
field_row(label_text, widget, required=False, hint="") -> tuple[QLabel, QWidget]
labeled_row(label_text, *widgets, spacing=6) -> QWidget
make_form_layout(...) -> QFormLayout
make_preview_label(text="─", status="info") -> QLabel

# ── Spin fields ──
spin_field(max_=999999, dec=2, min_=0, min_height=30) -> QDoubleSpinBox
int_spin_field(max_=9999, min_=0, min_height=30) -> QSpinBox
labeled_widget(widget, unit, unit_color=None, spacing=6) -> QWidget

# ── Result Badges ──
ResultBadge(text="─", color=None, status="success")
  .set_value(text, color=None)
  .set_status(status: str)
  .reset()

ModeBadge(text="─", color="blue")
# color: "blue" | "orange" | "green" | "red" | "purple"
  .set_mode(text, color=None)
  .reset()

FormGroup(title="", accent=None)
# accent افتراضي من _C["accent"]
  .add_row(label: str, widget: QWidget)
  .add_label_row(label_widget: QWidget)
  .add_separator()
  .form -> QFormLayout

InlinePreview(label="النتيجة:", color=None, status="success")
  .set_value(text: str)
  .reset()

# ── CrudButtonsBar ──
CrudButtonsBar(add_text="", save_text="", cancel_text="", show_mode=True)
# نصوص الأزرار من tr("btn_add") / tr("btn_save") / tr("btn_cancel") لو فارغة
# يشترك في bus.language_changed لتحديث نصوص الأزرار تلقائياً
# Signals: add_clicked, save_clicked, cancel_clicked
  .btn_add, .btn_save, .btn_cancel -> QPushButton
  .lbl_mode -> QLabel
  .set_mode_text(text: str)

ModeLabel   # مُستورد من components/label.py — المصدر الوحيد
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
# ألوان الـ inputs من _C — تتغير مع الثيم
# أزرار الـ presets بـ make_btn("normal") — تدعم الثيم
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
# _ComboFilterProxy مُحسَّن بـ setFilterFixedString للنص الفارغ
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

### `ui/widgets/combo/unit.py`

```python
UnitCombo(conn, last_key=None, current=None)
# يستخدم blocked_signals() داخلياً
# Signals: unit_changed(str)
  .current_unit() -> str
  .set_unit(unit: str)
  .refresh()

make_unit_combo(conn=None, current="cm", last_key=None) -> QComboBox

load_units(conn, force=False) -> list
# cache key = db path أو f"_id_{id(conn)}" كـ fallback آمن
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

---

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

### `ui/widgets/dialogs/shell.py` — `DialogShell`

```python
DialogShell(parent=None, title="", icon="📋", subtitle="",
            accent=None, min_width=380, min_height=0)
# RTL + modal تلقائي
# هيدر gradient من accent إلى accent + "cc" (~80% opacity)
# accent افتراضي من _C['accent']
  .body_layout -> QVBoxLayout
  .btn_layout -> QHBoxLayout
  ._accent -> str
```

---

### `ui/widgets/dialogs/base.py` — `BaseDialog`

```python
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
# رسالة: tr("delete_confirm_msg", name=item_name)

confirm_action(parent, title, message, icon="❓", confirm_text="",
               cancel_text="", danger=False, accent=None) -> bool

confirm_save(parent, item_name: str = "", extra_msg: str = "") -> bool
# رسالة: tr("save_confirm_msg", name=item_name)
# accent=_C["success"]
```