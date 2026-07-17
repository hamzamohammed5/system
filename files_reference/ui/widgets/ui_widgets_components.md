# دليل الكود — UI / Widgets (3): Components

> `ui/widgets/components/` — كل مكونات الواجهة القابلة لإعادة الاستخدام.
> يشمل: Button, Labels, Headers, Notification, Spinner, Stats, Badges, ActionToolbar, ComponentRow.
>
> ⚠️ **[تصحيح تسمية/تقسيم]** كان هذا المرجع يغطي سابقاً `ColorPickerWidget`
> (`helpers/color_picker.py`) رغم أن مساره الفعلي `ui/widgets/helpers/` وليس
> `ui/widgets/components/` — مخالفة لقاعدة "مرجع واحد = مسار واحد". تم فصله
> إلى **`ui_widgets_helpers.md`** المستقل. هذا الملف يغطي `ui/widgets/components/` فقط.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Button](#button) | `components/button.py` |
| [Label](#label) | `components/label.py` |
| [Amount Label](#amount-label) | `components/amount_label.py` |
| [Progress](#progress) | `components/progress.py` |
| [Headers List](#headers-list) | `components/headers_list.py` |
| [Headers Page](#headers-page) | `components/headers_page.py` |
| [Notification](#notification) | `components/notification.py` |
| [Spinner](#spinner) | `components/spinner.py` |
| [Stat Card](#stat-card) | `components/stat_card.py` |
| [Badge](#badge) | `components/badge.py` |
| [Status Chip](#status-chip) | `components/status_chip.py` |
| [ActionToolbar](#actiontoolbar) | `components/action_toolbar.py` |
| [Constants — General](#constants--general) | `components/constants_general.py` |
| [ComponentRow — Widget](#componentrow--widget) | `components/component_row/widget.py` |
| [ComponentRow — UI](#componentrow--ui) | `components/component_row/ui.py` |
| [ComponentRow — OpRows](#componentrow--oprows) | `components/component_row/op_rows.py` |
| [ComponentRow — Variants](#componentrow--variants) | `components/component_row/variants.py` |

---


## Button

### `ui/widgets/components/button.py`

```python
make_btn(text: str = "", style: str = "normal", fixed_size: bool = True,
         icon: str = None, compact: bool = False) -> QPushButton
# style: "primary" | "success" | "danger" | "ghost" | "normal"
# يحفظ style على الزر كـ Qt property ("_btn_style") لـ refresh_visible_buttons
# fixed_size=True → setFixedWidth (بعرض محسوب من _calc_btn_width_for_text)
# fixed_size=False → setMinimumWidth (قابل للتمدد، SizePolicy.Expanding)
# ألوان الأزرار تُقرأ من _C — تتغير مع الثيم

# ── icon (مفتاح من ICON_PATHS، مثل "reset") بدون text ──
# → زر أيقونة فقط، مربع الشكل (عرض = ارتفاع)، مرسوم بالكود (QSvgRenderer)
#   بدل الاعتماد على رمز يونيكود من الفونت (دعم غير مضمون في كل الأنظمة).
# stylesheet مربع منفصل (_get_square_stylesheet) بدون min-height/padding —
# القياس بالكامل عبر setFixedSize() لأن min-height في QSS كان يفرض
# ارتفاع زر نص عادي فوق أي setFixedSize برمجي.
# compact=True (مع icon) → حجم أصغر: margin = BTN_BORDER_W فقط
# compact=False (مع icon) → حجم عادي: icon_size = max(14, h - BTN_PAD_H)

# ── compact=True مع text (بدون icon) ──
# → زر مربع صغير حوالين رمز نصي (يونيكود قصير)، الحجم كامل (عرض+ارتفاع)
#   من QFontMetrics.boundingRect(text) + هامش صغير، بدل ثوابت زر نص عادي.

invalidate_stylesheet_cache()
# يمسح _stylesheet_cache — يُستدعى من apply_font() وعند تغيير الثيم

invalidate_icon_cache()
# يمسح _icon_cache (dict[(icon_key, size, color), QIcon]) — الألوان تتغير
# مع الثيم فلازم إعادة رسم الأيقونات SVG أيضاً

refresh_visible_buttons(root_widget) -> int
# يستدعي invalidate_stylesheet_cache() + invalidate_icon_cache() أولاً
# يُعيد تطبيق stylesheet على كل QPushButton في الـ widget tree عبر property("_btn_style")
# يفرّق بين:
#   - أزرار مربعة (property("_btn_square")) → _get_square_stylesheet + إعادة حساب
#     side = icon_size + BTN_BORDER_W*2 من جديد، وإعادة رسم الأيقونة SVG لو موجودة
#   - أزرار نص عادية → _get_stylesheet(style, base) + إعادة ضبط setFixedHeight
#     لو minimumHeight() > 0، وإعادة رسم الأيقونة (لو icon key محفوظ) بحجم h
# يتجاهل RuntimeError (widget محذوف) بصمت
# يرجع عدد الأزرار المحدثة

calc_btn_width(text: str, font_size: int, padding: int = BTN_TEXT_PAD) -> int
# = _calc_btn_width_for_text(text, font, extra_pad=padding) — نفس حساب make_btn
# الداخلي، عشان أي كود يحسب عرض زر يدوياً (لحجز مساحة قبل بناء الزر) ياخد
# نفس الرقم اللي make_btn هيطلعه فعلياً
```

**ICON_PATHS — أيقونات SVG مرسومة بالكود:**
```python
ICON_PATHS = {
    "reset":         "...",  # سهم دائري إعادة تحميل
    "chevron_right": "...",  # مثلث يمين — حالة مقفولة (expand/collapse)
    "chevron_down":  "...",  # مثلث لأسفل — حالة مفتوحة
}
# رموز يونيكود (↺, ▶, ▼) غير مضمونة الدعم في كل الفونتات/الأنظمة —
# تظهر أحياناً كمربع/حرف غريب. الحل: SVG path بسيط بمقاس viewBox="0 0 24 24"،
# اللون يُحقن وقت التوليد (_make_svg_icon) ليتماشى مع الثيم الحالي.

_make_svg_icon(icon_key: str, color: str, size=18) -> QIcon
# يبني QIcon من path مرسوم (QSvgRenderer → QPixmap) — نتيجة مخزّنة في _icon_cache
_calc_btn_width_for_text(text: str, font: QFont, extra_pad=0) -> int
# text_w (QFontMetrics.horizontalAdvance) + chrome (2×BTN_PAD_H + 2×BTN_BORDER_W) + extra_pad
# [FIX] يحسب من نفس القيم اللي الـ stylesheet المُولّد فعلياً يستخدمها
# (بدل رقم تقريبي منفصل) — يمنع قص النص في نصوص عربية/طويلة
```

**أنماط الأزرار:**

| style | الوصف | الألوان |
|-------|-------|---------|
| `"primary"` | الإجراء الرئيسي | `accent_light / accent_text` |
| `"success"` | حفظ / إضافة — أخضر | `success_bg / success` |
| `"danger"` | حذف / خطأ — أحمر | `danger_bg / danger` |
| `"ghost"` | ثانوي / إلغاء — شفاف | `border_med / text_sec` |
| `"normal"` | عادي — رمادي فاتح | `bg_surface_2 / text_sec` |

**الـ cache:**
```python
_stylesheet_cache: dict[tuple[str, int], str]
# key = (style_name, font_size)
# يُبنى بـ _build_stylesheet() أول مرة ثم يُعاد من الـ cache
# يُمسح بـ invalidate_stylesheet_cache() عند تغيير الثيم أو الخط
```

---

## Label

### `ui/widgets/components/label.py`

```python
InfoRow(separator="  ·  ")
  .set_parts(parts: list)   # يُرشح القيم الفارغة تلقائياً (str(p) for p if p)
  .set_text(text)
  .label() -> QLabel

ModeLabel(add_text="جديد", icon="")
  .set_add_mode(text=None)   # أزرق (_C['accent']) — وضع الإضافة
  .set_edit_mode(name="")    # برتقالي (_C['warning']) — وضع التعديل
  .set_custom(text, color=None)
  .is_edit_mode -> bool       # property
```

---

## Amount Label

### `ui/widgets/components/amount_label.py`

```python
format_amount(value, decimals=2, currency="ج") -> str
amount_color(value, positive_color=None, negative_color=None, zero_color=None) -> str
dr_cr_color(side: str) -> str    # side: "dr" | "cr"

AmountLabel(value=None, currency="ج", decimals=2, bold=True,
            font_size_offset=0, auto_color=True)
  .set_amount(value, color=None)
  # value == 0 → setText("─") + color = text_muted
  .set_debit(value)
  .set_credit(value)
  .reset(placeholder="─")

DebitCreditDisplay(currency="ج")
  .update(total_dr, total_cr)
  .reset()

BalanceDisplay(currency="ج")
  .set_balance(value, side_label="", color=None)
  .set_debit_credit_balance(dr, cr)
  .reset()
```

---

## Progress

### `ui/widgets/components/progress.py`

```python
ProgressBar(label="", color=None, height=8, show_pct=True, compact=False)
  .set_value(value, label=None)  # value: 0-100
  # يُحدّث fill width + percent label + لون تلقائي حسب النسبة:
  #   >= 90 → success | >= 60 → color | >= 30 → warning | else → danger
  .set_color(color)
  .value() -> float
  .reset()
  # resizeEvent: يُعيد حساب عرض الـ fill تلقائياً (guard: total_w > 0)

MultiProgressBar(spacing=8)
  .add_bar(label, value=0, color=None) -> ProgressBar
  .clear_bars()
  .update_bar(index, value)
```

---

## Headers List

### `ui/widgets/components/headers_list.py`

```python
SearchBar(placeholder="", delay_ms=250, height=34)
# placeholder افتراضي من tr("list_search_placeholder")
# debounce: لو delay > 0 → يبدأ timer | لو delay == 0 → emit فوري
# Signals: search_changed(str)
  .text() -> str          # text().strip().lower()
  .clear()
  .set_placeholder(text: str)
  .inp -> QLineEdit       # الحقل الداخلي للوصول المباشر

StatusBar()               # يرث من QLabel
  .set_count(shown: int, total: int)
  # shown == total → tr("showing_all", total=total)
  # shown != total → tr("showing_of", shown=shown, total=total)
  .set_text(text: str)
  .clear_count()

ListHeader(title="", add_text="", show_search=True,
           search_placeholder="", search_delay=250)
# يشترك في bus.language_changed بـ Qt.UniqueConnection لتحديث placeholder تلقائياً
# Signals: search_changed(str), add_clicked
  .add_action(text, callback=None, style="normal") -> QPushButton
  # يُضاف قبل btn_add لو موجود، وإلا يُضاف في الآخر
  .search_text() -> str
  .clear_search()
  .set_add_enabled(enabled: bool)
  .search_bar -> SearchBar | None
  .btn_add -> QPushButton | None

make_list_header(title="", add_text="", show_search=True,
                 placeholder="") -> ListHeader
```

---

## Headers Page

### `ui/widgets/components/headers_page.py`

```python
SectionHeader(title="")
  .set_title(title)
  .add_button(text, callback=None, style="normal") -> QPushButton

PageHeader(title="", subtitle="", icon="", accent=None, compact=False)
  .set_title(text)
  .set_subtitle(text)
  .add_action(text, callback=None, style="primary") -> QPushButton

DetailHeader(bg=None)
# bg=None → [إصلاح ثيم جذري] تُقرأ _C['bg_surface'] الحيّة وقت كل رسم فعلي
# داخل _refresh_style، لا قيمة محسوبة مسبقاً وممررة كنص ثابت (كانت المشكلة
# القديمة: BaseDetailPanel._build كان يحسب bg=(HEADER_BG or _C['bg_surface'])
# مرة واحدة ويُقفل عليها للأبد، فتحديثات الثيم اللاحقة لا تصل).
# ActionToolbar يُنشأ بـ lazy initialization — فقط عند أول استخدام فعلي
# _ensure_toolbar() ينشئ ActionToolbar ويُضيفه لـ _tb_section ويُظهره
  .set_title(text)             # title_is_custom=True — لا يُستبدل بـ tr('amount_dash_placeholder') بعدها
  .set_type_badge(text, color=None)          # افتراضي: _C['text_muted']
  .set_status_badge(text, text_color=None, bg=None, border=None)
  # افتراضي: _C['text_neutral'] / _C['card_fallback_bg'] / _C['card_fallback_border']
  .set_priority_badge(text, color=None)      # افتراضي: _C['text_neutral']
  .set_customer_name(name)     # setVisible(True/False) تلقائياً
  .set_info(parts: list)       # يمرر لـ InfoRow.set_parts()
  .add_stat_card(icon, title, value=None, color=None, compact=True) -> StatCard
  # value افتراضي: tr('amount_dash_placeholder') | color افتراضي: _C['blue']
  .clear_stat_cards()
  .add_action(text, callback=None, style="primary") -> QPushButton
  .toolbar -> ActionToolbar   # lazy property — يستدعي _ensure_toolbar()
```

---

## Notification

### `ui/widgets/components/notification.py`

```python
NotificationBar(show_dismiss=True)
# Signals: dismissed
  .show(message: str, level: str = "info", auto_hide: int = 0)
  # level: "success" | "info" | "warning" | "danger"
  # auto_hide > 0 → يُخفي تلقائياً بعد auto_hide milliseconds
  .hide_bar()
  # يوقف الـ timer ويُخفي الـ widget

BaseWarningBar(on_fix=None, on_edit=None,
               fix_text="🗑️ حذف الناقص", edit_text="✏️ تعديل",
               show_dismiss=True)
# Signals: fix_clicked, edit_clicked, dismissed
  .show_message(message, fix_text=None, edit_text=None)
  .show_orphans(orphans: list, product_name: str, type_labels: dict = None)
  # type_labels افتراضي: {"raw": "خامة", "semi": "نصف مصنع", ...}
  .hide_warning()
  .set_fix_visible(v: bool)
  .set_edit_visible(v: bool)
```

---

## Spinner

### `ui/widgets/components/spinner.py`

```python
_FRAMES = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]   # إطارات الأنيميشن

LoadingSpinner(text="جارٍ التحميل...", color=None, compact=False)
# color افتراضي: _C.get("accent", "#1565c0")
# interval: 100ms
  .start()       # setVisible(True) + يبدأ الـ timer
  .stop()        # يوقف الـ timer + يضع "✓"
  .set_text(text)
  .is_running() -> bool

LoadingOverlay(parent: QWidget = None)
# QFrame شفاف فوق أي widget
  .show_loading(text="جارٍ التحميل...")
  # يضبط الحجم على parent.size() لو موجود
  .hide_loading()
  # resizeEvent: يتزامن مع حجم الـ parent تلقائياً

LoadingButton(QPushButton)
  .set_loading(loading: bool, text=None)
  # loading=True: setEnabled(False) + يبدأ spinner
  # loading=False: setEnabled(True) + يعود للنص الأصلي
  .set_original_text(text)
```

---

## Stat Card

### `ui/widgets/components/stat_card.py`

```python
@dataclass
StatItem(label, color=_C["blue"] (factory), icon="", value=tr('dash') (factory),
         bg=None, border=None, bold_value=True, compact=False)
# color و value يُبنيان عبر field(default_factory=...) — يُقرآن وقت
# الإنشاء الفعلي لتجنب تجميد القيمة عند استيراد الموديول

StatCard(icon="", title="", value=None, color=None,
         bg=None, border=None, compact=False)
# color افتراضي: _C["blue"] (يُعاد ضبطه من _C في كل _refresh_style — لا يتجمد)
# value افتراضي: tr('dash') لو None
# ألوان bg/border من card_colors(color) لو لم تُحدَّدا صراحةً
  .set_value(text: str)
  .set_color(color: str)
  # يُحدّث _lbl_value و _lbl_title
  .value_label() -> QLabel

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

make_stat_row(*items: StatItem, separator=True, compact=False, bg=None) -> StatRow
stat_card_pair(label, color=None, icon="") -> tuple[QFrame, QLabel]
# color افتراضي: _C["blue"]
make_stat_card_simple(label, value=None, color=None, icon="") -> StatCard
# value افتراضي: tr('dash') | color افتراضي: _C["blue"]
```

**`StatRow` — [إصلاح dark-mode] الفواصل العمودية:**
```python
# StatRow نفسها لم تكن WidgetMixin أصلاً (لا اشتراك في bus.theme_changed) —
# الفواصل العمودية (v_divider) بين البطاقات كانت تتبنى ستايل ثابت وقت
# الإنشاء ولا تتحدث. الحل: WidgetMixin (font=False, lang=False, data=False)
# + _refresh_style() تعيد بناء كل ThemedFrame فاصل بلون _C['border_med']
# الحالي بنفس صيغة v_divider() الأصلية بالضبط.
```

---

## Badge

### `ui/widgets/components/badge.py`

```python
BadgeLabel()
# يرث من QLabel
# ألوان افتراضية: text_sec / bg_surface_2 / border
  .set_badge(text, text_color=None, bg=None, border=None)
  .clear_badge()
  # يُعيد الألوان الافتراضية
```

---

## Status Chip

### `ui/widgets/components/status_chip.py`

```python
StatusChip(icon="", label="", count=0, color="#6b7280",
           bg=None, border=None, compact=False)
# ألوان bg/border من card_colors(color) لو لم تُحدَّد
  .set_count(count: int)
  .count() -> int   # try int(text) / except → 0

make_status_chip(icon, label, count=0, color="#6b7280") -> StatusChip
```

---

## ActionToolbar

### `ui/widgets/components/action_toolbar.py`

```python
ActionToolbar(spacing=6)
# شريط أزرار أفقي بـ FlowLayout — الأزرار تنزل لسطر تاني تلقائياً
# الفواصل بين الأزرار العادية والـ danger أزرار تُبنى تلقائياً
  .add_action(text, style="normal", callback=None, enabled=True) -> QPushButton
  .add_danger(text, callback=None, enabled=True) -> QPushButton
  .add_separator()
  # يُضيف _SeparatorMarker (ليس QWidget) — يُبنى v_divider فعلي في _rebuild()
```

**`_rebuild()` — منطق إعادة البناء:**
```python
# يمسح كل الـ flow layout ثم يُعيد بناءه:
# 1. normal buttons مع separators بينها
# 2. v_divider بين normal و danger (لو الاثنان موجودان)
# 3. danger buttons
# يستدعي updateGeometry() في النهاية
```

---

## Constants — General

### `ui/widgets/components/constants_general.py`

> ⚠️ **[ملاحظة تسمية]** رغم اسم الملف الفعلي `constants_general.py` والمسار
> `ui/widgets/components/`، محتواه docstring داخلي يذكر `ui/constants_data/general.py`
> — على الأرجح أثر من نقل/إعادة هيكلة سابقة. المسار المعتمد فعلياً حسب
> `system_arch.txt` هو `ui/widgets/components/constants_general.py`. هذا
> الملف **جزء من تقسيم `ui/constants.py`** الأكبر — راجع `ui/constants/__init__.py`
> (خارج نطاق هذا المرجع) لكيفية تجميع كل هذه الثوابت الفرعية.

**الغرض:** يجمّع كل الثوابت الرقمية/الأبعاد المشتركة عبر واجهة المستخدم بالكامل
(أحجام خطوط، مسافات، هوامش، أبعاد لوحات وأزرار وجداول وحوارات ...) بحيث لا
يُكتب أي رقم "hardcoded" مباشرة داخل ملفات الـ widgets — كل شيء يُستورد من هنا.

**لا كلاسات ولا دوال — الملف بالكامل ثوابت module-level (`UPPER_CASE = value`)،**
مجمّعة تحت عناوين تعليقية (`# ── ... ───`). أبرز المجموعات:

```python
# حجم الخط
DEFAULT_FONT_SIZE = 11 ; MIN_FONT_SIZE = 8 ; MAX_FONT_SIZE = 20

# Sidebar
SIDEBAR_EXPANDED_WIDTH = 224 ; SIDEBAR_COLLAPSED_WIDTH = 56

# النافذة الرئيسية
CONTENT_MIN_WIDTH = 820
WINDOW_DEFAULT_W = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH
WINDOW_DEFAULT_H = 700 ; WINDOW_MIN_H = 500 ; WINDOW_MIN_CONTENT_W = 600

# Spacing (استخدم دائماً بدل أرقام hardcoded)
SPACING_XS=4  SPACING_SM=6  SPACING_MD=8  SPACING_LG=12  SPACING_XL=16
SPACING_ZERO=0  SPACING_MD_LG=10

# Margins (left, top, right, bottom)
MARGIN_ZERO=(0,0,0,0)  MARGIN_FORM=(8,8,8,8)  MARGIN_CONTENT_PANEL=(16,14,16,16)

# أبعاد Panels (BaseSection/BaseDetailPanel/BaseCrudForm)
LIST_PANEL_MIN_W=280  LIST_PANEL_MAX_W=560  DETAIL_PANEL_MIN_W=320
DETAIL_CONTENT_MIN_W=500  DETAIL_MIN_W=300  DETAIL_EMPTY_MIN_H=200
FORM_MIN_W=260  BTN_MIN_HEIGHT=30

# Dialog Shell
DIALOG_HDR_H_WITH_SUB=64  DIALOG_HDR_H=52  DIALOG_BTN_BAR_H=54
DIALOG_BTN_MIN_H=36  DIALOG_MIN_WIDTH=380
DIALOG_BODY_MARGINS=(20,16,20,12)  DIALOG_HDR_MARGIN_H=16
DIALOG_HDR_COL_SPACING=2  DIALOG_BTN_PAD_H=20  MSG_BTN_MIN_H=32

# Confirm Dialog
CONFIRM_BTN_MIN_H=34  CONFIRM_BTN_MIN_W=80  CONFIRM_MAX_WIDTH=520

# Splitter
SPLITTER_HANDLE_W=5  SPLITTER_HANDLE_BORDER_W=1  SPLITTER_RATIO=(1,2)
SPLITTER_APPLY_DELAY=50  SPLITTER_RETRY_DELAY=100

# Notifications / Timers
NOTIF_AUTO_HIDE_SUCCESS=3000  NOTIF_AUTO_HIDE_DEFAULT=0
REFRESH_AFTER_SAVE_DELAY=80

# Pagination Bar (BaseListPanel)
PAGINATION_BAR_H=44  PAGINATION_BTN_SPACING=10  PAGINATION_BTN_RADIUS=6
PAGINATION_BTN_PAD_H=14  PAGINATION_BTN_PAD_H_SM=8

# BaseListPanel
LIST_PANEL_MIN_W_DEFAULT=260  FILTER_DEBOUNCE_MS=250  LIST_EMPTY_MIN_H=100

# Tables (helpers عامة)
TABLE_EXTRA_PAD=24  COL_MIN_WIDTH=40  COL_MAX_WIDTH=300
TABLE_MIN_SECTION_SIZE=30  TABLE_MIN_HEIGHT_DEFAULT=120
TABLE_COMPACT_MAX_HEIGHT=300  TABLE_SPLITTER_MIN_HEIGHT=80
TABLE_SPLITTER_EXTRA_PAD=24  TABLE_SPLITTER_HANDLE_W=0
CALC_WIDTH_EXTRA_PAD=24  TABLE_COL_DEFAULT_W=100
TABLE_FIXED_COL_DEFAULT_W=100  TABLE_FIXED_WIDTH_PAD=4  TABLE_ROW_MIN_SECTION_PAD=4

# Splitter list panel (utils/splitter.py)
SPLITTER_LIST_MIN_W=280  SPLITTER_LIST_MAX_W=620
SMART_SPLITTER_HANDLE_W=4  SPLITTER_PANEL_MIN_W=200

# SearchableCombo
SEARCHABLE_COMBO_SEARCH_W=90  SEARCHABLE_COMBO_SEARCH_H=28
SEARCHABLE_COMBO_CLEAR_SIZE=20  SEARCHABLE_COMBO_CMB_MIN_W=150
SEARCHABLE_COMBO_INNER_RADIUS=4  SEARCHABLE_COMBO_PAD_H=6
SEARCHABLE_COMBO_PAD_V=2  SEARCHABLE_COMBO_SEARCH_DELAY=120

# DateRangeFilter
DATE_RANGE_EDIT_W=115  DATE_RANGE_EDIT_H=30  DATE_RANGE_EDIT_RADIUS=5
DATE_RANGE_EDIT_PAD_H=6  DATE_RANGE_EDIT_PAD_V=2  DATE_RANGE_DROPDOWN_W=20

LIST_W_OFFSET=60   # BaseSection._apply_sizes: LIST_MIN_W + LIST_W_OFFSET

# أبعاد widgets مخصصة
SEARCH_BAR_H=34  STATUS_BAR_H=24  SEARCH_BAR_BORDER_W=1.5
SEARCH_BAR_BORDER_RADIUS=6  SEARCH_BAR_PAD_H=10  STATUS_BAR_PAD_H=10
STATUS_BAR_BORDER_W=1  SECTION_BAR_W=3  SECTION_BAR_H=18  SECTION_BAR_RADIUS=2

# أزرار (components/button.py)
INPUT_HEIGHT_PAD=10  BTN_HEIGHT_PAD=8  BTN_PAD_H=14  BTN_BORDER_RADIUS=6
BTN_TEXT_PAD=32  BTN_BORDER_W=1.5  DROPDOWN_ARROW_W=24

# ListHeader / DetailHeader / PageHeader
LIST_HEADER_MARGIN_H=10  LIST_HEADER_MARGIN_T=10  LIST_HEADER_MARGIN_B=8
DETAIL_HEADER_MARGIN_H=20  DETAIL_HEADER_MARGIN_T=14
PAGE_HEADER_MARGIN_H=20  PAGE_HEADER_MARGIN_V=14
PAGE_HEADER_MARGIN_H_COMPACT=12  PAGE_HEADER_MARGIN_V_COMPACT=8

# Section header (DesignSection/CostingSection/AccountingSection)
SECTION_HEADER_HEIGHT=42  SECTION_HEADER_BORDER_W=1  SECTION_HEADER_PAD_RIGHT=16

# Notification / Warning bars
NOTIF_MARGIN_H=10  NOTIF_MARGIN_V=6  NOTIF_SPACING=8  NOTIF_BORDER_W=1
DISMISS_BTN_SIZE=22

# ProgressBar
PROGRESS_BAR_H=8  PROGRESS_TOP_SPACING=3
PROGRESS_THRESHOLD_SUCCESS=90  PROGRESS_THRESHOLD_NORMAL=60  PROGRESS_THRESHOLD_WARNING=30

# LoadingOverlay / LoadingSpinner
OVERLAY_MARGIN=20  SPINNER_FRAME_INTERVAL_MS=100  OVERLAY_BORDER_RADIUS=8

# Offer Form / Offers Tab / Offers Table / StatBox / StatCard / StatusChip / StatusCard
# (مجموعة كبيرة من الثوابت الخاصة بشاشات pricing/offers — أبعاد أعمدة، هوامش،
#  spacing لكل من: OfferForm, OffersTab, _OffersTable, StatBox, StatCard,
#  _StatCard, StatusChip, StatusCard — راجع الملف الفعلي للقيم الدقيقة،
#  كلها بنمط {WIDGET}_{PROPERTY}_{UNIT} ثابت الاتساق)

# ColorPickerWidget
COLOR_PICKER_PREVIEW_SIZE=28  COLOR_PICKER_PREVIEW_RADIUS=4

# FilterToolbar
FILTER_TOOLBAR_MARGIN_H=8  FILTER_TOOLBAR_MARGIN_V=6  FILTER_TOOLBAR_SPACING=8
FILTER_COMBO_MIN_H=28  FILTER_COMBO_MIN_W=160  FILTER_RESET_BTN_W=32
FILTER_SEARCH_H=28  FILTER_TOOLBAR_BORDER_RADIUS=6  FILTER_BAR_BORDER_RADIUS=8
TREE_BORDER_RADIUS=6  LIST_BORDER_RADIUS=4  TABLE_BORDER_RADIUS=8
FILTER_COMBO_BORDER_RADIUS=4  FILTER_COMBO_PAD_H=8  FILTER_CAT_ICON_W=20
FILTER_COUNT_LABEL_MIN_W=50

SEPARATOR_LINE_H=1   # h_divider الافتراضي

# DetailSection
DETAIL_SECTION_RADIUS=10  DETAIL_SECTION_MARGIN_B=12
DETAIL_SECTION_HDR_MARGIN_H=12  DETAIL_GRID_MARGIN_H=12
DETAIL_GRID_H_SPACING=16  DETAIL_GRID_V_SPACING=10  DETAIL_GRID_V_SPACING_C=6
DETAIL_GRID_PAD_COMPACT=4  DETAIL_GRID_PAD_NORMAL=6  DETAIL_LABEL_MIN_W=80
TWO_COL_H_SPACING=24  TWO_COL_V_SPACING=8

# FormFields / FormBadges / CategoryManager / FormGroup / CollapsibleCard / EmptyState
# (نفس النمط — راجع الملف الفعلي؛ كل الأسماء self-explanatory ومستخدمة في
#  الملفات الموثّقة بالمرجع تحت panels/*, managers/category.py)

INPUT_HEIGHT=32  SEARCH_INPUT_HEIGHT=34
SCROLL_BAR_WIDTH=6
TAB_MIN_W_SMALL=60  TAB_MIN_W_NORMAL=80
ROW_HEIGHT_COMPACT=34  ROW_HEIGHT_NORMAL=40  ROW_HEIGHT_LARGE=48

# ActionToolbar
ACTION_TOOLBAR_FLOW_V_SPACING=4  ACTION_TOOLBAR_MARGIN_V=4
ACTION_TOOLBAR_DEFAULT_SPACING=6  DETAIL_HEADER_TOOLBAR_SPACING=8

V_DIVIDER_WIDTH=1  V_DIVIDER_MARGIN_V=4  V_DIVIDER_INNER_MARGIN_H=0

# FlexibleTable / WrapDelegate (tables/flexible.py)
FLEX_WRAP_MIN_ROW_H=36  FLEX_WRAP_PADDING=4  FLEX_DEFAULT_COL_WIDTH=150
FLEX_TABLE_MIN_ROW_H=36  FLEX_ROW_HEIGHT_PAD=8

# Input styles (theme/input_styles.py)
INPUT_BORDER_RADIUS=6  INPUT_PAD_H=8  INPUT_BORDER_W=1  SEARCH_PAD_H=10

# Label styles (theme/label_styles.py)
STATUS_LABEL_RADIUS=4  STATUS_LABEL_PAD_V=2  STATUS_LABEL_PAD_H=8  LINK_BTN_RADIUS=4

# Sidebar nav (_NavButton, _sidebar, _ToggleButton, _SectionLabel)
NAV_BTN_H=38  NAV_BTN_W_OFFSET=16  NAV_ICO_W=22  NAV_ICO_FS=15
NAV_BTN_HEIGHT_PAD=14  BADGE_FS=8  SIDEBAR_COMPANY_H=46  SIDEBAR_TOGGLE_H=36
SIDEBAR_DIVIDER_H=1  SIDEBAR_SCROLL_W=3  SIDEBAR_SCROLL_MIN_H=20
NAV_LAYOUT_MARGIN_H=10  NAV_LAYOUT_SPACING=10  NAV_BTN_BORDER_RADIUS=6
NAV_BADGE_PAD_V=1  NAV_BADGE_PAD_H=6  NAV_BADGE_RADIUS=8  NAV_ACTIVE_BORDER_W=2
TAB_INDICATOR_BORDER_W=2
SECTION_LABEL_PAD_TOP=12  SECTION_LABEL_PAD_H=16  SECTION_LABEL_PAD_BOT=4
SECTION_LABEL_LTR_SPACING="1.5px"
SIDEBAR_NAV_MARGIN=8  SIDEBAR_NAV_SPACING=1  SIDEBAR_FOOTER_MARGIN_H=8
SIDEBAR_FOOTER_MARGIN_V=4  SIDEBAR_FOOTER_SPACING=1  SIDEBAR_DIV_MARGIN_V=2
SIDEBAR_DIV_MARGIN_H=4  SIDEBAR_ANIM_DURATION=200  SIDEBAR_TOGGLE_BORDER_W=1
SIDEBAR_SCROLL_RADIUS=1  SIDEBAR_BORDER_W=1

# Pricing Panel (_PricingPanel) — مجموعة PRICING_PANEL_* لأبعاد فورم التسعير كاملة
```

> **ملاحظة استخدام:** أي widget جديد في المشروع يحتاج بُعداً/مسافة معيارية
> يجب أن **يستورد الثابت من هنا** (`from ui.constants import X`) بدل كتابة
> رقم مباشر — هذا هو العقد غير المكتوب المتبع في كل ملفات `ui/widgets/*`
> المذكورة في هذا المرجع وغيره.

---

## ComponentRow — Widget

### `ui/widgets/components/component_row/widget.py`

```python
ComponentRow(catalog_fn, child_type="raw", child_id=None,
             qty=1.0, waste_pct=0.0, raw_total_qty=None,
             show_total_qty=False, variant_id=None,
             machine_op_row_id=None)
# Signals: removed(QWidget)
```

**Instance variables (state):**
```python
_catalog_fn            # callable يُرجع الـ catalog الحالي (dict)
_show_total_qty        # bool
_conn_cache            # connection cache — بدون SELECT 1 في الـ hot path
_pinned_type           # النوع المحدد حالياً
_pinned_id             # ID العنصر المحدد
_pinned_variant        # variant_id المحدد
_pinned_op_row_id      # machine_op_row_id المحدد
_init_machine_op_row_id
_init_child_type       # النوع الأولي عند الإنشاء
_init_child_id         # ID الأولي عند الإنشاء
_skip_timer_load       # يمنع QTimer من إعادة التحميل عند expose_load_op_rows
_conn_cache            # connection cache — بدون SELECT 1 في الـ hot path
_orphan                # _OrphanState dataclass
```

**`_OrphanState` dataclass:**
```python
@dataclass
class _OrphanState:
    active  : bool = False
    item_id : int | None = None
    type_   : str | None = None
    name    : str | None = None

    .clear()
    .display() -> str   # "⚠️  «name»محذوف  (ID: item_id)"
    .tooltip() -> str   # رسالة تحذير كاملة
```

**Attributes على الـ widget (UI):**
`cmb_type`, `_item_combo`, `cmb_variant`, `lbl_variant_cost`, `qty_edit`,
`waste_spin`, `lbl_waste`, `total_qty_edit`, `lbl_total_qty`, `cmb_op_row`,
`lbl_op_row_cost`, `_sub_row_widget`, `cmb_item` (property — alias لـ `_item_combo.cmb`)

**Methods:**
```python
.get_values() -> tuple | None
# (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
# يرجع None لو data is None أو orphan أو ValueError في qty

.get_waste_pct() -> float
.get_variant_id() -> int | None
.get_machine_op_row_id() -> int | None
.is_orphan() -> bool
.set_orphan_name(name: str | None)
.refresh_catalog(_new_catalog: dict = None)

.expose_load_op_rows(op_id, selected_row_id=None)
# synchronous — يمنع QTimer من إعادة التحميل (_skip_timer_load = True)
# يُستدعى من product_form عند تحميل سيناريو من DB

._refresh_cost_label()
# [E-03] يُحدِّث lbl_variant_cost من الـ catalog الجديد بعد تغيير سعر الخامة
# فقط لو _pinned_type == "raw" وليس orphan
# يبحث عن child_id في catalog["raw"]: entry = (id, name, cat, price, total_qty)
# unit_cost = price/total_qty لو total_qty > 0 وإلا price نفسه
# يضبط setText + tooltip (component_row_cost_tooltip) على lbl_variant_cost
# يُستدعى من _on_catalog_changed() و _refresh_data()

._refresh_data(company_id=None)
# [WidgetMixin] hook مرتبط بـ bus.company_data_changed عبر _init_widget_mixin
# يمسح _conn_cache ثم يجدول _on_catalog_changed() عبر QTimer.singleShot(0, ...)

._on_catalog_changed()
# يتحقق أن _pinned_type ضمن الأنواع الصالحة (أو يأخذه من cmb_type.currentData())
# لو مش orphan: يحدّث _pinned_id من الاختيار الحالي في _item_combo
# يستدعي _refresh_items() ثم _refresh_cost_label()

._is_widget_deleted(*widgets) -> bool
# مشتركة بين OpRowsMixin و VariantsMixin — sip.isdeleted()
# تتحقق من حذف self أولاً ثم أي من الـ widgets المعطاة
# عند أي exception → True (الاختيار الآمن)

._get_conn()
# يرجع connection من _conn_cache مباشرة بدون SELECT 1
# لو _conn_cache = None → [إصلاح هيكلة] يستدعي
#   CompanyService.get_active_erp_conn() (بدل db.shared.connection.get_connection()
#   المباشر القديم) ويُخزّن النتيجة في _conn_cache — نفس نمط _fetch_op_rows/
#   _fetch_variants في OpRowsMixin/VariantsMixin اللي بتمر عبر services/
# أي Exception → يرجع None بصمت
# لا يستخدم SELECT 1 تجنباً للـ overhead في hot path
```

**[WidgetMixin] الربط بالـ bus:**
```python
# [إصلاح] استُبدل الربط اليدوي بـ weakref (القديم: bus.data_changed +
# _bus_slot/_bus_slot_company + _disconnect_bus في closeEvent) بالكامل
# بـ WidgetMixin._init_widget_mixin القياسي:
QTimer.singleShot(
    0,
    lambda: self._init_widget_mixin(theme=True, font=False, lang=True, data=True),
)
# تأجيل بـ QTimer.singleShot(0) يحافظ على نفس توقيت التأجيل الأصلي.
# لا closeEvent مخصص، لا فصل يدوي — WidgetMixin يدير كل شيء بـ weakref داخلياً.
```

**[إصلاح 6 - إضافي] `_refresh_style(*_)`:**
```python
# [Fix - dark theme waste_spin] كانت theme=False وقت الإنشاء، فعناصر مبنية
# بستايل ثابت وقت الإنشاء فقط (waste_spin, cmb_variant, lbl_variant_cost,
# cmb_op_row, lbl_op_row_cost, lbl_waste, lbl_total_qty, sub_row) ما كانتش
# تتحدث عند تغيير الثيم. الحل: theme=True + _refresh_style() تعيد بناء كل
# هذه الستايلات من ألوان _C الحالية (تستدعي update_waste_style + دوال
# الستايل من ui.py: _variant_combo_style, _variant_cost_style,
# _op_row_combo_style, _sub_row_style)
```

**`_refresh_lang(*_)`:**
```python
# [i18n] يحدّث: tooltip/label الـ orphan (لو نشط)، تكلفة الخامة وtooltip‌ها،
# ثم يفوّض لـ OpRowsMixin/VariantsMixin لتحديث كومبوهات/labels التكلفة
# الداخلية بتاعتهم (لأنها تستخدم tr() أيضاً)
```

**[إصلاح 6] `_on_type_changed`:**
```python
# عند تغيير النوع عن "raw":
#   1. يستدعي _hide_variants()       ← يُخفي cmb_variant + lbl_variant_cost
#   2. يُخفي lbl_variant_cost صراحةً (cost_label.setVisible(False))
#      ← ضمان إضافي لحالة عدم وجود variants محملة
# المشكلة القديمة: _hide_variants() قد لا تُخفي lbl_variant_cost
#                  لو لم تكن variants محملة أصلاً
```

---

## ComponentRow — UI

### `ui/widgets/components/component_row/ui.py`

```python
build_row_ui(widget, child_type, child_id, qty, raw_total_qty,
             waste_pct, variant_id, machine_op_row_id, show_total_qty)
# كل الألوان من _C و status_colors() — لا hardcoded

update_waste_style(widget, val: float)
# val > 0 → يُظهر lbl_waste + يطبق waste_colors() على waste_spin
# val == 0 → يُخفي lbl_waste + يطبق _waste_zero_style()
# يستخدم waste_colors() و waste_zero_*() من core/colors

get_orphan_style() -> str
# [Phase 5] دالة بدل ثابت — تُحسَب في كل استخدام من _C الحالي
# تضمن أن الألوان تعكس الثيم الحالي دائماً عند تغيير الثيم

COMPONENT_TYPES = [
    ("raw",        "🧱 خامة"),
    ("semi",       "🔧 نصف مصنع"),
    ("labor_op",   "👷 عملية عمالة"),
    ("machine_op", "⚙️ عملية تشغيل"),
]
STYLE_NORMAL = ""
STYLE_ORPHAN = ...   # legacy ثابت يُحسب عند أول import — استخدم get_orphan_style() بدله
```

**[إصلاح ألوان]:**
- `_variant_combo_style()` و `_variant_cost_style()` يستخدمان `_C["input_positive_*"]` بدل hardcoded green.
- `_waste_zero_style()` يستخدم `waste_zero_*()` من core/colors بدل ثوابت hardcoded.
- `_op_row_combo_style()` يستخدم `status_colors("purple")` من core/colors.

---

## ComponentRow — OpRows

### `ui/widgets/components/component_row/op_rows.py` — `OpRowsMixin`

```python
.expose_load_op_rows(op_id, selected_row_id=None)
# synchronous — للاستدعاء الخارجي من product_form
# يضبط _skip_timer_load = True لمنع timer إعادة التحميل

._ensure_machine_op_rows()
._hide_op_rows()
._load_op_rows(op_id, selected_row_id=None)
# أولوية الاختيار (explicit is not None checks — لا or):
# 1. selected_row_id  (is not None)
# 2. _init_machine_op_row_id  (is not None)
# 3. _pinned_op_row_id  (is not None)
# 4. الصف الأول (fallback)

._on_op_row_changed(_index=0)
._update_op_row_cost_label()
._is_op_row_deleted() -> bool
# يستخدم _is_widget_deleted المشتركة من widget.py
```

**[إصلاح هيكلة]:** يستورد من `services/costing/machine_op_rows_service` بدل `db/` مباشرة.

**[إصلاح `_determine_target_id`]:** يستخدم `is not None` بدل `or`:
```python
# القديم (خطأ): selected_row_id or self._init_... or self._pinned_...
# المشكلة: ID = 0 يُتخطى بسبب سلوك or في Python
# الجديد: فحص صريح is not None لكل قيمة بالترتيب
if selected_row_id is not None: return selected_row_id
if self._init_machine_op_row_id is not None: return self._init_machine_op_row_id
return self._pinned_op_row_id
```

---

## ComponentRow — Variants

### `ui/widgets/components/component_row/variants.py` — `VariantsMixin`

```python
._load_variants(item_id, selected_variant_id=None)
._hide_variants()
# تُخفي cmb_variant و lbl_variant_cost معاً
._on_variant_changed()
._update_variant_cost_label()
._is_variant_deleted() -> bool
# يستخدم _is_widget_deleted المشتركة من widget.py
```

**[إصلاح هيكلة]:** يستورد من `services/costing/variant_service` بدل `db/` مباشرة:
- `get_variants_for_item(conn, item_id)` بدل `fetch_variants_for_item`
- `get_variant_unit_cost(conn, variant_id, item_id)` بدل SQL مباشر
- `get_item_price(conn, item_id)` بدل SQL مباشر

**`_populate_variant_combo` — منطق العرض:**
```python
# يُضيف "─ بدون variant ─" كأول خيار (data=None)
# لكل variant: يحسب unit_cost = item_price / pieces لو pieces > 0 و item_price > 0
# يُعيد اختيار selected_id لو موجود
# يستخدم blocked_signals() من utils/signals أثناء التعبئة
```

---

## علاقات الملفات

- `component_row/widget.py` (`ComponentRow`) يجمع `OpRowsMixin` (من `op_rows.py`) و `VariantsMixin` (من `variants.py`) معاً — كلاهما يعتمد على `_is_widget_deleted()` و `_get_conn()` المعرَّفتين في `widget.py` نفسه (وليس داخل الـ mixins).
- `component_row/ui.py` (`build_row_ui`, `update_waste_style`, `get_orphan_style`, `COMPONENT_TYPES`) يُستدعى من `widget.py` لبناء واجهة الصف بالكامل، ومن `op_rows.py`/`variants.py` بشكل غير مباشر عبر دوال الستايل (`_variant_combo_style`, `_variant_cost_style`, `_op_row_combo_style`, `_sub_row_style`) التي يستدعيها `widget.py._refresh_style()`.
- `headers_page.py` (`DetailHeader.toolbar`) يستورد `ActionToolbar` من `action_toolbar.py` بشكل lazy (داخل `_ensure_toolbar()`) لتفادي استيراد دائري.
- `action_toolbar.py` يستورد `make_btn` من `button.py` و `v_divider` من `theme/builders.py` (مرجع: `ui_widgets_theme.md`).
- `stat_card.py` (`DetailHeader.add_stat_card`) يُستدعى من `headers_page.py` عبر lazy import محلي.
- `notification.py` (`BaseWarningBar`) يستورد `make_btn` من `button.py`.
- كل الملفات في هذا المرجع تقريباً تعتمد على `WidgetMixin` من `core/widget_mixin.py` (مرجع: `ui_widgets_core.md`) و `tr()` من `core/i18n.py`، و `_C` من `ui/theme.py` (خارج نطاق `ui/widgets/`).
- `component_row/op_rows.py` و `component_row/variants.py` يستوردان `blocked_signals` من `utils/signals.py` (مرجع: `ui_widgets_utils.md`).
- `component_row/widget.py` يستورد `SearchableCombo` و `build_grouped_items` من `utils/searchable_combo.py` (مرجع: `ui_widgets_utils.md`).
- `constants_general.py` هو مصدر كل ثوابت الأبعاد (`SPACING_*`, `*_MIN_H`, إلخ) المستخدمة عبر كل ملفات هذا المرجع تقريباً — علاقة استيراد شبه شاملة وليست ثنائية محددة.
- `ui/widgets/helpers/color_picker.py` (مسار مختلف — مرجع منفصل: `ui_widgets_helpers.md`) يستورد `make_btn` من هذا المرجع (`components/button.py`) — تبعية خارجية واحدة فقط، لا علاقة عكسية.
---

## المستدعون الرئيسيون من خارج هذا المرجع

- `button.py` (`StyledButton`): يُستخدم في كل `tabs/*` و`widgets/*` — `invalidate_stylesheet_cache` يُستدعى من `apply_font()` (`ui/root.md`)
- `headers_page.py` (`DetailHeader`, `PageHeader`): يُستخدم من `BaseDetailPanel` (`ui_widgets_base.md`) وكل detail panels في tabs/
- `headers_list.py` (`ListHeader`, `StatusBar`): يُستخدم من `BaseListPanel` (`ui_widgets_base.md`)
- `notification.py` (`NotificationBar`): يُستخدم من `BaseDetailPanel` وأي form يحتاج إشعارات
- `label.py` (`ModeLabel`): يُستخدم من `managers/category.py` (`ui_widgets_managers.md`) وforms/
- `component_row/widget.py`: يُستدعى من `product_form` في `ui/tabs/costing/product/` (مؤكَّد من كود التعليقات)
- `BomTree`: يُستخدم من `product_main_panel.py` و`_orphan_handler.py` (مؤكَّد من `ui_tabs_costing.md`)
- `ScenarioEditor`: يُستدعى من `product_form` عند تحميل سيناريو من DB (مؤكَّد من التعليقات)
