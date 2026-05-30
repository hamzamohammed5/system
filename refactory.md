# خطة إعادة الهيكلة الشاملة
**التاريخ:** 2026-05-30  
**الهدف:** `tabs/UI → services/ → repos/ (db/)` مع `widgets/ (base classes)`

---

## 1. المشاكل المكتشفة بالترتيب الأولوية

### 🔴 أولوية قصوى

#### 1.1 `main_window.py` — placeholders بدل tabs حقيقية
```python
# الحالي (خطأ): كل tabs تعرض placeholder
w = _make_placeholder_tab(name)  # لا يستدعي أي section فعلي!

# المطلوب: استخدام الـ sections الحقيقية
from ui.tabs.costing_section    import CostingSection
from ui.tabs.pricing_section    import PricingSection
from ui.tabs.accounting_section import AccountingTab
from ui.tabs.inventory_section  import InventoryTab
from ui.tabs.design_section     import DesignSection
from ui.tabs.orders_section     import OrdersSection
```
**الإجراء:** تعديل `_build_tabs()` في `main_window.py`

#### 1.2 `services/inventory/inventory_service.py` — يستدعي دوال غير مؤكدة
الملف الجديد يستدعي: `fetch_items_with_stock`, `fetch_item_with_stock`,
`get_current_stock`, `fetch_movements`, `insert_movement`, etc.  
لكن `inventory_repo.py` محتواه غير موجود في السياق.  
**الإجراء:** إعادة كتابة `inventory_service.py` بدوال تستدعي مباشرة بالـ SQL أو بتحقق آمن من الـ repo.

#### 1.3 `ui/tabs/accounting/_conn_guard.py` — محتمل wrapper
إذا كان يقدم decorator للتحقق من الاتصال، يُستبدل بـ `@requires_company` من `ui/widgets/core/guard.py`.  
**الإجراء:** مراجعة المحتوى — إذا wrapper → حذف واستبدال المستدعين.

---

### 🟡 أولوية متوسطة

#### 2.1 `ui/tabs/accounting/accounting_tabs_builder.py`
إذا كان يبني `QTabWidget` فقط دون منطق إضافي → يُدمج في `accounting_section.py`.

#### 2.2 `ui/tabs/accounting/account_combo.py` + `accounts_combo_widget.py`
احتمال تكرار. أحدهما wrapper للآخر.  
**الإجراء:** إبقاء الأصلي وحذف الـ wrapper، وتحديث المستدعين.

#### 2.3 `ui/tabs/design/design_styles.py`
إذا كان يكرر `widgets/theme/styles.py` → حذف واستبدال المستدعين باستدعاء مباشر.

#### 2.4 `ui/tabs/pricing/pricing/_stat_box.py`
إذا كان wrapper لـ `StatCard` → حذف واستبدال باستدعاء مباشر لـ `StatCard`.

#### 2.5 `ui/tabs/costing/shared/_utils.py`
يُصدّر `SHARED_COLOR, SHARED_BG, PUBLISHED_COLOR, PUBLISHED_BG`.  
هذه ثوابت خاصة بـ costing — **تبقى مكانها** ولا تنتقل.

#### 2.6 `ui/tabs/companies/shared_items_mixin.py`
يُصدّر: `is_shared_id`, `extract_shared_id`, `get_published_local_names`.  
مستدعى من `shared_ops.py` و `list_panel_with_shared.py` — **يبقى مكانه** لأنه منطق خاص بالشركات.

---

### 🟢 أولوية منخفضة

#### 3.1 تحويل tab classes لترث من `BaseSection`
كل `*_tab.py` يجب أن يصبح orchestrator نظيف يرث من `TabSectionBase` أو `BaseSection`.

#### 3.2 تحويل list panels لترث من `BaseListPanel`
كل `*_table.py` يجب أن يرث من `BaseListPanel`.

#### 3.3 تحويل detail panels لترث من `BaseDetailPanel`
كل `*_detail*.py` أو `*_panel.py` يجب أن يرث من `BaseDetailPanel`.

---


## 3. ملفات تحتاج إنشاء

### 3.1 `services/inventory/inventory_service.py` ✅ تم
**ملاحظة مهمة:** الملف يستدعي دوال من `inventory_repo.py` بأسماء مفترضة.
يجب التحقق من أسماء الدوال الفعلية في `inventory_repo.py`.
**البديل الآمن:** كتابة SQL مباشرة في الـ service إذا كانت الدوال غير موجودة.

---

## 4. ترتيب التنفيذ

### المرحلة الأولى — إصلاح فوري (اليوم)

```
[A] تعديل main_window.py → استخدام sections حقيقية بدل placeholders
[B] إعادة كتابة inventory_service.py → SQL مباشر بدل افتراض دوال الـ repo
[C] إضافة مفاتيح الترجمة الجديدة في ar.py و en.py
```

### المرحلة الثانية — تحويل sections إلى orchestrators

```
[D] costing_section.py   → TabSectionBase + CostingSection
[E] inventory_section.py → TabSectionBase + InventoryTab
[F] orders_section.py    → TabSectionBase + OrdersSection
[G] design_section.py    → TabSectionBase + DesignSection
[H] pricing_section.py   → TabSectionBase + PricingSection
[I] accounting_section.py → TabSectionBase + AccountingTab
```

### المرحلة الثالثة — تحويل sub-tabs

```
[J] inventory/items/_items_tab.py       → BaseSection
[K] inventory/*_tab.py                  → BaseSection
[L] orders/customers_tab.py             → BaseSection
[M] orders/orders_tab.py                → BaseSection
[N] orders/dashboard_tab.py             → BaseSection
[O] design/designs_tab.py               → BaseSection
[P] design/dimension_sets_tab.py        → BaseSection
[Q] pricing/pricing_tab.py              → BaseSection
[R] pricing/offers/offers_tab.py        → BaseSection
```

### المرحلة الرابعة — تحويل list/detail panels

```
[S] inventory/items/_items_table.py     → BaseListPanel
[T] inventory/*_tab.py tables           → BaseListPanel
[U] orders/customers/_list.py           → BaseListPanel
[V] orders/orders/*_list_panel.py       → BaseListPanel
[W] design/designs/_designs_table.py    → BaseListPanel
```

### المرحلة الخامسة — تنظيف

```
[X] فحص accounting/_conn_guard.py → حذف إذا wrapper لـ requires_company
[Y] فحص account_combo vs accounts_combo_widget → حذف الـ wrapper
[Z] فحص design_styles.py → حذف إذا يكرر widgets/theme/styles.py
[AA] فحص pricing/_stat_box.py → حذف إذا wrapper لـ StatCard
```

---

## 5. قواعد Code Review (Checklist)

- [ ] لا نصوص عربية hardcoded — كل نص مرئي يستخدم `tr(key)`
- [ ] لا wrapper files — استدعاء مباشر للملف الحقيقي
- [ ] كل list panel يرث من `BaseListPanel`
- [ ] كل detail panel يرث من `BaseDetailPanel`
- [ ] كل section يرث من `BaseSection` أو `TabSectionBase`
- [ ] كل orchestrator tab يرث من `TabSectionBase`
- [ ] signals تستخدم `bus.company_data_changed` + `CONNECT_BUS = True`
- [ ] emit يستخدم `emit_company_data_changed()` لا `bus.data_changed.emit()`
- [ ] DB access عبر `_live_conn()` لا `company_state` مباشرة
- [ ] `@requires_company` على كل method تحتاج شركة نشطة

---

## 6. تفاصيل التحويل لكل section

### costing_section.py (orchestrator)
```python
class CostingSection(TabSectionBase):
    def _build_tabs(self, tabs):
        from ui.tabs.costing.raw_tab    import RawTab
        from ui.tabs.costing.labor_tab  import LaborTab
        from ui.tabs.costing.machine_tab import MachineTab
        from ui.tabs.costing.product_tab import ProductTab
        tabs.addTab(RawTab(self.conn),     tr("raw_tab"))
        tabs.addTab(LaborTab(self.conn),   tr("labor_tab"))
        tabs.addTab(MachineTab(self.conn), tr("machine_tab"))
        tabs.addTab(ProductTab(self.conn), tr("product_tab"))
```

### inventory_section.py (orchestrator)
```python
class InventoryTab(TabSectionBase):
    def _build_tabs(self, tabs):
        from ui.tabs.inventory.inventory_items_tab   import InventoryItemsTab
        from ui.tabs.inventory.inventory_inbound_tab import InventoryInboundTab
        from ui.tabs.inventory.inventory_outbound_tab import InventoryOutboundTab
        from ui.tabs.inventory.inventory_report_tab  import InventoryReportTab
        tabs.addTab(InventoryItemsTab(self.conn),   tr("inventory_items"))
        tabs.addTab(InventoryInboundTab(self.conn), tr("stock_in"))
        tabs.addTab(InventoryOutboundTab(self.conn),tr("stock_out"))
        tabs.addTab(InventoryReportTab(self.conn),  tr("inventory_report"))
```

### orders_section.py (orchestrator)
```python
class OrdersSection(TabSectionBase):
    def _build_tabs(self, tabs):
        from ui.tabs.orders.dashboard_tab  import DashboardTab
        from ui.tabs.orders.orders_tab     import OrdersTab
        from ui.tabs.orders.customers_tab  import CustomersTab
        tabs.addTab(DashboardTab(self.conn), tr("dashboard_tab"))
        tabs.addTab(OrdersTab(self.conn),   tr("orders_tab"))
        tabs.addTab(CustomersTab(self.conn),tr("customers_tab"))
```

### design_section.py (orchestrator)
```python
class DesignSection(TabSectionBase):
    def _build_tabs(self, tabs):
        from ui.tabs.design.designs_tab        import DesignsTab
        from ui.tabs.design.dimension_sets_tab import DimensionSetsTab
        tabs.addTab(DesignsTab(self.conn),       tr("designs_tab"))
        tabs.addTab(DimensionSetsTab(self.conn), tr("dimension_sets_tab"))
```

### pricing_section.py (orchestrator)
```python
class PricingSection(TabSectionBase):
    def _build_tabs(self, tabs):
        from ui.tabs.pricing.pricing_tab      import PricingTab
        from ui.tabs.pricing.offers.offers_tab import OffersTab
        tabs.addTab(PricingTab(self.conn), tr("pricing_tab"))
        tabs.addTab(OffersTab(self.conn),  tr("offers_tab"))
```

### accounting_section.py (orchestrator)
```python
class AccountingTab(TabSectionBase):
    def _build_tabs(self, tabs):
        from ui.tabs.accounting.accounts_tree     import AccountsTree
        from ui.tabs.accounting.journal_tab       import JournalTab
        from ui.tabs.accounting.ledger_tab        import LedgerTab
        from ui.tabs.accounting.financial_statements import FinancialStatements
        from ui.tabs.accounting.investors_tab     import InvestorsTab
        tabs.addTab(AccountsTree(self.conn),        tr("accounts_tab"))
        tabs.addTab(JournalTab(self.conn),          tr("journal_tab"))
        tabs.addTab(LedgerTab(self.conn),           tr("ledger_tab"))
        tabs.addTab(FinancialStatements(self.conn), tr("financial_tab"))
        tabs.addTab(InvestorsTab(self.conn),        tr("investors_tab"))
```

---

## 7. نموذج تحويل list panel (BaseListPanel)

```python
# المثال: items/_items_table.py
class ItemsTable(BaseListPanel):
    COLUMNS     = ["", tr("name"), tr("unit"), tr("price"), tr("category")]
    STRETCH_COL = 1
    COL_WIDTHS  = {0: 0, 2: 70, 3: 90, 4: 120}
    EMPTY_ICON  = "📦"
    EMPTY_TITLE = "no_data"
    SHOW_CATEGORY = True
    FILTER_SCOPE  = "all"
    CONNECT_BUS   = True

    def _load_rows(self) -> list:
        from services.shared.item_service import ItemService
        return [vars(r) for r in ItemService(self.conn).list_all()]

    def _fill_row(self, table, r: int, row: dict):
        from ui.widgets.tables.items import make_item
        table.setItem(r, 0, make_item("", user_data=row["id"]))
        table.setItem(r, 1, make_item(row.get("name", "")))
        table.setItem(r, 2, make_item(row.get("unit", "")))
        table.setItem(r, 3, make_item(f"{row.get('price', 0):.2f}"))
        table.setItem(r, 4, make_item(row.get("category_name", "")))
```

---

## 8. المرحلة الأولى: الملفات التي سيتم إنشاؤها/تعديلها الآن

### 8.1 `ui/main_window.py` — تعديل `_build_tabs()`
إزالة `_make_placeholder_tab` واستخدام sections حقيقية.

### 8.2 `services/inventory/inventory_service.py` — إعادة كتابة
استخدام SQL مباشر بدل افتراض أسماء دوال الـ repo.

### 8.3 `ui/i18n/ar.py` — إضافة مفاتيح tabs
إضافة مفاتيح أسماء التبويبات للـ sections.

### 8.4 `ui/i18n/en.py` — إضافة مفاتيح tabs
نفس المفاتيح بالإنجليزية.

### 8.5 `ui/tabs/costing_section.py` — orchestrator
تحويل إلى `TabSectionBase` orchestrator نظيف.

### 8.6 `ui/tabs/inventory_section.py` — orchestrator
تحويل إلى `TabSectionBase` orchestrator نظيف.

### 8.7 `ui/tabs/orders_section.py` — orchestrator
تحويل إلى `TabSectionBase` orchestrator نظيف.

### 8.8 `ui/tabs/design_section.py` — orchestrator
تحويل إلى `TabSectionBase` orchestrator نظيف.

### 8.9 `ui/tabs/pricing_section.py` — orchestrator
تحويل إلى `TabSectionBase` orchestrator نظيف.

### 8.10 `ui/tabs/accounting_section.py` — orchestrator
تحويل إلى `TabSectionBase` orchestrator نظيف.