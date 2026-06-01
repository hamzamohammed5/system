# دليل الكود — UI / Widgets (2): Base Panels

> `ui/widgets/base/` — القواعد المشتركة لكل لوحات القوائم والتفاصيل والأقسام والفورمات.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [BaseListPanel](#baselistpanel) | `base/list_panel.py` |
| [BaseDetailPanel](#basedetailpanel) | `base/detail_panel.py` |
| [BaseSection](#basesection) | `base/section.py` |
| [TabSectionBase](#tabsectionbase) | `base/tab_section.py` |
| [BaseCrudForm](#basecrudform) | `base/crud_form.py` |

---

## BaseListPanel

### `ui/widgets/base/list_panel.py`

**Override المطلوب:**
```python
COLUMNS: list          # أسماء الأعمدة
STRETCH_COL: int       # عمود يتمدد (-1 = آخر عمود)
EMPTY_ICON: str
EMPTY_TITLE: str       # مفتاح tr() أو نص — يُترجم تلقائياً عند تغيير اللغة
_load_rows() -> list   # يرجع list[dict]
_fill_row(table, row_index, row_data)
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
CONNECT_BUS: bool = True

# Sort settings
SORTABLE: bool = False
COL_KEYS: list = []
SORT_DEFAULT_COL: int = -1
SORT_DEFAULT_ASC: bool = True

# Pagination settings
PAGINATE: bool = False
PAGE_SIZE: int = 200

_match_filter(row, query) -> bool
_match_category(row, cat_id) -> bool
_match_date(row) -> bool               # يُستدعى فقط لو SHOW_DATE=True
_on_add_clicked()
_on_data_changed()                     # افتراضياً: self.refresh()
_build_extra_header_actions(header: ListHeader)
_sort_key(col, row)                    # يُستدعى فقط لو SORTABLE=True
```

**[إصلاح 5] `refresh()` المحدّث:**
```python
def refresh(self):
    self._all_rows = self._load_rows()
    if self._filter_toolbar and self.conn:
        self._timer.stop()    # ← يمنع double apply_filter
        self._filter_toolbar.reload(self.conn)
    self._apply_filter()
```

**بناء الـ Header:**
- لو `SHOW_CATEGORY` أو `SHOW_DATE` = True → يستخدم `FilterToolbar` بدل search في `ListHeader`
- لو كلاهما False → يستخدم `ListHeader` مع search مدمج
- `inp_search` يُضبط على `toolbar.inp_search` عند وجود FilterToolbar

**Pagination bar:**
- يظهر فقط لو `PAGINATE=True` و `total > PAGE_SIZE`
- يعرض "يعرض {shown} من {total}" + زر "تحميل إضافي" + زر "عرض الكل"
- `_on_load_more()` يُحمّل `PAGE_SIZE` إضافياً
- `_on_show_all()` يُحمّل كل ما تبقى

**Select مع Pagination:**
```python
panel.select_item(item_id)
# يبحث في الصفوف الظاهرة أولاً
# لو PAGINATE=True ولم يجد → يبحث في _page_rows
# يُحمّل الصفوف اللازمة حتى يصل للـ item
```

**Bus (عند `CONNECT_BUS=True`):**
يشترك في `company_data_changed` + `data_changed` + `theme_changed` + `language_changed`.

```python
def _on_theme_changed(theme_name):
    # يُعيد تطبيق: background + pagination styles + status bar style
    # يستدعي _rebuild_pagination_styles() + _rebuild_status_style()

def _on_language_changed(lang_code):
    # يُحدّث: placeholder البحث + empty state title + نصوص pagination
    # يستدعي: _update_empty_state_title() + _update_pagination_texts()
```

**API كامل:**
```python
panel.refresh()
panel.select_item(item_id: int)
panel.selected_id() -> int | None
panel.current_id -> int | None     # property — alias لـ selected_id()
panel.add_header_action(text, callback=None, style="normal") -> QPushButton
panel.set_add_enabled(enabled: bool)
panel.set_sort(col: int, ascending: bool = True)
panel.clear_sort()
panel.reset_pagination()
panel.total_rows -> int    # = len(self._page_rows)
panel.shown_rows -> int    # = self._shown_count
panel.table -> QTableWidget
```

---

## BaseDetailPanel

### `ui/widgets/base/detail_panel.py`

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
HEADER_BG: str = None          # افتراضياً: _C['bg_surface']
MIN_CONTENT_W: int = 500
CONNECT_BUS: bool = False

_build_header_cards()          # يُستدعى في __init__ قبل بناء الـ content
_build_header_buttons()        # يُستدعى في __init__ قبل بناء الـ content
_fill_header(data: dict)       # افتراضياً: self._hdr.set_title(data.get("name", "─"))
_on_data_changed()             # افتراضياً: load_item(self._item_id)
_on_theme_changed(theme_name)
_on_language_changed(lang_code)
```

**Signals:** `saved = pyqtSignal(int)` | `deleted = pyqtSignal()`

**`load_item(item_id)` — المنطق الفعلي:**
```python
# يُسند self._item_id = item_id
# يستدعي _load_data(item_id) مع try/except
# لو exception → show_error()
# لو data is None → _set_mode(has_data=False)
# لو data موجود → _set_mode(True) + _fill_header() + _fill_data()
# يحفظ dict(data) في self._item_data
```

**`_set_mode(has_data)` — يتحكم في الرؤية:**
```python
# has_data=True  → scroll مرئي + header مرئي + empty مخفي
# has_data=False → scroll مخفي + header مخفي + empty مرئي
```

**`_on_theme_changed`:**
```python
# يُعيد تطبيق bg_page على: self + scroll + inner widget + children
# يُعيد تطبيق scroll_style() على self._scroll
```

**API:**
```python
panel.load_item(item_id: int)
panel.clear()                  # يُعيد ضبط _item_id/_item_data + يُخفي notif
panel.show_success(msg, auto_hide=3000)
panel.show_error(msg)          # danger level — لا auto_hide
panel.show_warning(msg, auto_hide=0)
panel.show_info(msg, auto_hide=0)
panel.item_id -> int | None
panel.item_data -> dict | None
panel.header -> DetailHeader
panel.content_layout -> QVBoxLayout
```

---

## BaseSection

### `ui/widgets/base/section.py`

**ملاحظة:** `BaseSection` تجمع سلوك `CrudSection` القديم — استخدمها مباشرة.

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
# "none"   → لا فورم (يرجع self._list مباشرة)
# "bottom" → فورم أسفل لوحة القائمة (container: VBox(list + form))
# "left"   → يرجع self._list (الفورم خارج الـ splitter)

SPLITTER_RATIO: tuple = (1, 2)  # (list_stretch, detail_stretch)

_create_form() -> QWidget | None   # افتراضياً: None
_connect_signals()
# افتراضياً: list.item_selected → detail.load_item (لو موجودان)
_on_data_changed()     # افتراضياً: self.refresh()
_on_item_selected(item_id: int)
# افتراضياً: يستدعي detail.load_item(item_id) لو موجود
```

**`_build_left_panel()` — منطق FORM_POSITION:**
```python
# form = self._create_form()
# لو form is None أو FORM_POSITION == "none":
#   self._form = None → يرجع self._list
# لو FORM_POSITION == "bottom":
#   container = QWidget → VBoxLayout(list stretch=1, form) → self._form = form
# لو FORM_POSITION == "left" أو غيره:
#   self._form = form → يرجع self._list
```

**`_apply_sizes()` — يُشغَّل بـ QTimer.singleShot(50):**
```python
# total = splitter.width() أو self.width()
# لو total <= 0 → يجدول نفسه مرة أخرى بعد 100ms
# list_w = max(LIST_MIN_W, min(LIST_MIN_W + 60, LIST_MAX_W))
# detail_w = max(DETAIL_MIN_W, total - list_w - handle)
# يُطبّق setSizes حسب LAYOUT_REVERSED
```

**API:**
```python
section.refresh()            # يستدعي list.refresh() + _apply_sizes() بعد 80ms
section.clear_detail()       # يستدعي detail.clear() لو موجود
section.select_item(item_id) # يستدعي list.select_item() + _on_item_selected()
section.list_panel -> QWidget
section.detail_panel -> QWidget
section.form_panel -> QWidget | None
```

---

## TabSectionBase

### `ui/widgets/base/tab_section.py`

```python
TabSectionBase(conn_fn=None, parent=None)
# conn_fn: callable يُعيد connection — افتراضياً get_connection()
# يبني QTabWidget مع tab_style() ويستدعي _build_tabs()

def _build_tabs(self, tabs: QTabWidget)  # Override إلزامي
```

**`_is_owned_connection(conn)` — دالة مستقلة (ليست method):**
```python
# يرجع False لو conn is None
# يجلب company_state.get_erp_conn() — يستخدم get_erp_conn() (public API)
# لو conn is shared → False (لا تُغلق)
# لو conn مختلف → True (owned → يُغلق)
# عند أي exception → False (الاختيار الآمن)
```

**`closeEvent`:**
```python
# يستدعي _is_owned_connection(self.conn)
# لو True → self.conn.close() مع try/except
# لو False → لا شيء (الأغلب أن الـ connection مشترك)
```

**Properties:**
```python
section.conn -> ProtectedConnection
section.current_tab -> QWidget | None  # self._tabs.currentWidget()
```

---

## BaseCrudForm

### `ui/widgets/base/crud_form.py`

يرث من `QWidget + EditModeMixin + LiveConnMixin`.
يستخدم `emit_company_data_changed()` بدل `bus.data_changed.emit()`.

**Signals:** `saved = pyqtSignal(int)`

**إعدادات الـ subclass:**
```python
FORM_TITLE: str = "بيانات العنصر"
ADD_TEXT:   str = "➕  إضافة"
SAVE_TEXT:  str = "💾  حفظ التعديل"
```

**Hooks المطلوبة (override إلزامي):**
```python
_build_fields(group: FormGroup)        # يُستدعى في _build()
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
# يُستدعى بعد الـ FormGroup لإضافة widgets إضافية
```

**بناء الواجهة:**
```python
# outer layout → wrap_in_scroll(inner)
# inner: FormGroup(FORM_TITLE) + لوحة أزرار
# الأزرار: btn_add + btn_save + btn_cancel في HBoxLayout
# init_edit_mode يُستدعى في __init__
```

**منطق الحفظ:**
```python
# _on_add():
#   1. _collect() → None = فشل
#   2. _do_insert(data)
#   3. _reset()
#   4. emit_company_data_changed()
#   5. saved.emit(new_id)

# _on_save():
#   1. _collect() → None = فشل
#   2. _do_update(self._editing_id, data)
#   3. _reset()
#   4. emit_company_data_changed()
#   5. saved.emit(self._editing_id)

# _on_cancel():
#   1. _reset()
```

**`load_for_edit(item_id)`:**
```python
# يستدعي _do_load(item_id) مع try/except
# يستدعي _fill_fields(data)
# name = data.get("name", f"ID:{item_id}")
# enter_edit_mode(item_id, f"─── تعديل: {name} ───")
```

**`_reset()`:**
```python
# يستدعي _reset_fields()
# exit_edit_mode(f"─── {self.FORM_TITLE} ───")
```