"""
ui/i18n/ar.py
==============
القاموس العربي الكامل للتطبيق.

يُستخدم من I18nManager في ui/i18n.py كمصدر للترجمة العربية.
يُصدّر AR_STRINGS للاستخدام المستقل أو للاستيراد من أدوات الترجمة.

[Sync] متطابق في المفاتيح مع en.py — كل مفتاح موجود في الملفين بالضبط.
[Update] إضافة مفاتيح جديدة للماكينات وعمليات التشغيل والعمالة وعامة
"""

AR_STRINGS: dict[str, str] = {

    # ══════════════════════════════════════════════
    # أزرار وإجراءات
    # ══════════════════════════════════════════════
    "save":              "حفظ",
    "save_edit":         "حفظ التعديل",
    "add":               "إضافة",
    "edit":              "تعديل",
    "delete":            "حذف",
    "cancel":            "إلغاء",
    "confirm":           "تأكيد",
    "close":             "إغلاق",
    "search":            "بحث",
    "reset":             "إعادة تعيين",
    "refresh":           "تحديث",
    "export":            "تصدير",
    "import":            "استيراد",
    "print":             "طباعة",
    "back":              "رجوع",
    "next":              "التالي",
    "previous":          "السابق",
    "yes":               "نعم",
    "no":                "لا",
    "ok":                "حسناً",
    "apply":             "تطبيق",
    "browse":            "تصفح",
    "select":            "اختيار",
    "clear":             "مسح",
    "copy":              "نسخ",
    "paste":             "لصق",
    "open":              "فتح",
    "new":               "جديد",
    "all":               "الكل",
    "clone":             "استنساخ",
    "selected":          "محدد",

    # ══════════════════════════════════════════════
    # أزرار فورم
    # ══════════════════════════════════════════════
    "btn_add":      "➕  إضافة",
    "btn_save":     "💾  حفظ التعديل",
    "btn_cancel":   "✖  إلغاء",
    "btn_delete":   "🗑️  حذف",
    "btn_edit":     "✏️  تعديل",
    "btn_refresh":  "🔄  تحديث",

    # ══════════════════════════════════════════════
    # تنقل
    # ══════════════════════════════════════════════
    "nav_costing":       "حساب التكلفة",
    "nav_pricing":       "التسعير",
    "nav_accounting":    "الحسابات",
    "nav_inventory":     "المخزن",
    "nav_design":        "التصميمات",
    "nav_orders":        "الطلبات",
    "nav_shared":        "العناصر المشتركة",
    "nav_settings":      "الإعدادات",

    # ══════════════════════════════════════════════
    # إعدادات
    # ══════════════════════════════════════════════
    "settings":          "الإعدادات",
    "settings_font":     "حجم الخط",
    "settings_gimp":     "مسار GIMP",
    "settings_units":    "وحدات القياس",
    "settings_theme":    "المظهر",
    "settings_language": "اللغة",
    "theme_light":       "فاتح",
    "theme_dark":        "داكن",
    "lang_ar":           "العربية",
    "lang_en":           "English",
    "preview":           "معاينة",

    # ══════════════════════════════════════════════
    # حالات فارغة
    # ══════════════════════════════════════════════
    "no_data":              "لا توجد بيانات",
    "no_results":           "لا توجد نتائج",
    "no_search_results":    "جرب تغيير كلمة البحث أو الفلتر",
    "select_item_first":    "اختر عنصراً أولاً",
    "select_company":       "اختر شركة نشطة أولاً",

    "list_search_placeholder": "🔍  بحث...",
    "detail_select_item":      "اختر عنصراً من القائمة",

    # ══════════════════════════════════════════════
    # تأكيد
    # ══════════════════════════════════════════════
    "confirm_delete":       "تأكيد الحذف",
    "confirm_save":         "تأكيد الحفظ",
    "confirm_action":       "تأكيد",
    "delete_confirm_msg":   "هل تريد حذف «{name}»؟",
    "save_confirm_msg":     "تأكيد حفظ «{name}»؟",

    # ══════════════════════════════════════════════
    # نجاح / خطأ
    # ══════════════════════════════════════════════
    "success_add":          "تم الإضافة بنجاح",
    "success_save":         "تم الحفظ بنجاح",
    "success_delete":       "تم الحذف بنجاح",
    "error_load":           "خطأ في تحميل البيانات",
    "tab_load_error":       "خطأ في تحميل التبويب: {error}",
    "error_save":           "خطأ في الحفظ",
    "error_delete":         "خطأ في الحذف",
    "warning":              "تنبيه",
    "error":                "خطأ",
    "info":                 "معلومة",
    "notice":               "ملاحظة",
    "done":                 "تم",

    # ══════════════════════════════════════════════
    # رسائل التحقق من الحقول
    # ══════════════════════════════════════════════
    "enter_field":          "أدخل {label}",
    "select_field":         "اختر {label}",
    "field_positive":       "{label} يجب أن يكون أكبر من صفر",
    "field_positive_enter": "أدخل {label} أكبر من صفر",

    # ══════════════════════════════════════════════
    # حقول عامة
    # ══════════════════════════════════════════════
    "name":                 "الاسم",
    "code":                 "الكود",
    "description":          "الوصف",
    "notes":                "ملاحظات",
    "date":                 "التاريخ",
    "amount":               "المبلغ",
    "price":                "السعر",
    "quantity":             "الكمية",
    "unit":                 "الوحدة",
    "category":             "التصنيف",
    "status":               "الحالة",
    "type":                 "النوع",
    "total":                "الإجمالي",
    "subtotal":             "المجموع الفرعي",
    "discount":             "الخصم",
    "tax":                  "الضريبة",

    # ══════════════════════════════════════════════
    # وحدات زمنية
    # ══════════════════════════════════════════════
    "month":                "شهر",
    "day":                  "يوم",
    "hour":                 "ساعة",

    # ══════════════════════════════════════════════
    # محاسبة
    # ══════════════════════════════════════════════
    "accounts":             "الحسابات",
    "journal_entries":      "القيود المحاسبية",
    "trial_balance":        "ميزان المراجعة",
    "income_statement":     "قائمة الدخل",
    "balance_sheet":        "الميزانية العمومية",
    "debit":                "مدين",
    "credit":               "دائن",
    "balance":              "الرصيد",
    "ref_no":               "رقم المرجع",
    "investors":            "المستثمرون",
    "investor_add":         "إضافة مستثمر",
    "investor_movement":    "حركة مستثمر",
    "link_to_entry":        "ربط بقيد",
    "account_group":        "مجموعة الحسابات",
    "account_nature":       "طبيعة الحساب",
    "account_tree":         "شجرة الحسابات",
    "fiscal_year":          "السنة المالية",
    "owners_equity":        "حقوق الملكية",
    "assets":               "الأصول",
    "liabilities":          "الخصوم",
    "audit_log":            "سجل المراجعة",
    "debit_nature":         "طبيعة مدينة",
    "credit_nature":        "طبيعة دائنة",
    "account_level":        "مستوى الحساب",
    "account_code":         "كود الحساب",
    "account_type":         "نوع الحساب",
    "account_balance":      "رصيد الحساب",
    "opening_balance":      "الرصيد الافتتاحي",
    "closing_balance":      "الرصيد الختامي",
    "journal_date":         "تاريخ القيد",
    "journal_description":  "وصف القيد",
    "total_debit":          "إجمالي المدين",
    "total_credit":         "إجمالي الدائن",
    "balanced":             "متوازن",
    "unbalanced":           "غير متوازن",
    "post_entry":           "ترحيل القيد",
    "reverse_entry":        "عكس القيد",
    "draft":                "مسودة",
    "posted":               "مرحَّل",

    # ══════════════════════════════════════════════
    # مخزون
    # ══════════════════════════════════════════════
    "inventory":            "المخزن",
    "stock_in":             "وارد",
    "stock_out":            "صادر",
    "current_stock":        "المخزون الحالي",
    "inbound":              "وارد",
    "outbound":             "صادر",
    "inventory_report":     "تقرير المخزون",
    "item_name":            "اسم الصنف",
    "item_type":            "نوع الصنف",
    "min_stock":            "الحد الأدنى للمخزون",
    "current_balance":      "الرصيد الحالي",
    "movement_date":        "تاريخ الحركة",
    "movement_type":        "نوع الحركة",
    "unit_cost":            "سعر الوحدة",
    "total_inbound":        "إجمالي الوارد",
    "total_outbound":       "إجمالي الصادر",
    "low_stock":            "مخزون منخفض",
    "low_stock_items":      "الأصناف المنخفضة",
    "stock_value":          "قيمة المخزون",
    "no_movements":         "لا توجد حركات",
    "record_inbound":       "تسجيل وارد",
    "record_outbound":      "تسجيل صادر",
    "movement_ref":         "مرجع الحركة",

    # ══════════════════════════════════════════════
    # شركات
    # ══════════════════════════════════════════════
    "company":              "الشركة",
    "select_company_msg":   "اختر شركة للبدء",
    "no_company":           "لا توجد شركة نشطة",
    "manage_companies":     "إدارة الشركات",

    # ══════════════════════════════════════════════
    # تكلفة
    # ══════════════════════════════════════════════
    "cost":                 "التكلفة",
    "cost_per_unit":        "التكلفة للوحدة",
    "selling_price":        "سعر البيع",
    "profit_margin":        "هامش الربح",
    "waste":                "الهادر",
    "waste_pct":            "نسبة الهادر",

    # ══════════════════════════════════════════════
    # BOM — أنواع المكونات
    # ══════════════════════════════════════════════
    "components":           "المكونات",
    "raw_material":         "خامة",
    "semi_product":         "نصف مصنع",
    "labor_op":             "عملية عمالة",
    "machine_op":           "عملية تشغيل",

    # ══════════════════════════════════════════════
    # فلاتر
    # ══════════════════════════════════════════════
    "filter_all":               "— الكل —",
    "filter_all_categories":    "— كل التصنيفات —",
    "date_from":                "من:",
    "date_to":                  "إلى:",
    "today":                    "اليوم",
    "this_month":               "الشهر",
    "this_year":                "العام",

    # ══════════════════════════════════════════════
    # شريط الحالة
    # ══════════════════════════════════════════════
    "showing_of":   "{shown} / {total}",
    "showing_all":  "{total}",

    # ══════════════════════════════════════════════
    # تصنيفات
    # ══════════════════════════════════════════════
    "category_data":          "بيانات التصنيف",
    "category_name":          "الاسم",
    "category_parent":        "تابع لـ",
    "category_color":         "اللون",
    "category_add":           "تصنيف جديد",
    "category_new":           "الأبناء",
    "category_edit":          "تعديل",
    "category_delete":        "حذف",
    "category_select_first":  "اختر تصنيفاً أولاً",
    "category_name_required": "أدخل اسم التصنيف",
    "no_category":            "بدون تصنيف",

    # ══════════════════════════════════════════════
    # عمليات عامة
    # ══════════════════════════════════════════════
    "operation_add":    "إضافة",
    "operation_edit":   "تعديل",
    "operation_delete": "حذف",
    "operation_save":   "حفظ",
    "operation_cancel": "إلغاء",

    # ══════════════════════════════════════════════
    # تصميمات
    # ══════════════════════════════════════════════
    "designs":              "التصميمات",
    "design_add":           "إضافة تصميم",
    "design_categories":    "تصنيفات التصميم",
    "dimension_sets":       "مجموعات الأبعاد",
    "design_name":          "اسم التصميم",
    "design_file":          "ملف التصميم",
    "open_in_gimp":         "فتح في GIMP",
    "thumbnail":            "صورة مصغرة",
    "dimension_set_name":   "اسم مجموعة الأبعاد",
    "dimension_group":      "مجموعة الأبعاد",
    "dimension_field":      "حقل البعد",
    "dimension_value":      "قيمة البعد",
    "dimension_instance":   "نسخة الأبعاد",
    "no_designs":           "لا توجد تصميمات",
    "add_size":             "إضافة مقاس",
    "size_name":            "اسم المقاس",
    "size_width":           "العرض",
    "size_height":          "الارتفاع",
    "gimp_not_found":       "لم يتم العثور على GIMP",
    "file_not_found":       "الملف غير موجود",
    "source_set":           "مجموعة المصدر",
    "target_field":         "الحقل المستهدف",

    # ══════════════════════════════════════════════
    # طلبات
    # ══════════════════════════════════════════════
    "orders":               "الطلبات",
    "order_add":            "إضافة طلب",
    "customers":            "العملاء",
    "customer_add":         "إضافة عميل",
    "order_status":         "حالة الطلب",
    "order_date":           "تاريخ الطلب",
    "order_number":         "رقم الطلب",
    "order_total":          "إجمالي الطلب",
    "customer_name":        "اسم العميل",
    "customer_phone":       "هاتف العميل",
    "customer_address":     "عنوان العميل",
    "delivery_date":        "تاريخ التسليم",
    "payment_status":       "حالة الدفع",
    "order_items":          "بنود الطلب",
    "status_pending":       "معلق",
    "status_confirmed":     "مؤكد",
    "status_in_production": "قيد الإنتاج",
    "status_ready":         "جاهز للتسليم",
    "status_delivered":     "مُسلَّم",
    "status_cancelled":     "ملغي",
    "dashboard":            "لوحة التحكم",
    "recent_orders":        "الطلبات الأخيرة",
    "top_customers":        "أفضل العملاء",
    "order_log":            "سجل الطلب",
    "change_status":        "تغيير الحالة",
    "no_orders":            "لا توجد طلبات",
    "no_customers":         "لا يوجد عملاء",
    "paid":                 "مدفوع",
    "unpaid":               "غير مدفوع",
    "partial":              "جزئي",
    "deposit":              "عربون",
    "unit_price":           "سعر الوحدة",
    "item_qty":             "الكمية",
    "item_total":           "الإجمالي",

    # ── طلبات — عنوانات تبويبات القسم ─────────────────────
    "orders_section_tab_dashboard": "📊  لوحة المتابعة",
    "orders_section_tab_orders":    "📋  الطلبات",
    "orders_section_tab_customers": "👥  العملاء",

    # ── طلبات — حقول ونوافذ ──────────────────────────────
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

    # ══════════════════════════════════════════════
    # تسعير
    # ══════════════════════════════════════════════
    "pricing":              "التسعير",
    "offers":               "العروض",
    "offer_add":            "إضافة عرض",
    "offer_name":           "اسم العرض",
    "offer_validity":       "صلاحية العرض",
    "offer_items":          "بنود العرض",
    "base_cost":            "التكلفة الأساسية",
    "markup_pct":           "نسبة الهامش %",
    "final_price":          "السعر النهائي",
    "product_cost":         "تكلفة المنتج",
    "scenario_used":        "السيناريو المستخدم",
    "offer_total":          "إجمالي العرض",
    "no_offers":            "لا توجد عروض",
    "pricing_table":        "جدول التسعير",
    "cost_breakdown":       "تفصيل التكلفة",
    "min_price":            "الحد الأدنى للسعر",
    "suggested_price":      "السعر المقترح",
    "customer_price":       "سعر العميل",

    # ══════════════════════════════════════════════
    # حذف — رسائل خاصة
    # ══════════════════════════════════════════════
    "delete_has_children":  "لا يمكن الحذف — يحتوي على عناصر فرعية",
    "delete_has_items":     "لا يمكن الحذف — مرتبط بعناصر أخرى",

    # ══════════════════════════════════════════════
    # عناصر مشتركة
    # ══════════════════════════════════════════════
    "shared_items":  "العناصر المشتركة",
    "publish":       "نشر",
    "published":     "منشور",
    "not_published": "غير منشور",

    # ══════════════════════════════════════════════
    # العملة والوحدات
    # ══════════════════════════════════════════════
    "currency_abbr":          "جنيه",
    "currency_sym":           "ج",   # اختصار الجنيه للعرض المضغوط
    "amount_fmt":             "{amount:.2f}  ج",     # تنسيق المبلغ
    "amount_disc_fmt":        "{amount:.2f}  ج  ({pct:.1f}%)",  # مبلغ + نسبة خصم
    "currency":               "جنيه",
    "currency_per_piece":     "جنيه / قطعة",
    "currency_per_hour":      "جنيه / ساعة",
    "currency_per_unit":      "جنيه / وحدة",
    "piece":                  "قطعة",
    "minutes_abbr":           "د",

    # ══════════════════════════════════════════════
    # المنتجات
    # ══════════════════════════════════════════════
    "new_product":              "منتج جديد",
    "product_name_placeholder": "اسم المنتج...",
    "saved_products":           "المنتجات المحفوظة",
    "products_table_title":     "─── المنتجات المحفوظة ───",
    "no_products":              "لا توجد منتجات",
    "enter_product_name":       "أدخل اسم المنتج أولاً",
    "add_one_component":        "أضف مكوناً واحداً على الأقل",
    "product_name":             "اسم المنتج",
    "add_component":            "مكون",
    "edit_selected_btn":        "✏️ تعديل المحدد",
    "delete_selected_btn":      "🗑️ حذف المحدد",
    "editing_product_label":          "تعديل: {name}",
    "editing_product_orphans_label":  "تعديل: {name}  {count} مكون ناقص",
    "orphans_deleted_title":          "تم",
    "orphans_deleted_with_product_title": "تم — وتم حذف المنتج",
    "orphans_deleted_msg":            "✅ تم حذف {count} مكوّن ناقص:\n{names}",
    "orphans_deleted_product_removed_msg": "✅ تم حذف {count} مكوّن ناقص:\n{names}\n\nبما أن «{product_name}» لم يعد يحتوي على أي مكونات،\nتم حذفه تلقائياً.",

    # ══════════════════════════════════════════════
    # المكونات / BOM
    # ══════════════════════════════════════════════
    "element":            "العنصر",
    "row_or_variant":     "الصف / الـ variant",
    "qty":                "الكمية",
    "waste_pct_col":      "هادر %",
    "effective_qty":      "الكمية الفعلية",
    "component_scenario": "المكون / السيناريو",
    "total_cost":         "التكلفة الكلية",

    # ══════════════════════════════════════════════
    # BOM Tree
    # ══════════════════════════════════════════════
    "bom_tree":                        "هيكل BOM",
    "expand_all":                      "فتح الكل",
    "collapse_all":                    "إغلاق الكل",
    "delete_selected":                 "حذف المحدد",
    "default_scenario":                "سيناريو افتراضي",
    "delete_from_scenario":            "حذف",
    "from_scenario":                   "من السيناريو",
    "bom_delete_from_scenario_msg":    "{node_name} من السيناريو «{sc_name}»",
    "delete_sub_components_from_semi": "احذف المكونات الفرعية من المنتج النصف مصنع نفسه",

    # ── BOM Tree — node السيناريو ──────────────────────
    "bom_scenario_default_suffix":     "  (افتراضي)",
    "bom_scenario_star_icon":          "⭐ ",
    "bom_scenario_normal_icon":        "📋 ",

    # ── BOM Tree — node المكوّن (tooltips) ──────────────
    "bom_tooltip_qty_entered":         "الكمية المدخلة: {qty}",
    "bom_tooltip_waste":               "هادر {pct} %\nالكمية الفعلية = {qty} × (1 + {pct}/100) = {eff_qty}",
    "bom_tooltip_effective_qty":       "الكمية الفعلية = {eff_qty}",
    "bom_tooltip_unit_cost":           "تكلفة الوحدة: {cost}",
    "bom_tooltip_total_cost":          "التكلفة الكلية = {unit_cost} × {eff_qty} = {total_cost}",
    "bom_tooltip_machine_op_row_cost": "تكلفة الصف المحدد (ID:{row_id}): {cost}",
    "bom_qty_no_value":                "—",
    "bom_type_label_raw":              "🧱 {label}",
    "bom_type_label_semi":             "🔧 {label}",
    "bom_type_label_labor_op":         "👷 {label}",
    "bom_type_label_machine_op":       "⚙️ {label}",

    # ══════════════════════════════════════════════
    # السيناريوهات
    # ══════════════════════════════════════════════
    "scenario":                    "السيناريو",
    "add_scenario":                "إضافة سيناريو",
    "clone_scenario":              "استنساخ السيناريو",
    "rename_scenario":             "إعادة تسمية",
    "set_as_default":              "تعيين كافتراضي",
    "new_scenario":                "سيناريو جديد",
    "new_scenario_name":           "اسم السيناريو الجديد",
    "scenario_name":               "اسم السيناريو",
    "default_scenario_initial_name": "سيناريو 1",
    "new_name":                    "الاسم الجديد",
    "copy_of":                     "نسخة من",
    "cannot_delete_last_scenario": "لا يمكن حذف السيناريو الوحيد",
    "delete_scenario_confirm":     "هل تريد حذف السيناريو",
    "delete_scenario_confirm_msg": "هل تريد حذف السيناريو «{name}»؟",
    "delete_scenario_failed":      "فشل حذف السيناريو",
    "select_scenario":             "اختر سيناريو",

    # ══════════════════════════════════════════════
    # مقارنة السيناريوهات
    # ══════════════════════════════════════════════
    "scenario_comparison":        "مقارنة السيناريوهات",
    "compare_scenario":           "مقارنة مع",
    "default_scenario_cost":      "تكلفة الافتراضي",
    "compare_scenario_cost":      "تكلفة المقارن",
    "cost_diff":                  "فرق التكلفة",
    "fixed_price":                "السعر الثابت",
    "default_scenario_profit":    "ربح الافتراضي",
    "compare_scenario_profit":    "ربح المقارن",
    "profit_diff":                "فرق الربح",
    "compare_profit_margin":      "هامش ربح المقارن",
    "select_scenario_to_compare": "اختر سيناريو للمقارنة",
    "compare_higher_cost":        "تكلفة أعلى بـ",
    "profit_decreases":           "الربح ينخفض بـ",
    "compare_lower_cost":         "تكلفة أقل بـ",
    "profit_increases":           "الربح يرتفع بـ",
    "equal_cost_scenarios":       "السيناريوان متساويان في التكلفة",
    "select_product_to_compare":  "اختر منتجاً لبدء المقارنة",

    # ══════════════════════════════════════════════
    # الاستبدال الشامل
    # ══════════════════════════════════════════════
    "operation_required":     "العملية المطلوبة",
    "replace_element":        "استبدال العنصر",
    "edit_qty_only":          "تعديل الكمية فقط",
    "both_operations":        "الاثنين معاً",
    "replacement_raw":        "الخامة البديلة",
    "replacement_labor_op":   "عملية العمالة البديلة",
    "replacement_machine_op": "عملية التشغيل البديلة",
    "replacement":            "البديل",
    "select_replacement":     "اختر البديل",
    "no_alternatives":        "لا توجد بدائل",
    "apply_uniform_qty":      "تطبيق كمية موحدة",
    "filter_by_category":     "فلتر بالتصنيف",
    "select_all":             "الكل",
    "select_none":            "لا شيء",
    "invert_selection":       "عكس",
    "no_products_linked":     "لا توجد منتجات مرتبطة بهذا العنصر",
    "quick_select":           "تحديد سريع",
    "apply_to_selected":      "تطبيق على المحدد",
    "bulk_replace_window_title":     "🔄  استبدال / تعديل شامل",
    "bulk_replace_header_title":     "استبدال شامل  —  {name}",
    "select_at_least_one_product":   "اختر منتجاً واحداً على الأقل",
    "select_replacement_first":      "اختر العنصر البديل أولاً\nأو اختر «تعديل الكمية فقط» لو لا تريد الاستبدال.",
    "bulk_replace_desc_line":        "•  استبدال  «{old}»  بـ  «{new}»",
    "bulk_set_qty_desc_line":        "•  تعيين الكمية = {qty}",
    "bulk_keep_qty_desc_line":       "•  الاحتفاظ بالكمية المعدَّلة لكل منتج",
    "bulk_apply_confirm_msg":        "سيتم تطبيق التالي على {count} منتج:\n\n{ops}\n\nهل تريد المتابعة؟",
    "confirm_apply_title":           "تأكيد التطبيق",
    "bulk_completed_with_errors_title": "اكتمل مع أخطاء",
    "bulk_completed_success_msg":    "✅ تم تحديث {count} منتج بنجاح",
    "bulk_completed_with_errors_msg":   "✅ تم تحديث {updated} منتج بنجاح\n\n⚠️ فشل {failed} منتج:\n{errors}",

    # ══════════════════════════════════════════════
    # صفوف عمليات التشغيل
    # ══════════════════════════════════════════════
    "op_rows_editor":              "صفوف العملية",
    "add_row":                     "إضافة صف",
    "edit_row":                    "تعديل الصف",
    "delete_row":                  "حذف الصف",
    "row_description_placeholder": "وصف الصف...",
    "value_minutes":               "القيمة (دقائق)",
    "time_minutes":                "الوقت (دقائق)",
    "units":                       "الوحدات",
    "value":                       "القيمة",
    "count":                       "العدد",
    "total_op_cost":               "إجمالي تكلفة العملية",
    "select_row_first":            "اختر صفاً أولاً",
    "min_one_row_required":        "يجب وجود صف واحد على الأقل",
    "calc_mode":                   "وضع الحساب",
    "by_time":                     "بالوقت",
    "by_unit":                     "بالوحدة",
    "rate":                        "المعدل",

    # ══════════════════════════════════════════════
    # Variants الخامة
    # ══════════════════════════════════════════════
    "raw_variants":                "وحدات الإنتاج (Variants)",
    "variant_description_line1":   "كل variant يُعرِّف عدد القطع الناتجة من وحدة الخامة",
    "variant_unit_cost_formula":   "سعر الوحدة = السعر الكلي ÷ عدد القطع",
    "variant_name_placeholder":    "اسم الـ variant...",
    "pieces_count":                "عدد القطع",
    "pieces_tooltip_line1":        "عدد القطع الناتجة من وحدة الخامة",
    "add_variant":                 "إضافة variant",
    "enter_variant_name":          "أدخل اسم الـ variant",
    "select_variant_first":        "اختر variant أولاً",
    "delete_variant_confirm":      "هل تريد حذف الـ variant",
    "delete_variant_confirm_msg":  "هل تريد حذف الـ variant «{name}»؟",
    "currency_per_piece_short":    "جنيه/قطعة",

    # ══════════════════════════════════════════════
    # الخامات
    # ══════════════════════════════════════════════
    "raw_materials": "الخامات",
    "no_raws":       "لا توجد خامات",
    "saved_raws":    "الخامات المحفوظة",
    "raw_select_first":              "اختر خامة من الجدول أولاً",
    "raw_bulk_replace_btn":          "🔄 استبدال شامل",
    "raw_edit_shared_btn":           "🔗 تعديل المشترك",
    "raw_publish_btn":               "📤 نشر كمشترك",
    "raw_bulk_replace_not_available":"الاستبدال الشامل غير متاح للعناصر المشتركة.",
    "shared_item_title":             "عنصر مشترك",
    "raw_shared_edit_notice":        "هذه خامة مشتركة واردة — استخدم زر «🔗 تعديل المشترك» لتعديلها.",
    "raw_shared_delete_blocked":     "لا يمكن حذف خامة مشتركة من هنا.\nاستخدم نافذة «العناصر المشتركة» لحذفها أو فك الربط.",
    "raw_col_id":                    "ID",
    "raw_col_name":                  "الاسم",
    "raw_col_category":              "التصنيف",
    "raw_col_total_price":           "السعر الكلي",
    "raw_col_qty":                   "الكمية",
    "raw_col_unit_price":            "سعر الوحدة",

    # ══════════════════════════════════════════════
    # العمالة
    # ══════════════════════════════════════════════
    "labor_ops": "عمليات العمالة",

    # ══════════════════════════════════════════════
    # التشغيل
    # ══════════════════════════════════════════════
    "machine_ops": "عمليات التشغيل",

    # ══════════════════════════════════════════════
    # إعدادات تكلفة العمالة
    # ══════════════════════════════════════════════
    "labor_cost_settings":    "إعدادات تكلفة العمالة",
    "base_salary":            "الراتب الأساسي",
    "working_days":           "أيام العمل",
    "holiday_days":           "أيام الإجازة",
    "working_hours_per_day":  "ساعات العمل / يوم",
    "overhead_factor":        "معامل التحميل",
    "hourly_rate":            "معدل الأجر / ساعة",
    "save_labor_settings":    "حفظ إعدادات العمالة",
    "labor_settings_saved":   "تم حفظ إعدادات العمالة",

    # ══════════════════════════════════════════════
    # أسماء تبويبات الأقسام
    # ══════════════════════════════════════════════

    # Costing tabs
    "raw_tab":        "الخامات",
    "labor_tab":      "العمالة",
    "machine_tab":    "التشغيل",
    "product_tab":    "المنتجات",
    "categories_tab": "التصنيفات",

    # Accounting tabs
    "accounts_tab":   "شجرة الحسابات",
    "journal_tab":    "القيود المحاسبية",
    "ledger_tab":     "دفتر الأستاذ",
    "financial_tab":  "القوائم المالية",
    "investors_tab":  "المستثمرون",

    # Inventory tabs
    "inventory_items":          "أصناف المخزون",
    "inventory_items_tab":      "الأصناف",
    "inventory_inbound_tab":    "الوارد",
    "inventory_outbound_tab":   "الصادر",
    "inventory_report_tab":     "التقرير",
    "low_stock_alert":          "تنبيه مخزون منخفض",
    "avg_unit_cost":            "متوسط سعر الوحدة",
    "total_inbound_value":      "إجمالي قيمة الوارد",
    "total_outbound_value":     "إجمالي قيمة الصادر",

    # Orders tabs
    "orders_tab":    "الطلبات",
    "customers_tab": "العملاء",
    "dashboard_tab": "لوحة التحكم",

    # Design tabs
    "designs_tab":           "التصميمات",
    "dimension_sets_tab":    "مجموعات الأبعاد",
    "design_categories_tab": "تصنيفات التصميم",

    # Pricing tabs
    "pricing_tab": "التسعير",
    "offers_tab":  "العروض",

    # ══════════════════════════════════════════════
    # التطبيق
    # ══════════════════════════════════════════════
    "app_title":         "نظام إدارة التكاليف",
    "app_title_company": "نظام إدارة التكاليف — {name}",
    "under_development": "قيد التطوير",

    # ══════════════════════════════════════════════
    # قسم التكلفة وتبويباته
    # ══════════════════════════════════════════════
    "costing_section":    "حساب التكلفة",
    "final_product":      "منتج نهائي",
    "labor":              "العمالة",
    "machine":            "التشغيل",
    "machines":           "الماكينات",
    "machine_operations": "عمليات التشغيل",
    "labor_settings":     "إعدادات العمالة",
    "labor_operations":   "عمليات العمالة",

    # ══════════════════════════════════════════════
    # رسائل المنتجات
    # ══════════════════════════════════════════════
    "select_product_first":     "اختر منتجاً من الجدول أولاً",
    "select_product_to_delete": "اختر منتجاً أولاً",
    "delete_orphan_components": "حذف الناقص",

    # ══════════════════════════════════════════════
    # فورم الماكينة — مفاتيح جديدة
    # ══════════════════════════════════════════════
    "machine_form_title":         "بيانات الماكينة",
    "machine_name":               "اسم الماكينة",
    "machine_name_placeholder":   "مثال: ماكينة خياطة، فرن، مكبس...",
    "machine_name_required":      "أدخل اسم الماكينة",
    "rate_per_hour":              "معدل التشغيل / ساعة",
    "rate_per_unit":              "معدل التشغيل / وحدة",
    "add_machine_new":            "إضافة ماكينة جديدة",
    "editing_prefix":             "تعديل",
    "enter_name":                 "أدخل الاسم",
    "currency_per_hour_short":    "ج/س",
    "currency_per_unit_short":    "ج/و",
    "machines_table_title":       "─── الماكينات المحفوظة ───",

    # ══════════════════════════════════════════════
    # فورم عملية التشغيل — مفاتيح جديدة
    # ══════════════════════════════════════════════
    "machine_op_form_title":      "بيانات عملية التشغيل",
    "machine_op_name_placeholder": "مثال: خياطة غرزة، كبس...",
    "add_machine_op_new":         "إضافة عملية تشغيل جديدة",
    "add_op":                     "إضافة عملية",
    "op_name":                    "اسم العملية",
    "machine_label":              "الماكينة",
    "select_machine_first":       "اختر ماكينة أولاً",
    "add_op_first_hint":          "أضف العملية أولاً لتظهر الصفوف",
    "mode_time_label":            "⏱ بالوقت",
    "mode_unit_label":            "📦 بالوحدة",
    "calc_mode_label":            "طريقة الحساب",
    "machine_mode_tooltip":       "طريقة احتساب تكلفة الماكينة: بالوقت أو بالوحدة",
    "total_cost_label":           "إجمالي التكلفة",
    "op_added_success":           "تمت إضافة العملية «{name}»\nأضف الصفوف الآن ثم اضغط «حفظ التعديل»",
    "editing_rows_prefix":        "تعديل صفوف",
    "enter_op_name":              "أدخل اسم العملية",
    "machine_op_table_title":     "─── عمليات التشغيل المحفوظة ───",
    "mode_col":                   "الطريقة",
    "value_col":                  "القيمة",
    "cost_col":                   "التكلفة",
    "time_mode_short":            "⏱ وقت",
    "unit_mode_short":            "📦 وحدة",

    # ══════════════════════════════════════════════
    # فورم عملية العمالة — مفاتيح جديدة
    # ══════════════════════════════════════════════
    "labor_op_form_title":        "بيانات العملية",
    "time_label":                 "الوقت",
    "cost_label":                 "التكلفة",
    "minutes_label":              "دقيقة",
    "labor_op_name_placeholder":  "مثال: خياطة، تغليف...",
    "labor_op_table_title":       "─── عمليات العمالة المحفوظة ───",
    "cost_per_unit_col":          "التكلفة / وحدة",

    # ══════════════════════════════════════════════
    # فورم الخامة — مفاتيح جديدة
    # ══════════════════════════════════════════════
    "raw_form_title":             "بيانات الخامة",
    "raw_add_btn":                "➕  إضافة خامة",
    "raw_name_label":             "اسم الخامة",
    "raw_name_required":          "أدخل اسم الخامة...",
    "raw_price_label":            "السعر الكلي",
    "raw_qty_label":              "الكمية الإجمالية",
    "raw_qty_unit":               "وحدة",
    "raw_qty_tooltip":            "اتركه صفراً لو السعر بالوحدة\nسعر الوحدة = السعر الكلي ÷ الكمية الإجمالية",
    "raw_hint_with_qty":          "💡 سعر الوحدة = {price} ÷ {qty} = {unit} جنيه/وحدة",
    "raw_hint_qty_only":          "💡 سعر الوحدة = السعر الكلي ÷ الكمية الإجمالية",
    "raw_hint_no_qty":            "💡 بدون كمية إجمالية: السعر المسجل = سعر الوحدة مباشرة",
    "raw_add_variants_mode":      "أضف وحدات إنتاج لـ: {name}",

    # ══════════════════════════════════════════════
    # دفتر الأستاذ
    # ══════════════════════════════════════════════
    "ledger":                  "دفتر الأستاذ",
    "t_account":               "حساب T",
    "normal_balance_dr":       "طبيعة مدينة (DR↑)",
    "normal_balance_cr":       "طبيعة دائنة (CR↑)",

    # ══════════════════════════════════════════════
    # فورم القيد
    # ══════════════════════════════════════════════
    "journal_balanced":        "✅ متوازن — يمكن الحفظ",
    "journal_unbalanced":      "⚠️ غير متوازن",
    "add_journal_line":        "➕  إضافة صف",
    "journal_lines_title":     "📋  صفوف القيد",
    "journal_increase":        "زيادة ✚",
    "journal_decrease":        "نقص ✖",
    "entry_type_manual":       "📝 يدوي",
    "entry_type_opening":      "🟢 افتتاحي",
    "entry_type_closing":      "🔴 ختامي",
    "entry_type_transfer":     "🔄 ترحيل",
    "select_account":          "— اختر الحساب —",
    "select_journal_first":    "اختر قيداً أولاً",
    "journal_saved_success":   "✅ تم حفظ القيد بنجاح",
    "no_dr_line":              "لا يوجد أي صف مدين (DR)",
    "no_cr_line":              "لا يوجد أي صف دائن (CR)",
    "entry_description_placeholder": "وصف القيد الإجمالي...",
    "line_description_placeholder":  "بيان...",
    "balance_bar_diff":        "الفرق:",
    "balance_bar_add_rows":    "○ أضف صفوف",
    "entry_save_btn":          "💾  حفظ القيد",
    "entry_clear_btn":         "✖  مسح",
    "new_journal_entry":       "── قيد يومية جديد ──",

    # ══════════════════════════════════════════════
    # Audit Log
    # ══════════════════════════════════════════════
    "audit_log_delete":        "🗑️ حذف",
    "audit_log_update":        "✏️ تعديل",
    "audit_log_create":        "➕ إضافة",
    "audit_detail_title":      "تفاصيل العملية",
    "old_data":                "البيانات القديمة",
    "changed_by":              "بواسطة",
    "no_audit_records":        "لا توجد سجلات",
    "no_audit_yet":            "لم يُسجَّل أي عملية حتى الآن",
    "audit_all_tables":        "— كل الجداول —",
    "audit_all_types":         "— كل الأنواع —",

    # ══════════════════════════════════════════════
    # المستثمرون
    # ══════════════════════════════════════════════
    "investor_capital_badge":  "💰 رأس مال",
    "investor_drawings_badge": "💸 مسحوبات",
    "initial_capital":         "رأس المال الأولي",
    "capital_account":         "حساب رأس المال",
    "deposit_account":         "حساب الإيداع",
    "payment_account":         "حساب الصرف",
    "link_investor_to_entry":  "🔗  ربط بقيد محاسبي",
    "link_success":            "✅ تم ربط القيد بالمستثمر بنجاح",
    "investor_join_date":      "تاريخ الانضمام",
    "investor_new":            "مستثمر جديد",
    "select_investor":         "اختر المستثمر",
    "investor_movements":      "─── الحركات المالية ───",
    "delete_movement_title":   "تأكيد حذف الحركة",
    "delete_movement_msg":     "حذف {type} (قيد {ref})؟\n\n⚠️ سيتم حذف الحركة من سجل المستثمر وحذف القيد من الحسابات.",
    "investor_list_title":     "─── المستثمرون ───",
    "add_capital_title":       "💰  إضافة رأس مال",
    "add_drawings_title":      "💸  تسجيل مسحوبات",
    "expected_entry":          "القيد المتوقع:",
    "link_entry_info":         "🔗  ربط قيد محاسبي موجود بمستثمر\nاستخدم هذا لو أضفت القيد يدوياً في تبويب القيود وتريد نسبته لمستثمر.",
    "entry_ref_placeholder":   "مثال: JE-00012",
    "link_entry_btn":          "🔗  ربط",

    # ══════════════════════════════════════════════
    # Pagination
    # ══════════════════════════════════════════════
    "load_more":               "تحميل {count} إضافي  ▼",
    "show_all_records":        "عرض الكل",
    "showing_records":         "يعرض {shown:,} من {total:,}",
    "showing_all_records":     "يعرض كل {shown:,} سجل",

    # ══════════════════════════════════════════════
    # شريط الحالة والفلاتر
    # ══════════════════════════════════════════════
    "group_filter":            "🏷 التصنيف:",
    "balance_status_filter":   "الحالة:",
    "all_groups":              "— كل التصنيفات —",
    "balanced_filter":         "✅ متوازن",
    "unbalanced_filter":       "⚠️ غير متوازن",
    "move_type_all":           "كل الحركات",
    "move_type_dr":            "مدين فقط",
    "move_type_cr":            "دائن فقط",
    "clear_filters":           "↺ مسح الفلاتر",
    "entry_date_label":        "التاريخ:",
    "entry_type_label":        "النوع:",
    "entry_desc_label":        "الوصف:",

    # ══════════════════════════════════════════════
    # رسائل الحسابات
    # ══════════════════════════════════════════════
    "account_has_lines_msg":   "الحساب «{name}» أو أحد فروعه\nله {count} حركة في القيود — لا يمكن حذفه.",
    "delete_failed_msg":       "فشل الحذف:\n{error}",
    "select_category_first":   "اختر تصنيفًا أولًا",
    "sub_accounts_delete_warning": "⚠️ سيتم حذف {count} حساب فرعي معه.",

    # ══════════════════════════════════════════════
    # تبويبات قسم الحسابات
    # ══════════════════════════════════════════════
    "assets_tab":              "🏦  الأصول",
    "liabilities_tab":         "📋  الخصوم",
    "equity_tab":              "👑  حقوق الملكية",
    "capital_tab":             "👑 رأس المال",
    "drawings_tab":            "💸 المسحوبات",
    "revenue_tab":             "💹 الإيرادات",
    "expense_tab":             "📤 المصروفات",
    "income_statement_tab":    "📊 قائمة الدخل",
    "owners_equity_tab":       "👑 حقوق الملكية",
    "balance_sheet_tab":       "🏛️ الميزانية العمومية",
    "trial_balance_tab":       "⚖️ ميزان المراجعة",

    # ══════════════════════════════════════════════
    # شجرة الحسابات وإدارة التصنيفات
    # ══════════════════════════════════════════════
    "no_accounts_msg":         "لا توجد حسابات — أضف من الفورم على اليمين",
    "group_categories_header": "تصنيفات {type_name}",
    "group_add_edit_header":   "➕ إضافة / تعديل تصنيف {type_name}",
    "group_new_placeholder":   "تصنيف جديد",
    "group_name_placeholder":  "اسم التصنيف...",
    "group_parent_label":      "تابع لـ:",
    "group_color_label":       "اللون:",
    "group_without_parent":    "— بدون أب (رئيسي) —",
    "group_default_color":     "#607d8b",
    "accounts_col":            "الكود",
    "account_name_col":        "اسم الحساب",
    "group_count_col":         "عدد الحسابات",
    "group_tree_col":          "التصنيف",
    "group_tag_icon":          "🏷",
    "all_types_label":         "— كل التصنيفات —",
    "all_accounts_label":      "— كل التصنيفات —",

    # ══════════════════════════════════════════════
    # account_combo
    # ══════════════════════════════════════════════
    "select_account_combo":    "— اختر الحساب —",
    "all_types_combo":         "— كل التصنيفات —",
    "dr_badge":                "DR↑",
    "cr_badge":                "CR↑",

    # ══════════════════════════════════════════════
    # رسائل حالة الاتصال والتحميل
    # ══════════════════════════════════════════════
    "conn_error_msg":          "❌  خطأ في الاتصال بقاعدة البيانات:\n{error}",
    "init_failed_msg":         "❌  تعذّر تهيئة قاعدة بيانات المحاسبة\nجرّب إعادة تشغيل البرنامج أو تحديد الشركة مجدداً",
    "loading_db_msg":          "⏳  جاري تهيئة قاعدة البيانات... ({attempt}/{max})",
    "group_filter_tooltip":    "فلتر بالتصنيف",
    "search_placeholder":      "🔍 بحث...",

    # ══════════════════════════════════════════════
    # جدول الحركات المالية (_details_table)
    # ══════════════════════════════════════════════
    "movement_type_col":       "النوع",
    "movement_amount":         "المبلغ",
    "movement_desc":           "البيان",
    "capital_movement":        "💰 رأس مال",
    "drawings_movement":       "💸 مسحوبات",

    # ══════════════════════════════════════════════
    # تفاصيل المستثمر (_investor_details)
    # ══════════════════════════════════════════════
    "investor_detail_placeholder": "اختر مستثمراً لعرض تفاصيله",
    "total_capital":           "إجمالي رأس المال",
    "total_drawings":          "إجمالي المسحوبات",
    "net_investment":          "صافي الاستثمار",
    "investor_movements_header": "─── الحركات المالية ───",
    "delete_movement_btn":     "🗑️  حذف الحركة المحددة",
    "select_movement_first":   "اختر حركة أولاً",
    "investor_joined":         "انضم",

    # ══════════════════════════════════════════════
    # فورم المستثمر (_investor_form)
    # ══════════════════════════════════════════════
    "investor_data_header":    "بيانات المستثمر",
    "investor_name_placeholder": "اسم المستثمر...",
    "initial_capital_header":  "💰  رأس المال الأولي (اختياري)",
    "amount_label":            "المبلغ:",
    "capital_account_label":   "حساب رأس المال:",
    "deposit_account_label":   "حساب الإيداع:",
    "expected_entry_label":    "القيد:",
    "enter_amount_preview":    "─ أدخل مبلغاً لعرض القيد",
    "enter_investor_name":     "أدخل اسم المستثمر",
    "add_investor_btn":        "➕  إضافة مستثمر",
    "investor_added_failed_entry": "تم إضافة المستثمر لكن فشل القيد:\n{error}",

    # ══════════════════════════════════════════════
    # جدول المستثمرين (_investors_table)
    # ══════════════════════════════════════════════
    "investor_name_col":       "الاسم",
    "join_date_col":           "تاريخ الانضمام",
    "capital_col":             "رأس المال",
    "drawings_col":            "المسحوبات",
    "net_col":                 "صافي الاستثمار",
    "add_investment_btn":      "💰  إضافة استثمار",
    "select_investor_first":   "اختر مستثمراً أولاً",

    # ══════════════════════════════════════════════
    # نافذة الحركة (_movement_dialog)
    # ══════════════════════════════════════════════
    "capital_account_row":     "حساب رأس المال:",
    "drawings_account_row":    "حساب المسحوبات:",
    "payment_account_label":   "حساب الصرف (أصل):",
    "deposit_account_row":     "حساب الإيداع (أصل):",
    "enter_amount_warning":    "أدخل مبلغاً أكبر من صفر",
    "select_accounts_warning": "اختر الحسابات المطلوبة",
    "record_btn":              "✅  تسجيل",

    # ══════════════════════════════════════════════
    # لوحة الربط (_link_to_entry_panel)
    # ══════════════════════════════════════════════
    "link_data_header":        "بيانات الربط",
    "move_type_label":         "نوع الحركة:",
    "ref_no_label":            "رقم القيد:",
    "investor_not_found":      "اختر المستثمر",
    "entry_not_found":         "لم يُعثر على قيد برقم «{ref}»",
    "enter_ref_no":            "أدخل رقم القيد",
    "enter_positive_amount":   "أدخل مبلغاً أكبر من صفر",

    # ══════════════════════════════════════════════
    # تبويبات المستثمرين (_investors_layout)
    # ══════════════════════════════════════════════
    "investors_tab_title":     "👥  المستثمرون",
    "link_to_entry_tab_title": "🔗  ربط بقيد محاسبي",

    # ══════════════════════════════════════════════
    # الميزانية العمومية (balance_sheet_tab)
    # ══════════════════════════════════════════════
    "balance_sheet_title":     "الميزانية العمومية",
    "balance_sheet_balanced":  "✅ متوازنة",
    "total_assets":            "إجمالي الأصول",
    "total_liabilities":       "إجمالي الخصوم",
    "equity_label":            "حقوق الملكية",
    "assets_section":          "🏦 الأصول",
    "liabilities_equity_section": "📋 الخصوم وحقوق الملكية",
    "liabilities_label":       "خصوم",
    "capital_label_bs":        "رأس المال",
    "drawings_bs":             "مسحوبات",
    "net_income_bs":           "صافي الدخل",
    "equity_type_col":         "النوع",
    "balance_sheet_diff":      "⚠️ فرق: {diff}",

    # ══════════════════════════════════════════════
    # قائمة الدخل (income_statement_tab)
    # ══════════════════════════════════════════════
    "income_statement_title":  "قائمة الدخل",
    "total_revenues":          "إجمالي الإيرادات",
    "total_expenses":          "إجمالي المصروفات",
    "net_profit_loss":         "صافي الربح / الخسارة",
    "revenues_section":        "💹 الإيرادات",
    "expenses_section":        "📤 المصروفات",

    # ══════════════════════════════════════════════
    # قائمة حقوق الملكية (owners_equity_tab)
    # ══════════════════════════════════════════════
    "owners_equity_title":     "قائمة حقوق الملكية",
    "net_income_col":          "صافي الدخل",
    "drawings_label":          "المسحوبات",
    "net_equity":              "صافي حقوق الملكية",
    "equity_increases":        "📈 ما يزيد حقوق الملكية (CR↑)",
    "equity_decreases":        "📉 ما ينقص حقوق الملكية (DR↑)",
    "net_income_row":          "صافي الدخل للفترة",
    "income_minus_expenses":   "إيرادات - مصروفات",
    "equity_equation":         "رأس المال  {capital}  +  صافي الدخل  {net_income}  −  المسحوبات  {drawings}  =  صافي حقوق الملكية  {total}",

    # ══════════════════════════════════════════════
    # ميزان المراجعة (trial_balance_tab)
    # ══════════════════════════════════════════════
    "trial_balance_title":     "ميزان المراجعة",
    "trial_balance_legend":    "🔵 مدين (الرصيد الطبيعي DR)     🔴 دائن (الرصيد الطبيعي CR)    — القيمة تُعرض دائماً موجبة",
    "balance_col":             "الرصيد",
    "dr_balance":              "مدين",
    "cr_balance":              "دائن",
    "account_code_col":        "الكود",
    "type_col":                "النوع",
    "total_debit_col":         "مجموع المدين",
    "total_credit_col":        "مجموع الدائن",
    "balance_balanced":        "✅ الميزان متوازن",
    "balance_diff":            "⚠️ فرق: {diff}",
    "sum_debit_label":         "مجموع المدين: {val}",
    "sum_credit_label":        "مجموع الدائن: {val}",

    # ══════════════════════════════════════════════
    # أعمدة مشتركة للجداول
    # ══════════════════════════════════════════════
    "item_col":                "البند",
    "link_no_col":             "ID",

    # ══════════════════════════════════════════════
    # وصف قيود المستثمرين (helpers)
    # ══════════════════════════════════════════════
    "capital_entry_desc":   "رأس مال — {name}  {amount} {currency}",
    "drawings_entry_desc":  "مسحوبات — {name}  {amount} {currency}",

    # ══════════════════════════════════════════════
    # جدول القيود (journal_tree_table)
    # ══════════════════════════════════════════════
    "journal_table_title":         "── القيود المحاسبية المحفوظة ──",
    "journal_expand_all":          "⊞ توسيع الكل",
    "journal_collapse_all":        "⊟ طي الكل",
    "journal_delete_selected":     "🗑️  حذف المحدد",
    "journal_search_placeholder":  "بحث في الوصف أو رقم القيد...",
    "journal_status_balanced":     "✅ متوازن",
    "journal_status_unbalanced":   "⚠️ {diff}",
    "select_entry_first":          "اختر قيداً أولاً",
    "entry_type_auto":             "🤖 تلقائي",
    "journal_unbalanced_detail":   "⚠️  غير متوازن ({side} بـ {diff})",
    "dr_bigger":                   "DR أكبر",
    "cr_bigger":                   "CR أكبر",
    "add_at_least_one_line":       "أضف صفاً واحداً على الأقل",
    "balance_error_title":         "خطأ في التوازن",
    "balance_error_msg":           "مجموع DR ({dr}) ≠ مجموع CR ({cr})",

    # ══════════════════════════════════════════════
    # صفوف القيد (_lines_panel, _smart_line)
    # ══════════════════════════════════════════════
    "lines_col_account":           "الحساب",
    "lines_col_direction":         "الاتجاه",
    "lines_col_amount":            "المبلغ",
    "lines_col_desc":              "البيان",
    "investor_link_label":         "👤  ربط بمستثمر:",
    "investor_link_optional":      "(اختياري)",
    "investor_no_link":            "— لا يوجد ربط —",
    "journal_filter_all_statuses": "الكل",
    "journal_count_label":         "({count} قيد)",
    "journal_count_filtered":      "({shown} / {total})",
    "popup_hint_select":           "اضغط مرتين أو Enter للاختيار",
    "account_search_placeholder":  "🔍 بحث بالاسم أو الكود...",

    # ══════════════════════════════════════════════════════════════════
    # المخزن
    # ══════════════════════════════════════════════════════════════════
    "inventory_purchase_success":  "✅ تم تسجيل الاستلام وإنشاء قيد محاسبي",
    "inventory_supplier_keyword":   "مورد",
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
    "inventory_item_data_group":    "بيانات الصنف",
    "inventory_item_new_mode":      "─── صنف جديد ───",
    "edit_mode_fmt":                "─── تعديل: {name} ───",
    "inventory_item_name_placeholder": "اسم الصنف...",
    "inventory_qty_min_tooltip":    "الكمية الدنيا للتنبيه بالطلب",
    "inventory_raw_item_fmt":       "🧱 {name}",
    "inventory_default_account_placeholder": "— حساب المخزون الافتراضي —",
    "notes_placeholder":            "ملاحظات...",
    "inventory_add_item":           "إضافة صنف",
    "item":                         "الصنف",
    "inventory_select_item_placeholder": "— اختر الصنف —",
    "entry_no_col":                 "رقم القيد",
    "id_col":                       "ID",
    "avg_cost":                     "متوسط التكلفة",
    "total_value":                  "إجمالي القيمة",
    "inventory_below_min_tooltip":  "⚠️ تحت الحد الأدنى ({min})",
    "inventory_outbound_save":      "تسجيل الصرف",
    "inventory_inbound_save":       "تسجيل الاستلام + قيد محاسبي",
    "statement_col":                "البيان",
    "inventory_total_items_card":   "عدد الأصناف",
    "inventory_total_value_card":   "إجمالي قيمة المخزن",
    "inventory_low_stock_card":     "أصناف تحت الحد الأدنى",
    "inventory_zero_stock_card":    "أصناف نفدت",
    "inventory_detailed_report_header": "─── تقرير مخزن تفصيلي ───",
    "inventory_status_out":         "❌ نفد",
    "inventory_status_low":         "⚠️ منخفض",
    "inventory_status_ok":          "✅ متوفر",
    "inventory_select_item_for_moves": "اختر صنفاً لعرض حركاته",
    "inventory_item_moves_title_fmt": "📦  حركات: {name}  (رصيد: {qty} {unit})",
    "move_type_in":                 "📥 وارد",
    "move_type_out":                "📤 صادر",
    "move_type_adjust":             "⚖️ تسوية",

    # ══════════════════════════════════════════════════════════════════
    # التسعير
    # ══════════════════════════════════════════════════════════════════
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

    "offer_name_required":          "أدخل اسم العرض أولاً",
    "offer_product_required":       "أضف منتجاً واحداً على الأقل",
    "offer_cancel_btn":             "✖  إلغاء",
    "offer_header_search":          "بحث",
    "offer_header_total_col":       "إجمالي",
    "offer_item_final_icon":        "🏭 {name}",
    "offer_item_semi_icon":         "🔧 {name}",
    "offer_no_price_tooltip":       "هذا المنتج ليس له سعر في التسعير",
    "offer_cost_lbl":               "تكلفة:",
    "offer_price_lbl":              "سعر:",
    "offer_times_sym":              "×",
    "offer_equals_sym":             "=",
    "offer_min_one_product":        "أضف منتجاً واحداً على الأقل",
    "offer_name_placeholder":       "مثال: عرض رمضان، باقة العيد...",
    "offer_notes_placeholder":      "اختياري...",
    "offer_name_field":             "اسم العرض:",
    "offer_discount_field":         "الخصم:",
    "offer_category_field":         "التصنيف:",
    "offer_notes_field":            "ملاحظات:",
    "offer_row_search_hdr":         "بحث",
    "offer_row_product_hdr":        "المنتج",
    "offer_row_cost_hdr":           "تكلفة/و",
    "offer_row_price_hdr":          "سعر/و",
    "offer_row_qty_hdr":            "الكمية",
    "offer_row_total_hdr":          "إجمالي",
    "offer_row_cost_label":         "تكلفة:",
    "offer_row_price_label":        "سعر:",
    "offer_row_multiply_sign":      "×",
    "offer_row_equals_sign":        "=",
    "offer_row_unit_cost_tooltip":  "تكلفة الإنتاج / وحدة",
    "offer_row_unit_price_tooltip": "سعر التسعير / وحدة",
    "offer_row_no_pricing_tooltip": "هذا المنتج ليس له سعر في التسعير",
    "offer_row_line_total_tooltip": "إجمالي سعر السطر قبل الخصم",
    "offer_details_notes_prefix":   "📝 {notes}",
    "offer_details_title":          "📋  {name}  —  خصم {discount:.1f}%  │  {created_at}{category}",
    "offer_details_category_part":  "  │  🏷 {category}",
    "offer_col_count":              "عدد المنتجات",
    "offer_col_discount_pct":       "خصم %",
    "offer_col_total_listed":       "إجمالي السعر",
    "offer_col_sell_price":         "سعر البيع",
    "offer_col_cost":               "التكلفة",
    "offer_col_profit":             "الربح",
    "offer_col_date":               "التاريخ",
    "pricing_select_product_table": "اختر منتجاً من الجدول أولاً",
    "pricing_edit_selected_btn":    "✏️  تعديل المحدد",
    "pricing_save_price_btn":       "💾  حفظ السعر",
    "pricing_delete_price_btn":     "🗑️  حذف السعر",
    "pricing_cost_suffix":          "{cost:.2f}  ج (تكلفة)",
    "pricing_margin_pct_sign":      "%",
    "pricing_select_product_placeholder": "— اختر منتجاً —",
    "pricing_col_id":               "ID",
    "pricing_col_product":          "المنتج",
    "pricing_col_category":         "التصنيف",
    "pricing_col_cost":             "التكلفة",
    "pricing_col_margin_pct":       "الهامش %",
    "pricing_col_price":            "السعر",
    "pricing_col_profit":           "الربح",
    "pricing_col_margin_actual_pct":"هامش فعلي %",
    "pricing_amount_currency_fmt":  "{amount:.2f}  ج",

    # ══════════════════════════════════════════════════════════════════
    # الشركات والعناصر المشتركة
    # ══════════════════════════════════════════════════════════════════
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
    "shared_publish_title":         "📤  نشر عنصر كمشترك",
    "shared_name_colon":            "الاسم:",
    "shared_exists_title":          "عنصر موجود",
    "shared_exists_msg":            "يوجد عنصر مشترك باسم «{name}» بالفعل.\nهل تريد استخدامه بدلاً من إنشاء نسخة جديدة؟",
    "without_value":                "─ بدون",
    "dash":                         "—",
    "companies_manage_title":       "🏢  إدارة الشركات",
    "company_col_name":             "الاسم",
    "company_col_short":            "الاختصار",
    "company_col_status":           "الحالة",
    "company_col_actions":          "إجراءات",
    "company_tooltip_edit":         "تعديل",
    "company_tooltip_toggle":       "إيقاف / تفعيل",
    "company_tooltip_delete":       "حذف",
    "company_pick_color_title":     "اختر لون الشركة",
    "company_name_required":        "اسم الشركة مطلوب",
    "shared_item_not_found":        "⚠️  العنصر غير موجود",
    "no_companies_available":       "— لا توجد شركات —",
    "link_item_from":               "—  من: {company}",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — تبويب مجموعات المقاسات (orchestrator)
    # ══════════════════════════════════════════════════════════════════
    "dimension_sets_tab_values":    "📏  إدخال المقاسات",
    "dimension_sets_tab_groups":    "📋  المجموعات",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — Source Picker
    # ══════════════════════════════════════════════════════════════════
    "dim_src_picker_title":         "اختيار مصدر الحساب التلقائي",
    "dim_src_picker_header":        "اختر مجموعة القيم المصدر",
    "dim_src_picker_from_group":    "من مجموعة",
    "dim_src_picker_field":         "الحقل",
    "dim_src_picker_hint":          "اختر مجموعة القيم اللي هيتحسب منها الحقل",
    "dim_src_picker_no_values":     "لا توجد قيم محفوظة في هذه المجموعة",
    "dim_src_picker_apply":         "✓  تطبيق الحساب",
    "dim_src_picker_no_value_short": "لا توجد قيمة",
    "dim_src_preview_fmt":          "✓  {name}:  {val}  {sign}  =  {result}  {unit}",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — تصنيفات مجموعات المقاسات
    # ══════════════════════════════════════════════════════════════════
    "dim_cat_panel_title":          "📁  تصنيفات التصميمات",
    "dim_cat_col_name":             "التصنيف",
    "dim_cat_col_count":            "عدد المجموعات",
    "dim_cat_new_mode":             "─── تصنيف جديد ───",
    "dim_cat_edit_mode":            "─── تعديل: {name} ───",
    "dim_cat_no_parent":            "— بدون أب (رئيسي) —",
    "dim_cat_pick_color":           "اختر لون",
    "dim_cat_pick_color_title":     "اختر لون التصنيف",
    "dim_cat_has_children_warn":    "⚠️ يحتوي على {count} تصنيف فرعي — سيتم حذفها.",
    "dim_cat_has_sets_warn":        "⚠️ {count} مجموعة مقاسات ستفقد تصنيفها.",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — لوحة مجموعات المقاسات
    # ══════════════════════════════════════════════════════════════════
    "dim_sets_panel_title":         "📐  مجموعات المقاسات",
    "dim_sets_search_placeholder":  "🔍 بحث باسم المجموعة...",
    "dim_sets_all_categories":      "— كل التصنيفات —",
    "dim_sets_col_id":              "ID",
    "dim_sets_col_name":            "اسم المجموعة",
    "dim_sets_col_category":        "التصنيف",
    "dim_sets_col_unit":            "الوحدة",
    "dim_sets_col_fields":          "عدد الحقول",
    "dim_sets_form_title":          "بيانات المجموعة",
    "dim_sets_new_mode":            "─── مجموعة جديدة ───",
    "dim_sets_edit_mode":           "─── تعديل: {name} ───",
    "dim_sets_name_placeholder":    "مثال: مقاسات الثوب، مقاسات البنطلون...",
    "dim_sets_default_unit_label":  "الوحدة الافتراضية",
    "dim_sets_add_btn":             "➕  إضافة مجموعة",
    "dim_sets_fields_header":       "📋  حقول المجموعة المختارة",
    "dim_sets_linked_designs_warn": "المجموعة «{name}» مرتبطة بـ {count} تصميم.\nاحذف الارتباط من التصميمات أولاً.",
    "dim_sets_has_fields_warn":     "⚠️ تحتوي على {count} حقل — سيتم حذفها جميعاً.",
    "dim_sets_delete_blocked_title": "تعذر الحذف",
    "dim_sets_delete_confirm_title": "تأكيد الحذف",
    "dim_sets_delete_confirm_msg":   "حذف مجموعة «{name}»؟",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — Instance Popup (إدخال القيم)
    # ══════════════════════════════════════════════════════════════════
    "dim_inst_dlg_new_title":       "إضافة مجموعة قيم جديدة",
    "dim_inst_dlg_edit_title":      "تعديل مجموعة قيم",
    "dim_inst_hdr_new":             "➕  إضافة مجموعة قيم جديدة",
    "dim_inst_hdr_edit":            "✏️  تعديل القيم",
    "dim_inst_name_label":          "الاسم:",
    "dim_inst_name_placeholder":    "مثال: A4، مقاس L، النموذج الأول...",
    "dim_inst_values_label":        "القيم:",
    "dim_inst_no_numeric_fields":   "هذه المجموعة ليس لها حقول رقمية.",
    "dim_inst_calc_all_btn":        "⟳  حساب الكل تلقائياً",
    "dim_inst_auto_tooltip":        "حساب تلقائي من المصدر",
    "dim_inst_no_source_value":     "لا توجد قيمة للحقل المصدر بعد.\nأدخل قيمة المصدر في هذه المجموعة أولاً.",
    "dim_inst_no_cross_value":      "لا توجد قيمة للحقل المصدر في المجموعة المختارة.\nأدخل القيمة في مجموعة القيم المصدر أولاً.",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — حقول المجموعة
    # ══════════════════════════════════════════════════════════════════
    "dim_field_panel_title":            "حقول المجموعة",
    "dim_field_col_order":              "الترتيب",
    "dim_field_col_name_en":            "الاسم",
    "dim_field_col_label":              "التسمية",
    "dim_field_col_unit":               "الوحدة",
    "dim_field_col_type":               "النوع",
    "dim_field_col_required":           "إلزامي",
    "dim_field_col_depends":            "يعتمد على",
    "dim_field_type_number":            "رقم",
    "dim_field_type_text":              "نص",
    "dim_field_add_btn":                "➕  إضافة حقل",
    "dim_field_select_first":           "اختر حقلاً أولاً",
    "dim_field_move_up":                "▲",
    "dim_field_move_down":              "▼",
    "dim_field_dlg_new_title":          "إضافة حقل جديد",
    "dim_field_dlg_edit_title":         "تعديل حقل",
    "dim_field_name_en_label":          "الاسم (إنجليزي)",
    "dim_field_name_en_placeholder":    "مثال: length, width ...",
    "dim_field_label_ar_label":         "التسمية (عربي)",
    "dim_field_label_ar_placeholder":   "مثال: الطول، العرض ...",
    "dim_field_required_check":         "حقل إلزامي",
    "dim_field_dep_group_title":        "اعتماد على حقل من مجموعة مقاسات (اختياري)",
    "dim_field_source_set_label":       "المجموعة المصدر",
    "dim_field_source_field_label":     "الحقل المصدر",
    "dim_field_offset_label":           "إضافة / خصم",
    "dim_field_preview_label":          "المعاينة",
    "dim_field_same_set_prefix":        "← نفس المجموعة: {name}",
    "dim_field_select_source_set":      "— اختر مجموعة مقاسات —",
    "dim_field_no_numeric_fields":      "— لا توجد حقول رقمية —",
    "dim_field_dep_hint":               "القيمة = قيمة الحقل المصدر + الإضافة (سالب للخصم)",
    "dim_field_preview_no_value":       "لا توجد قيمة محفوظة بعد في المجموعة المصدر",
    "dim_field_name_required":          "أدخل الاسم والتسمية",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — قايمة مجموعات المقاسات
    # ══════════════════════════════════════════════════════════════════
    "dim_sets_list_title":              "📐  مجموعات المقاسات",
    "dim_sets_list_search":             "🔍  بحث...",
    "dim_sets_list_all_cats":           "كل التصنيفات",
    "dim_sets_list_count_all":          "{count} مجموعة",
    "dim_sets_list_count_filtered":     "{shown} من {total} مجموعة",
    "dim_sets_card_hint":               "💡 لإضافة أو تعديل المجموعات والتصنيفات — اذهب لتبويب «المجموعات»",
    "dim_sets_card_field_suffix":       "{count} حقل",
    "dim_sets_badge_values":            "{count} قيمة",
    "dim_sets_empty_select_title":      "اختر مجموعة مقاسات من القايمة",
    "dim_sets_empty_select_hint":       "اضغط على أي مجموعة من القايمة على اليسار",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — جدول قيم المقاسات
    # ══════════════════════════════════════════════════════════════════
    "dim_unnamed_set_fallback":         "مجموعة #{id}",
    "dim_inst_table_placeholder":       "اختر مجموعة مقاسات من القايمة",
    "dim_inst_table_status":            "{count} مجموعة قيم  ·  انقر مرتين للتعديل",
    "dim_inst_add_btn":                 "➕  إضافة قيمة",
    "dim_inst_edit_btn":                "✏️  تعديل",
    "dim_inst_copy_btn":                "📋  نسخ",
    "dim_inst_delete_confirm":          "حذف «{name}» وكل قيمها؟",
    "dim_inst_copy_title":              "نسخ مجموعة القيم",
    "dim_inst_copy_label":              "اسم النسخة الجديدة:",
    "dim_inst_copy_default":            "{name} (نسخة)",
    "dim_inst_col_name":                "الاسم",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — نافذة إضافة/تعديل مقاس
    # ══════════════════════════════════════════════════════════════════
    "design_size_dlg_new_title":        "إضافة مقاس جديد",
    "design_size_dlg_edit_title":       "تعديل مقاس",
    "design_size_set_label":            "مجموعة المقاسات",
    "design_size_instance_label":       "المقاس",
    "design_size_width_label":          "حقل العرض",
    "design_size_height_label":         "حقل الطول",
    "design_size_dpi_label":            "حقل الدقة (DPI)",
    "design_size_canvas_label":         "مقاس الكانفاس",
    "design_size_gimp_path_label":      "مسار ملف GIMP",
    "design_size_gimp_browse_tooltip":  "اختر ملف .xcf موجود",
    "design_size_select_set":           "─ اختر مجموعة مقاسات ─",
    "design_size_select_instance":      "─ اختر مقاساً ─",
    "design_size_select_width":         "─ اختر حقل العرض ─",
    "design_size_select_height":        "─ اختر حقل الطول ─",
    "design_size_select_dpi":           "─ اختياري: حقل الدقة (DPI) ─",
    "design_size_canvas_no_dpi":        "{w} × {h} {unit}  (حدد حقل DPI لحساب الـ px)",
    "design_size_canvas_with_dpi":      "{w} × {h} {unit}  →  {w_px} × {h_px} px  @  {dpi} DPI",
    "design_size_canvas_incomplete":    "⚠️  القيم غير مكتملة في هذا المقاس",
    "design_size_canvas_dash":          "─",
    "design_size_gimp_placeholder":     "مسار ملف .xcf — اتركه فارغاً لإنشاء ملف جديد",
    "design_size_choose_set":           "اختر مجموعة مقاسات",
    "design_size_choose_instance":      "اختر المقاس",
    "design_size_already_used":         "هذا المقاس مضاف بالفعل لهذا التصميم",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — بطاقة المقاس
    # ══════════════════════════════════════════════════════════════════
    "design_size_card_fallback_name":       "مقاس #{id}",
    "design_size_card_open_gimp_btn":       "فتح في GIMP",
    "design_size_card_create_gimp_btn":     "إنشاء في GIMP",
    "design_size_card_link_file_btn":       "ربط ملف",
    "design_size_card_file_exists":         "الملف موجود",
    "design_size_card_file_missing":        "الملف غير موجود",
    "design_size_card_file_none":           "لا يوجد ملف",
    "design_size_card_file_not_found_msg":  "الملف:\n{path}\n\nاستخدم «ربط ملف» لتحديث المسار.",
    "design_size_card_create_canvas_title": "إنشاء كانفاس",
    "design_size_card_create_canvas_msg":   "الأبعاد: {w} × {h} {unit}\nالبكسل: {w_px} × {h_px} px  @  {dpi} DPI\nالملف: {path}",
    "design_size_card_save_gimp_title":     "اختر مكان حفظ ملف GIMP",
    "design_size_card_link_file_title":     "اختر ملف GIMP موجود",
    "design_size_card_gimp_filter":         "GIMP Files (*.xcf);;All Files (*)",
    "design_size_card_dims_unknown":        "الأبعاد غير محددة",
    "design_size_card_dims_no_dpi":         "{w} × {h} {unit}",
    "design_size_card_dims_with_dpi":       "{w} × {h} {unit}  →  {w_px} × {h_px} px",
    "design_size_card_missing_gimp":        "GIMP غير موجود.\nحدد مساره من ⚙️ الإعدادات.",
    "design_size_card_pillow_missing":      "تحتاج تثبيت Pillow:\n\npip install Pillow",
    "design_size_card_open_failed":         "فشل فتح GIMP:\n{error}",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — قائمة التصميمات وبطاقاتها
    # ══════════════════════════════════════════════════════════════════
    "design_table_new_btn":                 "تصميم جديد  +",
    "design_table_set_filter_label":        "المجموعة:",
    "design_table_all_sets":                "كل المجموعات",
    "design_table_reset_filters_btn":       "↺  مسح",
    "design_table_count":                   "{count} تصميم",
    "design_table_empty_no_designs":        "لا توجد تصميمات",
    "design_table_empty_start":             "اضغط «تصميم جديد» للبدء",
    "design_table_empty_no_results":        "لا توجد نتائج",
    "design_table_empty_change_criteria":   "جرّب تغيير معايير البحث",
    "design_table_search_placeholder":      "بحث بالاسم...",
    "design_card_size_badge_tooltip":       "{count} مقاس",
    "design_card_status_all_files":         "✓  {count}/{total} ملف",
    "design_card_status_partial_files":     "⚡  {count}/{total} ملف",
    "design_card_status_no_files":          "○  {count} مقاس — بدون ملفات",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — لوحة تفاصيل التصميم
    # ══════════════════════════════════════════════════════════════════
    "design_detail_new_badge":          "جديد",
    "design_detail_saved_badge":        "محفوظ",
    "design_detail_new_title":          "تصميم جديد",
    "design_detail_new_btn":            "جديد",
    "design_detail_save_btn":           "حفظ التصميم",
    "design_detail_name_label":         "الاسم",
    "design_detail_name_placeholder":   "اسم التصميم...",
    "design_detail_category_label":     "التصنيف",
    "design_detail_notes_label":        "ملاحظات",
    "design_detail_notes_placeholder":  "اختياري...",
    "design_detail_sizes_section":      "المقاسات",
    "design_detail_add_size_btn":       "+ إضافة مقاس",
    "design_detail_save_first_warn":    "احفظ التصميم أولاً قبل إضافة مقاسات",
    "design_detail_no_sizes_title":     "لا توجد مقاسات بعد",
    "design_detail_no_sizes_hint":      "اضغط «+ إضافة مقاس» لإضافة أول مقاس",
    "design_detail_delete_size_confirm": "حذف هذا المقاس من التصميم؟",
    "design_detail_name_required":      "أدخل اسم التصميم",
    "design_detail_no_category":        "— بدون تصنيف —",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — تصنيفات التصميمات (Sidebar)
    # ══════════════════════════════════════════════════════════════════
    "design_cats_panel_title":          "التصنيفات",
    "design_cats_add_tooltip":          "تصنيف جديد",
    "design_cats_all":                  "كل التصميمات",
    "design_cats_search_placeholder":   "بحث في التصنيفات...",
    "design_cats_edit_btn":             "تعديل",
    "design_cats_delete_btn":           "حذف",
    "design_cats_new_form_title":       "تصنيف جديد",
    "design_cats_edit_form_title":      "تعديل: {name}",
    "design_cats_name_placeholder":     "اسم التصنيف...",
    "design_cats_parent_label":         "تابع لـ:",
    "design_cats_color_label":          "اللون:",
    "design_cats_pick_color_btn":       "اختر لون",
    "design_cats_save_btn":             "حفظ",
    "design_cats_cancel_btn":           "إلغاء",
    "design_cats_no_parent":            "— بدون أب —",
    "design_cats_has_children_warn":    "⚠️ {count} تصنيف فرعي سيُحذف.",
    "design_cats_has_designs_warn":     "⚠️ {count} تصميم سيفقد تصنيفه.",

}
