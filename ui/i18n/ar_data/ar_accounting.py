"""
ui/i18n/ar_data/accounting.py
========================
نصوص قسم المحاسبة (دفتر الأستاذ، القيود، الميزانيات، المستثمرون، Audit Log)
جزء من تقسيم ui/i18n/ar.py — راجع ui/i18n/ar/__init__.py.
"""

AR_STRINGS_ACCOUNTING: dict[str, str] = {
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
    "account_form_new":          "── حساب جديد ──",
    "account_form_edit":         "── تعديل: {name} ──",
    "account_form_enter_code_name": "أدخل الكود والاسم",
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
    # دفتر الأستاذ
    # ══════════════════════════════════════════════
    "ledger":                  "دفتر الأستاذ",
    "t_account":               "حساب T",
    "normal_balance_dr":       "طبيعة مدينة (DR↑)",
    "normal_balance_cr":       "طبيعة دائنة (CR↑)",
    "ledger_accounts_title":      "📚  الحسابات",
    "ledger_search_placeholder":  "بحث في البيان أو رقم القيد...",
    "ledger_select_account_prompt": "اختر حسابًا من القائمة لعرض حركاته",
    "t_account_dr_header":     "📥  مدين  (DR)",
    "t_account_cr_header":     "📤  دائن  (CR)",
    "t_account_total":         "{label}: {amount}",
    "t_account_summary":       "{code} — {name}  │  {type}  │  رصيد طبيعي: {nb}",
    "ledger_movements_count":  "عدد الحركات",
    "ledger_normal_balance_card": "الرصيد الطبيعي",
    "ledger_card_nb_dr":       "مدين (DR↑)",
    "ledger_card_nb_cr":       "دائن (CR↑)",
    "ledger_nb_short_dr":      "DR↑",
    "ledger_nb_short_cr":      "CR↑",

    # ══════════════════════════════════════════════
    # فورم القيد
    # ══════════════════════════════════════════════
    "journal_balanced":        "✅ متوازن — يمكن الحفظ",
    "journal_unbalanced":      "⚠️ غير متوازن",
    "add_journal_line":        "➕  إضافة صف",
    "journal_lines_title":     "📋  صفوف القيد",
    "journal_dr_total":        "DR: {amount}",
    "journal_cr_total":        "CR: {amount}",
    "journal_dr_col":          "DR",
    "journal_cr_col":          "CR",
    "journal_increase":        "زيادة ✚",
    "journal_decrease":        "نقص ✖",
    "entry_type_manual":        "📝 يدوي",
    "entry_type_opening":       "🟢 افتتاحي",
    "entry_type_closing":       "🔴 ختامي",
    "entry_type_transfer":      "🔄 ترحيل",
    "entry_type_manual_short":  "يدوي",
    "entry_type_opening_short": "افتتاحي",
    "entry_type_closing_short": "ختامي",
    "entry_type_transfer_short":"ترحيل",
    "entry_type_auto_short":    "تلقائي",
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

    "audit_log_header_title":       "🔍  سجل العمليات",
    "audit_table_filter_label":     "الجدول:",
    "audit_meta_line":              "الجدول: {table}  ·  رقم السجل: {record_id}  ·  بواسطة: {changed_by}",
    "audit_col_index":              "#",
    "audit_col_type":               "النوع",
    "audit_col_table":              "الجدول",
    "audit_col_record_id":          "رقم السجل",
    "audit_col_date":               "التاريخ",
    "audit_table_journal_entries":  "القيود المحاسبية",
    "audit_table_journal_lines":    "بنود القيود",
    "audit_table_accounts":         "الحسابات",
    "audit_table_inventory_moves":  "حركات المخزون",
    "audit_table_investor_entries": "قيود المستثمرين",
    "group_delete_accounts_warn":   "⚠️ {count} حساب سيفقد تصنيفه.",

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
    "accounting_no_company_msg": "⚠️  اختر شركة أولاً لعرض الحسابات",
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
    "investor_title_fmt":      "👤  {name}  │  {joined_label}: {date}",

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
    # entry_type_auto_short مُعرَّف أعلاه ضمن مجموعة entry_type_*_short
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
    "account_group_unassigned":    "─── بدون تصنيف ───",
    "account_code_placeholder":    "1141",
    "account_name_placeholder":    "اسم الحساب...",
    "account_tree_type_header":    "── {type} ──",
    "account_node_tooltip_with_group": "{name}  |  🏷 {group}",

    # ══════════════════════════════════════════════════════════════════
    # المكوّنات المشتركة — AmountLabel / DebitCreditDisplay / BalanceDisplay
    # ══════════════════════════════════════════════════════════════════
    "amount_dash_placeholder":          "─",
    "dr_total_label":                   "إجمالي DR:",
    "cr_total_label":                   "إجمالي CR:",
    "amount_zero_placeholder":          "0.00",
    "vertical_separator":               "│",
    "slash_separator":                  "/",
    "info_row_separator":               "  ·  ",
    "mode_label_wrap":                  "─── {content} ───",
    "balance_with_side":                " ({side_label})",
    "balance_dash":                     "الرصيد: ─",
    "progress_zero_pct":                "0%",
    "spinner_loading_text":             "جارٍ التحميل...",
    "spinner_done_check":               "✓",
    "loading_button_saving_text":       "جارٍ الحفظ...",
    "notif_icon_success":                "✅",
    "notif_icon_info":                   "ℹ️",
    "notif_icon_warning":                "⚠️",
    "notif_icon_danger":                 "❌",
    "dismiss_icon":                      "✖",
    "icon_edit_pencil":                  "✏️",
    "icon_delete_trash":                 "🗑️",
    "icon_save_disk":                    "💾",
    "warning_bar_fix_text":              "🗑️ حذف الناقص",
    "warning_bar_edit_text":             "✏️ تعديل",
    "warning_bar_icon":                  "⚠️",
    "orphan_type_raw":                   "خامة",
    "orphan_type_semi":                  "نصف مصنع",
    "orphan_type_labor_op":              "عملية عمالة",
    "orphan_type_machine_op":            "عملية تشغيل",
    "orphan_line_item":                  "• {type_label}: «{name}»",
    "orphans_warning_msg":               "«{product_name}» — {count} مكوّن محذوف:\n{lines}",

    # ── ColorPickerWidget ──────────────────────────────────
    "color_picker_btn":   "اختر لون",
    "color_picker_title": "اختر لون",

    # ── CategoryManager ────────────────────────────────────
    "category_tree_arrow": "↳ ",

    # ── FilterToolbar ──────────────────────────────────────
    "filter_reset_btn":         "↺",
    "filter_reset_tooltip":     "مسح الكل",
    "filter_cat_icon":          "🏷",
    "filter_date_icon":         "📅",

    # ── CollapsibleCard ────────────────────────────────────
    "collapsible_arrow_expanded":  "▼",
    "collapsible_arrow_collapsed": "▶",

    # ── InlinePreview / DataTable ──────────────────────────
    "inline_preview_label": "النتيجة:",
    "empty_icon_search":    "🔍",
    "empty_icon_table":     "📋",

    # ── SharedOpsMixin ─────────────────────────────────────
    "shared_item_not_shared_use_edit": "هذا عنصر عادي — استخدم «✏️ تعديل».",

    # ── Asset account icons (fill_asset_combo) ─────────────
    "asset_icon_bank":  "🏦",
    "asset_icon_cash":  "💵",
    "asset_icon_other": "📦",

    # ── Movement Dialog icons ───────────────────────────────
    "movement_icon_capital":  "💰",
    "movement_icon_drawings": "💸",

    # ── Investor icon ────────────────────────────────────────
    "investor_icon":          "👤",

    # ── CompanySelector / CompaniesDialog icons ─────────────
    "company_selector_icon":  "🏢",
    "company_selector_manage_icon": "⚙",
    "shared_item_linked_icon":      "🔗",
    "shared_linked_company_icon":   "✅",
    "shared_unlinked_company_icon": "○",
    "shared_company_prefix":        "🏢 ",
    "company_manage_icon":    "⚙",
    "company_edit_icon":      "✏",
    "company_toggle_pause":   "⏸",
    "company_toggle_play":    "▶",
    "company_delete_icon":    "🗑",

    # ── AccountTreePopup icons ──────────────────────────────
    "account_tree_equity_icon": "👑",
    "account_tree_group_icon":  "🏷",
    "account_tree_default_icon": "📁",

    # ── AccountTreePopup type icons ──────────────────────────
    "account_tree_icon_asset":     "🏦",
    "account_tree_icon_liability": "📋",
    "account_tree_icon_capital":   "👑",
    "account_tree_icon_drawings":  "💸",
    "account_tree_icon_revenue":   "💹",
    "account_tree_icon_expense":   "📤",

    # ── AccountTreePopup tree toggles / separators ───────────
    "tree_toggle_expanded":   "▼",
    "tree_toggle_collapsed":  "▶",
    "account_code_name_sep":  " — ",

    # ── _JournalTreeTable — prefixes / separators ─────────
    "journal_tree_entry_prefix": "    └─ ",
    "journal_tree_desc_sep":     "  │  ",

    # ── AccountsTreePanel — equity sub-type separator ──────
    "accounts_tree_sub_type_wrap": "── {name} ──",

}
