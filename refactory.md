# خطة إعادة الهيكلة — تحويل tabs/ إلى Orchestrators

**الهدف:** `tabs/UI → services/ → repos/ (db/)` مع قواعد `widgets/base`

---

## المبادئ الأساسية

```
tabs/          → Orchestrator فقط (لا repo مباشر، لا منطق حساب)
services/      → Business logic + validation
repos/ (db/)   → SQL فقط
widgets/base   → Base classes (BaseListPanel, BaseCrudForm, ...)
```

---

## المشاكل الموجودة حالياً (من تحليل الكود)

### 1. استدعاء repos مباشرة من tabs/

| الملف | المشكلة |
|-------|---------|
| `bom_tree.py` | `fetch_bom`, `delete_bom_row` من `db/shared/items_repo` مباشرة |
| `bom_tree.py` | `fetch_bom_for_scenario` من `db/costing/bom_scenarios_repo` مباشرة |
| `_scenario_node_builder.py` | `fetch_item`, `fetch_labor_op`, `fetch_machine_op` من repos مباشرة |
| `scenario_comparison_widget.py` | `calc_cost` + منطق حساب معقد داخل الـ widget |
| `product_form.py` | `fetch_item`, `fetch_orphan_bom_rows`, `fetch_default_scenario`, `insert_scenario` مباشرة |
| `_orphan_handler.py` | `fetch_orphan_bom_rows`, `delete_orphan_bom_rows`, `cleanup_empty_products_after_orphan_fix` مباشرة |
| `raw_variants_panel.py` | `insert_variant`, `update_variant`, `delete_variant`, `fetch_variant` مباشرة |
| `machine_op_rows_editor.py` | `fetch_op_rows`, `insert_op_row`, `update_op_row`, `delete_op_row`, `calc_op_row_cost`, `calc_op_total_cost` مباشرة |
| `_db_scenarios.py` | `fetch_scenarios`, `insert_scenario`, `update_scenario`, `delete_scenario`, `set_default_scenario`, `clone_scenario` مباشرة |
| `bulk_replace_helpers.py` | SQL مباشر + `calc_cost` في UI layer |
| `catalog_builder.py` | `fetch_items_by_type`, `fetch_all_labor_ops`, `fetch_all_machine_ops` مباشرة |

### 2. منطق حساب داخل الـ widgets

| الملف | المشكلة |
|-------|---------|
| `scenario_comparison_widget.py` | `_calc_scenario_cost()` — 40 سطر من business logic داخل QFrame |
| `_scenario_node_builder.py` | `calc_cost`, `calc_labor_op_cost`, `calc_machine_op_cost`, `raw_unit_price` داخل builder |
| `bom_tree.py` | `total_sc_cost` يُحسب داخل `_refresh()` |

### 3. bus events غير موحدة

| الملف | المشكلة |
|-------|---------|
| `raw_variants_panel.py` | ✅ محوَّل لـ `emit_company_data_changed` |
| `machine_op_rows_editor.py` | ✅ محوَّل |
| `_db_scenarios.py` | ✅ محوَّل |
| `labor_op_form.py` | ❌ يستخدم `bus.data_changed.connect` — يجب مراجعة |
| `machine_op_form.py` | ❌ `bus.data_changed.emit()` مباشرة |
| `product_form.py` | ❌ `bus.data_changed.emit()` مباشرة |

### 4. Hardcoded strings عربية بدل `tr()`

| الملف | المشكلة |
|-------|---------|
| `labor_tab.py` | `"⚙️  إعدادات العمالة"`, `"📋  عمليات العمالة"`, `"🏷️  التصنيفات"` hardcoded |
| `machine_tab.py` | كل labels hardcoded |
| `product_main_panel.py` | `"🗑️ حذف الناقص"`, `"✏️ تعديل"` hardcoded |
| `machine_op_form.py` | نصوص عربية كثيرة بدون `tr()` |
| `machine_form.py` | نصوص hardcoded |

### 5. `_SPLITTER_STYLE` مكررة

في `labor_tab.py` و `machine_tab.py` نفس الـ style محروقة. لا يربط بـ `_C` ولا يستجيب لـ `bus.theme_changed`.

### 6. `catalog_builder.py` في UI layer

`catalog_builder.py` موجود في `ui/tabs/costing/shared/` لكنه يبني بيانات من DB — يجب نقله أو تغليفه بـ service.

### 7. `product_main_panel.py` — `_build_extra_header_actions` hardcoded strings

```python
header.add_action("🗑️ حذف الناقص", ..., fix_text="🗑️ حذف الناقص")
```

---

## الخطة التفصيلية

### المرحلة 1 — Services جديدة (الأولوية الأعلى)

#### 1.1 `services/costing/scenario_service.py` (جديد)

يغلّف كل عمليات `bom_scenarios_repo` + حساب تكلفة السيناريو:

```python
ScenarioService(conn)

svc.list(item_id) -> list[ScenarioResult]
svc.get_default(item_id) -> ScenarioResult | None
svc.create(item_id, name, is_default=False) -> int
svc.rename(scenario_id, name)
svc.clone(scenario_id, name) -> int
svc.set_default(scenario_id)
svc.delete(scenario_id) -> bool
svc.ensure_default(item_id) -> int

# الجديد — ينقل منطق _calc_scenario_cost من scenario_comparison_widget
svc.calc_cost(scenario_id) -> float
svc.get_bom(scenario_id) -> list[BomRow]
svc.replace_bom(scenario_id, rows: list[BomComponent])
```

**الملفات المتأثرة:**
- `_db_scenarios.py` → يستدعي `ScenarioService` بدل repos مباشرة
- `scenario_comparison_widget.py` → `_calc_scenario_cost` يُحذف، يُستبدل بـ `svc.calc_cost`
- `product_form.py` → `fetch_default_scenario`, `insert_scenario` يُستبدلان
- `_save_logic.py` → `ensure_default_scenario` يأتي من Service

#### 1.2 `services/costing/bom_tree_service.py` (جديد)

يغلّف جلب بيانات BOM Tree:

```python
BomTreeService(conn)

svc.get_scenarios(item_id) -> list[ScenarioWithBom]
svc.get_bom_for_scenario(scenario_id) -> list[BomRow]
svc.get_sub_bom(item_id) -> list[BomRow]          # للنصف مصنع
svc.delete_bom_component(scenario_id, child_type, child_id)
svc.delete_bom_row_direct(parent_id, child_type, child_id)  # بدون سيناريو
```

**الملفات المتأثرة:**
- `bom_tree.py` → يستدعي `BomTreeService` بدل repos مباشرة
- `_fetch_bom_with_row_id_by_scenario` يُبسَّط

#### 1.3 `services/costing/variant_service.py` (جديد)

```python
VariantService(conn)

svc.list(item_id) -> list[VariantResult]
svc.get(variant_id) -> VariantResult | None
svc.add(item_id, name, pieces, notes=None) -> int
svc.update(variant_id, name, pieces, notes=None)
svc.delete(variant_id)
svc.calc_unit_cost(item_id, variant_id, item_price) -> float
```

**الملفات المتأثرة:**
- `raw_variants_panel.py` → كل `db.costing.raw_variants_repo` calls تُستبدل

#### 1.4 `services/costing/machine_op_rows_service.py` (جديد)

```python
MachineOpRowsService(conn)

svc.list(op_id) -> list[OpRowResult]
svc.get(row_id) -> OpRowResult | None
svc.add(op_id, label, value, count, sort_order=0) -> int
svc.update(row_id, label, value, count, sort_order=0)
svc.delete(row_id) -> bool          # يرفض لو آخر صف
svc.calc_row_cost(row_id) -> float
svc.calc_total_cost(op_id) -> float
```

**الملفات المتأثرة:**
- `machine_op_rows_editor.py` → كل `db.costing.machine_op_rows_repo` calls تُستبدل

#### 1.5 `services/costing/catalog_service.py` (جديد أو نقل)

ينقل منطق `catalog_builder.py` إلى services layer:

```python
CatalogService(conn)

svc.build() -> CatalogData
svc.build_raw() -> list
svc.build_labor_ops() -> list
svc.build_machine_ops() -> list
svc.build_semi() -> list
```

**الملفات المتأثرة:**
- `catalog_builder.py` → يصبح thin wrapper أو يُحذف
- `_catalog_provider.py` → يستدعي `CatalogService`

---

### المرحلة 2 — تنظيف الـ Widgets

#### 2.1 `scenario_comparison_widget.py`

**قبل:**
```python
def _calc_scenario_cost(self, scenario_id):
    # 40 سطر من منطق حساب معقد مع imports داخلية
    from db.costing.bom_scenarios_repo import fetch_bom_for_scenario
    from db.shared.items_repo import fetch_item
    from models.costing_base import raw_unit_price, effective_qty
    ...
```

**بعد:**
```python
def _calc_scenario_cost(self, scenario_id):
    from services.costing.scenario_service import ScenarioService
    return ScenarioService(self.conn).calc_cost(scenario_id)
```

#### 2.2 `bom_tree.py`

**قبل:**
- `_fetch_bom_with_row_id_by_scenario` — 50 سطر SQL مع PRAGMA
- `_fetch_all_scenarios` — SQL مباشر
- `_get_scenario_id_for_item` — SQL مباشر

**بعد:**
```python
def _refresh(self):
    svc = BomTreeService(self._conn)
    scenarios = svc.get_scenarios(self._pid)
    for sc in scenarios:
        bom_rows = svc.get_bom_for_scenario(sc.id)
        ...
```

#### 2.3 `raw_variants_panel.py`

**قبل:**
```python
from db.costing.raw_variants_repo import (
    fetch_variants_for_item, insert_variant, update_variant,
    delete_variant, fetch_variant,
)
```

**بعد:**
```python
from services.costing.variant_service import VariantService
# كل العمليات عبر VariantService(self.conn)
```

#### 2.4 `machine_op_rows_editor.py`

**قبل:** 8 imports من `db.costing.machine_op_rows_repo`

**بعد:**
```python
from services.costing.machine_op_rows_service import MachineOpRowsService
svc = MachineOpRowsService(self.conn)
```

#### 2.5 `_db_scenarios.py`

**قبل:** 6 imports من `db.costing.bom_scenarios_repo`

**بعد:**
```python
from services.costing.scenario_service import ScenarioService
svc = ScenarioService(self.conn)
```

---



## ترتيب التنفيذ المقترح

```
الأسبوع 1:
  ✅ ScenarioService         → يُبسّط 4 ملفات دفعة واحدة
  ✅ VariantService          → يُبسّط raw_variants_panel
  ✅ MachineOpRowsService    → يُبسّط machine_op_rows_editor

الأسبوع 2:
  ✅ BomTreeService          → يُبسّط bom_tree.py
  ✅ CatalogService          → ينقل catalog_builder لـ services layer
  ✅ توحيد bus events        → emit_company_data_changed في كل مكان

الأسبوع 3:
  ✅ splitter_vertical_style → إزالة _SPLITTER_STYLE المكررة
  ✅ tr() في كل النصوص      → labor_tab, machine_tab, machine_op_form
  ✅ BomNodeData dataclass   → فصل presentation عن data access في bom_tree
```

---

## ملخص الأثر المتوقع

| المعيار | قبل | بعد |
|---------|-----|-----|
| repo imports مباشرة في tabs/ | ~25 import | 0 |
| منطق حساب في widgets | ~80 سطر | 0 |
| `bus.data_changed.emit()` غير موحّدة | 6 أماكن | 0 |
| hardcoded strings عربية في tabs/ | ~40 نص | 0 |
| `_SPLITTER_STYLE` مكررة | 3 أماكن | 0 |
| services جديدة | 0 | 5 |

---

## ملاحظات مهمة

1. **`cleanup_empty_products_after_orphan_fix`** — هذه الدالة مستخدمة في `_orphan_handler.py` لكنها غير موثقة في `db.md` → يجب التحقق من وجودها أو إضافتها لـ `ProductService.fix_orphans()` الموجود.

2. **`fetch_bom_with_row_id_by_scenario`** — الـ PRAGMA SQL الموجود في `bom_tree.py` يتحقق من وجود أعمدة ديناميكياً. هذا المنطق يجب أن ينتقل لـ `BomTreeService` أو يُعالج في migration آمن.

3. **`catalog_builder._fetch_shared()`** — يفتح ويُغلق `central_conn` في كل استدعاء. في `CatalogService` يجب تحسين هذا بـ context manager أو تمرير `central_conn` اختياري.

4. **`_memory_scenarios.py`** — منطق الذاكرة صحيح ولا يحتاج تغيير جوهري، لكن عند بناء `ScenarioService` يجب التأكد من التوافق مع `switch_to_db_mode`.

# بنية المشروع — المرحلة السادسة
### الأهداف البنيوية للمرحلة السابعة

الهدف الأساسي هو استكمال تحويل ملفات `tabs/` لتصبح مجرد orchestrators تستدعي الأدوات الجاهزة:

```
tabs/UI ──→ services/ ──→ repos/ (db/)
  ↑                            ↑
widgets/ (base classes)    schema/
```

### الربط الصحيح بين الطبقات

```
tabs/UI ──→ services/ ──→ repos/ (db/)
  ↑                            ↑
widgets/ (base classes)    schema/
```

**القواعد:**
- **tabs** تستدعي **services** مش الـ repos مباشرة
- **services** لا تعرف عن PyQt — pure Python
- **widgets** توفر الـ UI infrastructure فقط
- **conn** دايماً يجي من الخارج (constructor) مش يتفتح جوا الـ Widget

---

### الـ Base Classes المتاحة

| الحاجة | الـ Class | الملف |
|--------|-----------|-------|
| لوحة قائمة | `BaseListPanel` | `ui/widgets/base/list_panel.py` |
| لوحة تفاصيل | `BaseDetailPanel` | `ui/widgets/base/detail_panel.py` |
| فورم CRUD | `BaseCrudForm` | `ui/widgets/base/crud_form.py` |
| قسم list+detail | `BaseSection` | `ui/widgets/base/section.py` |
| قسم مع فورم | `CrudSection` | `ui/widgets/panels/crud_section.py` |
| تبويبات | `TabSectionBase` | `ui/widgets/base/tab_section.py` |

---

### Template — List Panel

```python
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.items import make_item
from PyQt5.QtCore import Qt

class MyListPanel(BaseListPanel):
    COLUMNS            = ["الاسم", "التصنيف", "السعر"]
    STRETCH_COL        = 0
    EMPTY_ICON         = "📦"
    EMPTY_TITLE        = "لا توجد عناصر"
    LIST_TITLE         = "العناصر"
    ADD_TEXT           = "➕ إضافة"
    SEARCH_PLACEHOLDER = "🔍  بحث في العناصر..."
    SHOW_CATEGORY      = True
    FILTER_SCOPE       = "raw"

    def _load_rows(self) -> list:
        from services.shared.item_service import ItemService
        return [vars(r) for r in ItemService(self.conn).list_by_type("raw")]

    def _fill_row(self, table, row_index: int, row_data: dict):
        table.setItem(row_index, 0, make_item(row_data["name"], user_data=row_data["id"]))
        table.setItem(row_index, 1, make_item(row_data.get("category_name") or "—"))
        table.setItem(row_index, 2, make_item(
            f"{row_data.get('price', 0):,.2f}", align=Qt.AlignCenter
        ))

    def _on_add_clicked(self):
        pass  # emit signal أو افتح dialog
```

---

### Template — Detail Panel

```python
from ui.widgets.base.detail_panel import BaseDetailPanel
from ui.widgets.panels.detail_section import DetailSection

class MyDetailPanel(BaseDetailPanel):
    EMPTY_ICON    = "📦"
    EMPTY_TITLE   = "اختر عنصراً من القائمة"
    MIN_CONTENT_W = 500
    CONNECT_BUS   = True

    def _build_header_cards(self):
        self._card_price = self._hdr.add_stat_card("💰", "السعر", "─", "#1565c0")

    def _build_header_buttons(self):
        self._hdr.toolbar.add_action("✏️ تعديل", self._edit, "primary")
        self._hdr.toolbar.add_danger("🗑️ حذف", self._delete)

    def _build_content(self, layout):
        self._sec      = DetailSection("البيانات الأساسية", cols=2)
        self._lbl_name = self._sec.add_row("الاسم:")
        self._lbl_cat  = self._sec.add_row("التصنيف:")
        layout.addWidget(self._sec)

    def _load_data(self, item_id: int):
        from services.shared.item_service import ItemService
        return ItemService(self.conn).get(item_id)

    def _fill_header(self, data: dict):
        self._hdr.set_title(data.get("name", "─"))
        self._card_price.set_value(f"{data.get('price', 0):,.2f} ج")

    def _fill_data(self, data: dict):
        self._lbl_name.setText(data.get("name", "─"))
        self._lbl_cat.setText(data.get("category_name") or "بدون تصنيف")
```

---

### Template — Crud Form

```python
from ui.widgets.base.crud_form import BaseCrudForm
from ui.widgets.panels.form_parts import FormGroup
from ui.widgets.forms.inputs import RequiredLineEdit, AmountSpinBox

class MyForm(BaseCrudForm):
    FORM_TITLE = "بيانات العنصر"
    ADD_TEXT   = "➕  إضافة"
    SAVE_TEXT  = "💾  حفظ التعديل"

    def _build_fields(self, group: FormGroup):
        self.inp_name   = RequiredLineEdit("اسم العنصر")
        self.spin_price = AmountSpinBox()
        group.add_row("الاسم *", self.inp_name)
        group.add_row("السعر",   self.spin_price)

    def _collect(self) -> dict | None:
        if not self.inp_name.validate():
            return None
        return {"name": self.inp_name.text_stripped(), "price": self.spin_price.value()}

    def _do_insert(self, data: dict) -> int:
        from services.shared.item_service import ItemService
        return ItemService(self.conn).add(data["name"], data["price"], "raw")

    def _do_update(self, item_id: int, data: dict):
        from services.shared.item_service import ItemService
        ItemService(self.conn).update(item_id, data["name"], data["price"])

    def _do_load(self, item_id: int) -> dict | None:
        from services.shared.item_service import ItemService
        result = ItemService(self.conn).get(item_id)
        return vars(result) if result else None

    def _fill_fields(self, data: dict):
        self.inp_name.setText(data.get("name", ""))
        self.spin_price.setValue(data.get("price", 0))

    def _reset_fields(self):
        self.inp_name.clear()
        self.spin_price.setValue(0)
```

---

### Template — Section كاملة

```python
from ui.widgets.base.section import BaseSection

class MySection(BaseSection):
    LIST_MIN_W   = 300
    LIST_MAX_W   = 500
    DETAIL_MIN_W = 400
    CONNECT_BUS  = True

    def _create_list(self):
        return MyListPanel(conn=self.conn)

    def _create_detail(self):
        return MyDetailPanel(conn=self.conn)

    def _connect_signals(self):
        self._list.item_selected.connect(self._detail.load_item)
        self._detail.deleted.connect(self._list.refresh)
```

---

### Checklist — Feature جديدة

- [ ] List Panel يورث من `BaseListPanel`
- [ ] Detail Panel يورث من `BaseDetailPanel`
- [ ] Form يورث من `BaseCrudForm`
- [ ] Section يورث من `BaseSection` أو `CrudSection`
- [ ] Business Logic في `services/` مش في الـ Widget
- [ ] الـ Widget تستدعي الـ Service مش الـ Repo مباشرة
- [ ] `emit_company_data_changed()` بدل `bus.data_changed.emit()`
- [ ] `CONNECT_BUS = True` في الـ Detail Panel لو محتاج يتحدث تلقائياً
- [ ] الـ conn بيجي من الخارج (constructor) مش يتفتح جوا الـ Widget
- [ ] تحقق من الـ inputs في الـ service layer مش الـ widget فقط

---

## ملفات tabs الموجودة حالياً

### Section Files
```
ui/tabs/accounting_section.py
ui/tabs/costing_section.py
ui/tabs/design_section.py
ui/tabs/inventory_section.py
ui/tabs/orders_section.py
ui/tabs/pricing_section.py
```

### Accounting
```
ui/tabs/accounting/accounting_tabs_builder.py
ui/tabs/accounting/accounts_tree.py
ui/tabs/accounting/account_combo.py
ui/tabs/accounting/accounts_combo_widget.py
ui/tabs/accounting/financial_statements.py
ui/tabs/accounting/group_manager.py
ui/tabs/accounting/helpers.py
ui/tabs/accounting/investors_tab.py
ui/tabs/accounting/journal_tab.py
ui/tabs/accounting/ledger_tab.py
ui/tabs/accounting/_conn_guard.py
ui/tabs/accounting/_state_widgets.py
ui/tabs/accounting/financial/balance_sheet_tab.py
ui/tabs/accounting/financial/income_statement_tab.py
ui/tabs/accounting/financial/owners_equity_tab.py
ui/tabs/accounting/financial/trial_balance_tab.py
ui/tabs/accounting/financial/_financial_helpers.py
ui/tabs/accounting/investors/_investor_details.py
ui/tabs/accounting/investors/_investor_form.py
ui/tabs/accounting/investors/_investors_layout.py
ui/tabs/accounting/investors/_investors_panel.py
ui/tabs/accounting/investors/_investors_table.py
ui/tabs/accounting/investors/_details_table.py
ui/tabs/accounting/investors/_helpers.py
ui/tabs/accounting/investors/_link_to_entry_panel.py
ui/tabs/accounting/investors/_movement_dialog.py
ui/tabs/accounting/journal/journal_account_picker.py
ui/tabs/accounting/journal/journal_filter.py
ui/tabs/accounting/journal/journal_form.py
ui/tabs/accounting/journal/journal_group_combo.py
ui/tabs/accounting/journal/journal_lines.py
ui/tabs/accounting/journal/journal_tab_widget.py
ui/tabs/accounting/journal/journal_tree_table.py
ui/tabs/accounting/journal/account_picker/_account_picker_button.py
ui/tabs/accounting/journal/account_picker/_account_tree_popup.py
ui/tabs/accounting/journal/form/_balance_bar.py
ui/tabs/accounting/journal/form/_entry_meta.py
ui/tabs/accounting/journal/form/_journal_header.py
ui/tabs/accounting/journal/group_combo/_no_select_delegate.py
ui/tabs/accounting/journal/group_combo/_tree_group_combo.py
ui/tabs/accounting/journal/lines/_lines_panel.py
ui/tabs/accounting/journal/lines/_smart_line.py
ui/tabs/accounting/ledger/ledger_accounts_panel.py
ui/tabs/accounting/ledger/ledger_filter_bar.py
ui/tabs/accounting/ledger/ledger_stat_cards.py
ui/tabs/accounting/ledger/ledger_t_account.py
ui/tabs/accounting/tree/_account_form.py
ui/tabs/accounting/tree/_group_filter.py
ui/tabs/accounting/tree/_tree_builder.py
ui/tabs/accounting/tree/_tree_headers.py
ui/tabs/accounting/tree/_tree_nodes.py
```

### Costing
```
ui/tabs/costing/product_tab.py
ui/tabs/costing/raw_tab.py
ui/tabs/costing/labor_tab.py
ui/tabs/costing/machine_tab.py
ui/tabs/costing/product/product_form.py
ui/tabs/costing/product/product_main_panel.py
ui/tabs/costing/product/product_table.py
ui/tabs/costing/product/_catalog_provider.py
ui/tabs/costing/product/_orphan_handler.py
ui/tabs/costing/product/form/_header_bar.py
ui/tabs/costing/product/form/_rows_manager.py
ui/tabs/costing/product/form/_save_logic.py
ui/tabs/costing/raw/raw_input_panel.py
ui/tabs/costing/raw/raw_section.py
ui/tabs/costing/raw/raw_table_panel.py
ui/tabs/costing/labor/labor_op_form.py
ui/tabs/costing/labor/labor_op_table.py
ui/tabs/costing/labor/labor_settings.py
ui/tabs/costing/machine/machine_form.py
ui/tabs/costing/machine/machine_op_form.py
ui/tabs/costing/machine/machine_op_table.py
ui/tabs/costing/machine/machine_table.py
ui/tabs/costing/shared/bom_scenarios_panel.py
ui/tabs/costing/shared/bom_tree.py
ui/tabs/costing/shared/catalog_builder.py
ui/tabs/costing/shared/component_row.py
ui/tabs/costing/shared/machine_op_rows_editor.py
ui/tabs/costing/shared/raw_variants_panel.py
ui/tabs/costing/shared/scenario_comparison_widget.py
ui/tabs/costing/shared/bom_scenarios/...
ui/tabs/costing/shared/bulk_replace/...
```

### Design
```
ui/tabs/design/designs_tab.py
ui/tabs/design/dimension_sets_tab.py
ui/tabs/design/design_styles.py
ui/tabs/design/designs/...
ui/tabs/design/dimension_sets/...
```

### Inventory
```
ui/tabs/inventory/inventory_inbound_tab.py
ui/tabs/inventory/inventory_items_tab.py
ui/tabs/inventory/inventory_outbound_tab.py
ui/tabs/inventory/inventory_report_tab.py
ui/tabs/inventory/items/_item_form.py
ui/tabs/inventory/items/_items_tab.py
ui/tabs/inventory/items/_items_table.py
```

### Orders
```
ui/tabs/orders/orders_tab.py
ui/tabs/orders/customers_tab.py
ui/tabs/orders/dashboard_tab.py
ui/tabs/orders/_customer_form.py
ui/tabs/orders/_item_form.py
ui/tabs/orders/_order_detail.py
ui/tabs/orders/_order_form.py
ui/tabs/orders/customers/customer_detail_panel.py
ui/tabs/orders/customers/customers_list_panel.py
ui/tabs/orders/dashboard/_config.py
ui/tabs/orders/dashboard/_recent_table.py
ui/tabs/orders/dashboard/_status_grid.py
ui/tabs/orders/dashboard/_top_cards.py
ui/tabs/orders/order_detail/_header_fill.py
ui/tabs/orders/order_detail/_items_section.py
ui/tabs/orders/order_detail/_log_section.py
ui/tabs/orders/order_detail/_status_config.py
ui/tabs/orders/order_detail/_status_dialog.py
ui/tabs/orders/order_form/_item_row_widget.py
ui/tabs/orders/order_form/_products_fetcher.py
ui/tabs/orders/orders/_filter_toolbar.py
ui/tabs/orders/orders/_orders_list_panel.py
ui/tabs/orders/orders/_status_delegate.py
```

### Pricing
```
ui/tabs/pricing/pricing_tab.py
ui/tabs/pricing/pricing/...
ui/tabs/pricing/offers/...
```

### Companies
```
ui/tabs/companies/companies_dialog.py
ui/tabs/companies/company_selector.py
ui/tabs/companies/no_company_screen.py
ui/tabs/companies/shared_items_dialog.py
ui/tabs/companies/shared_items_manager.py
ui/tabs/companies/shared_items_mixin.py
ui/tabs/companies/_link_item_picker.py
ui/tabs/companies/shared_items_manager_helper/_add_shared_item_dialog.py
```