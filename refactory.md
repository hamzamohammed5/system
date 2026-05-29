
## بنية المشروع — المرحلة السادسة
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