"""
ui/i18n/ar_data/design.py
====================
نصوص قسم التصميمات (مجموعات المقاسات، المقاسات، التصنيفات)
جزء من تقسيم ui/i18n/ar.py — راجع ui/i18n/ar/__init__.py.
"""

AR_STRINGS_DESIGN: dict[str, str] = {
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
    "dim_field_move_up_btn":            "⬆️",
    "dim_field_move_down_btn":          "⬇️",
    "dim_field_required_yes":           "✓",
    "dim_cat_zero_sets":                "—",
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
    "dim_sets_meta_separator":          "  ·  ",
    "dim_sets_badge_values":            "{count} قيمة",
    "dim_sets_empty_select_title":      "اختر مجموعة مقاسات من القايمة",
    "dim_sets_empty_select_hint":       "اضغط على أي مجموعة من القايمة على اليسار",
    "dim_sets_list_default_unit":       "سم",

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
    "dim_inst_dlg_new_title":           "إضافة قيمة جديدة",
    "dim_inst_dlg_edit_title":          "تعديل القيمة",
    "dim_inst_hdr_new":                 "➕  إضافة قيمة جديدة",
    "dim_inst_hdr_edit":                "✏️  تعديل القيمة",
    "dim_inst_name_label":              "الاسم",
    "dim_inst_name_placeholder":        "اسم المجموعة...",
    "dim_inst_values_label":            "القيم",
    "dim_inst_auto_tooltip":            "احسب تلقائياً من المجموعة المصدر",
    "dim_inst_no_numeric_fields":       "لا توجد حقول رقمية في هذه المجموعة",
    "dim_inst_no_source_value":         "لا توجد قيمة محفوظة في المجموعة المصدر",
    "dim_inst_no_cross_value":          "لا توجد قيمة في الحقل المصدر المختار",
    "dim_inst_calc_all_btn":            "⟳  احسب الكل تلقائياً",
    "dim_inst_save_btn":                "💾  حفظ",
    "dim_inst_auto_icon":               "⟳",
    "dim_inst_empty_icon":              "📋",
    "dim_sets_set_icon":                "📐",
    "dim_sets_card_no_category":        "—",
    "dim_value_empty":                  "—",

    # ══════════════════════════════════════════════════════════════════
    # وحدة التصميمات — نافذة إضافة/تعديل مقاس
    # ══════════════════════════════════════════════════════════════════
    "design_size_dlg_new_title":        "إضافة مقاس جديد",
    "design_size_dlg_edit_title":       "تعديل مقاس",
    "design_size_dlg_header_icon":      "📐  ",
    "design_size_gimp_browse_icon":     "📂",
    "design_size_dlg_save_btn":         "💾  حفظ",
    "design_size_dlg_cancel_btn":       "✖  إلغاء",
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
    "design_size_card_edit_icon":           "✏",
    "design_size_card_delete_icon":         "🗑",
    "design_size_card_dpi_chip":            "{dpi} DPI",
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
    "design_card_thumb_placeholder_icon":   "🎨",
    "design_size_card_thumb_no_file_icon":  "📄",

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
    "design_cats_add_icon":             "+",
    "design_table_empty_icon":          "🎨",
    "design_detail_no_sizes_icon":      "📐",
    "design_detail_cat_arrow":          "↳ ",

}
