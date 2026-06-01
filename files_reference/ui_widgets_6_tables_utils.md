# دليل الكود — UI / Widgets (6): Tables & Utils

> `ui/widgets/tables/` + `ui/widgets/utils/`
> بناء الجداول وأدوات الواجهة المساعدة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Tables](#tables) | `tables/tables.py` |
| [Tables — Flexible](#tables--flexible) | `tables/flexible.py` |
| [Utils — Signals](#utils--signals) | `utils/signals.py` |
| [Utils — No Wheel](#utils--no-wheel) | `utils/no_wheel.py` |
| [Utils — Tooltip](#utils--tooltip) | `utils/tooltip.py` |
| [Utils — FlowLayout](#utils--flowlayout) | `utils/flow_layout.py` |
| [Utils — Splitter](#utils--splitter) | `utils/splitter.py` |
| [Utils — DateRange](#utils--daterange) | `utils/date_range.py` |
| [Utils — SearchableCombo](#utils--searchablecombo) | `utils/searchable_combo.py` |

---

## Tables

### `ui/widgets/tables/tables.py`

> دُمج `tables/builders.py` و `tables/items.py` في هذا الملف.

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
# border:none, border-radius:0 — للـ panels

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
# tooltip تلقائي = النص

WrapDelegate(parent=None, min_row_height=28, padding=6)
# word-wrap في خلايا الجدول

AutoTooltipDelegate(parent=None)
# tooltip تلقائي بالنص الكامل

FlexibleTreeWidget(parent=None)
  .setWrapColumn(col: int)
  .addFlexibleItem(parent_item, texts: list, tooltips: list = None) -> QTreeWidgetItem
```

> **ملاحظة:** `refresh_tooltips` لا يُعاد تصديره من هنا — استورد مباشرة:
> `from ui.widgets.utils.tooltip import refresh_tooltips`

---

## Utils — Signals

### `ui/widgets/utils/signals.py`

```python
@contextmanager
blocked_signals(*widgets)
# يوقف signals لواحد أو أكثر من الـ widgets ثم يعيدها تلقائياً

# مثال:
with blocked_signals(self.cmb_a, self.cmb_b):
    self.cmb_a.clear()
    self.cmb_b.clear()
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
# يضيف tooltip = النص الكامل لكل خلية

apply_tree_tooltips(tree: QTreeWidget, item=None, cols=None, recursive=True)

refresh_tooltips = apply_table_tooltips   # alias موحد
```

---

## Utils — FlowLayout

### `ui/widgets/utils/flow_layout.py`

```python
FlowLayout(parent=None, h_spacing=6, v_spacing=4)
# Layout يرتب الـ widgets أفقياً وينزل تلقائياً لسطر جديد
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
  .dt_from / dt_to -> QDateEdit
```

---

## Utils — SearchableCombo

### `ui/widgets/utils/searchable_combo.py`

```python
SearchableCombo()
# [P-05] _ComboFilterProxy مُحسَّن بـ setFilterFixedString للنص الفارغ
# debounce داخلي 120ms
# Signals: item_selected(data)

  .populate(items: list)
  # items: [(display_text, user_data, is_separator), ...]
  # الـ separators المتتالية بدون عناصر بينها تُتجاهَل

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