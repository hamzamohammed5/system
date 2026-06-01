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
# يُعيد تطبيق stylesheet على كل QPushButton في الـ widget tree
# يعتمد على property("_btn_style")
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

---

## Label

### `ui/widgets/components/label.py`

```python
InfoRow(separator="  ·  ")
  .set_parts(parts: list)   # يُرشح القيم الفارغة تلقائياً
  .set_text(text)
  .label() -> QLabel

ModeLabel(add_text="جديد", icon="")
  .set_add_mode(text=None)   # أزرق — وضع الإضافة
  .set_edit_mode(name="")    # برتقالي — وضع التعديل
  .set_custom(text, color=None)
  .is_edit_mode -> bool
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
  .set_color(color)
  .value() -> float
  .reset()
  # resizeEvent: يُعيد حساب عرض الـ fill تلقائياً

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
# يشترك في bus.language_changed تلقائياً
# Signals: search_changed(str)
  .text() -> str
  .clear()
  .set_placeholder(text: str)
  .inp -> QLineEdit

StatusBar()
  .set_count(shown: int, total: int)
  .set_text(text: str)
  .clear_count()

ListHeader(title="", add_text="", show_search=True,
           search_placeholder="", search_delay=250)
# يشترك في bus.language_changed لتحديث placeholder تلقائياً
# Signals: search_changed(str), add_clicked
  .add_action(text, callback=None, style="normal") -> QPushButton
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
  .set_title(text)
  .set_type_badge(text, color=None)
  .set_status_badge(text, text_color="#555", bg="#f5f5f5", border="#e0e0e0")
  .set_priority_badge(text, color="#6b7280")
  .set_customer_name(name)
  .set_info(parts: list)
  .add_stat_card(icon, title, value="─", color="#1565c0", compact=True) -> StatCard
  .clear_stat_cards()
  .add_action(text, callback=None, style="primary") -> QPushButton
  .toolbar -> ActionToolbar   # lazy property
```

---

## Notification

### `ui/widgets/components/notification.py`

```python
NotificationBar(show_dismiss=True)
# Signals: dismissed
  .show(message: str, level: str = "info", auto_hide: int = 0)
  # level: "success" | "info" | "warning" | "danger"
  .hide_bar()

BaseWarningBar(on_fix=None, on_edit=None,
               fix_text="🗑️ حذف الناقص", edit_text="✏️ تعديل",
               show_dismiss=True)
# Signals: fix_clicked, edit_clicked, dismissed
  .show_message(message, fix_text=None, edit_text=None)
  .show_orphans(orphans: list, product_name: str, type_labels: dict = None)
  .hide_warning()
  .set_fix_visible(v: bool)
  .set_edit_visible(v: bool)
```

---

## Spinner

### `ui/widgets/components/spinner.py`

```python
LoadingSpinner(text="جارٍ التحميل...", color=None, compact=False)
  .start()
  .stop()
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

## Stat Card

### `ui/widgets/components/stat_card.py`

```python
@dataclass
StatItem(label, color="#1565c0", icon="", value="─",
         bg=None, border=None, bold_value=True, compact=False)

StatCard(icon="", title="", value="─", color="#1565c0",
         bg=None, border=None, compact=False)
  .set_value(text: str)
  .set_color(color: str)
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
  .set_badge(text, text_color=None, bg=None, border=None)
  .clear_badge()
```

---

## Status Chip

### `ui/widgets/components/status_chip.py`

```python
StatusChip(icon="", label="", count=0, color="#6b7280",
           bg=None, border=None, compact=False)
  .set_count(count: int)
  .count() -> int

make_status_chip(icon, label, count=0, color="#6b7280") -> StatusChip
```

---

## ActionToolbar

### `ui/widgets/components/action_toolbar.py`

```python
ActionToolbar(spacing=6)
# شريط أزرار أفقي بـ FlowLayout — الأزرار تنزل لسطر تاني تلقائياً
  .add_action(text, style="normal", callback=None, enabled=True) -> QPushButton
  .add_danger(text, callback=None, enabled=True) -> QPushButton
  .add_separator()
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
# يستخدم weakref في bus slot لمنع dangling reference
# _bus_slot محفوظ كـ instance variable ويُفصل في closeEvent()
# _get_conn(): يثق في الـ cache مباشرة بدون SELECT 1 overhead

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
# يُحدِّث lbl_variant_cost من الـ catalog الجديد بعد تغيير سعر الخامة

._disconnect_bus()
# يفصل الـ slots من bus صريحاً — يُستدعى تلقائياً من closeEvent()

._is_widget_deleted(*widgets) -> bool
# مشترك بين OpRowsMixin و VariantsMixin — sip.isdeleted()
```

**Attributes على الـ widget:**
`cmb_type`, `_item_combo`, `cmb_variant`, `lbl_variant_cost`, `qty_edit`,
`waste_spin`, `lbl_waste`, `total_qty_edit`, `lbl_total_qty`, `cmb_op_row`,
`lbl_op_row_cost`, `_sub_row_widget`, `cmb_item` (alias لـ `_item_combo.cmb`)

---

## ComponentRow — UI

### `ui/widgets/components/component_row/ui.py`

```python
build_row_ui(widget, child_type, child_id, qty, raw_total_qty,
             waste_pct, variant_id, machine_op_row_id, show_total_qty)
# كل الألوان من _C و status_colors() — لا hardcoded

update_waste_style(widget, val: float)
# يستخدم waste_colors() و waste_zero_*() من core/colors

get_orphan_style() -> str
# [Phase 5] دالة بدل ثابت — تُحسب في كل استخدام من _C الحالي

COMPONENT_TYPES = [
    ("raw",        "🧱 خامة"),
    ("semi",       "🔧 نصف مصنع"),
    ("labor_op",   "👷 عملية عمالة"),
    ("machine_op", "⚙️ عملية تشغيل"),
]
STYLE_NORMAL = ""
STYLE_ORPHAN = ...   # legacy ثابت — استخدم get_orphan_style() بدله
```

---

## ComponentRow — OpRows

### `ui/widgets/components/component_row/op_rows.py` — `OpRowsMixin`

```python
.expose_load_op_rows(op_id, selected_row_id=None)
# synchronous — للاستدعاء الخارجي من product_form

._ensure_machine_op_rows()
._hide_op_rows()
._load_op_rows(op_id, selected_row_id=None)
# أولوية الاختيار:
# selected_row_id → _init_machine_op_row_id → _pinned_op_row_id → أول صف

._on_op_row_changed(_index=0)
._update_op_row_cost_label()
._is_op_row_deleted() -> bool
```

**ملاحظة [إصلاح هيكلة]:** يستورد من `services/costing/machine_op_rows_service` بدل `db/` مباشرة.
**ملاحظة [إصلاح]:** `_determine_target_id` يستخدم `is not None` بدل `or` لتجنب مشكلة ID = 0.

---

## ComponentRow — Variants

### `ui/widgets/components/component_row/variants.py` — `VariantsMixin`

```python
._load_variants(item_id, selected_variant_id=None)
._hide_variants()
._on_variant_changed()
._update_variant_cost_label()
._is_variant_deleted() -> bool
```

**ملاحظة [إصلاح هيكلة]:** يستورد من `services/costing/variant_service` بدل `db/` مباشرة.