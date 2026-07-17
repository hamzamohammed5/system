# دليل الكود — UI / Widgets (3): Components

> `ui/widgets/components/` — كل مكونات الواجهة القابلة لإعادة الاستخدام.
> يشمل: Button, Labels, Headers, Notification, Spinner, Stats, Badges, ActionToolbar, ColorPicker, ComponentRow.

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
| [ColorPicker](#colorpicker) | `helpers/color_picker.py` |
| [ComponentRow — Widget](#componentrow--widget) | `components/component_row/widget.py` |
| [ComponentRow — UI](#componentrow--ui) | `components/component_row/ui.py` |
| [ComponentRow — OpRows](#componentrow--oprows) | `components/component_row/op_rows.py` |
| [ComponentRow — Variants](#componentrow--variants) | `components/component_row/variants.py` |

---

## Button

### `ui/widgets/components/button.py`

```python
make_btn(text: str, style: str = "normal", fixed_size: bool = True) -> QPushButton
# style: "primary" | "success" | "danger" | "ghost" | "normal"
# يحفظ style على الزر كـ Qt property ("_btn_style") لـ refresh_visible_buttons
# fixed_size=True → setFixedWidth | False → setMinimumWidth (قابل للتمدد)
# ألوان الأزرار تُقرأ من _C — تتغير مع الثيم

invalidate_stylesheet_cache()
# يمسح _stylesheet_cache — يُستدعى من apply_font() وعند تغيير الثيم

refresh_visible_buttons(root_widget) -> int
# يستدعي invalidate_stylesheet_cache() أولاً
# يُعيد تطبيق stylesheet على كل QPushButton في الـ widget tree
# يعتمد على property("_btn_style")
# يتجاهل RuntimeError (widget محذوف) بصمت
# يرجع عدد الأزرار المحدثة

calc_btn_width(text: str, font_size: int, padding: int = 32) -> int
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
# ActionToolbar يُنشأ بـ lazy initialization — فقط عند أول استخدام فعلي
# _ensure_toolbar() ينشئ ActionToolbar ويُضيفه لـ _tb_section ويُظهره
  .set_title(text)
  .set_type_badge(text, color=None)
  .set_status_badge(text, text_color="#555", bg="#f5f5f5", border="#e0e0e0")
  .set_priority_badge(text, color="#6b7280")
  .set_customer_name(name)     # setVisible(True/False) تلقائياً
  .set_info(parts: list)       # يمرر لـ InfoRow.set_parts()
  .add_stat_card(icon, title, value="─", color="#1565c0", compact=True) -> StatCard
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
StatItem(label, color="#1565c0", icon="", value="─",
         bg=None, border=None, bold_value=True, compact=False)

StatCard(icon="", title="", value="─", color="#1565c0",
         bg=None, border=None, compact=False)
# ألوان bg/border من card_colors(color) لو لم تُحدَّد
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
stat_card_pair(label, color, icon="") -> tuple[QFrame, QLabel]
make_stat_card_simple(label, value="─", color="#1565c0", icon="") -> StatCard
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

## ColorPicker

### `ui/widgets/helpers/color_picker.py`

```python
ColorPickerWidget(default="#607d8b", btn_text="اختر لون")
# Signals: color_changed(str) — hex string
  .current_color() -> str
  .set_color(color: str)
```

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
_bus_slot              # مرجع slot الـ data_changed — يُحفظ لفصله في closeEvent [A-06]
_bus_slot_company      # مرجع slot الـ company_data_changed — يُحفظ لفصله [A-06]
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
# يحسب unit_cost = price / total_qty لو total_qty > 0 وإلا price
# يُستدعى من _on_catalog_changed()

._disconnect_bus()
# [A-06] يفصل _bus_slot و _bus_slot_company من bus صريحاً
# يُستدعى تلقائياً من closeEvent()

._is_widget_deleted(*widgets) -> bool
# مشتركة بين OpRowsMixin و VariantsMixin — sip.isdeleted()
# تتحقق من حذف self أولاً ثم أي من الـ widgets المعطاة
# عند أي exception → True (الاختيار الآمن)

._get_conn()
# يرجع connection من _conn_cache مباشرة بدون SELECT 1
# لو _conn_cache = None → يستدعي get_connection() ويُخزّن النتيجة
# لا يستخدم SELECT 1 تجنباً للـ overhead في hot path
```

**[A-06] Bus connection:**
```python
# يشترك في bus.data_changed + bus.company_data_changed  ← [FIX-4]
# يستخدم weakref لمنع dangling reference
# slots محفوظة في _bus_slot و _bus_slot_company
# تُفصل في closeEvent() عبر _disconnect_bus()
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