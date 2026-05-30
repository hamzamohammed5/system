# دليل الكود — UI / Widgets (7): Core Utilities & ComponentRow

> الجزء السابع — أدوات النواة المشتركة وصف مكوّنات BOM.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [Core — Colors](#core--colors) | `widgets/core/colors` |
| [Core — Events](#core--events) | `widgets/core/events` |
| [Core — Conn](#core--conn) | `widgets/core/conn` |
| [Core — Guard](#core--guard) | `widgets/core/guard` |
| [ComponentRow](#componentrow) | `components/component_row/widget`, `ui`, `op_rows`, `variants` |

---

## Core — Colors

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
# ملاحظة: الـ import داخل الدالة (lazy) مقصود لتجنب circular imports

waste_level(pct: float) -> str   # "high" | "medium" | "low" | "zero"
waste_colors(pct: float) -> tuple[str, str]

WASTE_COLORS = {
    "high":   ("#ffcdd2", "#e53935"),   # >= 20%
    "medium": ("#ffe0b2", "#f57c00"),   # >= 10%
    "low":    ("#fff8e1", "#ffe082"),   # > 0%
}
WASTE_ZERO_BG     = "#f5f5f5"
WASTE_ZERO_BORDER = "#e0e0e0"
WASTE_ZERO_COLOR  = "#999"
WASTE_TEXT_COLOR  = "#e65100"
```

**إضافة purple/orange لـ `_C`** (في `app_settings.py`) للتزامن الكامل مع الثيم:
```python
"purple":        "#6a1b9a",
"purple_bg":     "#f3e5f5",
"purple_border": "#ce93d8",
"orange":        "#e65100",
"orange_bg":     "#fff3e0",
"orange_border": "#ffcc80",
```

---

## Core — Events

### `ui/widgets/core/events.py`

```python
get_active_company_id() -> int | None
# يقرأ company_state.company_id — يرجع None لو غير جاهز

emit_company_data_changed()
# يُطلق bus.company_data_changed(cid) لو توجد شركة نشطة
# وإلا يُطلق bus.data_changed()
# المصدر الوحيد الصحيح لإطلاق أحداث تغيير البيانات

is_same_company(company_id: int) -> bool
# يقارن company_id بالشركة النشطة الحالية
```

**الاستخدام الصحيح:**
```python
# ✅ الصح — مقيّد بالشركة
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()

# ❌ تجنّب — للتوافق القديم فقط
from ui.events import bus
bus.data_changed.emit()
```

---

## Core — Conn

### `ui/widgets/core/conn.py`

#### `LiveConnMixin`

```python
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
```

**تحذير `_conn_attr`:**
```python
# لو subclass يستخدم اسماً مختلفاً:
class MyWidget(QWidget, LiveConnMixin):
    _conn_attr = "erp_conn"   # ضروري!

    def __init__(self):
        self.erp_conn = get_erp_connection()
```

#### `SafeConnMixin`

```python
._init_safe_conn(conn, db_name="accounting")
._get_safe_conn() -> Connection      # RuntimeError لو فشل
._get_company_id() -> int | None
._should_respond_to_company(company_id, stored_attr="_company_id") -> bool
```

#### `DualConnMixin(SafeConnMixin)`

```python
._init_dual_conn(acc_conn, erp_conn, acc_db="accounting")
._get_erp_conn() -> Connection       # RuntimeError لو فشل
._on_dual_company_event(company_id) -> bool
```

---

## Core — Guard

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
```

يعرض التحذير عبر (بالترتيب): `show_warning()` → `_warn()` → `_notif.show()` → debug log.

---

## ComponentRow

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
# يُحدِّث lbl_variant_cost من الـ catalog الجديد بعد تغيير سعر الخامة
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
    ("raw",        "🧱 خامة"),
    ("semi",       "🔧 نصف مصنع"),
    ("labor_op",   "👷 عملية عمالة"),
    ("machine_op", "⚙️ عملية تشغيل"),
]
STYLE_NORMAL = ""
STYLE_ORPHAN = ...   # يُبنى من status_colors("warning") — يتغير مع الثيم
```

---

### `ui/widgets/components/component_row/op_rows.py` — `OpRowsMixin`

```python
.expose_load_op_rows(op_id, selected_row_id=None)
# يُستدعى من الخارج (product_form) عند تحميل سيناريو من DB
# يعمل synchronously ويمنع QTimer من إعادة التحميل

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