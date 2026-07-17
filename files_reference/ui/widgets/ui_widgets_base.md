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
_refresh_data(company_id=None)         # افتراضياً: self.refresh() — [WidgetMixin]
_build_extra_header_actions(header: ListHeader)
_sort_key(col, row)                    # يُستدعى فقط لو SORTABLE=True
COL_MAX_WIDTHS: dict = None
# [Fix] سقف عرض مختلف لعمود معيّن (بدل السقف العام COL_MAX_WIDTH)
# يُمرَّر لـ auto_fit_columns() عبر _auto_resize()
```

> **[WidgetMixin]** `BaseListPanel` يستخدم `WidgetMixin` القياسي (`core/widget_mixin.py`)
> وليس نظام bus قديم منفصل. الأسماء الصحيحة الحالية للـ hooks القابلة
> للـ override هي `_refresh_style(*_)`, `_refresh_lang(*_)`, `_refresh_data(company_id=None)`
> — **لا** `_on_theme_changed`/`_on_language_changed`/`_on_data_changed` (أسماء قديمة محذوفة).

**[إصلاح 5] `refresh()` المحدّث:**
```python
def refresh(self):
    self._all_rows = self._load_rows()
    if self._filter_toolbar and self.conn:
        self._timer.stop()    # ← يمنع double apply_filter
        self._filter_toolbar.reload(self.conn)
    self._apply_filter()
```

**المشكلة القديمة قبل [إصلاح 5]:**
```
_filter_toolbar.reload()
  → يُعيد ملء categories combo
  → currentIndexChanged
  → filter_changed
  → _timer.start()
ثم refresh() تستدعي _apply_filter() مباشرة
النتيجة: _apply_filter() تُنفَّذ مرتين

الحل: self._timer.stop() قبل reload() يمنع التنفيذ المضاعف
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

**WidgetMixin (عند `CONNECT_BUS=True`):**
يستدعي `_init_widget_mixin(theme=True, font=True, lang=True, data=True)` — وإلا
(`CONNECT_BUS=False`) بدون `data=True`.

```python
def _refresh_style(*_):
    # يُعيد تطبيق: background + table_style() (مركزي لكل الجداول الوارثة)
    #             + empty_state background/color
    # يستدعي _rebuild_pagination_styles() + _rebuild_status_style()
    #        + refresh_visible_buttons() لأزرار الأكشن جوه خلايا الجدول وpagination

def _refresh_lang(*_):
    # يُحدّث: placeholder البحث + empty state title + نصوص pagination
    # يستدعي: _update_empty_state_title() + _update_pagination_texts()

def _refresh_data(company_id=None):
    # افتراضياً: self.refresh()
```

**[Fix] `showEvent` + `_schedule_fit` + `_do_fit` — إعادة قياس عرض الأعمدة عند الظهور:**
```python
# المشكلة: القياس اللي بيحصل جوه _fill_table() وقت البناء الأول غير
# موثوق لو الـ widget جوه تاب/QStackedWidget مخفي وقتها (splitter.width()
# يرجع صفر أو قيمة مؤقتة غلط).
# الحل: showEvent يعيد الحساب (_schedule_fit) في كل مرة الـ widget يظهر،
# وكل _fill_table تُجدول QTimer.singleShot(0, ...) إضافي بعد أحداث الـ
# layout المعلّقة. لو الـ widget مش ظاهر لسه، _do_fit يعيد جدولة نفسه
# بعد SPLITTER_RETRY_DELAY حتى _MAX_FIT_RETRIES=20 (≈ ثانيتين كحد أقصى).
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
panel.table -> QTableWidget   # attribute مباشر — الجدول الداخلي
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
CONNECT_BUS: bool = False      # افتراضياً False — يجب تفعيله صراحةً

_build_header_cards()          # يُستدعى في __init__ قبل بناء الـ content
_build_header_buttons()        # يُستدعى في __init__ قبل بناء الـ content
_fill_header(data: dict)       # افتراضياً: self._hdr.set_title(data.get("name", tr("value_dash")))
_refresh_data(company_id=None) # افتراضياً: load_item(self._item_id) لو self._item_id موجود
_refresh_style(*_)
_refresh_lang(*_)
```

> **[WidgetMixin]** نفس ملاحظة `BaseListPanel` — الأسماء الحالية `_refresh_style`/`_refresh_lang`/`_refresh_data`.
> `BaseDetailPanel` يستدعي `_init_widget_mixin(theme=True, font=True, lang=True, data=self.CONNECT_BUS)`
> لو `CONNECT_BUS=True`، وإلا `_init_widget_mixin(theme=True, lang=True)` (بدون font/data).

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

**`_refresh_style(*_)` — [إصلاح ثيم — جذري]:**
```python
# يُعيد تطبيق bg_page على: self + scroll + inner widget + children (بدون self._hdr)
# يُعيد تطبيق scroll_style() على self._scroll
# يستدعي self._force_repolish(self._hdr) — يجبر unpolish+polish فعلي على
# DetailHeader وكل أبناءه المباشرين المرئيين، بدل الاعتماد على repaint
# تلقائي قد يستخدم QSS قديم (cached) — خصوصاً لو الـ panel اتبنى وهو
# غير ظاهر (تاب غير نشط) وقت أول theme_changed.
# ⚠️ HEADER_BG: لو None (الافتراضي) → DetailHeader تقرأ _C['bg_surface']
# الحيّة وقت كل رسم فعلي (لا قيمة محسوبة مسبقاً وممررة كنص ثابت).
```

**`_refresh_lang(*_)`:**
```python
# translated = tr(self.EMPTY_TITLE)
# self._empty.set_title(translated)   — محاط بـ try/except
```

**إشعارات:**
```python
panel.show_success(msg, auto_hide=3000)
panel.show_error(msg)          # danger level — لا auto_hide
panel.show_warning(msg, auto_hide=0)
panel.show_info(msg, auto_hide=0)
# كلها تستدعي self._notif.show(msg, level, auto_hide)
# ⚠️ show_warning مهمة: guard.py يتحقق من hasattr(widget, "show_warning")
```

**API:**
```python
panel.load_item(item_id: int)
panel.clear()                  # يُعيد ضبط _item_id/_item_data + يُخفي notif
panel.show_success(msg, auto_hide=3000)
panel.show_error(msg)
panel.show_warning(msg, auto_hide=0)
panel.show_info(msg, auto_hide=0)
panel.item_id -> int | None
panel.item_data -> dict | None
panel.header -> DetailHeader
panel.content_layout -> QVBoxLayout
```

**Import الصحيح لـ scroll_style:**
```python
# [إصلاح 2.2] المسار الصحيح:
from ..theme.layout_styles import scroll_style
# (بدل from ..theme.styles import scroll_style المحذوف)
```

---

## BaseSection

### `ui/widgets/base/section.py`

**ملاحظة:** `BaseSection` تجمع سلوك `CrudSection` القديم [T-05]. `panels/crud_section.py`
**لم يعد موجوداً في `system_arch.txt`** — حُذف بالكامل، لا يوجد alias متبقٍ. استخدم
`BaseSection` من `ui/widgets/base/section.py` مباشرة لأي كود جديد.

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
COLLAPSIBLE: bool = True
# يسمح بإخفاء أي من الجانبين (list/detail) بالكامل لو المستخدم سحب حافة
# الـ splitter لحد قريب جداً من النهاية (سلوك QSplitter الافتراضي).
# الرجوع بنفس السحب اليدوي من نفس الحافة. False = يمنع الانهيار (الجانبان
# يفضلان ظاهرين دائماً) — override محلي لو الشاشة تحتاج ذلك.

FORM_POSITION: str = "none"
# [توحيد الجداول/Splitters — إصلاح] حُذفت قيمة "bottom" نهائياً.
# السبب: "bottom"/"top" كانتا تبنيان QVBoxLayout يدوي (فورم + قائمة فوق
# بعض عمودياً) *داخل نفس عمود QSplitter الأفقي* — تخطيط عمودي مدمج،
# مش splitter مستقل قابل للسحب. أي قسم محتاج فورم+قائمة جنب بعض قابلين
# للسحب لازم يستخدم _create_list()/_create_detail() مباشرة (نمط OrdersTab)
# بدل الاعتماد على FORM_POSITION.
# "none" → لا فورم: self._form = None، يرجع self._list مباشرة (الافتراضي)
# "left" → فورم يُنشأ عبر _create_form() لكن يُعرض داخل list panel نفسها
#          (لا splitter منفصل)، self._form = form (متاح عبر form_panel)

SPLITTER_RATIO: tuple = (1, 2)  # (list_stretch, detail_stretch)

_create_form() -> QWidget | None   # افتراضياً: None
_connect_signals()
# افتراضياً: list.item_selected → detail.load_item (لو موجودان)
_refresh_data(company_id=None)     # افتراضياً: self.refresh() — [WidgetMixin]
_on_item_selected(item_id: int)
# افتراضياً: يستدعي detail.load_item(item_id) لو موجود
```

**`_refresh_style(*_)`:**
```python
self._splitter.setStyleSheet(splitter_style())
```

**`_build_left_panel()` — منطق FORM_POSITION بالتفصيل (بعد حذف "bottom"):**
```python
form = self._create_form()

# لو form is None أو FORM_POSITION == "none":
#   self._form = None → يرجع self._list مباشرة

# لو FORM_POSITION == "left" أو أي قيمة أخرى:
#   self._form = form   ← يُحفظ (لا يُهمَل على عكس "none")
#   يرجع self._list (الفورم خارج الـ splitter — يديره الـ subclass بنفسه
#   عبر form_panel property، مفيد فقط للحالات النادرة التي لا تحتاج
#   فصلاً بصرياً قابلاً للسحب)
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
section.form_panel -> QWidget | None   # None لو FORM_POSITION="none" أو لا يوجد form
```

---

## TabSectionBase

### `ui/widgets/base/tab_section.py`

قاعدة مشتركة للأقسام التي تحتوي على `QTabWidget`. ترث من `QWidget, WidgetMixin`.

> **[إصلاح هيكلة]** `widgets/` (base classes) ممنوعة تستدعي `db/` أو
> `services/` مباشرة حسب الهيكلة المعمارية للمشروع (`widget → service → repo`).
> لذلك تغيّر الملف جذرياً عن النسخة القديمة:
> - `conn_fn` أصبح **معامل إلزامي** (لا `default`) — يُمرَّر من `tabs/` فقط،
>   التي تفتح الاتصال عبر الطبقة الصحيحة (`services/`).
> - **`_is_owned_connection` حُذفت بالكامل** — كانت تستدعي
>   `db.companies.company_state` مباشرة من `widgets/` لتحديد ملكية
>   الـ connection، وهذا كسر هيكلي بحد ذاته.
> - `closeEvent` **لم يعد يغلق `self.conn` إطلاقاً**. الـ widget لا يعرف
>   ولا يقرر ملكية الاتصال؛ هذا قرار `tabs/` عند اختيار `conn_fn`. الإغلاق
>   الفعلي يحدث في `company_state` عند تغيير الشركة، أو في `tabs/` صراحةً
>   لو كان الاتصال مملوكاً فعلاً لها.

```python
TabSectionBase(conn_fn, parent=None)
# conn_fn: callable إلزامي يُعيد connection — self.conn = conn_fn()
# يبني QTabWidget عبر normalize_tab_widget() ويستدعي _build_tabs()
# يستدعي apply_tab_widths() مرة واحدة بعد إضافة كل التبويبات (حل مركزي لقص نص التبويبات)
```

**Override إلزامي:**
```python
def _build_tabs(self, tabs: QTabWidget)
```

**Hook اختياري — دعم تحديث نص التبويبات عند تغيير اللغة (lang=True):**
```python
def _tab_label(self, index: int) -> str | None
# افتراضياً: يرجع None لكل الفهارس (لا تحديث)
# الوريث يمكنه override وإرجاع النص المترجم الجديد لكل index يريد تحديثه:
#     def _tab_label(self, index):
#         return {
#             0: f"{tr('tab_icon_raw')}  {tr('raw_tab')}",
#             1: f"{tr('categories_tab_icon')}  {tr('categories_tab')}",
#         }.get(index)
```

**`_refresh_style(*_)`:**
```python
# self._tabs.setStyleSheet(tab_style())
# apply_tab_widths(self._tabs)
```

**`_refresh_lang(*_)` — [إصلاح lang]:**
```python
# القديم: lang=False → كل الأقسام الوارثة (RawTab, LaborTab, MachineTab,
#         ProductTab...) لم تكن تستجيب لتغيير اللغة لايف؛ عناوين تباتها
#         الفرعية كانت تُبنى مرة واحدة فقط وتفضل كما هي حتى بعد تبديل اللغة.
# الجديد: lang=True دائماً + hook اختياري _tab_label():
for i in range(self._tabs.count()):
    label = self._tab_label(i)
    if label is not None:
        self._tabs.setTabText(i, label)
        updated = True
if updated:
    apply_tab_widths(self._tabs)   # إعادة حساب العرض لأن الطول تغيّر
# لو الوريث لم يوفّر _tab_label — لا شيء يحدث (نفس السلوك القديم تماماً)
```

**`closeEvent`:**
```python
# super().closeEvent(event) فقط — لا إغلاق لـ self.conn إطلاقاً
```

**Properties:**
```python
section.conn -> Connection            # = conn_fn()، يُضبط في __init__
section.current_tab -> QWidget | None  # self._tabs.currentWidget()
```

---

## BaseCrudForm

### `ui/widgets/base/crud_form.py`

**Imports الصحيحة:**
```python
# [إصلاح 2.4] المسار الصحيح:
from ui.widgets.mixins.form_mixins import EditModeMixin
# (بدل from ui.widgets.mixins.edit import EditModeMixin القديم)

# الاستخدام الصحيح للـ emit:
from ui.widgets.core.events import emit_company_data_changed
```

يرث من `QWidget + EditModeMixin + LiveConnMixin`.
يستخدم `emit_company_data_changed()` — لو مفيش شركة نشطة لا يطلق شيء.

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
#   4. emit_company_data_changed()   # لو مفيش شركة نشطة لا يطلق شيء
#   5. saved.emit(new_id)

# _on_save():
#   1. _collect() → None = فشل
#   2. _do_update(self._editing_id, data)
#   3. _reset()
#   4. emit_company_data_changed()   # لو مفيش شركة نشطة لا يطلق شيء
#   5. saved.emit(self._editing_id)

# _on_cancel():
#   1. _reset()
# أخطاء _do_insert / _do_update → QMessageBox.warning
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