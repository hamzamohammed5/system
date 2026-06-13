# خطة إعادة هيكلة نظام إدارة الشركات — منظمة حسب الملف

> **الهدف:** تحويل `tabs/` إلى orchestrators خالصة وفق التسلسل:
> `widgets/ (base) → tabs/UI → services/ → repos/ (db/) ← schema/`
>
> **القاعدة الذهبية:** لا hardcoded — لا ألوان، لا نصوص، لا بناء UI خارج أماكنها.

---

## فهرس سريع

- [المرحلة الأساسية](#المرحلة-الأساسية)
- [تبويبات المخزن](#تبويبات-المخزن)
- [تبويبات التسعير](#تبويبات-التسعير)
- [إدارة الشركات](#إدارة-الشركات)
- [ترتيب التطبيق](#ترتيب-التطبيق)

---

# المرحلة الأساسية

## `ui/theme/theme_manager.py` — إضافة ألوان جديدة

### المشاكل
عدم وجود ألوان مخصصة لـ:
- العناصر المشتركة / المنشورة
- حالات المخزون (منخفض / حرج / كافٍ)

### الحل
إضافة 8 ألوان جديدة إلى `_LIGHT_THEME` و `_DARK_THEME`:

```python
# في _LIGHT_THEME - أضف بعد الألوان الموجودة:
# ── Shared / Published items ──────────────────────────────
"shared_item_fg":      "#6a1b9a",   # نص العنصر المشترك
"shared_item_bg":      "#f3e5f5",   # خلفية صف العنصر المشترك
"published_item_fg":   "#0891b2",   # نص العنصر المنشور محلياً
"published_item_bg":   "#e0f7fa",   # خلفية صف العنصر المنشور

# ── Inventory Stock Levels ────────────────────────────────
"stock_critical_fg":   "#c62828",   # صفر مخزون (نص)
"stock_low_fg":        "#e65100",   # تحت الحد الأدنى (نص)
"stock_ok_fg":         "#2e7d32",   # مخزون كافٍ (نص)

# في _DARK_THEME - نفس المفاتيح:
"shared_item_fg":      "#CE93D8",
"shared_item_bg":      "#1a0828",
"published_item_fg":   "#26C6DA",
"published_item_bg":   "#0a2830",
"stock_critical_fg":   "#E57373",
"stock_low_fg":        "#FFB74D",
"stock_ok_fg":         "#66BB8A",
```

---

## `ui/i18n/ar.py` — إضافة مفاتيح الترجمة العربية

### المشاكل
عدم وجود مفاتيح ترجمة لـ UI المخزن والتسعير والشركات.

### الحل
أضف المفاتيح التالية في المكان المناسب حسب التصنيف:

```python
# ─────────────────────────────────────────────────────────────
# المخزن
# ─────────────────────────────────────────────────────────────
"inventory_purchase_success":  "✅ تم تسجيل الاستلام وإنشاء قيد محاسبي",
"inventory_select_item":        "اختر الصنف أولاً",
"inventory_select_payment":     "اختر حساب الدفع",
"inventory_valid_qty_cost":     "أدخل كمية وسعر صحيحين",
"inventory_adjust_negative":    "كمية التسوية لا يمكن أن تكون سالبة",
"record_outbound_success":      "تم تسجيل الصرف بنجاح",
"inventory_item_name":          "اسم الصنف",
"inventory_new_item":           "صنف جديد",
"inventory_unit_placeholder":   "قطعة / متر / كيلو...",
"inventory_min_qty_label":      "الحد الأدنى",
"inventory_link_raw":           "ربط بخامة",
"inventory_acc_account":        "حساب المخزون",
"inventory_outbound_title":     "📤  صرف / استهلاك مخزن",
"inventory_inbound_title":      "📥  استلام / شراء مخزن",
"inventory_recent_inbound":     "─── آخر حركات الوارد ───",
"inventory_recent_outbound":    "─── آخر حركات الصادر ───",
"inventory_items_header":       "─── أصناف المخزن ───",
"inventory_purpose":            "الغرض من الصرف...",
"inventory_payment_account":    "حساب الدفع",
"inventory_available_qty":      "الرصيد: {qty} {unit}",
"inventory_available_none":     "الرصيد: —",

# ─────────────────────────────────────────────────────────────
# التسعير
# ─────────────────────────────────────────────────────────────
"pricing_product_label":        "المنتج",
"pricing_margin_label":         "هامش الربح",
"pricing_final_price_label":    "السعر النهائي",
"pricing_cost_stat":            "التكلفة",
"pricing_suggested_stat":       "سعر البيع المقترح",
"pricing_manual_stat":          "السعر اليدوي",
"pricing_profit_stat":          "الربح",
"pricing_margin_actual_stat":   "هامش الربح الفعلي %",
"pricing_select_product":       "اختر منتجاً أولاً",
"pricing_price_positive":       "السعر يجب أن يكون أكبر من صفر",
"pricing_delete_confirm":       "حذف سعر «{name}»؟",
"pricing_saved_prices":         "─── قائمة الأسعار ───",
"pricing_new_mode":             "─── تسعير منتج ───",
"pricing_edit_mode":            "─── تعديل سعر: {name} ───",
"offer_new_mode":               "─── عرض جديد ───",
"offer_edit_mode":              "─── تعديل: {name} ───",
"offer_name_label":             "اسم العرض",
"offer_discount_label":         "الخصم",
"offer_category_label":         "التصنيف",
"offer_notes_label":            "ملاحظات",
"offer_add_product_btn":        "➕  إضافة منتج للعرض",
"offer_save_btn":               "💾  حفظ العرض",
"offer_total_before_disc":      "إجمالي السعر قبل الخصم",
"offer_discount_value":         "قيمة الخصم",
"offer_sell_price":             "سعر البيع النهائي",
"offer_total_cost":             "إجمالي التكلفة",
"offer_profit":                 "الربح",
"offer_select_product_search":  "🔍 بحث...",
"offer_col_product":            "المنتج",
"offer_col_category":           "التصنيف",
"offer_col_qty":                "الكمية",
"offer_col_unit_cost":          "تكلفة/وحدة",
"offer_col_unit_price":         "سعر/وحدة",
"offer_col_line_total":         "إجمالي السطر",
"offer_col_line_profit":        "الربح/سطر",
"offer_select_first":           "اختر عرضاً أولاً",
"offer_details_placeholder":    "اختر عرضاً لعرض تفاصيله",
"offer_saved_list":             "─── العروض المحفوظة ───",
"offer_products_tab":           "🎁  العروض",
"offer_categories_tab":         "🏷️  تصنيفات العروض",
"pricing_prices_tab":           "💰  الأسعار",
"pricing_categories_tab":       "🏷️  التصنيفات",

# ─────────────────────────────────────────────────────────────
# الشركات والعناصر المشتركة
# ─────────────────────────────────────────────────────────────
"companies_registered":         "الشركات المسجلة",
"company_add_btn":              "➕  إضافة شركة",
"company_name_label":           "اسم الشركة *",
"company_short_name_label":     "الاسم المختصر",
"company_color_label":          "اللون المميز",
"company_notes_label":          "ملاحظات",
"company_choose_color":         "اختر لوناً",
"company_new_title":            "✨  شركة جديدة",
"company_edit_title":           "✏️  تعديل: {name}",
"company_status_active":        "✅ نشطة",
"company_status_paused":        "⏸ موقوفة",
"company_updated_msg":          "تم تحديث بيانات «{name}»",
"company_created_msg":          "تم إنشاء شركة «{name}» بنجاح.\nتم إنشاء قواعد البيانات الخاصة بها.",
"company_delete_confirm":       "هل تريد حذف شركة «{name}»؟\n\nملاحظة: ملفات قواعد البيانات ستبقى على القرص.",
"shared_item_hint":             "💡  العناصر المشتركة مخزنة مركزياً — أي تعديل على السعر أو البيانات يتعكس فوراً على كل الشركات المشتركة فيها.",
"shared_publish_hint":          "💡  العنصر المشترك يُحفظ مركزياً ويظهر في كل الشركات المختارة.\n    أي تعديل على بياناته سيتعكس فوراً على كل الشركات.",
"shared_item_header":           "🔗  إدارة العناصر المشتركة بين الشركات",
"shared_add_btn":               "➕  إضافة عنصر مشترك",
"shared_edit_btn":              "✏️  تعديل المحدد",
"shared_delete_btn":            "🗑️  حذف المحدد",
"shared_refresh_btn":           "🔄  تحديث",
"shared_close_btn":             "✖  إغلاق",
"shared_link_btn":              "➕  ربط شركة",
"shared_unlink_btn":            "✖  فك الربط",
"shared_save_btn":              "💾  حفظ التغييرات",
"shared_publish_btn":           "📤  نشر العنصر",
"shared_name_required":         "أدخل اسم العنصر",
"shared_updated_msg":           "✅ تم حفظ التغييرات — ستنعكس فوراً على كل الشركات المشتركة.",
"shared_published_msg":         "✅ تم نشر «{name}» كعنصر مشترك وربطه بالشركات المختارة.",
"shared_linked_msg":            "✅ تم ربط الشركات المختارة بالعنصر «{name}»",
"shared_already_linked":        "هذه الشركة مربوطة بالفعل",
"shared_not_linked":            "هذه الشركة غير مربوطة أصلاً",
"shared_unlink_confirm":        "فك ربط هذه الشركة من العنصر المشترك؟",
"shared_delete_with_companies": "هذا العنصر مرتبط بـ {count} شركة. حذفه سيفك الربط تلقائياً. هل تريد المتابعة؟",
"shared_delete_simple":         "حذف هذا العنصر المشترك؟",
"shared_deleted_msg":           "✅ تم حذف العنصر المشترك",
"shared_companies_section":     "الشركات المشتركة في هذا العنصر",
"shared_item_data_section":     "بيانات العنصر",
"shared_companies_share":       "مشاركة مع الشركات",
"shared_select_all_btn":        "✅ الكل",
"shared_select_none_btn":       "☐ لا شيء",
"shared_quick_select":          "تحديد سريع:",
"link_item_title":              "🔗  اختر عنصراً للربط",
"link_item_prompt":             "اختر العنصر المشترك الذي تريد ربطه بشركتك:",
"link_item_btn":                "✅  ربط",
"no_company_welcome":           "مرحباً بك في نظام ERP",
"no_company_subtitle":          "اختر شركة من القائمة أعلاه للبدء\nأو أنشئ شركة جديدة",
"no_company_add_btn":           "➕  إنشاء شركة جديدة",
"company_name_placeholder":     "مثال: شركة النور للطباعة",
"company_short_placeholder":    "مثال: النور",
"raw_price_lbl":                "السعر الكلي (جنيه)",
"raw_total_qty_lbl":            "الكمية الإجمالية",
"machine_rate_hour_lbl":        "معدل التشغيل / ساعة (جنيه)",
"machine_rate_unit_lbl":        "معدل التشغيل / وحدة (جنيه)",
"labor_time_lbl":               "الوقت (دقيقة)",
"raw_unit_preview_lbl":         "سعر الوحدة",
"machine_name_col":             "الماكينة",
"shared_type_raw":              "خامة",
"shared_type_machine":          "ماكينة",
"shared_type_labor_op":         "عملية عمالة",
"shared_type_machine_op":       "عملية تشغيل",
"shared_companies_col":         "الشركات المشتركة",
"shared_last_update_col":       "آخر تحديث",
"shared_main_data_col":         "البيانات الرئيسية",
```

---

## `ui/i18n/en.py` — إضافة مفاتيح الترجمة الإنجليزية

### المشاكل
نفس المشاكل في اللغة الإنجليزية.

### الحل
أضف نفس المفاتيح بالإنجليزية:

```python
# ─────────────────────────────────────────────────────────────
# Inventory
# ─────────────────────────────────────────────────────────────
"inventory_purchase_success":   "✅ Inbound recorded and accounting entry created",
"inventory_select_item":        "Select an item first",
"inventory_select_payment":     "Select a payment account",
"inventory_valid_qty_cost":     "Enter valid quantity and price",
"inventory_adjust_negative":    "Adjustment quantity cannot be negative",
"record_outbound_success":      "Outbound recorded successfully",
"inventory_item_name":          "Item Name",
"inventory_new_item":           "New Item",
"inventory_unit_placeholder":   "piece / meter / kg...",
"inventory_min_qty_label":      "Min Level",
"inventory_link_raw":           "Link to Raw Material",
"inventory_acc_account":        "Inventory Account",
"inventory_outbound_title":     "📤  Issue / Consumption",
"inventory_inbound_title":      "📥  Receive / Purchase",
"inventory_recent_inbound":     "─── Recent Inbound Movements ───",
"inventory_recent_outbound":    "─── Recent Outbound Movements ───",
"inventory_items_header":       "─── Inventory Items ───",
"inventory_purpose":            "Purpose of issue...",
"inventory_payment_account":    "Payment Account",
"inventory_available_qty":      "Balance: {qty} {unit}",
"inventory_available_none":     "Balance: —",

# ─────────────────────────────────────────────────────────────
# Pricing
# ─────────────────────────────────────────────────────────────
"pricing_product_label":        "Product",
"pricing_margin_label":         "Profit Margin",
"pricing_final_price_label":    "Final Price",
"pricing_cost_stat":            "Cost",
"pricing_suggested_stat":       "Suggested Selling Price",
"pricing_manual_stat":          "Manual Price",
"pricing_profit_stat":          "Profit",
"pricing_margin_actual_stat":   "Actual Margin %",
"pricing_select_product":       "Select a product first",
"pricing_price_positive":       "Price must be greater than zero",
"pricing_delete_confirm":       "Delete price for «{name}»?",
"pricing_saved_prices":         "─── Price List ───",
"pricing_new_mode":             "─── Price a Product ───",
"pricing_edit_mode":            "─── Edit Price: {name} ───",
"offer_new_mode":               "─── New Offer ───",
"offer_edit_mode":              "─── Edit: {name} ───",
"offer_name_label":             "Offer Name",
"offer_discount_label":         "Discount",
"offer_category_label":         "Category",
"offer_notes_label":            "Notes",
"offer_add_product_btn":        "➕  Add Product to Offer",
"offer_save_btn":               "💾  Save Offer",
"offer_total_before_disc":      "Total Price Before Discount",
"offer_discount_value":         "Discount Amount",
"offer_sell_price":             "Final Selling Price",
"offer_total_cost":             "Total Cost",
"offer_profit":                 "Profit",
"offer_select_product_search":  "🔍 Search...",
"offer_col_product":            "Product",
"offer_col_category":           "Category",
"offer_col_qty":                "Qty",
"offer_col_unit_cost":          "Cost/Unit",
"offer_col_unit_price":         "Price/Unit",
"offer_col_line_total":         "Line Total",
"offer_col_line_profit":        "Line Profit",
"offer_select_first":           "Select an offer first",
"offer_details_placeholder":    "Select an offer to view details",
"offer_saved_list":             "─── Saved Offers ───",
"offer_products_tab":           "🎁  Offers",
"offer_categories_tab":         "🏷️  Offer Categories",
"pricing_prices_tab":           "💰  Prices",
"pricing_categories_tab":       "🏷️  Categories",

# ─────────────────────────────────────────────────────────────
# Companies
# ─────────────────────────────────────────────────────────────
"companies_registered":         "Registered Companies",
"company_add_btn":              "➕  Add Company",
"company_name_label":           "Company Name *",
"company_short_name_label":     "Short Name",
"company_color_label":          "Brand Color",
"company_notes_label":          "Notes",
"company_choose_color":         "Choose Color",
"company_new_title":            "✨  New Company",
"company_edit_title":           "✏️  Edit: {name}",
"company_status_active":        "✅ Active",
"company_status_paused":        "⏸ Paused",
"company_updated_msg":          "Company «{name}» updated",
"company_created_msg":          "Company «{name}» created successfully.\nDatabases have been initialized.",
"company_delete_confirm":       "Delete company «{name}»?\n\nNote: Database files will remain on disk.",
"shared_item_hint":             "💡  Shared items are stored centrally — any change is reflected across all linked companies.",
"shared_publish_hint":          "💡  Shared item is stored centrally and appears in all selected companies.\n    Any changes will be reflected immediately.",
"shared_item_header":           "🔗  Manage Shared Items Between Companies",
"shared_add_btn":               "➕  Add Shared Item",
"shared_edit_btn":              "✏️  Edit Selected",
"shared_delete_btn":            "🗑️  Delete Selected",
"shared_refresh_btn":           "🔄  Refresh",
"shared_close_btn":             "✖  Close",
"shared_link_btn":              "➕  Link Company",
"shared_unlink_btn":            "✖  Unlink",
"shared_save_btn":              "💾  Save Changes",
"shared_publish_btn":           "📤  Publish Item",
"shared_name_required":         "Enter item name",
"shared_updated_msg":           "✅ Changes saved — reflected immediately across all linked companies.",
"shared_published_msg":         "✅ «{name}» published as shared and linked to selected companies.",
"shared_linked_msg":            "✅ Selected companies linked to «{name}»",
"shared_already_linked":        "This company is already linked",
"shared_not_linked":            "This company is not linked",
"shared_unlink_confirm":        "Unlink this company from the shared item?",
"shared_delete_with_companies": "This item is linked to {count} company(ies). Deleting it will remove all links. Continue?",
"shared_delete_simple":         "Delete this shared item?",
"shared_deleted_msg":           "✅ Shared item deleted",
"shared_companies_section":     "Companies Sharing This Item",
"shared_item_data_section":     "Item Data",
"shared_companies_share":       "Share with Companies",
"shared_select_all_btn":        "✅ All",
"shared_select_none_btn":       "☐ None",
"shared_quick_select":          "Quick Select:",
"link_item_title":              "🔗  Select Item to Link",
"link_item_prompt":             "Select the shared item you want to link to your company:",
"link_item_btn":                "✅  Link",
"no_company_welcome":           "Welcome to the ERP System",
"no_company_subtitle":          "Select a company from the list above to start\nor create a new company",
"no_company_add_btn":           "➕  Create New Company",
"company_name_placeholder":     "e.g. Al-Nour Printing Co.",
"company_short_placeholder":    "e.g. Al-Nour",
"raw_price_lbl":                "Total Price (EGP)",
"raw_total_qty_lbl":            "Total Quantity",
"machine_rate_hour_lbl":        "Rate / Hour (EGP)",
"machine_rate_unit_lbl":        "Rate / Unit (EGP)",
"labor_time_lbl":               "Time (minutes)",
"raw_unit_preview_lbl":         "Unit Price",
"machine_name_col":             "Machine",
"shared_type_raw":              "Raw Material",
"shared_type_machine":          "Machine",
"shared_type_labor_op":         "Labor Operation",
"shared_type_machine_op":       "Machine Operation",
"shared_companies_col":         "Linked Companies",
"shared_last_update_col":       "Last Updated",
"shared_main_data_col":         "Main Data",
```

---

# تبويبات المخزن

## `ui/tabs/inventory/items/_item_form.py`

### المشاكل
- استيراد repos مباشرة: `from db.inventory.inventory_repo import ...`
- استخدام `get_connection()` مباشرة بدل `company_state`
- استخدام `bus.data_changed.emit()` — signal محذوف

### الحل
**الاستيرادات المطلوبة:**
```python
from db.inventory.inventory_repo import (
    fetch_inventory_item, insert_inventory_item, update_inventory_item,
)
from db.accounting.accounting_accounts_repo import fetch_leaf_accounts
from db.shared.items_repo import fetch_items_by_type
from ui.widgets.mixins.form_mixins import EditModeMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.widgets.core.conn import LiveConnMixin
from ui.theme import _C
```

**الفئة:**
```python
class _ItemForm(QWidget, EditModeMixin, LiveConnMixin):
    def __init__(self, inv_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self.acc_conn = acc_conn
        ...
    
    def _add(self):
        # ... جمع البيانات ...
        insert_inventory_item(self.inv_conn, **data)
        self._reset()
        emit_company_data_changed()  # ← بدل bus.data_changed.emit()
```

**النقاط المهمة:**
1. استبدل `bus.data_changed.emit()` بـ `emit_company_data_changed()`
2. استخدم `_C` للألوان من `ui.theme`
3. استخدم `tr()` لكل النصوص
4. الـ repos تُستدعى مباشرة (آمن — لا توجد services للمخزن بعد)

---

## `ui/tabs/inventory/items/_items_table.py`

### المشاكل
- استخدام `bus.data_changed.connect()` — signal محذوف
- hardcoded colors: `QColor("#c62828")`, `QColor("#e65100")`
- استيراد repos مباشرة

### الحل
**الاستيرادات:**
```python
from db.inventory.inventory_repo import (
    fetch_all_inventory, fetch_inventory_item, delete_inventory_item,
)
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.theme import _C
```

**الفئة:**
```python
class _ItemsTable(QWidget, BusConnectedMixin):
    def __init__(self, inv_conn, form, on_select, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._form = form
        self._on_select = on_select
        self._build()
        self._load()
        self._connect_bus(data=True)  # ← اشترك في data_changed
    
    def _on_data_changed(self):  # ← callback تلقائي عند تغيير البيانات
        self._load()
    
    def _load(self):
        rows = fetch_all_inventory(self.inv_conn)
        # ... ملء الجدول ...
        if inv["qty_on_hand"] == 0:
            qty_item.setForeground(QColor(_C["stock_critical_fg"]))  # ← بدل hardcoded
        elif inv["qty_on_hand"] <= inv["qty_min"]:
            qty_item.setForeground(QColor(_C["stock_low_fg"]))  # ← من theme
```

**النقاط المهمة:**
1. وسّع الفئة من `BusConnectedMixin`
2. استدعِ `self._connect_bus(data=True)` في `__init__`
3. عرّف `_on_data_changed()` لتحديث البيانات تلقائياً
4. استبدل الألوان بـ `_C["..."]`
5. في `closeEvent`، استدعِ `self._disconnect_bus()`

---

## `ui/tabs/inventory/inventory_inbound_tab.py`

### المشاكل
- استيراد repos مباشرة
- استخدام `bus.data_changed.connect()` — محذوف
- استخدام `get_accounting_connection()` و `get_inventory_connection()` بدل `company_state`
- hardcoded colors

### الحل
**الاستيرادات:**
```python
from db.inventory.inventory_repo import (
    fetch_all_inventory, fetch_inventory_item,
)
from db.accounting.accounting_accounts_repo import fetch_leaf_accounts
from db.accounting.accounting_inventory_repo import purchase_inventory
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.theme import _C
```

**الفئة:**
```python
class _InboundTab(QWidget, BusConnectedMixin):
    def __init__(self, inv_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self.acc_conn = acc_conn
        self._build()
        self._connect_bus(data=True)
    
    def _on_data_changed(self):
        self._reload_items()
        self._load_moves()
    
    def _save(self):
        # ... التحقق ...
        purchase_inventory(
            self.inv_conn, self.acc_conn,
            inv_id, qty, unit_cost, date, pay_acc, notes
        )
        self.inp_notes.clear()
        emit_company_data_changed()  # ← بدل bus.data_changed.emit()
```

---

## `ui/tabs/inventory/inventory_outbound_tab.py`

### المشاكل
- نفس مشاكل `inventory_inbound_tab.py`

### الحل
نفس الإجراء:
```python
class _OutboundTab(QWidget, BusConnectedMixin):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._build()
        self._connect_bus(data=True)
    
    def _on_data_changed(self):
        self._reload_items()
        self._load_moves()
    
    def _save(self):
        # ...
        record_inventory_move(self.inv_conn, inv_id, "out", qty, 0, date, notes)
        emit_company_data_changed()
```

---

## `ui/tabs/inventory/inventory_report_tab.py`

### المشاكل
- استخدام `bus.data_changed.connect()` — محذوف
- hardcoded colors عديدة
- استيراد repos مباشرة

### الحل
**الفئة الرئيسية:**
```python
class _ReportTab(QWidget, BusConnectedMixin):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._build()
        self._load()
        self._connect_bus(data=True)
    
    def _on_data_changed(self):
        self._load()
```

**الألوان:**
```python
def _card(label_key, color_key):
    color = _C[color_key]  # ← بدل hardcoded
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {_C['bg_surface']};
            border-left: 4px solid {color};
            border-radius: 6px;
        }}
    """)
```

---

## `ui/tabs/inventory_section.py`

### المشاكل
- استخدام `get_accounting_connection()` و `get_inventory_connection()` مباشرة

### الحل
**استبدل:**
```python
from db.companies.company_state import company_state

class InventoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ...
        
    def _build(self):
        # ...
        inv_conn = company_state.get_inventory_conn()  # ← بدل get_inventory_connection()
        acc_conn = company_state.get_accounting_conn()  # ← بدل get_accounting_connection()
        
        tabs.addTab(_ItemsTab(inv_conn, acc_conn, ...), ...)
```

---

# تبويبات التسعير

## `ui/tabs/pricing/pricing/_stat_box.py`

### المشاكل
- hardcoded colors في StyleSheet
- نصوص مضمنة

### الحل
**الدالة الجديدة:**
```python
from ui.theme import _C
from ui.widgets.core.i18n import tr

def stat_box(label: str, color: str = None) -> tuple:
    """يرجع (QFrame, QLabel_value) — بطاقة إحصائية."""
    if color is None:
        color = _C["accent"]
    
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {_C['bg_surface']};
            border: 1px solid {_C['border']};
            border-radius: 6px;
            padding: 4px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lay.setSpacing(2)
    
    lbl_title = QLabel(label)  # label آت من الخارج (من tr())
    lbl_title.setStyleSheet(
        f"font-size:10px; color:{_C['text_muted']};"
        "background:transparent; border:none;"
    )
    
    lbl_val = QLabel("─")
    lbl_val.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    
    lay.addWidget(lbl_title)
    lay.addWidget(lbl_val)
    return frame, lbl_val
```

---

## `ui/tabs/pricing/pricing/_pricing_panel.py`

### المشاكل
- استيراد repos مباشرة
- `bus.data_changed.connect()` — محذوف
- hardcoded colors عديدة: `#e65100`, `#1565c0`, `#2e7d32`

### الحل
**الاستيرادات:**
```python
from db.shared.items_repo import fetch_items_by_type, fetch_item
from db.pricing.pricing_repo import fetch_all_pricing, upsert_pricing, delete_pricing
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.theme import _C
```

**الفئة:**
```python
class _PricingPanel(QWidget, BusConnectedMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load_products_combo()
        self._load()
        self._connect_bus(data=True)
    
    def _on_data_changed(self):
        self._load_products_combo()
        self._load()
    
    def _save(self):
        # ...
        upsert_pricing(self.conn, prod_id, self.sp_margin.value(), price)
        self._reset_form()
        emit_company_data_changed()  # ← بدل bus.data_changed.emit()
```

**الألوان:**
```python
self.lbl_mode.setStyleSheet(f"font-weight:bold; color:{_C['orange']};")  # ← بدل hardcoded
```

---

## `ui/tabs/pricing/pricing_tab.py`

### المشاكل
- استخدام `get_connection()` مباشرة

### الحل
```python
from db.companies.company_state import company_state

class PricingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = company_state.get_erp_conn()  # ← بدل get_connection()
        self._build()
```

---

## `ui/tabs/pricing/offers/offer_item_row.py`

### المشاكل
- `bus.data_changed.connect()` — محذوف
- hardcoded colors
- استيراد repos

### الحل
**الفئة:**
```python
from ui.widgets.mixins.bus import BusConnectedMixin

class _OfferItemRow(QFrame, BusConnectedMixin):
    def __init__(self, conn, on_remove, on_change, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._on_remove = on_remove
        self._on_change = on_change
        self._build()
        self._load_products()
        self._connect_bus(data=True)
    
    def _on_data_changed(self):
        self._reload_products()
    
    def closeEvent(self, event):
        self._disconnect_bus()
        super().closeEvent(event)
```

---

## `ui/tabs/pricing/offers/offer_form.py`

### المشاكل
- `bus.data_changed.emit()` — محذوف
- hardcoded colors وnصوص عربية مباشرة
- استيراد repos

### الحل
**الاستيرادات:**
```python
from db.pricing.offers_repo import (
    fetch_offer, fetch_offer_items,
    insert_offer, update_offer, replace_offer_items,
)
from ui.widgets.core.events import emit_company_data_changed
from ui.theme import _C
```

**الفئة:**
```python
class _OfferForm(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn = conn
        ...
    
    def _save(self):
        name = self.inp_name.text().strip()
        # ... جمع البيانات ...
        if self._editing_id is not None:
            update_offer(conn, self._editing_id, name, discount, notes, category_id)
            replace_offer_items(conn, self._editing_id, items)
        else:
            oid = insert_offer(conn, name, discount, notes, category_id)
            replace_offer_items(conn, oid, items)
        
        self.reset()
        emit_company_data_changed()  # ← بدل bus.data_changed.emit()
```

---

## `ui/tabs/pricing/offers/offer_details.py`

### المشاكل
- hardcoded colors

### الحل
```python
from ui.theme import _C

class _OfferDetails(QFrame):
    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['orange_border']};
                border-radius: 8px;
            }}
        """)
        # ...
        cost_item.setForeground(QColor(_C["accent"]))  # ← بدل hardcoded
```

---

## `ui/tabs/pricing/offers/offers_table.py`

### المشاكل
- `bus.data_changed.connect()` — محذوف
- hardcoded colors
- استيراد repos

### الحل
**الفئة:**
```python
from ui.widgets.mixins.bus import BusConnectedMixin

class _OffersTable(QWidget, BusConnectedMixin):
    def __init__(self, conn, on_edit, on_delete, on_select, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._all_rows = []
        self._build()
        self._load()
        self._connect_bus(data=True)
    
    def _on_data_changed(self):
        self._load()
    
    def closeEvent(self, event):
        self._disconnect_bus()
        super().closeEvent(event)
```

---

## `ui/tabs/pricing/offers/offers_tab.py`

### المشاكل
- `bus.data_changed.emit()` — محذوف
- hardcoded colors في StyleSheets
- نصوص عربية مضمنة

### الحل
**الفئة:**
```python
from ui.widgets.core.events import emit_company_data_changed
from ui.theme import _C

class OffersTab(QWidget):
    def _build(self):
        # ...
        tabs.setStyleSheet(f"""
            QTabBar::tab:selected {{
                color: {_C['orange']};
                border-top: 2px solid {_C['orange']};
            }}
        """)
    
    def _delete_offer(self, offer_id):
        if confirm_delete(self, offer["name"]):
            delete_offer(conn, offer_id)
            self._details.clear()
            emit_company_data_changed()  # ← بدل bus.data_changed.emit()
```

---

# إدارة الشركات

## `ui/tabs/companies/no_company_screen.py`

### المشاكل
- نصوص عربية مضمنة
- hardcoded colors

### الحل
```python
from ui.widgets.core.i18n import tr
from ui.theme import _C

class NoCompanyScreen(QWidget):
    def _build(self):
        # ...
        title = QLabel(tr("no_company_welcome"))  # ← بدل "مرحباً بك"
        title.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; color: {_C['text_primary']};"
        )
        
        sub = QLabel(tr("no_company_subtitle"))  # ← بدل نص مضمن
        sub.setStyleSheet(f"font-size: 12pt; color: {_C['text_muted']};")
        
        btn = QPushButton(tr("no_company_add_btn"))  # ← بدل "إنشاء شركة"
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']};
                color: {_C['bg_input']};
            }}
        """)
```

---

## `ui/tabs/companies/companies_dialog.py`

### المشاكل
- hardcoded colors كثيرة: `"#2e7d52"`, `"#1b5e38"`, `"#e3f2fd"`, `"#fff8e1"` ... إلخ
- نصوص عربية مضمنة: `"✨  شركة جديدة"`, `"تم تحديث بيانات"` ... إلخ

### الحل
**استبدال منهجي:**

1. **في الأعلى، أضف:**
```python
from ui.widgets.core.i18n import tr
from ui.theme import _C
```

2. **استبدل كل الألوان:**
   - `"#2e7d52"` → `_C["success"]`
   - `"#1b5e38"` → `_C["success"]` (أداكن من الأول، لكن نفس الدلالة)
   - `"#e3f2fd"` → `_C["accent_light"]`
   - `"#bbdefb"` → `_C["accent_mid"]`
   - `"#fff8e1"` → `_C["warning_bg"]`
   - `"#ffecb3"` → `_C["warning_border"]`
   - `"#fdecea"` → `_C["danger_bg"]`
   - `"#ffcdd2"` → `_C["danger_border"]`
   - `"white"` → `_C["bg_surface"]`
   - `"#e0e0e0"` → `_C["border"]`
   - `"#888"` → `_C["text_muted"]`

3. **استبدل النصوص:**
   - `"✨  شركة جديدة"` → `tr("company_new_title")`
   - `"✏️  تعديل: {name}"` → `tr("company_edit_title").format(name=name)`
   - `"✅ نشطة"` / `"⏸ موقوفة"` → `tr("company_status_active")` / `tr("company_status_paused")`
   - `"تم تحديث بيانات «{name}»"` → `tr("company_updated_msg").format(name=name)`
   - `"تم إنشاء شركة«{name}» بنجاح..."` → `tr("company_created_msg").format(name=name)`
   - `"هل تريد حذف شركة «{name}»؟"` → `tr("company_delete_confirm").format(name=name)`

**مثال من الكود:**
```python
def _build_form_panel(self):
    grp = QGroupBox(tr("companies"))
    grp.setStyleSheet(f"""
        QGroupBox {{ color:{_C['success']}; 
                   border:1px solid {_C['border']};
                   border-radius:8px; }}
    """)
    # ...
    self._form_title = QLabel(tr("company_new_title"))  # ← بدل "✨  شركة جديدة"

def _save(self):
    # ...
    msg_info(self, tr("done"), tr("company_updated_msg").format(name=name))
    # ← بدل: msg_info(self, "تم", f"تم تحديث بيانات «{name}»")
```

---

## `ui/tabs/companies/shared_items_dialog.py`

### المشاكل
- hardcoded colors: `"#1565c0"`, `"#e3f2fd"`, `"#e8f5e9"`, `"#2e7d32"`, `"#fdecea"`, `"#c62828"`
- نصوص عربية مضمنة

### الحل
```python
from ui.widgets.core.i18n import tr
from ui.theme import _C

# الاستبدالات:
# "#1565c0" → _C["accent"]
# "#e3f2fd" → _C["accent_light"]
# "#90caf9" → _C["accent_mid"]
# "#e8f5e9" → _C["success_bg"]
# "#2e7d32" → _C["success"]
# "#a5d6a7" → _C["success_border"]
# "#fdecea" → _C["danger_bg"]
# "#c62828" → _C["danger"]
# "#ef9a9a" → _C["danger_border"]
# "#e0e0e0" → _C["border"]
# "#333" → _C["text_primary"]
# "#888" → _C["text_muted"]

# النصوص:
# "أدخل اسم العنصر" → tr("shared_name_required")
# "✅ تم حفظ التغييرات — ستنعكس..." → tr("shared_updated_msg")
# عنوان النافذة: tr("shared_item_header")
```

---

## `ui/tabs/companies/shared_items_manager.py`

### المشاكل
- نفس مشاكل `shared_items_dialog.py`
- hardcoded colors ونصوص عربية

### الحل
```python
from ui.widgets.core.i18n import tr
from ui.theme import _C

# الاستبدالات المنهجية نفسها
self.btn_add.setText(tr("shared_add_btn"))
self.btn_edit.setText(tr("shared_edit_btn"))
self.btn_delete.setText(tr("shared_delete_btn"))
```

---

## `ui/tabs/companies/shared_items_manager_helper/_add_shared_item_dialog.py`

### المشاكل
- hardcoded colors: `"#e3f2fd"`, `"#90caf9"`, `"#1565c0"`, `"white"`, `"#e0e0e0"`
- نصوص عربية مضمنة

### الحل
```python
from ui.widgets.core.i18n import tr
from ui.theme import _C

# الاستبدالات:
# "#e3f2fd" → _C["accent_light"]
# "#90caf9" → _C["accent_mid"]
# "#1565c0" → _C["accent"]
# "white" → _C["bg_surface"]
# "#e0e0e0" → _C["border"]

# النصوص:
# "💡  العنصر المشترك يُحفظ مركزياً..." → tr("shared_publish_hint")
# "بيانات العنصر المشترك" → tr("shared_item_data_section")
# "مشاركة مع الشركات" → tr("shared_companies_share")
# "تحديد سريع:" → tr("shared_quick_select")
# "✅ الكل" → tr("shared_select_all_btn")
# "☐ لا شيء" → tr("shared_select_none_btn")
# "📤  نشر العنصر" → tr("shared_publish_btn")
```

---

## `ui/tabs/companies/_link_item_picker.py`

### المشاكل
- hardcoded colors
- نصوص عربية مضمنة

### الحل
```python
from ui.widgets.core.i18n import tr

# النصوص:
self.setWindowTitle(tr("link_item_title"))  # ← بدل "🔗  اختر عنصراً للربط"
lay.addWidget(QLabel(tr("link_item_prompt")))  # ← بدل "اختر العنصر المشترك..."
ok_btn.setText(tr("link_item_btn"))  # ← بدل "✅  ربط"

# النوع:
_TYPE_AR = {
    "raw":        tr("shared_type_raw"),
    "machine":    tr("shared_type_machine"),
    "labor_op":   tr("shared_type_labor_op"),
    "machine_op": tr("shared_type_machine_op"),
}
```

---

## `ui/tabs/pricing_section.py`

### المشاكل
- hardcoded colors في `_TAB_STYLE`
- نصوص مضمنة

### الحل
```python
from ui.widgets.core.i18n import tr
from ui.theme import _C

class PricingSection(QWidget):
    def _build(self):
        self._header = QLabel(f"  💰  {tr('pricing')}")  # ← بدل hardcoded
        self._header.setFixedHeight(42)
        self._apply_theme()
        
        tabs.setStyleSheet(tab_style(accent=_C["orange"]))  # ← بدل _TAB_STYLE
```

---

# ترتيب التطبيق

## المرحلة 1 — الأساس (لا يكسر أي شيء)

1. ✅ `ui/theme/theme_manager.py` — أضف 8 ألوان جديدة
2. ✅ `ui/i18n/ar.py` — أضف ~100 مفتاح
3. ✅ `ui/i18n/en.py` — أضف ~100 مفتاح
4. ✅ `ui/tabs/pricing/pricing/_stat_box.py` — استبدل الألوان والنصوص

## المرحلة 2 — الـ widgets الصغيرة

5. ✅ `ui/tabs/companies/no_company_screen.py`
6. ✅ `ui/tabs/companies/_link_item_picker.py`
7. ✅ `ui/tabs/pricing/offers/offer_details.py`
8. ✅ `ui/tabs/pricing/offers/offer_item_row.py`

## المرحلة 3 — تبويبات المخزن

9. ✅ `ui/tabs/inventory/items/_item_form.py`
10. ✅ `ui/tabs/inventory/items/_items_table.py`
11. ✅ `ui/tabs/inventory/inventory_outbound_tab.py`
12. ✅ `ui/tabs/inventory/inventory_inbound_tab.py`
13. ✅ `ui/tabs/inventory/inventory_report_tab.py`
14. ✅ `ui/tabs/inventory_section.py`

## المرحلة 4 — تبويبات التسعير

15. ✅ `ui/tabs/pricing/pricing_tab.py`
16. ✅ `ui/tabs/pricing/pricing/_pricing_panel.py`
17. ✅ `ui/tabs/pricing/offers/offers_table.py`
18. ✅ `ui/tabs/pricing/offers/offer_form.py`
19. ✅ `ui/tabs/pricing/offers/offers_tab.py`
20. ✅ `ui/tabs/pricing_section.py`

## المرحلة 5 — إدارة الشركات

21. ✅ `ui/tabs/companies/companies_dialog.py`
22. ✅ `ui/tabs/companies/shared_items_dialog.py`
23. ✅ `ui/tabs/companies/shared_items_manager.py`
24. ✅ `ui/tabs/companies/shared_items_manager_helper/_add_shared_item_dialog.py`

## المرحلة 6 — التحقق

- [ ] اشغّل التطبيق وتأكد من عدم وجود `AttributeError` على `bus.data_changed`
- [ ] تأكد من عمل الـ theme switching (light/dark)
- [ ] تأكد من عمل الـ language switching (AR/EN)
- [ ] تحقق من أن كل الألوان تنعكس بشكل صحيح
- [ ] اختبر إضافة/تعديل/حذف في جميع التبويبات

---

# ملخص التغييرات

| الفئة | عدد الملفات | الملفات | 
|-------|-----------|--------|
| **Theme & i18n** | 3 | theme_manager.py, ar.py, en.py |
| **Inventory Tabs** | 6 | _item_form.py, _items_table.py, inventory_inbound_tab.py, inventory_outbound_tab.py, inventory_report_tab.py, inventory_section.py |
| **Pricing Tabs** | 7 | _stat_box.py, _pricing_panel.py, pricing_tab.py, offer_item_row.py, offer_form.py, offer_details.py, offers_table.py, offers_tab.py, pricing_section.py |
| **Companies** | 4 | no_company_screen.py, companies_dialog.py, shared_items_dialog.py, shared_items_manager.py, _add_shared_item_dialog.py, _link_item_picker.py |
| **المجموع** | **20 ملف** | — |

---

## قاعدة الفحص السريع

ابحث عن:
- ❌ `bus.data_changed` → استبدل بـ `BusConnectedMixin` + `emit_company_data_changed()`
- ❌ `"#` (ألوان hex مباشرة) → استبدل بـ `_C["..."]`
- ❌ `"white"`, `"#e0e0e0"`, `"#888"` → استبدل بـ `_C["bg_surface"]`, `_C["border"]`, `_C["text_muted"]`
- ❌ نصوص عربية/إنجليزية مباشرة → استبدل بـ `tr("key")`
- ❌ `get_connection()`, `get_accounting_connection()`, `get_inventory_connection()` → استبدل بـ `company_state.get_*_conn()`
- ❌ استيراد repos مباشرة في tabs → آمن حالياً (بدون services للمخزن/التسعير)

> **اختبار بعد كل مرحلة:** اشغّل التطبيق وافتح التبويب الذي عدّلته.