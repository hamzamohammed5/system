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
# يقرأ من module cache (_module_font_size) أولاً ثم AppState

set_font_size(size: int)
# يحدث module cache + AppState + DB

fs(base: int, delta: int = 0) -> int
# حجم خط نسبي — الحد الأدنى 7 دائماً
# مثال: fs(11, +2) = 13

apply_font(app: QApplication, size=None)
# يبني stylesheet + يُطبّقه على الـ app

apply_theme(theme_colors: dict, app=None)
# يحدث _C بالألوان الجديدة (مفاتيح موجودة + مفاتيح جديدة)
# يمسح كل الـ caches (stylesheet + button)
# يُطبّق stylesheet الجديد على الـ app فوراً
# يُستدعى من ThemeManager.set_theme() عند تغيير الثيم

get_theme_color(key, fallback="#000000") -> str
# يرجع لون من _C بأمان مع fallback

invalidate_stylesheet_cache()
# يمسح _ss_cache + يُعيد حساب _current_theme_hash
# يمسح _module_font_size أيضاً (يُجبر إعادة القراءة من AppState)
# يُستدعى عند تغيير الخط أو الثيم أو الشركة

_set_module_font_cache(size: int | None)
# يُحدّث _module_font_size مباشرة — للاستخدام الداخلي
```

**Stylesheet cache:** `_ss_cache` — key هو `(font_size, theme_hash)`.
يُبنى الـ stylesheet مرة واحدة لكل مجموعة (حجم خط + ثيم) ثم يُعاد استخدامه.

---

### `ui/app_state.py`

```python
AppState.font_size() -> int          # من DB مع cache — يُحمَّل مرة واحدة فقط
AppState.on_font_changed(size)
# يحدث _font_size cache
# يُزامن _module_font_size في app_settings عبر _set_module_font_cache
# يُبطل button stylesheet cache

AppState.invalidate()
# يمسح _font_size = None
# يستدعي invalidate_stylesheet_cache() الكامل من app_settings
# (ليس button cache فقط) — مهم عند تغيير الشركة

DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20
```

---

### `ui/events.py`

```python
bus = _EventBus()
bus.data_changed          # pyqtSignal() — إشعار عام (للتوافق مع الكود القديم)
bus.company_data_changed  # pyqtSignal(int) — مقيّد بـ company_id (الأفضل للاستخدام الجديد)
bus.font_changed          # pyqtSignal(int)
bus.theme_changed         # pyqtSignal(str) — "light" | "dark"
bus.language_changed      # pyqtSignal(str) — "ar" | "en"
```

---

### `ui/themes/theme_manager.py` — `theme_manager`

```python
theme_manager.current_theme -> str  # "light" | "dark"
theme_manager.is_dark -> bool
theme_manager.set_theme(theme_name, save=True)
# يستدعي apply_theme() من app_settings (يُحدّث _C + يمسح cache + يُطبّق stylesheet)
# يُطلق bus.theme_changed تلقائياً بعد التطبيق
# يحفظ في DB لو save=True
theme_manager.load_from_db()
# يحمّل الثيم المحفوظ + يطبّقه بدون save
theme_manager.get_available_themes() -> list[{key, name, active}]

# ثوابت الثيمات:
# THEMES: {"light": _LIGHT_THEME, "dark": _DARK_THEME}
# THEME_DISPLAY_NAMES: {"light": "فاتح", "dark": "داكن"}
# كل ثيم يحتوي على نفس مفاتيح _C في app_settings
```

---

### `ui/widgets/core/i18n.py` — `i18n_manager` + `tr()`

المصدر الوحيد لنظام الترجمة. يُحمِّل الترجمات تلقائياً من `ui/i18n/ar.py` و`ui/i18n/en.py` عند الاستيراد.

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str          # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
# يُحدّث _language + يُطبّق اتجاه Layout + يحفظ في DB + يُطلق language_changed
i18n_manager.translate(key, lang=None, **kwargs) -> str
# fallback للعربية لو المفتاح ناقص في اللغة المطلوبة
i18n_manager.load_from_db()
# يحمّل اللغة المحفوظة + يُطبّق الاتجاه
i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]
i18n_manager.add_translations(lang_code, translations: dict)
# يضيف/يحدث ترجمات برمجياً

def tr(key: str, lang=None, **kwargs) -> str
# دالة الترجمة الرئيسية
# مثال: tr("save")                           → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X")   → "هل تريد حذف «X»؟" | "Delete «X»?"
# مثال: tr("showing_of", shown=5, total=100) → "5 / 100"
```

> **ملاحظة:** لا تمرر نصاً عربياً مباشرة لـ `tr()` — استخدم المفتاح المقابل دائماً.
> راجع `files_reference/i18n_reference.md` لمزيد من التفاصيل.

---

## UI — Widgets Base

### `ui/widgets/base/list_panel.py` — `BaseListPanel`

**Override المطلوب:**
```python
COLUMNS: list          # أسماء الأعمدة
STRETCH_COL: int       # عمود يتمدد (-1 = آخر عمود)
EMPTY_ICON: str
EMPTY_TITLE: str       # مفتاح tr() أو نص مباشر
_load_rows() -> list   # تحميل البيانات — يرجع list[dict]
_fill_row(table, row_index, row_data)  # ملء صف واحد
```

**Override الاختياري:**
```python
COL_WIDTHS: dict = None
MIN_W: int = 260
LIST_TITLE: str = ""
ADD_TEXT: str = ""
SEARCH_PLACEHOLDER: str = "🔍  بحث..."
SHOW_CATEGORY: bool = False
SHOW_DATE: bool = False
FILTER_SCOPE: str = "all"
DATE_COL: str = "date"
# اسم الـ key في dict البيانات الذي يحتوي التاريخ
# يُستخدم في _match_date() لقراءة التاريخ من row[DATE_COL]
# override لو كان اسم الـ key مختلفاً في بياناتك
CONNECT_BUS: bool = True

# Sort settings
SORTABLE: bool = False
COL_KEYS: list = []              # مفاتيح الأعمدة للـ sort
SORT_DEFAULT_COL: int = -1
SORT_DEFAULT_ASC: bool = True

# Pagination settings
PAGINATE: bool = False
PAGE_SIZE: int = 200

_match_filter(row, query) -> bool
# افتراضياً: يبحث في row["name"]
_match_category(row, cat_id) -> bool
# افتراضياً: يقارن row["category_id"]
_match_date(row) -> bool
# يُستدعى فقط لو SHOW_DATE=True
# يقرأ row[DATE_COL] ويمرره لـ _filter_toolbar.in_date_range()
# override لو أردت منطق مقارنة مخصص
_on_add_clicked()
_on_data_changed()                # افتراضياً: self.refresh()
_build_extra_header_actions(header: ListHeader)
_sort_key(col, row)               # يُستدعى فقط لو SORTABLE=True
```

**Bus (عند `CONNECT_BUS=True`):**
يشترك في `company_data_changed` + `data_changed` + `theme_changed` + `language_changed`.

- `_on_theme_changed(theme_name)`:
  - يُعيد تطبيق `background` على الـ widget الرئيسي
  - يُعيد تطبيق stylesheet على `_empty_state`
  - يُعيد بناء styles الـ pagination bar والـ status bar عبر `_rebuild_pagination_styles()` و `_rebuild_status_style()`

- `_on_language_changed(lang_code)`:
  - يُحدّث placeholder البحث عبر `_header.search_bar.set_placeholder()`
  - يُحدّث نص empty state عبر `_empty_state.set_title(_tr_safe(EMPTY_TITLE))`
  - يُحدّث نصوص أزرار الـ pagination عبر `_update_pagination_texts()`

**API:**
```python
panel.refresh()
# يُعيد تحميل البيانات (_load_rows) + يُعيد تحميل categories في FilterToolbar + يُطبّق الفلتر
panel.select_item(item_id)
# يبحث في الصفوف الظاهرة أولاً، ثم يُحمِّل من _page_rows لو PAGINATE=True
panel.selected_id() -> int | None
panel.current_id -> int | None     # property — alias لـ selected_id()
panel.add_header_action(text, callback=None, style="normal") -> QPushButton
panel.set_add_enabled(enabled: bool)
panel.set_sort(col, ascending=True)
panel.clear_sort()
panel.reset_pagination()           # يُعيد تطبيق الفلتر من الصفحة الأولى
panel.total_rows -> int            # عدد الصفوف بعد الفلتر
panel.shown_rows -> int            # عدد الصفوف المعروضة حالياً
panel.table -> QTableWidget        # الجدول الداخلي
```

---

### `ui/widgets/base/detail_panel.py` — `BaseDetailPanel`

**Override المطلوب:**
```python
EMPTY_ICON: str = "📋"
EMPTY_TITLE: str = "اختر عنصراً من القائمة"  # مفتاح tr() أو نص مباشر
EMPTY_SUBTITLE: str = ""
_load_data(item_id: int) -> dict | None
_fill_data(data: dict)
_build_content(layout: QVBoxLayout)
```

**Override الاختياري:**
```python
HEADER_BG: str = None              # خلفية الـ DetailHeader
MIN_CONTENT_W: int = 500
CONNECT_BUS: bool = False
# عند CONNECT_BUS=True يشترك في data + theme + lang

_build_header_cards()              # يضيف stat cards للـ header
_build_header_buttons()            # يضيف أزرار للـ header toolbar
_fill_header(data: dict)           # افتراضياً: self._hdr.set_title(data["name"])
_on_data_changed()                 # افتراضياً: load_item(self._item_id)

_on_theme_changed(theme_name: str)
# يُعيد تطبيق bg_page على الـ panel نفسه
# يُعيد تطبيق scroll_style() على الـ scroll area
# يُعيد تطبيق bg_page على inner widget والـ content widget

_on_language_changed(lang_code: str)
# يُحدّث نص _empty عبر _empty.set_title(_tr_safe(EMPTY_TITLE))
```

**Signals:** `saved = pyqtSignal(int)` | `deleted = pyqtSignal()`

**API:**
```python
panel.load_item(item_id: int)
# يستدعي _load_data → _fill_header → _fill_data
# لو data = None → يُظهر empty state
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

> **ملاحظة:** `CrudSection` في `panels/crud_section.py` هو **alias** لـ `BaseSection` للتوافق مع الكود القديم. استخدم `BaseSection` مباشرة في الكود الجديد.

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
LAYOUT_REVERSED: bool = False      # يعكس ترتيب list/detail في الـ splitter
FORM_POSITION: str = "none"
# "none"   → لا فورم (السلوك الأصلي)
# "bottom" → فورم أسفل لوحة القائمة (container مع QVBoxLayout)
# "left"   → list فقط في الـ splitter (الفورم خارجه)
SPLITTER_RATIO: tuple = (1, 2)    # نسبة list:detail في الـ splitter

_create_form() -> QWidget | None   # None = لا فورم
_connect_signals()
# افتراضياً: list.item_selected → detail.load_item (لو الاتنين موجودين)
_on_data_changed()                 # افتراضياً: self.refresh()
_on_item_selected(item_id: int)    # افتراضياً: detail.load_item(item_id)
```

**API:**
```python
section.refresh()
# يستدعي list.refresh() + يُعيد ضبط splitter sizes (50ms delay)
section.clear_detail()             # يستدعي detail.clear() لو موجودة
section.select_item(item_id)       # يختار عنصراً برمجياً
section.list_panel -> QWidget
section.detail_panel -> QWidget
section.form_panel -> QWidget | None
```

---

### `ui/widgets/base/tab_section.py` — `TabSectionBase`

```python
TabSectionBase(conn_fn=None, parent=None)
# conn_fn: callable يُعيد connection — افتراضياً get_connection() من db.shared.connection

def _build_tabs(self, tabs: QTabWidget)  # Override إلزامي — يضيف التبويبات

# Properties:
section.conn -> ProtectedConnection
section.current_tab -> QWidget | None

# closeEvent:
# يُغلق conn فقط لو كان مملوكاً (_is_owned_connection) وليس shared من company_state
# الإغلاق الحقيقي يحدث في company_state عند تغيير الشركة
```

---

### `ui/widgets/base/crud_form.py` — `BaseCrudForm`

قاعدة مشتركة لكل فورمات CRUD. يرث من `QWidget + EditModeMixin + LiveConnMixin`.
يُطلق `bus.data_changed.emit()` بعد كل إضافة أو تعديل ناجح.

**Signals:** `saved = pyqtSignal(int)` — يُطلق بعد نجاح الإضافة أو التعديل مع ID العنصر.

**إعدادات الـ subclass:**
```python
FORM_TITLE: str = "بيانات العنصر"
ADD_TEXT:   str = "➕  إضافة"
SAVE_TEXT:  str = "💾  حفظ التعديل"
```

**Hooks المطلوبة (override إلزامي):**
```python
_build_fields(group: FormGroup)        # إضافة الحقول داخل FormGroup
_collect() -> dict | None              # جمع قيم الحقول — None عند فشل التحقق
_do_insert(data: dict) -> int          # إدراج سجل جديد — يرجع ID العنصر
_do_update(item_id: int, data: dict)   # تحديث سجل موجود
_do_load(item_id: int) -> dict | None  # تحميل بيانات للتعديل
_fill_fields(data: dict)               # ملء الحقول بالبيانات
_reset_fields()                        # مسح الحقول وإعادة الضبط
```

**Hook اختياري:**
```python
_build_extra(root_layout: QVBoxLayout)
# إضافة widgets إضافية بعد FormGroup — لا شيء افتراضياً
```

**API:**
```python
form.load_for_edit(item_id: int)
# _do_load → _fill_fields → enter_edit_mode

# Attributes المُنشأة تلقائياً:
form.btn_add    -> QPushButton
form.btn_save   -> QPushButton
form.btn_cancel -> QPushButton
form.lbl_mode   -> QLabel
```

---

## UI — Widgets Components

### `ui/widgets/components/button.py`

```python
make_btn(text: str, style: str = "normal", fixed_size: bool = True) -> QPushButton
# style: "primary" | "success" | "danger" | "ghost" | "normal"
# يحفظ style على الزر كـ Qt property ("_btn_style") لاستخدامها في refresh_visible_buttons
# fixed_size=True → setFixedWidth | False → setMinimumWidth (قابل للتمدد)
# ألوان الأزرار تُقرأ من _C تلقائياً — تتغير مع الثيم

invalidate_stylesheet_cache()
# يمسح _stylesheet_cache — يُستدعى من apply_font() وعند تغيير الثيم

refresh_visible_buttons(root_widget) -> int
# يُعيد تطبيق stylesheet على كل QPushButton في الـ widget tree
# يعتمد على property("_btn_style") — يتجاهل الأزرار بدون هذا الـ property
# يرجع عدد الأزرار المحدثة

calc_btn_width(text: str, font_size: int, padding: int = 32) -> int
```

**مثال استخدام مع الثيم واللغة:**
```python
from ui.widgets.components.button import make_btn
from ui.widgets.core.i18n import tr

btn_save   = make_btn(tr("btn_save"),   "success")
btn_cancel = make_btn(tr("btn_cancel"), "ghost")
btn_delete = make_btn(tr("btn_delete"), "danger")

def _on_language_changed(self, lang_code: str):
    self.btn_save.setText(tr("btn_save"))
    self.btn_cancel.setText(tr("btn_cancel"))
```

---

### `ui/widgets/components/label.py`

```python
# ── Labels ──
InfoRow(separator="  ·  ")
  .set_parts(parts: list)   # يُرشح القيم الفارغة تلقائياً
  .set_text(text)
  .label() -> QLabel

ModeLabel(add_text="جديد", icon="")
  .set_add_mode(text=None)   # أزرق — وضع الإضافة
  .set_edit_mode(name="")    # برتقالي — وضع التعديل
  .set_custom(text, color=None)
  .is_edit_mode -> bool

AmountLabel(value=None, currency="ج", decimals=2, bold=True,
            font_size_offset=0, auto_color=True)
  .set_amount(value, color=None)
  # value=0 → "─" بلون text_muted
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

ProgressBar(label="", color=None, height=8, show_pct=True, compact=False)
  .set_value(value, label=None)  # value: 0-100
  .set_color(color)
  .value() -> float
  .reset()
  # resizeEvent: يُعيد حساب عرض الـ fill تلقائياً
  # التحقق من total_w > 0 مقصود ومهم — لا تُزِله

MultiProgressBar(spacing=8)
  .add_bar(label, value=0, color=None) -> ProgressBar
  .clear_bars()
  .update_bar(index, value)

# ── Helpers ──
format_amount(value, decimals=2, currency="ج") -> str
amount_color(value, positive_color=None, negative_color=None, zero_color=None) -> str
# يقرأ الألوان من _C تلقائياً — تتغير مع الثيم
dr_cr_color(side: str) -> str    # side: "dr" | "cr"
```

---

### `ui/widgets/components/headers.py`

```python
SearchBar(placeholder="", delay_ms=250, height=34)
# placeholder افتراضي من tr("list_search_placeholder")
# Signals: search_changed(str)
  .text() -> str
  .clear()
  .set_placeholder(text: str)
  .inp -> QLineEdit   # الحقل الداخلي

StatusBar()
# نصوص العداد من tr("showing_of") و tr("showing_all")
  .set_count(shown: int, total: int)
  .set_text(text: str)
  .clear_count()

SectionHeader(title="")
  .set_title(title)
  .add_button(text, callback=None, style="normal") -> QPushButton

PageHeader(title="", subtitle="", icon="", accent=None, compact=False)
  .set_title(text)
  .set_subtitle(text)
  .add_action(text, callback=None, style="primary") -> QPushButton

DetailHeader(bg=None)
# ActionToolbar يُنشأ بـ lazy initialization — فقط عند أول استخدام فعلي
# _tb_section مخفي بـ setVisible(False) حتى أول استخدام (يمنع spacing فارغ)
  .set_title(text)
  .set_type_badge(text, color=None)
  .set_status_badge(text, text_color="#555", bg="#f5f5f5", border="#e0e0e0")
  .set_priority_badge(text, color="#6b7280")
  .set_customer_name(name)
  .set_info(parts: list)
  .add_stat_card(icon, title, value="─", color="#1565c0", compact=True) -> StatCard
  .clear_stat_cards()
  .add_action(text, callback=None, style="primary") -> QPushButton
  # alias لـ toolbar.add_action() — يُظهر _tb_section تلقائياً
  .toolbar -> ActionToolbar   # lazy property — يُنشئ عند أول وصول

ListHeader(title="", add_text="", show_search=True,
           search_placeholder="", search_delay=250)
# يشترك في bus.language_changed لتحديث placeholder تلقائياً عبر _on_language_changed
# placeholder افتراضي من tr("list_search_placeholder")
# Signals: search_changed(str), add_clicked
  .add_action(text, callback=None, style="normal") -> QPushButton
  .search_text() -> str
  .clear_search()
  .set_add_enabled(enabled: bool)
  .search_bar -> SearchBar | None
  .btn_add -> QPushButton | None

make_list_header(title="", add_text="", show_search=True,
                 placeholder="") -> ListHeader
# placeholder افتراضي من tr("list_search_placeholder")
```

---

### `ui/widgets/components/notification.py`

```python
NotificationBar(show_dismiss=True)
# Signals: dismissed
  .show(message: str, level: str = "info", auto_hide: int = 0)
  # level: "success" | "info" | "warning" | "danger"
  # ألوان الـ level من status_colors() — تتغير مع الثيم
  # auto_hide: إخفاء بعد N ms (0 = لا إخفاء تلقائي)
  .hide_bar()

BaseWarningBar(on_fix=None, on_edit=None,
               fix_text="🗑️ حذف الناقص", edit_text="✏️ تعديل",
               show_dismiss=True)
# Signals: fix_clicked, edit_clicked, dismissed
  .show_message(message, fix_text=None, edit_text=None)
  .show_orphans(orphans: list, product_name: str, type_labels: dict = None)
  # يُخفي نفسه تلقائياً لو orphans فارغة
  .hide_warning()
  .set_fix_visible(v: bool)
  .set_edit_visible(v: bool)
```

---

### `ui/widgets/components/spinner.py`

```python
LoadingSpinner(text="جارٍ التحميل...", color=None, compact=False)
# color يقرأ من _C["accent"] افتراضياً
  .start()
  .stop()         # يُظهر "✓"
  .set_text(text)
  .is_running() -> bool

LoadingOverlay(parent: QWidget = None)
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
# ألوانه الافتراضية من _C — تتغير مع الثيم
  .set_badge(text, text_color=None, bg=None, border=None)
  .clear_badge()

StatCard(icon="", title="", value="─", color="#1565c0",
         bg=None, border=None, compact=False)
# bg/border من card_colors(color) افتراضياً
  .set_value(text: str)
  .set_color(color: str)
  .value_label() -> QLabel

StatusChip(icon="", label="", count=0, color="#6b7280",
           bg=None, border=None, compact=False)
  .set_count(count: int)
  .count() -> int

@dataclass
StatItem(label: str, color: str = "#1565c0", icon: str = "",
         value: str = "─", bg: Optional[str] = None,
         border: Optional[str] = None, bold_value: bool = True,
         compact: bool = False)

StatRow(items: list[StatItem], separator=True, compact=False, bg=None)
  .set_value(index: int, text: str, color: str = None)
  .set_value_by_label(label: str, text: str, color: str = None)
  .value_label(index: int) -> QLabel
  .reset_all()
  .update_all(values: dict)   # {label: text}
  .card(index: int) -> _StatCard | None

StatusCard(icon="", label="", value="─", color="#1565c0", sub="")
  .set_value(text: str)
  .value_label() -> QLabel

# Helpers
make_stat_row(*items: StatItem, separator=True, compact=False, bg=None) -> StatRow
stat_card_pair(label, color, icon="") -> tuple[QFrame, QLabel]
make_stat_card_simple(label, value="─", color="#1565c0", icon="") -> StatCard
make_status_chip(icon, label, count=0, color="#6b7280") -> StatusChip
```

---

## UI — Widgets Panels

### `ui/widgets/panels/crud_section.py`

> **تنبيه:** `CrudSection` أصبح alias لـ `BaseSection` للتوافق مع الكود القديم.
> الكود الجديد يستخدم `BaseSection` من `ui/widgets/base/section.py` مباشرة.

```python
from ui.widgets.panels.crud_section import CrudSection
# مطابق تماماً لـ BaseSection — نفس الـ API والـ Override
```

---

### `ui/widgets/panels/state.py`

```python
EmptyState(icon="📋", title="لا توجد بيانات", subtitle="",
           action_text="", style="dashed", color=None,
           min_height=80, expandable=False)
# style: "dashed" | "solid" | "plain"
# color افتراضي من _C['text_muted']
# expandable=True → يتمدد ليملأ المساحة
# يحفظ _lbl_title reference لتحديثه مباشرة عند تغيير اللغة بدون إعادة بناء
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

### `ui/widgets/panels/filter.py` — `FilterToolbar`

```python
FilterToolbar(conn=None, scope="all", show_category=True,
              show_date=False, placeholder="بحث...",
              show_presets=False)
# يستمع لـ bus.company_data_changed لإعادة تحميل التصنيفات + تحديث conn من company_state
# Signals: filter_changed

toolbar.name_query -> str
toolbar.category_id
toolbar.in_date_range(date_str: str) -> bool
toolbar.match(name, cat_id, date_str="") -> bool
toolbar.set_count(shown: int, total: int)
toolbar.reload(conn=None)
# يُحدّث self._conn لو conn محدد، ثم يُعيد تحميل التصنيفات
toolbar.reset()
# يمسح البحث + يُعيد الـ category لـ index 0 + يُعيد DateRangeFilter
```

---

### `ui/widgets/panels/detail_section.py`

```python
DetailSection(title="", cols=1, compact=False)
# ألوان الـ labels والـ values من _C — تتغير مع الثيم
  .add_row(label, value="─", color=None, bold=False, icon="") -> QLabel
  .add_separator()
  .set_data(data: dict, clear_missing: bool = False) -> dict[str, QLabel]
  # يرجع {label_text: value_QLabel} للتحديث المباشر
  # clear_missing=True: يُخفي الصفوف غير الموجودة في data الجديدة (بدون حذفها)
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

### `ui/widgets/panels/collapsible_card.py`

```python
CollapsibleCard(title="", expanded=True, accent=None)
# accent افتراضي من _C['accent']
# Signals: toggled(bool)
# المحتوى في: card.content_layout (QVBoxLayout)
  .set_expanded(expanded: bool)
  .is_expanded -> bool
```

---

### `ui/widgets/panels/card_grid.py`

```python
CardGrid(cols=4, spacing=10)
  .add_widget(widget: QWidget)
  .clear()   # يحذف كل الـ widgets بـ deleteLater

CardGrid.from_widgets(widgets: list, cols=4, spacing=10) -> CardGrid
```

---

### `ui/widgets/panels/data_table.py`

```python
DataTableWidget(columns: list, stretch_col=-1, col_widths=None,
                title="", add_text="", search_placeholder="🔍  بحث...",
                row_height=ROW_HEIGHT_LARGE, empty_icon="📋",
                empty_title="لا توجد بيانات")
# Signals: add_clicked, search_changed(str), row_selected(int)
# يفرق بين 3 حالات:
#   total=0         → empty state "لا توجد بيانات"
#   total>0,shown>0 → يعرض الجدول
#   total>0,shown=0 → empty state "لا توجد نتائج" (icon=🔍)

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

## UI — Widgets Mixins

### `ui/widgets/mixins/bus.py` — `BusConnectedMixin`

```python
def _connect_bus(data=True, company=False, theme=False, lang=False)
# data=True    → يربط company_data_changed (مع _on_company_data_changed)
#              + data_changed (مع _on_data_changed_guarded)
# company=True → يربط company_data_changed لـ _on_company_changed (بدون فلتر شركة)
# theme=True   → يربط theme_changed لـ _on_theme_changed
# lang=True    → يربط language_changed لـ _on_language_changed
# guard يمنع double-connect (عبر _bus_connected flag)

def _disconnect_bus()
# يفصل كل الـ signals المرتبطة (data + company + theme + lang)
# يُعيد ضبط _bus_connected = False
# يمسح _cached_company_id = None

# Data changed handlers:
def _on_company_data_changed(company_id: int)
# [P-04] مقارنة مباشرة بـ _cached_company_id بدل استدعاء is_same_company()
# المرة الأولى: يُضبط _cached_company_id من company_state
# لو شركة مختلفة → تجاهل + تحديث الـ cache
# لو نفس الشركة → _on_data_changed() + _refresh_guard
def _on_data_changed_guarded()
# يتجاهل لو _refresh_guard=True (يمنع data_changed المكرر)
def _on_data_changed()            # Override

# Company changed handler:
def _on_company_changed(company_id: int)
# تلقائياً يُحدث _cached_company_id بالشركة الجديدة
# Override لإعادة البناء عند تغيير الشركة

# Theme & language handlers:
def _on_theme_changed(theme_name: str)    # Override — يُعيد بناء الـ styles
def _on_language_changed(lang_code: str)  # Override — يُحدّث النصوص بـ tr()

def invalidate_company_cache()
# يُعيد ضبط _cached_company_id = None
# استدعه عند تغيير الشركة النشطة في الـ widget أو إعادة بنائه
```

**مثال كامل مع theme وlanguage:**
```python
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.i18n import tr
from ui.app_settings import _C

class MyPanel(QWidget, BusConnectedMixin):
    EMPTY_TITLE = "no_data"  # مفتاح tr()

    def __init__(self):
        super().__init__()
        self._connect_bus(data=True, theme=True, lang=True)

    def _on_data_changed(self):
        self.refresh()

    def _on_theme_changed(self, theme_name: str):
        self.setStyleSheet(f"background:{_C['bg_page']};")
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )

    def _on_language_changed(self, lang_code: str):
        self.btn_add.setText(tr("btn_add"))
        self._empty_state.set_title(tr(self.EMPTY_TITLE))
        self._header.search_bar.set_placeholder(tr("list_search_placeholder"))
```

---

### `ui/widgets/mixins/refresh.py` — `RefreshableMixin`

```python
def refresh()
# يستدعي _load_data() ثم _fill_ui() مع try/except
def _load_data() -> []    # Override — يجلب البيانات
def _fill_ui(data)        # Override — يملأ الـ UI
def _on_refresh_error(error: Exception)
# افتراضياً: print — Override لعرض رسالة للمستخدم
```

---

### `ui/widgets/mixins/edit.py` — `EditModeMixin`

```python
def init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode=None)
def enter_edit_mode(item_id: int, mode_text: str = "")
def exit_edit_mode(add_text: str = "")
def _set_add_state()   # يُظهر btn_add ويُخفي btn_save/btn_cancel
def is_edit_mode -> bool   # property — True لو _editing_id ≠ None
# _editing_id: int | None — class variable (لا instance)
```

---

### `ui/widgets/mixins/rebuild.py` — `RebuildMixin`

```python
# يفترض: self._root_layout (QVBoxLayout)
def _replace_widget(new_widget: QWidget)
# يُزيل القديم (hide + deleteLater) ثم يُضيف الجديد
def _schedule_rebuild(delay_ms: int = 0)
# QTimer.singleShot(delay_ms, self._rebuild)
def _rebuild()   # Override
```

---

### `ui/widgets/mixins/select.py` — `SelectionMixin`

```python
_id_col: int  = 0
_id_role: int = Qt.UserRole

def _selected_id(table=None) -> int | None
# يقرأ من item.data(UserRole) أولاً، ثم item.text() كـ fallback
def _selected_row(table=None) -> int
def _warn_no_selection(msg: str = "")
# عنوان من tr("warning") + رسالة افتراضية من tr("select_item_first")
def _require_selection(msg: str = "") -> int | None
# يستدعي _warn_no_selection لو مفيش اختيار
```

---

### `ui/widgets/mixins/validate.py` — `FormValidationMixin`

```python
def _warn(msg: str)
# msg_warning(self, tr("warning"), msg)

def validate_required(fields: list, parent=None) -> bool
# fields: [(widget, label), ...]
# QLineEdit: يتحقق من text().strip()
# QComboBox: يتحقق من currentData() ≠ None
# رسائل: tr("enter_field", label=label) | tr("select_field", label=label)

def validate_amount(spinbox, label="", min_val=0.01, parent=None) -> bool
# رسالة: tr("field_positive_enter", label=label)

def validate_positive(value: float, label="", parent=None) -> bool
# رسالة: tr("field_positive", label=label)
```

---

### `ui/widgets/mixins/service.py` — `ServiceMixin`

```python
# Properties كسولة — instance جديد في كل وصول (لأن conn ممكن يتغير)
# يفترض: self.conn موجود ويشير لـ DB connection صالح
._item_service     -> ItemService(self.conn)
._category_service -> CategoryService(self.conn)
._product_service  -> ProductService(self.conn)
._order_service    -> OrderService(self.conn)
._journal_service  -> JournalService(self.conn)
```

---

### `ui/widgets/mixins/shared_ops.py` — `SharedOpsMixin`

```python
# يفترض: self._published_names: set[str] و self._all_rows: list[dict]
def _check_shared_id(item_id) -> bool
def _extract_shared_id(item_id) -> int | None
def _is_published(row: dict) -> bool
def _find_row_by_id(item_id) -> dict | None

def _edit_shared_item(item_id, shared_type: str, parent=None)
def _edit_published_item(row: dict, shared_type: str, parent=None)
def _publish_item(row: dict, shared_type: str, item_data: dict, parent=None)
# كل العمليات تستخدم emit_company_data_changed() بعد نجاحها
```

---

## UI — Widgets Shared

### `ui/widgets/shared/list_panel_with_shared.py` — `SharedItemsListPanel`

قاعدة مشتركة للجداول التي تدعم العناصر المشتركة/المنشورة.
يرث من `BaseListPanel + SharedOpsMixin + LiveConnMixin`.
العمود 0 يُخفى تلقائياً (`setColumnHidden(0, True)`) ويُستخدم لحمل الـ ID.

**إعدادات الـ subclass:**
```python
SHARED_TYPE:      str  = "raw"
TABLE_COLS:       list = []      # تُحوَّل لـ COLUMNS تلقائياً
TABLE_TITLE:      str  = ""      # يُسند لـ LIST_TITLE تلقائياً
HAS_BULK_REPLACE: bool = False   # يُظهر زر "استبدال شامل"
SHOW_CATEGORY:    bool = True
CONNECT_BUS:      bool = True
# STRETCH_COL يُضبط على 1 تلقائياً
```

**Hooks المطلوبة (override إلزامي):**
```python
_fetch_local_rows() -> list[dict]
_fill_table_row(r: int, item: dict)
_edit_item(item_id: int)
_delete_item(item_id: int, item_name: str)
```

**Hooks الاختيارية:**
```python
_get_shared_rows(local_rows: list) -> list[dict]   # افتراضياً: []
_get_item_data_for_publish(row: dict) -> dict       # افتراضياً: {}
_bulk_replace_item(item_id: int, item_name: str)
_setup_column_widths(table: QTableWidget)
_on_edit_shared()
# افتراضياً: يستدعي _edit_shared_item من SharedOpsMixin
# override لتخصيص سلوك تعديل العنصر المشترك
```

**أزرار الهيدر (تُضاف تلقائياً):**
- `"🔄 استبدال شامل"` — يظهر فقط لو `HAS_BULK_REPLACE=True`
- `"✏️ تعديل المحدد"` — يستدعي `_edit_item`
- `"🗑️ حذف المحدد"` — يستدعي `_delete_item`
- `"🔗 تعديل المشترك"` — يستدعي `_on_edit_shared`
- `"📤 نشر كمشترك"` — يستدعي `_publish_item` من `SharedOpsMixin`

**التلوين التلقائي للصفوف:**
```python
# العناصر المشتركة (row["_is_shared"] = True):
#   fg = SHARED_COLOR, bg = SHARED_BG
# العناصر المنشورة (row["_is_published"] = True أو name في _published_names):
#   fg = PUBLISHED_COLOR, bg = PUBLISHED_BG
# من: ui/tabs/costing/shared/_utils.py
```

**مساعدات:**
```python
panel._selected_row_data() -> tuple[int | None, str]   # (item_id, item_name)
panel._get_current_row_dict() -> dict | None
panel._live_conn()   # يستدعي get_connection() من db.shared.connection
```

---

## UI — Widgets Utils

### `ui/widgets/utils/signals.py`

```python
@contextmanager
blocked_signals(*widgets)
# يوقف signals لواحد أو أكثر من الـ widgets ثم يعيدها تلقائياً
# مثال: with blocked_signals(self.cmb_a, self.cmb_b): ...
```

---

### `ui/widgets/utils/searchable_combo.py`

```python
SearchableCombo()
# _ComboFilterProxy(QSortFilterProxyModel):
#   - للنص الفارغ: setFilterFixedString("") مباشرة (أسرع)
#   - للنص غير الفارغ: invalidateFilter() لاستدعاء filterAcceptsRow المخصصة
#   - حارس التغيير: لو النص لم يتغير → لا invalidation
#   - الـ separators دائماً مرئية
#   - الـ orphans دائماً مرئية
# debounce داخلي 120ms
# Signals: item_selected(data)
  .populate(items: list)
  # items: [(display_text, user_data, is_separator), ...]
  # الـ separators المتتالية بدون عناصر بينها تُتجاهل (pending_sep pattern)
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

### `ui/widgets/utils/tooltip.py`

```python
apply_table_tooltips(table: QTableWidget, cols: list[int] | None = None)
apply_tree_tooltips(tree: QTreeWidget, item=None, cols=None, recursive=True)
```

---

### `ui/widgets/utils/flow_layout.py`

```python
FlowLayout(parent=None, h_spacing=6, v_spacing=4)
# hasHeightForWidth() = True — يدعم dynamic height
```

---

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

### `ui/widgets/utils/splitter.py`

```python
fit_list_panel(splitter, list_index, table, min_w=280, max_w=620, extra_pad=24) -> int
fit_list_panel_delayed(splitter, list_index, table, delay_ms=0, min_w=280, max_w=620)

SmartSplitter(orientation=Qt.Horizontal)
  .set_list_widget(widget, list_table, list_index=0, min_w=280, max_w=620)
  .fit_now() -> int
  .fit_delayed(delay_ms=50)

SplitterScrollGuard(splitter, table, table_index=0, extra_pad=20, parent=None)
# يمنع الـ splitter من التوسع أكثر من عرض الجدول لما الـ horizontal scrollbar مش ظاهر
  .refresh()

_SplitterScrollGuard = SplitterScrollGuard   # alias
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

## UI — Widgets Dialogs

### `ui/widgets/dialogs/shell.py` — `DialogShell`

```python
DialogShell(parent=None, title="", icon="📋", subtitle="",
            accent=None, min_width=380, min_height=0)
# RTL + modal تلقائي
# هيدر: gradient من accent إلى accent + "cc" (~80% opacity)
# accent_transparent = accent + "cc" — صريح ولا لبس
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
# يستخدم make_btn من components/button — يدعم الثيم تلقائياً
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
# ألوان الأيقونات من _C تلقائياً
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
# danger=True, icon="🗑️"

confirm_action(parent, title, message, icon="❓", confirm_text="",
               cancel_text="", danger=False, accent=None) -> bool

confirm_save(parent, item_name: str = "", extra_msg: str = "") -> bool
# رسالة: tr("save_confirm_msg", name=item_name)
# accent=_C["success"]
```

---

## UI — Widgets Forms

### `ui/widgets/forms/inputs.py`

```python
AmountSpinBox(max_=999_999_999, dec=2, min_=0, height=32, currency="")
# يغير لون الـ spinbox تلقائياً لو القيمة > 0 (positive=True → أخضر)
# ألوان من _C عبر spinbox_style()

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
# يشترك في bus.language_changed لتحديث نصوص الأزرار تلقائياً عبر _on_language_changed
# Signals: add_clicked, save_clicked, cancel_clicked
  .btn_add, .btn_save, .btn_cancel -> QPushButton
  .lbl_mode -> QLabel
  .set_mode_text(text: str)

ModeLabel   # مُستورد من components/label.py — المصدر الوحيد
```

---

## UI — Widgets Combos

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

### `ui/widgets/helpers/color_picker.py`

```python
ColorPickerWidget(default="#607d8b", btn_text="اختر لون")
# Signals: color_changed(str) — hex string
  .current_color() -> str
  .set_color(color: str)
```

---

## UI — Widgets Theme

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

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48
```

---

### `ui/widgets/core/colors.py`

```python
card_colors(color: str) -> tuple[str, str]
# (bg, border) من CARD_PALETTE — fallback: ("#f5f5f5", "#e0e0e0")

status_colors(level: str) -> dict[str, str]
# يبني الـ map من _C في كل استدعاء — لا dict ثابت
# هذا يضمن التزامن التلقائي مع تغييرات الثيم
# level: "success" | "warning" | "danger" | "info" | "neutral" | "primary" | "purple" | "orange"
# يرجع: {"fg": str, "bg": str, "border": str}
# purple/orange: من _C.get() مع fallback آمن

waste_level(pct: float) -> str   # "high" | "medium" | "low" | "zero"
waste_colors(pct: float) -> tuple[str, str]

WASTE_COLORS = {"high": ("#ffcdd2","#e53935"), "medium": ("#ffe0b2","#f57c00"),
                "low": ("#fff8e1","#ffe082")}
WASTE_ZERO_BG = "#f5f5f5" | WASTE_ZERO_BORDER = "#e0e0e0"
WASTE_ZERO_COLOR = "#999" | WASTE_TEXT_COLOR = "#e65100"
```

---

### `ui/widgets/core/events.py`

```python
get_active_company_id() -> int | None
emit_company_data_changed()
# يُطلق bus.company_data_changed(cid) لو توجد شركة نشطة
# وإلا يُطلق bus.data_changed()
is_same_company(company_id: int) -> bool
```

---

### `ui/widgets/core/conn.py`

```python
# ── LiveConnMixin ──
# _conn_attr: str = "conn" — اسم الـ attribute الذي يحمل الـ connection
# ⚠️ لو subclass يستخدم self.erp_conn → حدد _conn_attr = "erp_conn"
# _conn_cache: instance variable (object.__setattr__) — لا class variable مشترك

  ._live_conn() -> Connection
  # 1. self.__dict__["_conn_cache"] لو سليم
  # 2. self.{_conn_attr} لو سليم
  # 3. company_state.get_erp_conn() كـ fallback
  # 4. RuntimeError واضحة لو كل شيء فشل
  ._invalidate_conn_cache()
  ._live_acc_conn() -> Connection

# ── SafeConnMixin ──
  ._init_safe_conn(conn, db_name="accounting")
  ._get_safe_conn() -> Connection      # RuntimeError لو فشل
  ._get_company_id() -> int | None
  ._should_respond_to_company(company_id, stored_attr="_company_id") -> bool

# ── DualConnMixin(SafeConnMixin) ──
  ._init_dual_conn(acc_conn, erp_conn, acc_db="accounting")
  ._get_erp_conn() -> Connection       # RuntimeError لو فشل
  ._on_dual_company_event(company_id) -> bool
```

---

### `ui/widgets/core/guard.py`

```python
@requires_company
def my_method(self): ...
# رسالة افتراضية: tr("select_company")

@requires_company(return_value=[])
def _load_rows(self) -> list: ...

@requires_company(return_value_factory=list)
def _load_rows(self) -> list: ...

@requires_company(message="رسالة مخصصة")
def my_method(self): ...

# يعرض التحذير عبر (بالترتيب):
# show_warning() → _warn() → _notif.show() → debug log
```

---

## UI — Managers

### `ui/widgets/managers/category.py`

```python
CategoryManager(conn, scope="all")
# يستمع لـ bus.data_changed + bus.language_changed
# يستخدم _live_conn() مرة واحدة لكل action — يُمررها للدوال الفرعية
# عناوين الأعمدة والأزرار من tr()
# يشترك في bus.language_changed لتحديث النصوص تلقائياً

CategoryForm(conn, scope, tree_widget)
  .load_for_edit(cat_id: int)
# يشترك في bus.language_changed لتحديث نصوص الـ groupbox والأزرار
# _refresh_parent_combo(conn=None, exclude_id=None)
```

---

## UI — Main

### `ui/main_window.py` — `MainWindow`

```python
MainWindow(app: QApplication)
# resize: WINDOW_DEFAULT_W × 820
# setLayoutDirection: Qt.RightToLeft
# setMinimumSize: (SIDEBAR_COLLAPSED_WIDTH + 400, 500)

# index_map:
# "costing":    1 | "pricing":    2 | "accounting": 3
# "inventory":  4 | "design":     5 | "orders":     6

# سلوكيات:
# "settings"     → SettingsDialog (لا يغير الـ stack index)
# "shared_items" → SharedItemsManagerDialog
# تغيير الشركة  → AppState.invalidate() + _refresh_tabs() + bus.company_data_changed
```

---

### `ui/settings_dialog.py` — `SettingsDialog`

```python
SettingsDialog(app: QApplication, parent=None)
# تبويبات: الخط | المظهر | اللغة | الوحدات | GIMP

# حفظ (_save):
#   - حجم الخط: set_font_size() + apply_font() + bus.font_changed
#   - الثيم: theme_manager.set_theme() → يُطلق bus.theme_changed تلقائياً
#   - اللغة: i18n_manager.set_language() + app.setLayoutDirection() + bus.language_changed
#   - GIMP path: set_setting() في erp DB

# _get_settings_conn_and_status() -> tuple[conn, has_company]
# يقرأ company_state.is_ready مرة واحدة فقط — يُعيد (conn, has_active_company)
```

---

## UI — ComponentRow

### `ui/widgets/components/component_row/widget.py` — `ComponentRow`

```python
ComponentRow(catalog_fn, child_type="raw", child_id=None,
             qty=1.0, waste_pct=0.0, raw_total_qty=None,
             show_total_qty=False, variant_id=None,
             machine_op_row_id=None)
# Signals: removed(QWidget)
# يستخدم weakref.ref(self) في bus slot — يمنع dangling reference
# _bus_slot محفوظ كـ instance variable ويُفصل في closeEvent()
# _get_conn(): بدون SELECT 1 overhead — يثق في الـ cache مباشرة

  .get_values() -> tuple | None
  # (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
  .get_waste_pct() -> float
  .get_variant_id() -> int | None
  .get_machine_op_row_id() -> int | None
  .is_orphan() -> bool
  .set_orphan_name(name: str | None)
  .refresh_catalog(_new_catalog: dict = None)
  .expose_load_op_rows(op_id, selected_row_id=None)
  # synchronous — يمنع QTimer من إعادة التحميل

  ._refresh_cost_label()
  # يُحدّث lbl_variant_cost من الـ catalog الجديد بعد تغيير سعر الخامة
  # يُستدعى تلقائياً من _on_catalog_changed بعد _refresh_items()
  # لا يفعل شيئاً لو: النوع ليس "raw"، أو orphan، أو لا يوجد child_id

  ._disconnect_bus()
  # يفصل _bus_slot من bus.data_changed صريحاً
  # يُستدعى تلقائياً من closeEvent()

  ._is_widget_deleted(*widgets) -> bool
  # مشترك بين OpRowsMixin و VariantsMixin — sip.isdeleted()
```

**Attributes:** `cmb_type`, `_item_combo`, `cmb_variant`, `lbl_variant_cost`, `qty_edit`, `waste_spin`, `lbl_waste`, `total_qty_edit`, `lbl_total_qty`, `cmb_op_row`, `lbl_op_row_cost`, `_sub_row_widget`, `cmb_item` (alias لـ `_item_combo.cmb`)

---

### `ui/widgets/components/component_row/ui.py`

```python
build_row_ui(widget, child_type, child_id, qty, raw_total_qty,
             waste_pct, variant_id, machine_op_row_id, show_total_qty)
# جميع الألوان من _C و status_colors() — لا hardcoded

update_waste_style(widget, val: float)
# يستخدم waste_colors() و status_colors() من core/colors — لا hardcoded

COMPONENT_TYPES = [
    ("raw","🧱 خامة"), ("semi","🔧 نصف مصنع"),
    ("labor_op","👷 عملية عمالة"), ("machine_op","⚙️ عملية تشغيل"),
]
STYLE_NORMAL = ""
STYLE_ORPHAN = ...   # يُبنى من status_colors("warning") — يتغير مع الثيم
```

---

### `ui/widgets/components/component_row/op_rows.py` — `OpRowsMixin`

```python
.expose_load_op_rows(op_id, selected_row_id=None)
._ensure_machine_op_rows()
._hide_op_rows()
._load_op_rows(op_id, selected_row_id=None)
# أولوية: selected_row_id → _init_machine_op_row_id → _pinned_op_row_id → أول صف
._on_op_row_changed(_index=0)
._update_op_row_cost_label()
._is_op_row_deleted() -> bool
```

---

### `ui/widgets/components/component_row/variants.py` — `VariantsMixin`

```python
._load_variants(item_id, selected_variant_id=None)
._hide_variants()
._on_variant_changed()
._update_variant_cost_label()
._is_variant_deleted() -> bool
```

---

## أمثلة

### قسم CRUD كامل مع دعم الثيم واللغة

```python
from ui.widgets.base.section import BaseSection
from ui.widgets.core.i18n import tr
from ui.app_settings import _C

class MySection(BaseSection):
    LIST_MIN_W  = 300
    CONNECT_BUS = True

    def _create_list(self):
        return MyListPanel(self.conn)

    def _create_detail(self):
        return MyDetailPanel(self.conn)

    def _connect_signals(self):
        self._list.item_selected.connect(self._detail.load_item)
```

---

### لوحة قائمة مع دعم الثيم واللغة

```python
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.core.i18n import tr
from ui.widgets.tables.items import make_item

class MyListPanel(BaseListPanel):
    COLUMNS     = [tr("name"), tr("price")]
    STRETCH_COL = 0
    EMPTY_ICON  = "📦"
    EMPTY_TITLE = "no_data"    # مفتاح tr() — يُترجم في _update_empty_state_title
    LIST_TITLE  = tr("raw_materials")
    ADD_TEXT    = tr("btn_add")
    CONNECT_BUS = True

    def _load_rows(self):
        return fetch_items_by_type(self.conn, "raw")

    def _fill_row(self, table, r, row):
        table.setItem(r, 0, make_item(row["name"], row["id"]))
        table.setItem(r, 1, make_item(f"{row['price']:,.2f}"))

    def _on_theme_changed(self, theme_name: str):
        super()._on_theme_changed(theme_name)
        # تحديثات مخصصة إضافية هنا

    def _on_language_changed(self, lang_code: str):
        super()._on_language_changed(lang_code)
        # تحديثات مخصصة إضافية هنا
```

---

### جدول مع دعم العناصر المشتركة

```python
from ui.widgets.shared.list_panel_with_shared import SharedItemsListPanel
from ui.widgets.tables.items import make_item
from ui.widgets.core.i18n import tr

class RawMaterialsPanel(SharedItemsListPanel):
    SHARED_TYPE      = "raw"
    TABLE_COLS       = ["#", tr("name"), tr("price"), tr("category")]
    TABLE_TITLE      = tr("raw_materials")
    HAS_BULK_REPLACE = True

    def _fetch_local_rows(self):
        return fetch_items_by_type(self.conn, "raw")

    def _fill_table_row(self, r, item):
        self.table.setItem(r, 0, make_item(str(item["id"]), item["id"]))
        self.table.setItem(r, 1, make_item(item["name"]))
        self.table.setItem(r, 2, make_item(f"{item['price']:,.2f}"))
        self.table.setItem(r, 3, make_item(item.get("category_name", "─")))

    def _edit_item(self, item_id): ...
    def _delete_item(self, item_id, item_name): ...
```

---

### bus events — الاستخدام الصحيح

```python
# ✅ الصح — مقيّد بالشركة
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()

# ❌ تجنّب — للتوافق القديم فقط
from ui.events import bus
bus.data_changed.emit()
```