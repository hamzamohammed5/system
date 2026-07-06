"""
ui/i18n/ar_data/general.py
=====================
نصوص عامة مشتركة (أزرار، تنقل، إعدادات، حالات فارغة، فلاتر، إلخ)
جزء من تقسيم ui/i18n/ar.py — راجع ui/i18n/ar/__init__.py.
"""

AR_STRINGS_GENERAL: dict[str, str] = {
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
    "field_colon":       " :",
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
    "btn_add_op":   "➕  إضافة عملية",
    "btn_add_component": "+  مكون",

    # ── Table shared/published row icons ──────────────────
    "table_shared_icon":      "🔗",
    "table_shared_prefix":    "🔗 ",
    "table_published_icon":   "📤",
    "table_published_prefix": "📤 ",

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

    # ── sidebar — section labels وأيقونات وتبديل ──────────
    "nav_section_production": "الإنتاج",
    "nav_section_finance":    "المالية",
    "nav_section_work":       "العمل",
    "nav_icon_costing":       "📊",
    "nav_icon_pricing":       "💰",
    "nav_icon_accounting":    "🏦",
    "nav_icon_inventory":     "📦",
    "nav_icon_design":        "🎨",
    "nav_icon_orders":        "📋",
    "nav_icon_shared":        "🔗",
    "nav_icon_settings":      "⚙️",
    "tab_icon_raw":           "📦",
    "tab_icon_semi":          "🔧",
    "tab_icon_final":         "🏭",
    "tab_icon_labor":         "👷",
    "tab_icon_machine":       "⚙️",
    "sidebar_collapse_tip":   "طي الشريط الجانبي",
    "sidebar_expand_tip":     "فرد الشريط الجانبي",
    "sidebar_collapse_icon":  "◀",
    "sidebar_expand_icon":    "▶",

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

    # ── إعدادات — عناوين tabs وواجهة ──────────────────────
    "settings_title":            "⚙️  إعدادات",
    "settings_tab_font":         "🔤  الخط",
    "settings_tab_theme":        "🎨  المظهر",
    "settings_tab_lang":         "🌐  اللغة",
    "settings_tab_units":        "📏  الوحدات",
    "settings_tab_gimp":         "🖼️  GIMP",
    "settings_btn_save":         "✅  حفظ",
    "settings_btn_cancel":       "✖  إلغاء",
    "settings_grp_font":         "حجم الخط",
    "settings_font_preview":     "معاينة النص — Preview 123\nأبجد هوز حطي كلمن — The quick brown fox\n١٢٣٤٥٦٧٨٩٠ — ABCDEFG abcdefg",
    "settings_font_hint":        "💡  اضغط حفظ لتطبيق حجم الخط الجديد على كامل الواجهة",
    "settings_grp_theme":        "اختر مظهر التطبيق",
    "settings_grp_theme_preview":"معاينة الألوان",
    "settings_grp_lang":         "اختر لغة الواجهة",
    "settings_lang_hint":        "💡  تغيير اللغة يُطبَّق فوراً بعد الحفظ",
    "settings_grp_units":        "وحدات القياس المتاحة",
    "settings_units_hint":       "💡  الوحدات الافتراضية (باللون الرمادي) لا يمكن حذفها",
    "settings_unit_default_tip": "وحدة افتراضية — لا يمكن حذفها",
    "settings_btn_add_unit":     "➕  إضافة وحدة",
    "settings_btn_del_unit":     "🗑️  حذف المحددة",
    "settings_btn_reset_units":  "↺  استعادة الافتراضية",
    "settings_grp_gimp":         "مسار برنامج GIMP",
    "settings_gimp_hint":        "💡  اتركه فارغاً للبحث التلقائي في المسارات الشائعة",
    "settings_gimp_placeholder": r"مثال: C:\Program Files\GIMP 2\bin\gimp-2.10.exe",
    "settings_btn_browse":       "📂  تصفح",
    "settings_no_company_notice":"⚠️  اختر شركة نشطة لعرض وحدات القياس ومسار GIMP",
    "settings_add_unit_title":   "إضافة وحدة",
    "settings_add_unit_prompt":  "اكتب رمز الوحدة (مثال: ft, yd, pt):",
    "settings_add_unit_label":   "اكتب التسمية الكاملة للوحدة «{val}» (مثال: ft — قدم):",
    "settings_unit_exists":      "الوحدة «{val}» موجودة بالفعل.",
    "settings_select_unit":      "اختر وحدة أولاً",
    "settings_no_del_default":   "لا يمكن حذف الوحدة الافتراضية «{val}».",
    "settings_del_unit_title":   "تأكيد الحذف",
    "settings_del_unit_msg":     "حذف الوحدة «{label}»؟",
    "settings_del_unit_btn":     "حذف",
    "settings_reset_units_title":"استعادة الافتراضية",
    "settings_reset_units_msg":  "حذف كل الوحدات المضافة والرجوع للقائمة الافتراضية؟",
    "settings_reset_units_btn":  "استعادة",
    "settings_warning_title":    "تنبيه",
    "settings_error_title":      "خطأ",
    "settings_no_company_units": "اختر شركة نشطة أولاً لإضافة وحدات قياس",
    "settings_no_company_del":   "اختر شركة نشطة أولاً لحذف وحدات القياس",
    "settings_no_company_reset": "اختر شركة نشطة أولاً لاستعادة الوحدات الافتراضية",
    "settings_browse_gimp":      "اختر ملف GIMP التنفيذي",
    "settings_gimp_filter":      "GIMP (gimp*.exe);;Executable Files (*.exe);;All Files (*)",
    "settings_theme_light_name": "فاتح",
    "settings_theme_light_desc": "خلفية بيضاء دافئة مريحة للعين",
    "settings_theme_dark_name":  "داكن",
    "settings_theme_dark_desc":  "خلفية داكنة للاستخدام الليلي",
    "settings_lang_ar_name":     "العربية",
    "settings_lang_ar_desc":     "واجهة باللغة العربية (RTL)",
    "settings_lang_en_name":     "English",
    "settings_lang_en_desc":     "Interface in English (LTR)",

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
    "empty_icon_default":      "📭",
    "value_dash":              "—",
    "empty_placeholder":       "─",

    # ══════════════════════════════════════════════
    # تأكيد
    # ══════════════════════════════════════════════
    "confirm_delete":       "تأكيد الحذف",
    "confirm_save":         "تأكيد الحفظ",
    "confirm_save_q":       "تأكيد الحفظ؟",
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
    "detail_load_error":    "خطأ في تحميل التفاصيل: {error}",
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
    "combo_clear_search":     "✖",
    "combo_sep_no_category":  "─── بدون تصنيف ───",

    # ══════════════════════════════════════════════
    # عمليات عامة
    # ══════════════════════════════════════════════
    "operation_add":    "إضافة",
    "operation_edit":   "تعديل",
    "operation_delete": "حذف",
    "operation_save":   "حفظ",
    "operation_cancel": "إلغاء",

    # ══════════════════════════════════════════════
    # حذف — رسائل خاصة
    # ══════════════════════════════════════════════
    "delete_has_children":  "لا يمكن الحذف — يحتوي على عناصر فرعية",
    "delete_has_items":     "لا يمكن الحذف — مرتبط بعناصر أخرى",

    # ══════════════════════════════════════════════
    # أسماء تبويبات الأقسام
    # ══════════════════════════════════════════════

    # Costing tabs
    "raw_tab":        "الخامات",
    "labor_tab":      "العمالة",
    "machine_tab":    "التشغيل",
    "product_tab":    "المنتجات",
    "categories_tab": "التصنيفات",
    "categories_tab_icon": "🏷️",

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
    "inventory_section_tab_moves": "الحركات",
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
    # Pagination
    # ══════════════════════════════════════════════
    "load_more":               "تحميل {count} إضافي  ▼",
    "show_all_records":        "عرض الكل",
    "showing_records":         "يعرض {shown:,} من {total:,}",
    "showing_all_records":     "يعرض كل {shown:,} سجل",

}
