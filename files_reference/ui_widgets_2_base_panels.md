# دليل الكود — UI / Widgets (2): Base Panels

> الجزء الثاني — القواعد المشتركة لكل لوحات القوائم والتفاصيل والأقسام والفورمات.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [BaseListPanel](#baselistpanel) | `base/list_panel` |
| [BaseDetailPanel](#basedetailpanel) | `base/detail_panel` |
| [BaseSection / CrudSection](#basesection--crudsection) | `base/section`, `panels/crud_section` |
| [TabSectionBase](#tabsectionbase) | `base/tab_section` |
| [BaseCrudForm](#basecrudform) | `base/crud_form` |

---

## BaseListPanel

### `ui/widgets/base/list_panel.py` — `BaseListPanel`

**Override المطلوب:**
```python
COLUMNS: list          # أسماء الأعمدة
STRETCH_COL: int       # عمود يتمدد (-1 = آخر عمود)
EMPTY_ICON: str
EMPTY_TITLE: str       # مفتاح tr() أو نص مباشر — يُترجم تلقائياً عند تغيير اللغة
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
  - يُعيد بناء styles الـ pagination bar والـ status bar

- `_on_language_changed(lang_code)`:
  - يُحدّث placeholder البحث عبر `_header.search_bar.set_placeholder()`
  - يُحدّث نص empty state عبر `_empty_state.set_title(_tr_safe(EMPTY_TITLE))`
  - يُحدّث نصوص أزرار الـ pagination

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
panel.reset_pagination()
panel.total_rows -> int
panel.shown_rows -> int
panel.table -> QTableWidget
```

**مثال:**
```python
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.core.i18n import tr
from ui.widgets.tables.items import make_item
from ui.app_settings import _C

class MyListPanel(BaseListPanel):
    COLUMNS     = [tr("name"), tr("price")]
    STRETCH_COL = 0
    EMPTY_ICON  = "📦"
    EMPTY_TITLE = "no_data"    # مفتاح tr() — يُترجم تلقائياً عند تغيير اللغة
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
        # إعادة تطبيق أي styles إضافية خاصة بالـ subclass

    def _on_language_changed(self, lang_code: str):
        super()._on_language_changed(lang_code)
        # تحديث أي نصوص إضافية خاصة بالـ subclass
```

---

## BaseDetailPanel

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
HEADER_BG: str = None
MIN_CONTENT_W: int = 500
CONNECT_BUS: bool = False

_build_header_cards()
_build_header_buttons()
_fill_header(data: dict)           # افتراضياً: self._hdr.set_title(data["name"])
_on_data_changed()                 # افتراضياً: load_item(self._item_id)

_on_theme_changed(theme_name: str)
# يُعيد تطبيق bg_page على الـ panel وscroll area والـ inner widgets

_on_language_changed(lang_code: str)
# يُحدّث نص _empty عبر _empty.set_title(_tr_safe(EMPTY_TITLE))
```

**ملاحظة (theme/lang):** عند `CONNECT_BUS=True` يشترك تلقائياً في `theme_changed` و `language_changed` إضافةً لـ `data_changed`.

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

## BaseSection / CrudSection

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
LAYOUT_REVERSED: bool = False
FORM_POSITION: str = "none"
# "none"   → لا فورم
# "bottom" → فورم أسفل لوحة القائمة
# "left"   → list فقط في الـ splitter
SPLITTER_RATIO: tuple = (1, 2)

_create_form() -> QWidget | None
_connect_signals()
# افتراضياً: list.item_selected → detail.load_item
_on_data_changed()
_on_item_selected(item_id: int)
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

**مثال:**
```python
from ui.widgets.base.section import BaseSection

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

## TabSectionBase

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
```

---

## BaseCrudForm

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
# إضافة widgets إضافية بعد FormGroup
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