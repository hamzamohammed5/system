"""
ui/i18n/ar_data/costing.py
=====================
نصوص قسم حساب التكلفة (BOM، المنتجات، الخامات، العمالة، الماكينات، السيناريوهات)
جزء من تقسيم ui/i18n/ar.py — راجع ui/i18n/ar/__init__.py.
"""

AR_STRINGS_COSTING: dict[str, str] = {
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
    "component_type_raw":        "🧱 خامة",
    "component_type_semi":       "🔧 نصف مصنع",
    "component_type_labor_op":   "👷 عملية عمالة",
    "component_type_machine_op": "⚙️ عملية تشغيل",

    # ══════════════════════════════════════════════
    # ComponentRow (صف المكوّن في BOM)
    # ══════════════════════════════════════════════
    "component_row_orphan_display":   "⚠️  {name_part}محذوف  (ID: {item_id})",
    "component_row_orphan_tooltip":   "⚠️ هذا المكون ({type_}{name_part} ID:{item_id}) تم حذفه من قاعدة البيانات.\nاختر بديلاً من القائمة أو احذف هذا الصف.",
    "component_row_orphan_name_part": " «{name}»",
    "component_row_cost_tooltip":     "سعر الوحدة: {unit_cost}\nالسعر الإجمالي: {price}{total_qty_line}",
    "component_row_total_qty_line":   "\nالكمية الكلية: {total_qty}",
    "op_row_fallback_label":          "صف {id}",
    "op_row_cost_suffix":             "= {cost} ج/قطعة",
    "op_row_combo_approx_cost":       "  ≈ {cost} ج",
    "op_row_combo_fraction":          "({value} ÷ {count})",
    "variant_combo_tooltip":          "وحدة الإنتاج — تكلفة الوحدة = سعر الخامة ÷ عدد القطع",
    "waste_spin_tooltip":             "نسبة الهادر %\nمثال: 10% → الكمية الفعلية = الكمية × 1.10",
    "total_qty_placeholder":          "الكلي",
    "total_qty_tooltip":              "الكمية الكلية للخامة.",
    "divide_symbol":                  "÷",
    "sub_row_label":                  "↳ صف العملية:",
    "variant_combo_none":             "─ بدون variant ─",
    "variant_combo_item_priced":      "📐 {name}  ({pieces} قطعة → {unit_cost} ج/قطعة)",
    "variant_combo_item_plain":       "📐 {name}  ({pieces} قطعة)",
    "variant_cost_suffix":            "= {cost} ج",
    "waste_icon":                     "⚠️",
    "component_row_remove_btn":       "❌",
    "waste_spin_suffix":              " %",

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
    'component_row_no_items_placeholder': 'لا توجد {type_label} مسجلة',

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

    # ── BOM Tree — header & button icons ─────────────
    "bom_tree_header_icon":            "🔩 ",
    "bom_tree_expand_icon":            "⊞ ",
    "bom_tree_collapse_icon":          "⊟ ",
    "bom_tree_del_icon":               "🗑 ",
    "bom_tree_warning_icon":           "⚠️",
    "bom_tree_star_icon":              "⭐",
    "bom_tree_multiply_sign":          "×",
    "preview_eq_dash":                 "= ─",

    # ── BOM Tree — node السيناريو ──────────────────────
    "bom_scenario_default_suffix":     "  (افتراضي)",
    "bom_scenario_star_icon":          "⭐ ",
    "bom_scenario_normal_icon":        "📋 ",

    # ── _BomScenariosPanel icons ──────────────────
    "scenarios_panel_target_icon":     "🎯",
    "scenarios_panel_star_badge":      "⭐ ",
    "scenarios_panel_btn_star_icon":   "⭐ ",
    "scenarios_panel_btn_edit_icon":   "✏️ ",
    "scenarios_panel_btn_clone_icon":  "📋 ",
    "scenarios_panel_btn_add_icon":    "➕ ",
    "scenarios_panel_btn_del_icon":    "🗑",

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
    "scenario_comparison_icon":   "📊",
    "scenario_comparison_higher_icon": "⬆",
    "scenario_comparison_lower_icon":  "⬇",
    "positive_sign":              "+",
    "percent_sign":               "%",
    "scenario_combo_placeholder": "─ {label} ─",

    # ══════════════════════════════════════════════
    # الاستبدال الشامل
    # ══════════════════════════════════════════════
    "operation_required":     "العملية المطلوبة",
    "operation_section_title": "⚙️  العملية المطلوبة",
    "replace_element":        "استبدال العنصر",
    "replace_element_btn":    "🔀  استبدال العنصر",
    "edit_qty_only":          "تعديل الكمية فقط",
    "edit_qty_only_btn":      "🔢  تعديل الكمية فقط",
    "both_operations":        "الاثنين معاً",
    "both_operations_btn":    "✅  الاثنين معاً",
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
    "op_rows_editor_icon":         "📋  ",
    "op_rows_time_icon":           "⏱",
    "op_rows_unit_icon":           "📦",
    "op_rows_add_icon":            "➕ ",
    "op_rows_save_icon":           "💾 ",
    "op_rows_edit_icon":           "✏️ ",
    "op_rows_del_icon":            "🗑️ ",
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
    "raw_variants_icon":           "📐  ",
    "raw_variants_info_icon":      "💡 ",
    "raw_variants_add_icon":       "➕ ",
    "raw_variants_save_icon":      "💾 ",
    "raw_variants_edit_icon":      "✏️ ",
    "raw_variants_del_icon":       "🗑️ ",
    "raw_variants_equals_sign":    "= ",
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
    "raw_empty_icon":        "🧱",
    "raw_table_list_title":  "─── الخامات المحفوظة ───",
    "raw_select_first":              "اختر خامة من الجدول أولاً",
    "raw_bulk_replace_btn":          "🔄 استبدال شامل",
    "raw_edit_shared_btn":           "🔗 تعديل المشترك",
    "raw_publish_btn":               "📤 نشر كمشترك",
    "shared_bulk_replace_btn":       "🔄 استبدال شامل",
    "shared_edit_shared_btn":        "🔗 تعديل المشترك",
    "shared_publish_as_shared_btn":  "📤 نشر كمشترك",
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
    'raw_col_actions':   'الإجراءات',      # en: 'Actions'
    'btn_edit_short':    'تعديل',        # en: 'Edit'
    'btn_delete_short':  'حذف',          # en: 'Delete'
    'btn_edit':          'تعديل الخامة', # tooltip
    'btn_delete':        'حذف الخامة',   # tooltip

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
    # قسم التكلفة وتبويباته
    # ══════════════════════════════════════════════
    "costing_section":    "حساب التكلفة",
    "final_product":      "منتج نهائي",
    "labor":              "العمالة",
    "machine":            "التشغيل",
    "machines":           "الماكينات",
    "machines_icon":      "🖥️",
    "machine_operations": "عمليات التشغيل",
    "machine_operations_icon": "⚙️",
    "labor_settings":     "إعدادات العمالة",
    "labor_settings_icon": "⚙️",
    "labor_operations":   "عمليات العمالة",
    "labor_operations_icon": "📋",

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

}
