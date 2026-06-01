# دليل الكود — UI / Widgets (2): Base Panels

> الجزء الثاني — القواعد المشتركة لكل لوحات القوائم والتفاصيل والأقسام والفورمات.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [BaseListPanel](#baselistpanel) | `base/list_panel.py` |
| [BaseDetailPanel](#basedetailpanel) | `base/detail_panel.py` |
| [BaseSection](#basesection) | `base/section.py` |
| [CrudSection (alias)](#crudsection-alias) | `panels/crud_section.py` |
| [TabSectionBase](#tabsectionbase) | `base/tab_section.py` |
| [BaseCrudForm](#basecrudform) | `base/crud_form.py` |

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
# [E-02] اسم الـ key في dict البيانات الذي يحتوي التاريخ
CONNECT_BUS: bool = True

# Sort settings
SORTABLE: bool = False
COL_KEYS: list = []
SORT_DEFAULT_COL: int = -1
SORT_DEFAULT_ASC: bool = True

# Pagination settings
PAGINATE: bool = False
PAGE_SIZE: int = 200

_match_filter(row, query) -> bool      # افتراضياً: يبحث في row["name"]
_match_category(row, cat_id) -> bool   # افتراضياً: يقارن row["category_id"]
_match_date(row) -> bool               # [E-02] يُستدعى فقط لو SHOW_DATE=True
_on_add_clicked()
_on_data_changed()                     # افتراضياً: self.refresh()
_build_extra_header_actions(header: ListHeader)
_sort_key(col, row)                    # يُستدعى فقط لو SORTABLE=True
```

**Bus (عند `CONNECT_BUS=True`):**
يشترك في `company_data_changed` + `data_changed` + `theme_changed` + `language_changed`.

```python
def _on_theme_changed(theme_name: str):
    # يُعيد تطبيق background على الـ widget الرئيسي (من _C['bg_input'])
    # يُعيد تطبيق stylesheet على _empty_state
    # يُعيد بناء styles الـ pagination bar والـ status bar
    # ⚠️ عند override: استدعي super()._on_theme_changed(theme_name) أولاً

def _on_language_changed(lang_code: str):
    # يُحدّث placeholder البحث عبر _header.search_bar.set_placeholder()
    # يُحدّث نص empty state عبر _empty_state.set_title(_tr_safe(EMPTY_TITLE))
    # يُحدّث نصوص أزرار الـ pagination
    # ⚠️ عند override: استدعي super()._on_language_changed(lang_code) أولاً
```

**[إصلاح 5] refresh() المحدّث:**
يُوقف الـ `_timer` قبل `reload()` لمنع تشغيل `_apply_filter` مرتين عند إعادة ملء الـ categories combo.

**API:**
```python
panel.refresh()
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
from ui.widgets.tables.tables import make_item

class MyListPanel(BaseListPanel):
    COLUMNS     = [tr("name"), tr("price")]
    STRETCH_COL = 0
    EMPTY_ICON  = "📦"
    EMPTY_TITLE = "no_data"    # مفتاح tr() — يُترجم تلقائياً
    CONNECT_BUS = True

    def _load_rows(self):
        return fetch_items_by_type(self.conn, "raw")

    def _fill_row(self, table, r, row):
        table.setItem(r, 0, make_item(row["name"], row["id"]))
        table.setItem(r, 1, make_item(f"{row['price']:,.2f}"))
```

---

## BaseDetailPanel

### `ui/widgets/base/detail_panel.py` — `BaseDetailPanel`

**Override المطلوب:**
```python
EMPTY_ICON: str = "📋"
EMPTY_TITLE: str = "اختر عنصراً من القائمة"
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
# يُعيد تطبيق bg_page + scroll_style()
# ⚠️ عند override: استدعي super()._on_theme_changed(theme_name) أولاً

_on_language_changed(lang_code: str)
# يُحدّث نص _empty عبر _empty.set_title(_tr_safe(EMPTY_TITLE))
# ⚠️ عند override: استدعي super()._on_language_changed(lang_code) أولاً
```

**Signals:** `saved = pyqtSignal(int)` | `deleted = pyqtSignal()`

**API:**
```python
panel.load_item(item_id: int)
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

## BaseSection

### `ui/widgets/base/section.py` — `BaseSection`

> **[T-05] توحيد BaseSection و CrudSection:**
> `BaseSection` استوعبت كل خصائص `CrudSection`.
> `CrudSection` في `panels/crud_section.py` أصبحت alias للتوافق فقط.

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

# [T-05] من CrudSection:
FORM_POSITION: str = "none"
# "none"   → لا فورم (الافتراضي)
# "bottom" → فورم أسفل لوحة القائمة
# "left"   → list panel فقط (الفورم خارج الـ splitter)

SPLITTER_RATIO: tuple = (1, 2)

_create_form() -> QWidget | None   # [T-05] افتراضياً: None
_connect_signals()
# افتراضياً: list.item_selected → detail.load_item
_on_data_changed()     # افتراضياً: self.refresh()
_on_item_selected(item_id: int)
# افتراضياً: detail.load_item(item_id)
```

**API:**
```python
section.refresh()
section.clear_detail()
section.select_item(item_id)
section.list_panel -> QWidget
section.detail_panel -> QWidget
section.form_panel -> QWidget | None   # [T-05]
```

---

## CrudSection (alias)

### `ui/widgets/panels/crud_section.py`

> **تنبيه:** `CrudSection` أصبح alias لـ `BaseSection` للتوافق مع الكود القديم.

```python
from ui.widgets.panels.crud_section import CrudSection
# مطابق تماماً لـ BaseSection
```

---

## TabSectionBase

### `ui/widgets/base/tab_section.py` — `TabSectionBase`

```python
TabSectionBase(conn_fn=None, parent=None)
# conn_fn: callable يُعيد connection — افتراضياً get_connection() من db.shared.connection

def _build_tabs(self, tabs: QTabWidget)  # Override إلزامي

# Properties:
section.conn -> ProtectedConnection
section.current_tab -> QWidget | None

# closeEvent:
# [إصلاح 18] يُغلق conn فقط لو _is_owned_connection() = True
# [FIX] يستخدم get_erp_conn() (public API) بدل _get_conn("erp") (private)
```

---

## BaseCrudForm

### `ui/widgets/base/crud_form.py` — `BaseCrudForm`

قاعدة مشتركة لكل فورمات CRUD. يرث من `QWidget + EditModeMixin + LiveConnMixin`.
**[FIX]** يستخدم `emit_company_data_changed()` بدل `bus.data_changed.emit()` بعد كل إضافة/تعديل.

**Signals:** `saved = pyqtSignal(int)`

**إعدادات الـ subclass:**
```python
FORM_TITLE: str = "بيانات العنصر"
ADD_TEXT:   str = "➕  إضافة"
SAVE_TEXT:  str = "💾  حفظ التعديل"
```

**Hooks المطلوبة (override إلزامي):**
```python
_build_fields(group: FormGroup)
_collect() -> dict | None              # None عند فشل التحقق
_do_insert(data: dict) -> int
_do_update(item_id: int, data: dict)
_do_load(item_id: int) -> dict | None
_fill_fields(data: dict)
_reset_fields()
```

**Hook اختياري:**
```python
_build_extra(root_layout: QVBoxLayout)
```

**API:**
```python
form.load_for_edit(item_id: int)
form.btn_add    -> QPushButton
form.btn_save   -> QPushButton
form.btn_cancel -> QPushButton
form.lbl_mode   -> QLabel
```