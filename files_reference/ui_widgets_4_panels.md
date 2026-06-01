# دليل الكود — UI / Widgets (4): Panels

> الجزء الرابع — لوحات الواجهة: حالة فارغة، فلتر، تفاصيل، بطاقات قابلة للطي، شبكة بطاقات، جداول بيانات.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [State (Empty State)](#state-empty-state) | `panels/state.py` |
| [FilterToolbar](#filtertoolbar) | `panels/filter.py` |
| [DetailSection](#detailsection) | `panels/detail_section.py` |
| [CollapsibleCard + CardGrid](#collapsiblecard--cardgrid) | `panels/layout_widgets.py` |
| [DataTableWidget](#datatablewidget) | `panels/data_table.py` |
| [CrudSection (alias)](#crudsection-alias) | `panels/crud_section.py` |

---

## State (Empty State)

### `ui/widgets/panels/state.py`

```python
EmptyState(icon="📋", title="لا توجد بيانات", subtitle="",
           action_text="", style="dashed", color=None,
           min_height=80, expandable=False)
# style: "dashed" | "solid" | "plain"
# color افتراضي من _C['text_muted']
# expandable=True → يتمدد ليملأ المساحة
# يحفظ _lbl_title reference لتحديثه مباشرة عند تغيير اللغة
# Signals: action_clicked
  .set_title(text: str)    # يُحدّث النص مباشرة بدون إعادة بناء
  .title() -> str

EmptyPanelState(icon, title, subtitle, action_text, color, parent)
# alias لـ EmptyState(expandable=True) — للتوافق مع الكود القديم

set_table_empty_state(table: QTableWidget, message="لا توجد بيانات",
                      icon="📋", color=None)
# يضيف صفاً واحداً بـ span كامل على كل الأعمدة

clear_table_empty_state(table: QTableWidget)
# يمسح صف الحالة الفارغة لو كان موجوداً (يتحقق من ItemIsSelectable)
```

---

## FilterToolbar

### `ui/widgets/panels/filter.py` — `FilterToolbar`

```python
FilterToolbar(conn=None, scope="all", show_category=True,
              show_date=False, placeholder="بحث...",
              show_presets=False)
# [إصلاح 14] يستمع لـ bus.company_data_changed لإعادة تحميل
#   التصنيفات تلقائياً عند تغيير الشركة النشطة
# يُحدِّث self._conn من company_state عند تغيير الشركة
# Signals: filter_changed

toolbar.name_query -> str
toolbar.category_id
toolbar.in_date_range(date_str: str) -> bool
toolbar.match(name, cat_id, date_str="") -> bool
toolbar.set_count(shown: int, total: int)
toolbar.reload(conn=None)
# [تحسين 16] يُحدّث self._conn لو conn محدد، ثم يُعيد تحميل التصنيفات
toolbar.reset()
# يمسح البحث + يُعيد الـ category لـ index 0 + يُعيد DateRangeFilter
```

**ملاحظة [إصلاح 14]:**
`_on_company_changed(company_id)` يُستدعى تلقائياً عند `bus.company_data_changed`.
يجلب الـ connection الجديد من `company_state.get_erp_conn()` ويُعيد تحميل التصنيفات.

---

## DetailSection

### `ui/widgets/panels/detail_section.py`

```python
DetailSection(title="", cols=1, compact=False)
# ألوان الـ labels والـ values من _C — تتغير مع الثيم
  .add_row(label, value="─", color=None, bold=False, icon="") -> QLabel
  .add_separator()
  .set_data(data: dict, clear_missing: bool = False) -> dict[str, QLabel]
  # يرجع {label_text: value_QLabel} للتحديث المباشر
  # clear_missing=True: يُخفي الصفوف غير الموجودة في data الجديدة
  # clear_missing=False (افتراضي): يحافظ على الصفوف الزائدة مع قيمها القديمة
  .clear_rows()              # يحذف كل الصفوف من الذاكرة
  .update_value(index, value, color=None)
  .value_label(index: int) -> QLabel | None
  .reset_values()            # يُعيد كل القيم لـ "─"
  .show_all_rows()           # يُظهر الصفوف المخفية بـ clear_missing=True

make_detail_row(label, value="─", color=None, bold=False) -> tuple[QLabel, QLabel]

TwoColDetails()
  .add(label, value="─", color=None, bold=False) -> QLabel
  .reset()
```

---

## CollapsibleCard + CardGrid

### `ui/widgets/panels/layout_widgets.py`

> **ملاحظة:** دُمج `panels/collapsible_card.py` و `panels/card_grid.py` في هذا الملف.

```python
# ── CollapsibleCard ──
CollapsibleCard(title="", expanded=True, accent=None)
# accent افتراضي من _C['accent']
# Signals: toggled(bool)
# المحتوى في: card.content_layout (QVBoxLayout)
  .set_expanded(expanded: bool)
  .is_expanded -> bool

# ── CardGrid ──
CardGrid(cols=4, spacing=10)
  .add_widget(widget: QWidget)
  .clear()   # يحذف كل الـ widgets بـ deleteLater

CardGrid.from_widgets(widgets: list, cols=4, spacing=10) -> CardGrid
```

---

## DataTableWidget

### `ui/widgets/panels/data_table.py`

```python
DataTableWidget(columns: list, stretch_col=-1, col_widths=None,
                title="", add_text="", search_placeholder="🔍  بحث...",
                row_height=ROW_HEIGHT_LARGE, empty_icon="📋",
                empty_title="لا توجد بيانات")
# Signals: add_clicked, search_changed(str), row_selected(int)
# [إصلاح 7] يفرق بين 3 حالات:
#   total=0         → empty state "لا توجد بيانات"
#   total>0,shown>0 → يعرض الجدول
#   total>0,shown=0 → empty state "لا توجد نتائج" (icon=🔍، subtitle=جرب تغيير البحث)

  .begin_fill()
  .insert_row() -> int
  .end_fill(shown: int = None)
  # shown: عدد الصفوف الظاهرة بعد الفلتر
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

## CrudSection (alias)

### `ui/widgets/panels/crud_section.py`

> **تنبيه:** `CrudSection` أصبح alias لـ `BaseSection` للتوافق مع الكود القديم.
> الكود الجديد يستخدم `BaseSection` من `ui/widgets/base/section.py` مباشرة.

```python
from ui.widgets.panels.crud_section import CrudSection
# مطابق تماماً لـ BaseSection — راجع الجزء الثاني للتفاصيل
```