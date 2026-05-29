# خطة إعادة هيكلة `ui/tabs/` — المرحلة السابعة

> الهدف: تحويل كل ملفات `tabs/` لتصبح **orchestrators نظيفة** تستدعي الأدوات الجاهزة من `widgets/base/`، وإزالة كل كود مكرر، وتوحيد البنية عبر القسم بالكامل.

---

## المبادئ الحاكمة

| المبدأ | التطبيق |
|--------|---------|
| **لا Repo مباشرة من الـ Tab** | كل استدعاء DB يمر عبر `services/` |
| **لا PyQt في الـ Service** | الـ services هي pure Python |
| **الـ conn من الخارج دايماً** | constructor injection، مش `get_connection()` جوا الـ Widget |
| **لا كود مكرر** | كل pattern متكرر يتحول لـ Base Class أو Mixin |
| **`emit_company_data_changed()` بدل `bus.data_changed.emit()`** | للدقة والأداء |
| **`CONNECT_BUS = True`** | في الـ Detail Panels اللي محتاجة تتحدث |
| **لا hardcoded styles** | كل الـ styles من `_C` dict أو `theme/styles.py` |

---

## هيكل الطبقات المستهدف

```
tabs/UI  ──────►  services/  ──────►  repos/ (db/)
   ↑                                       ↑
widgets/base (List, Detail, Form, Section)  schema/
   ↑
widgets/mixins (Bus, Edit, Refresh, Select, Validate, Service)
   ↑
widgets/components (buttons, labels, notifications...)
```

---

## القسم الأول: الخامات (`costing/raw/`)

### الوضع الحالي
- `raw_input_panel.py` — فورم ضخم يستدعي repo مباشرة، يحتوي على `EditModeMixin` و`LiveConnMixin` يدوياً
- `raw_table_panel.py` — جدول يبني كل شيء يدوياً، يدمج shared logic بالقوة
- `raw_section.py` — يبني `QSplitter` يدوياً

### المشاكل
- استدعاء `fetch_item`, `insert_item`, `update_item`, `delete_item` مباشرة من الـ Widget
- `_load`, `_apply_filter`, بناء الجدول — كل ده مكرر في كل tab
- الـ shared items logic مدمجة في الـ table بدل Mixin منفصل
- الـ `QSplitter` style مكررة في كل section

### الخطة

#### `raw/raw_input_panel.py` → `RawInputPanel(BaseCrudForm)`

```python
from ui.widgets.base.crud_form import BaseCrudForm
from ui.widgets.panels.form_parts import FormGroup, spin_field, labeled_widget
from ui.widgets.forms.inputs import RequiredLineEdit, AmountSpinBox
from ui.tabs.costing.shared.raw_variants_panel import _RawVariantsPanel

class RawInputPanel(BaseCrudForm):
    FORM_TITLE = "بيانات الخامة"
    ADD_TEXT   = "➕  إضافة خامة"
    SAVE_TEXT  = "💾  حفظ التعديل"

    def _build_fields(self, group: FormGroup):
        self.inp_name      = RequiredLineEdit("أدخل اسم الخامة...")
        self.spin_price    = AmountSpinBox(dec=2)
        self.spin_total_qty = spin_field(max_=999999, dec=4)
        self.lbl_hint      = hint_label("")          # من form_parts
        self.cmb_category  = CategoryCombo(self.conn, scope="raw")
        self._variants     = _RawVariantsPanel(self.conn)

        group.add_row("اسم الخامة *",      self.inp_name)
        group.add_row("السعر الكلي :",      labeled_widget(self.spin_price, "جنيه"))
        group.add_row("الكمية الإجمالية :", labeled_widget(self.spin_total_qty, "وحدة"))
        group.add_row("",                   self.lbl_hint)
        group.add_row("التصنيف :",          self.cmb_category)
        # variants panel بعد الـ group

    def _collect(self) -> dict | None:
        # التحقق عبر FormValidationMixin
        if not self.validate_required([(self.inp_name, "اسم الخامة")]):
            return None
        return {
            "name":      self.inp_name.text_stripped(),
            "price":     self.spin_price.value(),
            "total_qty": self.spin_total_qty.value() or None,
            "category_id": self.cmb_category.get_category(),
        }

    def _do_insert(self, data: dict) -> int:
        from services.shared.item_service import ItemService
        new_id = ItemService(self.conn).add(
            data["name"], data["price"], "raw",
            category_id=data["category_id"], total_qty=data["total_qty"]
        )
        self._variants.load_item(new_id, data["price"])
        return new_id

    def _do_update(self, item_id: int, data: dict):
        from services.shared.item_service import ItemService
        ItemService(self.conn).update(
            item_id, data["name"], data["price"],
            category_id=data["category_id"], total_qty=data["total_qty"]
        )

    def _do_load(self, item_id: int) -> dict | None:
        from services.shared.item_service import ItemService
        r = ItemService(self.conn).get(item_id)
        return vars(r) if r else None

    def _fill_fields(self, data: dict):
        self.inp_name.setText(data["name"])
        self.spin_price.setValue(data.get("price", 0))
        self.spin_total_qty.setValue(data.get("total_qty") or 0)
        self.cmb_category.set_category(data.get("category_id"))
        self._variants.load_item(data["id"], data.get("price", 0))

    def _reset_fields(self):
        self.inp_name.clear()
        self.spin_price.setValue(0)
        self.spin_total_qty.setValue(0)
        self.cmb_category.setCurrentIndex(0)
        self._variants.clear()
```

**التحسينات:**
- حذف `EditModeMixin` و`LiveConnMixin` الـ manual — الـ `BaseCrudForm` بيورثهم
- حذف `_collect`, `_add`, `_save_edit`, `_cancel_edit`, `_reset` الـ manual
- `_update_hint` تنتقل لـ `_on_fields_changed` hook في الـ Base Class
- الـ price→hint live preview يتحول لـ `spin_price.valueChanged.connect(self._update_hint)`

---

#### `raw/raw_table_panel.py` → `RawTablePanel(BaseListPanel, SharedOpsMixin)`

```python
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.mixins.shared_ops import SharedOpsMixin
from ui.widgets.tables.items import make_item, colored_item
from ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog import BulkReplaceDialog

class RawTablePanel(BaseListPanel, SharedOpsMixin):
    COLUMNS            = ["ID", "الاسم", "التصنيف", "السعر الكلي", "الكمية", "سعر الوحدة"]
    STRETCH_COL        = 1
    EMPTY_ICON         = "🧱"
    EMPTY_TITLE        = "لا توجد خامات"
    LIST_TITLE         = "─── الخامات المحفوظة ───"
    ADD_TEXT           = ""          # بدون زر Add هنا (الـ form منفصل)
    SHOW_CATEGORY      = True
    FILTER_SCOPE       = "raw"
    COL_WIDTHS         = {0: 45, 2: 110, 3: 90, 4: 90, 5: 95}

    def _load_rows(self) -> list:
        from services.shared.item_service import ItemService
        local = [vars(r) for r in ItemService(self.conn).list_by_type("raw")]
        shared = self._get_shared_rows(local, "raw")   # عبر SharedOpsMixin
        return local + shared

    def _fill_row(self, table, r: int, row: dict):
        is_shared    = row.get("_is_shared", False)
        is_published = row.get("_is_published", False)
        prefix = "🔗 " if is_shared else ("📤 " if is_published else "")
        color  = _SHARED_COLOR if is_shared else (_PUBLISHED_COLOR if is_published else None)

        id_item = make_item("🔗" if is_shared else ("📤" if is_published else str(row.get("id",""))),
                            user_data=row.get("id"))
        table.setItem(r, 0, id_item)
        table.setItem(r, 1, make_item(prefix + row.get("name",""), color=color))
        table.setItem(r, 2, make_item(row.get("category_name") or "—", color=color))
        table.setItem(r, 3, make_item(f"{row.get('price',0):.2f}", color=color))
        table.setItem(r, 4, make_item(str(row.get("total_qty","—")), color=color))
        from models.costing_base import raw_unit_price
        unit = raw_unit_price(row)
        table.setItem(r, 5, make_item(f"{unit:.4f}", color=color))

    def _build_extra_header_actions(self, header):
        header.add_action("🔄 استبدال شامل", self._bulk_replace, "primary")
        header.add_action("🔗 تعديل المشترك", self._edit_shared_selected, "normal")
        header.add_action("📤 نشر كمشترك",   self._publish_selected, "normal")

    def _on_row_double_clicked(self, item_id):
        self._form.load_for_edit(item_id)    # يُمرَّر كـ dependency

    def _bulk_replace(self):
        item_id = self.selected_id()
        if not item_id: return
        BulkReplaceDialog(self.conn, "raw", item_id, parent=self).exec_()
```

**التحسينات:**
- حذف `_load`, `_apply_filter`, بناء الجدول يدوياً — كل ده في `BaseListPanel`
- legend الـ shared/published تنتقل لـ `BaseListPanel._build_legends()` hook
- حذف 150+ سطر boilerplate

---

#### `raw/raw_section.py` → `RawSection(BaseSection)`

```python
from ui.widgets.base.section import BaseSection

class RawSection(BaseSection):
    FORM_POSITION = "top"      # الفورم فوق، الجدول تحت
    LIST_MIN_W    = 400

    def _create_list(self):
        return RawTablePanel(conn=self.conn)

    def _create_form(self):
        return RawInputPanel(conn=self.conn)

    def _connect_signals(self):
        self._form.saved.connect(self._list.refresh)
        self._list.item_selected.connect(self._form.load_for_edit)
```

**التحسينات:**
- حذف `QSplitter` اليدوي — `BaseSection` بيبنيه
- حذف `_SPLITTER_STYLE` المكررة — موجودة في `BaseSection`

---

## القسم الثاني: العمليات — العمالة (`costing/labor/`)

### المشاكل الحالية
- `labor_op_form.py` — يبني فورم يدوياً، `EditModeMixin` يدوي، repo مباشر
- `labor_op_table.py` — يرث من `SharedItemsListPanel` (جيد) لكن `_fetch_local_rows` بيستدعي repo مباشرة
- `labor_settings.py` — يقرأ/يكتب settings مباشرة بدون service

### الخطة

#### `labor/labor_op_form.py` → `LaborOpForm(BaseCrudForm)`

```python
class LaborOpForm(BaseCrudForm):
    FORM_TITLE = "بيانات العملية"
    ADD_TEXT   = "➕  إضافة"
    SAVE_TEXT  = "💾  حفظ التعديل"

    def __init__(self, conn, settings, parent=None):
        self._settings = settings
        super().__init__(conn, parent)

    def _build_fields(self, group: FormGroup):
        self.inp_name    = RequiredLineEdit("مثال: خياطة، تغليف...")
        self.sp_minutes  = spin_field(max_=99999, dec=2)
        self.cmb_category = CategoryCombo(self.conn, scope="labor")
        self.lbl_cost    = ResultBadge()

        self.sp_minutes.valueChanged.connect(self._update_preview)

        group.add_row("اسم العملية :", self.inp_name)
        group.add_row("الوقت :",       labeled_widget(self.sp_minutes, "دقيقة"))
        group.add_row("التصنيف :",     self.cmb_category)
        group.add_row("التكلفة :",     self.lbl_cost)

    def _update_preview(self):
        rate = self._settings.get_hourly_rate()
        cost = (self.sp_minutes.value() / 60.0) * rate
        self.lbl_cost.set_value(
            f"{cost:.2f} جنيه / وحدة   ({self.sp_minutes.value():.2f} د ÷ 60 × {rate:.2f})"
        )

    def _collect(self) -> dict | None:
        if not self.validate_required([(self.inp_name, "اسم العملية")]):
            return None
        return {
            "name":        self.inp_name.text_stripped(),
            "minutes":     self.sp_minutes.value(),
            "category_id": self.cmb_category.get_category(),
        }

    def _do_insert(self, data: dict) -> int:
        from db.costing.operations_repo import insert_labor_op
        return insert_labor_op(self.conn, data["name"], data["minutes"],
                               category_id=data["category_id"])

    def _do_update(self, op_id: int, data: dict):
        from db.costing.operations_repo import update_labor_op
        update_labor_op(self.conn, op_id, data["name"], data["minutes"],
                        category_id=data["category_id"])

    def _do_load(self, op_id: int) -> dict | None:
        from db.costing.operations_repo import fetch_labor_op
        r = fetch_labor_op(self.conn, op_id)
        return dict(r) if r else None

    def _fill_fields(self, data: dict):
        self.inp_name.setText(data["name"])
        self.sp_minutes.setValue(data["minutes"])
        self.cmb_category.set_category(data.get("category_id"))

    def _reset_fields(self):
        self.inp_name.clear()
        self.sp_minutes.setValue(0)
        self.lbl_cost.reset()
        self.cmb_category.setCurrentIndex(0)
```

#### `labor/labor_op_table.py` — تحسين داخلي (يبقى يرث من `SharedItemsListPanel`)

```python
# التغيير الوحيد: استخدام service بدل repo مباشرة في _fetch_local_rows
def _fetch_local_rows(self) -> list:
    from db.costing.operations_repo import fetch_all_labor_ops
    return [_to_dict(op) for op in fetch_all_labor_ops(self._live_conn())]
    # ملاحظة: لو اتعمل LaborOpService، يتستبدل بـ LaborOpService(conn).list()
```

#### `labor/labor_settings.py` — تحسين: استخدام `settings_repo` عبر service wrapper

```python
# إضافة SettingsService (إن لم يكن موجوداً) يغلف get_setting/set_setting
# أو الإبقاء على النمط الحالي مع توحيد الـ keys كـ constants في ملف منفصل:

# labor/labor_settings_keys.py
MONTHLY_SALARY    = "monthly_salary"
WORKING_DAYS      = "working_days"
HOLIDAY_DAYS      = "holiday_days"
WORKING_HOURS_DAY = "working_hours_day"
OVERHEAD_FACTOR   = "overhead_factor"
```

---

## القسم الثالث: الماكينات (`costing/machine/`)

### المشاكل الحالية
- `machine_form.py` — repo مباشر، EditModeMixin يدوي
- `machine_op_form.py` — ضخم، بيبني rows_editor جوا الفورم
- `machine_table.py` و`machine_op_table.py` — `SharedItemsListPanel` (جيد لكن) repo مباشر

### الخطة

#### `machine/machine_form.py` → `MachineForm(BaseCrudForm)`

```python
class MachineForm(BaseCrudForm):
    FORM_TITLE = "بيانات الماكينة"

    def _build_fields(self, group: FormGroup):
        self.inp_name       = RequiredLineEdit("مثال: ماكينة خياطة...")
        self.sp_rate_hour   = spin_field(max_=999999, dec=2)
        self.sp_rate_unit   = spin_field(max_=999999, dec=2)
        self.cmb_category   = CategoryCombo(self.conn, scope="machine")

        group.add_row("اسم الماكينة :",        self.inp_name)
        group.add_row("معدل التشغيل / ساعة :", labeled_widget(self.sp_rate_hour, "جنيه / ساعة"))
        group.add_row("معدل التشغيل / وحدة :", labeled_widget(self.sp_rate_unit, "جنيه / وحدة"))
        group.add_row("التصنيف :",              self.cmb_category)

    def _collect(self): ...
    def _do_insert(self, data): ...
    def _do_update(self, machine_id, data): ...
    def _do_load(self, machine_id): ...
    def _fill_fields(self, data): ...
    def _reset_fields(self): ...
```

#### `machine/machine_op_form.py` — تحسين هيكلي (مش full rewrite)

الملف ده معقد بسبب الـ `_OpRowsEditor` المدمج. الخطوات:

1. **استخراج `_MachineOpHeader`**: الحقول العلوية (اسم، ماكينة، وضع، تصنيف) تنفصل عن الـ rows editor
2. **تحويل `_OpRowsEditor`** ليُمرَّر `conn` من الخارج بدل `_live_conn()` جوا
3. **توحيد `_on_machine_changed`** — يستخدم signal chain بدل استدعاء مباشر

```python
# machine_op_form.py — الهيكل الجديد
class _MachineOpForm(QWidget, EditModeMixin, LiveConnMixin):
    def __init__(self, conn, parent=None):
        ...
        self._header = _MachineOpHeader(conn)      # الحقول فقط
        self._rows   = _OpRowsEditor(conn)         # الصفوف فقط
        self._header.machine_changed.connect(self._rows.update_rates)
```

---

## القسم الرابع: المنتجات (`costing/product/`)

### المشاكل الحالية
- `product_form.py` — orchestrator جيد لكن `load_product` ضخمة جداً
- `form/_rows_manager.py` — جيد لكن `add_row` تُنشئ `ComponentRow` مباشرة
- `form/_save_logic.py` — جيد كـ helper لكن يستدعي repos مباشرة
- `form/_header_bar.py` — جيد لكن الـ height fixed بدون سبب
- `product_table.py` — يبني الجدول يدوياً بالكامل
- `product_main_panel.py` — جيد كـ orchestrator لكن `_check_orphans` و`_fix_orphans` ممكن يتحسنوا

### الخطة

#### `product/product_table.py` → `ProductTable(BaseListPanel)`

```python
class ProductTable(BaseListPanel):
    COLUMNS       = ["ID", "الاسم", "التصنيف", "التكلفة"]
    STRETCH_COL   = 1
    EMPTY_ICON    = "🏭"
    EMPTY_TITLE   = "لا توجد منتجات"
    SHOW_CATEGORY = True
    COL_WIDTHS    = {0: 45, 2: 110, 3: 120}

    def __init__(self, conn, product_type, on_select=None, on_edit=None,
                 on_delete=None, parent=None):
        self.product_type = product_type
        self._on_select   = on_select
        self._on_edit     = on_edit
        self._on_delete   = on_delete
        scope = "semi" if product_type == "semi" else "final"
        self.FILTER_SCOPE = scope
        super().__init__(conn, parent)

    def _load_rows(self) -> list:
        from services.costing.product_service import ProductService
        # product_service.list_by_type(type) يرجع list[ProductResult]
        return [vars(r) for r in ProductService(self.conn).list_by_type(self.product_type)]

    def _fill_row(self, table, r: int, row: dict):
        from models.costing import calc_cost
        cost = calc_cost(self.conn, row["id"])
        table.setItem(r, 0, make_item(str(row["id"]), user_data=row["id"]))
        table.setItem(r, 1, make_item(row["name"]))
        table.setItem(r, 2, make_item(row.get("category_name") or "—"))
        table.setItem(r, 3, make_item(f"{cost:.4f}"))

    def _build_extra_header_actions(self, header):
        header.add_action("✏️ تعديل", lambda: self._on_edit and self._on_edit(self.selected_id()))
        header.add_danger("🗑️ حذف",   lambda: self._on_delete and self._on_delete(self.selected_id()))

    def _on_row_selected(self, item_id):
        if self._on_select:
            self._on_select(item_id)

    def selected_pid(self):
        return self.selected_id()
```

#### `form/_save_logic.py` → استخدام `ProductService`

```python
class _SaveLogic:
    def __init__(self, conn_fn):
        self._conn_fn = conn_fn

    def save(self, *, is_editing, editing_id, name, product_type,
             category_id, current_scenario_id, rows,
             scenarios_panel, parent_widget) -> int | None:
        if not name:
            QMessageBox.warning(parent_widget, "تنبيه", "ادخل اسم المنتج اولا")
            return None
        if not rows:
            QMessageBox.warning(parent_widget, "تنبيه", "اضف مكونا واحدا على الاقل")
            return None
        try:
            from services.costing.product_service import ProductService, BomComponent
            svc = ProductService(self._conn_fn())
            components = [
                BomComponent(
                    child_type=r[0], child_id=r[1], qty=r[2],
                    waste_pct=r[3] or 0.0, variant_id=r[4],
                    machine_op_row_id=r[5]
                )
                for r in rows
            ]
            result = svc.save(
                {"id": editing_id if is_editing else None,
                 "name": name, "type": product_type,
                 "price": 0, "category_id": category_id},
                components,
                scenario_id=current_scenario_id,
            )
            return result.product_id
        except Exception as e:
            QMessageBox.warning(parent_widget, "خطأ", str(e))
            return None
```

#### `form/_header_bar.py` — تحسينات

```python
# 1. حذف setFixedHeight(150) — يتحدد تلقائياً حسب المحتوى
# 2. استخدام CrudButtonsBar بدل بناء الأزرار يدوياً
# 3. column headers تنتقل لـ DataTableWidget.header أو تتحول لـ property
```

#### `product/product_main_panel.py` — تحسينات

```python
# _check_orphans → يستخدم ProductService.get_orphan_components()
# _fix_orphans   → يستخدم ProductService.fix_orphans()
# حذف import مباشر لـ fetch_item, delete_item, fetch_orphan_bom_rows
```

---

## القسم الخامس: الـ Shared Components (`costing/shared/`)

### `shared/component_row.py` → انتقال تدريجي

الملف ده معقد جداً (500+ سطر). الخطة:

1. **المرحلة أ — تنظيف الـ imports**: استخدام الـ `ComponentRow` الجديد من `ui/widgets/components/component_row/widget.py` مباشرة بدل الـ copy الموجود في `shared/`
2. **المرحلة ب — `_load_op_rows`**: تنتقل كاملاً لـ `op_rows.py` في `widgets/components/component_row/`
3. **المرحلة ج — `_load_variants`**: تنتقل لـ `variants.py`
4. **المرحلة د — `get_values`**: يبقى الـ single source of truth، يُختبر منفصلاً

### `shared/bulk_replace/bulk_replace_dialog.py` — تحسين

```python
# المشكلة: _apply() يستدعي fetch_bom + replace_bom مباشرة
# الحل: استخدام BulkReplaceService جديد

class BulkReplaceService:
    """
    services/costing/bulk_replace_service.py
    """
    def __init__(self, conn):
        self.conn = conn

    def apply(self, child_type, child_id, new_child_id,
              product_ids: list, uniform_qty=None,
              do_replace=True, do_qty=True) -> tuple[int, list[str]]:
        """
        يطبق الاستبدال على قائمة منتجات.
        يرجع (عدد_المحدّثين, قائمة_الأخطاء)
        """
        ...
```

### `shared/bom_scenarios_panel.py` — تحسين

```python
# حذف _make_btn static method الـ manual → استخدام make_btn من widgets/components/button.py
# توحيد style الأزرار مع بقية التطبيق
```

### `shared/catalog_builder.py` — بدون تغيير هيكلي
الملف جيد كما هو، فقط:
- إضافة `@lru_cache` محدود للـ `_fetch_shared` لتقليل استدعاءات DB

---

## القسم السادس: `labor_tab.py`, `machine_tab.py`, `raw_tab.py`, `product_tab.py`

### الهيكل الموحد المستهدف لكل Tab

```python
from ui.widgets.base.tab_section import TabSectionBase
from ui.widgets.managers.category import CategoryManager

class XxxTab(TabSectionBase):
    """
    كل tab = tabs فقط، مفيش logic هنا
    """
    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(XxxMainSection(self.conn), "📦  العناصر")
        tabs.addTab(CategoryManager(self.conn, scope="xxx"), "🏷️  التصنيفات")
```

### `labor_tab.py` — الهيكل الجديد

```python
class LaborTab(TabSectionBase):
    def _build_tabs(self, tabs: QTabWidget):
        self._settings = _LaborSettingsPanel(self.conn)
        tabs.addTab(self._settings,                               "⚙️  إعدادات العمالة")
        tabs.addTab(_LaborOpsSection(self.conn, self._settings),  "📋  عمليات العمالة")
        tabs.addTab(CategoryManager(self.conn, scope="labor"),    "🏷️  التصنيفات")

# _LaborOpsSection يرث من BaseSection
class _LaborOpsSection(BaseSection):
    FORM_POSITION = "top"
    def _create_list(self): return LaborOpTable(self.conn, ...)
    def _create_form(self): return LaborOpForm(self.conn, self._settings)
    def _connect_signals(self):
        self._form.saved.connect(self._list.refresh)
        self._list.item_selected.connect(self._form.load_for_edit)
```

### `machine_tab.py` — الهيكل الجديد

```python
class MachineTab(TabSectionBase):
    def _build_tabs(self, tabs: QTabWidget):
        tabs.addTab(_MachinesSection(self.conn),    "🖥️  الماكينات")
        tabs.addTab(_MachineOpsSection(self.conn),  "⚙️  عمليات التشغيل")
        tabs.addTab(CategoryManager(self.conn, scope="machine"), "🏷️  التصنيفات")

class _MachinesSection(BaseSection):
    def _create_list(self): return MachineTable(self.conn, ...)
    def _create_form(self): return MachineForm(self.conn)

class _MachineOpsSection(BaseSection):
    def _create_list(self): return MachineOpTable(self.conn, ...)
    def _create_form(self): return MachineOpForm(self.conn)
```

---

## القسم السابع: Imports الموحدة (Anti-pattern fix)

### المشكلة
كل ملف بيعمل import مختلف لنفس الأدوات:
```python
# الحالة الحالية — مكررة في 20+ ملف
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, ...
from ui.helpers import make_table, buttons_row, section_label, confirm_delete, danger_button
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.form_utils import FormGroup, labeled_widget, spin_field, ResultBadge, ...
```

### الحل: `costing/__init__.py` و`costing/shared/_imports.py`

```python
# ui/tabs/costing/shared/_imports.py
"""
Re-exports مشتركة لكل ملفات costing tabs
"""
# PyQt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

# UI Base
from ui.widgets.base.list_panel   import BaseListPanel
from ui.widgets.base.detail_panel import BaseDetailPanel
from ui.widgets.base.section      import BaseSection

# UI Components
from ui.widgets.components.button  import make_btn
from ui.widgets.components.label   import ResultBadge, ModeBadge
from ui.widgets.panels.form_parts  import FormGroup, labeled_widget, spin_field
from ui.widgets.forms.inputs       import RequiredLineEdit, AmountSpinBox
from ui.widgets.tables.items       import make_item, colored_item, center_item
from ui.widgets.combo.category     import CategoryCombo
from ui.widgets.core.conn          import LiveConnMixin
from ui.events                     import bus
```

---

## القسم الثامن: التحسينات العامة عبر كل الـ Tabs

### 1. حذف كل `LiveConnMixin` اليدوي
كل widget يرث من Base Class يحصل على `_live_conn()` تلقائياً.

### 2. توحيد `data_changed` emit
```python
# ❌ الحالة الحالية في كل مكان
bus.data_changed.emit()

# ✅ المطلوب
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()
```

### 3. حذف `QTimer.singleShot(0, ...)` الزائد
في `_rows_manager.py`:
```python
# ❌ حالياً
QTimer.singleShot(0, row.refresh_catalog)

# ✅ يتعوض بـ
row.refresh_catalog()  # synchronous، مفيش حاجة للـ timer
```

### 4. توحيد `_to_dict` helper
الدالة دي مكررة في 5+ ملفات:
```python
# ❌ مكررة في:
# labor_op_table.py, machine_table.py, machine_op_table.py, ...

# ✅ تنتقل لـ
# ui/tabs/costing/shared/_utils.py
def to_dict(row) -> dict:
    if isinstance(row, dict): return row
    try: return dict(row)
    except Exception: return {}
```

### 5. توحيد `confirm_delete` calls
```python
# ❌ حالياً (manual import في كل ملف)
from ui.helpers import confirm_delete
if confirm_delete(self, item_name): ...

# ✅ عبر BaseListPanel._delete_selected()
# يُستدعى تلقائياً من delete button في الـ Base Class
```

### 6. حذف `_SPLITTER_STYLE` المكررة
الـ style دي موجودة في 4+ ملفات بنفس القيم:
```python
# ✅ تنتقل لـ
from ui.widgets.theme.styles import splitter_style
# وتُستخدم في BaseSection مباشرة
```

---

## القسم التاسع: services جديدة محتاجة

### `services/costing/labor_op_service.py` (جديد)

```python
class LaborOpService:
    def __init__(self, conn): self.conn = conn

    def list(self) -> list[LaborOpResult]: ...
    def get(self, op_id) -> LaborOpResult | None: ...
    def add(self, name, minutes, category_id=None) -> int: ...
    def update(self, op_id, name, minutes, category_id=None): ...
    def delete(self, op_id): ...
    def calc_cost(self, op_id) -> float: ...
```

### `services/costing/machine_service.py` (جديد)

```python
class MachineService:
    def list(self) -> list[MachineResult]: ...
    def get(self, machine_id) -> MachineResult | None: ...
    def add(self, name, rate_per_hour, rate_per_unit, category_id=None) -> int: ...
    def update(self, machine_id, ...): ...
    def delete(self, machine_id): ...

class MachineOpService:
    def list(self) -> list[MachineOpResult]: ...
    def get(self, op_id) -> MachineOpResult | None: ...
    def add(self, machine_id, name, mode, value, category_id=None) -> int: ...
    def calc_cost(self, op_id, row_id=None) -> float: ...
```

### `services/costing/bulk_replace_service.py` (جديد)

```python
class BulkReplaceService:
    def apply(self, child_type, old_id, new_id,
              product_ids, uniform_qty=None,
              do_replace=True, do_qty=True) -> tuple[int, list[str]]: ...
```

---

## القسم العاشر: ترتيب التنفيذ (Milestones)

### Milestone 1 — البنية التحتية (Priority: عالية)
- [ ] إنشاء `services/costing/labor_op_service.py`
- [ ] إنشاء `services/costing/machine_service.py`
- [ ] إنشاء `services/costing/bulk_replace_service.py`
- [ ] إنشاء `ui/tabs/costing/shared/_utils.py` (to_dict + constants)
- [ ] إنشاء `ui/tabs/costing/shared/_imports.py` (re-exports)

### Milestone 2 — الخامات (Priority: عالية)
- [ ] `RawInputPanel(BaseCrudForm)`
- [ ] `RawTablePanel(BaseListPanel, SharedOpsMixin)`
- [ ] `RawSection(BaseSection)`
- [ ] `raw_tab.py` — تبسيط

### Milestone 3 — العمالة (Priority: متوسطة)
- [ ] `LaborOpForm(BaseCrudForm)`
- [ ] `_LaborOpsSection(BaseSection)` — يدمج form + table
- [ ] `labor_tab.py` — تبسيط

### Milestone 4 — الماكينات (Priority: متوسطة)
- [ ] `MachineForm(BaseCrudForm)`
- [ ] `_MachinesSection(BaseSection)`
- [ ] `_MachineOpsSection(BaseSection)` (مع الـ rows editor)
- [ ] `machine_tab.py` — تبسيط

### Milestone 5 — المنتجات (Priority: متوسطة-عالية)
- [ ] `ProductTable(BaseListPanel)`
- [ ] `_save_logic.py` → استخدام `ProductService`
- [ ] `_header_bar.py` → تحسينات (CrudButtonsBar)
- [ ] `product_main_panel.py` → استخدام `ProductService` للـ orphans

### Milestone 6 — الـ Shared Components (Priority: منخفضة-متوسطة)
- [ ] `ComponentRow` — انتقال تدريجي للـ version الجديد في `widgets/`
- [ ] `bulk_replace_dialog.py` → استخدام `BulkReplaceService`
- [ ] `bom_scenarios_panel.py` → توحيد الأزرار

### Milestone 7 — التنظيف النهائي (Priority: منخفضة)
- [ ] حذف كل `_SPLITTER_STYLE` المكررة
- [ ] توحيد `bus.data_changed.emit()` → `emit_company_data_changed()`
- [ ] حذف `QTimer.singleShot(0, ...)` الزائد
- [ ] توحيد `_to_dict` في ملف مشترك

---

## القسم الحادي عشر: ما لا يتغير

| الملف | السبب |
|-------|-------|
| `shared/bom_tree.py` | منطق معقد ومحدد، لا يستفيد من Base Classes |
| `shared/bom_scenarios_panel.py` | Mixin pattern فريد |
| `shared/catalog_builder.py` | Pure function، لا علاقة له بالـ UI |
| `shared/machine_op_rows_editor.py` | Widget متخصص، `QGroupBox` base كافي |
| `product/form/_rows_manager.py` | منطق فريد للـ BOM rows |
| `product/product_form.py` | orchestrator جيد، تحسينات طفيفة فقط |

---

## ملخص التوفير المتوقع

| الملف | السطور الحالية | المتوقع بعد | التوفير |
|-------|---------------|------------|---------|
| `raw_input_panel.py` | ~200 | ~80 | ~60% |
| `raw_table_panel.py` | ~300 | ~100 | ~67% |
| `raw_section.py` | ~50 | ~20 | ~60% |
| `labor_op_form.py` | ~120 | ~70 | ~42% |
| `machine_form.py` | ~120 | ~70 | ~42% |
| `product_table.py` | ~100 | ~50 | ~50% |
| `labor_tab.py` | ~70 | ~30 | ~57% |
| `machine_tab.py` | ~80 | ~35 | ~56% |
| **المجموع** | **~1040** | **~455** | **~56%** |

---

## قواعد الـ Code Review لكل ملف جديد

```
✅ يورث من Base Class مناسب؟
✅ لا استدعاء مباشر لـ repo من الـ Widget؟
✅ الـ conn بيجي من الخارج (constructor)؟
✅ لا PyQt في الـ Service؟
✅ لا _SPLITTER_STYLE محلية؟
✅ emit_company_data_changed() بدل bus.data_changed.emit()؟
✅ لا to_dict() محلية؟
✅ الـ imports من re-exports مش مباشرة؟
✅ CONNECT_BUS = True في Detail Panel؟
✅ FormValidationMixin للـ validation بدل QMessageBox يدوي في collect()؟
```