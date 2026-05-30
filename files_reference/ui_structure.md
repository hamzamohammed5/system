# دليل الكود — UI Structure

> مرجع نقطة الدخول + النافذة الرئيسية + الـ Sidebar + كل الـ Tabs/Sections.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [نقطة الدخول](#نقطة-الدخول) | `main.py` |
| [النافذة الرئيسية](#النافذة-الرئيسية) | `ui/main_window.py` |
| [Sidebar — المكونات](#sidebar--المكونات) | `_sidebar`, `_nav_button`, `_section_label`, `_toggle_button` |
| [Tabs — Sections الرئيسية](#tabs--sections-الرئيسية) | `costing_section`, `pricing_section`, `accounting_section`, `inventory_section`, `design_section`, `orders_section` |
| [Tabs — التكلفة](#tabs--التكلفة) | `product_tab`, `raw_tab`, `labor_tab`, `machine_tab` |
| [Tabs — التسعير](#tabs--التسعير) | `pricing_tab`, `offers_tab` |
| [Tabs — المحاسبة](#tabs--المحاسبة) | `accounts_tree`, `journal_tab`, `ledger_tab`, `audit_log_tab`, `financial_statements`, `investors_tab` |
| [Tabs — المخزن](#tabs--المخزن) | `inventory_items_tab`, `inventory_inbound_tab`, `inventory_outbound_tab`, `inventory_report_tab` |
| [Tabs — التصميمات](#tabs--التصميمات) | `designs_tab`, `dimension_sets_tab` |
| [Tabs — الطلبات](#tabs--الطلبات) | `orders_tab`, `customers_tab`, `dashboard_tab` |
| [Tabs — الشركات](#tabs--الشركات) | `companies_dialog`, `company_selector`, `no_company_screen`, `shared_items_manager` |

---

## نقطة الدخول

### `main.py`

تسلسل التشغيل:

```
1. init_db()                                      ← تهيئة companies.db فقط
2. QApplication(sys.argv)
3. theme_manager.load_from_db()                   ← تحميل الثيم المحفوظ
4. i18n_manager.load_from_db()                    ← تحميل اللغة المحفوظة
5. app.setStyleSheet(_build_stylesheet(get_font_size()))
6. app.setLayoutDirection(i18n_manager.qt_direction)
7. install_no_wheel_filter(app)                   ← منع عجلة الماوس على inputs
8. install_shift_wheel_filter(app)                ← Shift+Wheel مسموح
9. MainWindow(app).show()
10. app.exec_()
```

**الاستيراد:**
```python
from ui.widgets.core.i18n import i18n_manager
```

**ملاحظة:** لا يُنشئ أي connection لشركة — كل الـ connections تُنشأ لاحقاً عبر `company_state`.

---

## النافذة الرئيسية

### `ui/main_window.py` — `MainWindow(QMainWindow)`

**التهيئة:**
```python
MainWindow(app: QApplication)
# resize: WINDOW_DEFAULT_W × 820
# setLayoutDirection: Qt.RightToLeft
# setMinimumSize: (SIDEBAR_COLLAPSED_WIDTH + 400, 500)
```

**هيكل الـ Layout:**
```
QHBoxLayout (central widget)
├── _Sidebar                    (Fixed width, Expanding height)
├── QFrame (separator, 1px)
└── QScrollArea (_content_scroll, stretch=1)
    └── QStackedWidget (_stack, minWidth=CONTENT_MIN_WIDTH)
        ├── [0] NoCompanyScreen     ← يظهر لو مفيش شركة
        ├── [1] CostingSection
        ├── [2] PricingSection
        ├── [3] AccountingTab
        ├── [4] InventoryTab
        ├── [5] DesignSection
        └── [6] OrdersSection
```

**index_map للـ Navigation:**
```python
{
    "costing":    1,
    "pricing":    2,
    "accounting": 3,
    "inventory":  4,
    "design":     5,
    "orders":     6,
}
```

**الدوال الرئيسية:**
```python
_build()                        # يبني الهيكل الأساسي
_build_tabs()                   # ينشئ الـ tab widgets (index 1-6)
_destroy_tabs()                 # يحذف الـ tabs + يمسح الـ cache
_refresh_tabs()                 # = _build_tabs()

_on_company_changed(company_id) # AppState.invalidate() + _refresh_tabs() + bus.company_data_changed
_on_nav(clicked_btn)            # تبديل الـ stack index
_open_shared_items()            # يفتح SharedItemsManagerDialog
```

**سلوكيات خاصة:**
- `"settings"` nav → يفتح `SettingsDialog` ثم `sidebar.refresh_all_buttons()` — لا يغير الـ stack
- `"shared_items"` nav → يفتح `SharedItemsManagerDialog` مباشرة
- عند تغيير الشركة → `AppState.invalidate()` أولاً (يمسح font_size cache)

---

## Sidebar — المكونات

### `ui/main_window_helper/_sidebar.py` — `_Sidebar(QFrame)`

```python
_Sidebar(on_company_changed: callable, parent=None)
# Fixed width: SIDEBAR_EXPANDED_WIDTH (224px) افتراضياً
# SizePolicy: Fixed × Expanding
```

**هيكل الـ Layout:**
```
QVBoxLayout
├── CompanySelector          (height=46, border-bottom)
├── QScrollArea (nav_scroll)
│   └── QWidget (nav_widget)
│       ├── _SectionLabel("الإنتاج")
│       ├── _NavButton(📊, "حساب التكلفة", key="costing")
│       ├── _NavButton(💰, "التسعير", key="pricing")
│       ├── _SectionLabel("المالية")
│       ├── _NavButton(🏦, "الحسابات", key="accounting")
│       ├── _NavButton(📦, "المخزن", key="inventory")
│       ├── _SectionLabel("العمل")
│       ├── _NavButton(🎨, "التصميمات", key="design")
│       └── _NavButton(📋, "الطلبات", key="orders")
└── footer
    ├── QFrame (separator)
    ├── _NavButton(🔗, "العناصر المشتركة", key="shared_items")
    ├── _NavButton(⚙️, "الإعدادات", key="settings")
    └── _ToggleButton
```

**API:**
```python
sidebar.get_buttons() -> list[_NavButton]
sidebar.get_company_selector() -> CompanySelector
sidebar.refresh_all_buttons()
```

**الـ collapse animation:**
- Duration: 200ms، EasingCurve: InOutCubic
- Target widths: `SIDEBAR_COLLAPSED_WIDTH (56)` أو `SIDEBAR_EXPANDED_WIDTH (224)`
- عند collapse: CompanySelector يختفي، الأزرار تُخفي النصوص

---

### `ui/main_window_helper/_nav_button.py` — `_NavButton(QPushButton)`

```python
_NavButton(icon: str, label: str, badge: str = "", parent=None)
# setCheckable(True)
# SizePolicy: Fixed × Fixed
```

**Layout داخلي (QHBoxLayout):**
```
[_txt_lbl (stretch=1)] [_badge_lbl] [_ico_lbl (22px)]
```

**API:**
```python
btn.set_badge(text)
btn.set_collapsed(collapsed)
btn.refresh_sizes()
btn.setChecked(v)
btn.property("nav_key")  # "costing" | "pricing" | etc.
```

**الثوابت المُعاد تصديرها:**
```python
from ui.main_window_helper._nav_button import (
    SIDEBAR_EXPANDED_WIDTH,   # 224
    SIDEBAR_COLLAPSED_WIDTH,  # 56
    CONTENT_MIN_WIDTH,        # 820
    WINDOW_DEFAULT_W,         # 1044
)
```

---

### `ui/main_window_helper/_section_label.py` — `_SectionLabel(QLabel)`

```python
_SectionLabel(text: str, parent=None)
# النص يُحوَّل تلقائياً لـ UPPERCASE
```

**API:**
```python
lbl._apply_style()
lbl.set_collapsed(collapsed)  # setVisible(not collapsed)
```

---

### `ui/main_window_helper/_toggle_button.py` — `_ToggleButton(QPushButton)`

```python
_ToggleButton(parent=None)
# height: 36px

btn.toggle_state() -> bool
# True = collapsed, False = expanded
```

---

## Tabs — Sections الرئيسية

### `ui/tabs/costing_section.py` — `CostingSection` → index 1

```python
CostingSection()
# QTabWidget داخلي:
# ├── "المنتجات"    → ProductTab(conn)
# ├── "الخامات"     → RawTab(conn)
# ├── "العمالة"     → LaborTab(conn)
# └── "التشغيل"     → MachineTab(conn)
```

---

### `ui/tabs/pricing_section.py` — `PricingSection` → index 2

```python
PricingSection()
# QTabWidget داخلي:
# ├── "التسعير"  → PricingTab(conn)
# └── "العروض"   → OffersTab(conn)
```

---

### `ui/tabs/accounting_section.py` — `AccountingTab` → index 3

```python
AccountingTab()
# QTabWidget داخلي:
# ├── "الحسابات"        → AccountsTree(conn)
# ├── "القيود"           → JournalTab(conn)
# ├── "دفتر الأستاذ"    → LedgerTab(conn)
# ├── "سجل المراجعة"    → AuditLogTab(conn)
# ├── "التقارير المالية" → FinancialStatements(conn)
# └── "المستثمرون"       → InvestorsTab(conn)
```

---

### `ui/tabs/inventory_section.py` — `InventoryTab` → index 4

```python
InventoryTab()
# QTabWidget داخلي:
# ├── "الأصناف"   → InventoryItemsTab(conn)
# ├── "وارد"      → InventoryInboundTab(conn)
# ├── "صادر"      → InventoryOutboundTab(conn)
# └── "التقارير"  → InventoryReportTab(conn)
```

---

### `ui/tabs/design_section.py` — `DesignSection` → index 5

```python
DesignSection()
# QTabWidget داخلي:
# ├── "التصميمات"       → DesignsTab(conn)
# └── "مجموعات الأبعاد" → DimensionSetsTab(conn)
```

---

### `ui/tabs/orders_section.py` — `OrdersSection` → index 6

```python
OrdersSection()
# QTabWidget داخلي:
# ├── "لوحة التحكم" → DashboardTab(conn)
# ├── "الطلبات"     → OrdersTab(conn)
# └── "العملاء"     → CustomersTab(conn)
```

---

## Tabs — التكلفة

### `ui/tabs/costing/product_tab.py` — `ProductTab`

```python
ProductTab(conn)
# Sub-widgets:
#   product_table.py      → ProductTable
#   product_form.py       → ProductForm
#   product_main_panel.py → ProductMainPanel
```

**`ProductMainPanel`:**
- `_header_bar.py` → `_HeaderBar`
- `_rows_manager.py` → `_RowsManager`
- `_save_logic.py` → `_SaveLogic`

**مكونات BOM المشتركة:**
```python
# ui/tabs/costing/shared/
bom_scenarios_panel.py        → BomScenariosPanel
bom_tree.py                   → BomTree
component_row.py              → ComponentRow
catalog_builder.py            → CatalogBuilder
raw_variants_panel.py         → RawVariantsPanel
machine_op_rows_editor.py     → MachineOpRowsEditor
scenario_comparison_widget.py → ScenarioComparisonWidget
bulk_replace/                 → BulkReplaceDialog
```

---

### `ui/tabs/costing/raw_tab.py` — `RawTab`

```python
RawTab(conn)
# Sub-widgets:
#   raw/raw_table_panel.py → RawTablePanel
#   raw/raw_section.py     → RawSection
#   raw/raw_input_panel.py → RawInputPanel
```

---

### `ui/tabs/costing/labor_tab.py` — `LaborTab`

```python
LaborTab(conn)
# Sub-widgets:
#   labor/labor_op_table.py  → LaborOpTable
#   labor/labor_op_form.py   → LaborOpForm
#   labor/labor_settings.py  → LaborSettings
```

---

### `ui/tabs/costing/machine_tab.py` — `MachineTab`

```python
MachineTab(conn)
# Sub-widgets:
#   machine/machine_table.py    → MachineTable
#   machine/machine_form.py     → MachineForm
#   machine/machine_op_table.py → MachineOpTable
#   machine/machine_op_form.py  → MachineOpForm
```

---

## Tabs — التسعير

### `ui/tabs/pricing/pricing_tab.py` — `PricingTab`

```python
PricingTab(conn)
# Sub-widgets:
#   pricing/_pricing_panel.py → _PricingPanel
#   pricing/_stat_box.py      → _StatBox
```

---

### `ui/tabs/pricing/offers/offers_tab.py` — `OffersTab`

```python
OffersTab(conn)
# Sub-widgets:
#   offers/offers_table.py   → OffersTable
#   offers/offer_form.py     → OfferForm
#   offers/offer_details.py  → OfferDetails
#   offers/offer_item_row.py → OfferItemRow
```

---

## Tabs — المحاسبة

### `ui/tabs/accounting/accounts_tree.py` — `AccountsTree`

```python
AccountsTree(conn)
# Sub-widgets:
#   tree/_account_form.py  → _AccountForm
#   tree/_group_filter.py  → _GroupFilter
#   tree/_tree_builder.py  → _TreeBuilder
#   tree/_tree_headers.py  → _TreeHeaders
#   tree/_tree_nodes.py    → _TreeNodes
```

---

### `ui/tabs/accounting/journal_tab.py` — `JournalTab`

```python
JournalTab(conn)
# Sub-widgets:
#   journal/journal_tab_widget.py    → JournalTabWidget
#   journal/journal_form.py          → JournalForm
#   journal/journal_tree_table.py    → JournalTreeTable
#   journal/journal_filter.py        → JournalFilter
#   journal/journal_lines.py         → JournalLines
#   journal/journal_account_picker.py → JournalAccountPicker
#   journal/journal_group_combo.py   → JournalGroupCombo
#   form/_balance_bar.py             → _BalanceBar
#   form/_entry_meta.py              → _EntryMeta
#   form/_journal_header.py          → _JournalHeader
#   lines/_lines_panel.py            → _LinesPanel
#   lines/_smart_line.py             → _SmartLine
```

---

### `ui/tabs/accounting/ledger_tab.py` — `LedgerTab`

```python
LedgerTab(conn)
# Sub-widgets:
#   ledger/ledger_accounts_panel.py → LedgerAccountsPanel
#   ledger/ledger_filter_bar.py     → LedgerFilterBar
#   ledger/ledger_stat_cards.py     → LedgerStatCards
#   ledger/ledger_t_account.py      → LedgerTAccount
```

---

### `ui/tabs/accounting/audit_log_tab.py` — `AuditLogTab`

```python
AuditLogTab(conn)
# سجل المراجعة — عرض audit_log مع فلتر
```

---

### `ui/tabs/accounting/financial_statements.py` — `FinancialStatements`

```python
FinancialStatements(conn)
# QTabWidget داخلي:
# ├── "ميزان المراجعة"  → TrialBalanceTab
# ├── "قائمة الدخل"     → IncomeStatementTab
# ├── "الميزانية"        → BalanceSheetTab
# └── "حقوق الملكية"    → OwnersEquityTab
```

---

### `ui/tabs/accounting/investors_tab.py` — `InvestorsTab`

```python
InvestorsTab(conn)
# Sub-widgets (investors/):
#   _investors_layout.py    → _InvestorsLayout
#   _investors_panel.py     → _InvestorsPanel
#   _investors_table.py     → _InvestorsTable
#   _investor_form.py       → _InvestorForm
#   _investor_details.py    → _InvestorDetails
#   _details_table.py       → _DetailsTable
#   _movement_dialog.py     → _MovementDialog
#   _link_to_entry_panel.py → _LinkToEntryPanel
```

---

## Tabs — المخزن

### `ui/tabs/inventory/inventory_items_tab.py` — `InventoryItemsTab`

```python
InventoryItemsTab(conn)
# Sub-widgets (items/):
#   _item_form.py   → _ItemForm
#   _items_tab.py   → _ItemsTab
#   _items_table.py → _ItemsTable
```

---

### `ui/tabs/inventory/inventory_inbound_tab.py` — `InventoryInboundTab`

```python
InventoryInboundTab(conn)
```

---

### `ui/tabs/inventory/inventory_outbound_tab.py` — `InventoryOutboundTab`

```python
InventoryOutboundTab(conn)
```

---

### `ui/tabs/inventory/inventory_report_tab.py` — `InventoryReportTab`

```python
InventoryReportTab(conn)
```

---

## Tabs — التصميمات

### `ui/tabs/design/designs_tab.py` — `DesignsTab`

```python
DesignsTab(conn)
# Sub-widgets (designs/):
#   _design_detail_panel.py      → _DesignDetailPanel
#   _designs_categories_panel.py → _DesignsCategoriesPanel
#   _designs_table.py            → _DesignsTable
#   _size_card.py                → _SizeCard
#   _size_dialog.py              → _SizeDialog
#   _xcf_thumbnail.py            → _XcfThumbnail
```

---

### `ui/tabs/design/dimension_sets_tab.py` — `DimensionSetsTab`

```python
DimensionSetsTab(conn)
# Sub-widgets (dimension_sets/):
#   _categories_panel.py     → _CategoriesPanel
#   _sets_panel.py           → _SetsPanel
#   _fields_panel.py         → _FieldsPanel
#   _groups_panel.py         → _GroupsPanel
#   _field_dialog.py         → _FieldDialog
#   _values_panel.py         → _ValuesPanel
#   _source_picker_dialog.py → _SourcePickerDialog
```

---

## Tabs — الطلبات

### `ui/tabs/orders/dashboard_tab.py` — `DashboardTab`

```python
DashboardTab(conn)
# Sub-widgets (dashboard/):
#   _config.py       → _Config
#   _top_cards.py    → _TopCards
#   _status_grid.py  → _StatusGrid
#   _recent_table.py → _RecentTable
```

---

### `ui/tabs/orders/orders_tab.py` — `OrdersTab`

```python
OrdersTab(conn)
# Sub-widgets:
#   _order_form.py              → _OrderForm
#   _order_detail.py            → _OrderDetail
#   orders/_filter_toolbar.py   → _FilterToolbar
#   orders/_orders_list_panel.py → _OrdersListPanel
#   orders/_status_delegate.py  → _StatusDelegate
#   order_form/_item_row_widget.py  → _ItemRowWidget
#   order_form/_products_fetcher.py → _ProductsFetcher
#   order_detail/_header_fill.py    → _HeaderFill
#   order_detail/_items_section.py  → _ItemsSection
#   order_detail/_log_section.py    → _LogSection
#   order_detail/_status_dialog.py  → _StatusDialog
```

---

### `ui/tabs/orders/customers_tab.py` — `CustomersTab`

```python
CustomersTab(conn)
# Sub-widgets:
#   _customer_form.py                    → _CustomerForm
#   customers/customers_list_panel.py    → CustomersListPanel
#   customers/customer_detail_panel.py   → CustomerDetailPanel
```

---

## Tabs — الشركات

### `ui/tabs/companies/company_selector.py` — `CompanySelector(QWidget)`

```python
CompanySelector()
# Signals: company_changed(int)
selector._open_manager()
```

---

### `ui/tabs/companies/companies_dialog.py` — `CompaniesDialog`

```python
CompaniesDialog(parent=None)
```

---

### `ui/tabs/companies/no_company_screen.py` — `NoCompanyScreen`

```python
NoCompanyScreen()
# Signals: open_manager
# index 0 في الـ stack
```

---

### `ui/tabs/companies/shared_items_manager.py` — `SharedItemsManagerDialog`

```python
SharedItemsManagerDialog(central_conn, parent=None)
# Signals: items_changed
```

---

## ملاحظات التطوير

**1. إضافة Tab جديدة:**
```python
# في MainWindow._build_tabs():
from ui.tabs.my_section import MySection
self._stack.addWidget(MySection())  # index N

# في index_map:
"my_key": N

# في _sidebar._build():
_NavButton("🔑", "اسم القسم", key="my_key")
```

**2. bus events في الـ Tabs:**
- الـ tabs تشترك في `bus.company_data_changed` عبر `BusConnectedMixin`
- عند تغيير الشركة: `MainWindow._on_company_changed()` → `_destroy_tabs()` → `_build_tabs()` → tabs جديدة

**3. الـ connections:**
- كل tab تحصل على `conn` من `company_state.get_erp_conn()` وقت الإنشاء
- `ProtectedConnection` لا تُغلق يدوياً — يديرها `company_state`

**4. الـ Placeholder tabs:**
```python
_make_placeholder_tab(section_name) -> QWidget
# يظهر "🚧 قيد التطوير"
```
ENDOFFILE
Output

exit code 0
