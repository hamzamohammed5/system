# خطة إعادة هيكلة النظام — تحويل tabs/ إلى Orchestrators

**الهدف الاستراتيجي:**
```
tabs/UI ──→ services/ ──→ repos/ (db/)
  ↑                                ↑
widgets/ (base classes)       schema/
```

---

## 0. القواعد العامة للتطبيق

1. **لا wrapper files** — كل استدعاء يذهب مباشرة للملف الذي يحتوي الكود الفعلي.
2. **لا ملفات وسيطة بلا قيمة** — أي ملف يستورد ملفاً آخر فقط ليعيد تصديره يُحذف.
3. **BaseListPanel / BaseSection / BaseDetailPanel / BaseCrudForm** هي الأساس — لا إعادة اختراع.
4. **bus.company_data_changed** للإشعارات الجديدة، **bus.data_changed** للتوافق القديم.
5. **tr()** لكل نص ظاهر للمستخدم — لا نصوص عربية hardcoded في الكود.
6. **LiveConnMixin._live_conn()** لأي DB connection — لا استدعاء مباشر لـ company_state خارج المكان المناسب.

---

## 1. تحليل الوضع الحالي

### 1.1 ملفات تفتقد لها مراجع في الكود (Missing Files)

من تحليل الكود الموجود مقابل system_arch.txt:

| الملف المُستدعى | الملف الفعلي | الإجراء |
|---|---|---|
| `ui/widgets/core/__init__.py` (مُستدعى: `from ..core import get_font_size`) | غير مذكور في system_arch | **إنشاء** `ui/widgets/core/__init__.py` يصدّر `get_font_size` من `ui.app_settings` |
| `ui/widgets/panels/form_parts.py` → `FormGroup` | موجود في system_arch | ✅ موجود |
| `ui/tabs/costing/shared/_utils.py` → `SHARED_COLOR, SHARED_BG, PUBLISHED_COLOR, PUBLISHED_BG` | موجود في system_arch | يحتاج تحقق من المحتوى |
| `ui/tabs/companies/shared_items_mixin.py` → `get_published_local_names, is_shared_id, extract_shared_id` | موجود في system_arch | يحتاج تحقق |
| `services/costing/catalog_service.py` | موجود في system_arch | ✅ موجود |

### 1.2 استدعاءات غير مباشرة تحتاج توحيد

```python
# في list_panel_with_shared.py:
from ui.widgets.base.list_panel import BaseListPanel  # ✅ مباشر

# لكن:
def _live_conn(self):
    from db.shared.connection import get_connection
    return get_connection()  # ❌ يتجاهل LiveConnMixin الموروث!
```

---

## 2. ملف `ui/widgets/core/__init__.py` — ينقصنا

الكود في عدة ملفات يستدعي:
```python
from ..core import get_font_size
```
هذا يعني `ui/widgets/core/__init__.py` يجب أن يوجد.

**الملف المطلوب:**
```python
# ui/widgets/core/__init__.py
from ui.app_settings import get_font_size

__all__ = ["get_font_size"]
```

---

## 3. تحليل كل tab وما يحتاجه

### 3.1 `ui/tabs/costing/` — الأكثر تعقيداً

#### الملفات الموجودة:
- `raw_tab.py` → يستخدم `raw_section.py` → `raw_input_panel.py` + `raw_table_panel.py`
- `labor_tab.py` → `labor/labor_op_form.py` + `labor/labor_op_table.py`
- `machine_tab.py` → `machine/machine_form.py` + `machine/machine_op_form.py` + `machine/machine_table.py` + `machine/machine_op_table.py`
- `product_tab.py` → `product/product_form.py` + `product/product_main_panel.py` + `product/product_table.py`

#### المشاكل المحتملة في costing:

**A. `raw_table_panel.py`** يرث من `SharedItemsListPanel` (موجود في `shared/list_panel_with_shared.py`).
- يجب أن يرث من `BaseListPanel` مباشرة وينفذ hooks.
- `_live_conn` في `SharedItemsListPanel` يتجاهل `LiveConnMixin` — **يحتاج إصلاح**.

**B. `product/form/_rows_manager.py`** يدير `ComponentRow` instances.
- `ComponentRow` يستخدم `bus.data_changed` فقط — يحتاج ربط `company_data_changed`.

**C. `shared/bom_scenarios/`** يحتوي ملفين:
- `_db_scenarios.py` — سيناريوهات محفوظة في DB
- `_memory_scenarios.py` — سيناريوهات مؤقتة في الذاكرة
- يجب أن يستخدما `services/costing/scenario_service.py` مباشرة.

**D. `shared/bulk_replace/`** — يستخدم `services/costing/bulk_replace_service.py`.

#### مفاتيح ترجمة ناقصة في costing:
لا توجد مفاتيح ناقصة كبيرة — `ar.py` و `en.py` يغطيان معظم costing strings.
لكن يحتاج التحقق من:
- رسائل validation في `product_form.py`
- عناوين tabs في `costing_section.py`

---

### 3.2 `ui/tabs/accounting/` — معقد جداً

#### الهيكل الحالي (من system_arch):
```
accounting/
├── financial/ (4 tabs: balance_sheet, income, owners_equity, trial_balance)
├── investors/ (8 ملفات — panel, form, table, details, dialog)
├── journal/ (account_picker, form, group_combo, lines, filter, tree_table, widget)
├── ledger/ (accounts_panel, filter_bar, stat_cards, t_account)
├── tree/ (account_form, group_filter, tree_builder, tree_headers, tree_nodes)
└── +15 ملف في الجذر
```

#### المشاكل:
- `accounting_tabs_builder.py` + `helpers.py` قد تكون wrapper files تحتاج دمج.
- `_conn_guard.py` — إذا كان wrapper لـ `LiveConnMixin` أو `requires_company` يُحذف ويُستبدل.
- `account_combo.py` + `accounts_combo_widget.py` — محتمل تكرار، يحتاج دمج.

#### مفاتيح ترجمة ناقصة لـ accounting:
```python
# في ar.py و en.py — يحتاج إضافة:
"investors":                "المستثمرون",          # "Investors"
"investor_add":             "إضافة مستثمر",       # "Add Investor"
"investor_movement":        "حركة مستثمر",        # "Investor Movement"
"link_to_entry":            "ربط بقيد",           # "Link to Entry"
"account_group":            "مجموعة الحسابات",    # "Account Group"
"account_nature":           "طبيعة الحساب",       # "Account Nature"
"debit_nature":             "مدين",               # "Debit"
"credit_nature":            "دائن",               # "Credit"
"account_level":            "مستوى الحساب",       # "Account Level"
"account_tree":             "شجرة الحسابات",      # "Account Tree"
"fiscal_year":              "السنة المالية",      # "Fiscal Year"
"period":                   "الفترة",             # "Period"
"owners_equity":            "حقوق الملكية",       # "Owners Equity"
"audit_log":                "سجل المراجعة",       # "Audit Log"
```

---

### 3.3 `ui/tabs/inventory/` — متوسط التعقيد

#### الهيكل:
```
inventory/
├── items/ (_item_form.py, _items_tab.py, _items_table.py)
├── inventory_inbound_tab.py
├── inventory_outbound_tab.py
├── inventory_items_tab.py
├── inventory_report_tab.py
```

#### المشاكل المحتملة:
- `_items_tab.py` + `inventory_items_tab.py` — احتمال تكرار، يحتاج مراجعة.
- يجب أن يستخدم `db/inventory/inventory_repo.py` عبر service layer.

**لا يوجد inventory service في `services/`** — هذا إغفال مهم!
- يحتاج إنشاء `services/inventory/inventory_service.py` أو استخدام `inventory_repo.py` مباشرة إذا كانت العمليات بسيطة.

#### مفاتيح ترجمة ناقصة لـ inventory:
```python
# في ar.py و en.py:
"inbound":                  "وارد",               # "Inbound"
"outbound":                 "صادر",               # "Outbound"
"inventory_report":         "تقرير المخزون",      # "Inventory Report"
"item_name":                "اسم الصنف",          # "Item Name"
"item_type":                "نوع الصنف",          # "Item Type"
"min_stock":                "الحد الأدنى",        # "Min Stock"
"current_balance":          "الرصيد الحالي",      # "Current Balance"
"movement_date":            "تاريخ الحركة",       # "Movement Date"
"movement_type":            "نوع الحركة",         # "Movement Type"
"reference":                "المرجع",             # "Reference"
```

---

### 3.4 `ui/tabs/orders/` — متوسط التعقيد

#### الهيكل:
```
orders/
├── customers/ (customer_detail_panel.py, customers_list_panel.py)
├── dashboard/ (_config.py, _recent_table.py, _status_grid.py, _top_cards.py)
├── order_detail/ (5 ملفات)
├── order_form/ (_item_row_widget.py, _products_fetcher.py)
├── orders/ (_filter_toolbar.py, _orders_list_panel.py, _status_delegate.py)
├── _customer_form.py, _item_form.py, _order_detail.py, _order_form.py
├── customers_tab.py, dashboard_tab.py, orders_tab.py
```

#### المشاكل:
- `_orders_list_panel.py` + `orders_tab.py` + `_order_detail.py` — يجب أن يرثوا من `BaseListPanel` / `BaseDetailPanel`.
- `_products_fetcher.py` — يجب أن يستخدم `services/costing/catalog_service.py` مباشرة.
- `_status_delegate.py` — `QStyledItemDelegate` مخصص، هذا صحيح.

#### مفاتيح ترجمة ناقصة لـ orders:
```python
# في ar.py و en.py:
"order_number":             "رقم الطلب",          # "Order Number"
"order_total":              "إجمالي الطلب",       # "Order Total"
"customer_name":            "اسم العميل",         # "Customer Name"
"customer_phone":           "هاتف العميل",        # "Customer Phone"
"customer_address":         "عنوان العميل",       # "Customer Address"
"delivery_date":            "تاريخ التسليم",      # "Delivery Date"
"payment_status":           "حالة الدفع",         # "Payment Status"
"order_items":              "بنود الطلب",         # "Order Items"
"status_pending":           "معلق",               # "Pending"
"status_confirmed":         "مؤكد",               # "Confirmed"
"status_in_production":     "قيد الإنتاج",        # "In Production"
"status_ready":             "جاهز",               # "Ready"
"status_delivered":         "مُسلَّم",             # "Delivered"
"status_cancelled":         "ملغي",               # "Cancelled"
"dashboard":                "لوحة التحكم",        # "Dashboard"
"recent_orders":            "الطلبات الأخيرة",    # "Recent Orders"
"top_customers":            "أفضل العملاء",       # "Top Customers"
```

---

### 3.5 `ui/tabs/design/` — متوسط التعقيد

#### الهيكل:
```
design/
├── designs/ (design_detail_panel, designs_categories, designs_table, size_card)
├── dimension_sets/ (8 ملفات)
├── design_styles.py, designs_tab.py, dimension_sets_tab.py
```

#### المشاكل:
- `design_styles.py` — يحتمل أن يكون styles مكررة مع `widgets/theme/styles.py`. يحتاج دمج أو حذف.
- `designs_categories/_row_and_form.py` — يجب أن يستخدم `CategoryManager` من `widgets/managers/category.py` أو `CategoryService`.

#### مفاتيح ترجمة ناقصة لـ design:
```python
# في ar.py و en.py:
"design_name":              "اسم التصميم",        # "Design Name"
"design_file":              "ملف التصميم",        # "Design File"
"design_size":              "مقاس التصميم",       # "Design Size"
"dimension_set_name":       "اسم مجموعة الأبعاد", # "Dimension Set Name"
"dimension_group":          "مجموعة الأبعاد",     # "Dimension Group"
"dimension_field":          "حقل البعد",          # "Dimension Field"
"dimension_value":          "قيمة البعد",         # "Dimension Value"
"dimension_instance":       "نسخة الأبعاد",       # "Dimension Instance"
"open_in_gimp":             "فتح في GIMP",        # "Open in GIMP"
"thumbnail":                "صورة مصغرة",         # "Thumbnail"
```

---

### 3.6 `ui/tabs/pricing/` — بسيط نسبياً

#### الهيكل:
```
pricing/
├── offers/ (6 ملفات)
├── pricing/ (_pricing_panel.py, _stat_box.py)
└── pricing_tab.py
```

#### المشاكل:
- `_stat_box.py` — إذا كان wrapper لـ `StatCard` يُحذف ويُستبدل بـ `StatCard` مباشرة.
- `offers/offer_item_row.py` — يجب أن يشابه `ComponentRow` في البنية.

#### مفاتيح ترجمة ناقصة لـ pricing:
```python
# في ar.py و en.py:
"offer_name":               "اسم العرض",          # "Offer Name"
"offer_validity":           "صلاحية العرض",       # "Offer Validity"
"offer_items":              "بنود العرض",         # "Offer Items"
"base_cost":                "التكلفة الأساسية",   # "Base Cost"
"markup_pct":               "نسبة الهامش",        # "Markup %"
"final_price":              "السعر النهائي",      # "Final Price"
"product_cost":             "تكلفة المنتج",       # "Product Cost"
"scenario_used":            "السيناريو المستخدم", # "Scenario Used"
```

---

## 4. الإصلاحات المحددة المطلوبة

### 4.1 إصلاح `ui/widgets/shared/list_panel_with_shared.py`

**المشكلة:** `_live_conn` يتجاهل `LiveConnMixin` الموروث.

```python
# الكود الحالي (خطأ):
def _live_conn(self):
    from db.shared.connection import get_connection
    return get_connection()

# الإصلاح — حذف هذا override تماماً، LiveConnMixin يتولى الأمر
# أو إذا احتاج connection مختلف:
# لا شيء — LiveConnMixin._live_conn() يفعل نفس الشيء بشكل أصح
```

### 4.2 إصلاح `ui/tabs/costing/shared/_utils.py`

هذا الملف يُصدّر ثوابت ألوان `SHARED_COLOR, SHARED_BG, PUBLISHED_COLOR, PUBLISHED_BG`.
يجب أن تنتقل هذه الثوابت إلى `ui/widgets/core/colors.py` أو تبقى في `_utils.py` إذا كانت خاصة بـ costing.

**القرار:** تبقى في `_utils.py` لأنها ألوان خاصة بمنطق العناصر المشتركة في costing.

### 4.3 `ui/tabs/accounting/accounting_tabs_builder.py`

إذا كان هذا الملف يبني `QTabWidget` فقط دون منطق، يُدمج في `accounting_section.py`.

### 4.4 حذف `ui/widgets/panels/crud_section.py` كملف مستقل

`CrudSection` أصبحت alias لـ `BaseSection` (من `ui/widgets/base/section.py`).
يجب تحديث جميع imports لتستخدم `BaseSection` مباشرة:

```python
# قبل:
from ui.widgets.panels.crud_section import CrudSection

# بعد:
from ui.widgets.base.section import BaseSection as CrudSection  # للتوافق
# أو مباشرة:
from ui.widgets.base.section import BaseSection
```

### 4.5 توحيد `_conn_guard.py` في accounting

إذا كان `_conn_guard.py` يوفر decorator للتحقق من الاتصال، يُستبدل بـ `@requires_company` من `ui/widgets/core/guard.py`.

---

## 5. خطة التنفيذ المرحلية

### المرحلة 1: الأساس (أولوية عالية)

#### 1-A: إنشاء `ui/widgets/core/__init__.py`
```python
from ui.app_settings import get_font_size
__all__ = ["get_font_size"]
```

#### 1-B: إصلاح `list_panel_with_shared.py`
- حذف override `_live_conn`
- التأكد من صحة الـ inheritance chain

#### 1-C: إنشاء `services/inventory/inventory_service.py`
الـ inventory لا يملك service layer — يحتاج إنشاء:
```python
class InventoryService:
    def __init__(self, conn): ...
    def get_current_stock(self, item_id): ...
    def record_inbound(self, ...): ...
    def record_outbound(self, ...): ...
    def get_movements(self, filters): ...
    def get_report(self, date_from, date_to): ...
```

---

### المرحلة 2: توحيد Tabs (أولوية متوسطة)

#### 2-A: `costing_section.py`
يجب أن يكون orchestrator نظيف:
```python
class CostingSection(TabSectionBase):
    def _build_tabs(self, tabs):
        tabs.addTab(RawTab(self.conn),     tr("nav_costing") + " — " + tr("raw_materials"))
        tabs.addTab(LaborTab(self.conn),   tr("labor_ops"))
        tabs.addTab(MachineTab(self.conn), tr("machine_ops"))
        tabs.addTab(ProductTab(self.conn), tr("new_product"))
```

#### 2-B: تحويل tab classes لترث من `BaseSection`
كل tab مثل `RawTab`, `LaborTab` يجب أن يكون:
```python
class RawTab(BaseSection):
    LIST_MIN_W = 320
    CONNECT_BUS = True

    def _create_list(self):
        return RawTablePanel(self.conn)

    def _create_detail(self):
        return RawInputPanel(self.conn)

    def _connect_signals(self):
        self._list.item_selected.connect(self._detail.load_item)
```

#### 2-C: تحويل list panels لترث من `BaseListPanel`
كل `*_table.py` يجب أن يكون:
```python
class LaborOpTable(BaseListPanel):
    COLUMNS = ["ID", tr("name"), tr("cost_per_hour"), tr("category")]
    STRETCH_COL = 1
    EMPTY_ICON = "👷"
    EMPTY_TITLE = "labor_ops"
    SHOW_CATEGORY = True
    CONNECT_BUS = True

    def _load_rows(self):
        return LaborOpService(self.conn).list_all()

    def _fill_row(self, table, r, row):
        table.setItem(r, 0, make_item("", user_data=row["id"]))
        table.setItem(r, 1, make_item(row["name"]))
        # ...
```

---

### المرحلة 3: مفاتيح الترجمة (أولوية متوسطة)

#### إضافات لـ `ui/i18n/ar.py`:

```python
# === Accounting ===
"investors":                "المستثمرون",
"investor_add":             "إضافة مستثمر",
"investor_movement":        "حركة مستثمر",
"link_to_entry":            "ربط بقيد",
"account_group":            "مجموعة الحسابات",
"account_nature":           "طبيعة الحساب",
"account_tree":             "شجرة الحسابات",
"fiscal_year":              "السنة المالية",
"owners_equity":            "حقوق الملكية",
"audit_log":                "سجل المراجعة",
"debit_nature":             "طبيعة مدينة",
"credit_nature":            "طبيعة دائنة",

# === Inventory ===
"inbound":                  "وارد",
"outbound":                 "صادر",
"inventory_report":         "تقرير المخزون",
"item_name":                "اسم الصنف",
"item_type":                "نوع الصنف",
"min_stock":                "الحد الأدنى للمخزون",
"current_balance":          "الرصيد الحالي",
"movement_date":            "تاريخ الحركة",
"movement_type":            "نوع الحركة",

# === Orders ===
"order_number":             "رقم الطلب",
"order_total":              "إجمالي الطلب",
"customer_name":            "اسم العميل",
"customer_phone":           "هاتف العميل",
"customer_address":         "عنوان العميل",
"delivery_date":            "تاريخ التسليم",
"payment_status":           "حالة الدفع",
"order_items":              "بنود الطلب",
"status_pending":           "معلق",
"status_confirmed":         "مؤكد",
"status_in_production":     "قيد الإنتاج",
"status_ready":             "جاهز",
"status_delivered":         "مُسلَّم",
"status_cancelled":         "ملغي",
"dashboard":                "لوحة التحكم",
"recent_orders":            "الطلبات الأخيرة",
"top_customers":            "أفضل العملاء",

# === Design ===
"design_name":              "اسم التصميم",
"design_file":              "ملف التصميم",
"open_in_gimp":             "فتح في GIMP",
"thumbnail":                "صورة مصغرة",
"dimension_set_name":       "اسم مجموعة الأبعاد",
"dimension_group":          "مجموعة الأبعاد",
"dimension_field":          "حقل البعد",
"dimension_value":          "قيمة البعد",
"dimension_instance":       "نسخة الأبعاد",

# === Pricing ===
"offer_name":               "اسم العرض",
"offer_validity":           "صلاحية العرض",
"offer_items":              "بنود العرض",
"base_cost":                "التكلفة الأساسية",
"markup_pct":               "نسبة الهامش %",
"final_price":              "السعر النهائي",
"product_cost":             "تكلفة المنتج",
"scenario_used":            "السيناريو المستخدم",
```

#### إضافات لـ `ui/i18n/en.py`:
نفس المفاتيح بالإنجليزية (موضحة في الجدول أعلاه).

---

### المرحلة 4: إصلاحات قصيرة المدى (أولوية منخفضة)

#### 4-A: `design_styles.py`
فحص المحتوى — إذا كان يكرر `widgets/theme/styles.py` يُحذف ويُستبدل باستدعاء مباشر.

#### 4-B: `accounting/account_combo.py` + `accounts_combo_widget.py`
فحص التكرار — الأرجح واحد منهما wrapper للآخر.

#### 4-C: Placeholder tabs في `main_window.py`
```python
# الكود الحالي يبني placeholders:
w = _make_placeholder_tab(name)

# يجب استبداله بالـ widgets الفعلية:
from ui.tabs.costing_section    import CostingSection
from ui.tabs.pricing_section    import PricingSection
# إلخ...
```

---

## 6. ملف `ui/widgets/core/__init__.py` — أولوية فورية

هذا الملف ضروري لأن عدة ملفات تستدعيه:

```python
# المستدعيون:
from ..core import get_font_size          # في label.py, headers.py, etc.
from ..core import get_font_size          # في form_parts.py
```

**الملف المطلوب** (بسيط جداً):
```python
"""ui/widgets/core/__init__.py"""
from ui.app_settings import get_font_size

__all__ = ["get_font_size"]
```

---

## 7. `services/inventory/inventory_service.py` — ينقصنا

**لا يوجد service للمخزون رغم وجود repo كامل في `db/inventory/inventory_repo.py`.**

```python
"""services/inventory/inventory_service.py"""
class InventoryService:
    def __init__(self, conn):
        self.conn = conn

    def get_items(self, filters=None) -> list[dict]: ...
    def get_item(self, item_id: int) -> dict | None: ...
    def record_inbound(self, item_id, qty, date, ref, notes) -> int: ...
    def record_outbound(self, item_id, qty, date, ref, notes) -> int: ...
    def get_movements(self, item_id=None, date_from=None, date_to=None) -> list[dict]: ...
    def get_current_stock(self, item_id: int) -> float: ...
    def get_report(self, date_from, date_to) -> list[dict]: ...
```

---

## 8. ترتيب التنفيذ المقترح

```
الأسبوع 1:
  [P1] ui/widgets/core/__init__.py                 ← فوري، يحل imports مكسورة
  [P1] إصلاح list_panel_with_shared._live_conn      ← سطر واحد
  [P1] إضافة مفاتيح الترجمة لـ ar.py + en.py        ← ملفان

الأسبوع 2:
  [P2] services/inventory/inventory_service.py     ← service layer ناقصة
  [P2] inventory tabs تستخدم service مباشرة
  [P2] تحويل inventory list panels → BaseListPanel

الأسبوع 3:
  [P3] costing_section.py كـ orchestrator نظيف
  [P3] RawTab/LaborTab/MachineTab → BaseSection
  [P3] table panels → BaseListPanel

الأسبوع 4:
  [P4] accounting section review
  [P4] orders/design/pricing tabs review
  [P4] main_window.py placeholder → real widgets

الأسبوع 5:
  [P5] design_styles.py مراجعة وحذف التكرارات
  [P5] accounting/account_combo دمج إذا تكرار
  [P5] حذف crud_section.py المستقل (الـ BaseSection يغطيه)
```

---

## 9. قواعد Code Review لكل تعديل

قبل إغلاق أي ملف تعديل، تحقق من:

- [ ] لا توجد نصوص عربية hardcoded — كل نص مرئي للمستخدم يستخدم `tr(key)`
- [ ] لا `from db.companies.company_state import company_state` خارج `conn.py` و `guard.py`
- [ ] لا استدعاء مباشر لـ `company_state.get_erp_conn()` في tabs — يمر عبر `_live_conn()`
- [ ] لا wrapper files — الاستدعاء مباشر للملف الذي يحتوي الكود
- [ ] كل list panel يرث من `BaseListPanel`
- [ ] كل detail panel يرث من `BaseDetailPanel`
- [ ] كل section يرث من `BaseSection`
- [ ] signals تستخدم `bus.company_data_changed` مع `CONNECT_BUS = True`
- [ ] لا `bus.data_changed.emit()` في tabs — يستخدم `emit_company_data_changed()`

---

## 10. ملاحظات ختامية

### ما هو مكتمل بالفعل (لا يحتاج تغيير):
- `widgets/base/` — الـ base classes مكتملة ومحكمة
- `widgets/mixins/` — الـ mixins جاهزة
- `widgets/core/` — colors, conn, events, guard, i18n كلها جاهزة
- `services/costing/` — كاملة
- `services/shared/` — كاملة
- `services/accounting/journal_service.py` — كاملة
- `services/orders/order_service.py` — كاملة
- `ui/i18n/ar.py` + `ui/i18n/en.py` — تحتاج إضافات فقط (المرحلة 3)

### الفجوة الأكبر:
**`services/inventory/`** غائب كلياً — يجب إنشاؤه.

### الخطر الأكبر:
**`main_window.py`** حالياً يبني placeholders فقط (`_make_placeholder_tab`) —
التطبيق لا يعرض أي قسم حقيقي. هذا يعني tabs الفعلية لا تُستدعى أبداً ولا يمكن اختبارها عبر UI.
إصلاح هذا يجب أن يكون **أولوية قصوى** بعد التأكد من أن كل section module يعمل.