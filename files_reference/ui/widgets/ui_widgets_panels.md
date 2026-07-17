# دليل الكود — UI / Widgets (5): Panels

> `ui/widgets/panels/`
> لوحات الواجهة الموحدة: مدخلات ثيميّة، حالة فارغة، فلاتر، أقسام تفاصيل،
> بطاقات قابلة للطي، جداول بيانات، وحقول/شارات/أزرار الفورمات.
>
> ⚠️ **[تصحيح تسمية/تقسيم]** كان هذا المرجع يغطي سابقاً `panels/` و
> `forms/` و `combo/` معاً في ملف واحد — مخالفة لقاعدة "مرجع واحد = مسار
> واحد". تم فصل `forms/` إلى **`ui_widgets_forms.md`** و `combo/` إلى
> **`ui_widgets_combo.md`**. هذا الملف يغطي `ui/widgets/panels/` فقط.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Themed Inputs](#themed-inputs) | `panels/themed_inputs.py` |
| [State (Empty State)](#state-empty-state) | `panels/state.py` |
| [FilterToolbar](#filtertoolbar) | `panels/filter.py` |
| [DetailSection](#detailsection) | `panels/detail_section.py` |
| [CollapsibleCard + CardGrid](#collapsiblecard--cardgrid) | `panels/layout_widgets.py` |
| [DataTableWidget](#datatablewidget) | `panels/data_table.py` |
| [Forms — Labels](#forms--labels) | `panels/form_labels.py` |
| [Forms — Fields](#forms--fields) | `panels/form_fields.py` |
| [Forms — Badges](#forms--badges) | `panels/form_badges.py` |
| [Forms — Buttons Bar](#forms--buttons-bar) | `panels/form_buttons.py` |
| [Forms — Group](#forms--group) | `panels/form_group.py` |

> ملاحظة: الأقسام تحت "Forms —" هنا كلها ملفات فعلية داخل `ui/widgets/panels/`
> (وليس `ui/widgets/forms/`) — التسمية "Forms" تصف الغرض الوظيفي للملف
> (حقول/شارات/أزرار فورمات) لا مساره. `ui/widgets/forms/inputs.py` (المسار
> الفعلي المختلف) مُغطّى في `ui_widgets_forms.md` المنفصل.

---

## Themed Inputs

### `ui/widgets/panels/themed_inputs.py`

**الغرض:** الحل الجذري لمشكلة "خلفيات فاتحة باقية بعد التحويل لـ dark". كثير من
أماكن المشروع كانت تستخدم `QLineEdit()` / `QComboBox()` مباشرة بدون
`setStyleSheet()` خالص، فتأخذ الـ Qt default style (أبيض دائماً) لأنه لا يوجد
ستايل يُحقن وقت الإنشاء ولا استماع لـ `theme_changed`. الحل: كل الـ widgets هنا
ترث `WidgetMixin` وتسجل نفسها في `theme_changed` عبر `_init_widget_mixin(theme=True,...)`،
مع `_refresh_style()` تُستدعى تلقائياً عند كل تغيير ثيم وأيضاً أول مرة وقت الإنشاء.

**من يستدعي هذا الملف:** يُستورد على نطاق واسع جداً في كل المشروع تقريباً —
كل الملفات في `panels/`, `components/`, `combo/`, `utils/searchable_combo.py`,
`utils/date_range.py`, `dialogs/*`, `forms/inputs.py` وغيرها تستخدم
`ThemedLineEdit`/`ThemedComboBox`/`ThemedFrame` كبديل مباشر عن `QLineEdit`/
`QComboBox`/`QFrame` الخام.

```python
class ThemedLineEdit(QLineEdit, WidgetMixin):
    def __init__(self, parent=None, min_height=INPUT_HEIGHT, error: bool = False)
    # _init_widget_mixin(font=False, lang=False, data=False) — theme=True افتراضياً
    # [ملاحظة تصميم مهمة] لا يستدعي self._refresh_style() تلقائياً في نهاية
    #   __init__ إلا لو type(self) is ThemedLineEdit بالضبط (وليس subclass).
    #   السبب: كلاسات وارثة (مثل _TreeGroupCombo) قد تحتاج بناء أجزاء إضافية
    #   بعد super().__init__() وقبل أول استدعاء لـ _refresh_style الخاصة
    #   بها (override) — لو استدعيناها هنا تلقائياً، ستُنفَّذ نسخة الوريث
    #   قبل بناء أجزائه فيُرمى AttributeError. كل كلاس Themed* يستدعي
    #   self._refresh_style() صراحةً بنفسه في آخر سطر من __init__.
    ._refresh_style(*_)   # setStyleSheet(input_style(self._h, error=self._error))
    .set_error(error: bool)   # يبدّل حالة الخطأ (حدود حمراء) ويعيد الرسم فوراً

class ThemedComboBox(QComboBox, WidgetMixin):
    def __init__(self, parent=None, min_height=INPUT_HEIGHT, auto_style: bool = True)
    # auto_style=True (افتراضي) → _init_widget_mixin + _refresh_style() فوراً
    # auto_style=False → للكلاسات الوارثة التي تبني أجزاء إضافية (مثل self._tree_view)
    #   قبل استدعاء _refresh_style()/_init_widget_mixin() يدوياً بنفسها
    ._refresh_style(*_)   # setStyleSheet(input_style(self._h))

class ThemedDateEdit(QDateEdit, WidgetMixin):
    def __init__(self, parent=None, min_height=INPUT_HEIGHT)
    # نفس نمط ThemedLineEdit: type(self) is ThemedDateEdit check
    ._refresh_style(*_)   # setStyleSheet(input_style(self._h))

class ThemedTextEdit(QTextEdit, WidgetMixin):
    def __init__(self, parent=None, min_height=INPUT_HEIGHT)
    ._refresh_style(*_)   # setStyleSheet(input_style(self._h))

class ThemedPlainTextEdit(QPlainTextEdit, WidgetMixin):
    def __init__(self, parent=None, min_height=INPUT_HEIGHT)
    # ⚠️ لا تستدعي _refresh_style() صراحةً حتى مع type(self) is check —
    #   لا يوجد استدعاء أول رسم في __init__ لهذا الكلاس تحديداً (فرق طفيف
    #   عن باقي كلاسات Themed* في نفس الملف)

class ThemedFrame(QFrame, WidgetMixin):
    def __init__(self, parent=None, bg_key="bg_surface", border="none", border_radius=0)
    # setAttribute(Qt.WA_StyledBackground, True) — [أساسي] بدونها خاصية
    #   "background" في الـ stylesheet لا تُطبَّق فعلياً وقت الرسم لـ QFrame
    #   (بعكس QLineEdit/QComboBox اللي عندهم هذا السلوك افتراضياً)
    # [إصلاح جذري] لا يستدعي self._refresh_style() في __init__ إلا لو
    #   type(self) is ThemedFrame بالضبط — لنفس سبب ThemedLineEdit تماماً،
    #   لكن أخطر هنا لأن عدد كبير من الكلاسات الوارثة (ListHeader, EmptyState,
    #   NotificationBar, StatCard, _OfferItemRow, ...) لها override كامل
    #   لـ _refresh_style() يعتمد على attributes/widgets لم تُبنَ بعد وقت
    #   نداء ThemedFrame.__init__ (لأن super().__init__() نفسها لسه بتتنفذ)
    .showEvent(event)
    # [إصلاح dark-theme] يجبر _refresh_style() مرة أخرى عند ظهور الـ frame
    #   فعلياً — يغطي حالة تغيّر الثيم أثناء إخفاء الـ frame (Qt أحياناً
    #   يؤجل إعادة رسم QSS المتداخل حتى أول repaint كامل بعد الظهور، فقد
    #   يستخدم نسخة مخزّنة/قديمة (cached) للستايل حتى ذلك الحين)
    ._refresh_style(*_)
    # radius = f"border-radius:{radius}px; " لو border_radius محدد
    # setStyleSheet(f"background: {_C[bg_key]}; border: {border}; {radius}")
    .set_bg_key(bg_key: str)   # يغيّر مفتاح لون الخلفية من _C ويعيد الرسم فوراً
```

**علاقة مباشرة:** `ThemedFrame` هي القاعدة لعدد كبير من widgets موثّقة في
مراجع أخرى: `EmptyState`, `NotificationBar`/`BaseWarningBar` (`components/notification.py`),
`ListHeader` (`components/headers_list.py`), `DetailHeader`/`PageHeader`
(`components/headers_page.py`), `StatCard`/`_StatCard` (`components/stat_card.py`),
`StatusChip`/`StatusCard` (`components/status_chip.py`), `LoadingOverlay`
(`components/spinner.py`), `DetailSection` (`panels/detail_section.py`),
`CollapsibleCard` (`panels/layout_widgets.py`), `DialogShell._sep`/`_make_header`
(`dialogs/dialogs_base.py`), `_sub_row_widget` في `ComponentRow`
(`components/component_row/ui.py`).

---

## State (Empty State)

### `ui/widgets/panels/state.py`

```python
EmptyState(icon=None, title="", subtitle="", action_text="",
           style="dashed", color=None, min_height=EMPTY_STATE_DEFAULT_MIN_H,
           expandable=False, parent=None)
# ThemedFrame + WidgetMixin(theme=True, font=True, lang=True, data=False)
# icon=None → tr('empty_icon_table') | title="" → tr('no_data')
# style: "dashed" | "solid" | "plain" (يحدد نمط الحدود border-style)
# expandable=True → SizePolicy.Expanding + spacing/margins أكبر (EMPTY_STATE_*_EXPANDED)
# يحفظ _lbl_title / _lbl_icon / _lbl_sub كـ references للتحديث المباشر
# action_text غير فارغ → زر (make_btn) بستايل "primary" لو expandable وإلا "success"
# Signals: action_clicked
  .set_title(text: str)
  .title() -> str

._refresh_style(*_)
# يعيد بناء: الإطار (bg/border حسب card_colors(color)) + كل الـ labels
# (icon/title/sub) بألوان وأحجام خط محدّثة من _C/get_font_size()

._refresh_lang(*_)
# لو _lbl_title موجود و _title_text فارغ (لم يُمرَّر title صراحة) → يُحدّث
# النص لـ tr('no_data') الحالي (يدعم تبديل اللغة لايف فقط للعنوان الافتراضي)

EmptyPanelState(icon=None, title="", subtitle="", action_text="",
                color=None, parent=None) -> EmptyState
# alias — title افتراضي tr('no_data') لو فارغ، color افتراضي _C['text_muted']،
# style="plain", expandable=True دائماً — للتوافق مع الكود القديم

set_table_empty_state(table: QTableWidget, message="", icon=None, color=None)
# message="" → tr('no_data') | icon=None → tr('empty_icon_table')
# يضيف صفاً واحداً (setRowCount(1)) بارتفاع EMPTY_STATE_TABLE_ROW_H
# نص الخلية = f"{icon}  {message}" بخط italic، محاذاة وسط، Qt.ItemIsEnabled فقط
# لو أكثر من عمود → setSpan(0, 0, 1, col_count)

clear_table_empty_state(table: QTableWidget)
# لو rowCount()==1 والصف الوحيد غير قابل للتحديد (علامة empty state) → يمسحه
# ويُعيد setSpan(0,0,1,1) لو كان هناك أكثر من عمود
```

**Imports:**
```python
# [FIX] absolute imports بدل relative:
from ui.font  import fs, get_font_size
from ui.theme import _C
```

---

## FilterToolbar

### `ui/widgets/panels/filter.py`

```python
FilterToolbar(conn=None, scope="all", show_category=True,
              show_date=False, placeholder=None, show_presets=False,
              parent=None)
# placeholder=None → مفتاح tr() الافتراضي 'list_search_placeholder'
#   (self._placeholder_key = placeholder or 'list_search_placeholder' — يُعامَل
#   كمفتاح ترجمة وليس نصاً حرفياً)
# [إصلاح 14] WidgetMixin(data=True) يستمع لـ bus.company_data_changed — يُعيد
#   تحميل التصنيفات تلقائياً عبر _refresh_data()
# [تحسين 16] reload() يُحدّث self._conn ثم يُعيد تحميل التصنيفات
# Signals: filter_changed
```

**Imports:**
```python
# [FIX] absolute imports — ثلاث نقاط (relative) كانت تُسبب ImportError:
from ui.font  import fs, get_font_size, FS_SM
from ui.theme import _C
```

**`_refresh_data(company_id=None)` — [إصلاح هيكلة]:**
```python
# القديم (محذوف): from db.companies.company_state import company_state
# الجديد: عبر CompanyService فقط (المسار الصحيح widget → service → repo):
#   لو CompanyService.is_company_ready():
#       new_conn = CompanyService.get_active_erp_conn()
#       لو new_conn ليس None → self._conn = new_conn
# ثم يستدعي self._reload_categories() دائماً (حتى لو فشل تحديث الاتصال)
```

```python
toolbar.name_query -> str
toolbar.category_id
toolbar.in_date_range(date_str: str) -> bool
toolbar.match(name, cat_id, date_str="") -> bool
toolbar.set_count(shown: int, total: int)
toolbar.reload(conn=None)
# [تحسين 16] يُحدّث self._conn لو conn مُعطى، ثم يُعيد تحميل التصنيفات
toolbar.reset()
# يمسح البحث، يُعيد cmb_cat لـ index 0 (بـ blocked_signals)، ويستدعي
# _date_filter.reset() لو موجود وإلا filter_changed.emit() مباشرة
```

**`_reload_categories()`:**
```python
# لو cmb_cat=None أو self._conn=None → يرجع فوراً
# يحفظ prev = currentData() قبل المسح
# داخل blocked_signals(self.cmb_cat):
#   يستدعي populate_category_combo(cmb_cat, conn, scope, all_label=tr('filter_all_categories'))
#   لو استثناء → fallback: addItem(tr('filter_all_categories'), None)
#   يُعيد اختيار prev لو لا يزال موجوداً ضمن العناصر
```

---

## DetailSection

### `ui/widgets/panels/detail_section.py`

**Import الصحيح:**
```python
# [إصلاح 2.3] المسار الصحيح:
from ..components.headers_page import SectionHeader
# (بدل from ..components.headers import SectionHeader المحذوف)
```

```python
DetailSection(title="", cols=1, compact=False)
  .add_row(label, value="─", color=None, bold=False, icon="") -> QLabel
  .add_separator()
  .set_data(data: dict, clear_missing: bool = False) -> dict[str, QLabel]
  # clear_missing=True: يُخفي الصفوف غير الموجودة في data الجديدة
  .clear_rows()
  .update_value(index, value, color=None)
  .value_label(index: int) -> QLabel | None
  .reset_values()
  .show_all_rows()

make_detail_row(label, value="─", color=None, bold=False) -> tuple[QLabel, QLabel]

TwoColDetails()
  .add(label, value="─", color=None, bold=False) -> QLabel
  .reset()
```

---

## CollapsibleCard + CardGrid

### `ui/widgets/panels/layout_widgets.py`

**Imports:**
```python
# [FIX] absolute imports — ثلاث نقاط (relative) كانت تُسبب ImportError:
from ui.font  import fs, get_font_size
from ui.theme import _C
```

```python
CollapsibleCard(title="", expanded=True, accent=None)
# Signals: toggled(bool)
# المحتوى في: card.content_layout (QVBoxLayout)
  .set_expanded(expanded: bool)
  .is_expanded -> bool

CardGrid(cols=4, spacing=10)
  .add_widget(widget: QWidget)
  .clear()

CardGrid.from_widgets(widgets: list, cols=4, spacing=10) -> CardGrid
```

---

## DataTableWidget

### `ui/widgets/panels/data_table.py`

```python
DataTableWidget(columns, stretch_col=-1, col_widths=None,
                title="", add_text="", search_placeholder="🔍  بحث...",
                row_height=ROW_HEIGHT_LARGE, empty_icon="📋",
                empty_title="لا توجد بيانات")
# Signals: add_clicked, search_changed(str), row_selected(int)
# [إصلاح 7] end_fill() تفرّق بين 3 حالات:
#   total=0         → empty state "لا توجد بيانات"    (_empty)
#   total>0,shown>0 → يعرض الجدول
#   total>0,shown=0 → empty state "لا توجد نتائج"     (_empty_filtered, icon=🔍)
```

**`end_fill(shown: int = None)`:**
```python
total   = self.table.rowCount()
visible = shown if shown is not None else total

has_data          = visible > 0
is_filtered_empty = (not has_data) and (total > 0)

self.table.setVisible(has_data)
self._empty.setVisible(not has_data and not is_filtered_empty)
self._empty_filtered.setVisible(is_filtered_empty)
```

```python
  .begin_fill()
  .insert_row() -> int
  .end_fill(shown: int = None)
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

## Forms — Labels

### `ui/widgets/panels/form_labels.py`

```python
form_label(text, color=None) -> QLabel
# color افتراضي: _C['text_sec'] | font-weight: 600
# alignment: AlignRight | AlignVCenter

required_label(text) -> QLabel
# علامة * بلون _C["danger"] كـ RichText
# alignment: AlignRight | AlignVCenter

hint_label(text, color=None) -> QLabel
# color افتراضي: _C['text_muted'] | font-size: fs(base, -1)
# wordWrap: True

section_title(text, color=None, icon="") -> QLabel
# color افتراضي: _C['accent'] | font-weight: 700
# icon يُدمج: f"{icon}  {text}" لو icon غير فارغ

separator_line() -> QFrame
# QFrame.HLine | height: 1 | color: _C['border']
```

---

## Forms — Fields

### `ui/widgets/panels/form_fields.py`

**Import الصحيح:**
```python
# [FIX] المسار الصحيح:
from ..theme.input_styles import spinbox_style
# (بدل from ..theme.styles الذي لم يعد موجوداً بعد Refactor V3)
```

**كلاسات داخلية (WidgetMixin themed):**
```python
_ThemedDoubleSpinBox(min_height=FORM_FIELD_DEFAULT_H)
# QDoubleSpinBox + WidgetMixin(font=False, lang=False, data=False)
# _refresh_style() يُطبّق spinbox_style(self._h, widget="QDoubleSpinBox")

_ThemedSpinBox(min_height=FORM_FIELD_DEFAULT_H)
# QSpinBox + WidgetMixin(font=False, lang=False, data=False)
# _refresh_style() يُطبّق spinbox_style(self._h, widget="QSpinBox")
```

```python
spin_field(max_=999999, dec=2, min_=0, min_height=FORM_FIELD_DEFAULT_H) -> QDoubleSpinBox
# يبني _ThemedDoubleSpinBox (يتابع الثيم تلقائياً) + setRange/setDecimals/setMinimumHeight

int_spin_field(max_=9999, min_=0, min_height=FORM_FIELD_DEFAULT_H) -> QSpinBox
# يبني _ThemedSpinBox (يتابع الثيم تلقائياً) + setRange/setMinimumHeight

labeled_widget(widget, unit, unit_color=None, spacing=6) -> QWidget
# [widget] [unit_label] — unit_color افتراضي: _C['text_muted']
# يُضيف addStretch() في النهاية

field_row(label_text, widget, required=False, hint="") -> tuple[QLabel, QWidget]
# required=True → required_label() | False → form_label()
# hint → يُغلّف widget في QVBoxLayout مع hint_label أسفله
# يرجع (label, widget_or_container)

labeled_row(label_text, *widgets, spacing=6) -> QWidget
# [form_label] [widget1] [widget2] ... [stretch]
# يقبل strings كـ hint_label تلقائياً
# يتجاهل None في الـ widgets

make_form_layout(spacing=10,
                 label_align=Qt.AlignRight | Qt.AlignVCenter,
                 contents_margins=(12, 10, 12, 10)) -> QFormLayout
# FieldGrowthPolicy: ExpandingFieldsGrow
```

---

## Forms — Badges

### `ui/widgets/panels/form_badges.py`

```python
make_preview_label(text="─", status="info") -> QLabel
# يستخدم status_colors(status) من core/colors
# wordWrap: True | border-radius: 6px | padding: 8px 12px
# font-size: fs(base, -1)
```

#### `ResultBadge(QLabel)`

```python
ResultBadge(text="─", color=None, status="success", parent=None)
# color: لون نص مخصص — يُلغي fg من status_colors لو محدد
# status: "success" | "warning" | "danger" | "info" | ...
# border-radius: 4px | padding: 4px 8px | font-weight: bold
```

**API:**
```python
  .set_value(text: str, color: str = None)
  # لو color جديد ومختلف → يُعيد تطبيق _apply()

  .set_status(status: str)
  # لو status مختلف → يُعيد تطبيق _apply()

  .reset()
  # setText("─")
```

**منطق `_apply()`:**
```python
# لو _custom_color محدد:
#   color = _custom_color | bg/border من status_colors
# لو لا:
#   color = s['fg'] | bg/border من status_colors
```

#### `ModeBadge(QLabel)`

```python
ModeBadge(text="─", color="blue", parent=None)
# color: "blue" | "orange" | "green" | "red" | "purple"
# يُترجم color → status key:
#   "blue"   → "primary"
#   "orange" → "warning"
#   "green"  → "success"
#   "red"    → "danger"
#   "purple" → "purple"
# border-radius: 4px | padding: 3px 8px | font-weight: bold
# font-size: fs(base, -1)
```

**API:**
```python
  .set_mode(text: str, color: str = None)
  # لو color جديد ومختلف → يُعيد تطبيق _apply_style()

  .reset()
  # setText("─")
```

#### `InlinePreview(QWidget)`

```python
InlinePreview(label="النتيجة:", color=None, status="success", parent=None)
# Layout: [QLabel(label)] [ResultBadge("─")]  [stretch]
# label: color=_C['text_sec'] | font-weight: 600 | font-size: fs(base, -1)
# _lbl_value: ResultBadge داخلي
```

**API:**
```python
  .set_value(text: str)
  # يستدعي self._lbl_value.set_value(text)

  .reset()
  # يستدعي self._lbl_value.reset()
```

**مثال:**
```python
from ui.widgets.panels.form_badges import ResultBadge, ModeBadge, InlinePreview

# badge للنتيجة المحسوبة
badge = ResultBadge("─", status="success")
badge.set_value("250.00 ج", color=_C['success'])
badge.set_status("warning")   # يُغيّر الألوان
badge.reset()                 # يُعيد "─"

# badge للوضع الحالي
mode = ModeBadge("─", color="blue")
mode.set_mode("وضع التعديل", color="orange")

# عرض inline
preview = InlinePreview(label="التكلفة الكلية:", status="success")
preview.set_value("1,200.00 ج")
preview.reset()
```

---

## Forms — Buttons Bar

### `ui/widgets/panels/form_buttons.py`

```python
CrudButtonsBar(QWidget, WidgetMixin)
CrudButtonsBar(add_text="", save_text="", cancel_text="", show_mode=True, parent=None)
# نصوص الأزرار من tr() لو فارغة:
#   add_text    → tr("btn_add")
#   save_text   → tr("btn_save")
#   cancel_text → tr("btn_cancel")
# show_mode=True → يُظهر lbl_mode فوق الأزرار
# show_mode=False → lbl_mode يُنشأ لكن غير مرئي (للـ compatibility)
# _init_widget_mixin(theme=True, font=True, lang=True, data=False) — لا ربط bus يدوي
# Signals: add_clicked, save_clicked, cancel_clicked
```

**`_refresh_style(*_)`:**
```python
# لو show_mode=True فقط → يُعيد تلوين lbl_mode (accent color + bold + fs(base,0))
```

**Attributes:**
```python
  .btn_add    -> QPushButton   # style: "primary"
  .btn_save   -> QPushButton   # style: "success"
  .btn_cancel -> QPushButton   # style: "ghost"
  .lbl_mode   -> QLabel        # دائماً موجود حتى لو show_mode=False
```

**API:**
```python
  .set_mode_text(text: str)
  # lbl_mode.setText(text)
```

**`_refresh_lang(*_)`:**
```python
# [WidgetMixin hook] يُحدّث النصوص من tr() مباشرة — لا يُخزّن النصوص المخصصة:
self.btn_add.setText(tr("btn_add"))
self.btn_save.setText(tr("btn_save"))
self.btn_cancel.setText(tr("btn_cancel"))
```

**ملاحظة:** لو مررت `add_text` مخصص — سيُفقد عند تغيير اللغة. الـ mixin يُعيد دائماً `tr("btn_add")`.

**Layout الداخلي:**
```
QVBoxLayout:
  [lbl_mode]          ← لو show_mode=True
  QHBoxLayout:
    [btn_add] [btn_save] [btn_cancel] [stretch]
```

**مثال:**
```python
from ui.widgets.panels.form_buttons import CrudButtonsBar

bar = CrudButtonsBar(show_mode=True)
bar.add_clicked.connect(self._on_add)
bar.save_clicked.connect(self._on_save)
bar.cancel_clicked.connect(self._on_cancel)
bar.set_mode_text("─── تعديل: المنتج ───")

# مع نصوص مخصصة (تُفقد عند تغيير اللغة):
bar = CrudButtonsBar(add_text="➕ إضافة منتج", show_mode=False)
```

---

## Forms — Group

### `ui/widgets/panels/form_group.py`

```python
FormGroup(title="", accent=None, parent=None)
# يرث من QGroupBox
# accent افتراضي: _C["accent"]
# border-radius: 10px | margin-top: 10px | padding-top: 6px
# title position: top right (RTL)
```

**Layout الداخلي:**
```python
self.form = QFormLayout(self)
# spacing: 10
# labelAlignment: AlignRight | AlignVCenter
# contentsMargins: (12, 14, 12, 12)
```

**API:**
```python
  .add_row(label: str, widget: QWidget)
  # form.addRow(label, widget)

  .add_label_row(label_widget: QWidget)
  # form.addRow(label_widget) — بدون label نصي

  .add_separator()
  # يُضيف QFrame.HLine بارتفاع 1 بلون _C['border']
  # form.addRow(sep)

  .form -> QFormLayout   # الـ layout الداخلي للوصول المباشر
```

```python
FormGroup(QGroupBox, WidgetMixin)
# _init_widget_mixin(font=False, lang=False, data=False) — theme=True افتراضياً
```

**`_refresh_style(*_)`:**
```python
# يُطبق QGroupBox stylesheet مع:
#   title color = self._custom_accent or _C['accent']
#   background = _C['bg_surface'] | border = _C['border']
#   border-radius: FORM_GROUP_BORDER_RADIUS | margin-top: FORM_GROUP_MARGIN_TOP
#   padding-top: FORM_GROUP_PADDING_TOP | title padding: FORM_GROUP_TITLE_PAD_H
# مربوطة بـ WidgetMixin(theme=True) — تُعاد تلقائياً عند bus.theme_changed/font_changed
```

**`add_separator()` — [تحديث]:**
```python
# لا يبني QFrame خام بستايل ثابت — يستخدم _ThemedSeparator (QFrame + WidgetMixin)
# داخلي يتابع الثيم تلقائياً عبر _refresh_style() الخاصة به:
class _ThemedSeparator(QFrame, WidgetMixin):
    # QFrame.HLine | height: SEPARATOR_LINE_H
    # _init_widget_mixin(font=False, lang=False, data=False)
    # _refresh_style(*_): setStyleSheet(f"background:{_C['border']}; border:none;")
self.form.addRow(sep)
```

**مثال:**
```python
from ui.widgets.panels.form_group import FormGroup

grp = FormGroup("بيانات المنتج", accent=_C['accent'])
grp.add_row("الاسم :", self.inp_name)
grp.add_row("السعر :", self.spin_price)
grp.add_separator()
grp.add_row("الفئة :", self.cmb_category)

# الوصول المباشر للـ form layout:
grp.form.setSpacing(12)
```

---

## علاقات الملفات

- `themed_inputs.py` (`ThemedFrame`) هو القاعدة لعدد كبير من widgets في هذا المرجع نفسه: `EmptyState`، `DetailSection`، `CollapsibleCard`، وكذلك widgets في مراجع أخرى (`ListHeader`, `NotificationBar`, `DetailHeader`/`PageHeader`, `StatCard`, `LoadingOverlay` — راجع `ui_widgets_components.md`).
- `filter.py` (`FilterToolbar`) يستخدم `blocked_signals` من `utils/signals.py` و `SearchBar` من `components/headers_list.py` (مرجع: `ui_widgets_utils.md` و `ui_widgets_components.md`)، ويستدعي `populate_category_combo` من `combo/category.py` (مرجع: `ui_widgets_combo.md`).
- `form_fields.py`, `form_group.py`, `themed_inputs.py` كلها تعتمد على `theme/input_styles.py`/`theme/table_styles.py` (مرجع: `ui_widgets_theme.md`) لكل الألوان والستايلات.
- `data_table.py` يعتمد على `tables/tables.py` (`make_list_table`, `auto_fit_columns` — مرجع: `ui_widgets_tables.md`) و `components/headers_list.py` (`ListHeader`).
- `layout_widgets.py` (`CollapsibleCard`) يستخدم `theme/builders.py` (`h_divider`) و `theme/card_styles.py` (`card_style`).
- كل الملفات في هذا المرجع تتبع نمط `WidgetMixin` الموحّد من `core/widget_mixin.py` (مرجع: `ui_widgets_core.md`) لربطها بأحداث الثيم/اللغة/بيانات الشركة.
- `ui/widgets/forms/inputs.py` (مسار مختلف تماماً — مرجع منفصل: `ui_widgets_forms.md`) يستورد `ThemedLineEdit`/`ThemedComboBox`/`ThemedDateEdit` من هذا الملف (`panels/themed_inputs.py`).