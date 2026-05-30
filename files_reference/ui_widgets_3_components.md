# دليل الكود — UI / Widgets (3): Components

> الجزء الثالث — مكونات الواجهة القابلة لإعادة الاستخدام: أزرار، لوحات رأس، إشعارات، مؤشرات تحميل، بطاقات إحصائية.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [Button](#button) | `components/button` |
| [Label](#label) | `components/label` |
| [Headers](#headers) | `components/headers` |
| [Notification](#notification) | `components/notification` |
| [Spinner](#spinner) | `components/spinner` |
| [StatRow](#statrow) | `components/stat_row` |
| [ActionToolbar](#actiontoolbar) | `components/action_toolbar` |
| [ColorPicker](#colorpicker) | `helpers/color_picker` |

---

## Button

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

**مثال مع الثيم واللغة:**
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

## Label

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

## Headers

### `ui/widgets/components/headers.py`

```python
SearchBar(placeholder="", delay_ms=250, height=34)
# placeholder افتراضي من tr("list_search_placeholder")
# Signals: search_changed(str)
  .text() -> str
  .clear()
  .set_placeholder(text: str)
  .inp -> QLineEdit

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
# يشترك في bus.language_changed لتحديث placeholder تلقائياً
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

## Notification

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

## Spinner

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

## StatRow

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

## ActionToolbar

### `ui/widgets/components/action_toolbar.py`

```python
ActionToolbar(spacing=6)
# شريط أزرار أفقي بـ FlowLayout — الأزرار تنزل لسطر تاني تلقائياً
  .add_action(text, style="normal", callback=None, enabled=True) -> QPushButton
  .add_danger(text, callback=None, enabled=True) -> QPushButton
  .add_separator()
  # فاصل مرئي بين الأزرار العادية
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