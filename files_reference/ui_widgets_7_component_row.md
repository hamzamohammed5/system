# دليل الكود — UI / Widgets (7): ComponentRow

> `ui/widgets/components/component_row/` — صف مكوّنات BOM.
> لـ core/ (colors, events, conn, guard) → راجع `ui_widgets_1_app_settings.md`

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [ComponentRow — Widget](#componentrow--widget) | `components/component_row/widget.py` |
| [ComponentRow — UI](#componentrow--ui) | `components/component_row/ui.py` |
| [ComponentRow — OpRows](#componentrow--oprows) | `components/component_row/op_rows.py` |
| [ComponentRow — Variants](#componentrow--variants) | `components/component_row/variants.py` |

---

## ComponentRow — Widget

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
# لا يفعل شيئاً لو: النوع ليس "raw"، أو orphan، أو لا يوجد child_id

._disconnect_bus()
# يفصل _bus_slot من bus.data_changed صريحاً
# يُستدعى تلقائياً من closeEvent()

._is_widget_deleted(*widgets) -> bool
# مشترك بين OpRowsMixin و VariantsMixin — sip.isdeleted()
```

**Attributes:**
`cmb_type`, `_item_combo`, `cmb_variant`, `lbl_variant_cost`, `qty_edit`,
`waste_spin`, `lbl_waste`, `total_qty_edit`, `lbl_total_qty`, `cmb_op_row`,
`lbl_op_row_cost`, `_sub_row_widget`, `cmb_item` (alias لـ `_item_combo.cmb`)

---

## ComponentRow — UI

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

## ComponentRow — OpRows

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

## ComponentRow — Variants

### `ui/widgets/components/component_row/variants.py` — `VariantsMixin`

```python
._load_variants(item_id, selected_variant_id=None)
._hide_variants()
._on_variant_changed()
._update_variant_cost_label()
._is_variant_deleted() -> bool
```