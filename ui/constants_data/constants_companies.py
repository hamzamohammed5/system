"""
ui/constants_data/companies.py
=========================
ثوابت قسم الشركات والعناصر المشتركة
جزء من تقسيم ui/constants.py — راجع ui/constants/__init__.py.
"""

# ── PublishAsSharedDialog (_add_shared_item_dialog) ────────
PUBLISH_DLG_BORDER_W        = 1     # عرض border لعناصر PublishAsSharedDialog
PUBLISH_DLG_SPIN_MAX_DEFAULT = 9999999  # الحد الأقصى الافتراضي لـ QDoubleSpinBox في PublishAsSharedDialog
PUBLISH_DLG_SPIN_DEC_DEFAULT = 4    # عدد الخانات العشرية الافتراضي لـ QDoubleSpinBox
PUBLISH_DLG_SPIN_MAX_MINUTES = 9999 # الحد الأقصى لـ spinbox الدقائق (labor_op)
PUBLISH_DLG_SPIN_DEC_MINUTES = 2    # عدد الخانات العشرية لـ spinbox الدقائق
PUBLISH_DLG_MIN_W           = 480   # عرض أدنى لـ PublishAsSharedDialog
PUBLISH_DLG_MIN_H           = 440   # ارتفاع أدنى لـ PublishAsSharedDialog
PUBLISH_DLG_ROOT_SPACING    = 12    # spacing لـ root layout في PublishAsSharedDialog
PUBLISH_DLG_ROOT_MARGIN     = (16, 16, 16, 12)  # contentsMargins لـ root layout
PUBLISH_DLG_HINT_RADIUS     = 6     # border-radius لـ hint label
PUBLISH_DLG_HINT_PAD_V      = 8     # padding عمودي لـ hint label
PUBLISH_DLG_HINT_PAD_H      = 12    # padding أفقي لـ hint label
PUBLISH_DLG_GRP_RADIUS      = 8     # border-radius لـ QGroupBox
PUBLISH_DLG_GRP_PAD_TOP     = 10    # padding-top لـ QGroupBox
PUBLISH_DLG_GRP_MARGIN_TOP  = 6     # margin-top لـ QGroupBox
PUBLISH_DLG_GRP_TITLE_PAD_H = 8     # padding أفقي لعنوان QGroupBox
PUBLISH_DLG_DATA_SPACING    = 10    # spacing لـ QFormLayout في data_grp
PUBLISH_DLG_INPUT_MIN_H     = 32    # min-height للـ inputs والـ spinboxes
PUBLISH_DLG_LIST_MAX_H      = 120   # max-height لـ lst_companies
PUBLISH_DLG_LIST_RADIUS     = 6     # border-radius لـ lst_companies
PUBLISH_DLG_LIST_ITEM_PAD_V = 5     # padding عمودي لـ item في lst_companies
PUBLISH_DLG_LIST_ITEM_PAD_H = 10    # padding أفقي لـ item في lst_companies
PUBLISH_DLG_QUICK_BTN_MIN_H = 26    # min-height لأزرار الاختيار السريع
PUBLISH_DLG_QUICK_BTN_MAX_W = 90    # max-width لأزرار الاختيار السريع
PUBLISH_DLG_OK_BTN_MIN_H    = 34    # min-height لزر النشر
PUBLISH_DLG_OK_BTN_RADIUS   = 6     # border-radius لزر النشر
PUBLISH_DLG_OK_BTN_PAD_H    = 18    # padding أفقي لزر النشر

# ── CompaniesDialog ────────────────────────────────────────
COMPANIES_DLG_BORDER_W        = 1     # عرض border لعناصر CompaniesDialog (حدود عادية 1px)
COMPANIES_DLG_HDR_BORDER_W    = 2     # عرض border-bottom لهيدر الجدول في CompaniesDialog
COMPANIES_DLG_MIN_W           = 820   # عرض أدنى لـ CompaniesDialog
COMPANIES_DLG_MIN_H           = 560   # ارتفاع أدنى لـ CompaniesDialog
COMPANIES_DLG_ROOT_MARGIN     = (12, 12, 12, 12)  # contentsMargins لـ root layout
COMPANIES_DLG_ROOT_SPACING    = 10   # spacing لـ root layout
COMPANIES_DLG_TITLE_PAD_V     = 4    # padding عمودي لعنوان CompaniesDialog
COMPANIES_DLG_SPLITTER_HANDLE_W = 6  # handleWidth للـ splitter
COMPANIES_DLG_SPLITTER_L      = 460  # عرض الجانب الأيسر (جدول) في splitter
COMPANIES_DLG_SPLITTER_R      = 320  # عرض الجانب الأيمن (فورم) في splitter
COMPANIES_DLG_CLOSE_BTN_H     = 34   # ارتفاع زر الإغلاق
COMPANIES_DLG_CLOSE_BTN_RADIUS= 5    # border-radius لزر الإغلاق
COMPANIES_DLG_CLOSE_BTN_PAD_H = 18   # padding أفقي لزر الإغلاق
COMPANIES_DLG_TABLE_PANEL_SPACING = 6  # spacing لـ table panel
COMPANIES_DLG_ADD_BTN_H       = 32   # ارتفاع زر إضافة شركة
COMPANIES_DLG_TABLE_COL3_W    = 110  # عرض عمود الأزرار في الجدول
COMPANIES_DLG_TABLE_RADIUS    = 6    # border-radius لـ QTableWidget
COMPANIES_DLG_TABLE_ITEM_PAD_V= 4    # padding عمودي لـ item في الجدول
COMPANIES_DLG_TABLE_ITEM_PAD_H= 8    # padding أفقي لـ item في الجدول
COMPANIES_DLG_HDR_PAD_V       = 6    # padding عمودي لـ header section
COMPANIES_DLG_HDR_PAD_H       = 8    # padding أفقي لـ header section
COMPANIES_DLG_FORM_RADIUS     = 8    # border-radius لـ form panel
COMPANIES_DLG_FORM_MARGIN     = (16, 16, 16, 16)  # contentsMargins لـ form panel
COMPANIES_DLG_FORM_SPACING    = 10   # spacing لـ form panel
COMPANIES_DLG_INP_H           = 32   # ارتفاع حقول الإدخال
COMPANIES_DLG_INP_RADIUS      = 5    # border-radius لحقول الإدخال
COMPANIES_DLG_INP_PAD_V       = 2    # padding عمودي لحقول الإدخال
COMPANIES_DLG_INP_PAD_H       = 8    # padding أفقي لحقول الإدخال
COMPANIES_DLG_COLOR_PREVIEW_SIZE  = 32  # حجم مربع معاينة اللون (عرض وارتفاع)
COMPANIES_DLG_COLOR_PREVIEW_RADIUS= 5   # border-radius لمربع معاينة اللون
COMPANIES_DLG_COLOR_BTN_H     = 32   # ارتفاع زر اختيار اللون
COMPANIES_DLG_COLOR_BTN_PAD_H = 10   # padding أفقي لزر اختيار اللون
COMPANIES_DLG_NOTES_MAX_H     = 80   # max-height لـ QTextEdit الملاحظات
COMPANIES_DLG_NOTES_RADIUS    = 5    # border-radius لـ QTextEdit الملاحظات
COMPANIES_DLG_NOTES_PAD       = 4    # padding لـ QTextEdit الملاحظات
COMPANIES_DLG_SAVE_BTN_H      = 34   # ارتفاع زر الحفظ
COMPANIES_DLG_CANCEL_BTN_H    = 34   # ارتفاع زر الإلغاء
COMPANIES_DLG_CANCEL_BTN_RADIUS = 5  # border-radius لزر الإلغاء
COMPANIES_DLG_CANCEL_BTN_PAD_H = 14  # padding أفقي لزر الإلغاء
COMPANIES_DLG_BTN_RADIUS      = 5    # border-radius لأزرار _btn_style
COMPANIES_DLG_BTN_PAD_H       = 14   # padding أفقي لأزرار _btn_style
COMPANIES_DLG_NAME_BADGE_RADIUS= 4   # border-radius لـ name_lbl في الجدول
COMPANIES_DLG_NAME_BADGE_PAD_V = 3   # padding عمودي لـ name_lbl
COMPANIES_DLG_NAME_BADGE_PAD_H = 8   # padding أفقي لـ name_lbl
COMPANIES_DLG_BTNS_CELL_MARGIN_H = 4   # left/right margin لـ btns_lay في خلية الأزرار
COMPANIES_DLG_BTNS_CELL_MARGIN_V = 2   # top/bottom margin لـ btns_lay في خلية الأزرار
COMPANIES_DLG_BTNS_CELL_SPACING  = 4   # spacing بين أزرار الخلية
COMPANIES_DLG_ACTION_BTN_SIZE    = 28  # حجم أزرار الإجراءات (عرض وارتفاع)
COMPANIES_DLG_ACTION_BTN_RADIUS  = 4   # border-radius لأزرار الإجراءات
COMPANIES_DLG_ROW_H              = 42  # ارتفاع الصف في الجدول

# ── CompanySelector ────────────────────────────────────────
COMPANY_SELECTOR_BORDER_W     = 1    # عرض border لعناصر CompanySelector (combo وزر الإدارة)
COMPANY_SELECTOR_MARGIN_H     = 8    # left/right margin لـ lay في CompanySelector
COMPANY_SELECTOR_MARGIN_V     = 4    # top/bottom margin لـ lay في CompanySelector
COMPANY_SELECTOR_SPACING      = 6    # spacing لـ lay في CompanySelector
COMPANY_SELECTOR_ICO_W        = 22   # عرض ثابت لـ label الأيقونة في CompanySelector
COMPANY_SELECTOR_COMBO_MIN_W  = 180  # عرض أدنى لـ combo الشركات
COMPANY_SELECTOR_COMBO_H      = 30   # ارتفاع ثابت لـ combo الشركات
COMPANY_SELECTOR_COMBO_RADIUS = 5    # border-radius لـ combo الشركات
COMPANY_SELECTOR_COMBO_PAD_V  = 2    # padding عمودي لـ combo الشركات
COMPANY_SELECTOR_COMBO_PAD_H  = 8    # padding أفقي لـ combo الشركات
COMPANY_SELECTOR_DROP_W       = 20   # عرض drop-down arrow في combo الشركات
COMPANY_SELECTOR_ITEM_PAD_V   = 6    # padding عمودي لـ item في قائمة combo الشركات
COMPANY_SELECTOR_ITEM_PAD_H   = 10   # padding أفقي لـ item في قائمة combo الشركات
COMPANY_SELECTOR_ITEM_MIN_H   = 28   # ارتفاع أدنى لـ item في قائمة combo الشركات
COMPANY_SELECTOR_MANAGE_BTN_SIZE = 30  # حجم زر الإدارة (عرض وارتفاع)
COMPANY_SELECTOR_MANAGE_BTN_RADIUS = 5  # border-radius لزر الإدارة

# ── NoCompanyScreen ────────────────────────────────────────
NO_COMPANY_ICON_SIZE       = 32   # font-size لأيقونة الترحيب في NoCompanyScreen
NO_COMPANY_BTN_H           = 42   # ارتفاع زر «إنشاء شركة» في NoCompanyScreen
NO_COMPANY_BTN_W           = 220  # عرض زر «إنشاء شركة» في NoCompanyScreen
NO_COMPANY_BTN_RADIUS      = 8    # border-radius لزر NoCompanyScreen
NO_COMPANY_SPACING         = 16   # spacing بين عناصر NoCompanyScreen

# ── SharedItemsManagerDialog ───────────────────────────────
SHARED_MGR_TREE_TYPE_FONT_DELTA = 1    # زيادة pointSize لخط عناصر النوع في شجرة SharedItemsManager
SHARED_MGR_HDR_BORDER_W    = 2    # عرض border-bottom لهيدر SharedItemsManagerDialog
SHARED_MGR_HINT_BORDER_W   = 1    # عرض border لـ hint label في SharedItemsManagerDialog
SHARED_MGR_BTN_DEL_BORDER_W= 1    # عرض border لزر الحذف في SharedItemsManagerDialog
SHARED_MGR_MIN_W           = 820  # عرض أدنى لـ SharedItemsManagerDialog
SHARED_MGR_MIN_H           = 600  # ارتفاع أدنى لـ SharedItemsManagerDialog
SHARED_MGR_BODY_MARGIN     = (16, 14, 16, 14)  # contentsMargins لـ body layout
SHARED_MGR_BODY_SPACING    = 10   # spacing لـ body layout
SHARED_MGR_HINT_RADIUS     = 6    # border-radius لـ hint label
SHARED_MGR_HINT_PAD_V      = 8    # padding عمودي لـ hint label
SHARED_MGR_HINT_PAD_H      = 12   # padding أفقي لـ hint label
SHARED_MGR_BTN_MIN_H       = 32   # ارتفاع أدنى لأزرار الشجرة
SHARED_MGR_BTN_ADD_RADIUS  = 6    # border-radius لزر الإضافة
SHARED_MGR_BTN_ADD_PAD_H   = 14   # padding أفقي لزر الإضافة
SHARED_MGR_BTN_DEL_RADIUS  = 4    # border-radius لزر الحذف
SHARED_MGR_BTN_DEL_PAD_H   = 12   # padding أفقي لزر الحذف
SHARED_MGR_TREE_BORDER_W   = 1    # عرض border لـ QTreeWidget في SharedItemsManagerDialog
SHARED_MGR_TREE_RADIUS     = 8    # border-radius لـ QTreeWidget
SHARED_MGR_TREE_ITEM_PAD_V = 5    # padding عمودي لـ item في الشجرة
SHARED_MGR_TREE_ITEM_PAD_H = 8    # padding أفقي لـ item في الشجرة
SHARED_MGR_COL1_W          = 110  # عرض عمود النوع في الشجرة
SHARED_MGR_COL2_W          = 180  # عرض عمود البيانات في الشجرة
SHARED_MGR_COL3_W          = 160  # عرض عمود الشركات في الشجرة
SHARED_MGR_COL4_W          = 130  # عرض عمود آخر تحديث في الشجرة
SHARED_MGR_HDR_H           = 60   # ارتفاع هيدر SharedItemsManagerDialog
SHARED_MGR_HDR_MARGIN_H    = 20   # left/right margin لـ header layout
SHARED_MGR_CLOSE_BTN_H     = 34   # ارتفاع زر الإغلاق

# ── SharedItemsDialog ──────────────────────────────────────
SHARED_DLG_HDR_BORDER_W        = 1    # عرض border لـ header label في SharedItemsDialog
SHARED_DLG_LINK_BTN_BORDER_W   = 1    # عرض border لأزرار ربط/فك الشركات في SharedItemsDialog
SHARED_DLG_GRP_BORDER_W        = 1    # عرض border لـ QGroupBox في SharedItemsDialog
SHARED_DLG_LIST_BORDER_W       = 1    # عرض border لـ QListWidget في SharedItemsDialog
SHARED_DLG_SPIN_MAX_DEFAULT    = 9999999  # الحد الأقصى الافتراضي لـ QDoubleSpinBox في SharedItemsDialog
SHARED_DLG_SPIN_DEC_DEFAULT    = 4    # عدد الخانات العشرية الافتراضي لـ QDoubleSpinBox
SHARED_DLG_SPIN_MAX_MINUTES    = 9999    # الحد الأقصى لـ spinbox الدقائق (labor_op)
SHARED_DLG_SPIN_DEC_MINUTES    = 2    # عدد الخانات العشرية لـ spinbox الدقائق
SHARED_DLG_MIN_W           = 560  # عرض أدنى لـ SharedItemsDialog
SHARED_DLG_MIN_H           = 500  # ارتفاع أدنى لـ SharedItemsDialog
SHARED_DLG_ROOT_SPACING    = 12   # spacing لـ root layout في SharedItemsDialog
SHARED_DLG_ROOT_MARGIN     = (16, 16, 16, 12)  # contentsMargins لـ root layout
SHARED_DLG_HDR_RADIUS      = 6    # border-radius لـ header label
SHARED_DLG_HDR_PAD_V       = 8    # padding عمودي لـ header label
SHARED_DLG_HDR_PAD_H       = 12   # padding أفقي لـ header label
SHARED_DLG_GRP_RADIUS      = 8    # border-radius لـ QGroupBox
SHARED_DLG_GRP_PAD_TOP     = 10   # padding-top لـ QGroupBox
SHARED_DLG_GRP_MARGIN_TOP  = 6    # margin-top لـ QGroupBox
SHARED_DLG_GRP_TITLE_PAD_H = 8    # padding أفقي لعنوان QGroupBox
SHARED_DLG_DATA_SPACING    = 10   # spacing لـ QFormLayout في data_grp
SHARED_DLG_INPUT_MIN_H     = 32   # min-height للـ inputs والـ spinboxes
SHARED_DLG_LIST_MAX_H      = 120  # max-height لـ lst_companies
SHARED_DLG_LIST_RADIUS     = 6    # border-radius لـ lst_companies
SHARED_DLG_LIST_ITEM_PAD_V = 5    # padding عمودي لـ item في lst_companies
SHARED_DLG_LIST_ITEM_PAD_H = 10   # padding أفقي لـ item في lst_companies
SHARED_DLG_LINK_BTN_RADIUS = 5    # border-radius لأزرار ربط الشركات
SHARED_DLG_LINK_BTN_PAD_V  = 4    # padding عمودي لأزرار ربط الشركات
SHARED_DLG_LINK_BTN_PAD_H  = 12   # padding أفقي لأزرار ربط الشركات
SHARED_DLG_LINK_BTN_MIN_H  = 28   # ارتفاع أدنى لأزرار ربط الشركات
SHARED_DLG_SAVE_BTN_MIN_H  = 34   # ارتفاع أدنى لزر الحفظ
SHARED_DLG_SAVE_BTN_RADIUS = 6    # border-radius لزر الحفظ
SHARED_DLG_SAVE_BTN_PAD_H  = 18   # padding أفقي لزر الحفظ
SHARED_DLG_PREVIEW_RADIUS  = 4    # border-radius لـ preview label (سعر الوحدة)
SHARED_DLG_PREVIEW_PAD_V   = 4    # padding عمودي لـ preview label
SHARED_DLG_PREVIEW_PAD_H   = 8    # padding أفقي لـ preview label

# ── LinkItemPicker ─────────────────────────────────────────
LINK_PICKER_BORDER_W       = 1     # عرض border لعناصر LinkItemPicker (القائمة وزر الإلغاء)
LINK_PICKER_MIN_W          = 460   # عرض أدنى لـ LinkItemPicker
LINK_PICKER_MIN_H          = 380   # ارتفاع أدنى لـ LinkItemPicker
LINK_PICKER_SPACING        = 10    # spacing لـ root layout في LinkItemPicker
LINK_PICKER_MARGIN         = (16, 16, 16, 16)  # contentsMargins لـ root layout
LINK_PICKER_LIST_RADIUS    = 6     # border-radius لـ QListWidget
LINK_PICKER_LIST_ITEM_PAD_V= 8    # padding عمودي لـ item في QListWidget
LINK_PICKER_LIST_ITEM_PAD_H= 12   # padding أفقي لـ item في QListWidget
LINK_PICKER_OK_BTN_H       = 34   # ارتفاع زر الربط
LINK_PICKER_OK_BTN_RADIUS  = 5    # border-radius لزر الربط
LINK_PICKER_OK_BTN_PAD_H   = 18   # padding أفقي لزر الربط
LINK_PICKER_BTN_PAD_V      = 4    # padding عمودي لأزرار LinkItemPicker
LINK_PICKER_CANCEL_BTN_H   = 34   # ارتفاع زر الإلغاء
LINK_PICKER_CANCEL_BTN_RADIUS = 5  # border-radius لزر الإلغاء
LINK_PICKER_CANCEL_BTN_PAD_H  = 14 # padding أفقي لزر الإلغاء

