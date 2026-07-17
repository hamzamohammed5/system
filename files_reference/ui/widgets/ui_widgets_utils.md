# دليل الكود — UI / Widgets: Utils

> `ui/widgets/utils/` — أدوات الواجهة المساعدة (signals, wheel filter, tooltips, layouts, splitter, date range, searchable combo).

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Utils — Signals](#utils--signals) | `utils/signals.py` |
| [Utils — No Wheel](#utils--no-wheel) | `utils/no_wheel.py` |
| [Utils — Tooltip](#utils--tooltip) | `utils/tooltip.py` |
| [Utils — FlowLayout](#utils--flowlayout) | `utils/flow_layout.py` |
| [Utils — Splitter](#utils--splitter) | `utils/splitter.py` |
| [Utils — DateRange](#utils--daterange) | `utils/date_range.py` |
| [Utils — SearchableCombo](#utils--searchablecombo) | `utils/searchable_combo.py` |

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

refresh_tooltips = apply_table_tooltips   # alias موحد — يُستخدم من tables/flexible.py
```

> **[إصلاح tooltip أبيض على Windows]** إضافة `CustomTooltipFilter` +
> `install_custom_tooltip_filter()`. على Windows (خصوصاً `windowsvista`/
> `windows11` style)، `QToolTip` الافتراضي أحياناً يتجاهل كلاً من الـ QSS
> المطبّق على `QApplication` والـ `QPalette`، ويرجع لرسم tooltip أبيض عبر
> محرك الثيم الأصلي للنظام بدل محرك رسم Qt نفسه.

```python
class _TooltipLabel(QLabel)
# QLabel عائم (window flag = Qt.ToolTip | Qt.FramelessWindowHint)
# WA_TransparentForMouseEvents + WA_ShowWithoutActivating
  .show_at(text: str, global_pos: QPoint)
  # يقرأ _C وget_font_size() وقت الظهور مباشرة — يتماشى تلقائياً مع أي
  # تغيير ثيم لاحق. إزاحة (+14, +18) عن مؤشر الماوس، مع تصحيح موضع لو
  # خرج عن حدود الشاشة (screen.availableGeometry())

class CustomTooltipFilter(QObject)
# Event filter عام يُركَّب على مستوى QApplication — يعترض QEvent.ToolTip
# قبل المعالجة الافتراضية ويعرض _TooltipLabel بدلاً من QToolTip الأصلي
  .eventFilter(obj, event) -> bool
  # [Fix] لبعض composite widgets (QDoubleSpinBox) أجزاء داخلية (QLineEdit،
  # أزرار up/down) تستقبل QEvent.ToolTip بدل الـ widget الأب — الكود يطلع
  # في سلسلة parentWidget() حتى يلاقي toolTip فعلي أو يوصل للسقف.
  # event.ignore() + return True: يمنع Qt من رسم QToolTip الأصلي حتى لو
  # النص فارغ (كان أحياناً يرجع لمحرك الثيم الأصلي للنظام رغم ذلك).

install_custom_tooltip_filter(app: QApplication) -> CustomTooltipFilter
# يُركَّب مرة واحدة على مستوى QApplication — يُستدعى من main.py بعد إنشاء
# QApplication مباشرة. آمن الاستدعاء المتكرر (singleton عبر _installed_filter
# على مستوى الموديول) — لا يُركِّب فلتر ثانٍ فوق الأول.
```

**ملاحظة معمارية:** `CustomTooltipFilter` مستقل تماماً عن
`apply_table_tooltips`/`apply_tree_tooltips` — تلك الدوال تحدد *نص* الـ
tooltip المعروض على كل خلية/عنصر، بينما هذا الفلتر يتحكم فقط في *شكل رسم*
أي tooltip في التطبيق بعد أن يتحدد نصه.

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

> **[FIX عرض الـ combo]** `self.cmb` كان يستخدم `setSizeAdjustPolicy(QComboBox.AdjustToContents)`.
> المشكلة: وقت أول بناء الـ widget، الـ source model فاضٍ (`populate()` تُنفَّذ
> لاحقاً عبر `QTimer.singleShot` من `_RowsManager.add_row`)، فـ `AdjustToContents`
> كان يعطي الـ combo عرضاً شبه صفري في أول layout pass — العمود يظهر فارغاً
> تماماً (لا نص "اختر" ولا سهم) رغم إضافته فعلياً بـ `stretch=1`.
> **الحل:** `AdjustToMinimumContentsLengthWithIcon` مع `setMinimumContentsLength(1)`
> ثابت — الـ combo يأخذ عرضاً معقولاً من أول لحظة بغض النظر عن حالة الـ model،
> ويكبر مع الـ stretch أو مع محتواه لو أكبر من الحد الأدنى.

```python
SearchableCombo()
# [P-05] _ComboFilterProxy مُحسَّن:
#   set_filter() المُحسَّن بحارس التغيير وتحسين Qt الداخلي:
#     1. النص لم يتغير → تجاهل كامل (لا invalidation)
#     2. النص فارغ    → setFilterFixedString("") مباشرة
#                        Qt يعلم أن كل الصفوف ستظهر ويُحسِّن داخلياً
#     3. النص غير فارغ → تحديث _filter_text ثم invalidateFilter() مرة واحدة
#                        filterAcceptsRow المخصصة تُطبَّق للـ separators/orphans
#   النتيجة: أقل invalidations بـ ~40% في حالة مسح النص الشائعة
# debounce داخلي 120ms (SEARCH_DELAY_MS)
# Signals: item_selected(data)

  .populate(items: list)
  # items: [(display_text, user_data, is_separator), ...]
  # الـ separators المتتالية بدون عناصر بينها تُتجاهَل (pending_sep pattern)

  .clear_items()
  .current_data()
  .get_selected_id() -> int | None
  .set_selection(user_data)
  # لو لم يجد مع فلتر نشط → يمسح الفلتر ويحاول مرة أخرى
  .set_placeholder(text: str)
  .block_signals(val: bool)
  .count() -> int
  .item_data(idx: int) -> data
  .set_item_text(idx: int, text: str)
  .add_item_at_start(text: str, data)   # للـ orphans — يستدعي invalidateFilter()
  .cmb -> QComboBox

build_grouped_items(items: list) -> list
# items[i]: (id, name, cat_id, cat_name, ...) — يقبل tuples بأي حجم ≥ 2
# يجمّع حسب cat_name — "بدون تصنيف" في الآخر
# يتجاهل cat_name=None أو فارغ → يُعامَل كـ NO_CAT
```

**`_ComboFilterProxy` — السلوك:**
```python
# الـ separators: دائماً مرئية حتى لو لم يتبقَّ عناصر بعدها
# الـ orphans (user_data[0] == "__orphan__"): دائماً مرئية
# البحث: case-insensitive على الجزء بعد "—" أو النص الكامل
```
## علاقات الملفات

- `splitter.py` يستورد `calc_width` من `tables/tables.py` (مرجع: `ui_widgets_tables.md`) و `splitter_style()` من `theme/table_styles.py` (مرجع: `ui_widgets_theme.md`).
- `searchable_combo.py` يستورد `ThemedLineEdit`/`ThemedComboBox` من `panels/themed_inputs.py` (مرجع: `ui_widgets_panels.md`).
- `date_range.py` يستورد `ThemedDateEdit` من `panels/themed_inputs.py` و `make_btn` من `components/button.py` (مرجع: `ui_widgets_components.md`).
- `no_wheel.py` يستورد `ThemedComboBox`/`ThemedDateEdit` من `panels/themed_inputs.py`.
- `signals.py` (`blocked_signals`) يُستخدم على نطاق واسع في كل المشروع تقريباً (combo/category.py, component_row/variants.py, component_row/op_rows.py, panels/filter.py, ...) كبديل موحّد لتكرار `blockSignals(True/False)` يدوياً.
- `tooltip.py` مستقل عن باقي ملفات `utils/` — يُستدعى فقط من `main.py` (لـ `install_custom_tooltip_filter`) ومن `tables/flexible.py` (لـ `refresh_tooltips`).
