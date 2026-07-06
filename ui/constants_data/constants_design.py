"""
ui/constants_data/design.py
======================
ثوابت قسم التصميمات (المقاسات، التصنيفات، مجموعات الأبعاد)
جزء من تقسيم ui/constants.py — راجع ui/constants/__init__.py.
"""

# ── _CatRow (design categories row) ───────────────────────
CAT_ROW_MIN_H           = 36    # ارتفاع أدنى لصف التصنيف
CAT_ROW_MARGIN_H        = 12    # left margin أساسي لصف التصنيف
CAT_ROW_MARGIN_R        = 10    # right margin لصف التصنيف
CAT_ROW_SPACING         = 8     # spacing داخل HBoxLayout للصف
CAT_ROW_DEPTH_INDENT    = 16    # indent إضافي لكل مستوى تفرع
CAT_ROW_INDENT_LINE_W   = 2     # عرض خط الربط للعناصر الفرعية
CAT_ROW_INDENT_LINE_H   = 16    # ارتفاع خط الربط للعناصر الفرعية
CAT_ROW_DOT_W           = 10    # عرض ثابت لنقطة اللون
CAT_ROW_BADGE_W         = 24    # عرض ثابت لشارة العداد
CAT_ROW_BADGE_H         = 18    # ارتفاع ثابت لشارة العداد
CAT_ROW_BADGE_RADIUS    = 9     # border-radius لشارة العداد

# ── _CatForm (design categories form) ─────────────────────
CAT_FORM_RADIUS             = 5     # border-radius عام للفورم (px)
CAT_FORM_MARGIN             = (12, 12, 12, 12)  # contentsMargins للـ layout
CAT_FORM_SPACING            = 8     # spacing داخل VBoxLayout الرئيسي
CAT_FORM_INP_H              = 32    # ارتفاع أدنى لحقل الاسم
CAT_FORM_CMB_H              = 30    # ارتفاع أدنى للـ combo الأب
CAT_FORM_COLOR_PREVIEW_SIZE = 24    # حجم مربع معاينة اللون (عرض وارتفاع)
CAT_FORM_COLOR_PREVIEW_RADIUS = 6   # border-radius مربع معاينة اللون
CAT_FORM_BTN_COLOR_H        = 26    # ارتفاع أدنى لزر اختيار اللون
CAT_FORM_BTN_H              = 30    # ارتفاع أدنى لأزرار الحفظ/الإلغاء
CAT_FORM_BTN_DEFAULT_H      = 28    # ارتفاع افتراضي لـ _btn_ss
CAT_FORM_BTN_SPACING        = 6     # spacing بين أزرار الحفظ/الإلغاء
CAT_FORM_COLOR_ROW_SPACING  = 8     # spacing صف اللون

# ── _DesignCard ────────────────────────────────────────
DESIGN_CARD_W               = 172   # عرض ثابت لبطاقة التصميم
DESIGN_CARD_THUMB           = 128   # ارتفاع/عرض منطقة الـ thumbnail
DESIGN_CARD_RADIUS          = "10px"  # border-radius الخارجي للبطاقة
DESIGN_CARD_RADIUS_SM       = "6px"   # border-radius داخلي (thumbnail)
DESIGN_CARD_BADGE_X_OFFSET  = 30    # مسافة الـ badge من يمين الـ thumbnail
DESIGN_CARD_BADGE_Y         = 8     # y الـ badge فوق الـ thumbnail
DESIGN_CARD_BADGE_W         = 22    # عرض الـ badge
DESIGN_CARD_BADGE_H         = 18    # ارتفاع الـ badge
DESIGN_CARD_BADGE_RADIUS    = 9     # border-radius الـ badge
DESIGN_CARD_INFO_MARGIN_H   = 10    # left/right margin منطقة المعلومات
DESIGN_CARD_INFO_MARGIN_T   = 8     # top margin منطقة المعلومات
DESIGN_CARD_INFO_MARGIN_B   = 10    # bottom margin منطقة المعلومات
DESIGN_CARD_INFO_SPACING    = 3     # spacing داخل layout المعلومات

# ── SizeCard (helper.py) ───────────────────────────────
SIZE_CARD_THUMB_SIZE    = 100   # عرض/ارتفاع الـ thumbnail في بطاقة المقاس (px)
SIZE_CARD_BTN_HEIGHT    = 26    # ارتفاع أدنى لأزرار بطاقة المقاس (px)
SIZE_CARD_BTN_RADIUS    = 5     # border-radius لأزرار بطاقة المقاس (px)
SIZE_CARD_BTN_PAD_H     = 10    # padding أفقي لأزرار بطاقة المقاس (px)
SIZE_CARD_DEFAULT_DPI   = 300   # الـ DPI الافتراضي لإنشاء canvas في GIMP
SIZE_CARD_SCREEN_DPI    = 96    # الـ DPI المستخدم عند وحدة px (screen DPI)

# ── _SizeCard (_size_card.py) ──────────────────────────
SIZE_CARD_RADIUS          = "10px"  # border-radius الخارجي لبطاقة المقاس
SIZE_CARD_RADIUS_XS       = "4px"   # border-radius أزرار التعديل/الحذف الصغيرة
SIZE_CARD_THUMB_W         = 72      # عرض/ارتفاع thumbnail بطاقة المقاس (px)
SIZE_CARD_MIN_H           = 90      # الحد الأدنى لارتفاع بطاقة المقاس (px)
SIZE_CARD_MAIN_MARGIN     = 12      # margin الجزء الرئيسي من البطاقة (px)
SIZE_CARD_MAIN_SPACING    = 12      # spacing الجزء الرئيسي من البطاقة (px)
SIZE_CARD_INFO_SPACING    = 3       # spacing عمود المعلومات (px)
SIZE_CARD_BTNS_SPACING    = 5       # spacing عمود الأزرار (px)
SIZE_CARD_ACT_SPACING     = 4       # spacing صف أزرار الإجراءات (px)
SIZE_CARD_ICON_BTN_W      = 28      # عرض أزرار الأيقونات (تعديل/حذف) (px)
SIZE_CARD_ICON_BTN_H      = 26      # ارتفاع أزرار الأيقونات (تعديل/حذف) (px)
SIZE_CARD_STATUS_MARGIN_H = 12      # margin أفقي لشريط الحالة (px)
SIZE_CARD_STATUS_MARGIN_V = 5       # margin رأسي لشريط الحالة (px)
SIZE_CARD_STATUS_SPACING  = 8       # spacing شريط الحالة (px)
SIZE_CARD_CHIPS_SPACING   = 4       # spacing بين الـ chips (وحدة/DPI) (px)
SIZE_CARD_CHIP_RADIUS     = 3       # border-radius الـ chip (px)
SIZE_CARD_CHIP_PAD_V      = 1       # padding رأسي للـ chip (px)
SIZE_CARD_CHIP_PAD_H      = 6       # padding أفقي للـ chip (px)
SIZE_CARD_BORDER_W        = 1       # سُمك border البطاقة والـ chip (px)
SIZE_CARD_MAIN_BTN_W      = 120     # عرض أدنى للزر الرئيسي (GIMP) (px)
SIZE_CARD_MAIN_BTN_H      = 30      # ارتفاع الزر الرئيسي (GIMP) (px)

# ── XcfWatcher / _xcf_thumbnail.py ─────────────────────
XCF_WATCHER_DEBOUNCE_MS   = 1500    # تأخير الـ debounce قبل اعتبار ملف XCF متغيّر (ms)
XCF_THUMB_MIN_SIZE        = 64      # الحد الأدنى لحجم الـ placeholder thumbnail (px)

# ── DesignsCategoriesPanel ─────────────────────────────
DESIGN_CATS_SIDEBAR_W        = 230   # عرض ثابت لـ DesignsCategoriesPanel
DESIGN_CATS_HDR_H            = 52    # ارتفاع header في DesignsCategoriesPanel
DESIGN_CATS_HDR_MARGIN_L     = 14    # left margin لـ hdr_lay
DESIGN_CATS_HDR_MARGIN_R     = 10    # right margin لـ hdr_lay
DESIGN_CATS_HDR_SPACING      = 8     # spacing لـ hdr_lay
DESIGN_CATS_BTN_ADD_SIZE     = 26    # حجم زر الإضافة (عرض وارتفاع)
DESIGN_CATS_BTN_ADD_RADIUS   = 13    # border-radius زر الإضافة (= size/2)
DESIGN_CATS_SEARCH_MARGIN_V  = 6     # top/bottom margin لـ sf_lay
DESIGN_CATS_SEARCH_SPACING   = 6     # spacing لـ sf_lay
DESIGN_CATS_INP_MIN_H        = 30    # min-height لـ inp_search
DESIGN_CATS_BTN_CLEAR_SIZE   = 22    # حجم زر مسح البحث (عرض وارتفاع)
DESIGN_CATS_LIST_MARGIN_V    = 6     # top/bottom margin لـ _list_lay
DESIGN_CATS_LIST_SPACING     = 1     # spacing لـ _list_lay
DESIGN_CATS_ACT_MARGIN_H     = 10    # left/right margin لـ ab layout
DESIGN_CATS_ACT_MARGIN_V     = 8     # top/bottom margin لـ ab layout
DESIGN_CATS_ACT_SPACING      = 6     # spacing لـ ab layout
DESIGN_CATS_BTN_MIN_H        = 28    # min-height لأزرار الإجراءات
DESIGN_CATS_SEP_H            = 1     # ارتفاع فاصل HLine بين «الكل» والتصنيفات
DESIGN_CATS_SCROLL_W         = 4     # عرض scrollbar في panel التصنيفات
DESIGN_CATS_SCROLL_RADIUS    = 2     # border-radius لـ scrollbar handle
DESIGN_CATS_SCROLL_MIN_H     = 20    # min-height لـ scrollbar handle
DESIGN_CATS_SEARCH_FRAME_PAD_V = 8   # padding عمودي لـ QFrame شريط البحث
DESIGN_CATS_SEARCH_FRAME_PAD_H = 12  # padding أفقي لـ QFrame شريط البحث
DESIGN_CATS_SEP_MARGIN_V     = 3     # margin عمودي لفاصل HLine بين «الكل» والتصنيفات
DESIGN_CATS_SEP_MARGIN_H     = 12    # margin أفقي لفاصل HLine بين «الكل» والتصنيفات

# ── _DesignsTable ──────────────────────────────────────
DESIGNS_TABLE_TB_MARGIN_H    = 14    # left/right margin لـ tb_lay في toolbar
DESIGNS_TABLE_TB_MARGIN_V    = 10    # top/bottom margin لـ tb_lay في toolbar
DESIGNS_TABLE_TB_SPACING     = 8     # spacing لـ tb_lay في toolbar
DESIGNS_TABLE_ROW_SPACING    = 8     # spacing لـ row1 و row2
DESIGNS_TABLE_INP_MIN_H      = 34    # min-height لـ inp_search و btn_new
DESIGNS_TABLE_CMB_MIN_H      = 28    # min-height لـ cmb_set و _btn_rst
DESIGNS_TABLE_CMB_DROP_W     = 16    # عرض drop-down arrow في cmb_set
DESIGNS_TABLE_GRID_MARGIN    = 14    # margin كل جهات _grid_layout
DESIGNS_TABLE_GRID_SPACING   = 12    # spacing لـ _grid_layout
DESIGNS_TABLE_SCROLL_W       = 6     # عرض scrollbar في منطقة الكروت
DESIGNS_TABLE_SCROLL_RADIUS  = 3     # border-radius لـ scrollbar handle
DESIGNS_TABLE_SCROLL_MIN_H   = 20    # min-height لـ scrollbar handle
DESIGNS_TABLE_INP_PAD_H      = 12    # padding أفقي لـ inp_search
DESIGNS_TABLE_REFLOW_DELAY   = 60    # ms — QTimer.singleShot في resizeEvent
DESIGNS_TABLE_SEARCH_DELAY   = 280   # ms — QTimer interval لـ _search_timer
DESIGNS_TABLE_COLS_SIDE_PAD  = 28    # padding جانبي لحساب عدد الأعمدة
DESIGNS_TABLE_MIN_COLS       = 2     # الحد الأدنى لعدد أعمدة الـ grid
DESIGNS_TABLE_EMPTY_SPACING  = 12    # spacing لـ ef_lay (حالة فارغة)
DESIGNS_TAB_SPLITTER_LIST_W    = 360   # عرض جانب قائمة الكروت في splitter DesignsTab (px)
DESIGNS_TAB_SPLITTER_DETAIL_W  = 640   # عرض جانب لوحة التفاصيل في splitter DesignsTab (px)

# ── _DesignDetailPanel ─────────────────────────────────
DESIGN_DETAIL_HDR_MARGIN_H   = 18    # left/right margin لـ hdr_lay
DESIGN_DETAIL_HDR_MARGIN_T   = 14    # top margin لـ hdr_lay
DESIGN_DETAIL_HDR_MARGIN_B   = 16    # bottom margin لـ hdr_lay
DESIGN_DETAIL_HDR_SPACING    = 14    # spacing لـ hdr_lay
DESIGN_DETAIL_TITLE_ROW_SPACING = 8  # spacing لـ title_row
DESIGN_DETAIL_BTN_ROW_SPACING   = 6  # spacing لـ btn_row
DESIGN_DETAIL_FIELD_SPACING  = 4     # spacing بين label والـ widget في كل حقل
DESIGN_DETAIL_ROW2_SPACING   = 10    # spacing لـ row2 (cat + notes)
DESIGN_DETAIL_SH_MARGIN_H    = 18    # left/right margin لـ sh_lay
DESIGN_DETAIL_SH_MARGIN_V    = 10    # top/bottom margin لـ sh_lay
DESIGN_DETAIL_SH_SPACING     = 8     # spacing لـ sh_lay
DESIGN_DETAIL_SIZES_MARGIN   = 14    # margin كل جهات _sizes_layout
DESIGN_DETAIL_SIZES_SPACING  = 10    # spacing لـ _sizes_layout
DESIGN_DETAIL_SCROLL_W       = 5     # عرض scrollbar في منطقة المقاسات
DESIGN_DETAIL_SCROLL_RADIUS  = 2     # border-radius لـ scrollbar handle
DESIGN_DETAIL_SCROLL_MIN_H   = 20    # min-height لـ scrollbar handle
DESIGN_DETAIL_CMB_MIN_W      = 160   # min-width لـ cmb_cat
DESIGN_DETAIL_ES_SPACING     = 6     # spacing لـ es_lay (empty sizes state)

# ── _SizeDialog (_size_dialog.py) ──────────────────────
SIZE_DLG_MIN_W            = 520   # الحد الأدنى لعرض الدايالوج (px)
SIZE_DLG_MARGIN_H         = 20    # margin أفقي للـ root layout (px)
SIZE_DLG_MARGIN_V         = 18    # margin رأسي للـ root layout (px)
SIZE_DLG_ROOT_SPACING     = 14    # spacing للـ root layout (px)
SIZE_DLG_HDR_RADIUS       = 8     # border-radius رأس الدايالوج (px)
SIZE_DLG_HDR_PAD_V        = 8     # padding رأسي لرأس الدايالوج (px)
SIZE_DLG_HDR_PAD_H        = 14    # padding أفقي لرأس الدايالوج (px)
SIZE_DLG_FORM_SPACING     = 12    # spacing لـ QFormLayout (px)
SIZE_DLG_FIELD_H          = 34    # ارتفاع أدنى لحقول الفورم (combo/input) (px)
SIZE_DLG_CANVAS_RADIUS    = 6     # border-radius لصندوق معاينة الكانفاس (px)
SIZE_DLG_CANVAS_PAD_V     = 6     # padding رأسي لصندوق معاينة الكانفاس (px)
SIZE_DLG_CANVAS_PAD_H     = 12    # padding أفقي لصندوق معاينة الكانفاس (px)
SIZE_DLG_CANVAS_BORDER_W  = 1     # سُمك border صندوق معاينة الكانفاس (px)
SIZE_DLG_BROWSE_BTN_SIZE  = 34    # عرض/ارتفاع زر تصفح ملف GIMP (px)
SIZE_DLG_BROWSE_RADIUS    = 6     # border-radius زر تصفح ملف GIMP (px)
SIZE_DLG_BROWSE_BORDER_W  = 1.5   # سُمك border زر تصفح ملف GIMP (px)
SIZE_DLG_BTN_H            = 36    # ارتفاع أدنى لأزرار الحفظ/الإلغاء (px)
SIZE_DLG_BTN_OK_RADIUS    = 7     # border-radius زر الحفظ (px)
SIZE_DLG_BTN_OK_PAD_V     = 6     # padding رأسي زر الحفظ (px)
SIZE_DLG_BTN_OK_PAD_H     = 20    # padding أفقي زر الحفظ (px)
SIZE_DLG_BTN_CANCEL_PAD_V = 5     # padding رأسي زر الإلغاء (px)
SIZE_DLG_BTN_CANCEL_PAD_H = 16    # padding أفقي زر الإلغاء (px)

# ══════════════════════════════════════════════════════════
# _SourcePickerDialog — ui/tabs/design/dimension_sets/_source_picker_dialog.py
# ══════════════════════════════════════════════════════════
SRC_PICKER_DLG_MIN_W        = 480   # الحد الأدنى لعرض النافذة (px)
SRC_PICKER_DLG_MIN_H        = 360   # الحد الأدنى لارتفاع النافذة (px)
SRC_PICKER_ROOT_MARGIN_H    = 20    # margin أفقي للـ root layout (px)
SRC_PICKER_ROOT_MARGIN_V    = 18    # margin رأسي للـ root layout (px)
SRC_PICKER_ROOT_SPACING     = 14    # spacing للـ root layout (px)
SRC_PICKER_HDR_MARGIN_H     = 14    # margin أفقي لرأس النافذة (px)
SRC_PICKER_HDR_MARGIN_V     = 12    # margin رأسي لرأس النافذة (px)
SRC_PICKER_HDR_SPACING      = 4     # spacing لرأس النافذة (px)
SRC_PICKER_LIST_SPACING     = 4     # spacing لقائمة الـ instances (px)
SRC_PICKER_LIST_MARGIN      = 10    # margin لقائمة الـ instances (px)
SRC_PICKER_PREVIEW_MARGIN_H = 14    # margin أفقي لصندوق المعاينة (px)
SRC_PICKER_PREVIEW_MARGIN_V = 10    # margin رأسي لصندوق المعاينة (px)
SRC_PICKER_BTN_OK_MIN_W     = 140   # عرض أدنى لزر التطبيق (px)
SRC_PICKER_ROW_MARGIN_H     = 12    # margin أفقي لصف الـ instance (px)
SRC_PICKER_ROW_MARGIN_V     = 8     # margin رأسي لصف الـ instance (px)
SRC_PICKER_ROW_SPACING      = 12    # spacing لصف الـ instance (px)
SRC_PICKER_BTN_RADIUS       = 7     # border-radius لأزرار primary/ghost (px)
SRC_PICKER_BTN_PRIMARY_PAD_V = 6    # padding رأسي لزر primary (px)
SRC_PICKER_BTN_PRIMARY_PAD_H = 20   # padding أفقي لزر primary (px)
SRC_PICKER_BTN_GHOST_PAD_V   = 5    # padding رأسي لزر ghost (px)
SRC_PICKER_BTN_GHOST_PAD_H   = 16   # padding أفقي لزر ghost (px)
SRC_PICKER_HDR_FRAME_RADIUS  = 10   # border-radius لإطار الرأس (px)
SRC_PICKER_EMPTY_PAD         = 20   # padding لحالة عدم وجود قيم (px)
SRC_PICKER_SCROLL_RADIUS     = 8    # border-radius لـ QScrollArea (px)
SRC_PICKER_FRAME_RADIUS      = 8    # border-radius لإطار المعاينة/الصف (px)
SRC_PICKER_RADIO_SIZE        = 18   # حجم مؤشر الـ radio button (عرض/ارتفاع) (px)
SRC_PICKER_RADIO_RADIUS      = 9    # border-radius لمؤشر الـ radio button (= size/2) (px)
SRC_PICKER_RADIO_BORDER_W    = 2    # سُمك border لمؤشر الـ radio button (px)
SRC_PICKER_RESULT_BADGE_RADIUS = 5  # border-radius لشارة النتيجة (px)
SRC_PICKER_RESULT_BADGE_PAD_V  = 1  # padding رأسي لشارة النتيجة (px)
SRC_PICKER_RESULT_BADGE_PAD_H  = 8  # padding أفقي لشارة النتيجة (px)
SRC_PICKER_BORDER_W          = 1.5  # سُمك border لعناصر scroll/preview/row frame (px)
SRC_PICKER_HDR_BORDER_W      = 1    # سُمك border لإطار الرأس وشارة النتيجة (px)

# ══════════════════════════════════════════════════════════
# _ValuesPanel — ui/tabs/design/dimension_sets/_values_panel.py
# ══════════════════════════════════════════════════════════
DIM_VALUES_LIST_MIN_W       = 240   # الحد الأدنى لعرض لوحة قائمة المجموعات (px)
DIM_VALUES_LIST_MAX_W       = 360   # الحد الأقصى لعرض لوحة قائمة المجموعات (px)
DIM_VALUES_SPLITTER_R       = 720   # عرض الجانب الأيمن (جدول القيم) في الـ splitter (px)

# ══════════════════════════════════════════════════════════
# _InstancePopup — ui/tabs/design/dimension_sets/values_panel/_instance_popup.py
# ══════════════════════════════════════════════════════════
DIM_INST_DLG_MIN_W          = 520   # الحد الأدنى لعرض النافذة (px)
DIM_INST_DLG_MIN_H          = 400   # الحد الأدنى لارتفاع النافذة (px)
DIM_INST_ROOT_MARGIN_H      = 24    # margin أفقي للـ root layout (px)
DIM_INST_ROOT_MARGIN_V      = 20    # margin رأسي للـ root layout (px)
DIM_INST_ROOT_SPACING       = 16    # spacing للـ root layout (px)
DIM_INST_HDR_RADIUS         = 8     # border-radius رأس النافذة (px)
DIM_INST_HDR_PAD_V          = 8     # padding رأسي لرأس النافذة (px)
DIM_INST_HDR_PAD_H          = 14    # padding أفقي لرأس النافذة (px)
DIM_INST_NAME_LBL_W         = 90    # عرض ثابت لتسمية حقل الاسم (px)
DIM_INST_FIELD_H            = 36    # ارتفاع أدنى لحقول الإدخال (px)
DIM_INST_FIELD_RADIUS       = 8     # border-radius لحقول الإدخال (px)
DIM_INST_FIELD_PAD_V        = 4     # padding رأسي لحقول الإدخال (px)
DIM_INST_FIELD_PAD_H        = 12    # padding أفقي لحقول الإدخال (px)
DIM_INST_FIELD_BORDER_W     = 1.5   # سُمك border لحقول الإدخال (px)
DIM_INST_SCROLL_W           = 6     # عرض scrollbar (px)
DIM_INST_SCROLL_RADIUS      = 3     # border-radius لـ scrollbar handle (px)
DIM_INST_SCROLL_MIN_H       = 24    # min-height لـ scrollbar handle (px)
DIM_INST_GRID_SPACING       = 10    # spacing لشبكة حقول القيم (px)
DIM_INST_GRID_MARGIN_V      = 4     # margin رأسي لشبكة حقول القيم (px)
DIM_INST_FIELD_LBL_W        = 130   # عرض ثابت لتسمية كل حقل قيمة (px)
DIM_INST_UNIT_LBL_W         = 38    # عرض ثابت لتسمية الوحدة (px)
DIM_INST_AUTO_BTN_SIZE      = 32    # حجم زر الحساب التلقائي (عرض/ارتفاع) (px)
DIM_INST_AUTO_BTN_RADIUS    = 5     # border-radius زر الحساب التلقائي (px)
DIM_INST_AUTO_BTN_PAD_V     = 3     # padding رأسي زر الحساب التلقائي (px)
DIM_INST_AUTO_BTN_PAD_H     = 6     # padding أفقي زر الحساب التلقائي (px)
DIM_INST_EMPTY_PAD          = 12    # padding لتسمية حالة عدم وجود حقول رقمية (px)
DIM_INST_ACT_BTN_H          = 36    # ارتفاع أدنى لأزرار الحفظ/الإلغاء/الحساب الكل (px)
DIM_INST_ACT_BTN_RADIUS     = 7     # border-radius لأزرار الحفظ/الإلغاء/الحساب الكل (px)
DIM_INST_GHOST_BTN_PAD_V    = 5     # padding رأسي لأزرار الإلغاء/الحساب الكل (px)
DIM_INST_GHOST_BTN_PAD_H    = 14    # padding أفقي لأزرار الإلغاء/الحساب الكل (px)
DIM_INST_SAVE_BTN_PAD_V     = 6     # padding رأسي لزر الحفظ (px)
DIM_INST_SAVE_BTN_PAD_H     = 18    # padding أفقي لزر الحفظ (px)
DIM_INST_SAVE_BTN_MIN_W     = 100   # عرض أدنى لزر الحفظ (px)
DIM_INST_VALUE_SPIN_MIN      = -99999  # الحد الأدنى لـ QDoubleSpinBox في حقول القيم
DIM_INST_VALUE_SPIN_MAX      = 99999   # الحد الأقصى لـ QDoubleSpinBox في حقول القيم
DIM_INST_VALUE_SPIN_DECIMALS = 4       # عدد الخانات العشرية لـ QDoubleSpinBox في حقول القيم

# ══════════════════════════════════════════════════════════
# _InstancesTable — ui/tabs/design/dimension_sets/values_panel/_instances_table.py
# ══════════════════════════════════════════════════════════
DIM_INST_TBL_BTN_BORDER_W    = 1.5   # سُمك border لأزرار toolbar (px)
DIM_INST_TBL_BTN_RADIUS      = 7     # border-radius لأزرار toolbar (px)
DIM_INST_TBL_BTN_PAD_V       = 5     # padding رأسي لأزرار toolbar الثانوية (px)
DIM_INST_TBL_BTN_PAD_H       = 14    # padding أفقي لأزرار toolbar الثانوية (px)
DIM_INST_TBL_PRIMARY_PAD_V   = 6     # padding رأسي لزر الإضافة الأساسي (px)
DIM_INST_TBL_PRIMARY_PAD_H   = 18    # padding أفقي لزر الإضافة الأساسي (px)
DIM_INST_TBL_TOOLBAR_MARGIN_H = 14   # margin أفقي لشريط الأدوات (px)
DIM_INST_TBL_TOOLBAR_MARGIN_V = 10   # margin رأسي لشريط الأدوات (px)
DIM_INST_TBL_TOOLBAR_SPACING  = 10   # spacing لشريط الأدوات (px)
DIM_INST_TBL_BTN_H            = 34   # ارتفاع أدنى لأزرار toolbar (px)
DIM_INST_TBL_CELL_PAD         = 8    # padding لخلايا الجدول (px، يُستخدم أفقي/رأسي معاً)
DIM_INST_TBL_CELL_PAD_H       = 12   # padding أفقي لخلايا الجدول (px)
DIM_INST_TBL_HDR_BORDER_W     = 2    # سُمك الخط السفلي لرأس الجدول (px)
DIM_INST_TBL_STATUS_PAD       = 6    # padding لشريط الحالة (px)
DIM_INST_TBL_NAME_COL_W       = 160  # عرض عمود الاسم (px)
DIM_INST_TBL_VALUE_COL_W      = 110  # عرض أعمدة القيم (px)
DIM_INST_TBL_MIN_SECTION_W    = 60   # الحد الأدنى لعرض أي عمود (px)
DIM_INST_TBL_ROW_H_PAD        = 6    # إضافة ثابتة لارتفاع الصف فوق (خط × 3) (px)
DIM_INST_TBL_EMPTY_SPACING    = 8    # مسافة بين أيقونة وحالة الفراغ في الجدول (px)
DIM_INST_TBL_HAIRLINE_W       = 1    # سُمك الخطوط الفاصلة العادية (toolbar/status bar) (px)

# ══════════════════════════════════════════════════════════
# _SetsListPanel / _SetCard — ui/tabs/design/dimension_sets/values_panel/_sets_list_panel.py
# ══════════════════════════════════════════════════════════
DIM_SETS_LIST_CARD_MIN_H         = 72    # ارتفاع أدنى لبطاقة مجموعة مقاسات (px)
DIM_SETS_LIST_CARD_BORDER_W      = 1.5   # سُمك border البطاقة العادية (px)
DIM_SETS_LIST_CARD_SELECTED_BORDER_W = 2 # سُمك border البطاقة المختارة (px)
DIM_SETS_LIST_CARD_RADIUS        = 10    # border-radius للبطاقة (px)
DIM_SETS_LIST_CARD_MARGIN_H      = 14    # margin أفقي داخل البطاقة (px)
DIM_SETS_LIST_CARD_MARGIN_V      = 10    # margin رأسي داخل البطاقة (px)
DIM_SETS_LIST_CARD_SPACING       = 10    # spacing بين عناصر البطاقة (px)
DIM_SETS_LIST_ICON_LBL_W         = 34    # عرض ثابت لأيقونة البطاقة (px)
DIM_SETS_LIST_TEXT_COL_SPACING   = 2     # spacing بين اسم المجموعة ومعلوماتها (px)
DIM_SETS_LIST_BADGE_W            = 58    # عرض شارة عدد القيم (px)
DIM_SETS_LIST_BADGE_H            = 22    # ارتفاع شارة عدد القيم (px)
DIM_SETS_LIST_BADGE_RADIUS       = 11    # border-radius شارة عدد القيم (px، = h/2)
DIM_SETS_LIST_HDR_PAD_V          = 10    # padding رأسي لرأس اللوحة (px)
DIM_SETS_LIST_HDR_PAD_H          = 16    # padding أفقي لرأس اللوحة (px)
DIM_SETS_LIST_HAIRLINE_W         = 1     # سُمك الخطوط الفاصلة العادية (px)
DIM_SETS_LIST_SEARCH_FRAME_MARGIN_H = 10 # margin أفقي لإطار البحث (px)
DIM_SETS_LIST_SEARCH_FRAME_MARGIN_V = 8  # margin رأسي لإطار البحث (px)
DIM_SETS_LIST_SEARCH_SPACING     = 6     # spacing بين حقل البحث وقائمة التصنيفات (px)
DIM_SETS_LIST_SEARCH_FIELD_H     = 32    # ارتفاع أدنى لحقل البحث/قائمة التصنيفات (px)
DIM_SETS_LIST_CMB_CAT_MAX_W      = 130   # أقصى عرض لقائمة التصنيفات (px)
DIM_SETS_LIST_INP_BORDER_W       = 1.5   # سُمك border حقول البحث/الفلترة (px)
DIM_SETS_LIST_INP_RADIUS         = 8     # border-radius حقول البحث/الفلترة (px)
DIM_SETS_LIST_INP_PAD_V          = 3     # padding رأسي لحقول البحث/الفلترة (px)
DIM_SETS_LIST_INP_PAD_H          = 10    # padding أفقي لحقل البحث (px)
DIM_SETS_LIST_CMB_PAD_H          = 8     # padding أفقي لقائمة التصنيفات (px)
DIM_SETS_LIST_SCROLL_W           = 6     # عرض scrollbar (px)
DIM_SETS_LIST_SCROLL_RADIUS      = 3     # border-radius لـ scrollbar handle (px)
DIM_SETS_LIST_SCROLL_MIN_H       = 24    # min-height لـ scrollbar handle (px)
DIM_SETS_LIST_CARDS_SPACING      = 8     # spacing بين بطاقات المجموعات (px)
DIM_SETS_LIST_CARDS_MARGIN       = 10    # margin حول منطقة البطاقات (px)
DIM_SETS_LIST_COUNT_PAD          = 6     # padding لعداد النتائج أسفل اللوحة (px)

# ══════════════════════════════════════════════════════════
# _FieldDialog — ui/tabs/design/dimension_sets/_field_dialog.py
# ══════════════════════════════════════════════════════════
DIM_FIELD_DLG_MIN_W          = 500     # الحد الأدنى لعرض النافذة (px)
DIM_FIELD_DLG_ROOT_SPACING   = 12      # spacing للـ root layout (px)
DIM_FIELD_DLG_ROOT_MARGIN    = 16      # margin كل جهات الـ root layout (px)
DIM_FIELD_DLG_FORM_SPACING   = 10      # spacing لـ QFormLayout (px)
DIM_FIELD_DLG_INPUT_H        = 30      # ارتفاع أدنى لحقول الإدخال (name/label/unit/type/combo) (px)
DIM_FIELD_DLG_GRP_RADIUS     = 6       # border-radius لمجموعة الاعتمادية (px)
DIM_FIELD_DLG_GRP_MARGIN_TOP = 8       # margin-top لمجموعة الاعتمادية (px)
DIM_FIELD_DLG_GRP_PAD_TOP    = 8       # padding-top لمجموعة الاعتمادية (px)
DIM_FIELD_DLG_GRP_TITLE_RIGHT = 12     # إزاحة يمين عنوان المجموعة (px)
DIM_FIELD_DLG_GRP_TITLE_PAD  = 4       # padding أفقي لعنوان المجموعة (px)
DIM_FIELD_DLG_SOURCE_CMB_MIN_W = 220   # عرض أدنى لقائمة الحقل المصدر (px)
DIM_FIELD_DLG_PREVIEW_RADIUS = 4       # border-radius لصندوق المعاينة/التلميح (px)
DIM_FIELD_DLG_PREVIEW_PAD_V  = 4       # padding رأسي لصندوق المعاينة/التلميح (px)
DIM_FIELD_DLG_PREVIEW_PAD_H  = 8       # padding أفقي لصندوق المعاينة/التلميح (px)
DIM_FIELD_DLG_SPIN_DEFAULT_MIN = -99999  # الحد الأدنى الافتراضي لـ _spin()
DIM_FIELD_DLG_SPIN_DEFAULT_MAX = 9999    # الحد الأقصى الافتراضي لـ _spin()
DIM_FIELD_DLG_SPIN_DEFAULT_DEC = 2       # عدد الخانات العشرية الافتراضي لـ _spin()
DIM_FIELD_DLG_OFFSET_MIN     = -9999   # الحد الأدنى لـ sp_offset
DIM_FIELD_DLG_OFFSET_MAX     = 9999    # الحد الأقصى لـ sp_offset
DIM_FIELD_DLG_OFFSET_DEC     = 4       # عدد الخانات العشرية لـ sp_offset

# ══════════════════════════════════════════════════════════
# _FieldsPanel — ui/tabs/design/dimension_sets/_fields_panel.py
# ══════════════════════════════════════════════════════════
DIM_FIELD_PANEL_ROOT_SPACING   = 6     # spacing للـ root layout (px)
DIM_FIELD_PANEL_COL_ORDER_W    = 60    # عرض عمود الترتيب (px)
DIM_FIELD_PANEL_COL_NAME_W     = 90    # عرض عمود الاسم (إنجليزي) (px)
DIM_FIELD_PANEL_COL_UNIT_W     = 60    # عرض عمود الوحدة (px)
DIM_FIELD_PANEL_COL_TYPE_W     = 55    # عرض عمود النوع (px)
DIM_FIELD_PANEL_COL_REQ_W      = 55    # عرض عمود الإلزامي (px)
DIM_FIELD_PANEL_COL_DEP_W      = 180   # عرض عمود الاعتمادية (px)
DIM_FIELD_PANEL_BTN_H          = 28    # ارتفاع أدنى لأزرار اللوحة (px)

# ══════════════════════════════════════════════════════════
# _CategoriesPanel — ui/tabs/design/dimension_sets/_categories_panel.py
# ══════════════════════════════════════════════════════════
DIM_CAT_PANEL_BTN_ROW_SPACING  = 6     # spacing لصف الأزرار (buttons_row)
DIM_CAT_PANEL_ROOT_MARGIN      = 8     # margin كل جهات الـ root layout (px)
DIM_CAT_PANEL_ROOT_SPACING     = 8     # spacing للـ root layout (px)
DIM_CAT_PANEL_HDR_RADIUS       = 6     # border-radius لرأس اللوحة (px)
DIM_CAT_PANEL_HDR_PAD_V        = 6     # padding رأسي لرأس اللوحة (px)
DIM_CAT_PANEL_HDR_PAD_H        = 12    # padding أفقي لرأس اللوحة (px)
DIM_CAT_PANEL_TREE_COL_NAME_W  = 200   # عرض عمود اسم التصنيف في الشجرة (px)
DIM_CAT_PANEL_TREE_COL_COUNT_W = 80    # عرض عمود عدد المجموعات في الشجرة (px)
DIM_CAT_PANEL_TREE_BTN_H       = 28    # ارتفاع أدنى لأزرار الشجرة (تعديل/حذف) (px)
DIM_CAT_PANEL_FORM_SPACING     = 8     # spacing لفورم إضافة/تعديل التصنيف (px)
DIM_CAT_PANEL_INPUT_H          = 30    # ارتفاع أدنى لحقل اسم التصنيف (px)
DIM_CAT_PANEL_COMBO_H          = 28    # ارتفاع أدنى لقائمة التصنيف الأب (px)
DIM_CAT_PANEL_COLOR_SWATCH_SIZE = 28   # حجم مربع معاينة اللون (عرض/ارتفاع) (px)
DIM_CAT_PANEL_COLOR_BTN_H      = 28    # ارتفاع أدنى لزر اختيار اللون (px)
DIM_CAT_PANEL_ACTION_BTN_H     = 30    # ارتفاع أدنى لأزرار إضافة/حفظ/إلغاء (px)
DIM_CAT_PANEL_COLOR_SWATCH_RADIUS = 4  # border-radius لمربع معاينة اللون (px)
DIM_CAT_PANEL_COLOR_SWATCH_BORDER_W = 1  # سُمك border لمربع معاينة اللون (px)

# ══════════════════════════════════════════════════════════
# _SetsPanel — ui/tabs/design/dimension_sets/_sets_panel.py
# ══════════════════════════════════════════════════════════
DIM_SETS_PANEL_HDR_RADIUS      = 6    # border-radius لرأس اللوحة (px)
DIM_SETS_PANEL_HDR_PAD_V       = 6    # padding رأسي لرأس اللوحة (px)
DIM_SETS_PANEL_HDR_PAD_H       = 10   # padding أفقي لرأس اللوحة (px)
DIM_SETS_PANEL_HINT_RADIUS     = 4    # border-radius لصندوق التلميح (px)
DIM_SETS_PANEL_HINT_BORDER_W   = 1    # سُمك border صندوق التلميح (px)
DIM_SETS_PANEL_HINT_PAD_V      = 4    # padding رأسي لصندوق التلميح (px)
DIM_SETS_PANEL_HINT_PAD_H      = 8    # padding أفقي لصندوق التلميح (px)

# ══════════════════════════════════════════════════════════
# _SetsManagerPanel / _GroupsPanel — ui/tabs/design/dimension_sets/_groups_panel.py
# ══════════════════════════════════════════════════════════
DIM_GROUPS_BTN_ROW_SPACING   = 6     # spacing لصف الأزرار (buttons_row) (px)
DIM_GROUPS_MGR_HDR_RADIUS    = 6     # border-radius لرأس لوحة إدارة المجموعات (px)
DIM_GROUPS_MGR_HDR_PAD_V     = 6     # padding رأسي لرأس لوحة إدارة المجموعات (px)
DIM_GROUPS_MGR_HDR_PAD_H     = 12    # padding أفقي لرأس لوحة إدارة المجموعات (px)
DIM_GROUPS_FIELDS_HDR_RADIUS = 4     # border-radius لرأس _FieldsPanel (px)
DIM_GROUPS_FIELDS_HDR_PAD_V  = 5     # padding رأسي لرأس _FieldsPanel (px)
DIM_GROUPS_FIELDS_HDR_PAD_H  = 10    # padding أفقي لرأس _FieldsPanel (px)
DIM_GROUPS_MGR_ROOT_SPACING  = 8     # spacing لـ root layout في _SetsManagerPanel (px)
DIM_GROUPS_TOP_SPACING       = 6     # spacing للجزء العلوي (جدول + فورم) (px)
DIM_GROUPS_MINI_BTN_H        = 28    # ارتفاع أدنى لأزرار تعديل/حذف المجموعة (px)

# ── design_styles._Styles ──────────────────────────────────
STYLES_RADIUS_LG              = 6     # border-radius الأساسي (px) — كان "6px"
STYLES_RADIUS_SM               = 4     # border-radius صغير (px) — كان "4px"
STYLES_RADIUS_XS                = 3     # border-radius أصغر (px) — كان "3px"
STYLES_BTN_HEIGHT_PAD           = 8     # الإضافة لحساب الارتفاع القياسي للأزرار (normal*2 + PAD)
STYLES_LABEL_FIELD_LETTER_SPACING = 0.2  # letter-spacing لـ label_field (px)
STYLES_BADGE_PAD_V              = 2     # padding رأسي لـ badge_accent (px)
STYLES_BADGE_PAD_H              = 8     # padding أفقي لـ badge_accent / badge_count (px)
STYLES_BADGE_COUNT_RADIUS       = 10    # border-radius لـ badge_count (px)
STYLES_BADGE_COUNT_PAD_V        = 1     # padding رأسي لـ badge_count (px)
STYLES_BADGE_COUNT_MIN_W        = 20    # الحد الأدنى لعرض badge_count (px)
STYLES_BTN_PAD_H                = 14    # padding أفقي لأزرار عادية/ghost/success/danger (px)
STYLES_BTN_PRIMARY_PAD_H        = 18    # padding أفقي لزر primary (px)
STYLES_INPUT_PAD_H              = 10    # padding أفقي لحقول الإدخال والبحث (px)
STYLES_COMBO_PAD_H              = 8     # padding أفقي لـ combo_field (px)
STYLES_COMBO_DROPDOWN_BORDER_W  = 1     # سُمك border-left لسهم الـ combo (px)
STYLES_COMBO_DROPDOWN_W         = 22    # عرض سهم القائمة المنسدلة في combo_field (px)

