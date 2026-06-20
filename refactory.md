# خطة التحسين الشاملة لوحدة الطلبات (Orders)

---

## أولاً: مفاتيح الترجمة الجديدة

> **مؤكد غير موجودة** بعد مراجعة `ar.py` و`en.py` كاملاً.
> كل مفتاح يُضاف في الملفين معاً.

### في `ui/i18n/ar.py` — أضف داخل `AR_STRINGS` تحت قسم `# طلبات`

```python
"order_internal_notes":    "ملاحظات داخلية",
"order_new_btn":           "＋  طلب جديد",
"customer_new_btn":        "＋  عميل جديد",
"order_reorder_btn":       "📋  إعادة طلب",
"order_change_status_btn": "🔄  تغيير الحالة",
"order_cancel_btn_action": "❌  إلغاء الطلب",
"order_edit_btn":          "✏️  تعديل",
"order_delete_btn":        "🗑️  حذف",
"order_add_item_btn":      "＋  إضافة بند",
"order_edit_item_btn":     "✏️  تعديل البند",
"order_del_item_btn":      "🗑️  حذف البند",
"order_import_offer_btn":  "📥  استيراد",
"order_select_offer_lbl":  "أو استورد عرضاً:",
"order_subtotal_lbl":      "الإجمالي قبل الخصم:",
"order_items_count_lbl":   "البنود:",
"order_no_items_warn":     "أضف بنداً واحداً على الأقل",
"order_no_customer_warn":  "اختر عميلاً أولاً",
"order_save_btn":          "💾  حفظ الطلب",
"order_new_title":         "📋  طلب جديد",
"order_edit_title":        "✏️  تعديل الطلب",
"order_customer_section":  "👤  بيانات العميل",
"order_details_section":   "📋  تفاصيل الطلب",
"order_items_section":     "📦  بنود الطلب",
"order_notes_section":     "📝  الملاحظات",
"order_customer_notes":    "ملاحظات للعميل:",
"order_internal_notes_lbl":"ملاحظات داخلية:",
"order_customer_search":   "ابحث عن عميل بالاسم أو الهاتف أو الكود...",
"order_item_search":       "🔍 بحث...",
"order_select_product":    "— اختر منتجاً —",
"order_select_offer":      "— اختر عرضاً —",
"order_unit_label":        "الوحدة",
"order_unit_default":      "قطعة",
"order_discount_total":    "الخصم الكلي",
"order_paid_amount":       "المدفوع",
"order_priority_label":    "الأولوية",
"order_type_label":        "نوع الطلب",
"order_due_date_label":    "تاريخ التسليم",
"order_status_label":      "الحالة",
"order_search_placeholder":"🔍  بحث برقم الطلب أو اسم العميل...",
"order_all_statuses":      "كل الحالات",
"order_all_priorities":    "كل الأولويات",
"order_reset_filter":      "↺  مسح",
"order_refresh_btn":       "↺  تحديث",
"order_delete_confirm":    "حذف الطلب {number} نهائياً؟\nلا يمكن التراجع عن هذا الإجراء.",
"order_delete_failed":     "لا يمكن حذف الطلب إلا في حالة الانتظار أو الإلغاء.",
"order_reorder_confirm":   "إنشاء طلب جديد بناءً على {number}؟",
"order_cancel_reason":     "سبب إلغاء الطلب {number}:",
"order_cancel_title":      "إلغاء الطلب",
"item_unit_price":         "سعر الوحدة:",
"item_discount_lbl":       "خصم:",
"item_qty_lbl":            "الكمية:",
"item_total_lbl":          "الإجمالي :",
"item_notes_lbl":          "ملاحظات:",
"item_design_ref_lbl":     "مرجع التصميم :",
"item_name_lbl":           "البند *",
"item_desc_lbl":           "الوصف :",
"item_save_btn":           "💾  حفظ البند",
"item_add_title":          "➕  إضافة بند",
"item_edit_title":         "✏️  تعديل بند",
"item_name_warn":          "أدخل اسم البند",
"contact_name_lbl":        "الاسم * :",
"contact_role_lbl":        "الصفة :",
"contact_phone_lbl":       "الهاتف :",
"contact_email_lbl":       "الإيميل :",
"contact_notes_lbl":       "ملاحظات :",
"contact_add_btn":         "➕  إضافة جهة اتصال",
"contact_del_btn":         "🗑️  حذف",
"contact_ok_btn":          "✅  إضافة",
"contact_title":           "جهة اتصال",
"contact_name_warn":       "أدخل اسم جهة الاتصال",
"customer_basic_section":  "البيانات الأساسية",
"customer_contacts_section":"جهات الاتصال الإضافية",
"customer_type_individual":"فرد",
"customer_type_company":   "شركة",
"customer_name_lbl":       "الاسم * :",
"customer_type_lbl":       "النوع :",
"customer_phone_lbl":      "الهاتف :",
"customer_phone2_lbl":     "هاتف 2 :",
"customer_email_lbl":      "الإيميل :",
"customer_city_lbl":       "المدينة :",
"customer_address_lbl":    "العنوان :",
"customer_notes_lbl":      "ملاحظات :",
"customer_save_btn":       "💾  حفظ",
"customer_new_title":      "👤  عميل جديد",
"customer_edit_title":     "✏️  تعديل بيانات العميل",
"customer_name_warn":      "أدخل اسم العميل",
"customer_delete_confirm": "حذف العميل «{name}» نهائياً؟\nلا يمكن حذف عميل له طلبات مسجلة.",
"customer_delete_failed":  "لا يمكن حذف هذا العميل لوجود طلبات مرتبطة به.\nيمكنك تعطيله بدلاً من الحذف.",
"customer_toggle_active":  "✅  تفعيل",
"customer_toggle_inactive":"⏸  تعطيل",
"status_change_title":     "تغيير حالة الطلب",
"status_current_lbl":      "الحالة الحالية:",
"status_new_lbl":          "الحالة الجديدة:",
"status_note_lbl":         "ملاحظات (اختياري):",
"status_note_placeholder": "سبب التغيير...",
"status_change_btn":       "✅  تغيير الحالة",
"dashboard_recent_orders": "آخر الطلبات",
"dashboard_status_dist":   "توزيع الطلبات حسب الحالة",
"order_type_new":          "🆕 جديد",
"order_type_reorder":      "🔄 إعادة طلب",
"order_type_custom":       "⚙️ مخصص",
"priority_low":            "⬇ منخفض",
"priority_normal":         "➡ عادي",
"priority_high":           "⬆ عالي",
"priority_urgent":         "🔴 عاجل",
"status_on_hold":          "⏸ معلق",
"status_in_progress":      "🔧 تنفيذ",
"status_ready":            "📦 جاهز",
"order_total_value":       "إجمالي القيمة",
"order_total_paid":        "إجمالي المدفوع",
"order_urgent_count":      "عاجل",
"order_total_count":       "إجمالي الطلبات",
"order_no_items_title":    "لا توجد بنود في هذا الطلب",
"order_no_items_hint":     "اضغط «＋ إضافة بند» لإضافة منتج",
"order_select_first":      "اختر طلباً من القائمة",
"order_select_subtitle":   "أو أنشئ طلباً جديداً بالضغط على ＋ طلب جديد",
"customer_select_first":   "اختر عميلاً من القائمة",
"customer_select_subtitle":"أو أضف عميلاً جديداً بالضغط على ＋",
"log_section_title":       "سجل تغييرات الحالة",
"log_col_from":            "من",
"log_col_to":              "إلى",
"log_col_notes":           "الملاحظات",
"log_col_time":            "الوقت",
"items_col_name":          "البند",
"items_col_desc":          "الوصف",
"items_col_qty":           "الكمية",
"items_col_unit":          "الوحدة",
"items_col_price":         "السعر",
"items_col_discount":      "الخصم%",
"items_col_total":         "الإجمالي",
"customer_col_code":       "الكود",
"customer_col_name":       "الاسم",
"customer_col_phone":      "الهاتف",
"customer_col_city":       "المدينة",
"customer_col_orders":     "الطلبات",
"order_col_number":        "رقم الطلب",
"order_col_customer":      "العميل",
"order_col_status":        "الحالة",
"order_col_priority":      "⚑",
"order_col_date":          "التاريخ",
"customer_total_orders":   "إجمالي الطلبات",
"customer_active_orders":  "طلبات جارية",
"customer_total_value":    "إجمالي القيمة",
"customer_balance":        "المتبقي",
"customer_contacts_title": "📞  جهات الاتصال",
"customer_orders_title":   "📋  آخر الطلبات",
"customer_no_contacts":    "لا توجد جهات اتصال",
"offer_select_label":      "— اختر عرضاً —",
"order_header_total":      "الإجمالي",
"order_header_paid":       "المدفوع",
"order_header_balance":    "المتبقي",
"order_header_due":        "التسليم",
```

### في `ui/i18n/en.py` — أضف داخل `EN_STRINGS` تحت قسم `# Orders`

```python
"order_internal_notes":    "Internal Notes",
"order_new_btn":           "＋  New Order",
"customer_new_btn":        "＋  New Customer",
"order_reorder_btn":       "📋  Re-order",
"order_change_status_btn": "🔄  Change Status",
"order_cancel_btn_action": "❌  Cancel Order",
"order_edit_btn":          "✏️  Edit",
"order_delete_btn":        "🗑️  Delete",
"order_add_item_btn":      "＋  Add Item",
"order_edit_item_btn":     "✏️  Edit Item",
"order_del_item_btn":      "🗑️  Delete Item",
"order_import_offer_btn":  "📥  Import",
"order_select_offer_lbl":  "Or import an offer:",
"order_subtotal_lbl":      "Subtotal (before discount):",
"order_items_count_lbl":   "Items:",
"order_no_items_warn":     "Add at least one item",
"order_no_customer_warn":  "Select a customer first",
"order_save_btn":          "💾  Save Order",
"order_new_title":         "📋  New Order",
"order_edit_title":        "✏️  Edit Order",
"order_customer_section":  "👤  Customer Info",
"order_details_section":   "📋  Order Details",
"order_items_section":     "📦  Order Items",
"order_notes_section":     "📝  Notes",
"order_customer_notes":    "Customer Notes:",
"order_internal_notes_lbl":"Internal Notes:",
"order_customer_search":   "Search customer by name, phone or code...",
"order_item_search":       "🔍 Search...",
"order_select_product":    "— Select Product —",
"order_select_offer":      "— Select Offer —",
"order_unit_label":        "Unit",
"order_unit_default":      "piece",
"order_discount_total":    "Total Discount",
"order_paid_amount":       "Paid",
"order_priority_label":    "Priority",
"order_type_label":        "Order Type",
"order_due_date_label":    "Delivery Date",
"order_status_label":      "Status",
"order_search_placeholder":"🔍  Search by order number or customer...",
"order_all_statuses":      "All Statuses",
"order_all_priorities":    "All Priorities",
"order_reset_filter":      "↺  Clear",
"order_refresh_btn":       "↺  Refresh",
"order_delete_confirm":    "Permanently delete order {number}?\nThis action cannot be undone.",
"order_delete_failed":     "Order can only be deleted in pending or cancelled status.",
"order_reorder_confirm":   "Create a new order based on {number}?",
"order_cancel_reason":     "Reason for cancelling order {number}:",
"order_cancel_title":      "Cancel Order",
"item_unit_price":         "Unit Price:",
"item_discount_lbl":       "Discount:",
"item_qty_lbl":            "Qty:",
"item_total_lbl":          "Total:",
"item_notes_lbl":          "Notes:",
"item_design_ref_lbl":     "Design Ref:",
"item_name_lbl":           "Item *",
"item_desc_lbl":           "Description:",
"item_save_btn":           "💾  Save Item",
"item_add_title":          "➕  Add Item",
"item_edit_title":         "✏️  Edit Item",
"item_name_warn":          "Enter item name",
"contact_name_lbl":        "Name * :",
"contact_role_lbl":        "Role :",
"contact_phone_lbl":       "Phone :",
"contact_email_lbl":       "Email :",
"contact_notes_lbl":       "Notes :",
"contact_add_btn":         "➕  Add Contact",
"contact_del_btn":         "🗑️  Delete",
"contact_ok_btn":          "✅  Add",
"contact_title":           "Contact",
"contact_name_warn":       "Enter contact name",
"customer_basic_section":  "Basic Info",
"customer_contacts_section":"Additional Contacts",
"customer_type_individual":"Individual",
"customer_type_company":   "Company",
"customer_name_lbl":       "Name * :",
"customer_type_lbl":       "Type :",
"customer_phone_lbl":      "Phone :",
"customer_phone2_lbl":     "Phone 2 :",
"customer_email_lbl":      "Email :",
"customer_city_lbl":       "City :",
"customer_address_lbl":    "Address :",
"customer_notes_lbl":      "Notes :",
"customer_save_btn":       "💾  Save",
"customer_new_title":      "👤  New Customer",
"customer_edit_title":     "✏️  Edit Customer",
"customer_name_warn":      "Enter customer name",
"customer_delete_confirm": "Permanently delete customer «{name}»?\nCustomers with orders cannot be deleted.",
"customer_delete_failed":  "Cannot delete this customer — linked orders exist.\nYou can deactivate instead.",
"customer_toggle_active":  "✅  Activate",
"customer_toggle_inactive":"⏸  Deactivate",
"status_change_title":     "Change Order Status",
"status_current_lbl":      "Current Status:",
"status_new_lbl":          "New Status:",
"status_note_lbl":         "Notes (optional):",
"status_note_placeholder": "Reason for change...",
"status_change_btn":       "✅  Change Status",
"dashboard_recent_orders": "Recent Orders",
"dashboard_status_dist":   "Orders by Status",
"order_type_new":          "🆕 New",
"order_type_reorder":      "🔄 Re-order",
"order_type_custom":       "⚙️ Custom",
"priority_low":            "⬇ Low",
"priority_normal":         "➡ Normal",
"priority_high":           "⬆ High",
"priority_urgent":         "🔴 Urgent",
"status_on_hold":          "⏸ On Hold",
"status_in_progress":      "🔧 In Progress",
"status_ready":            "📦 Ready",
"order_total_value":       "Total Value",
"order_total_paid":        "Total Paid",
"order_urgent_count":      "Urgent",
"order_total_count":       "Total Orders",
"order_no_items_title":    "No items in this order",
"order_no_items_hint":     "Press «＋ Add Item» to add a product",
"order_select_first":      "Select an order from the list",
"order_select_subtitle":   "Or create a new order by pressing ＋ New Order",
"customer_select_first":   "Select a customer from the list",
"customer_select_subtitle":"Or add a new customer by pressing ＋",
"log_section_title":       "Status Change Log",
"log_col_from":            "From",
"log_col_to":              "To",
"log_col_notes":           "Notes",
"log_col_time":            "Time",
"items_col_name":          "Item",
"items_col_desc":          "Description",
"items_col_qty":           "Qty",
"items_col_unit":          "Unit",
"items_col_price":         "Price",
"items_col_discount":      "Disc%",
"items_col_total":         "Total",
"customer_col_code":       "Code",
"customer_col_name":       "Name",
"customer_col_phone":      "Phone",
"customer_col_city":       "City",
"customer_col_orders":     "Orders",
"order_col_number":        "Order No.",
"order_col_customer":      "Customer",
"order_col_status":        "Status",
"order_col_priority":      "⚑",
"order_col_date":          "Date",
"customer_total_orders":   "Total Orders",
"customer_active_orders":  "Active Orders",
"customer_total_value":    "Total Value",
"customer_balance":        "Balance",
"customer_contacts_title": "📞  Contacts",
"customer_orders_title":   "📋  Recent Orders",
"customer_no_contacts":    "No contacts",
"offer_select_label":      "— Select Offer —",
"order_header_total":      "Total",
"order_header_paid":       "Paid",
"order_header_balance":    "Balance",
"order_header_due":        "Due Date",
```

---

## ثانياً: ألوان جديدة في `theme_manager.py`

**لا يوجد أي لون جديد يحتاج إضافة.**
جميع الألوان المستخدمة في ملفات orders موجودة بالفعل في `_LIGHT_THEME` و`_DARK_THEME`:

| اللون المستخدم | المفتاح الموجود |
|---|---|
| `#1565c0` / أزرق | `_C['accent']` |
| `#10b981` / أخضر | `_C['success']` |
| `#ef4444` / أحمر | `_C['danger']` |
| `#6b7280` / رمادي | `_C['text_muted']` |
| `#f59e0b` / برتقالي | `_C['warning']` |
| `#8b5cf6` / بنفسجي | `_C['purple']` |
| `#374151` / داكن | `_C['text_sec']` |
| `#9ca3af` / فاتح | `_C['text_disabled']` |
| `#b45309` / بني | `_C['warning']` (نفس الغرض) |
| `#065f46` / أخضر داكن | `_C['success']` (نفس الغرض) |
| `#1d4ed8` / أزرق غامق | `_C['accent']` (نفس الغرض) |
| `#6d28d9` / بنفسجي | `_C['purple']` (نفس الغرض) |
| `#991b1b` / أحمر داكن | `_C['danger']` (نفس الغرض) |
| `#9a3412` / برتقالي داكن | `_C['orange']` |

---

## ثالثاً: إعدادات خطوط جديدة في `font.py`

**لا يوجد أي إعداد خط جديد يحتاج إضافة.**
جميع احتياجات الخطوط في ملفات orders تُغطيها الثوابت الموجودة:
- `FS_XS = 10`, `FS_SM = 11`, `FS_BASE = 12`, `FS_MD = 13`, `FS_LG = 14`, `FS_XL = 16`
- `get_font_size()` للـ dynamic sizing
- `fs(base, delta)` للأحجام النسبية

---

## رابعاً: التعديلات على كل ملف

---

### `ui/tabs/orders/orders_section.py`

**المشاكل:** لا يوجد hardcoded، لكن `get_font_size` مستوردة من مكان خاطئ.

```python
"""
ui/tabs/orders/orders_section.py
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.orders.orders_schema import get_orders_connection, create_orders_tables
from ui.tabs.orders.orders_tab    import OrdersTab
from ui.tabs.orders.customers_tab import CustomersTab
from ui.tabs.orders.dashboard_tab import OrdersDashboardTab
from ui.widgets.theme.layout_styles import tab_style


class OrdersSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_orders_connection()
        create_orders_tables(self.conn)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet(tab_style())

        self._dashboard_tab = OrdersDashboardTab(self.conn)
        self._orders_tab    = OrdersTab(self.conn)
        self._customers_tab = CustomersTab(self.conn)

        tabs.addTab(self._dashboard_tab, "📊 لوحة المتابعة")
        tabs.addTab(self._orders_tab,    "📋 الطلبات")
        tabs.addTab(self._customers_tab, "👥 العملاء")

        tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(tabs)

    def _on_tab_changed(self, index):
        if index == 0:
            self._dashboard_tab.refresh()
        elif index == 1:
            self._orders_tab.refresh()
        elif index == 2:
            self._customers_tab.refresh()

    def closeEvent(self, event):
        try:
            self.conn.close()
        except Exception:
            pass
        super().closeEvent(event)
```

---

### `ui/tabs/orders/orders_tab.py`

**المشاكل:** استيراد `BaseSection` من مكان خاطئ.

```python
"""
ui/tabs/orders/orders_tab.py
"""
from ui.tabs.orders._order_detail           import _OrderDetail
from ui.tabs.orders.orders._orders_list_panel import _OrdersListPanel
from ui.widgets.base.section                import BaseSection


class OrdersTab(BaseSection):

    LIST_MIN_W = 280

    def __init__(self, conn, parent=None):
        self._conn = conn
        super().__init__(conn=conn, parent=parent)

    def _create_list(self):
        return _OrdersListPanel(self._conn)

    def _create_detail(self):
        return _OrderDetail(self._conn)

    def _connect_signals(self):
        self._list.order_selected.connect(self._on_order_selected)
        self._list.new_order.connect(self._on_new_order)
        self._detail.saved.connect(self._on_saved)
        self._detail.deleted.connect(self._on_deleted)
        self._detail.status_changed.connect(self._on_status_changed)
        self._list._filter_bar.changed.connect(self._fit_splitter_delayed)

    def _on_order_selected(self, order_id: int):
        self._detail.load_order(order_id)

    def _on_new_order(self):
        self._detail.new_order()

    def _on_saved(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)
        self._fit_splitter_delayed()

    def _on_deleted(self):
        self._list.refresh()
        self._detail.clear()
        self._fit_splitter_delayed()

    def _on_status_changed(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)
        self._detail.load_order(order_id)

    def _fit_splitter_delayed(self, *args):
        super()._fit_splitter_delayed()
```

---

### `ui/tabs/orders/customers_tab.py`

**المشاكل:** استيراد `BaseSection` من مكان خاطئ.

```python
"""
ui/tabs/orders/customers_tab.py
"""
from ui.tabs.orders._customer_form                   import _CustomerForm
from ui.tabs.orders.customers.customers_list_panel   import CustomersListPanel
from ui.tabs.orders.customers.customer_detail_panel  import CustomerDetailPanel
from ui.widgets.base.section                         import BaseSection


class CustomersTab(BaseSection):

    LIST_MIN_W = 300

    def __init__(self, conn, parent=None):
        self._conn = conn
        super().__init__(conn=conn, parent=parent)

    def _create_list(self):
        return CustomersListPanel(self._conn)

    def _create_detail(self):
        return CustomerDetailPanel(self._conn)

    def _connect_signals(self):
        self._list.customer_selected.connect(self._detail.load_customer)
        self._list.new_customer.connect(self._new_customer)
        self._detail.edited.connect(self._on_edited)
        self._detail.deleted.connect(self._list.refresh)

    def _on_edited(self, cid: int):
        self._list.refresh()
        self._fit_splitter_delayed(50)

    def _new_customer(self):
        dlg = _CustomerForm(self._conn, parent=self)
        dlg.saved.connect(self._on_saved)
        dlg.exec_()

    def _on_saved(self, cid: int):
        self._list.refresh()
        self._list.select_customer(cid)
        self._detail.load_customer(cid)
        self._fit_splitter_delayed(50)
```

---

### `ui/tabs/orders/dashboard_tab.py`

**المشاكل:** hardcoded text، استيراد خاطئ.

```python
"""
ui/tabs/orders/dashboard_tab.py
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_orders_summary, fetch_all_orders
from ui.widgets.core.i18n import tr

from .dashboard._top_cards    import build_top_cards
from .dashboard._status_grid  import build_status_grid
from .dashboard._recent_table import build_recent_table, fill_recent_table


class OrdersDashboardTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scroll.setMaximumHeight(340)

        top_content = QWidget()
        top_lay = QVBoxLayout(top_content)
        top_lay.setContentsMargins(20, 16, 20, 12)
        top_lay.setSpacing(16)

        top_lay.addLayout(build_top_cards(self))

        lbl_status = QLabel(tr("dashboard_status_dist"))
        lbl_status.setStyleSheet("font-weight:bold;")
        top_lay.addWidget(lbl_status)
        top_lay.addWidget(build_status_grid(self))

        scroll.setWidget(top_content)
        root.addWidget(scroll)

        hdr_widget = QWidget()
        recent_hdr = QHBoxLayout(hdr_widget)
        recent_hdr.setContentsMargins(20, 8, 20, 4)

        lbl_recent = QLabel(tr("dashboard_recent_orders"))
        lbl_recent.setStyleSheet("font-weight:bold;")

        btn_refresh = QPushButton(tr("order_refresh_btn"))
        btn_refresh.setMinimumHeight(30)
        btn_refresh.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_refresh.clicked.connect(self.refresh)

        recent_hdr.addWidget(lbl_recent)
        recent_hdr.addStretch()
        recent_hdr.addWidget(btn_refresh)
        root.addWidget(hdr_widget)

        table_container = QWidget()
        tc_lay = QVBoxLayout(table_container)
        tc_lay.setContentsMargins(20, 0, 20, 16)
        tc_lay.setSpacing(0)
        tc_lay.addWidget(build_recent_table(self))
        root.addWidget(table_container, stretch=1)

    def refresh(self):
        summary = fetch_orders_summary(self.conn)

        self._lbl_total.setText(str(summary.get("total") or 0))
        self._lbl_urgent.setText(str(summary.get("urgent") or 0))
        self._lbl_total_value.setText(f"{(summary.get('total_value') or 0):,.0f} {tr('currency_sym')}")
        self._lbl_total_paid.setText(f"{(summary.get('total_paid') or 0):,.0f} {tr('currency_sym')}")

        for status, lbl in self._status_chips.items():
            lbl.setText(str(summary.get(status) or 0))

        fill_recent_table(self, fetch_all_orders(self.conn)[:20])
```

---

### `ui/tabs/orders/dashboard/_config.py`

**المشاكل:** كل النصوص والألوان hardcoded.

```python
"""
ui/tabs/orders/dashboard/_config.py
"""
from ui.theme import _C
from ui.widgets.core.i18n import tr


def get_status_config() -> dict:
    """يرجع إعدادات الحالات مع الألوان من _C."""
    return {
        "pending":     ("⏳", tr("status_pending"),     _C['warning'],  _C['warning_bg'],  _C['warning_border']),
        "confirmed":   ("✅", tr("status_confirmed"),   _C['accent'],   _C['accent_light'],_C['accent_mid']),
        "in_progress": ("🔧", tr("status_in_progress"), _C['purple'],   _C['purple_bg'],   _C['purple_border']),
        "ready":       ("📦", tr("status_ready"),       _C['success'],  _C['success_bg'],  _C['success_border']),
        "delivered":   ("🚚", tr("status_delivered"),   _C['text_sec'], _C['bg_surface_2'],_C['border']),
        "cancelled":   ("❌", tr("status_cancelled"),   _C['danger'],   _C['danger_bg'],   _C['danger_border']),
        "on_hold":     ("⏸", tr("status_on_hold"),     _C['orange'],   _C['orange_bg'],   _C['orange_border']),
    }


def get_status_map() -> dict:
    return {
        "pending":     f"⏳ {tr('status_pending')}",
        "confirmed":   f"✅ {tr('status_confirmed')}",
        "in_progress": f"🔧 {tr('status_in_progress')}",
        "ready":       f"📦 {tr('status_ready')}",
        "delivered":   f"🚚 {tr('status_delivered')}",
        "cancelled":   f"❌ {tr('status_cancelled')}",
        "on_hold":     f"⏸ {tr('status_on_hold')}",
    }


def get_status_color() -> dict:
    return {
        "pending":     _C['warning'],
        "confirmed":   _C['accent'],
        "in_progress": _C['purple'],
        "ready":       _C['success'],
        "delivered":   _C['text_sec'],
        "cancelled":   _C['danger'],
        "on_hold":     _C['orange'],
    }


def get_type_map() -> dict:
    return {
        "new":     tr("order_type_new"),
        "reorder": tr("order_type_reorder"),
        "custom":  tr("order_type_custom"),
    }


def get_priority_map() -> dict:
    return {
        "low":    tr("priority_low"),
        "normal": tr("priority_normal"),
        "high":   tr("priority_high"),
        "urgent": tr("priority_urgent"),
    }


TABLE_COLS_KEYS = [
    "order_col_number", "order_col_customer", "order_type_label",
    "order_col_status", "order_col_priority", "order_header_total", "order_date"
]

COL_WIDTHS = {0: 130, 1: 160, 2: 80, 3: 100, 4: 75, 5: 100, 6: 90}
```

---

### `ui/tabs/orders/dashboard/_top_cards.py`

**المشاكل:** hardcoded text وألوان hardcoded.

```python
"""
ui/tabs/orders/dashboard/_top_cards.py
"""
from PyQt5.QtWidgets import QHBoxLayout
from ui.widgets.components.stat_card import make_stat_card_simple
from ui.widgets.core.i18n import tr
from ui.theme import _C


def build_top_cards(dashboard) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(12)

    f1, dashboard._lbl_total = make_stat_card_simple(
        "📋", tr("order_total_count"),  color=_C['accent'])
    f2, dashboard._lbl_urgent = make_stat_card_simple(
        "🔴", tr("order_urgent_count"), color=_C['danger'])
    f3, dashboard._lbl_total_value = make_stat_card_simple(
        "💰", tr("order_total_value"),  color=_C['success'])
    f4, dashboard._lbl_total_paid = make_stat_card_simple(
        "✅", tr("order_total_paid"),   color=_C['accent'])

    for f in (f1, f2, f3, f4):
        row.addWidget(f, stretch=1)

    return row
```

---

### `ui/tabs/orders/dashboard/_status_grid.py`

**المشاكل:** يستورد من `_config.py` القديم الذي يحتوي على hardcoded.

```python
"""
ui/tabs/orders/dashboard/_status_grid.py
"""
from ui.widgets.panels.layout_widgets import CardGrid
from ui.widgets.components.status_chip import make_status_chip
from ._config import get_status_config


def build_status_grid(dashboard) -> CardGrid:
    dashboard._status_chips = {}
    grid = CardGrid(cols=4, spacing=10)

    for status, (icon, label, color, bg, border) in get_status_config().items():
        chip, cnt_lbl = make_status_chip(icon, label, 0, color, bg, border)
        grid.add_widget(chip)
        dashboard._status_chips[status] = cnt_lbl

    return grid
```

---

### `ui/tabs/orders/dashboard/_recent_table.py`

**المشاكل:** hardcoded column names وألوان.

```python
"""
ui/tabs/orders/dashboard/_recent_table.py
"""
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QColor

from ui.widgets.tables.tables import (
    make_table, insert_row, ROW_HEIGHT_NORMAL,
    auto_fit_columns,
)
from ui.widgets.core.i18n import tr
from ._config import get_status_map, get_status_color, get_type_map, get_priority_map, COL_WIDTHS


def build_recent_table(dashboard):
    cols = [tr(k) for k in [
        "order_col_number", "order_col_customer", "order_type_label",
        "order_col_status", "order_col_priority", "order_header_total", "order_date"
    ]]
    table = make_table(cols, stretch_col=-1, col_widths=COL_WIDTHS)
    dashboard.recent_table = table

    container_widget = table  # بدون splitter — table مباشرة
    return container_widget


def fill_recent_table(dashboard, orders: list):
    table = dashboard.recent_table
    table.setRowCount(0)

    status_map   = get_status_map()
    status_color = get_status_color()
    type_map     = get_type_map()
    priority_map = get_priority_map()

    for o in orders:
        r = insert_row(table, ROW_HEIGHT_NORMAL)

        num_item = QTableWidgetItem(o["order_number"])
        f = QFont()
        f.setWeight(QFont.Medium)
        num_item.setFont(f)
        table.setItem(r, 0, num_item)

        table.setItem(r, 1, QTableWidgetItem(o["customer_name"]))
        table.setItem(r, 2, QTableWidgetItem(type_map.get(o["order_type"], o["order_type"])))

        status_item = QTableWidgetItem(status_map.get(o["status"], o["status"]))
        status_item.setForeground(QColor(status_color.get(o["status"], "#555")))
        status_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 3, status_item)

        pri_item = QTableWidgetItem(priority_map.get(o["priority"], ""))
        pri_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 4, pri_item)

        amt_item = QTableWidgetItem(f"{(o['net_amount'] or 0):,.2f} {tr('currency_sym')}")
        amt_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 5, amt_item)

        date_item = QTableWidgetItem(o["order_date"] or "")
        date_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 6, date_item)

    auto_fit_columns(table, fixed_cols=list(COL_WIDTHS.keys()), stretch_col=-1)
```

---

### `ui/tabs/orders/order_detail/_status_config.py`

**المشاكل:** كل القيم hardcoded.

```python
"""
ui/tabs/orders/order_detail/_status_config.py
"""
from ui.theme import _C
from ui.widgets.core.i18n import tr


def get_status_labels() -> dict:
    return {
        "pending":     (f"⏳ {tr('status_pending')}",     _C['warning'],  _C['warning_bg'],  _C['warning_border']),
        "confirmed":   (f"✅ {tr('status_confirmed')}",   _C['accent'],   _C['accent_light'],_C['accent_mid']),
        "in_progress": (f"🔧 {tr('status_in_progress')}", _C['purple'],   _C['purple_bg'],   _C['purple_border']),
        "ready":       (f"📦 {tr('status_ready')}",       _C['success'],  _C['success_bg'],  _C['success_border']),
        "delivered":   (f"🚚 {tr('status_delivered')}",   _C['text_sec'], _C['bg_surface_2'],_C['border']),
        "cancelled":   (f"❌ {tr('status_cancelled')}",   _C['danger'],   _C['danger_bg'],   _C['danger_border']),
        "on_hold":     (f"⏸ {tr('status_on_hold')}",     _C['orange'],   _C['orange_bg'],   _C['orange_border']),
    }


def get_priority_labels() -> dict:
    return {
        "low":    (tr("priority_low"),    _C['text_disabled']),
        "normal": (tr("priority_normal"), _C['text_muted']),
        "high":   (tr("priority_high"),   _C['warning']),
        "urgent": (tr("priority_urgent"), _C['danger']),
    }


def get_type_labels() -> dict:
    return {
        "new":     tr("order_type_new"),
        "reorder": tr("order_type_reorder"),
        "custom":  tr("order_type_custom"),
    }


STATUS_TRANSITIONS = {
    "pending":     ["confirmed", "cancelled", "on_hold"],
    "confirmed":   ["in_progress", "cancelled", "on_hold"],
    "in_progress": ["ready", "cancelled", "on_hold"],
    "ready":       ["delivered", "cancelled"],
    "on_hold":     ["pending", "confirmed", "cancelled"],
    "delivered":   [],
    "cancelled":   ["pending"],
}

# للتوافق مع الكود القديم — تُحسب عند الاستدعاء
def get_status_labels_short() -> dict:
    return {k: v[0] for k, v in get_status_labels().items()}

def get_status_colors() -> dict:
    return {k: v[1:] for k, v in get_status_labels().items()}
```

---

### `ui/tabs/orders/order_detail/_header_fill.py`

**المشاكل:** يستورد `STATUS_LABELS` و `PRIORITY_LABELS` و `TYPE_LABELS` كثوابت hardcoded.

```python
"""
ui/tabs/orders/order_detail/_header_fill.py
"""
from ui.widgets.core.i18n import tr
from ._status_config import (
    get_status_labels, get_priority_labels, get_type_labels, STATUS_TRANSITIONS
)
from ui.theme import _C


def _fill_header(detail):
    d = detail._order_data
    STATUS_LABELS   = get_status_labels()
    PRIORITY_LABELS = get_priority_labels()
    TYPE_LABELS     = get_type_labels()

    detail._hdr.set_title(d["order_number"])
    detail._hdr.set_type_badge(TYPE_LABELS.get(d["order_type"], ""))

    si = STATUS_LABELS.get(d["status"], (d["status"], _C['text_sec'], _C['bg_surface_2'], _C['border']))
    detail._hdr.set_status_badge(si[0], si[1], si[2], si[3])

    pri_lbl, pri_color = PRIORITY_LABELS.get(d["priority"], ("", _C['text_muted']))
    detail._hdr.set_priority_badge(pri_lbl, pri_color)

    customer_line = f"👤  {d['customer_name']}  ({d['customer_code']})"
    info_parts = []
    if d.get("customer_phone"): info_parts.append(f"📞 {d['customer_phone']}")
    if d.get("customer_city"):  info_parts.append(f"📍 {d['customer_city']}")

    detail._hdr.set_customer_name(customer_line)
    detail._hdr.set_info(info_parts)

    net    = d.get("net_amount")  or 0
    paid   = d.get("paid_amount") or 0
    remain = net - paid

    detail._card_total.set_value(f"{net:,.2f} {tr('currency_sym')}")
    detail._card_paid.set_value(f"{paid:,.2f} {tr('currency_sym')}")
    detail._card_balance.set_value(f"{remain:,.2f} {tr('currency_sym')}")
    detail._card_balance.set_color(_C['danger'] if remain > 0 else _C['success'])
    detail._card_due.set_value(d.get("due_date") or "─")

    status     = d["status"]
    can_edit   = status not in ("delivered", "cancelled")
    can_cancel = status not in ("delivered", "cancelled")
    can_delete = status in ("pending", "cancelled")
    can_change = bool(STATUS_TRANSITIONS.get(status))

    detail.btn_edit.setEnabled(can_edit)
    detail.btn_cancel.setEnabled(can_cancel)
    detail.btn_delete.setEnabled(can_delete)
    detail.btn_status.setEnabled(can_change)
    detail.btn_add_item.setEnabled(can_edit)
```

---

### `ui/tabs/orders/order_detail/_items_section.py`

**المشاكل:** استيرادات خاطئة، hardcoded text وألوان، `make_splitter_table_guarded` غير موجودة.

```python
"""
ui/tabs/orders/order_detail/_items_section.py
"""
from PyQt5.QtWidgets import QFrame, QHBoxLayout
from PyQt5.QtCore    import Qt

from db.orders.orders_repo import fetch_order_items
from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.panels.state import EmptyState
from ui.widgets.components.button import make_btn
from ui.widgets.tables.tables import (
    make_table, insert_row, auto_fit_columns,
    make_item, bold_item, colored_item, muted_item,
    ROW_HEIGHT_NORMAL,
)
from ui.widgets.core.i18n import tr
from ui.theme import _C


def _build_items_section(detail):
    items_hdr = SectionHeader(tr("order_items_section"))
    detail.btn_add_item = items_hdr.add_button(tr("order_add_item_btn"), detail._add_item, "success")
    detail._content_lay.addWidget(items_hdr)

    detail.items_table = make_table(
        columns=[
            tr("items_col_name"), tr("items_col_desc"), tr("items_col_qty"),
            tr("items_col_unit"), tr("items_col_price"),
            tr("items_col_discount"), tr("items_col_total"),
        ],
        stretch_col=0,
        col_widths={2: 65, 3: 65, 4: 90, 5: 60, 6: 95},
    )
    detail.items_table.setMaximumHeight(280)
    detail.items_table.setMinimumHeight(60)
    detail._content_lay.addWidget(detail.items_table)

    detail._empty_items = EmptyState(
        icon="📦",
        title=tr("order_no_items_title"),
        subtitle=tr("order_no_items_hint"),
        style="dashed",
        color=_C['success'],
        min_height=90,
    )
    detail._empty_items.action_clicked.connect(detail._add_item)
    detail._content_lay.addWidget(detail._empty_items)

    item_toolbar = QFrame()
    item_toolbar.setStyleSheet("background:transparent;")
    itb_lay = QHBoxLayout(item_toolbar)
    itb_lay.setContentsMargins(0, 0, 0, 0)
    itb_lay.setSpacing(6)

    detail.btn_edit_item = make_btn(tr("order_edit_item_btn"), "ghost")
    detail.btn_edit_item.setMinimumHeight(28)
    detail.btn_edit_item.clicked.connect(detail._edit_item)

    detail.btn_del_item = make_btn(tr("order_del_item_btn"), "danger")
    detail.btn_del_item.setMinimumHeight(28)
    detail.btn_del_item.clicked.connect(detail._del_item)

    itb_lay.addWidget(detail.btn_edit_item)
    itb_lay.addWidget(detail.btn_del_item)
    itb_lay.addStretch()

    detail._item_toolbar = item_toolbar
    detail._content_lay.addWidget(item_toolbar)


def _fill_items(detail):
    items = fetch_order_items(detail.conn, detail._order_id)
    table = detail.items_table
    table.setRowCount(0)

    has_items = bool(items)
    table.setVisible(has_items)
    detail._empty_items.setVisible(not has_items)
    detail.btn_edit_item.setVisible(has_items)
    detail.btn_del_item.setVisible(has_items)
    detail._item_toolbar.setVisible(has_items)

    for item in items:
        r = insert_row(table, ROW_HEIGHT_NORMAL)

        name_item = make_item(item["item_name"], user_data=item["id"])
        bold_item(name_item)
        table.setItem(r, 0, name_item)
        table.setItem(r, 1, make_item(item.get("description") or ""))
        table.setItem(r, 2, make_item(f"{item['quantity']:g}", align=Qt.AlignCenter))

        unit_item = muted_item(make_item(item["unit"], align=Qt.AlignCenter))
        table.setItem(r, 3, unit_item)
        table.setItem(r, 4, make_item(f"{item['unit_price']:,.2f}", align=Qt.AlignCenter))

        disc_item = muted_item(make_item(f"{item['discount_pct']:g}%", align=Qt.AlignCenter))
        table.setItem(r, 5, disc_item)

        total_val  = item["quantity"] * item["unit_price"] * (1 - item["discount_pct"] / 100)
        total_item = colored_item(
            f"{total_val:,.2f}", _C['accent'], align=Qt.AlignCenter
        )
        bold_item(total_item)
        table.setItem(r, 6, total_item)

    if has_items:
        auto_fit_columns(table, fixed_cols=[2, 3, 4, 5, 6], stretch_col=0)
```

---

### `ui/tabs/orders/order_detail/_log_section.py`

**المشاكل:** استيرادات خاطئة، `make_splitter_table_guarded` غير موجودة.

```python
"""
ui/tabs/orders/order_detail/_log_section.py
"""
from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_status_log
from ui.widgets.panels.layout_widgets import CollapsibleCard
from ui.widgets.tables.tables import (
    make_table, insert_row, auto_fit_columns,
    make_item, colored_item, bold_item, muted_item,
    ROW_HEIGHT_COMPACT,
)
from ui.widgets.core.i18n import tr
from ._status_config import get_status_labels


def _build_log_section(detail):
    detail._log_card = CollapsibleCard(tr("log_section_title"), expanded=False)

    detail.log_table = make_table(
        columns=[
            tr("log_col_from"), tr("log_col_to"),
            tr("log_col_notes"), tr("log_col_time"),
        ],
        stretch_col=2,
        col_widths={0: 100, 1: 100, 3: 120},
    )
    detail.log_table.setMaximumHeight(160)
    detail._log_card.content_layout.addWidget(detail.log_table)
    detail._content_lay.addWidget(detail._log_card)


def _fill_log(detail):
    logs   = [dict(r) for r in fetch_status_log(detail.conn, detail._order_id)]
    table  = detail.log_table
    STATUS_LABELS = get_status_labels()
    table.setRowCount(0)

    for log in logs:
        r = insert_row(table, ROW_HEIGHT_COMPACT)

        old_lbl  = STATUS_LABELS.get(log.get("old_status") or "", ("—",))[0]
        new_info = STATUS_LABELS.get(log.get("new_status", ""),
                                     (log.get("new_status", ""), "#555", "#f5f5f5", "#e0e0e0"))
        new_lbl, new_color = new_info[0], new_info[1]

        table.setItem(r, 0, muted_item(make_item(old_lbl)))

        new_item = make_item(new_lbl)
        bold_item(new_item)
        colored_item(new_lbl, new_color)
        table.setItem(r, 1, new_item)

        table.setItem(r, 2, make_item(log.get("notes") or ""))
        table.setItem(r, 3, muted_item(
            make_item((log.get("changed_at") or "")[:16], align=Qt.AlignCenter)
        ))

    if logs:
        auto_fit_columns(table, fixed_cols=[0, 1, 3], stretch_col=2)
```

---

### `ui/tabs/orders/order_detail/_status_dialog.py`

**المشاكل:** hardcoded text، استيرادات خاطئة، ألوان hardcoded.

```python
"""
ui/tabs/orders/order_detail/_status_dialog.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ._status_config import get_status_labels, get_status_labels_short, get_status_colors


class _StatusDialog(QDialog):
    def __init__(self, current_status: str, next_statuses: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("status_change_title"))
        self.setMinimumWidth(400)
        self.setModal(True)
        self._result = (next_statuses[0] if next_statuses else current_status, "")
        self._build(current_status, next_statuses)

    def _build(self, current, nexts):
        self.setStyleSheet(input_style())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        STATUS_LABELS_SHORT = get_status_labels_short()
        STATUS_COLORS       = get_status_colors()

        lbl_hdr = QLabel(tr("status_change_title"))
        lbl_hdr.setStyleSheet(f"""
            font-size: 14px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: 8px; padding: 8px 14px; border: none;
        """)
        lay.addWidget(lbl_hdr)

        cur_info = STATUS_COLORS.get(current, (_C['text_sec'], _C['bg_surface_2'], _C['border']))
        lbl_cur  = QLabel(f"{tr('status_current_lbl')}  {STATUS_LABELS_SHORT.get(current, current)}")
        lbl_cur.setStyleSheet(
            f"color:{cur_info[0]}; font-weight:600; font-size:12px;"
            f"background:{cur_info[1]}; border:1px solid {cur_info[2]};"
            "border-radius:6px; padding:6px 10px;"
        )
        lay.addWidget(lbl_cur)

        lay.addWidget(QLabel(tr("status_new_lbl")))
        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(36)
        for s in nexts:
            self._cmb.addItem(STATUS_LABELS_SHORT.get(s, s), s)
        lay.addWidget(self._cmb)

        lay.addWidget(QLabel(tr("status_note_lbl")))
        self._note = QLineEdit()
        self._note.setPlaceholderText(tr("status_note_placeholder"))
        lay.addWidget(self._note)

        btns = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = make_btn(tr("status_change_btn"), "primary")
        btn_ok.setMinimumHeight(38)
        btn_ok.clicked.connect(self._save)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok, stretch=1)
        lay.addLayout(btns)

    def _save(self):
        self._result = (self._cmb.currentData(), self._note.text().strip())
        self.accept()

    def get_result(self):
        return self._result
```

---

### `ui/tabs/orders/_order_detail.py`

**المشاكل:** استيرادات خاطئة، hardcoded text.

```python
"""
ui/tabs/orders/_order_detail.py
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QDialog
from PyQt5.QtCore import pyqtSignal

from db.orders.orders_repo import (
    fetch_order, fetch_order_items,
    change_order_status, cancel_order, delete_order,
    reorder as do_reorder, delete_order_item,
)
from ui.tabs.orders._order_form import _OrderForm
from ui.tabs.orders._item_form  import _ItemForm
from ui.widgets.base.detail_panel import BaseDetailPanel
from ui.widgets.core.i18n import tr
from ui.theme import _C

from ui.tabs.orders.order_detail._items_section import _build_items_section, _fill_items
from ui.tabs.orders.order_detail._log_section   import _build_log_section, _fill_log
from ui.tabs.orders.order_detail._header_fill   import _fill_header
from ui.tabs.orders.order_detail._status_config import STATUS_TRANSITIONS
from ui.tabs.orders.order_detail._status_dialog import _StatusDialog


class _OrderDetail(BaseDetailPanel):
    saved          = pyqtSignal(int)
    deleted        = pyqtSignal()
    status_changed = pyqtSignal(int)

    EMPTY_ICON     = "📋"
    EMPTY_TITLE    = "order_select_first"      # مفتاح tr
    EMPTY_SUBTITLE = "order_select_subtitle"   # مفتاح tr

    def __init__(self, conn, parent=None):
        self._order_id   = None
        self._order_data = None
        super().__init__(conn=conn, parent=parent)

    def _build_header_cards(self):
        self._card_total   = self._hdr.add_stat_card("💰", tr("order_header_total"),  color=_C['accent'])
        self._card_paid    = self._hdr.add_stat_card("✅", tr("order_header_paid"),   color=_C['success'])
        self._card_balance = self._hdr.add_stat_card("⚖️", tr("order_header_balance"),color=_C['danger'])
        self._card_due     = self._hdr.add_stat_card("📅", tr("order_header_due"),    color=_C['warning'])

    def _build_header_buttons(self):
        self.btn_edit    = self._hdr.toolbar.add_action(tr("order_edit_btn"),          "primary")
        self.btn_status  = self._hdr.toolbar.add_action(tr("order_change_status_btn"), "ghost")
        self.btn_reorder = self._hdr.toolbar.add_action(tr("order_reorder_btn"),       "ghost")
        self.btn_cancel  = self._hdr.toolbar.add_danger(tr("order_cancel_btn_action"))
        self.btn_delete  = self._hdr.toolbar.add_danger(tr("order_delete_btn"))

        self.btn_edit.clicked.connect(self._edit_order)
        self.btn_status.clicked.connect(self._change_status_dialog)
        self.btn_reorder.clicked.connect(self._do_reorder)
        self.btn_cancel.clicked.connect(self._cancel_order)
        self.btn_delete.clicked.connect(self._delete_order)

    def _build_content(self, lay: QVBoxLayout):
        _build_items_section(self)
        _build_log_section(self)

    def _load_data(self, item_id: int):
        return fetch_order(self.conn, item_id)

    def _fill_data(self, data: dict):
        self._order_id   = self._item_id
        self._order_data = data
        _fill_header(self)
        _fill_items(self)
        _fill_log(self)

    def load_order(self, order_id: int):
        self.load_item(order_id)

    def clear(self):
        self._order_id   = None
        self._order_data = None
        self._item_id    = None
        self._item_data  = None
        self._show_empty()

    def new_order(self):
        dlg = _OrderForm(self.conn, parent=self)
        dlg.saved.connect(self._on_form_saved)
        dlg.exec_()

    def _edit_order(self):
        if not self._order_id:
            return
        dlg = _OrderForm(self.conn, order_id=self._order_id, parent=self)
        dlg.saved.connect(self._on_form_saved)
        dlg.exec_()

    def _on_form_saved(self, order_id: int):
        self.load_order(order_id)
        self.saved.emit(order_id)

    def _change_status_dialog(self):
        if not self._order_id or not self._order_data:
            return
        current       = self._order_data["status"]
        next_statuses = STATUS_TRANSITIONS.get(current, [])
        if not next_statuses:
            return
        dlg = _StatusDialog(current, next_statuses, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_status, note = dlg.get_result()
            change_order_status(self.conn, self._order_id, new_status, note)
            self.status_changed.emit(self._order_id)

    def _cancel_order(self):
        if not self._order_id:
            return
        d = self._order_data
        if d["status"] in ("delivered", "cancelled"):
            return
        reason, ok = _get_text_input(
            self,
            tr("order_cancel_title"),
            tr("order_cancel_reason").format(number=d['order_number'])
        )
        if ok:
            cancel_order(self.conn, self._order_id, reason)
            self.status_changed.emit(self._order_id)

    def _delete_order(self):
        if not self._order_id:
            return
        d = self._order_data
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("order_delete_confirm").format(number=d['order_number']),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if delete_order(self.conn, self._order_id):
                self.deleted.emit()
            else:
                QMessageBox.warning(self, tr("warning"), tr("order_delete_failed"))

    def _do_reorder(self):
        if not self._order_id:
            return
        d = self._order_data
        if QMessageBox.question(
            self, tr("order_reorder_btn"),
            tr("order_reorder_confirm").format(number=d['order_number']),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            new_id = do_reorder(self.conn, self._order_id)
            if new_id:
                self.load_order(new_id)
                self.saved.emit(new_id)

    def _add_item(self):
        if not self._order_id:
            return
        if self._order_data and self._order_data["status"] in ("delivered", "cancelled"):
            QMessageBox.information(self, tr("info"), tr("order_no_items_warn"))
            return
        dlg = _ItemForm(self.conn, self._order_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            _fill_items(self)
            self._fill_header_amounts()

    def _edit_item(self):
        from PyQt5.QtCore import Qt
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, tr("info"), tr("select_item_first"))
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        dlg = _ItemForm(self.conn, self._order_id, item_id=item_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            _fill_items(self)
            self._fill_header_amounts()

    def _del_item(self):
        from PyQt5.QtCore import Qt
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, tr("info"), tr("select_item_first"))
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        name    = self.items_table.item(row, 0).text()
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("delete_confirm_msg").format(name=name),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_order_item(self.conn, item_id)
            _fill_items(self)
            self._fill_header_amounts()

    def _fill_header_amounts(self):
        if not self._order_id:
            return
        row = fetch_order(self.conn, self._order_id)
        self._order_data = dict(row) if row else None
        if self._order_data:
            net    = self._order_data.get("net_amount")  or 0
            paid   = self._order_data.get("paid_amount") or 0
            remain = net - paid
            self._card_total.set_value(f"{net:,.2f} {tr('currency_sym')}")
            self._card_paid.set_value(f"{paid:,.2f} {tr('currency_sym')}")
            self._card_balance.set_value(f"{remain:,.2f} {tr('currency_sym')}")
            self._card_balance.set_color(_C['danger'] if remain > 0 else _C['success'])


def _get_text_input(parent, title, prompt):
    from PyQt5.QtWidgets import QInputDialog
    return QInputDialog.getText(parent, title, prompt)
```

---

### `ui/tabs/orders/orders/_orders_list_panel.py`

**المشاكل:** استيرادات خاطئة، hardcoded text وألوان.

```python
"""
ui/tabs/orders/orders/_orders_list_panel.py
"""
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout
from PyQt5.QtCore    import Qt, pyqtSignal

from db.orders.orders_repo import fetch_all_orders
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.tables import (
    make_item, colored_item, bold_item, muted_item,
)
from ui.widgets.core.i18n import tr
from ui.theme import _C

from ._filter_toolbar  import _FilterToolbar
from ._status_delegate import _StatusDelegate
from ..order_detail._status_config import get_status_labels, get_priority_labels


class _OrdersListPanel(BaseListPanel):
    order_selected = pyqtSignal(int)
    new_order      = pyqtSignal()

    COLUMNS     = []   # تُبنى ديناميكياً في __init__
    STRETCH_COL = -1
    COL_WIDTHS  = {0: 130, 1: 150, 2: 100, 3: 32, 4: 90}
    MIN_W       = 280
    MAX_W       = 560
    EMPTY_ICON  = "📋"
    EMPTY_TITLE = "no_orders"   # مفتاح tr

    def __init__(self, conn, parent=None):
        self.COLUMNS = [
            tr("order_col_number"), tr("order_col_customer"),
            tr("order_col_status"), tr("order_col_priority"), tr("order_date"),
        ]
        self._filter_bar = _FilterToolbar()
        super().__init__(conn=conn, parent=parent)
        self.item_selected.connect(self.order_selected.emit)
        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

    def _build_toolbar(self, lay: QVBoxLayout):
        self._filter_bar.btn_new.clicked.connect(self.new_order.emit)
        self._filter_bar.changed.connect(self._apply_filter)
        lay.addWidget(self._filter_bar)

    def _load_rows(self) -> list:
        return fetch_all_orders(self.conn)

    def _match_filter(self, row, q: str) -> bool:
        if not hasattr(self, '_filter_bar'):
            return True
        status   = self._filter_bar.status_filter
        priority = self._filter_bar.priority_filter
        if status   and row["status"]   != status:   return False
        if priority and row["priority"] != priority: return False
        if q and q not in row["order_number"].lower() \
            and q not in row["customer_name"].lower():
            return False
        return True

    def _fill_row(self, table, r, row):
        STATUS_LABELS   = get_status_labels()
        PRIORITY_LABELS = get_priority_labels()

        num_item = make_item(row["order_number"], user_data=row["id"])
        bold_item(num_item)
        colored_item(row["order_number"], _C['accent'])
        table.setItem(r, 0, num_item)

        table.setItem(r, 1, make_item(row["customer_name"], tooltip=row["customer_name"]))

        status_text = STATUS_LABELS.get(row["status"], (row["status"],))[0]
        s_item = make_item(status_text, align=Qt.AlignCenter)
        s_item.setData(Qt.UserRole + 1, row["status"])
        table.setItem(r, 2, s_item)

        pri_lbl, pri_color = PRIORITY_LABELS.get(row["priority"], ("", _C['text_muted']))
        pri_text = pri_lbl.split()[0] if pri_lbl else ""
        pri_item = make_item(pri_text, align=Qt.AlignCenter)
        from PyQt5.QtGui import QColor
        pri_item.setForeground(QColor(pri_color))
        if row["priority"] in ("high", "urgent"):
            bold_item(pri_item)
        table.setItem(r, 3, pri_item)

        table.setItem(r, 4, muted_item(make_item((row["order_date"] or "")[:10])))

    def select_order(self, order_id: int):
        self.select_item(order_id)
```

---

### `ui/tabs/orders/orders/_filter_toolbar.py`

**المشاكل:** hardcoded text وألوان، استيرادات خاطئة.

```python
"""
ui/tabs/orders/orders/_filter_toolbar.py
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QPushButton, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QFontMetrics, QFont

from ui.theme import _C
from ui.widgets.components.button import make_btn
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE
from ..order_detail._status_config import get_status_labels, get_priority_labels


def _combo_ss() -> str:
    return f"""
        QComboBox {{
            background: {_C['bg_surface_2']};
            border: 1px solid {_C['border']};
            border-radius: 5px;
            padding: 0 8px;
            min-height: 28px;
            font-size: {FS_BASE - 1}px;
            color: {_C['text_primary']};
        }}
        QComboBox:focus {{ border-color: {_C['accent']}; }}
        QComboBox::drop-down {{ border: none; width: 16px; }}
        QComboBox QAbstractItemView {{
            background: {_C['bg_input']};
            border: 1px solid {_C['border_med']};
            selection-background-color: {_C['accent_light']};
            selection-color: {_C['accent_text']};
            outline: none;
        }}
    """


def _new_btn_ss() -> str:
    return f"""
        QPushButton {{
            background: {_C['accent']}; color: white;
            border: none; border-radius: 8px;
            padding: 0 16px; font-weight: 700; font-size: {FS_BASE}px;
        }}
        QPushButton:hover {{ background: {_C['accent_hover']}; }}
    """


def _fixed_btn(text: str, h: int = 36) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_new_btn_ss())
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(h)
    fm = QFontMetrics(QFont("", FS_BASE))
    w  = fm.horizontalAdvance(text) + 40
    btn.setFixedWidth(max(w, 100))
    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return btn


class _FilterToolbar(QFrame):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.changed.emit)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border: none;
                border-bottom: 1px solid {_C['border']};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 10)
        root.setSpacing(8)

        row0 = QHBoxLayout()
        row0.setContentsMargins(0, 0, 0, 0)
        row0.setSpacing(0)

        self.btn_new = _fixed_btn(tr("order_new_btn"), h=36)
        row0.addWidget(self.btn_new)
        row0.addStretch(1)
        root.addLayout(row0)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("order_search_placeholder"))
        self.inp_search.setFixedHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: {FS_BASE}px;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())
        root.addWidget(self.inp_search)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        STATUS_LABELS   = get_status_labels()
        PRIORITY_LABELS = get_priority_labels()

        self.cmb_status = QComboBox()
        self.cmb_status.setFixedHeight(28)
        self.cmb_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_status.setStyleSheet(_combo_ss())
        self.cmb_status.addItem(tr("order_all_statuses"), None)
        for k, (lbl, *_) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self.changed.emit)

        self.cmb_priority = QComboBox()
        self.cmb_priority.setFixedHeight(28)
        self.cmb_priority.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_priority.setStyleSheet(_combo_ss())
        self.cmb_priority.addItem(tr("order_all_priorities"), None)
        for k, (lbl, _) in PRIORITY_LABELS.items():
            icon = lbl.split()[0] if lbl else ""
            self.cmb_priority.addItem(icon, k)
        self.cmb_priority.currentIndexChanged.connect(self.changed.emit)

        btn_reset = make_btn(tr("order_reset_filter"), "ghost")
        btn_reset.setToolTip(tr("order_reset_filter"))
        btn_reset.clicked.connect(self.reset)

        row2.addWidget(self.cmb_status,   stretch=3)
        row2.addWidget(self.cmb_priority, stretch=2)
        row2.addWidget(btn_reset)
        root.addLayout(row2)

    @property
    def search_text(self) -> str:
        return self.inp_search.text().strip().lower()

    @property
    def status_filter(self):
        return self.cmb_status.currentData()

    @property
    def priority_filter(self):
        return self.cmb_priority.currentData()

    def reset(self):
        self.cmb_status.setCurrentIndex(0)
        self.cmb_priority.setCurrentIndex(0)
        self.inp_search.clear()
```

---

### `ui/tabs/orders/orders/_status_delegate.py`

**المشاكل:** hardcoded ألوان، استيراد `_C` من مكان خاطئ، استيراد `table_utils`.

```python
"""
ui/tabs/orders/orders/_status_delegate.py
"""
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QApplication
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui  import QColor, QPainter, QBrush, QPen

from ui.tables.tables import ROW_HEIGHT_LARGE
from ui.font import get_font_size, fs
from ..order_detail._status_config import get_status_labels


class _StatusDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        STATUS_LABELS = get_status_labels()
        status_key = index.data(Qt.UserRole + 1)
        text = index.data(Qt.DisplayRole) or ""

        info = STATUS_LABELS.get(status_key)
        if info:
            _, fg, bg, bd = info
        else:
            from ui.theme import _C
            fg, bg, bd = _C['text_sec'], _C['bg_surface_2'], _C['border']

        rect   = option.rect
        pad_v  = 7
        pad_h  = 6
        badge_w = min(rect.width() - pad_h * 2, 90)
        badge_h = rect.height() - pad_v * 2
        badge_h = max(badge_h, 22)
        badge_h = min(badge_h, 28)
        badge_x = rect.x() + (rect.width() - badge_w) // 2
        badge_y = rect.y() + (rect.height() - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(bg)))
        painter.setPen(QPen(QColor(bd), 1.2))
        painter.drawRoundedRect(badge_rect, 10, 10)

        painter.setPen(QPen(QColor(fg)))
        f = painter.font()
        f.setBold(True)
        base = get_font_size()
        f.setPointSize(max(8, fs(base, -1)))
        painter.setFont(f)
        painter.drawText(badge_rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(100, ROW_HEIGHT_LARGE)
```

**ملاحظة:** الاستيراد `from ui.tables.tables` — تأكد من المسار الصحيح `from ui.widgets.tables.tables import ROW_HEIGHT_LARGE`.

---

### `ui/tabs/orders/_order_form.py`

**المشاكل:** استيرادات خاطئة، hardcoded text وألوان، `get_costing_connection` محذوفة.

```python
"""
ui/tabs/orders/_order_form.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QDateEdit,
    QMessageBox, QGroupBox,
    QDoubleSpinBox, QScrollArea, QWidget, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate

from db.orders.customers_repo import fetch_all_customers, search_customers
from db.orders.orders_repo import (
    fetch_order, insert_order, update_order,
    fetch_order_items, insert_order_item,
    update_order_item, delete_order_item,
)
from db.shared.connection import get_connection
from .order_form._item_row_widget  import _ItemRowWidget
from .order_form._products_fetcher import fetch_offers, fetch_offer_lines

from ui.theme import _C
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE, FS_SM


def _group_ss(accent=None) -> str:
    c = accent or _C['accent']
    return f"""
        QGroupBox {{
            font-weight: bold;
            color: {_C['text_sec']};
            border: 1px solid {_C['border']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background: {_C['bg_surface']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            right: 12px;
            padding: 0 6px;
            font-size: {FS_SM}px;
            color: {c};
        }}
    """


def _get_status_options() -> list:
    from .order_detail._status_config import get_status_labels
    labels = get_status_labels()
    return [
        ("pending",     labels["pending"][0]),
        ("confirmed",   labels["confirmed"][0]),
        ("in_progress", labels["in_progress"][0]),
        ("ready",       labels["ready"][0]),
    ]


def _get_priority_options() -> list:
    from .order_detail._status_config import get_priority_labels
    labels = get_priority_labels()
    return [(k, v[0]) for k, v in labels.items()]


def _get_type_options() -> list:
    from .order_detail._status_config import get_type_labels
    labels = get_type_labels()
    return list(labels.items())


class _OrderForm(QDialog):
    saved = pyqtSignal(int)

    def __init__(self, conn, order_id: int = None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.order_id   = order_id
        self._customer_id = None
        self._item_rows: list[_ItemRowWidget] = []

        _ItemRowWidget.invalidate_cache()

        self.setWindowTitle(tr("order_edit_title") if order_id else tr("order_new_title"))
        self.setMinimumWidth(880)
        self.setMinimumHeight(760)
        self.setModal(True)
        self._build()
        if order_id:
            self._load()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.setStyleSheet(input_style())

        hdr = QLabel(tr("order_edit_title") if self.order_id else tr("order_new_title"))
        hdr.setStyleSheet(f"""
            font-size: {FS_BASE + 3}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: 8px; padding: 10px 16px;
        """)
        root.addWidget(hdr)

        self._build_customer_section(root)
        self._build_order_details(root)
        self._build_items_section(root)
        self._build_notes_section(root)
        self._build_save_buttons(root)

        self._add_item_row()

    def _build_customer_section(self, root):
        cust_grp = QGroupBox(tr("order_customer_section"))
        cust_grp.setStyleSheet(_group_ss(_C['accent']))
        c_lay = QVBoxLayout(cust_grp)
        c_lay.setSpacing(8)

        search_row = QHBoxLayout()
        self.inp_cust_search = QLineEdit()
        self.inp_cust_search.setPlaceholderText(tr("order_customer_search"))
        self.inp_cust_search.textChanged.connect(self._search_customers)

        btn_new_cust = make_btn(tr("customer_new_btn"), "success")
        btn_new_cust.clicked.connect(self._new_customer)

        search_row.addWidget(self.inp_cust_search, stretch=1)
        search_row.addWidget(btn_new_cust)
        c_lay.addLayout(search_row)

        self.cmb_customer = QComboBox()
        self.cmb_customer.setPlaceholderText(f"─ {tr('select_field').format(label=tr('customer_name'))} ─")
        self._all_customers = fetch_all_customers(self.conn, active_only=True)
        for c in self._all_customers:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or tr('no_data')})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.currentIndexChanged.connect(self._on_customer_changed)
        c_lay.addWidget(self.cmb_customer)

        self._lbl_cust_info = QLabel("")
        self._lbl_cust_info.setStyleSheet(
            f"font-size:{FS_SM}px; color:{_C['text_muted']};"
            f"background:{_C['bg_surface_2']};"
            f"border:1px solid {_C['border']}; border-radius:6px; padding:6px 10px;"
        )
        self._lbl_cust_info.setVisible(False)
        c_lay.addWidget(self._lbl_cust_info)
        root.addWidget(cust_grp)

    def _build_order_details(self, root):
        order_grp = QGroupBox(tr("order_details_section"))
        order_grp.setStyleSheet(_group_ss(_C['accent']))
        form = QFormLayout(order_grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_type = QComboBox()
        for k, v in _get_type_options():
            self.cmb_type.addItem(v, k)
        form.addRow(f"{tr('order_type_label')} :", self.cmb_type)

        self.cmb_status = QComboBox()
        for k, v in _get_status_options():
            self.cmb_status.addItem(v, k)
        if not self.order_id:
            self.cmb_status.setVisible(False)
        form.addRow(f"{tr('order_status_label')} :", self.cmb_status)

        self.cmb_priority = QComboBox()
        for k, v in _get_priority_options():
            self.cmb_priority.addItem(v, k)
        self.cmb_priority.setCurrentIndex(1)
        form.addRow(f"{tr('order_priority_label')} :", self.cmb_priority)

        self.inp_due_date = QDateEdit()
        self.inp_due_date.setCalendarPopup(True)
        self.inp_due_date.setDate(QDate.currentDate().addDays(7))
        self.inp_due_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow(f"{tr('order_due_date_label')} :", self.inp_due_date)

        self.sp_discount = QDoubleSpinBox()
        self.sp_discount.setRange(0, 99_999)
        self.sp_discount.setDecimals(2)
        self.sp_discount.setSuffix(f" {tr('currency_sym')}")
        form.addRow(f"{tr('order_discount_total')} :", self.sp_discount)

        self.sp_paid = QDoubleSpinBox()
        self.sp_paid.setRange(0, 9_999_999)
        self.sp_paid.setDecimals(2)
        self.sp_paid.setSuffix(f" {tr('currency_sym')}")
        form.addRow(f"{tr('order_paid_amount')} :", self.sp_paid)
        root.addWidget(order_grp)

    def _build_items_section(self, root):
        items_grp = QGroupBox(tr("order_items_section"))
        items_grp.setStyleSheet(_group_ss(_C['warning']))
        items_lay = QVBoxLayout(items_grp)
        items_lay.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_add_item = make_btn(tr("order_add_item_btn"), "success")
        btn_add_item.clicked.connect(self._add_item_row)

        lbl_offer = QLabel(tr("order_select_offer_lbl"))
        lbl_offer.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")

        self.cmb_offers = QComboBox()
        self.cmb_offers.setMinimumHeight(34)
        self.cmb_offers.setMinimumWidth(200)
        self._load_offers_combo()

        btn_import_offer = make_btn(tr("order_import_offer_btn"), "ghost")
        btn_import_offer.clicked.connect(self._import_offer)

        toolbar.addWidget(btn_add_item)
        toolbar.addStretch()
        toolbar.addWidget(lbl_offer)
        toolbar.addWidget(self.cmb_offers, stretch=1)
        toolbar.addWidget(btn_import_offer)
        items_lay.addLayout(toolbar)

        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(6)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        items_lay.addWidget(self._rows_container)

        total_bar = QFrame()
        total_bar.setStyleSheet(f"""
            QFrame {{
                background: {_C['accent_light']};
                border: 1px solid {_C['accent_mid']};
                border-radius: 6px;
            }}
        """)
        total_row = QHBoxLayout(total_bar)
        total_row.setContentsMargins(14, 8, 14, 8)

        lbl_items_count = QLabel(tr("order_items_count_lbl"))
        lbl_items_count.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{FS_SM}px; background:transparent;"
        )
        self.lbl_items_count = QLabel("0")
        self.lbl_items_count.setStyleSheet(
            f"font-weight:bold; color:{_C['accent_text']}; background:transparent;"
        )
        lbl_subtotal_txt = QLabel(tr("order_subtotal_lbl"))
        lbl_subtotal_txt.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{FS_SM}px; background:transparent;"
        )
        self.lbl_subtotal = QLabel(f"0.00 {tr('currency_sym')}")
        self.lbl_subtotal.setStyleSheet(
            f"font-weight:bold; color:{_C['accent_text']}; font-size:{FS_BASE + 1}px; background:transparent;"
        )

        total_row.addWidget(lbl_items_count)
        total_row.addWidget(self.lbl_items_count)
        total_row.addStretch()
        total_row.addWidget(lbl_subtotal_txt)
        total_row.addWidget(self.lbl_subtotal)
        items_lay.addWidget(total_bar)
        root.addWidget(items_grp)

    def _build_notes_section(self, root):
        notes_grp = QGroupBox(tr("order_notes_section"))
        notes_grp.setStyleSheet(_group_ss(_C['text_muted']))
        n_lay = QVBoxLayout(notes_grp)
        n_lay.setSpacing(8)

        self.inp_notes = QTextEdit()
        self.inp_notes.setPlaceholderText(tr("order_customer_notes"))
        self.inp_notes.setMaximumHeight(65)
        n_lay.addWidget(QLabel(tr("order_customer_notes")))
        n_lay.addWidget(self.inp_notes)

        self.inp_internal = QTextEdit()
        self.inp_internal.setPlaceholderText(tr("order_internal_notes"))
        self.inp_internal.setMaximumHeight(65)
        n_lay.addWidget(QLabel(tr("order_internal_notes_lbl")))
        n_lay.addWidget(self.inp_internal)
        root.addWidget(notes_grp)

    def _build_save_buttons(self, root):
        btns = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_save = make_btn(tr("order_save_btn"), "primary")
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save, stretch=1)
        root.addLayout(btns)

    def _add_item_row(self, prefill: dict = None) -> _ItemRowWidget:
        row = _ItemRowWidget()
        row.changed.connect(self._update_totals)
        row.removed.connect(self._remove_item_row)
        self._item_rows.append(row)
        self._rows_layout.addWidget(row)
        if prefill:
            row.load_from_order_item(prefill)
        self._update_totals()
        return row

    def _remove_item_row(self, row_widget: _ItemRowWidget):
        if row_widget in self._item_rows:
            self._item_rows.remove(row_widget)
        self._rows_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self._update_totals()

    def _update_totals(self):
        total = sum(r.get_total() for r in self._item_rows)
        valid = sum(1 for r in self._item_rows if r.get_product_name())
        self.lbl_items_count.setText(str(valid))
        self.lbl_subtotal.setText(f"{total:,.2f} {tr('currency_sym')}")

    def _load_offers_combo(self):
        self.cmb_offers.clear()
        self.cmb_offers.addItem(tr("offer_select_label"), None)
        for o in fetch_offers():
            cat = f" [{o['category_name']}]" if o.get("category_name") else ""
            label = f"🎁 {o['name']}  —  {tr('discount')} {o['discount']:.0f}%{cat}"
            self.cmb_offers.addItem(label, o["id"])

    def _import_offer(self):
        oid = self.cmb_offers.currentData()
        if not oid:
            return
        offer_discount = 0.0
        try:
            conn_erp = get_connection("erp")
            o = conn_erp.execute("SELECT discount FROM offers WHERE id=?", (oid,)).fetchone()
            if o:
                offer_discount = float(o["discount"])
        except Exception:
            pass

        lines = fetch_offer_lines(oid)
        if not lines:
            QMessageBox.information(self, tr("info"), tr("no_data"))
            return

        for r in list(self._item_rows):
            if not r.get_product_name():
                self._remove_item_row(r)

        for line in lines:
            row = self._add_item_row()
            pid = line.get("item_id")
            if pid:
                cmb = row.cmb_product
                for i in range(cmb.count()):
                    if cmb.itemData(i) == pid:
                        cmb.blockSignals(True)
                        cmb.setCurrentIndex(i)
                        cmb.blockSignals(False)
                        for p in _ItemRowWidget._get_products():
                            if p["id"] == pid:
                                row._unit_price = p.get("price") or 0.0
                                row.lbl_price.setText(f"{row._unit_price:.2f} {tr('currency_sym')}")
                                break
                        break
            row.sp_qty.setValue(line["qty"])
            row.set_offer_discount(offer_discount)

        self.cmb_offers.setCurrentIndex(0)

    def _search_customers(self, text: str):
        if len(text) < 2:
            return
        results = search_customers(self.conn, text)
        self.cmb_customer.blockSignals(True)
        self.cmb_customer.clear()
        for c in results:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or tr('no_data')})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.blockSignals(False)
        if results:
            self.cmb_customer.setCurrentIndex(0)
            self._on_customer_changed(0)

    def _on_customer_changed(self, idx: int):
        cid = self.cmb_customer.currentData()
        self._customer_id = cid
        if cid:
            from db.orders.customers_repo import fetch_customer
            c = fetch_customer(self.conn, cid)
            if c:
                parts = []
                if c["phone"]:  parts.append(f"📞 {c['phone']}")
                if c["city"]:   parts.append(f"📍 {c['city']}")
                if c["email"]:  parts.append(f"✉️ {c['email']}")
                self._lbl_cust_info.setText("  |  ".join(parts) if parts else "")
                self._lbl_cust_info.setVisible(bool(parts))
        else:
            self._lbl_cust_info.setVisible(False)

    def _new_customer(self):
        from ui.tabs.orders._customer_form import _CustomerForm
        dlg = _CustomerForm(self.conn, parent=self)
        dlg.saved.connect(self._on_customer_created)
        dlg.exec_()

    def _on_customer_created(self, customer_id: int):
        from db.orders.customers_repo import fetch_customer
        c = fetch_customer(self.conn, customer_id)
        if c:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or tr('no_data')})"
            self.cmb_customer.insertItem(0, label, customer_id)
            self.cmb_customer.setCurrentIndex(0)
            self._customer_id = customer_id

    def _load(self):
        d = fetch_order(self.conn, self.order_id)
        if not d:
            return

        for i in range(self.cmb_customer.count()):
            if self.cmb_customer.itemData(i) == d["customer_id"]:
                self.cmb_customer.setCurrentIndex(i)
                break

        for cmb, key in [(self.cmb_type, "order_type"),
                         (self.cmb_priority, "priority"),
                         (self.cmb_status, "status")]:
            for i in range(cmb.count()):
                if cmb.itemData(i) == d[key]:
                    cmb.setCurrentIndex(i)
                    break

        if d["due_date"]:
            self.inp_due_date.setDate(QDate.fromString(d["due_date"], "yyyy-MM-dd"))
        self.sp_discount.setValue(d["discount"] or 0)
        self.sp_paid.setValue(d["paid_amount"] or 0)
        self.inp_notes.setPlainText(d["notes"] or "")
        self.inp_internal.setPlainText(d["internal_notes"] or "")

        for r in list(self._item_rows):
            self._remove_item_row(r)

        items = fetch_order_items(self.conn, self.order_id)
        for item in items:
            self._add_item_row(prefill=dict(item))

    def _save(self):
        if not self._customer_id:
            QMessageBox.warning(self, tr("warning"), tr("order_no_customer_warn"))
            return

        valid_rows = [r for r in self._item_rows if r.get_product_name()]
        if not valid_rows:
            QMessageBox.warning(self, tr("warning"), tr("order_no_items_warn"))
            return

        priority   = self.cmb_priority.currentData()
        order_type = self.cmb_type.currentData()
        due_date   = self.inp_due_date.date().toString("yyyy-MM-dd")
        discount   = self.sp_discount.value()
        paid       = self.sp_paid.value()
        notes      = self.inp_notes.toPlainText().strip()
        internal   = self.inp_internal.toPlainText().strip()

        if self.order_id:
            update_order(self.conn, self.order_id, priority=priority,
                         due_date=due_date, discount=discount,
                         paid_amount=paid, notes=notes, internal_notes=internal)
            existing = fetch_order_items(self.conn, self.order_id)
            for eid in {i["id"] for i in existing}:
                delete_order_item(self.conn, eid)
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(self.conn, self.order_id,
                                  item_name=d["item_name"], description=d["description"],
                                  quantity=d["quantity"], unit=d["unit"],
                                  unit_price=d["unit_price"], discount_pct=d["discount_pct"],
                                  design_ref=d["design_ref"], notes=d["notes"], sort_order=idx)
            self.saved.emit(self.order_id)
        else:
            oid = insert_order(self.conn, customer_id=self._customer_id,
                               order_type=order_type, priority=priority,
                               due_date=due_date, discount=discount,
                               paid_amount=paid, notes=notes, internal_notes=internal)
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(self.conn, oid,
                                  item_name=d["item_name"], description=d["description"],
                                  quantity=d["quantity"], unit=d["unit"],
                                  unit_price=d["unit_price"], discount_pct=d["discount_pct"],
                                  design_ref=d["design_ref"], notes=d["notes"], sort_order=idx)
            self.saved.emit(oid)

        self.accept()
```

---

### `ui/tabs/orders/order_form/_item_row_widget.py`

**المشاكل:** hardcoded text وألوان، استيراد `_C` من مكان خاطئ.

```python
"""
ui/tabs/orders/order_form/_item_row_widget.py
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QDoubleSpinBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QBrush

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM, FS_BASE
from ._products_fetcher import fetch_priced_products


class _ItemRowWidget(QFrame):
    changed = pyqtSignal()
    removed = pyqtSignal(object)

    _products_cache: list = None

    @classmethod
    def _get_products(cls) -> list:
        if cls._products_cache is None:
            cls._products_cache = fetch_priced_products()
        return cls._products_cache

    @classmethod
    def invalidate_cache(cls):
        cls._products_cache = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db_item_id   = None
        self._unit_price   = 0.0
        self._discount_pct = 0.0
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 8px;
            }}
            QFrame:hover {{ border-color: {_C['accent_mid']}; }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(5)

        # صف 1
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("order_item_search"))
        self.inp_search.setFixedWidth(100)
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['accent_light']}; border: 1px solid {_C['accent_mid']};
                border-radius: 5px; padding: 2px 8px; font-size: {FS_SM}px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """)
        self.inp_search.textChanged.connect(self._on_search)

        self.btn_clr = QPushButton("✖")
        self.btn_clr.setFixedSize(22, 22)
        self.btn_clr.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{_C['text_muted']};font-size:{FS_SM - 1}px;}}"
            f"QPushButton:hover{{color:{_C['danger']};}}"
        )
        self.btn_clr.clicked.connect(lambda: self.inp_search.clear())
        self.btn_clr.setVisible(False)
        self.inp_search.textChanged.connect(lambda t: self.btn_clr.setVisible(bool(t)))

        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumHeight(30)
        self.cmb_product.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_product.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 2px 8px; font-size: {FS_BASE}px;
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
        """)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        row1.addWidget(self.inp_search)
        row1.addWidget(self.btn_clr)
        row1.addWidget(self.cmb_product, stretch=1)
        root.addLayout(row1)

        # صف 2
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_price_t = QLabel(tr("item_unit_price"))
        lbl_price_t.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.lbl_price = QLabel("─")
        self.lbl_price.setMinimumWidth(85)
        self.lbl_price.setAlignment(Qt.AlignCenter)
        self.lbl_price.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['success']};"
            f"background:{_C['success_bg']}; border:1px solid {_C['success_border']};"
            "border-radius:5px; padding:3px 8px;"
        )

        lbl_disc_t = QLabel(tr("item_discount_lbl"))
        lbl_disc_t.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.lbl_disc = QLabel("─")
        self.lbl_disc.setMinimumWidth(60)
        self.lbl_disc.setAlignment(Qt.AlignCenter)
        self.lbl_disc.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['warning']};"
            f"background:{_C['warning_bg']}; border:1px solid {_C['warning_border']};"
            "border-radius:5px; padding:3px 8px;"
        )

        lbl_qty = QLabel(tr("item_qty_lbl"))
        lbl_qty.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.sp_qty = QDoubleSpinBox()
        self.sp_qty.setRange(0.001, 99_999)
        self.sp_qty.setDecimals(3)
        self.sp_qty.setValue(1)
        self.sp_qty.setMinimumHeight(30)
        self.sp_qty.setFixedWidth(90)
        self.sp_qty.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {_C['bg_surface']}; border: 2px solid {_C['accent']};
                border-radius: 5px; padding: 2px 6px;
                font-size:{FS_BASE}px; font-weight:bold; color:{_C['accent']};
            }}
        """)
        self.sp_qty.valueChanged.connect(self._recalc)

        self.inp_unit = QLineEdit(tr("order_unit_default"))
        self.inp_unit.setFixedWidth(55)
        self.inp_unit.setMinimumHeight(30)
        self.inp_unit.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 2px 5px; font-size: {FS_SM}px;
            }}
        """)

        self.lbl_total = QLabel(f"0.00 {tr('currency_sym')}")
        self.lbl_total.setMinimumWidth(95)
        self.lbl_total.setAlignment(Qt.AlignCenter)
        self.lbl_total.setStyleSheet(
            f"font-size:{FS_BASE + 1}px; font-weight:bold; color:{_C['accent']};"
            f"background:{_C['accent_light']}; border:1px solid {_C['accent_mid']};"
            "border-radius:5px; padding:3px 10px;"
        )

        lbl_note = QLabel(tr("item_notes_lbl"))
        lbl_note.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("...")
        self.inp_notes.setMinimumHeight(30)
        self.inp_notes.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 2px 8px; font-size: {FS_SM}px;
            }}
        """)

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(30, 30)
        btn_del.setStyleSheet(f"""
            QPushButton{{background:{_C['danger_bg']};border:1px solid {_C['danger_border']};
            border-radius:5px;font-size:{FS_BASE}px;}}
            QPushButton:hover{{background:{_C['danger_hover_bg']};}}
        """)
        btn_del.clicked.connect(lambda: self.removed.emit(self))

        row2.addWidget(lbl_price_t)
        row2.addWidget(self.lbl_price)
        row2.addWidget(lbl_disc_t)
        row2.addWidget(self.lbl_disc)
        row2.addWidget(lbl_qty)
        row2.addWidget(self.sp_qty)
        row2.addWidget(self.inp_unit)
        row2.addWidget(self.lbl_total)
        row2.addWidget(lbl_note)
        row2.addWidget(self.inp_notes, stretch=1)
        row2.addWidget(btn_del)
        root.addLayout(row2)

        self._populate_combo()

    def _populate_combo(self, filter_text: str = ""):
        prev = self.cmb_product.currentData()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        self.cmb_product.addItem(f"— {tr('order_select_product')} —", None)

        products = self._get_products()
        q = filter_text.strip().lower()
        current_cat = None

        for p in products:
            name = p["name"]
            if q and q not in name.lower():
                continue
            cat  = p.get("category_name") or tr("no_category")
            icon = "🏭" if p["type"] == "final" else "🔧"

            if cat != current_cat:
                current_cat = cat
                sep_idx = self.cmb_product.count()
                self.cmb_product.addItem(f"── {cat} ──", f"__cat__{cat}")
                model = self.cmb_product.model()
                item  = model.item(sep_idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
                    from PyQt5.QtGui import QFont as QF
                    f = QF(); f.setBold(True); f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                    item.setForeground(QBrush(QColor(_C['text_separator'])))

            self.cmb_product.addItem(f"  {icon} {name}", p["id"])

        self.cmb_product.blockSignals(False)

        if prev and not isinstance(prev, str):
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev:
                    self.cmb_product.setCurrentIndex(i)
                    return
        self.cmb_product.setCurrentIndex(0)
        self._on_product_changed()

    def _on_search(self, text: str):
        self._populate_combo(filter_text=text)

    def _on_product_changed(self):
        pid = self.cmb_product.currentData()
        if not pid or isinstance(pid, str):
            self._unit_price   = 0.0
            self._discount_pct = 0.0
            self.lbl_price.setText("─")
            self.lbl_disc.setText("─")
            self.lbl_total.setText(f"0.00 {tr('currency_sym')}")
            self.changed.emit()
            return

        for p in self._get_products():
            if p["id"] == pid:
                self._unit_price = p.get("price") or 0.0
                break

        self.lbl_price.setText(f"{self._unit_price:.2f} {tr('currency_sym')}")
        self.lbl_disc.setText(f"{self._discount_pct:.1f} %")
        self._recalc()

    def _recalc(self):
        qty   = self.sp_qty.value()
        total = qty * self._unit_price * (1 - self._discount_pct / 100)
        self.lbl_total.setText(f"{total:,.2f} {tr('currency_sym')}")
        self.changed.emit()

    def set_offer_discount(self, discount_pct: float):
        self._discount_pct = discount_pct
        self.lbl_disc.setText(f"{discount_pct:.1f} %")
        self._recalc()

    def get_product_id(self):
        pid = self.cmb_product.currentData()
        if not pid or isinstance(pid, str):
            return None
        return pid

    def get_product_name(self) -> str:
        pid = self.get_product_id()
        if pid:
            for p in self._get_products():
                if p["id"] == pid:
                    return p["name"]
        return ""

    def get_data(self) -> dict:
        name = self.get_product_name()
        if not name:
            return None
        return {
            "item_name":    name,
            "description":  "",
            "quantity":     self.sp_qty.value(),
            "unit":         self.inp_unit.text().strip() or tr("order_unit_default"),
            "unit_price":   self._unit_price,
            "discount_pct": self._discount_pct,
            "design_ref":   "",
            "notes":        self.inp_notes.text().strip(),
        }

    def get_total(self) -> float:
        return self.sp_qty.value() * self._unit_price * (1 - self._discount_pct / 100)

    def load_from_order_item(self, item: dict):
        self._db_item_id   = item["id"]
        self._unit_price   = item["unit_price"]
        self._discount_pct = item["discount_pct"]

        name = item["item_name"]
        for p in self._get_products():
            if p["name"] == name:
                for i in range(self.cmb_product.count()):
                    if self.cmb_product.itemData(i) == p["id"]:
                        self.cmb_product.blockSignals(True)
                        self.cmb_product.setCurrentIndex(i)
                        self.cmb_product.blockSignals(False)
                        break
                break

        self.lbl_price.setText(f"{self._unit_price:.2f} {tr('currency_sym')}")
        self.lbl_disc.setText(f"{self._discount_pct:.1f} %")
        self.sp_qty.setValue(item["quantity"])
        self.inp_unit.setText(item["unit"] or tr("order_unit_default"))
        self.inp_notes.setText(item["notes"] or "")
        self._recalc()

    @property
    def db_item_id(self):
        return self._db_item_id
```

---

### `ui/tabs/orders/order_form/_products_fetcher.py`

**المشاكل:** `get_costing_connection` محذوفة — يُستبدل بـ `get_connection("erp")`.

```python
"""
ui/tabs/orders/order_form/_products_fetcher.py
"""


def fetch_priced_products() -> list:
    try:
        from db.shared.connection import get_connection
        conn = get_connection("erp")
        rows = conn.execute("""
            SELECT
                i.id, i.name, i.type, i.category_id,
                c.name  AS category_name,
                c.color AS category_color,
                p.price
            FROM   items i
            JOIN   pricing p ON p.item_id = i.id
            LEFT JOIN categories c ON c.id = i.category_id
            WHERE  i.type IN ('final', 'semi')
            ORDER  BY COALESCE(c.name, 'ω') ASC, i.name ASC
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def fetch_offers() -> list:
    try:
        from db.shared.connection import get_connection
        conn = get_connection("erp")
        rows = conn.execute("""
            SELECT o.id, o.name, o.discount, c.name AS category_name
            FROM   offers o
            LEFT JOIN categories c ON c.id = o.category_id
            ORDER  BY o.name
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def fetch_offer_lines(offer_id: int) -> list:
    try:
        from db.shared.connection import get_connection
        conn = get_connection("erp")
        rows = conn.execute("""
            SELECT oi.item_id, oi.qty, i.name AS item_name, p.price
            FROM   offer_items oi
            JOIN   items i  ON i.id = oi.item_id
            LEFT JOIN pricing p ON p.item_id = oi.item_id
            WHERE  oi.offer_id = ?
        """, (offer_id,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
```

---

### `ui/tabs/orders/_item_form.py`

**المشاكل:** hardcoded text وألوان، استيرادات خاطئة.

```python
"""
ui/tabs/orders/_item_form.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_order_items, insert_order_item, update_order_item
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_BASE, FS_SM


def _spin(min_=0, max_=9999999, dec=2, suffix=""):
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(34)
    if suffix:
        s.setSuffix(f" {suffix}")
    return s


class _ItemForm(QDialog):
    def __init__(self, conn, order_id: int, item_id: int = None, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.order_id = order_id
        self.item_id  = item_id

        self.setWindowTitle(tr("item_edit_title") if item_id else tr("item_add_title"))
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setStyleSheet(input_style())
        self._build()
        if item_id:
            self._load()

        self.sp_qty.valueChanged.connect(self._update_total)
        self.sp_price.valueChanged.connect(self._update_total)
        self.sp_discount.valueChanged.connect(self._update_total)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        hdr = QLabel(tr("item_add_title") if not self.item_id else tr("item_edit_title"))
        hdr.setStyleSheet(f"""
            font-size: {FS_BASE + 1}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: 8px; padding: 8px 14px;
        """)
        root.addWidget(hdr)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("product_name_placeholder"))
        form.addRow(tr("item_name_lbl"), self.inp_name)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText(tr("description"))
        form.addRow(tr("item_desc_lbl"), self.inp_desc)

        self.sp_qty = _spin(min_=0.001, max_=99999, dec=3)
        self.sp_qty.setValue(1)
        form.addRow(tr("item_qty_lbl"), self.sp_qty)

        self.inp_unit = QLineEdit()
        self.inp_unit.setText(tr("order_unit_default"))
        self.inp_unit.setPlaceholderText(tr("order_unit_default"))
        form.addRow(tr("order_unit_label"), self.inp_unit)

        self.sp_price = _spin(max_=9999999, dec=2, suffix=tr("currency_sym"))
        form.addRow(tr("item_unit_price"), self.sp_price)

        self.sp_discount = _spin(max_=100, dec=2, suffix="%")
        form.addRow(tr("item_discount_lbl"), self.sp_discount)

        self.lbl_total = QLabel(f"0.00 {tr('currency_sym')}")
        self.lbl_total.setStyleSheet(f"""
            font-size: {FS_BASE + 2}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border: 1px solid {_C['accent_mid']};
            border-radius: 6px; padding: 6px 12px;
        """)
        form.addRow(tr("item_total_lbl"), self.lbl_total)

        self.inp_design_ref = QLineEdit()
        self.inp_design_ref.setPlaceholderText(tr("item_design_ref_lbl"))
        form.addRow(tr("item_design_ref_lbl"), self.inp_design_ref)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes"))
        form.addRow(tr("item_notes_lbl"), self.inp_notes)

        root.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_save = make_btn(tr("item_save_btn"), "primary")
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save, stretch=1)
        root.addLayout(btn_row)

    def _update_total(self):
        qty      = self.sp_qty.value()
        price    = self.sp_price.value()
        discount = self.sp_discount.value()
        total    = qty * price * (1 - discount / 100)
        self.lbl_total.setText(f"{total:,.2f} {tr('currency_sym')}")

    def _load(self):
        items = fetch_order_items(self.conn, self.order_id)
        item  = next((i for i in items if i["id"] == self.item_id), None)
        if not item:
            return
        self.inp_name.setText(item["item_name"])
        self.inp_desc.setText(item["description"] or "")
        self.sp_qty.setValue(item["quantity"])
        self.inp_unit.setText(item["unit"])
        self.sp_price.setValue(item["unit_price"])
        self.sp_discount.setValue(item["discount_pct"])
        self.inp_design_ref.setText(item["design_ref"] or "")
        self.inp_notes.setText(item["notes"] or "")
        self._update_total()

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("item_name_warn"))
            self.inp_name.setFocus()
            return

        qty      = self.sp_qty.value()
        unit     = self.inp_unit.text().strip() or tr("order_unit_default")
        price    = self.sp_price.value()
        discount = self.sp_discount.value()
        desc     = self.inp_desc.text().strip()
        ref      = self.inp_design_ref.text().strip()
        notes    = self.inp_notes.text().strip()

        if self.item_id:
            update_order_item(
                self.conn, self.item_id,
                item_name=name, description=desc,
                quantity=qty, unit=unit,
                unit_price=price, discount_pct=discount,
                design_ref=ref, notes=notes,
            )
        else:
            insert_order_item(
                self.conn, self.order_id,
                item_name=name, description=desc,
                quantity=qty, unit=unit,
                unit_price=price, discount_pct=discount,
                design_ref=ref, notes=notes,
            )
        self.accept()
```

---

### `ui/tabs/orders/_customer_form.py`

**المشاكل:** hardcoded text وألوان، استيرادات خاطئة.

```python
"""
ui/tabs/orders/_customer_form.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.customers_repo import (
    fetch_customer, insert_customer, update_customer,
    fetch_contacts, insert_contact, update_contact, delete_contact,
)
from ui.widgets.tables.tables import make_compact_table, make_item, insert_row, ROW_HEIGHT_COMPACT
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_BASE, FS_SM


def _group_ss() -> str:
    return f"""
        QGroupBox {{
            font-weight: bold;
            color: {_C['text_sec']};
            border: 1px solid {_C['border']};
            border-radius: 8px;
            margin-top: 8px;
            padding-top: 8px;
            background: {_C['bg_surface']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            right: 12px; padding: 0 4px;
            font-size: {FS_SM}px;
            color: {_C['accent']};
        }}
    """


class _CustomerForm(QDialog):
    saved = pyqtSignal(int)

    def __init__(self, conn, customer_id: int = None, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.customer_id = customer_id
        self._contacts   = []

        self.setWindowTitle(tr("customer_edit_title") if customer_id else tr("customer_new_title"))
        self.setMinimumWidth(580)
        self.setMinimumHeight(620)
        self.setModal(True)
        self._build()
        if customer_id:
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        hdr = QLabel(tr("customer_edit_title") if self.customer_id else tr("customer_new_title"))
        hdr.setStyleSheet(f"""
            font-size: {FS_BASE + 2}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: 8px; padding: 8px 14px;
        """)
        root.addWidget(hdr)
        self.setStyleSheet(input_style())

        basic_grp = QGroupBox(tr("customer_basic_section"))
        basic_grp.setStyleSheet(_group_ss())
        form = QFormLayout(basic_grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("customer_name_lbl"))
        form.addRow(tr("customer_name_lbl"), self.inp_name)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem(tr("customer_type_individual"), "individual")
        self.cmb_type.addItem(tr("customer_type_company"),    "company")
        form.addRow(tr("customer_type_lbl"), self.cmb_type)

        self.inp_phone = QLineEdit()
        form.addRow(tr("customer_phone_lbl"), self.inp_phone)

        self.inp_phone2 = QLineEdit()
        form.addRow(tr("customer_phone2_lbl"), self.inp_phone2)

        self.inp_email = QLineEdit()
        form.addRow(tr("customer_email_lbl"), self.inp_email)

        self.inp_city = QLineEdit()
        form.addRow(tr("customer_city_lbl"), self.inp_city)

        self.inp_address = QLineEdit()
        form.addRow(tr("customer_address_lbl"), self.inp_address)

        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(70)
        form.addRow(tr("customer_notes_lbl"), self.inp_notes)

        root.addWidget(basic_grp)

        contacts_grp = QGroupBox(tr("customer_contacts_section"))
        contacts_grp.setStyleSheet(_group_ss())
        c_lay = QVBoxLayout(contacts_grp)
        c_lay.setSpacing(8)

        self.contacts_table = make_compact_table(
            columns=[
                tr("contact_name_lbl"), tr("contact_role_lbl"),
                tr("contact_phone_lbl"), tr("contact_email_lbl"), tr("contact_notes_lbl"),
            ],
            stretch_col=0,
            col_widths={1: 80, 2: 100, 3: 120, 4: 120},
            max_height=150,
        )
        c_lay.addWidget(self.contacts_table)

        c_btn_row = QHBoxLayout()
        btn_add_c = make_btn(tr("contact_add_btn"), "success")
        btn_add_c.clicked.connect(self._add_contact_dialog)
        btn_del_c = make_btn(tr("contact_del_btn"), "danger")
        btn_del_c.clicked.connect(self._del_contact)
        c_btn_row.addWidget(btn_add_c)
        c_btn_row.addWidget(btn_del_c)
        c_btn_row.addStretch()
        c_lay.addLayout(c_btn_row)
        root.addWidget(contacts_grp)

        btn_row = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_save = make_btn(tr("customer_save_btn"), "primary")
        btn_save.setMinimumHeight(38)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save, stretch=1)
        root.addLayout(btn_row)

    def _load(self):
        c = fetch_customer(self.conn, self.customer_id)
        if not c:
            return
        self.inp_name.setText(c["name"])
        self.inp_phone.setText(c["phone"] or "")
        self.inp_phone2.setText(c["phone2"] or "")
        self.inp_email.setText(c["email"] or "")
        self.inp_city.setText(c["city"] or "")
        self.inp_address.setText(c["address"] or "")
        self.inp_notes.setPlainText(c["notes"] or "")
        for i in range(self.cmb_type.count()):
            if self.cmb_type.itemData(i) == c["customer_type"]:
                self.cmb_type.setCurrentIndex(i)
                break
        self._contacts = list(fetch_contacts(self.conn, self.customer_id))
        self._refresh_contacts_table()

    def _refresh_contacts_table(self):
        self.contacts_table.setRowCount(0)
        for ct in self._contacts:
            r = insert_row(self.contacts_table, ROW_HEIGHT_COMPACT)
            cid   = ct.get("id")   if isinstance(ct, dict) else ct["id"]
            name  = ct.get("name", "")  if isinstance(ct, dict) else ct["name"]
            role  = ct.get("role",  "") or ""
            phone = ct.get("phone", "") or ""
            email = ct.get("email", "") or ""
            notes = ct.get("notes", "") or ""
            self.contacts_table.setItem(r, 0, make_item(name, user_data=cid))
            self.contacts_table.setItem(r, 1, make_item(role))
            self.contacts_table.setItem(r, 2, make_item(phone))
            self.contacts_table.setItem(r, 3, make_item(email))
            self.contacts_table.setItem(r, 4, make_item(notes))

    def _add_contact_dialog(self):
        dlg = _ContactDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._contacts.append(dlg.get_data())
            self._refresh_contacts_table()

    def _del_contact(self):
        row = self.contacts_table.currentRow()
        if row < 0:
            return
        self._contacts.pop(row)
        self._refresh_contacts_table()

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("customer_name_warn"))
            self.inp_name.setFocus()
            return

        ctype   = self.cmb_type.currentData()
        phone   = self.inp_phone.text().strip()
        phone2  = self.inp_phone2.text().strip()
        email   = self.inp_email.text().strip()
        city    = self.inp_city.text().strip()
        address = self.inp_address.text().strip()
        notes   = self.inp_notes.toPlainText().strip()

        if self.customer_id:
            update_customer(self.conn, self.customer_id, name=name, customer_type=ctype,
                            phone=phone, phone2=phone2, email=email,
                            address=address, city=city, notes=notes)
            cid = self.customer_id
        else:
            cid = insert_customer(self.conn, name=name, customer_type=ctype,
                                  phone=phone, phone2=phone2, email=email,
                                  address=address, city=city, notes=notes)

        for ct in self._contacts:
            if not ct.get("id"):
                insert_contact(self.conn, cid, name=ct.get("name", ""),
                               role=ct.get("role", ""), phone=ct.get("phone", ""),
                               email=ct.get("email", ""), notes=ct.get("notes", ""))

        self.saved.emit(cid)
        self.accept()


class _ContactDialog(QDialog):
    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("contact_title"))
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build()
        if data:
            self._load(data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)
        self.setStyleSheet(input_style())

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name  = QLineEdit(); form.addRow(tr("contact_name_lbl"),  self.inp_name)
        self.inp_role  = QLineEdit(); form.addRow(tr("contact_role_lbl"),  self.inp_role)
        self.inp_phone = QLineEdit(); form.addRow(tr("contact_phone_lbl"), self.inp_phone)
        self.inp_email = QLineEdit(); form.addRow(tr("contact_email_lbl"), self.inp_email)
        self.inp_notes = QLineEdit(); form.addRow(tr("contact_notes_lbl"), self.inp_notes)
        root.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = make_btn(tr("contact_ok_btn"), "primary")
        btn_ok.clicked.connect(self._ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok, stretch=1)
        root.addLayout(btn_row)

    def _load(self, data: dict):
        self.inp_name.setText(data.get("name", ""))
        self.inp_role.setText(data.get("role", ""))
        self.inp_phone.setText(data.get("phone", ""))
        self.inp_email.setText(data.get("email", ""))
        self.inp_notes.setText(data.get("notes", ""))

    def _ok(self):
        if not self.inp_name.text().strip():
            QMessageBox.warning(self, tr("warning"), tr("contact_name_warn"))
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "id":    None,
            "name":  self.inp_name.text().strip(),
            "role":  self.inp_role.text().strip(),
            "phone": self.inp_phone.text().strip(),
            "email": self.inp_email.text().strip(),
            "notes": self.inp_notes.text().strip(),
        }
```

---

### `ui/tabs/orders/customers/customers_list_panel.py`

**المشاكل:** hardcoded text وألوان، استيرادات خاطئة.

```python
"""
ui/tabs/orders/customers/customers_list_panel.py
"""
from PyQt5.QtWidgets import (
    QHBoxLayout, QComboBox, QPushButton, QSizePolicy, QLineEdit, QVBoxLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.customers_repo import fetch_all_customers
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.tables import make_item, colored_item, bold_item, muted_item
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_BASE, FS_SM


def _combo_ss() -> str:
    return f"""
        QComboBox {{
            background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
            border-radius: 5px; padding: 0 8px; min-height: 28px;
            font-size: {FS_SM}px; color: {_C['text_primary']};
        }}
        QComboBox:focus {{ border-color: {_C['accent']}; }}
        QComboBox::drop-down {{ border: none; width: 16px; }}
    """


class CustomersListPanel(BaseListPanel):
    customer_selected = pyqtSignal(int)
    new_customer      = pyqtSignal()

    COLUMNS     = []   # تُبنى في __init__
    STRETCH_COL = -1
    COL_WIDTHS  = {0: 80, 1: 160, 2: 110, 3: 80, 4: 55}
    MIN_W       = 280
    MAX_W       = 560
    EMPTY_ICON  = "👥"
    EMPTY_TITLE = "no_customers"   # مفتاح tr

    def __init__(self, conn, parent=None):
        self.COLUMNS = [
            tr("customer_col_code"), tr("customer_col_name"),
            tr("customer_col_phone"), tr("customer_col_city"),
            tr("customer_col_orders"),
        ]
        self._type_filter   = None
        self._active_filter = None
        super().__init__(conn=conn, parent=parent)
        self.item_selected.connect(self.customer_selected.emit)

    def _build_toolbar(self, lay: QVBoxLayout):
        row1 = QHBoxLayout()

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("order_customer_search"))
        self.inp_search.setFixedHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']}; border: 1px solid {_C['border_med']};
                border-radius: 6px; padding: 0 10px; font-size: {FS_BASE}px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton(tr("customer_new_btn"))
        btn_new.setFixedHeight(34)
        btn_new.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: white;
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: {FS_BASE}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        btn_new.clicked.connect(self.new_customer.emit)

        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(btn_new)
        lay.addLayout(row1)

        row2 = QHBoxLayout()

        self.cmb_type = QComboBox()
        self.cmb_type.setFixedHeight(28)
        self.cmb_type.addItem(tr("filter_all"), None)
        self.cmb_type.addItem(tr("customer_type_individual"), "individual")
        self.cmb_type.addItem(tr("customer_type_company"),    "company")
        self.cmb_type.setStyleSheet(_combo_ss())
        self.cmb_type.currentIndexChanged.connect(self._on_combo_changed)

        self.cmb_active = QComboBox()
        self.cmb_active.setFixedHeight(28)
        self.cmb_active.addItem(tr("all"), None)
        self.cmb_active.addItem(tr("status_confirmed"), 1)    # نشط
        self.cmb_active.addItem(tr("status_cancelled"),  0)   # غير نشط
        self.cmb_active.setStyleSheet(_combo_ss())
        self.cmb_active.currentIndexChanged.connect(self._on_combo_changed)

        row2.addWidget(self.cmb_type,   stretch=1)
        row2.addWidget(self.cmb_active, stretch=1)
        lay.addLayout(row2)

    def _on_combo_changed(self):
        self._type_filter   = self.cmb_type.currentData()
        self._active_filter = self.cmb_active.currentData()
        self._apply_filter()

    def _load_rows(self) -> list:
        return fetch_all_customers(self.conn)

    def _match_filter(self, row, q: str) -> bool:
        typ    = getattr(self, '_type_filter',   None)
        active = getattr(self, '_active_filter', None)
        if typ    is not None and row["customer_type"] != typ:    return False
        if active is not None and row["is_active"]     != active: return False
        if q and q not in (row["name"]  or "").lower() \
              and q not in (row["phone"] or "").lower() \
              and q not in (row["code"]  or "").lower():
            return False
        return True

    def _fill_row(self, table, r, row):
        code_item = make_item(row["code"] or "", user_data=row["id"], tooltip=row["code"] or "")
        from ui.widgets.tables.tables import muted_item
        table.setItem(r, 0, muted_item(code_item))

        name_item = make_item(row["name"], tooltip=row["name"])
        if not row["is_active"]:
            from PyQt5.QtGui import QColor
            name_item.setForeground(QColor(_C['text_disabled']))
        else:
            bold_item(name_item)
        table.setItem(r, 1, name_item)

        table.setItem(r, 2, muted_item(make_item(row["phone"] or "—", tooltip=row["phone"] or "")))
        table.setItem(r, 3, muted_item(make_item(row["city"]  or "—", tooltip=row["city"]  or "")))

        cnt_item = make_item(str(row["orders_count"] or 0), align=Qt.AlignCenter)
        from PyQt5.QtGui import QColor
        cnt_item.setForeground(QColor(_C['accent']))
        table.setItem(r, 4, cnt_item)

    def select_customer(self, cid: int):
        self.select_item(cid)
```

---

### `ui/tabs/orders/customers/customer_detail_panel.py`

**المشاكل:** hardcoded text وألوان، استيرادات خاطئة، `make_splitter_table_guarded` غير موجودة.

```python
"""
ui/tabs/orders/customers/customer_detail_panel.py
"""
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout
from PyQt5.QtCore    import Qt, pyqtSignal

from db.orders.customers_repo import (
    fetch_customer, delete_customer, toggle_customer_active,
    fetch_customer_stats, fetch_contacts,
)
from db.orders.orders_repo import fetch_customer_orders

from ui.tabs.orders._customer_form import _CustomerForm
from ui.widgets.base.detail_panel import BaseDetailPanel
from ui.widgets.tables.tables import (
    make_table, make_compact_table, insert_row, auto_fit_columns,
    make_item, bold_item, colored_item, muted_item,
    ROW_HEIGHT_COMPACT,
)
from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.components.button import make_btn
from ui.widgets.core.i18n import tr
from ui.theme import _C

from ..order_detail._status_config import get_status_labels, get_priority_labels


class CustomerDetailPanel(BaseDetailPanel):
    edited  = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     = "👤"
    EMPTY_TITLE    = "customer_select_first"
    EMPTY_SUBTITLE = "customer_select_subtitle"

    def __init__(self, conn, parent=None):
        super().__init__(conn=conn, parent=parent)

    def _build_header_cards(self):
        self._card_total_orders  = self._hdr.add_stat_card("📋", tr("customer_total_orders"),  color=_C['accent'])
        self._card_active_orders = self._hdr.add_stat_card("🔧", tr("customer_active_orders"), color=_C['purple'])
        self._card_total_value   = self._hdr.add_stat_card("💰", tr("customer_total_value"),   color=_C['success'])
        self._card_balance       = self._hdr.add_stat_card("⚖️", tr("customer_balance"),        color=_C['danger'])

    def _build_header_buttons(self):
        self.btn_edit   = self._hdr.toolbar.add_action(tr("order_edit_btn"),          "primary")
        self.btn_toggle = self._hdr.toolbar.add_action(tr("customer_toggle_inactive"), "ghost")
        self.btn_del    = self._hdr.toolbar.add_danger(tr("order_delete_btn"))
        self.btn_edit.clicked.connect(self._edit)
        self.btn_toggle.clicked.connect(self._toggle_active)
        self.btn_del.clicked.connect(self._delete)

    def _build_content(self, lay: QVBoxLayout):
        self._contacts_hdr = SectionHeader(tr("customer_contacts_title"))
        lay.addWidget(self._contacts_hdr)

        self.contacts_table = make_compact_table(
            columns=[
                tr("contact_name_lbl"), tr("contact_role_lbl"),
                tr("contact_phone_lbl"), tr("contact_email_lbl"),
            ],
            stretch_col=0,
            col_widths={1: 80, 2: 100, 3: 120},
            max_height=140,
        )
        lay.addWidget(self.contacts_table)

        self._orders_hdr = SectionHeader(tr("customer_orders_title"))
        lay.addWidget(self._orders_hdr)

        self.orders_table = make_table(
            columns=[
                tr("order_col_number"), tr("order_col_status"),
                tr("order_col_priority"), tr("order_header_total"), tr("order_date"),
            ],
            stretch_col=0,
            col_widths={1: 90, 2: 70, 3: 80, 4: 90},
        )
        self.orders_table.setMaximumHeight(220)
        lay.addWidget(self.orders_table)

    def _load_data(self, item_id: int):
        return fetch_customer(self.conn, item_id)

    def _fill_data(self, data: dict):
        c = data
        type_map = {
            "individual": tr("customer_type_individual"),
            "company":    f"🏢 {tr('customer_type_company')}",
        }
        self._hdr.set_title(c["name"])
        self._hdr.set_type_badge(type_map.get(c["customer_type"], ""))
        self._hdr.set_status_badge(
            c["code"] or "", text_color=_C['text_muted'],
            bg="transparent", border="transparent")

        parts = []
        if c.get("phone"):  parts.append(f"📞 {c['phone']}")
        if c.get("city"):   parts.append(f"📍 {c['city']}")
        if c.get("email"):  parts.append(f"✉️ {c['email']}")
        self._hdr.set_info(parts)

        stats = fetch_customer_stats(self.conn, self._item_id)
        self._card_total_orders.set_value(str(stats.get("total_orders") or 0))
        self._card_active_orders.set_value(str(stats.get("active") or 0))
        self._card_total_value.set_value(f"{(stats.get('total_value') or 0):,.0f} {tr('currency_sym')}")
        balance = (stats.get("total_value") or 0) - (stats.get("total_paid") or 0)
        self._card_balance.set_value(f"{balance:,.0f} {tr('currency_sym')}")
        self._card_balance.set_color(_C['danger'] if balance > 0 else _C['success'])

        self.btn_toggle.setText(
            tr("customer_toggle_active") if not c["is_active"] else tr("customer_toggle_inactive")
        )

        contacts = [dict(ct) for ct in fetch_contacts(self.conn, self._item_id)]
        self.contacts_table.setRowCount(0)
        for ct in contacts:
            r = insert_row(self.contacts_table, ROW_HEIGHT_COMPACT)
            self.contacts_table.setItem(r, 0, bold_item(make_item(ct["name"])))
            self.contacts_table.setItem(r, 1, muted_item(make_item(ct.get("role") or "")))
            self.contacts_table.setItem(r, 2, make_item(ct.get("phone") or ""))
            self.contacts_table.setItem(r, 3, muted_item(make_item(ct.get("email") or "")))

        self._contacts_hdr.setVisible(bool(contacts))
        self.contacts_table.setVisible(bool(contacts))

        STATUS_LABELS   = get_status_labels()
        PRIORITY_LABELS = get_priority_labels()
        orders = fetch_customer_orders(self.conn, self._item_id)
        table  = self.orders_table
        table.setRowCount(0)

        for o in orders[:20]:
            r = insert_row(table, ROW_HEIGHT_COMPACT)
            num_item = make_item(o["order_number"])
            bold_item(num_item)
            from PyQt5.QtGui import QColor
            num_item.setForeground(QColor(_C['accent']))
            table.setItem(r, 0, num_item)

            status_lbl = STATUS_LABELS.get(o["status"], (o["status"],))[0]
            table.setItem(r, 1, make_item(status_lbl))

            pri_lbl, _ = PRIORITY_LABELS.get(o["priority"], ("", ""))
            table.setItem(r, 2, muted_item(make_item(pri_lbl)))

            val_item = make_item(f"{(o['net_amount'] or 0):,.2f} {tr('currency_sym')}",
                                 align=Qt.AlignCenter)
            val_item.setForeground(QColor(_C['accent']))
            table.setItem(r, 3, val_item)
            table.setItem(r, 4, muted_item(make_item(o["order_date"] or "")))

        if orders:
            auto_fit_columns(table, fixed_cols=[1, 2, 3, 4], stretch_col=0)

    def load_customer(self, cid: int):
        self.load_item(cid)

    def _edit(self):
        if not self._item_id:
            return
        dlg = _CustomerForm(self.conn, customer_id=self._item_id, parent=self)
        dlg.saved.connect(lambda cid: (self.load_customer(cid), self.edited.emit(cid)))
        dlg.exec_()

    def _delete(self):
        if not self._item_id:
            return
        c = self._item_data
        if not c:
            return
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("customer_delete_confirm").format(name=c['name']),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if delete_customer(self.conn, self._item_id):
                self._item_id = None
                self._show_empty()
                self.deleted.emit()
            else:
                QMessageBox.warning(self, tr("warning"), tr("customer_delete_failed"))

    def _toggle_active(self):
        if not self._item_id:
            return
        toggle_customer_active(self.conn, self._item_id)
        self.load_customer(self._item_id)
        self.edited.emit(self._item_id)
```

---

## خامساً: تحسينات مقترحة

### 5.1 دمج `_status_config.py` في ملف واحد

الملفان `ui/tabs/orders/order_detail/_status_config.py` و `ui/tabs/orders/orders/_status_delegate.py` يستخدمان نفس data. الحل الموجود في الخطة يمررها كـ functions — هذا كافٍ.

### 5.2 حذف التكرار في STATUS_LABELS

يوجد تعريف `STATUS_LABELS` في ثلاثة ملفات:
- `orders/_status_delegate.py`
- `orders/_filter_toolbar.py`
- `order_detail/_status_config.py`

بعد التعديل أعلاه، كل الملفات تستورد من `_status_config.py` عبر `get_status_labels()`.

### 5.3 `make_splitter_table_guarded` غير موجودة

تم استبدالها بـ `make_table()` مع `setMaximumHeight` — وهو الحل الأبسط المتاح.  
لو احتجت splitter حقيقي لاحقاً، أضفه في `ui/widgets/tables/tables.py`.

### 5.4 `bold_item` و `colored_item` كدوال مستقلة

في `tables.py` الفعلي، `bold_item` و `colored_item` يُرجعان `QTableWidgetItem` — استخدامهما كـ wrapper على item قائم يحتاج التأكد من الـ signature. لو `bold_item(item)` يُعدّل in-place، استخدمه كذلك. لو يُنشئ item جديد، مرر النص مباشرة.

### 5.5 `app_settings.py`

هذا الملف **غير موجود** في `system_arch.txt`. جميع استيراداته يُستبدل بـ:
```python
from ui.theme import _C
```

---

## ملخص الملفات المتأثرة

| الملف | التغيير |
|---|---|
| `ui/i18n/ar.py` | إضافة ~90 مفتاح جديد |
| `ui/i18n/en.py` | إضافة ~90 مفتاح جديد |
| `ui/tabs/orders/orders_section.py` | إصلاح استيراد + `tab_style()` |
| `ui/tabs/orders/orders_tab.py` | إصلاح استيراد `BaseSection` |
| `ui/tabs/orders/customers_tab.py` | إصلاح استيراد `BaseSection` |
| `ui/tabs/orders/dashboard_tab.py` | إصلاح استيرادات + `tr()` |
| `ui/tabs/orders/dashboard/_config.py` | إعادة كتابة كاملة — دوال بدل ثوابت |
| `ui/tabs/orders/dashboard/_top_cards.py` | إصلاح استيرادات + `tr()` + `_C` |
| `ui/tabs/orders/dashboard/_status_grid.py` | إصلاح استيرادات |
| `ui/tabs/orders/dashboard/_recent_table.py` | إصلاح استيرادات + `tr()` + `_C` |
| `ui/tabs/orders/order_detail/_status_config.py` | إعادة كتابة — دوال بدل ثوابت |
| `ui/tabs/orders/order_detail/_header_fill.py` | استخدام دوال `_status_config` |
| `ui/tabs/orders/order_detail/_items_section.py` | إصلاح استيرادات + `tr()` + `_C` |
| `ui/tabs/orders/order_detail/_log_section.py` | إصلاح استيرادات + `tr()` |
| `ui/tabs/orders/order_detail/_status_dialog.py` | إصلاح استيرادات + `tr()` + `_C` |
| `ui/tabs/orders/_order_detail.py` | إصلاح استيرادات + `tr()` |
| `ui/tabs/orders/orders/_orders_list_panel.py` | إصلاح استيرادات + `tr()` + `_C` |
| `ui/tabs/orders/orders/_filter_toolbar.py` | إعادة كتابة — `tr()` + `_C` + `FS_*` |
| `ui/tabs/orders/orders/_status_delegate.py` | إصلاح استيرادات + `_C` |
| `ui/tabs/orders/_order_form.py` | إعادة كتابة — `tr()` + `_C` + `FS_*` |
| `ui/tabs/orders/order_form/_item_row_widget.py` | إعادة كتابة — `tr()` + `_C` + `FS_*` |
| `ui/tabs/orders/order_form/_products_fetcher.py` | إصلاح `get_costing_connection` |
| `ui/tabs/orders/_item_form.py` | إعادة كتابة — `tr()` + `_C` + `FS_*` |
| `ui/tabs/orders/_customer_form.py` | إعادة كتابة — `tr()` + `_C` + `FS_*` |
| `ui/tabs/orders/customers/customers_list_panel.py` | إعادة كتابة — `tr()` + `_C` + `FS_*` |
| `ui/tabs/orders/customers/customer_detail_panel.py` | إعادة كتابة — `tr()` + `_C` + `FS_*` |