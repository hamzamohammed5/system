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
1. init_db()                        ← تهيئة companies.db فقط
2. QApplication(sys.argv)
3. theme_manager.load_from_db()     ← تحميل الثيم المحفوظ
4. i18n_manager.load_from_db()      ← تحميل اللغة المحفوظة
5. app.setStyleSheet(_build_stylesheet(get_font_size()))
6. app.setLayoutDirection(i18n_manager.qt_direction)
7. install_no_wheel_filter(app)     ← منع عجلة الماوس على inputs
8. install_shift_wheel_filter(app)  ← Shift+Wheel مسموح
9. MainWindow(app).show()
10. app.exec_()
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
# يحدث أحجام الأزرار + _SectionLabels عند تغيير حجم الخط
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
الترتيب RTL: أيقونة يمين، نص يسار.

**API:**
```python
btn.set_badge(text)           # يُظهر/يُخفي الـ badge
btn.set_collapsed(collapsed)  # يُخفي النص والـ badge + يغير العرض
btn.refresh_sizes()           # يحدث أحجام الخط عند تغيير الإعدادات
btn.setChecked(v)             # يغير الـ style (active/inactive)

# nav_key property:
btn.property("nav_key")       # "costing" | "pricing" | etc.
```

**الثوابت المُعاد تصديرها (للـ imports القديمة):**
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
lbl._apply_style()        # يُطبق الـ stylesheet الحالي (يُستدعى من refresh_all_buttons)
lbl.set_collapsed(collapsed)  # setVisible(not collapsed)
```

**Style:** `color: sidebar_muted | font-size: fs(base, -2) | font-weight: 700 | letter-spacing: 1.5px`

---

### `ui/main_window_helper/_toggle_button.py` — `_ToggleButton(QPushButton)`

```python
_ToggleButton(parent=None)
# height: 36px
# cursor: PointingHandCursor
```

**API:**
```python
btn.toggle_state() -> bool
# يبدل الحالة ويرجع: True = collapsed, False = expanded
# يغير النص: "◀" (expanded) أو "▶" (collapsed)
# يغير الـ tooltip: "طي الشريط الجانبي" / "فرد الشريط الجانبي"
```

---

## Tabs — Sections الرئيسية

كل section هي الـ widget اللي بتتحط في الـ `_stack` في `MainWindow`.

### `ui/tabs/costing_section.py` — `CostingSection` → index 1

```python
CostingSection()
# QTabWidget داخلي بتبويبات:
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
# يُبنى عبر accounting_tabs_builder.py
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
# قسم CRUD للمنتجات (semi + final)
# يشمل: قائمة المنتجات + فورم BOM + حساب التكلفة
# Sub-widgets:
#   product_table.py  → ProductTable     (قائمة المنتجات)
#   product_form.py   → ProductForm      (فورم الإضافة/التعديل)
#   product_main_panel.py → ProductMainPanel
```

**`ProductMainPanel`** — اللوحة الرئيسية:
- `_header_bar.py` → `_HeaderBar` — شريط العنوان + أزرار الإجراءات
- `_rows_manager.py` → `_RowsManager` — إدارة صفوف BOM
- `_save_logic.py` → `_SaveLogic` — منطق الحفظ

**مكونات BOM المشتركة:**
```python
# ui/tabs/costing/shared/
bom_scenarios_panel.py   → BomScenariosPanel    # إدارة السيناريوهات
bom_tree.py              → BomTree              # شجرة عرض BOM
component_row.py         → ComponentRow         # صف مكون واحد
catalog_builder.py       → CatalogBuilder       # بناء الكاتالوج
raw_variants_panel.py    → RawVariantsPanel     # إدارة variants الخامات
machine_op_rows_editor.py → MachineOpRowsEditor # محرر صفوف عمليات التشغيل
scenario_comparison_widget.py → ScenarioComparisonWidget
bulk_replace/            → BulkReplaceDialog    # استبدال مكون في منتجات متعددة
```

---

### `ui/tabs/costing/raw_tab.py` — `RawTab`

```python
RawTab(conn)
# قسم CRUD للخامات
# Sub-widgets:
#   raw/raw_table_panel.py  → RawTablePanel   (جدول الخامات)
#   raw/raw_section.py      → RawSection      (القسم الكامل)
#   raw/raw_input_panel.py  → RawInputPanel   (فورم الإدخال)
```

---

### `ui/tabs/costing/labor_tab.py` — `LaborTab`

```python
LaborTab(conn)
# قسم CRUD لعمليات العمالة
# Sub-widgets:
#   labor/labor_op_table.py  → LaborOpTable
#   labor/labor_op_form.py   → LaborOpForm
#   labor/labor_settings.py  → LaborSettings  (إعدادات الراتب/ساعات العمل)
```

---

### `ui/tabs/costing/machine_tab.py` — `MachineTab`

```python
MachineTab(conn)
# قسم CRUD للماكينات وعمليات التشغيل
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
# جدول أسعار المنتجات النهائية مع هامش الربح
# Sub-widgets:
#   pricing/_pricing_panel.py → _PricingPanel
#   pricing/_stat_box.py      → _StatBox      (إجماليات)
```

---

### `ui/tabs/pricing/offers/offers_tab.py` — `OffersTab`

```python
OffersTab(conn)
# CRUD للعروض
# Sub-widgets:
#   offers/offers_table.py  → OffersTable
#   offers/offer_form.py    → OfferForm
#   offers/offer_details.py → OfferDetails
#   offers/offer_item_row.py → OfferItemRow  (صف منتج في العرض)
```

---

## Tabs — المحاسبة

### `ui/tabs/accounting/accounts_tree.py` — `AccountsTree`

```python
AccountsTree(conn)
# شجرة الحسابات مع CRUD + مجموعات الحسابات
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
# قيود محاسبية — قائمة + فورم
# Sub-widgets:
#   journal/journal_tab_widget.py   → JournalTabWidget   (الهيكل الكامل)
#   journal/journal_form.py         → JournalForm        (فورم القيد)
#   journal/journal_tree_table.py   → JournalTreeTable   (جدول القيود)
#   journal/journal_filter.py       → JournalFilter      (فلتر بحث)
#   journal/journal_lines.py        → JournalLines       (صفوف القيد)
#   journal/journal_account_picker.py → JournalAccountPicker
#   journal/journal_group_combo.py  → JournalGroupCombo

# form/ sub-widgets:
#   form/_balance_bar.py   → _BalanceBar   (شريط التوازن)
#   form/_entry_meta.py    → _EntryMeta    (بيانات القيد)
#   form/_journal_header.py → _JournalHeader

# lines/ sub-widgets:
#   lines/_lines_panel.py  → _LinesPanel   (لوحة الصفوف)
#   lines/_smart_line.py   → _SmartLine    (صف ذكي)
```

---

### `ui/tabs/accounting/ledger_tab.py` — `LedgerTab`

```python
LedgerTab(conn)
# دفتر الأستاذ — حركات الحساب
# Sub-widgets:
#   ledger/ledger_accounts_panel.py → LedgerAccountsPanel
#   ledger/ledger_filter_bar.py     → LedgerFilterBar
#   ledger/ledger_stat_cards.py     → LedgerStatCards
#   ledger/ledger_t_account.py      → LedgerTAccount  (حساب T)
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

# financial/ sub-widgets:
#   financial/trial_balance_tab.py     → TrialBalanceTab
#   financial/income_statement_tab.py  → IncomeStatementTab
#   financial/balance_sheet_tab.py     → BalanceSheetTab
#   financial/owners_equity_tab.py     → OwnersEquityTab
#   financial/_financial_helpers.py    → helpers مشتركة
```

---

### `ui/tabs/accounting/investors_tab.py` — `InvestorsTab`

```python
InvestorsTab(conn)
# CRUD للمستثمرين + ربطهم بالقيود
# Sub-widgets (investors/):
#   _investors_layout.py    → _InvestorsLayout   (الهيكل الكامل)
#   _investors_panel.py     → _InvestorsPanel    (قائمة المستثمرين)
#   _investors_table.py     → _InvestorsTable    (الجدول)
#   _investor_form.py       → _InvestorForm      (فورم الإضافة/التعديل)
#   _investor_details.py    → _InvestorDetails   (تفاصيل المستثمر)
#   _details_table.py       → _DetailsTable      (جدول الحركات)
#   _helpers.py             → helpers
#   _movement_dialog.py     → _MovementDialog    (dialog إضافة حركة)
#   _link_to_entry_panel.py → _LinkToEntryPanel  (ربط بقيد)
```

**Helper tabs:**
```python
# ui/tabs/accounting/
accounting_tabs_builder.py   → AccountingTabsBuilder   # يبني كل الـ tabs
_conn_guard.py               → _ConnGuard              # حماية الاتصال
_state_widgets.py            → _StateWidgets           # شاشات الحالة الفارغة
account_combo.py             → AccountCombo            # combo اختيار الحساب
accounts_combo_widget.py     → AccountsComboWidget
group_manager.py             → GroupManager            # إدارة مجموعات الحسابات
helpers.py                   → helpers مشتركة
```

---

## Tabs — المخزن

### `ui/tabs/inventory/inventory_items_tab.py` — `InventoryItemsTab`

```python
InventoryItemsTab(conn)
# CRUD لأصناف المخزن
# Sub-widgets (items/):
#   _item_form.py   → _ItemForm
#   _items_tab.py   → _ItemsTab
#   _items_table.py → _ItemsTable
```

---

### `ui/tabs/inventory/inventory_inbound_tab.py` — `InventoryInboundTab`

```python
InventoryInboundTab(conn)
# تسجيل حركات الوارد (stock in)
```

---

### `ui/tabs/inventory/inventory_outbound_tab.py` — `InventoryOutboundTab`

```python
InventoryOutboundTab(conn)
# تسجيل حركات الصادر (stock out)
```

---

### `ui/tabs/inventory/inventory_report_tab.py` — `InventoryReportTab`

```python
InventoryReportTab(conn)
# تقارير المخزن — رصيد + حركات + تقييم
```

---

## Tabs — التصميمات

### `ui/tabs/design/designs_tab.py` — `DesignsTab`

```python
DesignsTab(conn)
# CRUD للتصميمات
# Sub-widgets (designs/):
#   _design_detail_panel.py      → _DesignDetailPanel
#   _designs_categories_panel.py → _DesignsCategoriesPanel
#   _designs_table.py            → _DesignsTable
#   _size_card.py                → _SizeCard          (بطاقة مقاس)
#   _size_dialog.py              → _SizeDialog
#   _xcf_thumbnail.py            → _XcfThumbnail      (معاينة ملف GIMP)
#   designs_categories/          → _row_and_form.py
#   designs_table/_design_card.py → _DesignCard
#   size_card/helper.py
#   design_detail_panel/         → sub-components
```

---

### `ui/tabs/design/dimension_sets_tab.py` — `DimensionSetsTab`

```python
DimensionSetsTab(conn)
# إدارة مجموعات الأبعاد والحقول والقيم
# Sub-widgets (dimension_sets/):
#   _categories_panel.py → _CategoriesPanel
#   _sets_panel.py       → _SetsPanel        (قائمة المجموعات)
#   _fields_panel.py     → _FieldsPanel      (حقول المجموعة)
#   _groups_panel.py     → _GroupsPanel
#   _field_dialog.py     → _FieldDialog      (dialog إضافة/تعديل حقل)
#   _values_panel.py     → _ValuesPanel      (قيم الـ instances)
#   _source_picker_dialog.py → _SourcePickerDialog
#   values_panel/        → _instance_popup, _instances_table, _sets_list_panel
```

**Design styles مشتركة:**
```python
# ui/tabs/design/design_styles.py
design_styles.py  → دوال style مشتركة للتصميمات
```

---

## Tabs — الطلبات

### `ui/tabs/orders/dashboard_tab.py` — `DashboardTab`

```python
DashboardTab(conn)
# لوحة تحكم الطلبات — إحصائيات + آخر الطلبات
# Sub-widgets (dashboard/):
#   _config.py       → _Config         (إعدادات الألوان والحالات)
#   _top_cards.py    → _TopCards       (بطاقات الإحصاء العلوية)
#   _status_grid.py  → _StatusGrid     (شبكة الحالات)
#   _recent_table.py → _RecentTable    (جدول آخر الطلبات)
```

---

### `ui/tabs/orders/orders_tab.py` — `OrdersTab`

```python
OrdersTab(conn)
# CRUD للطلبات
# Sub-widgets:
#   _order_form.py   → _OrderForm      (فورم الطلب)
#   _order_detail.py → _OrderDetail    (تفاصيل الطلب)
#
# orders/
#   _filter_toolbar.py    → _FilterToolbar
#   _orders_list_panel.py → _OrdersListPanel
#   _status_delegate.py   → _StatusDelegate  (delegate لعرض حالة الطلب)
#
# order_form/
#   _item_row_widget.py  → _ItemRowWidget   (صف منتج في الطلب)
#   _products_fetcher.py → _ProductsFetcher (جلب المنتجات)
#
# order_detail/
#   _header_fill.py   → _HeaderFill
#   _items_section.py → _ItemsSection
#   _log_section.py   → _LogSection    (سجل تغيير الحالة)
#   _status_config.py → _StatusConfig
#   _status_dialog.py → _StatusDialog  (dialog تغيير الحالة)
```

---

### `ui/tabs/orders/customers_tab.py` — `CustomersTab`

```python
CustomersTab(conn)
# CRUD للعملاء
# Sub-widgets:
#   _customer_form.py  → _CustomerForm
#
# customers/
#   customers_list_panel.py  → CustomersListPanel
#   customer_detail_panel.py → CustomerDetailPanel
```

---

## Tabs — الشركات

### `ui/tabs/companies/company_selector.py` — `CompanySelector(QWidget)`

```python
CompanySelector()
# Signals: company_changed(int)
# الـ widget العلوي في الـ Sidebar
# يُطلق company_changed عند تغيير الشركة النشطة
# يفتح CompaniesDialog عند الضغط على "إدارة"

selector._open_manager()   # يفتح نافذة إدارة الشركات
```

---

### `ui/tabs/companies/companies_dialog.py` — `CompaniesDialog`

```python
CompaniesDialog(parent=None)
# نافذة إدارة الشركات (إضافة، تعديل، تفعيل/تعطيل، حذف)
```

---

### `ui/tabs/companies/no_company_screen.py` — `NoCompanyScreen`

```python
NoCompanyScreen()
# Signals: open_manager
# شاشة "لا توجد شركة نشطة" — index 0 في الـ stack
# تظهر عند بدء التطبيق بدون شركة محددة
```

---

### `ui/tabs/companies/shared_items_manager.py` — `SharedItemsManagerDialog`

```python
SharedItemsManagerDialog(central_conn, parent=None)
# Signals: items_changed
# نافذة إدارة العناصر المشتركة بين الشركات
# Sub-widgets:
#   shared_items_manager_helper/_add_shared_item_dialog.py → _AddSharedItemDialog
```

**دوال مساعدة أخرى:**
```python
# ui/tabs/companies/
shared_items_dialog.py  → SharedItemsDialog   # dialog اختيار عناصر مشتركة
shared_items_mixin.py   → SharedItemsMixin    # Mixin للـ tabs اللي تدعم العناصر المشتركة
_link_item_picker.py    → _LinkItemPicker     # picker لربط عنصر بشركة
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
# يُستخدم مؤقتاً أثناء التطوير بدل الـ widget الحقيقي
# يظهر "🚧 قيد التطوير"
```