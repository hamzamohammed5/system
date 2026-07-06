"""
ui/constants_data/orders.py
======================
ثوابت قسم الطلبات والعملاء
جزء من تقسيم ui/constants.py — راجع ui/constants/__init__.py.
"""

# ══════════════════════════════════════════════════════════
# CustomersListPanel — ui/tabs/orders/customers/customers_list_panel.py
# ══════════════════════════════════════════════════════════
CUSTOMERS_LIST_COL_CODE_W   = 80    # عرض عمود الكود (px)
CUSTOMERS_LIST_COL_NAME_W   = 160   # عرض عمود الاسم (px)
CUSTOMERS_LIST_COL_PHONE_W  = 110   # عرض عمود الهاتف (px)
CUSTOMERS_LIST_COL_CITY_W   = 80    # عرض عمود المدينة (px)
CUSTOMERS_LIST_COL_ORDERS_W = 55    # عرض عمود عدد الطلبات (px)

# ══════════════════════════════════════════════════════════
# CustomerDetailPanel — ui/tabs/orders/customers/customer_detail_panel.py
# ══════════════════════════════════════════════════════════
CUSTOMER_CONTACTS_MAX_H      = 140   # max_height لجدول جهات الاتصال (px)
CUSTOMER_ORDERS_MAX_H        = 220   # max_height لجدول آخر الطلبات (px)
CUSTOMER_CONTACT_COL_ROLE_W  = 80    # عرض عمود الصفة في جدول جهات الاتصال (px)
CUSTOMER_CONTACT_COL_PHONE_W = 100   # عرض عمود الهاتف في جدول جهات الاتصال (px)
CUSTOMER_CONTACT_COL_EMAIL_W = 120   # عرض عمود الإيميل في جدول جهات الاتصال (px)
CUSTOMER_CONTACT_COL_NOTES_W = 120   # عرض عمود الملاحظات في جدول جهات الاتصال (px)
CUSTOMER_ORDERS_COL_STATUS_W = 90    # عرض عمود الحالة في جدول الطلبات (px)
CUSTOMER_ORDERS_COL_PRI_W    = 70    # عرض عمود الأولوية في جدول الطلبات (px)
CUSTOMER_ORDERS_COL_TOTAL_W  = 80    # عرض عمود الإجمالي في جدول الطلبات (px)
CUSTOMER_ORDERS_COL_DATE_W   = 90    # عرض عمود التاريخ في جدول الطلبات (px)

# ══════════════════════════════════════════════════════════
# Orders Dashboard — ui/tabs/orders/dashboard/
# ══════════════════════════════════════════════════════════
DASHBOARD_RECENT_TABLE_COL_WIDTHS = {0: 130, 1: 160, 2: 80, 3: 100, 4: 75, 5: 100, 6: 90}
DASHBOARD_TABLE_BORDER_PAD        = 4    # يُضاف لمجموع عرض الأعمدة لحساب TABLE_TOTAL_W (px)
DASHBOARD_TOP_CARDS_SPACING       = 12   # spacing لصف البطاقات الإحصائية العلوية (px)
DASHBOARD_SCROLL_MAX_H            = 340  # ارتفاع أقصى لمنطقة scroll العلوية في OrdersDashboardTab (px)
DASHBOARD_TOP_MARGIN              = (20, 16, 20, 12)  # contentsMargins لـ top_lay (l,t,r,b)
DASHBOARD_TOP_SPACING             = 16   # spacing لـ top_lay في OrdersDashboardTab (px)
DASHBOARD_RECENT_HDR_MARGIN       = (20, 8, 20, 4)   # contentsMargins لـ recent_hdr (l,t,r,b)
DASHBOARD_TABLE_CONTAINER_MARGIN  = (20, 0, 20, 16)  # contentsMargins لـ table_container (l,t,r,b)
DASHBOARD_REFRESH_BTN_MIN_H       = 30   # ارتفاع أدنى لزر التحديث في OrdersDashboardTab (px)
DASHBOARD_RECENT_LIMIT            = 20   # عدد الطلبات الأخيرة المعروضة في جدول Dashboard

# ══════════════════════════════════════════════════════════
# Order Detail — Items Section — ui/tabs/orders/order_detail/_items_section.py
# ══════════════════════════════════════════════════════════
ORDER_ITEMS_TABLE_COL_WIDTHS = {2: 65, 3: 65, 4: 90, 5: 60, 6: 95}  # عرض أعمدة جدول بنود الطلب (px)
ORDER_ITEMS_TABLE_MAX_H      = 280   # ارتفاع أقصى لجدول بنود الطلب (px)
ORDER_ITEMS_TABLE_MIN_H      = 60    # ارتفاع أدنى لجدول بنود الطلب (px)
ORDER_ITEMS_EMPTY_MIN_H      = 90    # min_height لـ EmptyState بنود الطلب (px)
ORDER_ITEMS_TOOLBAR_SPACING  = 6     # spacing لشريط أدوات البنود (px)
ORDER_ITEMS_BTN_MIN_H        = 28    # ارتفاع أدنى لأزرار تعديل/حذف البند (px)

# ══════════════════════════════════════════════════════════
# Order Detail — Log Section — ui/tabs/orders/order_detail/_log_section.py
# ══════════════════════════════════════════════════════════
ORDER_LOG_TABLE_COL_WIDTHS = {0: 100, 1: 100, 3: 120}  # عرض أعمدة جدول سجل الحالة (px)
ORDER_LOG_TABLE_MAX_H      = 160   # ارتفاع أقصى لجدول سجل الحالة (px)

# ══════════════════════════════════════════════════════════
# Order Form — Item Row Widget — ui/tabs/orders/order_form/_item_row_widget.py
# ══════════════════════════════════════════════════════════
ITEM_ROW_FRAME_RADIUS       = 8     # border-radius لإطار _ItemRowWidget (px)
ITEM_ROW_ROOT_MARGIN_H      = 10    # left/right margin لـ root layout (px)
ITEM_ROW_ROOT_MARGIN_V      = 8     # top/bottom margin لـ root layout (px)
ITEM_ROW_ROOT_SPACING       = 5     # spacing لـ root VBoxLayout (px)
ITEM_ROW_ROW_SPACING        = 6     # spacing لـ row1 (بحث + combo) (px)
ITEM_ROW_ROW2_SPACING       = 8     # spacing لـ row2 (سعر/خصم/كمية/إجمالي) (px)
ITEM_ROW_SEARCH_W           = 100   # عرض ثابت لحقل البحث (px)
ITEM_ROW_INPUT_MIN_H        = 30    # ارتفاع أدنى للحقول والـ combo (px)
ITEM_ROW_CLEAR_BTN_SIZE     = 22    # حجم زر مسح البحث (عرض وارتفاع) (px)
ITEM_ROW_INPUT_RADIUS       = 5     # border-radius لحقول الإدخال والـ combo (px)
ITEM_ROW_QTY_W              = 90    # عرض ثابت لحقل الكمية (px)
ITEM_ROW_UNIT_W             = 55    # عرض ثابت لحقل الوحدة (px)
ITEM_ROW_PRICE_LBL_MIN_W    = 85    # عرض أدنى لتسمية السعر (px)
ITEM_ROW_DISC_LBL_MIN_W     = 60    # عرض أدنى لتسمية الخصم (px)
ITEM_ROW_TOTAL_LBL_MIN_W    = 95    # عرض أدنى لتسمية الإجمالي (px)
ITEM_ROW_DEL_BTN_SIZE       = 30    # حجم زر الحذف (عرض وارتفاع) (px)
ITEM_ROW_QTY_MIN            = 0.001 # الحد الأدنى لقيمة الكمية
ITEM_ROW_QTY_MAX            = 99_999  # الحد الأقصى لقيمة الكمية
ITEM_ROW_QTY_DECIMALS       = 3     # عدد الخانات العشرية لحقل الكمية
ITEM_ROW_QTY_DEFAULT        = 1     # القيمة الافتراضية لحقل الكمية

# ══════════════════════════════════════════════════════════
# Order Detail — Status Dialog — ui/tabs/orders/order_detail/_status_dialog.py
# ══════════════════════════════════════════════════════════
STATUS_DLG_MIN_W        = 400   # الحد الأدنى لعرض نافذة تغيير الحالة (px)
STATUS_DLG_MARGIN       = (20, 18, 20, 18)  # contentsMargins للـ root layout (l,t,r,b)
STATUS_DLG_SPACING      = 12    # spacing للـ root layout (px)
STATUS_DLG_HDR_RADIUS   = 8     # border-radius لعنوان النافذة (px)
STATUS_DLG_HDR_PAD_V    = 8     # padding رأسي لعنوان النافذة (px)
STATUS_DLG_HDR_PAD_H    = 14    # padding أفقي لعنوان النافذة (px)
STATUS_DLG_CUR_RADIUS   = 6     # border-radius لصندوق الحالة الحالية (px)
STATUS_DLG_CUR_BORDER_W = 1     # عرض border لصندوق الحالة الحالية (px)
STATUS_DLG_CUR_PAD_V    = 6     # padding رأسي لصندوق الحالة الحالية (px)
STATUS_DLG_CUR_PAD_H    = 10    # padding أفقي لصندوق الحالة الحالية (px)
STATUS_DLG_CMB_MIN_H    = 36    # ارتفاع أدنى لقائمة الحالة الجديدة (px)
STATUS_DLG_BTN_OK_MIN_H = 38    # ارتفاع أدنى لزر تأكيد التغيير (px)

# ══════════════════════════════════════════════════════════
# Orders List — Filter Toolbar — ui/tabs/orders/orders/_filter_toolbar.py
# ══════════════════════════════════════════════════════════
FILTER_TB_COMBO_RADIUS       = 5     # border-radius لـ combo الحالة/الأولوية (px)
FILTER_TB_COMBO_PAD_H        = 8     # padding أفقي لـ combo الحالة/الأولوية (px)
FILTER_TB_COMBO_MIN_H        = 28    # ارتفاع أدنى لـ combo الحالة/الأولوية (px)
FILTER_TB_COMBO_DROPDOWN_W   = 16    # عرض سهم القائمة المنسدلة لـ combo (px)
FILTER_TB_NEW_BTN_RADIUS     = 8     # border-radius لزر "طلب جديد" (px)
FILTER_TB_NEW_BTN_H          = 36    # ارتفاع افتراضي لزر "طلب جديد" (px)
FILTER_TB_NEW_BTN_MIN_W      = 100   # الحد الأدنى لعرض زر "طلب جديد" (px)
FILTER_TB_NEW_BTN_TEXT_PAD   = 40    # إضافة لحساب عرض الزر من عرض النص (px)
FILTER_TB_ROOT_MARGIN_H      = 12    # left/right margin لـ root layout (px)
FILTER_TB_ROOT_MARGIN_T      = 12    # top margin لـ root layout (px)
FILTER_TB_ROOT_MARGIN_B      = 10    # bottom margin لـ root layout (px)
FILTER_TB_ROOT_SPACING       = 8     # spacing لـ root VBoxLayout (px)
FILTER_TB_ROW2_SPACING       = 6     # spacing لصف combo الحالة/الأولوية/زر المسح (px)
FILTER_TB_SEARCH_H           = 34    # ارتفاع ثابت لحقل البحث (px)
FILTER_TB_SEARCH_RADIUS      = 6     # border-radius لحقل البحث (px)
FILTER_TB_SEARCH_PAD_H       = 10    # padding أفقي لحقل البحث (px)
FILTER_TB_SEARCH_BORDER_W    = 1.5   # عرض border لحقل البحث (px)

# ══════════════════════════════════════════════════════════
# Orders List Panel — ui/tabs/orders/orders/_orders_list_panel.py
# ══════════════════════════════════════════════════════════
ORDERS_LIST_COL_WIDTHS   = {0: 130, 1: 150, 2: 100, 3: 32, 4: 90}  # عرض أعمدة جدول الطلبات (px)
ORDERS_LIST_MIN_W        = 280   # الحد الأدنى لعرض لوحة القائمة (px)
ORDERS_LIST_MAX_W        = 560   # الحد الأقصى لعرض لوحة القائمة (px)
ORDERS_LIST_AUTOFIT_MIN_W= 30    # الحد الأدنى لعرض عمود عند auto_fit_columns (px)
CUSTOMERS_LIST_MIN_W     = 300   # الحد الأدنى لعرض لوحة قائمة العملاء (px)
ORDERS_LIST_AUTOFIT_MAX_W= 300   # الحد الأقصى لعرض عمود عند auto_fit_columns (px)
ORDERS_SPLITTER_FIT_DELAY_MS = 50  # تأخير (ms) قبل ضبط عرض الـ splitter بعد تحديث القائمة

# ══════════════════════════════════════════════════════════
# Orders List — Status Delegate — ui/tabs/orders/orders/_status_delegate.py
# ══════════════════════════════════════════════════════════
STATUS_DELEGATE_PAD_V         = 7     # padding رأسي حول الـ badge (px)
STATUS_DELEGATE_PAD_H         = 6     # padding أفقي حول الـ badge (px)
STATUS_DELEGATE_BADGE_MAX_W   = 90    # الحد الأقصى لعرض الـ badge (px)
STATUS_DELEGATE_BADGE_MIN_H   = 22    # الحد الأدنى لارتفاع الـ badge (px)
STATUS_DELEGATE_BADGE_MAX_H   = 28    # الحد الأقصى لارتفاع الـ badge (px)
STATUS_DELEGATE_BADGE_RADIUS  = 10    # border-radius لإطار الـ badge (px)
STATUS_DELEGATE_BORDER_W      = 1.2   # عرض border إطار الـ badge (px)
STATUS_DELEGATE_FONT_MIN_PT   = 8     # الحد الأدنى لحجم خط نص الـ badge (pt)
STATUS_DELEGATE_SIZE_HINT_W   = 100   # عرض sizeHint الافتراضي للخلية (px)


# ══════════════════════════════════════════════════════════════
# _OrderDetail — ui/tabs/orders/_order_detail.py
# ══════════════════════════════════════════════════════════════
ORDER_DETAIL_ICON_TOTAL   = "order_icon_total"    # مفتاح tr لأيقونة بطاقة الإجمالي
ORDER_DETAIL_ICON_PAID    = "order_icon_paid"     # مفتاح tr لأيقونة بطاقة المدفوع
ORDER_DETAIL_ICON_BALANCE = "order_icon_balance"  # مفتاح tr لأيقونة بطاقة الرصيد
ORDER_DETAIL_ICON_DUE     = "order_icon_due"      # مفتاح tr لأيقونة بطاقة الاستحقاق

# ══════════════════════════════════════════════════════════════
# _OrderForm — ui/tabs/orders/_order_form.py
# ══════════════════════════════════════════════════════════════
ORDER_FORM_MIN_W            = 880   # الحد الأدنى لعرض نافذة الطلب (px)
ORDER_FORM_MIN_H            = 760   # الحد الأدنى لارتفاع نافذة الطلب (px)
ORDER_FORM_ROOT_MARGIN      = (20, 18, 20, 18)  # contentsMargins للـ root layout (l,t,r,b)
ORDER_FORM_ROOT_SPACING     = 14    # spacing للـ root layout (px)
ORDER_FORM_GRP_SPACING      = 8     # spacing عام لـ QGroupBox layouts (px)
ORDER_FORM_GRP_MARGIN_TOP   = 10    # margin-top للـ QGroupBox (px)
ORDER_FORM_GRP_PAD_TOP      = 10    # padding-top للـ QGroupBox (px)
ORDER_FORM_GRP_TITLE_PAD_H  = 6     # padding أفقي لعنوان QGroupBox (px)
ORDER_FORM_DETAILS_SPACING  = 10    # spacing لـ QFormLayout تفاصيل الطلب (px)
ORDER_FORM_TOOLBAR_SPACING  = 8     # spacing شريط أدوات البنود (px)
ORDER_FORM_OFFERS_MIN_H     = 34    # ارتفاع أدنى لـ cmb_offers (px)
ORDER_FORM_OFFERS_MIN_W     = 200   # عرض أدنى لـ cmb_offers (px)
ORDER_FORM_ROWS_SPACING     = 6     # spacing بين صفوف البنود (px)
ORDER_FORM_ROWS_MARGIN      = (0, 0, 4, 0)   # contentsMargins لـ rows layout (l,t,r,b)
ORDER_FORM_TOTAL_BAR_RADIUS = 6     # border-radius لشريط الإجمالي (px)
ORDER_FORM_TOTAL_BAR_MARGIN = (14, 8, 14, 8) # contentsMargins لشريط الإجمالي (l,t,r,b)
ORDER_FORM_NOTES_MAX_H      = 65    # ارتفاع أقصى لحقول الملاحظات (px)
ORDER_FORM_NOTES_SPACING    = 8     # spacing لقسم الملاحظات (px)
ORDER_FORM_SAVE_BTN_MIN_H   = 40    # ارتفاع أدنى لزر الحفظ (px)
ORDER_FORM_CUST_INFO_RADIUS = 6     # border-radius لـ label معلومات العميل (px)
ORDER_FORM_CUST_INFO_PAD    = (6, 10)   # padding (v, h) لـ label معلومات العميل (px)
ORDER_FORM_DUE_DATE_DEFAULT = 7     # عدد أيام الاستحقاق الافتراضي من اليوم
ORDER_FORM_DISCOUNT_MAX     = 99_999    # الحد الأقصى لقيمة الخصم الكلي
ORDER_FORM_PAID_MAX         = 9_999_999 # الحد الأقصى للمبلغ المدفوع

# ══════════════════════════════════════════════════════════════
# _CustomerForm — ui/tabs/orders/_customer_form.py
# ══════════════════════════════════════════════════════════════
CUSTOMER_FORM_MIN_W         = 580   # الحد الأدنى لعرض نافذة العميل (px)
CUSTOMER_FORM_MIN_H         = 620   # الحد الأدنى لارتفاع نافذة العميل (px)
CUSTOMER_FORM_ROOT_MARGIN   = (20, 18, 20, 18)  # contentsMargins للـ root layout (l,t,r,b)
CUSTOMER_FORM_ROOT_SPACING  = 14    # spacing للـ root layout (px)
CUSTOMER_FORM_FORM_SPACING  = 10    # spacing لـ QFormLayout (px)
CUSTOMER_FORM_GRP_RADIUS    = 8     # border-radius للـ QGroupBox (px)
CUSTOMER_FORM_GRP_MARGIN_T  = 8     # margin-top للـ QGroupBox (px)
CUSTOMER_FORM_GRP_PAD_TOP   = 8     # padding-top للـ QGroupBox (px)
CUSTOMER_FORM_GRP_TITLE_PAD = 4     # padding أفقي لعنوان QGroupBox (px)
CUSTOMER_FORM_GRP_TITLE_R   = 12    # مسافة right لعنوان QGroupBox (px)
CUSTOMER_FORM_NOTES_MAX_H   = 70    # ارتفاع أقصى لحقل الملاحظات (px)
CUSTOMER_FORM_CONTACTS_MAX_H= 150   # ارتفاع أقصى لجدول جهات الاتصال (px)
CUSTOMER_FORM_CONTACTS_SPACING = 8  # spacing لقسم جهات الاتصال (px)
CUSTOMER_FORM_SAVE_BTN_MIN_H= 38    # ارتفاع أدنى لزر الحفظ (px)
CUSTOMER_FORM_HDR_RADIUS    = 8     # border-radius لعنوان النافذة (px)
CUSTOMER_FORM_HDR_PAD       = "8px 14px"  # padding لعنوان النافذة
CUSTOMER_FORM_CONTACTS_COL1_W = 80   # عرض عمود «الصفة» في جدول جهات الاتصال (px)
CUSTOMER_FORM_CONTACTS_COL2_W = 100  # عرض عمود «الهاتف» في جدول جهات الاتصال (px)
CUSTOMER_FORM_CONTACTS_COL3_W = 120  # عرض عمود «الإيميل» في جدول جهات الاتصال (px)
CUSTOMER_FORM_CONTACTS_COL4_W = 120  # عرض عمود «ملاحظات» في جدول جهات الاتصال (px)

# ══════════════════════════════════════════════════════════════
# _ContactDialog — ui/tabs/orders/_customer_form.py
# ══════════════════════════════════════════════════════════════
CONTACT_DLG_MIN_W           = 400   # الحد الأدنى لعرض نافذة جهة الاتصال (px)
CONTACT_DLG_ROOT_MARGIN     = (16, 16, 16, 16)  # contentsMargins للـ root layout (l,t,r,b)
CONTACT_DLG_ROOT_SPACING    = 10    # spacing للـ root layout (px)
CONTACT_DLG_FORM_SPACING    = 8     # spacing لـ QFormLayout (px)

# ══════════════════════════════════════════════════════════════
# _ItemForm — ui/tabs/orders/_item_form.py
# ══════════════════════════════════════════════════════════════
ITEM_FORM_MIN_W             = 480   # الحد الأدنى لعرض نافذة البند (px)
ITEM_FORM_ROOT_MARGIN       = (20, 18, 20, 18)  # contentsMargins للـ root layout (l,t,r,b)
ITEM_FORM_ROOT_SPACING      = 12    # spacing للـ root layout (px)
ITEM_FORM_FORM_SPACING      = 10    # spacing لـ QFormLayout (px)
ITEM_FORM_SPIN_MIN_H        = 34    # ارتفاع أدنى لـ QDoubleSpinBox (px)
ITEM_FORM_SPIN_MAX          = 9_999_999  # الحد الأقصى الافتراضي لـ QDoubleSpinBox
ITEM_FORM_TOTAL_RADIUS      = 6     # border-radius لـ label الإجمالي (px)
ITEM_FORM_TOTAL_PAD         = "6px 12px"  # padding لـ label الإجمالي
ITEM_FORM_SAVE_BTN_MIN_H    = 36    # ارتفاع أدنى لزر الحفظ (px)
ITEM_FORM_QTY_MIN           = 0.001 # الحد الأدنى لقيمة الكمية
ITEM_FORM_QTY_MAX           = 99_999    # الحد الأقصى لقيمة الكمية
ITEM_FORM_QTY_DECIMALS      = 3     # عدد الخانات العشرية لحقل الكمية
ITEM_FORM_PRICE_MAX         = 9_999_999 # الحد الأقصى لسعر الوحدة
ITEM_FORM_DISCOUNT_MAX      = 100   # الحد الأقصى لنسبة الخصم (%)
ITEM_FORM_HDR_RADIUS        = 8     # border-radius لعنوان النافذة (px)
ITEM_FORM_HDR_PAD           = "8px 14px"  # padding لعنوان النافذة
ORDER_FORM_HDR_RADIUS       = 8     # border-radius لعنوان نافذة الطلب (px)
ORDER_FORM_HDR_PAD          = "10px 16px"  # padding لعنوان نافذة الطلب


