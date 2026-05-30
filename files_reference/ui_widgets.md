# دليل الكود — UI / Widgets

> مرجع سريع لكل مكونات الواجهة في `ui/widgets` و`ui/` العامة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [UI — App Settings](#ui--app-settings) | `app_settings`, `app_state`, `events`, `themes`, `i18n` |
| [UI — Widgets Base](#ui--widgets-base) | `base/list_panel`, `base/detail_panel`, `base/section`, `base/tab_section`, `base/crud_form` |
| [UI — Widgets Components](#ui--widgets-components) | `button`, `label`, `headers`, `notification`, `spinner`, `stat_row`, `action_toolbar` |
| [UI — Widgets Panels](#ui--widgets-panels) | `crud_section`, `state`, `filter`, `detail_section`, `collapsible_card`, `card_grid`, `data_table` |
| [UI — Widgets Mixins](#ui--widgets-mixins) | `bus`, `refresh`, `edit`, `rebuild`, `select`, `validate`, `service`, `shared_ops` |
| [UI — Widgets Utils](#ui--widgets-utils) | `signals`, `no_wheel`, `tooltip`, `flow_layout`, `splitter`, `date_range`, `searchable_combo` |
| [UI — Widgets Tables](#ui--widgets-tables) | `tables/builders`, `tables/items`, `tables/flexible` |
| [UI — Widgets Dialogs](#ui--widgets-dialogs) | `shell`, `base`, `message`, `confirm` |
| [UI — Widgets Forms](#ui--widgets-forms) | `forms/inputs`, `panels/form_parts` |
| [UI — Widgets Combos](#ui--widgets-combos) | `combo/unit`, `combo/category` |
| [UI — Widgets Theme](#ui--widgets-theme) | `theme/styles` |
| [UI — Managers](#ui--managers) | `managers/category` |
| [UI — Main](#ui--main) | `main_window`, `settings_dialog` |
| [UI — ComponentRow](#ui--componentrow) | `component_row/widget`, `component_row/ui`, `component_row/op_rows`, `component_row/variants` |
| [UI — Widgets Shared](#ui--widgets-shared) | `shared/list_panel_with_shared` |


---

## UI — App Settings

### `ui/app_settings.py`

**ثوابت:**
- `DEFAULT_FONT_SIZE = 11`
- `MIN_FONT_SIZE = 8`
- `MAX_FONT_SIZE = 20`
- `SIDEBAR_EXPANDED_WIDTH = 224`
- `SIDEBAR_COLLAPSED_WIDTH = 56`
- `CONTENT_MIN_WIDTH = 820`
- `WINDOW_DEFAULT_W = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH`

**`_C`** — dict ألوان التطبيق الحالية (يتغير مع الثيم).  
المفاتيح: `bg_page, bg_surface, bg_surface_2, bg_hover, bg_active, bg_input, border, border_med, border_focus, border_strong, text_primary, text_sec, text_muted, text_disabled, accent, accent_hover, accent_light, accent_mid, accent_text, sidebar_bg, sidebar_text, sidebar_muted, sidebar_hover, sidebar_active, sidebar_border, danger, danger_bg, danger_border, success, success_bg, success_border, warning, warning_bg, warning_border, info, info_bg, info_border, tab_active, tab_indicator, purple, purple_bg, purple_border, orange, orange_bg, orange_border`

```python
get_font_size() -> int
# يقرأ من module cache أولاً ثم AppState

set_font_size(size: int)
# يحدث cache + AppState + DB

fs(base: int, delta: int = 0) -> int
# حجم خط نسبي — الحد الأدنى 7
# مثال: fs(11, +2) = 13

apply_font(app: QApplication, size=None)
apply_theme(theme_colors: dict, app=None)
# يحدث _C + يمسح الـ cache + يطبق stylesheet

get_theme_color(key, fallback="#000000") -> str
invalidate_stylesheet_cache()
```

---

### `ui/app_state.py`

```python
AppState.font_size() -> int          # من DB مع cache
AppState.on_font_changed(size)       # يحدث cache + stylesheet cache
AppState.invalidate()                # يمسح كل الـ cache — عند تغيير الشركة
```

---

### `ui/events.py`

```python
bus = _EventBus()
bus.data_changed          # pyqtSignal() — إشعار عام
bus.company_data_changed  # pyqtSignal(int) — مع company_id
bus.font_changed          # pyqtSignal(int)
bus.theme_changed         # pyqtSignal(str) — "light" | "dark"
bus.language_changed      # pyqtSignal(str) — "ar" | "en"
```

---

### `ui/themes/__init__.py` (theme_manager)

```python
theme_manager.current_theme -> str  # "light" | "dark"
theme_manager.is_dark -> bool
theme_manager.set_theme(theme_name, save=True)
# يطبق الثيم ويُطلق bus.theme_changed تلقائياً
theme_manager.load_from_db()
theme_manager.get_available_themes() -> list[{key, name, active}]
```

---

### `ui/widgets/core/i18n.py` (i18n_manager + tr)

المصدر الوحيد لنظام الترجمة في التطبيق.

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
i18n_manager.load_from_db()
i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]

tr(key, lang=None, **kwargs) -> str
# مثال: tr("save") → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X") → "هل تريد حذف «X»؟"
```

---

## UI — Widgets Base

### `ui/widgets/base/list_panel.py` — `BaseListPanel`

**Override المطلوب:**
```python
COLUMNS: list          # أسماء الأعمدة
STRETCH_COL: int       # عمود يتمدد (-1 = لا يوجد)
EMPTY_ICON: str
EMPTY_TITLE: str
_load_rows() -> list   # تحميل البيانات
_fill_row(table, row_index, row_data)  # ملء صف واحد
```

**Override الاختياري:**
```python
COL_WIDTHS: dict
LIST_TITLE: str
ADD_TEXT: str
SEARCH_PLACEHOLDER: str
SHOW_CATEGORY: bool = False
SHOW_DATE: bool = False
FILTER_SCOPE: str = "all"
DATE_COL: str = "date"
CONNECT_BUS: bool = True
SORTABLE: bool = False
COL_KEYS: list
SORT_DEFAULT_COL: int = -1
PAGINATE: bool = False
PAGE_SIZE: int = 200

_match_filter(row, query) -> bool
_match_category(row, cat_id) -> bool
_match_date(row) -> bool
_on_add_clicked()
_on_data_changed()
_build_extra_header_actions(header)
_sort_key(col, row)
```

**API:**
```python
panel.refresh()
panel.select_item(item_id)
panel.selected_id() -> int | None
panel.current_id -> int | None  # property
panel.add_header_action(text, callback=None, style="normal") -> QPushButton
panel.set_add_enabled(enabled: bool)
panel.total_rows -> int
panel.shown_rows -> int
```

---

### `ui/widgets/base/detail_panel.py` — `BaseDetailPanel`

**Override المطلوب:**
```python
EMPTY_ICON, EMPTY_TITLE, EMPTY_SUBTITLE
_load_data(item_id) -> dict | None
_fill_data(data: dict)
_build_content(layout: QVBoxLayout)
```

**Override الاختياري:**
```python
HEADER_BG: str
MIN_CONTENT_W: int = 500
CONNECT_BUS: bool = False
_build_header_cards()
_build_header_buttons()
_fill_header(data)
_on_data_changed()
```

**Signals:** `saved = pyqtSignal(int)` | `deleted = pyqtSignal()`

**API:**
```python
panel.load_item(item_id)
panel.clear()
panel.show_success(msg, auto_hide=3000)
panel.show_error(msg)
panel.show_warning(msg, auto_hide=0)
panel.show_info(msg, auto_hide=0)
panel.item_id -> int | None
panel.item_data -> dict | None
panel.header -> DetailHeader
panel.content_layout -> QVBoxLayout
```

---

### `ui/widgets/base/section.py` — `BaseSection`

**Override المطلوب:**
```python
_create_list() -> QWidget
_create_detail() -> QWidget
```

**Override الاختياري:**
```python
LIST_MIN_W: int = 280
LIST_MAX_W: int = 560
DETAIL_MIN_W: int = 320
CONNECT_BUS: bool = False
LAYOUT_REVERSED: bool = False
FORM_POSITION: str = "none"  # "none" | "bottom" | "left"
SPLITTER_RATIO: tuple = (1, 2)

_create_form() -> QWidget | None
_connect_signals()
_on_data_changed()
_on_item_selected(item_id)
```

**API:**
```python
section.refresh()
section.clear_detail()
section.select_item(item_id)
section.list_panel -> QWidget
section.detail_panel -> QWidget
section.form_panel -> QWidget | None
```

---

### `ui/widgets/base/crud_form.py` — `BaseCrudForm`
 
قاعدة مشتركة لكل فورمات CRUD. يوفر `QWidget + EditModeMixin + LiveConnMixin` مع `FormGroup` وأزرار add/save/cancel داخل scroll.
 
**Signals:** `saved = pyqtSignal(int)` — يُطلق بعد نجاح الإضافة أو التعديل مع ID العنصر.
 
**إعدادات الـ subclass:**
```python
FORM_TITLE : str = "بيانات العنصر"  # عنوان الـ FormGroup
ADD_TEXT   : str = "➕  إضافة"       # نص زر الإضافة
SAVE_TEXT  : str = "💾  حفظ التعديل" # نص زر الحفظ
```
 
**Hooks المطلوبة (override إلزامي):**
```python
_build_fields(group: FormGroup)       # إضافة الحقول داخل FormGroup
_collect() → dict | None              # جمع قيم الحقول — None عند فشل التحقق
_do_insert(data: dict) → int          # إدراج سجل جديد — يرجع ID
_do_update(item_id: int, data: dict)  # تحديث سجل موجود
_do_load(item_id: int) → dict | None  # تحميل بيانات للتعديل
_fill_fields(data: dict)              # ملء الحقول بالبيانات
_reset_fields()                       # مسح الحقول وإعادة الضبط
```
 
**Hook اختياري:**
```python
_build_extra(root_layout: QVBoxLayout)  # إضافة widgets إضافية بعد FormGroup
```
 
**API:**
```python
form.load_for_edit(item_id: int)
# يُحمِّل عنصراً للتعديل ويدخل edit mode تلقائياً
# يستدعي _do_load → _fill_fields → enter_edit_mode
 
# Attributes المُنشأة تلقائياً:
form.btn_add    → QPushButton
form.btn_save   → QPushButton
form.btn_cancel → QPushButton
form.lbl_mode   → QLabel
```
 
**مثال:**
```python
class MyForm(BaseCrudForm):
    FORM_TITLE = "بيانات العنصر"
    ADD_TEXT   = "➕ إضافة"
    SAVE_TEXT  = "💾 حفظ التعديل"
 
    def _build_fields(self, group):
        self.inp_name = RequiredLineEdit("اسم...")
        group.add_row("الاسم :", self.inp_name)
 
    def _collect(self):
        if not self.inp_name.validate():
            return None
        return {"name": self.inp_name.text_stripped()}
 
    def _do_insert(self, data) -> int:
        return ItemService(self.conn).add(data["name"], 0, "raw")
 
    def _do_update(self, item_id, data):
        ItemService(self.conn).update(item_id, data["name"], 0)
 
    def _do_load(self, item_id):
        r = ItemService(self.conn).get(item_id)
        return vars(r) if r else None
 
    def _fill_fields(self, data):
        self.inp_name.setText(data.get("name", ""))
 
    def _reset_fields(self):
        self.inp_name.clear()
```


## UI — Widgets Components

### `ui/widgets/components/button.py`

```python
make_btn(text, style="normal", fixed_size=True) -> QPushButton
# style: "primary" | "success" | "danger" | "ghost" | "normal"

invalidate_stylesheet_cache()
refresh_visible_buttons(root_widget) -> int
```

---

### `ui/widgets/components/label.py`

```python
# ── Labels ──
InfoRow(separator="  ·  ")
  .set_parts(parts: list)
  .set_text(text)

ModeLabel(add_text="جديد", icon="")
  .set_add_mode(text=None)
  .set_edit_mode(name="")
  .set_custom(text, color=None)
  .is_edit_mode -> bool

AmountLabel(value=None, currency="ج", decimals=2, bold=True,
            font_size_offset=0, auto_color=True)
  .set_amount(value, color=None)
  .set_debit(value)
  .set_credit(value)
  .reset(placeholder="─")

# ── Display Widgets ──
DebitCreditDisplay(currency="ج")
  .update(total_dr, total_cr)
  .reset()

BalanceDisplay(currency="ج")
  .set_balance(value, side_label="", color=None)
  .set_debit_credit_balance(dr, cr)
  .reset()

ProgressBar(label="", color=None, height=8, show_pct=True)
  .set_value(value, label=None)  # 0-100
  .reset()

MultiProgressBar(spacing=8)
  .add_bar(label, value=0, color=None) -> ProgressBar
  .clear_bars()
  .update_bar(index, value)

# ── Helpers ──
format_amount(value, decimals=2, currency="ج") -> str
amount_color(value, positive_color=None, negative_color=None, zero_color=None) -> str
```

---

### `ui/widgets/components/headers.py`

```python
SearchBar(placeholder="", delay_ms=250, height=34)
# Signals: search_changed(str)
  .text() -> str
  .clear()
  .set_placeholder(text)

StatusBar()
  .set_count(shown, total)
  .set_text(text)
  .clear_count()

SectionHeader(title="")
  .set_title(title)
  .add_button(text, callback=None, style="normal") -> QPushButton

PageHeader(title="", subtitle="", icon="", accent=None, compact=False)
  .set_title(text) | .set_subtitle(text)
  .add_action(text, callback=None, style="primary") -> QPushButton

DetailHeader(bg=None)
  .set_title(text)
  .set_type_badge(text, color=None)
  .set_status_badge(text, text_color, bg, border)
  .set_priority_badge(text, color="#6b7280")
  .set_customer_name(name)
  .set_info(parts: list)
  .add_stat_card(icon, title, value="─", color="#1565c0", compact=True)
  .clear_stat_cards()
  .add_action(text, callback=None, style="primary") -> QPushButton
  .toolbar -> ActionToolbar

ListHeader(title="", add_text="", show_search=True,
           search_placeholder="", search_delay=250)
# Signals: search_changed(str), add_clicked
  .add_action(text, callback=None, style="normal") -> QPushButton
  .search_text() -> str
  .clear_search()
  .set_add_enabled(enabled)
  .search_bar -> SearchBar | None
  .btn_add -> QPushButton | None
```

---

### `ui/widgets/components/notification.py`

```python
NotificationBar(show_dismiss=True)
# Signals: dismissed
  .show(message, level="info", auto_hide=0)
  # level: "success" | "info" | "warning" | "danger"
  .hide_bar()

BaseWarningBar(on_fix=None, on_edit=None, fix_text="🗑️ حذف الناقص",
               edit_text="✏️ تعديل", show_dismiss=True)
# Signals: fix_clicked, edit_clicked, dismissed
  .show_message(message, fix_text=None, edit_text=None)
  .show_orphans(orphans, product_name, type_labels=None)
  .hide_warning()
  .set_fix_visible(v) | .set_edit_visible(v)
```

---

### `ui/widgets/components/spinner.py`

```python
LoadingSpinner(text="جارٍ التحميل...", color=None, compact=False)
  .start() | .stop() | .set_text(text)
  .is_running() -> bool

LoadingOverlay(parent=None)
  .show_loading(text="جارٍ التحميل...")
  .hide_loading()

LoadingButton(text="")
  .set_loading(loading: bool, text=None)
  .set_original_text(text)
```

---

### `ui/widgets/components/stat_row.py`

```python
BadgeLabel()
  .set_badge(text, text_color=None, bg=None, border=None)
  .clear_badge()

StatCard(icon="", title="", value="─", color="#1565c0",
         bg=None, border=None, compact=False)
  .set_value(text)
  .set_color(color)
  .value_label() -> QLabel

StatusChip(icon="", label="", count=0, color="#6b7280",
           bg=None, border=None, compact=False)
  .set_count(count)
  .count() -> int

@dataclass
StatItem(label, color="#1565c0", icon="", value="─",
         bg=None, border=None, bold_value=True, compact=False)

StatRow(items: list[StatItem], separator=True, compact=False, bg=None)
  .set_value(index, text, color=None)
  .set_value_by_label(label, text, color=None)
  .value_label(index) -> QLabel
  .reset_all()
  .update_all(values: dict)
  .card(index) -> _StatCard | None

# Helpers
make_stat_row(*items, separator=True, compact=False, bg=None) -> StatRow
stat_card_pair(label, color, icon="") -> tuple[QFrame, QLabel]
make_stat_card_simple(label, value="─", color="#1565c0", icon="") -> StatCard
make_status_chip(icon, label, count=0, color="#6b7280") -> StatusChip
```

---

## UI — Widgets Panels

### `ui/widgets/panels/state.py`

```python
EmptyState(icon="📋", title="لا توجد بيانات", subtitle="",
           action_text="", style="dashed", color=None,
           min_height=80, expandable=False)
# Signals: action_clicked
  .set_title(text)
  .title() -> str

EmptyPanelState(...)  # alias لـ EmptyState(expandable=True)

set_table_empty_state(table, message="لا توجد بيانات", icon="📋", color=None)
clear_table_empty_state(table)
```

---

### `ui/widgets/panels/filter.py` — `FilterToolbar`

```python
FilterToolbar(conn=None, scope="all", show_category=True,
              show_date=False, placeholder="بحث...",
              show_presets=False)
# Signals: filter_changed

toolbar.name_query -> str
toolbar.category_id
toolbar.in_date_range(date_str) -> bool
toolbar.match(name, cat_id, date_str) -> bool
toolbar.set_count(shown, total)
toolbar.reload(conn=None)
toolbar.reset()
```

---

### `ui/widgets/panels/detail_section.py`

```python
DetailSection(title="", cols=1, compact=False)
  .add_row(label, value="─", color=None, bold=False, icon="") -> QLabel
  .add_separator()
  .set_data(data: dict, clear_missing=False) -> dict[str, QLabel]
  .clear_rows()
  .update_value(index, value, color=None)
  .value_label(index) -> QLabel | None
  .reset_values()
  .show_all_rows()

make_detail_row(label, value="─", color=None, bold=False) -> tuple[QLabel, QLabel]

TwoColDetails()
  .add(label, value="─", color=None, bold=False) -> QLabel
  .reset()
```

---

### `ui/widgets/panels/collapsible_card.py`

```python
CollapsibleCard(title="", expanded=True, accent=None)
# Signals: toggled(bool)
# المحتوى في: card.content_layout (QVBoxLayout)
  .set_expanded(expanded: bool)
  .is_expanded -> bool
```

---

### `ui/widgets/panels/card_grid.py`

```python
CardGrid(cols=4, spacing=10)
  .add_widget(widget)
  .clear()

CardGrid.from_widgets(widgets: list, cols=4, spacing=10) -> CardGrid
```

---

### `ui/widgets/panels/data_table.py`

```python
DataTableWidget(columns, stretch_col=-1, col_widths=None,
                title="", add_text="", search_placeholder="🔍  بحث...",
                row_height=ROW_HEIGHT_LARGE, empty_icon="📋",
                empty_title="لا توجد بيانات")
# Signals: add_clicked, search_changed(str), row_selected(int)

  .begin_fill()
  .insert_row() -> int
  .end_fill(shown=None)
  .selected_id() -> int | None
  .select_row_by_id(item_id)
  .add_header_action(text, callback=None, style="normal") -> QPushButton
  .search_text() -> str
  .clear_search()
  .set_add_enabled(enabled)
  .header -> ListHeader
  .table -> QTableWidget
```

---

## UI — Widgets Mixins

### `ui/widgets/mixins/bus.py` — `BusConnectedMixin`

```python
def _connect_bus(data=True, company=False, theme=False, lang=False)
def _disconnect_bus()
def _on_data_changed()
def _on_company_changed(company_id)
def _on_theme_changed(theme_name)
def _on_language_changed(lang_code)
def invalidate_company_cache()
```

---

### `ui/widgets/mixins/refresh.py` — `RefreshableMixin`

```python
def refresh()
def _load_data() -> []  # Override
def _fill_ui(data)      # Override
def _on_refresh_error(error)  # Override اختياري
```

---

### `ui/widgets/mixins/edit.py` — `EditModeMixin`

```python
def init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode=None)
def enter_edit_mode(item_id, mode_text="")
def exit_edit_mode(add_text="")
def is_edit_mode -> bool
# _editing_id: int | None
```

---

### `ui/widgets/mixins/rebuild.py` — `RebuildMixin`

```python
# يفترض: self._root_layout (QVBoxLayout)
def _replace_widget(new_widget)
def _schedule_rebuild(delay_ms=0)
def _rebuild()  # Override
```

---

### `ui/widgets/mixins/select.py` — `SelectionMixin`

```python
_id_col: int = 0
_id_role: int = Qt.UserRole

def _selected_id(table=None) -> int | None
def _selected_row(table=None) -> int
def _require_selection(msg="") -> int | None
def _warn_no_selection(msg="")
```

---

### `ui/widgets/mixins/validate.py` — `FormValidationMixin`

```python
def _warn(msg)
def validate_required(fields: list, parent=None) -> bool
# fields: [(widget, label), ...]
# يدعم QLineEdit و QComboBox

def validate_amount(spinbox, label="", min_val=0.01) -> bool
def validate_positive(value, label="") -> bool
```

---

### `ui/widgets/mixins/service.py` — `ServiceMixin`

```python
# Properties كسولة — يفترض: self.conn
._item_service    -> ItemService(self.conn)
._category_service -> CategoryService(self.conn)
._product_service  -> ProductService(self.conn)
._order_service    -> OrderService(self.conn)
._journal_service  -> JournalService(self.conn)
```

---

### `ui/widgets/mixins/shared_ops.py` — `SharedOpsMixin`

```python
def _edit_shared_item(item_id, shared_type, parent=None)
def _publish_item(row, shared_type, item_data, parent=None)
```

---


## UI — Widgets Shared
 
### `ui/widgets/shared/list_panel_with_shared.py` — `SharedItemsListPanel`
 
قاعدة مشتركة للجداول التي تدعم العناصر المشتركة/المنشورة بين الشركات.
يرث من `BaseListPanel + SharedOpsMixin + LiveConnMixin`.
 
**إعدادات الـ subclass:**
```python
SHARED_TYPE      : str  = "raw"    # "raw" | "machine" | "labor_op" | "machine_op"
TABLE_COLS       : list = []       # أسماء الأعمدة — تُحوَّل تلقائياً لـ COLUMNS
TABLE_TITLE      : str  = ""       # عنوان الجدول
HAS_BULK_REPLACE : bool = False    # يُظهر زر "استبدال شامل" في الهيدر
SHOW_CATEGORY    : bool = True     # افتراضياً مفعَّل
CONNECT_BUS      : bool = True
```
 
**ملاحظة:** العمود 0 يُخفى تلقائياً (`setColumnHidden(0, True)`) ويُستخدم لحمل الـ ID.
`STRETCH_COL` يُضبط على 1 تلقائياً.
 
**Hooks المطلوبة (override إلزامي):**
```python
_fetch_local_rows() → list[dict]
_fill_table_row(r: int, item: dict)
_edit_item(item_id: int)
_delete_item(item_id: int, item_name: str)
```
 
**Hooks الاختيارية:**
```python
_get_shared_rows(local_rows: list) → list[dict]
_get_item_data_for_publish(row: dict) → dict
_bulk_replace_item(item_id: int, item_name: str)
_setup_column_widths(table)
_on_edit_shared()
```
 
**مساعدات:**
```python
panel._selected_row_data() → tuple[int | None, str]
panel._get_current_row_dict() → dict | None
```

---

## UI — Widgets Utils

### `ui/widgets/utils/signals.py`

```python
@contextmanager
blocked_signals(*widgets)
```

---

### `ui/widgets/utils/searchable_combo.py`

```python
SearchableCombo()
# Signals: item_selected(data)
  .populate(items: list)
  .clear_items()
  .current_data()
  .get_selected_id()
  .set_selection(user_data)
  .set_placeholder(text)
  .count() -> int
  .item_data(idx) -> data
  .add_item_at_start(text, data)

build_grouped_items(items: list) -> list
```

---

### `ui/widgets/utils/no_wheel.py`

```python
install_no_wheel_filter(app: QApplication)

NoWheelCombo(QComboBox)
NoWheelSpin(QSpinBox)
NoWheelDouble(QDoubleSpinBox)
NoWheelDate(QDateEdit)
NoWheelSlider(QSlider)
```

---

### `ui/widgets/utils/tooltip.py`

```python
apply_table_tooltips(table, cols=None)
apply_tree_tooltips(tree, item=None, cols=None, recursive=True)
```

---

### `ui/widgets/utils/flow_layout.py`

```python
FlowLayout(parent=None, h_spacing=6, v_spacing=4)
```

---

### `ui/widgets/utils/date_range.py`

```python
DateRangeFilter(default_from=None, default_to=None,
                width=115, height=30, show_presets=False)
# Signals: range_changed
  .in_range(date_str: str) -> bool
  .reset()
  .from_date -> QDate
  .to_date -> QDate
  .set_from(date) | .set_to(date)
  .dt_from -> QDateEdit
  .dt_to   -> QDateEdit
```

---

### `ui/widgets/utils/splitter.py`

```python
fit_list_panel(splitter, list_index, table, min_w=280, max_w=620, extra_pad=24) -> int
fit_list_panel_delayed(splitter, list_index, table, delay_ms=0, ...)

SmartSplitter(orientation=Qt.Horizontal)
  .set_list_widget(widget, list_table, list_index=0, min_w=280, max_w=620)
  .fit_now() -> int
  .fit_delayed(delay_ms=50)

SplitterScrollGuard(splitter, table, table_index=0, extra_pad=20)
  .refresh()
```

---

## UI — Widgets Tables

### `ui/widgets/tables/builders.py`

```python
make_table(columns, stretch_col=-1, col_widths=None,
           max_height=None, min_height=100,
           row_height=ROW_HEIGHT_NORMAL) -> QTableWidget

make_compact_table(columns, stretch_col=-1, col_widths=None,
                   max_height=200) -> QTableWidget

make_list_table(columns, stretch_col=-1, col_widths=None) -> QTableWidget

make_fixed_table(columns, col_widths: dict, max_height=None,
                 min_height=60, row_height=ROW_HEIGHT_NORMAL) -> QTableWidget

make_splitter_table(columns, ...) -> tuple[QSplitter, QTableWidget]
make_splitter_table_guarded(columns, ...) -> tuple[QSplitter, QTableWidget, SplitterScrollGuard]

fit_splitter_table(splitter, table, extra_pad=20, delay_ms=0)

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48
```

---

### `ui/widgets/tables/items.py`

```python
make_item(text="", user_data=None, align=None, tooltip=None) -> QTableWidgetItem
bold_item(text, color=None, align=None, user_data=None, tooltip=None) -> QTableWidgetItem
colored_item(text, color, align=None, user_data=None, tooltip=None) -> QTableWidgetItem
center_item(text, color=None, bold=False, user_data=None) -> QTableWidgetItem
muted_item(text) -> QTableWidgetItem

insert_row(table, height=ROW_HEIGHT_NORMAL) -> int
set_row_bg(table, row, color)
apply_row_height(table, height=ROW_HEIGHT_NORMAL)
calc_width(table, extra_pad=4) -> int
auto_fit_columns(table, fixed_cols=None, stretch_col=-1, min_width=40, max_width=300)
apply_tooltips(table, cols=None)
```

---

### `ui/widgets/tables/flexible.py`

```python
make_flexible_table(columns, stretch_col=-1, wrap_cols=None,
                    min_row_height=32) -> QTableWidget

set_flexible_columns(table, wrap_cols=None, min_row_height=32)

FlexItem(text="", tooltip=None) -> QTableWidgetItem

WrapDelegate(parent=None, min_row_height=28, padding=6)

refresh_tooltips(table)
```

---

## UI — Widgets Dialogs

### `ui/widgets/dialogs/shell.py` — `DialogShell`

```python
DialogShell(parent=None, title="", icon="📋", subtitle="",
            accent=None, min_width=380, min_height=0)
  .body_layout -> QVBoxLayout
  .btn_layout -> QHBoxLayout
```

---

### `ui/widgets/dialogs/base.py` — `BaseDialog`

```python
BaseDialog(parent=None, title="", icon="📋", subtitle="",
           min_size=(500, 400), accent=None, show_btns=True)

def _build_content(lay: QVBoxLayout)  # Override
def _on_accept()                       # Override

  .set_ok_enabled(enabled)
  .set_ok_text(text)
```

---

### `ui/widgets/dialogs/message.py`

```python
msg_question(parent, title, text) -> bool
msg_info(parent, title, text)
msg_warning(parent, title, text)
msg_critical(parent, title, text)
```

---

### `ui/widgets/dialogs/confirm.py`

```python
confirm_delete(parent, item_name, extra_msg="") -> bool
confirm_action(parent, title, message, icon="❓", confirm_text="",
               cancel_text="", danger=False, accent=None) -> bool
confirm_save(parent, item_name="", extra_msg="") -> bool
```

---

## UI — Widgets Forms

### `ui/widgets/forms/inputs.py`

```python
AmountSpinBox(max_=999_999_999, dec=2, min_=0, height=32, currency="")

DateField(date=None, height=32, width=None)
  .date_str() -> str  # "YYYY-MM-DD"
  .set_date_str(s)

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

### `ui/widgets/panels/form_parts.py`

```python
# ── Label builders ──
form_label(text, color=None) -> QLabel
required_label(text) -> QLabel
hint_label(text, color=None) -> QLabel
section_title(text, color=None, icon="") -> QLabel
separator_line() -> QFrame

# ── Row builders ──
field_row(label_text, widget, required=False, hint="") -> tuple[QLabel, QWidget]
labeled_row(label_text, *widgets, spacing=6) -> QWidget
make_form_layout(spacing=10, ...) -> QFormLayout
make_preview_label(text="─", status="info") -> QLabel

# ── Spin fields ──
spin_field(max_=999999, dec=2, min_=0, min_height=30) -> QDoubleSpinBox
int_spin_field(max_=9999, min_=0, min_height=30) -> QSpinBox
labeled_widget(widget, unit, unit_color=None, spacing=6) -> QWidget

# ── Result Badges ──
ResultBadge(text="─", color=None, status="success")
  .set_value(text, color=None)
  .set_status(status)
  .reset()

ModeBadge(text="─", color="blue")
  .set_mode(text, color=None)
  .reset()

FormGroup(title="", accent=None)
  .add_row(label, widget)
  .add_label_row(label_widget)
  .add_separator()
  .form -> QFormLayout

InlinePreview(label="النتيجة:", color=None, status="success")
  .set_value(text)
  .reset()

# ── CrudButtonsBar ──
CrudButtonsBar(add_text="", save_text="", cancel_text="", show_mode=True)
# Signals: add_clicked, save_clicked, cancel_clicked
  .btn_add, .btn_save, .btn_cancel -> QPushButton
  .lbl_mode -> QLabel
  .set_mode_text(text)

ModeLabel  # من components/label.py
```

---

## UI — Widgets Combos

### `ui/widgets/combo/unit.py`

```python
UnitCombo(conn, last_key=None, current=None)
# Signals: unit_changed(str)
  .current_unit() -> str
  .set_unit(unit)
  .refresh()

make_unit_combo(conn=None, current="cm", last_key=None) -> QComboBox

load_units(conn, force=False) -> list
save_units(conn, units: list)
add_unit(conn, value, label) -> bool
remove_unit(conn, value) -> bool
get_all_units(conn) -> list
reset_units_to_default(conn)
invalidate_units_cache(conn=None)

get_last_unit(conn, key, fallback="cm") -> str
set_last_unit(conn, key, unit)
```

---

### `ui/widgets/combo/category.py`

```python
CategoryCombo(conn, scope="all")
  .refresh()
  .get_category() -> int | None
  .set_category(cat_id)

populate_category_combo(combo, conn, scope="all", all_label="— الكل —")
```

---

### `ui/widgets/helpers/color_picker.py`

```python
ColorPickerWidget(default="#607d8b", btn_text="اختر لون")
# Signals: color_changed(str)
  .current_color() -> str
  .set_color(color)
```

---

## UI — Widgets Theme

### `ui/widgets/theme/styles.py`

```python
# ── Inputs ──
input_style(height=32, error=False) -> str
spinbox_style(height=32, positive=False, widget="QDoubleSpinBox") -> str

# ── Tables ──
table_style(variant="normal") -> str
# variant: "normal" | "compact" | "large"

splitter_style() -> str
scroll_style(width=6) -> str

# ── Cards & Frames ──
card_style(bg=None, border=None, radius=10) -> str
status_card_style(status="info", radius=8) -> str
group_box_style(accent=None) -> str

# ── Tabs ──
tab_style(accent=None, size="normal") -> str
# size: "normal" | "inner" | "small"

# ── Misc ──
tree_style() -> str
list_style() -> str
filter_bar_style() -> str
toolbar_style() -> str
muted_label_style(font_offset=-1) -> str
section_title_style(color=None, font_offset=0) -> str
icon_btn_style(color="#aaa", hover_color="#e53935") -> str
link_btn_style(color=None) -> str

# ── Dividers ──
h_divider(color=None, height=1) -> QFrame
v_divider(color=None, width=1, margin_v=4) -> QFrame

# ── Scroll ──
wrap_in_scroll(widget, min_height=0, horizontal=False) -> QScrollArea

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48
```

---

### `ui/widgets/core/colors.py`

```python
card_colors(color: str) -> tuple[str, str]
# (bg, border) من CARD_PALETTE

status_colors(level: str) -> dict
# level: "success" | "warning" | "danger" | "info" | "neutral" | "primary" | "purple" | "orange"
# Returns: {fg, bg, border}

waste_level(pct) -> str
waste_colors(pct) -> tuple[str, str]
```

---

### `ui/widgets/core/events.py`

```python
get_active_company_id() -> int | None
emit_company_data_changed()
is_same_company(company_id) -> bool
```

---

### `ui/widgets/core/conn.py`

```python
# ── LiveConnMixin ──
  ._live_conn() -> Connection
  ._invalidate_conn_cache()
  ._live_acc_conn() -> Connection

# ── SafeConnMixin ──
  ._init_safe_conn(conn, db_name="accounting")
  ._get_safe_conn() -> Connection
  ._get_company_id() -> int | None
  ._should_respond_to_company(company_id, stored_attr="_company_id") -> bool

# ── DualConnMixin(SafeConnMixin) ──
  ._init_dual_conn(acc_conn, erp_conn, acc_db="accounting")
  ._get_erp_conn() -> Connection
  ._on_dual_company_event(company_id) -> bool
```

---

### `ui/widgets/core/guard.py`

```python
@requires_company
def my_method(self): ...

@requires_company(return_value=[])
def _load_rows(self) -> list: ...

@requires_company(return_value_factory=list)
def _load_rows(self) -> list: ...
```

---

## UI — Managers

### `ui/widgets/managers/category.py`

```python
CategoryManager(conn, scope="all")
# شجرة QTreeWidget لإدارة التصنيفات
# يشترك في bus.data_changed + bus.language_changed

CategoryForm(conn, scope, tree_widget)
  .load_for_edit(cat_id)
```

---

## UI — Main

### `ui/main_window.py` — `MainWindow`

```python
MainWindow(app: QApplication)

# index_map:
# "costing":    1
# "pricing":    2
# "accounting": 3
# "inventory":  4
# "design":     5
# "orders":     6
```

---

### `ui/settings_dialog.py` — `SettingsDialog`

```python
SettingsDialog(app, parent=None)
# تبويبات: الخط | المظهر | اللغة | الوحدات | GIMP
# حفظ: يُطلق bus.font_changed + bus.theme_changed + bus.language_changed
```

---

## UI — ComponentRow

### `ui/widgets/components/component_row/widget.py` — `ComponentRow`

```python
ComponentRow(catalog_fn,
             child_type="raw",
             child_id=None,
             qty=1.0,
             waste_pct=0.0,
             raw_total_qty=None,
             show_total_qty=False,
             variant_id=None,
             machine_op_row_id=None)
# Signals: removed(QWidget)

  .get_values() -> tuple | None
  # (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)

  .get_waste_pct() -> float
  .get_variant_id() -> int | None
  .get_machine_op_row_id() -> int | None
  .is_orphan() -> bool
  .set_orphan_name(name)
  .refresh_catalog(_new_catalog=None)
  .expose_load_op_rows(op_id, selected_row_id=None)
```

**Attributes:** `cmb_type`, `_item_combo`, `cmb_variant`, `lbl_variant_cost`, `qty_edit`, `waste_spin`, `total_qty_edit`, `cmb_op_row`, `lbl_op_row_cost`, `_sub_row_widget`

---

## أمثلة شائعة

### إنشاء قسم CRUD كامل

```python
from ui.widgets.base.section import BaseSection

class MySection(BaseSection):
    LIST_MIN_W = 300
    CONNECT_BUS = True

    def _create_list(self):
        return MyListPanel(self.conn)

    def _create_detail(self):
        return MyDetailPanel(self.conn)

    def _connect_signals(self):
        self._list.item_selected.connect(self._detail.load_item)
```

### استخدام bus events

```python
from ui.widgets.mixins.bus import BusConnectedMixin

class MyWidget(QWidget, BusConnectedMixin):
    def __init__(self):
        super().__init__()
        self._connect_bus(data=True, theme=True)

    def _on_data_changed(self):
        self.refresh()

    def _on_theme_changed(self, theme_name):
        self.setStyleSheet(f"background:{_C['bg_page']};")
```

### التحقق من الشركة النشطة

```python
from ui.widgets.core.guard import requires_company

class MyPanel(QWidget):
    @requires_company(return_value=[])
    def _load_rows(self):
        return fetch_all_items(self.conn)
```
