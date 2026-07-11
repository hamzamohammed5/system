"""
ui/constants_data/general.py
=======================
ثوابت عامة مشتركة (أحجام، مسافات، أبعاد panels، مكوّنات UI أساسية)
جزء من تقسيم ui/constants.py — راجع ui/constants/__init__.py.
"""

# ── حجم الخط ──────────────────────────────────────────────
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20

# ── أبعاد الـ Sidebar ─────────────────────────────────────
SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56

# ── أبعاد النافذة ─────────────────────────────────────────
CONTENT_MIN_WIDTH    = 820
WINDOW_DEFAULT_W     = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH
WINDOW_DEFAULT_H     = 700   # الارتفاع الافتراضي للنافذة الرئيسية
WINDOW_MIN_H         = 500   # الارتفاع الأدنى للنافذة الرئيسية
WINDOW_MIN_CONTENT_W = 600   # عرض المحتوى الأدنى (بدون sidebar)

# ── Spacing & Margins ─────────────────────────────────────
# استخدم دي في كل الـ widgets بدل أرقام hardcoded
SPACING_XS = 4
SPACING_SM = 6
SPACING_MD = 8
SPACING_LG = 12
SPACING_XL = 16
SPACING_ZERO = 0   # لـ layouts بدون مسافة (مثل root layouts)
SPACING_MD_LG = 10   # بين SPACING_MD وSPACING_LG — لفورمات تبويبات المخزون (وارد/صادر)

# ── Margins (left, top, right, bottom) ───────────────────
MARGIN_ZERO          = (0, 0, 0, 0)
MARGIN_FORM          = (8, 8, 8, 8)       # BaseCrudForm inner layout
MARGIN_CONTENT_PANEL = (16, 14, 16, 16)   # BaseDetailPanel content area

# ── أبعاد الـ Panels ──────────────────────────────────────
# BaseSection
LIST_PANEL_MIN_W  = 280
LIST_PANEL_MAX_W  = 560
DETAIL_PANEL_MIN_W = 320

# BaseDetailPanel
DETAIL_CONTENT_MIN_W = 500
DETAIL_MIN_W         = 300
DETAIL_EMPTY_MIN_H   = 200    # EmptyState min_height

# BaseCrudForm
FORM_MIN_W       = 260
BTN_MIN_HEIGHT   = 30

# ── Dialog Shell ──────────────────────────────────────────
DIALOG_HDR_H_WITH_SUB  = 64           # ارتفاع header النافذة مع subtitle
DIALOG_HDR_H           = 52           # ارتفاع header النافذة بدون subtitle
DIALOG_BTN_BAR_H       = 54           # ارتفاع شريط الأزرار في النافذة
DIALOG_BTN_MIN_H       = 36           # ارتفاع أدنى لأزرار النوافذ
DIALOG_MIN_WIDTH       = 380          # عرض أدنى افتراضي للنوافذ
DIALOG_BODY_MARGINS    = (20, 16, 20, 12)  # margins منطقة المحتوى (l,t,r,b)
DIALOG_HDR_MARGIN_H    = 16           # left/right margin لـ header النافذة
DIALOG_HDR_COL_SPACING = 2            # spacing عمود العنوان/subtitle في header
DIALOG_BTN_PAD_H       = 20           # padding أفقي لأزرار النافذة ذات accent مخصص
MSG_BTN_MIN_H          = 32           # ارتفاع أدنى لأزرار MessageDialog
BASE_DIALOG_DEFAULT_SIZE = (500, 400)  # أبعاد BaseDialog الافتراضية (عرض, ارتفاع)

# ── Confirm Dialog ────────────────────────────────────────
CONFIRM_BTN_MIN_H     = 34   # ارتفاع أدنى لأزرار نافذة التأكيد
CONFIRM_BTN_MIN_W     = 80   # عرض أدنى لأزرار نافذة التأكيد
CONFIRM_MAX_WIDTH     = 520  # عرض أقصى لنافذة التأكيد

# ── Settings Dialog ───────────────────────────────────────
SETTINGS_DLG_MIN_W       = 560   # عرض أدنى لنافذة الإعدادات
SETTINGS_DLG_MIN_H       = 480   # ارتفاع أدنى لنافذة الإعدادات
SETTINGS_SWATCH_SIZE     = 36    # حجم مربع عينة اللون (عرض × ارتفاع) في تبويب الثيم
SETTINGS_GIMP_DEFAULT_DIR = r"C:\Program Files"  # مسار البحث الافتراضي عن GIMP
SETTINGS_TAB_MARGINS     = (20, 16, 20, 16)  # margins محتوى كل تبويب في نافذة الإعدادات
SETTINGS_CARD_MARGINS    = (12, 8, 12, 8)    # margins بطاقة الثيم/اللغة
SETTINGS_BTN_BAR_MARGINS = (20, 8, 20, 8)    # margins شريط الأزرار السفلي
SETTINGS_UNITS_LIST_MIN_H = 140              # ارتفاع أدنى لقائمة الوحدات
SETTINGS_VAL_LBL_MIN_W    = 44               # عرض أدنى لِلابل قيمة حجم الخط
SETTINGS_CLEAR_BTN_W      = 28               # عرض زر مسح مسار GIMP
SETTINGS_PREVIEW_RADIUS    = 6    # border-radius لمعاينة الخط ولـ tab bar
SETTINGS_PREVIEW_PAD       = 12   # padding لمعاينة الخط
SETTINGS_CARD_RADIUS       = 8    # border-radius لبطاقة الثيم/اللغة
SETTINGS_SWATCH_RADIUS     = 6    # border-radius لمربع عينة اللون
SETTINGS_CARD_INNER_PAD    = 4    # padding داخلي لبطاقة الثيم/اللغة (fallback في stylesheet)
SETTINGS_GIMP_INPUT_RADIUS = 4    # border-radius لحقل مسار GIMP
SETTINGS_GIMP_INPUT_PAD_H  = 8    # padding أفقي لحقل مسار GIMP
SETTINGS_NOTICE_RADIUS     = 6    # border-radius للافتة "اختر شركة نشطة"
SETTINGS_NOTICE_PAD_V      = 6    # padding رأسي للافتة التنبيه
SETTINGS_NOTICE_PAD_H      = 10   # padding أفقي للافتة التنبيه
SETTINGS_TAB_PAD_V         = 8    # padding رأسي لتبويب QTabBar
SETTINGS_TAB_PAD_H         = 18   # padding أفقي لتبويب QTabBar
SETTINGS_TAB_MIN_W         = 80   # عرض أدنى لتبويب QTabBar

# ── Splitter ──────────────────────────────────────────────
SPLITTER_HANDLE_W    = 5
SPLITTER_HANDLE_BORDER_W = 1  # عرض border-top/bottom لـ QSplitter handle
SPLITTER_RATIO       = (1, 2)    # (list, detail)
SPLITTER_APPLY_DELAY = 50        # ms — QTimer.singleShot قبل apply sizes
SPLITTER_RETRY_DELAY = 100       # ms — إعادة المحاولة لو width=0

# ── Notifications / Timers ────────────────────────────────
NOTIF_AUTO_HIDE_SUCCESS = 3000   # ms — BaseDetailPanel.show_success
NOTIF_AUTO_HIDE_DEFAULT = 0      # ms — 0 = لا تختفي تلقائياً

# ── Refresh delays ────────────────────────────────────────
REFRESH_AFTER_SAVE_DELAY = 80    # ms — BaseSection.refresh → _apply_sizes

# ── Pagination Bar ────────────────────────────────────────
PAGINATION_BAR_H       = 44    # ارتفاع شريط الـ pagination
PAGINATION_BTN_SPACING = 10    # مسافة بين أزرار الـ pagination
PAGINATION_BTN_RADIUS  = 6     # border-radius لأزرار الـ pagination
PAGINATION_BTN_PAD_H   = 14    # padding أفقي لزر "تحميل المزيد"
PAGINATION_BTN_PAD_H_SM= 8     # padding أفقي لزر "عرض الكل"

# ── BaseListPanel ─────────────────────────────────────────
LIST_PANEL_MIN_W_DEFAULT = 260   # MIN_W الافتراضي لـ BaseListPanel
FILTER_DEBOUNCE_MS       = 250   # تأخير الـ timer قبل تطبيق الفلتر
LIST_EMPTY_MIN_H         = 100   # EmptyState min_height في list panel

# ── Table helpers ──────────────────────────────────────────
TABLE_EXTRA_PAD = 24    # extra_pad في fit_splitter_table
COL_MIN_WIDTH   = 40    # auto_fit_columns — min_width
COL_MAX_WIDTH   = 300   # auto_fit_columns — max_width

# ── Table build helpers ────────────────────────────────────────
TABLE_MIN_SECTION_SIZE      = 30    # minimumSectionSize للـ QHeaderView الأفقي
TABLE_MIN_HEIGHT_DEFAULT    = 120   # min_height الافتراضي لـ make_table
TABLE_COMPACT_MAX_HEIGHT    = 300   # max_height الافتراضي لـ make_compact_table
TABLE_SPLITTER_MIN_HEIGHT   = 80    # min_height الافتراضي لجداول الـ splitter
TABLE_SPLITTER_EXTRA_PAD    = 24    # extra_pad الافتراضي في make_splitter_table
TABLE_SPLITTER_HANDLE_W     = 0     # handleWidth للـ QSplitter المحيط بالجدول
CALC_WIDTH_EXTRA_PAD        = 24    # extra_pad الافتراضي في calc_width
TABLE_COL_DEFAULT_W         = 100   # عرض العمود الافتراضي في _build_table
TABLE_FIXED_COL_DEFAULT_W   = 100   # عرض العمود الافتراضي في make_fixed_table
TABLE_FIXED_WIDTH_PAD       = 4     # padding إضافي لحساب fixed width الكلي
TABLE_ROW_MIN_SECTION_PAD   = 4     # يُطرح من row_height لـ minimumSectionSize

# ── Splitter list panel ────────────────────────────────────
SPLITTER_LIST_MIN_W      = 280   # عرض أدنى للوحة القائمة في fit_list_panel
SPLITTER_LIST_MAX_W      = 620   # عرض أقصى للوحة القائمة في fit_list_panel
SMART_SPLITTER_HANDLE_W  = 4     # handleWidth لـ SmartSplitter
SPLITTER_PANEL_MIN_W     = 200   # عرض أدنى لأي panel داخل SmartSplitter
SPLITTER_SCROLL_GUARD_EXTRA_PAD = 20   # extra_pad الافتراضي في SplitterScrollGuard
SMART_SPLITTER_FIT_DELAY_MS     = 50   # delay_ms الافتراضي في SmartSplitter.fit_delayed

# ── SearchableCombo ────────────────────────────────────────
SEARCHABLE_COMBO_SEARCH_W     = 90    # عرض حقل البحث في SearchableCombo
SEARCHABLE_COMBO_SEARCH_H     = 28    # ارتفاع أدنى لحقل البحث في SearchableCombo
SEARCHABLE_COMBO_CLEAR_SIZE   = 20    # حجم زر مسح البحث (عرض وارتفاع)
SEARCHABLE_COMBO_CMB_MIN_W    = 150   # عرض أدنى للـ QComboBox في SearchableCombo
SEARCHABLE_COMBO_INNER_RADIUS = 4     # border-radius لحقل البحث في SearchableCombo
SEARCHABLE_COMBO_PAD_H        = 6     # padding أفقي لحقل البحث في SearchableCombo
SEARCHABLE_COMBO_PAD_V        = 2     # padding عمودي لحقل البحث في SearchableCombo
SEARCHABLE_COMBO_SEARCH_DELAY = 120   # debounce delay (ms) لـ SearchableCombo

# ── DateRangeFilter ────────────────────────────────────────
DATE_RANGE_EDIT_W        = 115   # عرض QDateEdit الافتراضي في DateRangeFilter
DATE_RANGE_EDIT_H        = 30    # ارتفاع أدنى لـ QDateEdit في DateRangeFilter
DATE_RANGE_EDIT_RADIUS   = 5     # border-radius لـ QDateEdit في DateRangeFilter
DATE_RANGE_EDIT_PAD_H    = 6     # padding أفقي لـ QDateEdit
DATE_RANGE_EDIT_PAD_V    = 2     # padding عمودي لـ QDateEdit
DATE_RANGE_DROPDOWN_W    = 20    # عرض زر القائمة المنسدلة في QDateEdit
DATE_RANGE_LAYOUT_SPACING = 6    # spacing بين عناصر DateRangeFilter

# ── Splitter list offset ───────────────────────────────────
LIST_W_OFFSET = 60   # section._apply_sizes: LIST_MIN_W + LIST_W_OFFSET

# ── Widget-specific heights ────────────────────────────────
SEARCH_BAR_H     = 34   # SearchBar fixed height
STATUS_BAR_H     = 24   # StatusBar fixed height
SEARCH_BAR_BORDER_W      = 1.5  # عرض border لحقل SearchBar
SEARCH_BAR_BORDER_RADIUS = 6    # border-radius لحقل SearchBar
SEARCH_BAR_PAD_H         = 10   # padding أفقي لحقل SearchBar
STATUS_BAR_PAD_H         = 10   # padding أفقي لـ StatusBar
STATUS_BAR_BORDER_W      = 1    # عرض border-top لـ StatusBar
SECTION_BAR_W    = 3    # SectionHeader accent bar width
SECTION_BAR_H    = 18   # SectionHeader accent bar height
SECTION_BAR_RADIUS = 2  # border-radius لـ SectionHeader accent bar

# ── Button dimensions ─────────────────────────────────────
INPUT_HEIGHT_PAD  = 10  # إضافة لـ font*2: h = base*2 + INPUT_HEIGHT_PAD  (→ 32px @ size 11)
BTN_HEIGHT_PAD    = 8   # إضافة لـ font*2: h = base*2 + BTN_HEIGHT_PAD
BTN_PAD_H         = 14  # padding أفقي داخل الزر (padding:0 Xpx)
BTN_BORDER_RADIUS = 6   # border-radius للأزرار
BTN_TEXT_PAD      = 32  # QFontMetrics.horizontalAdvance + BTN_TEXT_PAD
BTN_BORDER_W      = 1.5 # عرض border للأزرار (make_btn)
DROPDOWN_ARROW_W  = 24  # عرض سهم القوائم المنسدلة (drop-down arrow)

# ── List header margins ────────────────────────────────────
LIST_HEADER_MARGIN_H = 10   # left/right margin لـ ListHeader
LIST_HEADER_MARGIN_T = 10   # top margin لـ ListHeader
LIST_HEADER_MARGIN_B = 8    # bottom margin لـ ListHeader
LIST_HEADER_BORDER_W = 1    # عرض border-bottom لـ ListHeader

# ── Detail header layout ───────────────────────────────────
DETAIL_HEADER_MARGIN_H = 20   # left/right margin لـ DetailHeader
DETAIL_HEADER_MARGIN_T = 14   # top margin لـ DetailHeader
DETAIL_HEADER_BORDER_W = 1    # عرض border-bottom لـ DetailHeader
PAGE_HEADER_MARGIN_H         = 20   # left/right margin لـ PageHeader (وضع عادي)
PAGE_HEADER_MARGIN_V         = 14   # top/bottom margin لـ PageHeader (وضع عادي)
PAGE_HEADER_MARGIN_H_COMPACT = 12   # left/right margin لـ PageHeader (وضع compact)
PAGE_HEADER_MARGIN_V_COMPACT = 8    # top/bottom margin لـ PageHeader (وضع compact)
PAGE_HEADER_BORDER_W         = 1    # عرض border-bottom لـ PageHeader

# ── Section header (design/costing/accounting sections) ────
SECTION_HEADER_HEIGHT = 42   # ارتفاع هيدر القسم (DesignSection, CostingSection)
SECTION_HEADER_BORDER_W = 1  # عرض border-bottom لهيدر القسم (DesignSection, CostingSection)
SECTION_HEADER_PAD_RIGHT = 16  # padding-right لهيدر القسم (DesignSection, CostingSection)

# ── Notification / Warning bars ────────────────────────────
NOTIF_MARGIN_H   = 10   # left/right margin لـ NotificationBar و BaseWarningBar
NOTIF_MARGIN_V   = 6    # top/bottom margin لـ NotificationBar و BaseWarningBar
NOTIF_SPACING    = 8    # spacing بين عناصر NotificationBar
NOTIF_BORDER_W   = 1    # عرض border لـ NotificationBar و BaseWarningBar
DISMISS_BTN_SIZE = 22   # حجم زر الإغلاق في NotificationBar

# ── ProgressBar ────────────────────────────────────────────
PROGRESS_BAR_H       = 8   # ارتفاع شريط التقدم الافتراضي
PROGRESS_TOP_SPACING = 3   # spacing بين صف العنوان والشريط
PROGRESS_THRESHOLD_SUCCESS = 90  # % — الحد الأدنى لعرض لون success في ProgressBar
PROGRESS_THRESHOLD_NORMAL  = 60  # % — الحد الأدنى لعرض اللون الأساسي في ProgressBar
PROGRESS_THRESHOLD_WARNING = 30  # % — الحد الأدنى لعرض لون warning في ProgressBar (أقل منه = danger)

# ── LoadingOverlay ─────────────────────────────────────────
OVERLAY_MARGIN        = 20   # margin في LoadingOverlay (كل الجهات)
SPINNER_FRAME_INTERVAL_MS = 100  # ms — سرعة تبديل frames الأنيميشن في LoadingSpinner/LoadingButton
OVERLAY_BORDER_RADIUS = 8    # border-radius لـ LoadingOverlay

# ── Offer Form (pricing offers) ────────────────────────────
OFFER_FORM_SCROLL_MIN_H   = 110   # min-height لـ scroll area في فورم العرض
OFFER_FORM_SCROLL_MAX_H   = 260   # max-height لـ scroll area في فورم العرض
OFFER_FORM_DISC_W         = 90    # عرض ثابت لـ spinbox الخصم في فورم العرض
OFFER_FORM_CAT_W          = 150   # عرض ثابت لـ combo التصنيف في فورم العرض
OFFER_FORM_HDR_ICON_W     = 20    # عرض عمود أيقونة في رأس الأعمدة
OFFER_FORM_HDR_DEL_W      = 28    # عرض عمود حذف في رأس الأعمدة
OFFER_FORM_HDR_SEARCH_W   = 120   # عرض عمود البحث في رأس الأعمدة
OFFER_FORM_HDR_COST_W     = 72    # عرض عمود التكلفة في رأس الأعمدة
OFFER_FORM_HDR_PRICE_W    = 72    # عرض عمود السعر في رأس الأعمدة
OFFER_FORM_HDR_QTY_W      = 85    # عرض عمود الكمية في رأس الأعمدة
OFFER_FORM_HDR_TOTAL_W    = 80    # عرض عمود الإجمالي في رأس الأعمدة
OFFER_ROW_PRODUCT_COMBO_W = 180   # عرض أدنى لـ combo المنتج في صف العرض

# ── Offers Tab (OffersTab) ─────────────────────────────────
OFFERS_TAB_SPLITTER_HANDLE_W = 6    # handleWidth للـ splitter في OffersTab
OFFERS_TAB_FORM_SIZE         = 320  # حجم لوحة الفورم الابتدائي في splitter العمودي
OFFERS_TAB_BOTTOM_SIZE       = 480  # حجم لوحة الجزء السفلي الابتدائي في splitter العمودي
OFFERS_TAB_TABLE_SIZE        = 480  # حجم لوحة الجدول الابتدائي في splitter الأفقي
OFFERS_TAB_DETAILS_SIZE      = 420  # حجم لوحة التفاصيل الابتدائي في splitter الأفقي

# ── Offers Table (_OffersTable) ────────────────────────────
OFFERS_TABLE_ROOT_MARGIN   = (12, 8, 12, 10)  # contentsMargins لـ root layout
OFFERS_TABLE_COL0_ID_W     = 35    # عرض عمود ID
OFFERS_TABLE_COL1_NAME_W   = 140   # عرض عمود اسم العرض
OFFERS_TABLE_COL2_CAT_W    = 90    # عرض عمود التصنيف
OFFERS_TABLE_COL3_COUNT_W  = 80    # عرض عمود عدد المنتجات
OFFERS_TABLE_COL4_DISC_W   = 55    # عرض عمود نسبة الخصم
OFFERS_TABLE_COL5_LISTED_W = 85    # عرض عمود الإجمالي قبل الخصم
OFFERS_TABLE_COL6_SELL_W   = 80    # عرض عمود سعر البيع
OFFERS_TABLE_COL7_COST_W   = 75    # عرض عمود التكلفة
OFFERS_TABLE_COL8_PROFIT_W = 75    # عرض عمود الربح
OFFERS_TABLE_COL9_DATE_W   = 120   # عرض عمود التاريخ

# ── StatBox (pricing stat_box helper) ─────────────────────
STAT_BOX_BORDER_RADIUS    = 6    # border-radius لـ stat_box QFrame
STAT_BOX_BORDER_W         = 1    # عرض border لـ stat_box QFrame
STAT_BOX_PADDING          = 4    # padding الخارجي لـ stat_box QFrame

# ── StatCard ──────────────────────────────────────────────
STAT_CARD_MARGIN_COMPACT  = (10, 8, 10, 8)    # margins الـ StatCard compact
STAT_CARD_MARGIN_NORMAL   = (14, 12, 14, 12)  # margins الـ StatCard normal
STAT_CARD_SPACING_COMPACT = 2                  # spacing الـ StatCard compact
STAT_CARD_SPACING_NORMAL  = 3                  # spacing الـ StatCard normal
STAT_CARD_BORDER_RADIUS   = 10                 # border-radius لـ StatCard
STAT_CARD_BORDER_W        = 1                  # عرض border لـ StatCard

# ── _StatCard (inner) ─────────────────────────────────────
STAT_INNER_MARGIN_COMPACT  = (10, 6, 10, 6)   # margins الـ _StatCard compact
STAT_INNER_MARGIN_NORMAL   = (14, 10, 14, 10) # margins الـ _StatCard normal
STAT_INNER_TOP_SPACING     = 4                 # spacing صف العنوان في _StatCard
STAT_INNER_BORDER_RADIUS   = 8                 # border-radius لـ _StatCard
STAT_INNER_BORDER_W        = 1                 # عرض border لـ _StatCard

# ── StatusChip ────────────────────────────────────────────
STATUS_CHIP_MARGIN_COMPACT = (10, 6, 10, 6)   # margins الـ StatusChip compact
STATUS_CHIP_MARGIN_NORMAL  = (12, 8, 12, 8)   # margins الـ StatusChip normal
STATUS_CHIP_BORDER_RADIUS  = 8                 # border-radius لـ StatusChip
STATUS_CHIP_BORDER_W       = 1                 # عرض border لـ StatusChip

# ── StatusCard ────────────────────────────────────────────
STATUS_CARD_MARGIN        = (16, 14, 16, 14)  # margins الـ StatusCard
STATUS_CARD_SPACING       = 4                  # spacing الـ StatusCard
STATUS_CARD_BORDER_RADIUS = 12                 # border-radius لـ StatusCard
STATUS_CARD_BORDER_W      = 1                  # عرض border لـ StatusCard
# ── ColorPickerWidget ──────────────────────────────────────
COLOR_PICKER_PREVIEW_SIZE   = 28   # حجم مربع معاينة اللون (عرض وارتفاع)
COLOR_PICKER_PREVIEW_RADIUS = 4    # border-radius لمربع معاينة اللون

# ── FilterToolbar ─────────────────────────────────────────
FILTER_TOOLBAR_MARGIN_H  = 8    # left/right margin لـ FilterToolbar
FILTER_TOOLBAR_MARGIN_V  = 6    # top/bottom margin لـ FilterToolbar
FILTER_TOOLBAR_SPACING   = 8    # spacing بين عناصر FilterToolbar
FILTER_COMBO_MIN_H       = 28   # ارتفاع أدنى للـ combo في FilterToolbar
FILTER_COMBO_MIN_W       = 160  # عرض أدنى للـ combo في FilterToolbar
FILTER_RESET_BTN_W       = 32   # عرض زر reset في FilterToolbar
FILTER_SEARCH_H          = 28   # ارتفاع SearchBar في FilterToolbar
FILTER_TOOLBAR_BORDER_RADIUS = 6   # border-radius لـ FilterToolbar QWidget
FILTER_BAR_BORDER_RADIUS     = 8   # border-radius لـ filter_bar_style QFrame
TREE_BORDER_RADIUS           = 6   # border-radius لـ QTreeWidget
LIST_BORDER_RADIUS           = 4   # border-radius لـ QListWidget
TABLE_BORDER_RADIUS          = 8   # border-radius لـ QTableWidget

# ── table_style variants (padding) ──────────────────────────
TABLE_STYLE_COMPACT_ITEM_PAD_V   = 4    # padding رأسي لعنصر الجدول (compact)
TABLE_STYLE_COMPACT_ITEM_PAD_H   = 6    # padding أفقي لعنصر الجدول (compact)
TABLE_STYLE_LARGE_ITEM_PAD_V     = 8    # padding رأسي لعنصر الجدول (large)
TABLE_STYLE_LARGE_ITEM_PAD_H     = 12   # padding أفقي لعنصر الجدول (large)
TABLE_STYLE_NORMAL_ITEM_PAD_V    = 5    # padding رأسي لعنصر الجدول (normal)
TABLE_STYLE_NORMAL_ITEM_PAD_H    = 10   # padding أفقي لعنصر الجدول (normal)
TABLE_STYLE_NORMAL_HEADER_PAD_V  = 6    # padding رأسي لهيدر الجدول (normal)
TABLE_STYLE_NORMAL_HEADER_PAD_H  = 10   # padding أفقي لهيدر الجدول (normal)
SPLITTER_HANDLE_RADIUS           = 3    # border-radius لمقبض QSplitter
FILTER_COMBO_BORDER_RADIUS   = 4   # border-radius للـ combo وزر reset في FilterToolbar
FILTER_COMBO_PAD_H           = 8   # padding أفقي للـ combo في FilterToolbar
FILTER_COMBO_PAD_V           = 2   # padding عمودي للـ combo في FilterToolbar
FILTER_CAT_ICON_W            = 20  # عرض label أيقونة التصنيف في FilterToolbar
FILTER_COUNT_LABEL_MIN_W     = 50  # عرض أدنى لـ lbl_count في FilterToolbar
FILTER_DATE_DEFAULT_FROM     = (2000, 1, 1)  # تاريخ البداية الافتراضي لنطاق التاريخ (سنة، شهر، يوم)

# ── Separator line ─────────────────────────────────────────
SEPARATOR_LINE_H = 1   # ارتفاع فاصل HLine (detail_section، form_group)

# ── DetailSection ─────────────────────────────────────────
DETAIL_SECTION_RADIUS    = 10   # border-radius لـ DetailSection
DETAIL_SECTION_MARGIN_B  = 12   # bottom margin لـ DetailSection root layout
DETAIL_SECTION_HDR_MARGIN_H = 12  # left/right margin للهيدر في DetailSection
DETAIL_GRID_MARGIN_H     = 12   # left/right margin للـ grid في DetailSection
DETAIL_GRID_H_SPACING    = 16   # horizontal spacing للـ grid في DetailSection
DETAIL_GRID_V_SPACING    = 10   # vertical spacing للـ grid في DetailSection (normal)
DETAIL_GRID_V_SPACING_C  = 6    # vertical spacing للـ grid في DetailSection (compact)
DETAIL_GRID_PAD_COMPACT  = 4    # top/bottom padding للـ grid (compact)
DETAIL_GRID_PAD_NORMAL   = 6    # top/bottom padding للـ grid (normal)
DETAIL_LABEL_MIN_W       = 80   # عرض أدنى لـ label العنوان في DetailSection
TWO_COL_H_SPACING        = 24   # horizontal spacing في TwoColDetails
TWO_COL_V_SPACING        = 8    # vertical spacing في TwoColDetails

# ── FormFields ────────────────────────────────────────────
FORM_FIELD_DEFAULT_H     = 30   # min_height الافتراضي لـ spin_field / int_spin_field
FORM_HINT_SPACING        = 2    # spacing بين الـ widget والـ hint label في field_row
FORM_LAYOUT_SPACING      = 10   # spacing الافتراضي لـ make_form_layout
FORM_LAYOUT_MARGIN       = (12, 10, 12, 10)  # contentsMargins الافتراضية لـ make_form_layout
LABELED_WIDGET_SPACING   = 6    # spacing الافتراضي لـ labeled_widget
LABELED_INPUT_SPACING    = 8    # spacing الافتراضي لـ LabeledInput (label ↔ widget)

# ── FormBadges ────────────────────────────────────────────
BADGE_LABEL_PAD_V        = 3    # padding عمودي لـ BadgeLabel
BADGE_LABEL_PAD_H        = 12   # padding أفقي لـ BadgeLabel
BADGE_LABEL_BORDER_RADIUS= 20   # border-radius لـ BadgeLabel
BADGE_LABEL_BORDER_W     = 1.5  # عرض border لـ BadgeLabel (px)
DR_CR_DISPLAY_SPACING     = 12   # spacing بين عناصر DebitCreditDisplay
DR_CR_CHIP_BORDER_RADIUS  = 4    # border-radius لـ chip الـ DR/CR في DebitCreditDisplay
DR_CR_CHIP_PAD_V          = 3    # padding عمودي لـ chip الـ DR/CR
DR_CR_CHIP_PAD_H          = 10   # padding أفقي لـ chip الـ DR/CR
BALANCE_DISPLAY_BORDER_W  = 1    # عرض border لـ BalanceDisplay
BALANCE_DISPLAY_RADIUS    = 6    # border-radius لـ BalanceDisplay
BALANCE_DISPLAY_PAD_V     = 6    # padding عمودي لـ BalanceDisplay
BALANCE_DISPLAY_PAD_H     = 16   # padding أفقي لـ BalanceDisplay
BADGE_BORDER_RADIUS      = 4    # border-radius لـ ResultBadge / ModeBadge
BADGE_PAD_H              = 8    # padding أفقي لـ ResultBadge / ModeBadge
BADGE_PAD_V              = 4    # padding عمودي لـ ResultBadge
MODE_BADGE_PAD_V         = 3    # padding عمودي لـ ModeBadge
PREVIEW_LABEL_RADIUS     = 6    # border-radius لـ make_preview_label
PREVIEW_LABEL_PAD_V      = 8    # padding عمودي لـ make_preview_label
PREVIEW_LABEL_PAD_H      = 12   # padding أفقي لـ make_preview_label
INLINE_PREVIEW_SPACING   = 8    # spacing بين عناصر InlinePreview

# ── CategoryManager ────────────────────────────────────────
CATEGORY_MANAGER_MARGIN  = (0, 0, 0, 0)   # contentsMargins للـ CategoryManager layout
CATEGORY_MANAGER_SPACING = 6               # spacing بين عناصر CategoryManager
CATEGORY_FORM_SPACING    = 6               # spacing داخل QFormLayout في CategoryForm
CATEGORY_TREE_COL0_W     = 200             # عرض عمود الاسم في شجرة التصنيفات
CATEGORY_TREE_COL1_W     = 80             # عرض عمود التصنيفات الفرعية
CATEGORY_TREE_COL2_W     = 80             # عرض عمود الكمية

# ── FormGroup ─────────────────────────────────────────────
FORM_GROUP_BORDER_RADIUS = 10   # border-radius لـ FormGroup QGroupBox
FORM_GROUP_MARGIN_TOP    = 10   # margin-top لـ FormGroup QGroupBox
FORM_GROUP_PADDING_TOP   = 6    # padding-top لـ FormGroup QGroupBox
FORM_GROUP_TITLE_PAD_H   = 8    # padding أفقي للعنوان في FormGroup::title
FORM_GROUP_FORM_MARGIN   = (12, 14, 12, 12)  # contentsMargins لـ QFormLayout داخل FormGroup

# ── CollapsibleCard ───────────────────────────────────────
COLLAPSIBLE_CARD_HDR_BORDER_RADIUS  = "10px 10px 0 0"   # border-radius لزر header CollapsibleCard
COLLAPSIBLE_CARD_HDR_PAD_V          = 10                 # padding عمودي لزر header CollapsibleCard
COLLAPSIBLE_CARD_HDR_PAD_H          = 14                 # padding أفقي لزر header CollapsibleCard
COLLAPSIBLE_CARD_CONTENT_MARGIN_H   = 12                 # left/right margin لـ content_layout
COLLAPSIBLE_CARD_CONTENT_MARGIN_V   = 10                 # top/bottom margin لـ content_layout (approx)
COLLAPSIBLE_CARD_CONTENT_SPACING    = 8                  # spacing لـ content_layout

# ── EmptyState ────────────────────────────────────────────
EMPTY_STATE_SPACING          = 6    # spacing الافتراضي لـ EmptyState layout
EMPTY_STATE_SPACING_EXPANDED = 8    # spacing لـ EmptyState (expandable)
EMPTY_STATE_MARGIN_H         = 20   # left/right margin لـ EmptyState layout
EMPTY_STATE_MARGIN_V         = 16   # top/bottom margin لـ EmptyState layout (normal)
EMPTY_STATE_MARGIN_V_EXPANDED= 30   # top/bottom margin لـ EmptyState layout (expandable)
EMPTY_STATE_BORDER_RADIUS    = 10   # border-radius لـ EmptyState QFrame
EMPTY_STATE_ACTION_BTN_W     = 140  # عرض زر الإجراء في EmptyState (غير expandable)
EMPTY_STATE_TABLE_ROW_H      = 60   # ارتفاع صف الحالة الفارغة في الجداول
EMPTY_STATE_DEFAULT_MIN_H    = 80   # min_height الافتراضي لـ EmptyState (غير محدد)

# ── CardGrid ──────────────────────────────────────────────
CARD_GRID_DEFAULT_COLS    = 4    # عدد الأعمدة الافتراضي لـ CardGrid
CARD_GRID_DEFAULT_SPACING = 10   # spacing الافتراضي لـ CardGrid

# ── Card / Frame styles ────────────────────────────────────
CARD_BORDER_RADIUS        = 10   # border-radius افتراضي لـ card_style (QFrame)
STATUS_CARD_STYLE_RADIUS  = 8    # border-radius لـ status_card_style (QFrame)

# ── Input heights ──────────────────────────────────────────
INPUT_HEIGHT              = 32   # min-height افتراضي لـ QLineEdit / QComboBox / QSpinBox
SEARCH_INPUT_HEIGHT       = 34   # min-height لـ search_input_style (= SEARCH_BAR_H)
AMOUNT_SPINBOX_MAX        = 999_999_999  # الحد الأقصى الافتراضي لـ AmountSpinBox
NOTES_LINE_EDIT_HEIGHT    = 30   # ارتفاع افتراضي لـ NotesLineEdit

# ── ScrollBar ──────────────────────────────────────────────
SCROLL_BAR_WIDTH          = 6    # عرض شريط التمرير الافتراضي
SCROLL_HANDLE_MIN_LEN     = 30   # الحد الأدنى لطول مقبض الـ scrollbar (عمودي/أفقي)

# ── Tab sizes ──────────────────────────────────────────────
TAB_MIN_W_SMALL           = 60   # min-width للتبويب الصغير
TAB_MIN_W_NORMAL          = 80   # min-width للتبويب العادي
TAB_PAD_V_SMALL           = 6    # padding رأسي لتبويب صغير
TAB_PAD_H_SMALL           = 12   # padding أفقي لتبويب صغير
TAB_PAD_V_NORMAL          = 8    # padding رأسي لتبويب عادي
TAB_PAD_H_NORMAL          = 16   # padding أفقي لتبويب عادي

# ── Tree / List item padding ─────────────────────────────────
TREE_ITEM_PAD_V           = 3    # padding رأسي لعنصر QTreeWidget
TREE_ITEM_PAD_H           = 2    # padding أفقي لعنصر QTreeWidget
LIST_ITEM_PAD_V           = 3    # padding رأسي لعنصر QListWidget
LIST_ITEM_PAD_H           = 6    # padding أفقي لعنصر QListWidget
LIST_ITEM_BORDER_W        = 1    # عرض border-bottom لعنصر QListWidget

# ── Table row heights ──────────────────────────────────────
ROW_HEIGHT_COMPACT        = 34   # ارتفاع صف الجدول (compact)
ROW_HEIGHT_NORMAL         = 40   # ارتفاع صف الجدول (normal)
ROW_HEIGHT_LARGE          = 48   # ارتفاع صف الجدول (large)

# ── ActionToolbar ─────────────────────────────────────────
ACTION_TOOLBAR_FLOW_V_SPACING = 4   # v_spacing لـ FlowLayout في ActionToolbar
ACTION_TOOLBAR_MARGIN_V       = 4   # top/bottom contentsMargins لـ ActionToolbar
ACTION_TOOLBAR_DEFAULT_SPACING = 6  # spacing الافتراضي لـ ActionToolbar.__init__
DETAIL_HEADER_TOOLBAR_SPACING  = 8  # spacing لـ ActionToolbar داخل DetailHeader._ensure_toolbar

# ── FlowLayout ───────────────────────────────────────────────
FLOW_LAYOUT_DEFAULT_H_SPACING = 6   # h_spacing الافتراضي لـ FlowLayout
FLOW_LAYOUT_DEFAULT_V_SPACING = 4   # v_spacing الافتراضي لـ FlowLayout

# ── Divider ────────────────────────────────────────────────
V_DIVIDER_WIDTH           = 1    # عرض الفاصل العمودي الافتراضي
V_DIVIDER_MARGIN_V        = 4    # margin عمودي للفاصل العمودي الافتراضي

# ── FlexibleTable / WrapDelegate ───────────────────────
FLEX_WRAP_MIN_ROW_H    = 36   # ارتفاع صف أدنى لـ WrapDelegate
FLEX_WRAP_PADDING      = 4    # padding أفقي داخل خلية WrapDelegate
FLEX_DEFAULT_COL_WIDTH = 150  # عرض العمود الافتراضي في sizeHint لو لم يُحدَّد
FLEX_TABLE_MIN_ROW_H   = 36   # ارتفاع صف أدنى لـ make_flexible_table / set_flexible_columns
FLEX_ROW_HEIGHT_PAD    = 8    # padding عمودي يُضاف لارتفاع النص في sizeHint

# ── V_Divider (inner) ──────────────────────────────────
V_DIVIDER_INNER_MARGIN_H  = 0    # margin أفقي داخلي للفاصل العمودي

# ── Input styles ───────────────────────────────────────
INPUT_BORDER_RADIUS       = 6    # border-radius لـ QLineEdit / QComboBox / QSpinBox
INPUT_PAD_H               = 8    # padding أفقي لـ input_style / spinbox_style
INPUT_BORDER_W            = 1    # عرض border لـ input_style / spinbox_style
SEARCH_PAD_H              = 10   # padding أفقي لـ search_input_style

# ── Label styles ───────────────────────────────────────
STATUS_LABEL_RADIUS       = 4    # border-radius لـ status_label_style
STATUS_LABEL_PAD_V        = 2    # padding عمودي لـ status_label_style
STATUS_LABEL_PAD_H        = 8    # padding أفقي لـ status_label_style
LINK_BTN_RADIUS           = 4    # border-radius لـ link_btn_style

# ── Sidebar nav ────────────────────────────────────────────
NAV_BTN_H            = 38   # ارتفاع زر التنقل الثابت (_NavButton, _sidebar)
NAV_BTN_W_OFFSET     = 16   # فرق عرض الزر عن SIDEBAR_EXPANDED_WIDTH
NAV_ICO_W            = 22   # عرض label الأيقونة في _NavButton
NAV_ICO_FS           = 15   # حجم خط الأيقونة (ثابت بصري للـ sidebar)
NAV_BTN_HEIGHT_PAD   = 14   # padding لحساب ارتفاع الزر الديناميكي (base*2 + pad)
BADGE_FS             = 8    # حجم خط badge الإشعار في _NavButton
SIDEBAR_COMPANY_H    = 46   # ارتفاع CompanySelector في الـ sidebar
SIDEBAR_TOGGLE_H     = 36   # ارتفاع زر طي/فرد الـ sidebar (_ToggleButton)
SIDEBAR_DIVIDER_H    = 1    # ارتفاع الفاصل الأفقي في footer الـ sidebar
SIDEBAR_SCROLL_W     = 3    # عرض scrollbar الـ sidebar (px)
SIDEBAR_SCROLL_MIN_H = 20   # min-height لـ handle الـ scrollbar في الـ sidebar

# ── _NavButton layout ──────────────────────────────────────
NAV_LAYOUT_MARGIN_H   = 10   # left/right margin لـ QHBoxLayout داخل _NavButton
NAV_LAYOUT_SPACING    = 10   # spacing الـ QHBoxLayout داخل _NavButton
NAV_BTN_BORDER_RADIUS = 6    # border-radius لزر _NavButton (checked + unchecked)
NAV_BADGE_PAD_V       = 1    # padding عمودي لـ badge label في _NavButton
NAV_BADGE_PAD_H       = 6    # padding أفقي لـ badge label في _NavButton
NAV_BADGE_RADIUS      = 8    # border-radius لـ badge label في _NavButton
NAV_ACTIVE_BORDER_W   = 2    # عرض border-right للزر النشط في _NavButton
TAB_INDICATOR_BORDER_W = 2  # عرض border-top لـ tab نشط (QTabBar)

# ── _SectionLabel ──────────────────────────────────────────
SECTION_LABEL_PAD_TOP     = 12      # padding-top لـ _SectionLabel
SECTION_LABEL_PAD_H       = 16      # padding left/right لـ _SectionLabel
SECTION_LABEL_PAD_BOT     = 4       # padding-bottom لـ _SectionLabel
SECTION_LABEL_LTR_SPACING = "1.5px" # letter-spacing لـ _SectionLabel

# ── _Sidebar nav & footer layout ──────────────────────────
SIDEBAR_NAV_MARGIN      = 8    # margin كل جهات nav_lay في _Sidebar
SIDEBAR_NAV_SPACING     = 1    # spacing بين عناصر nav_lay في _Sidebar
SIDEBAR_FOOTER_MARGIN_H = 8    # left/right margin لـ f_lay في footer الـ _Sidebar
SIDEBAR_FOOTER_MARGIN_V = 4    # top/bottom margin لـ f_lay في footer الـ _Sidebar
SIDEBAR_FOOTER_SPACING  = 1    # spacing بين عناصر f_lay في footer الـ _Sidebar
SIDEBAR_DIV_MARGIN_V    = 2    # top/bottom margin للفاصل الأفقي في footer الـ _Sidebar
SIDEBAR_DIV_MARGIN_H    = 4    # left/right margin للفاصل الأفقي في footer الـ _Sidebar
SIDEBAR_ANIM_DURATION   = 200  # مدة أنيميشن طي/فرد الـ _Sidebar (ms)
SIDEBAR_TOGGLE_BORDER_W = 1    # عرض border-top لـ _ToggleButton
SIDEBAR_SCROLL_RADIUS   = 1    # border-radius لـ scrollbar track/handle في _Sidebar
SIDEBAR_BORDER_W        = 1    # عرض border الـ frame وفواصل header الـ sidebar

# ── Offer Form buttons padding ─────────────────────────────
OFFER_ADD_ROW_BTN_PAD_V = 4    # padding عمودي لزر «إضافة منتج» في فورم العرض
OFFER_ADD_ROW_BTN_PAD_H = 12   # padding أفقي لزر «إضافة منتج» في فورم العرض
OFFER_SAVE_BTN_PAD_H    = 18   # padding أفقي لزر «حفظ» في فورم العرض

# ── Offer Item Row search input padding ───────────────────
OFFER_ROW_SEARCH_PAD_V  = 2    # padding عمودي لحقل البحث في صف العرض
OFFER_ROW_SEARCH_PAD_H  = 6    # padding أفقي لحقل البحث في صف العرض

# ── Offer Details table column widths ─────────────────────
OFFER_DET_COL1_CAT_W    = 90   # عرض عمود التصنيف في جدول تفاصيل العرض
OFFER_DET_COL2_QTY_W    = 55   # عرض عمود الكمية في جدول تفاصيل العرض
OFFER_DET_COL3_COST_W   = 80   # عرض عمود تكلفة الوحدة في جدول تفاصيل العرض
OFFER_DET_COL4_PRICE_W  = 75   # عرض عمود سعر الوحدة في جدول تفاصيل العرض
OFFER_DET_COL5_TOTAL_W  = 90   # عرض عمود إجمالي السطر في جدول تفاصيل العرض
OFFER_DET_COL6_PROFIT_W = 80   # عرض عمود ربح السطر في جدول تفاصيل العرض

# ── Pricing Panel (_PricingPanel) ──────────────────────────
PRICING_PANEL_SPIN_MIN_H       = 30    # min-height لـ QDoubleSpinBox في _spin
PRICING_PANEL_ROOT_MARGIN      = (12, 10, 12, 12)  # contentsMargins لـ root layout
PRICING_PANEL_ROOT_SPACING     = 8     # spacing لـ root layout
PRICING_PANEL_BTN_ROW_SPACING  = 8     # spacing لصف الأزرار (buttons_row)
PRICING_PANEL_FORM_FRAME_RADIUS = 8    # border-radius لإطار الفورم
PRICING_PANEL_FORM_FRAME_BORDER_W = 1  # عرض border لإطار الفورم
PRICING_PANEL_FORM_MARGIN      = (14, 12, 14, 12)  # contentsMargins لـ form layout
PRICING_PANEL_FORM_SPACING     = 10    # spacing لـ form layout
PRICING_PANEL_ROW1_SPACING     = 12    # spacing لصف حقول المنتج/الهامش/السعر
PRICING_PANEL_CMB_PRODUCT_MIN_H = 32   # min-height لـ combo المنتج
PRICING_PANEL_CMB_PRODUCT_MIN_W = 200  # min-width لـ combo المنتج
PRICING_PANEL_SP_MARGIN_W      = 110   # عرض ثابت لـ spinbox الهامش
PRICING_PANEL_SP_PRICE_W       = 130   # عرض ثابت لـ spinbox السعر
PRICING_PANEL_ROW1_INNER_SPACING = 8   # addSpacing بين مجموعات الحقول في row1
PRICING_PANEL_STATS_ROW_SPACING= 8     # spacing لصف بطاقات الإحصاء
PRICING_PANEL_TABLE_COL0_ID_W   = 40   # عرض عمود ID
PRICING_PANEL_TABLE_COL1_NAME_W = 160  # عرض عمود المنتج
PRICING_PANEL_TABLE_COL2_CAT_W  = 100  # عرض عمود التصنيف
PRICING_PANEL_TABLE_COL3_COST_W = 80   # عرض عمود التكلفة
PRICING_PANEL_TABLE_COL4_MARGIN_W = 70 # عرض عمود الهامش %
PRICING_PANEL_TABLE_COL5_PRICE_W  = 80 # عرض عمود السعر
PRICING_PANEL_TABLE_COL6_PROFIT_W = 80 # عرض عمود الربح
PRICING_PANEL_TABLE_COL7_MARGIN_ACTUAL_W = 90  # عرض عمود الهامش الفعلي %
