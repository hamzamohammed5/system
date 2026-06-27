"""
ui/constants.py
===============
ثوابت التطبيق — المصدر الوحيد لكل الثوابت.
لا يستورد من أي ملف آخر في ui/.
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

# ── Confirm Dialog ────────────────────────────────────────
CONFIRM_BTN_MIN_H     = 34   # ارتفاع أدنى لأزرار نافذة التأكيد
CONFIRM_BTN_MIN_W     = 80   # عرض أدنى لأزرار نافذة التأكيد
CONFIRM_MAX_WIDTH     = 520  # عرض أقصى لنافذة التأكيد

# ── Splitter ──────────────────────────────────────────────
SPLITTER_HANDLE_W    = 5
SPLITTER_RATIO       = (1, 2)    # (list, detail)
SPLITTER_APPLY_DELAY = 50        # ms — QTimer.singleShot قبل apply sizes
SPLITTER_RETRY_DELAY = 100       # ms — إعادة المحاولة لو width=0

# ── Notifications / Timers ────────────────────────────────
NOTIF_AUTO_HIDE_SUCCESS = 3000   # ms — BaseDetailPanel.show_success
NOTIF_AUTO_HIDE_DEFAULT = 0      # ms — 0 = لا تختفي تلقائياً

# ── Refresh delays ────────────────────────────────────────
REFRESH_AFTER_SAVE_DELAY = 80    # ms — BaseSection.refresh → _apply_sizes

# ── ComponentRow ──────────────────────────────────────────
COMPONENT_ROW_LOAD_DELAY = 50    # ms — QTimer deferred load للـ variants/op_rows

# ComponentRow — أبعاد الـ widgets
COMPONENT_ROW_OUTER_MARGIN_V   = 2    # top/bottom margin للـ outer layout
COMPONENT_ROW_OUTER_SPACING    = 2    # spacing الـ outer VBoxLayout
COMPONENT_ROW_WASTE_MAX_PCT    = 100  # الحد الأقصى لنسبة الهادر (%)
COMPONENT_ROW_WASTE_MIN_PCT    = 0    # الحد الأدنى لنسبة الهادر (%)
COMPONENT_ROW_WASTE_DECIMALS   = 1    # عدد الخانات العشرية لـ waste_spin
COMPONENT_ROW_MAIN_SPACING     = 6    # spacing الصف الرئيسي
COMPONENT_ROW_VARIANT_MIN_W    = 130  # عرض أدنى لـ cmb_variant
COMPONENT_ROW_VARIANT_MAX_W    = 180  # عرض أقصى لـ cmb_variant
COMPONENT_ROW_QTY_MIN_W        = 60   # عرض أدنى لـ qty_edit / total_qty_edit
COMPONENT_ROW_QTY_MAX_W        = 90   # عرض أقصى لـ qty_edit / total_qty_edit
COMPONENT_ROW_WASTE_MIN_W      = 75   # عرض أدنى لـ waste_spin
COMPONENT_ROW_WASTE_MAX_W      = 90   # عرض أقصى لـ waste_spin
COMPONENT_ROW_WIDGET_MIN_H     = 26   # ارتفاع أدنى للـ widgets (variant, waste, op_row)
COMPONENT_ROW_WASTE_ICON_W     = 18   # عرض ثابت لـ lbl_waste
COMPONENT_ROW_DIVIDE_ICON_W    = 14   # عرض ثابت لـ lbl_total_qty
COMPONENT_ROW_DELETE_BTN_W     = 32   # عرض ثابت لزر الحذف
COMPONENT_ROW_OP_CMB_MIN_W     = 280  # عرض أدنى لـ cmb_op_row
COMPONENT_ROW_SUB_MARGIN_H     = 8    # left/right margin لصف العملية الفرعي
COMPONENT_ROW_SUB_MARGIN_V     = 3    # top/bottom margin لصف العملية الفرعي
COMPONENT_ROW_SUB_SPACING      = 8    # spacing صف العملية الفرعي
COMPONENT_ROW_BORDER_RADIUS    = 4    # border-radius للـ widgets داخل ComponentRow

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

# ── Splitter list offset ───────────────────────────────────
LIST_W_OFFSET = 60   # section._apply_sizes: LIST_MIN_W + LIST_W_OFFSET

# ── Widget-specific heights ────────────────────────────────
SEARCH_BAR_H     = 34   # SearchBar fixed height
STATUS_BAR_H     = 24   # StatusBar fixed height
SECTION_BAR_W    = 3    # SectionHeader accent bar width
SECTION_BAR_H    = 18   # SectionHeader accent bar height

# ── Button dimensions ─────────────────────────────────────
INPUT_HEIGHT_PAD  = 10  # إضافة لـ font*2: h = base*2 + INPUT_HEIGHT_PAD  (→ 32px @ size 11)
BTN_HEIGHT_PAD    = 8   # إضافة لـ font*2: h = base*2 + BTN_HEIGHT_PAD
BTN_PAD_H         = 14  # padding أفقي داخل الزر (padding:0 Xpx)
BTN_BORDER_RADIUS = 6   # border-radius للأزرار
BTN_TEXT_PAD      = 32  # QFontMetrics.horizontalAdvance + BTN_TEXT_PAD
DROPDOWN_ARROW_W  = 24  # عرض سهم القوائم المنسدلة (drop-down arrow)

# ── List header margins ────────────────────────────────────
LIST_HEADER_MARGIN_H = 10   # left/right margin لـ ListHeader
LIST_HEADER_MARGIN_T = 10   # top margin لـ ListHeader
LIST_HEADER_MARGIN_B = 8    # bottom margin لـ ListHeader

# ── Detail header layout ───────────────────────────────────
DETAIL_HEADER_MARGIN_H = 20   # left/right margin لـ DetailHeader
DETAIL_HEADER_MARGIN_T = 14   # top margin لـ DetailHeader

# ── Section header (design/costing/accounting sections) ────
SECTION_HEADER_HEIGHT = 42   # ارتفاع هيدر القسم (DesignSection, CostingSection)

# ── Notification / Warning bars ────────────────────────────
NOTIF_MARGIN_H   = 10   # left/right margin لـ NotificationBar و BaseWarningBar
NOTIF_MARGIN_V   = 6    # top/bottom margin لـ NotificationBar و BaseWarningBar
NOTIF_SPACING    = 8    # spacing بين عناصر NotificationBar
DISMISS_BTN_SIZE = 22   # حجم زر الإغلاق في NotificationBar

# ── ProgressBar ────────────────────────────────────────────
PROGRESS_BAR_H       = 8   # ارتفاع شريط التقدم الافتراضي
PROGRESS_TOP_SPACING = 3   # spacing بين صف العنوان والشريط

# ── LoadingOverlay ─────────────────────────────────────────
OVERLAY_MARGIN        = 20   # margin في LoadingOverlay (كل الجهات)
OVERLAY_BORDER_RADIUS = 8    # border-radius لـ LoadingOverlay

# ── StatCard ──────────────────────────────────────────────
STAT_CARD_MARGIN_COMPACT  = (10, 8, 10, 8)    # margins الـ StatCard compact
STAT_CARD_MARGIN_NORMAL   = (14, 12, 14, 12)  # margins الـ StatCard normal
STAT_CARD_SPACING_COMPACT = 2                  # spacing الـ StatCard compact
STAT_CARD_SPACING_NORMAL  = 3                  # spacing الـ StatCard normal
STAT_CARD_BORDER_RADIUS   = 10                 # border-radius لـ StatCard

# ── _StatCard (inner) ─────────────────────────────────────
STAT_INNER_MARGIN_COMPACT  = (10, 6, 10, 6)   # margins الـ _StatCard compact
STAT_INNER_MARGIN_NORMAL   = (14, 10, 14, 10) # margins الـ _StatCard normal
STAT_INNER_TOP_SPACING     = 4                 # spacing صف العنوان في _StatCard
STAT_INNER_BORDER_RADIUS   = 8                 # border-radius لـ _StatCard

# ── StatusChip ────────────────────────────────────────────
STATUS_CHIP_MARGIN_COMPACT = (10, 6, 10, 6)   # margins الـ StatusChip compact
STATUS_CHIP_MARGIN_NORMAL  = (12, 8, 12, 8)   # margins الـ StatusChip normal
STATUS_CHIP_BORDER_RADIUS  = 8                 # border-radius لـ StatusChip

# ── StatusCard ────────────────────────────────────────────
STATUS_CARD_MARGIN        = (16, 14, 16, 14)  # margins الـ StatusCard
STATUS_CARD_SPACING       = 4                  # spacing الـ StatusCard
STATUS_CARD_BORDER_RADIUS = 12                 # border-radius لـ StatusCard
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
FILTER_COMBO_BORDER_RADIUS   = 4   # border-radius للـ combo وزر reset في FilterToolbar
FILTER_COMBO_PAD_H           = 8   # padding أفقي للـ combo في FilterToolbar
FILTER_CAT_ICON_W            = 20  # عرض label أيقونة التصنيف في FilterToolbar
FILTER_COUNT_LABEL_MIN_W     = 50  # عرض أدنى لـ lbl_count في FilterToolbar

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

# ── ScrollBar ──────────────────────────────────────────────
SCROLL_BAR_WIDTH          = 6    # عرض شريط التمرير الافتراضي

# ── Tab sizes ──────────────────────────────────────────────
TAB_MIN_W_SMALL           = 60   # min-width للتبويب الصغير
TAB_MIN_W_NORMAL          = 80   # min-width للتبويب العادي

# ── Table row heights ──────────────────────────────────────
ROW_HEIGHT_COMPACT        = 34   # ارتفاع صف الجدول (compact)
ROW_HEIGHT_NORMAL         = 40   # ارتفاع صف الجدول (normal)
ROW_HEIGHT_LARGE          = 48   # ارتفاع صف الجدول (large)

# ── ActionToolbar ─────────────────────────────────────────
ACTION_TOOLBAR_FLOW_V_SPACING = 4   # v_spacing لـ FlowLayout في ActionToolbar
ACTION_TOOLBAR_MARGIN_V       = 4   # top/bottom contentsMargins لـ ActionToolbar

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

# ── Accounting Tabs Builder ────────────────────────────────
EQUITY_TAB_SPLITTER_SIZES    = (600, 300)  # أحجام الـ splitter في build_equity_tab (tree, categories)

# ── State Widgets (_state_widgets) ─────────────────────────
STATE_LABEL_PADDING      = 40   # padding لـ labels الحالة (no_company, loading, error)
STATE_ERROR_BORDER_RADIUS= 8    # border-radius لـ make_error_widget
STATE_ERROR_MARGIN       = 20   # margin لـ make_error_widget

# ── _AccountCombo ──────────────────────────────────────────
ACCOUNT_COMBO_GROUP_W          = 130  # عرض ثابت لـ cmb_group في _AccountCombo
ACCOUNT_COMBO_SEARCH_W         = 90   # عرض ثابت لـ inp_search في _AccountCombo
ACCOUNT_COMBO_ACCOUNT_MIN_W    = 200  # عرض أدنى لـ cmb_account في _AccountCombo
ACCOUNT_COMBO_NB_BADGE_W       = 44   # عرض ثابت لـ lbl_nb badge في _AccountCombo
ACCOUNT_COMBO_BADGE_BORDER_RADIUS = 3  # border-radius لـ badge DR/CR في _AccountCombo
ACCOUNT_COMBO_BADGE_PAD_V      = 2    # padding عمودي لـ badge DR/CR في _AccountCombo
ACCOUNT_COMBO_BADGE_PAD_H      = 4    # padding أفقي لـ badge DR/CR في _AccountCombo
ACCOUNT_COMBO_LAYOUT_SPACING   = 4    # spacing بين عناصر الـ HBoxLayout الرئيسي في _AccountCombo

# ── Financial Tabs (balance_sheet, income_statement) ──────
FINANCIAL_TAB_MARGIN_H       = 12   # left/right margin للـ root layout في التبويبات المالية
FINANCIAL_TAB_MARGIN_T       = 10   # top margin للـ root layout في التبويبات المالية
FINANCIAL_TAB_MARGIN_B       = 12   # bottom margin للـ root layout في التبويبات المالية
FINANCIAL_TAB_SPACING        = 10   # spacing للـ root layout في التبويبات المالية
FINANCIAL_SPLITTER_HANDLE_W  = 6    # handleWidth للـ QSplitter في التبويبات المالية
FINANCIAL_TABLE_MARGIN_INNER = 4    # margin داخلي بين الجانبين في الـ splitter (top/side)
FINANCIAL_COL_CODE_W         = 60   # عرض عمود الكود في جداول التبويبات المالية
FINANCIAL_COL_AMOUNT_W       = 110  # عرض عمود المبلغ في جداول التبويبات المالية
FINANCIAL_COL_TYPE_W         = 80   # عرض عمود النوع في جدول الميزانية العمومية
FINANCIAL_BTN_PAD_H          = 12   # padding أفقي لأزرار الحالة في التبويبات المالية
FINANCIAL_COL_AMOUNT_OE_W    = 100  # عرض عمود المبلغ في تبويب حقوق الملكية
FINANCIAL_HDR_BORDER_RADIUS  = 4    # border-radius لهيدر الأقسام في التبويبات المالية
FINANCIAL_HDR_PAD_V          = 4    # padding عمودي لهيدر الأقسام في التبويبات المالية
FINANCIAL_HDR_PAD_H          = 8    # padding أفقي لهيدر الأقسام في التبويبات المالية
FINANCIAL_FRAME_MARGIN_H     = 12   # left/right margin لـ frames في التبويبات المالية
FINANCIAL_FRAME_MARGIN_V     = 8    # top/bottom margin لـ frames في التبويبات المالية
FINANCIAL_FRAME_BORDER_RADIUS= 6    # border-radius لـ frames في التبويبات المالية
FINANCIAL_LEGEND_BORDER_RADIUS= 4   # border-radius لـ legend label في ميزان المراجعة
FINANCIAL_LEGEND_PAD_V       = 4    # padding عمودي لـ legend label في ميزان المراجعة
FINANCIAL_LEGEND_PAD_H       = 10   # padding أفقي لـ legend label في ميزان المراجعة
FINANCIAL_TOTALS_SPACING     = 24   # spacing بين عناصر شريط الإجماليات في ميزان المراجعة
FINANCIAL_TB_SPACING         = 8    # spacing للـ root layout في ميزان المراجعة
FINANCIAL_TB_COL_CODE_W      = 70   # عرض عمود الكود في ميزان المراجعة
FINANCIAL_TB_COL_TYPE_W      = 100  # عرض عمود النوع في ميزان المراجعة
FINANCIAL_TB_COL_DEBIT_W     = 120  # عرض عمود المدين في ميزان المراجعة
FINANCIAL_TB_COL_CREDIT_W    = 120  # عرض عمود الدائن في ميزان المراجعة
FINANCIAL_TB_COL_BALANCE_W   = 110  # عرض عمود الرصيد في ميزان المراجعة

# ── Investor Details Panel ─────────────────────────────────
INVESTOR_DETAIL_MARGIN_H     = 12   # left/right margin للوحة تفاصيل المستثمر
INVESTOR_DETAIL_MARGIN_T     = 8    # top margin للوحة تفاصيل المستثمر
INVESTOR_DETAIL_MARGIN_B     = 12   # bottom margin للوحة تفاصيل المستثمر
INVESTOR_DETAIL_SPACING      = 8    # spacing للوحة تفاصيل المستثمر
INVESTOR_TITLE_BORDER_RADIUS = 6    # border-radius لعنوان المستثمر
INVESTOR_TITLE_PAD_V         = 8    # padding عمودي لعنوان المستثمر
INVESTOR_TITLE_PAD_H         = 14   # padding أفقي لعنوان المستثمر
INVESTOR_DEL_BTN_MIN_H       = 28   # ارتفاع أدنى لزر حذف الحركة
INVESTOR_MOV_COL_DATE_W      = 90   # عرض عمود التاريخ في جدول الحركات
INVESTOR_MOV_COL_TYPE_W      = 90   # عرض عمود النوع في جدول الحركات
INVESTOR_MOV_COL_AMOUNT_W    = 110  # عرض عمود المبلغ في جدول الحركات
INVESTOR_MOV_COL_REF_W       = 95   # عرض عمود المرجع في جدول الحركات

# ── Investors Panel (_investors_panel) ─────────────────────
INVESTOR_FORM_SPLIT_SIZES    = (310, 600)  # (form, table) أحجام الـ splitter الأفقي
INVESTOR_PANEL_TOP_H         = 320         # ارتفاع الجزء العلوي في splitter عمودي
INVESTOR_PANEL_DETAIL_H      = 320         # ارتفاع لوحة التفاصيل في splitter عمودي

# ── Investors Table (_investors_table) ─────────────────────
INVESTOR_TABLE_COL_MAX_W     = 200   # max_width في auto_fit_columns لجدول المستثمرين

# ── Movement Dialog (_movement_dialog) ─────────────────────
MOVEMENT_DIALOG_MIN_W        = 500   # عرض أدنى لنافذة حركة المستثمر
MOVEMENT_DIALOG_SPACING      = 14   # spacing لـ root layout في نافذة الحركة
MOVEMENT_DIALOG_MARGINS      = (20, 16, 20, 16)  # margins نافذة الحركة (l,t,r,b)
MOVEMENT_DIALOG_BTN_H        = 34   # ارتفاع أدنى لأزرار نافذة الحركة
MOVEMENT_DIALOG_TITLE_RADIUS = 6    # border-radius للـ lbl_title في نافذة الحركة
MOVEMENT_DIALOG_TITLE_PAD_V  = 8    # padding عمودي للـ lbl_title في نافذة الحركة
MOVEMENT_DIALOG_TITLE_PAD_H  = 14   # padding أفقي للـ lbl_title في نافذة الحركة
MOVEMENT_DIALOG_PREVIEW_RADIUS = 6  # border-radius للـ lbl_preview في نافذة الحركة
MOVEMENT_DIALOG_PREVIEW_PAD_V  = 8  # padding عمودي للـ lbl_preview في نافذة الحركة
MOVEMENT_DIALOG_PREVIEW_PAD_H  = 12 # padding أفقي للـ lbl_preview في نافذة الحركة

# ── Link To Entry Panel (_link_to_entry_panel) ─────────────
LINK_PANEL_MARGINS           = (12, 10, 12, 10)  # margins لوحة الربط بالقيد (l,t,r,b)
LINK_PANEL_SPACING           = 10   # spacing لـ root layout في لوحة الربط
LINK_PANEL_INFO_RADIUS       = 6    # border-radius للـ lbl_info في لوحة الربط
LINK_PANEL_INFO_PAD          = 10   # padding للـ lbl_info في لوحة الربط

# ── AccountPickerButton ────────────────────────────────────
ACCOUNT_PICKER_NB_LABEL_W        = 44   # عرض ثابت لـ lbl_nb (DR/CR badge) في _AccountPickerButton
ACCOUNT_PICKER_BTN_BORDER_RADIUS = 4    # border-radius لزر الحساب في _AccountPickerButton
ACCOUNT_PICKER_BTN_BORDER_W      = 1    # عرض border لزر الحساب في _AccountPickerButton
ACCOUNT_PICKER_BTN_PAD_V         = 2    # padding عمودي لزر الحساب في _AccountPickerButton
ACCOUNT_PICKER_BTN_PAD_H         = 10   # padding أفقي لزر الحساب في _AccountPickerButton
ACCOUNT_PICKER_BADGE_BORDER_RADIUS = 3  # border-radius لـ badge DR/CR في _AccountPickerButton
ACCOUNT_PICKER_BADGE_PAD_V       = 2    # padding عمودي لـ badge DR/CR في _AccountPickerButton
ACCOUNT_PICKER_BADGE_PAD_H       = 4    # padding أفقي لـ badge DR/CR في _AccountPickerButton
ACCOUNT_PICKER_FIRE_CHANGED_DELAY = 50  # ms — QTimer.singleShot قبل _fire_changed في _AccountPickerButton

# ── AccountTreePopup ───────────────────────────────────────
ACCOUNT_TREE_FONT_SIZE_DELTA_L0   = 1    # زيادة حجم الخط لعناصر المستوى الأول في الشجرة (equity_group, type indent=0)
ACCOUNT_TREE_FONT_SIZE_DELTA_L1   = 0    # زيادة حجم الخط لعناصر المستوى الثاني في الشجرة (type indent=1)
ACCOUNT_TREE_POPUP_MIN_W          = 440  # عرض أدنى لـ _AccountTreePopup
ACCOUNT_TREE_POPUP_MAX_H          = 520  # ارتفاع أقصى لـ _AccountTreePopup
ACCOUNT_TREE_POPUP_MARGINS        = (6, 6, 6, 6)   # contentsMargins لـ root layout في _AccountTreePopup
ACCOUNT_TREE_POPUP_OPEN_W         = 60   # إضافة للعرض عند فتح الـ popup (btn.width + هذا)
ACCOUNT_TREE_POPUP_OPEN_H         = 460  # ارتفاع الـ popup عند الفتح
ACCOUNT_TREE_LIST_BORDER_RADIUS   = 4    # border-radius لـ QListWidget في _AccountTreePopup
ACCOUNT_TREE_LIST_ITEM_PAD_V      = 3    # padding عمودي لـ item في QListWidget
ACCOUNT_TREE_LIST_ITEM_PAD_H      = 6    # padding أفقي لـ item في QListWidget
ACCOUNT_TREE_SEARCH_PAD_V         = 2    # padding عمودي لـ QLineEdit البحث في _AccountTreePopup
ACCOUNT_TREE_SEARCH_PAD_H         = 8    # padding أفقي لـ QLineEdit البحث في _AccountTreePopup
ACCOUNT_TREE_BORDER_W             = 1    # عرض border لـ QDialog و QListWidget في _AccountTreePopup

# ── _BalanceBar ────────────────────────────────────────────
BALANCE_BAR_MARGIN_H         = 14   # left/right margin لـ _BalanceBar layout
BALANCE_BAR_MARGIN_V         = 8    # top/bottom margin لـ _BalanceBar layout
BALANCE_BAR_SPACING          = 4    # spacing بين عناصر _BalanceBar
BALANCE_BAR_BORDER_RADIUS    = 6    # border-radius لـ QFrame في _BalanceBar
BALANCE_BAR_BORDER_W         = 1    # عرض border لـ QFrame في _BalanceBar
BALANCE_BAR_BADGE_RADIUS     = 4    # border-radius لـ badge القيم (DR/CR/diff)
BALANCE_BAR_BADGE_PAD_V      = 3    # padding عمودي لـ badge القيم
BALANCE_BAR_BADGE_PAD_H      = 10   # padding أفقي لـ badge القيم
BALANCE_BAR_BADGE_MARGIN_L   = 4    # margin-left لـ badge القيم

# ── _EntryTypeBadge / _EntryRefLabel ──────────────────────
ENTRY_BADGE_BORDER_W         = 1    # عرض border لـ _EntryTypeBadge
ENTRY_BADGE_BORDER_RADIUS    = 4    # border-radius لـ _EntryTypeBadge
ENTRY_BADGE_PAD_V            = 2    # padding عمودي لـ _EntryTypeBadge
ENTRY_BADGE_PAD_H            = 10   # padding أفقي لـ _EntryTypeBadge
ENTRY_REF_BORDER_W           = 1    # عرض border لـ _EntryRefLabel
ENTRY_REF_BORDER_RADIUS      = 4    # border-radius لـ _EntryRefLabel
ENTRY_REF_PAD_V              = 2    # padding عمودي لـ _EntryRefLabel
ENTRY_REF_PAD_H              = 10   # padding أفقي لـ _EntryRefLabel

# ── _JournalHeader ─────────────────────────────────────────
JOURNAL_HEADER_DATE_W        = 130  # عرض ثابت لـ QDateEdit في _JournalHeader
JOURNAL_HEADER_CMB_W         = 110  # عرض ثابت لـ QComboBox نوع القيد في _JournalHeader
JOURNAL_HEADER_SPACING       = 8    # spacing بين عناصر _JournalHeader layout
JOURNAL_HEADER_CMB_RADIUS    = 4    # border-radius لـ QComboBox في _JournalHeader
JOURNAL_HEADER_CMB_BORDER_W  = 1    # عرض border لـ QComboBox في _JournalHeader
JOURNAL_HEADER_CMB_PAD_V     = 2    # padding عمودي لـ QComboBox في _JournalHeader
JOURNAL_HEADER_CMB_PAD_H     = 6    # padding أفقي لـ QComboBox في _JournalHeader
JOURNAL_HEADER_GROUP_SPACING = 6    # addSpacing بين مجموعات الحقول في _JournalHeader

# ── _TreeGroupCombo ─────────────────────────────────────────
TREE_GROUP_COMBO_BORDER_W          = 1   # عرض border لـ QTreeView في _TreeGroupCombo
TREE_GROUP_COMBO_ITEM_PAD_V        = 3   # padding عمودي لـ item في QTreeView
TREE_GROUP_COMBO_ITEM_PAD_H        = 6   # padding أفقي لـ item في QTreeView
TREE_GROUP_COMBO_ITEM_MIN_H        = 24  # ارتفاع أدنى لـ item في QTreeView
TREE_GROUP_COMBO_HEADER_FONT_DELTA = 1   # زيادة pointSize لخط عناصر الرأس في _TreeGroupCombo

# ── _LinesPanel ─────────────────────────────────────────────
LINES_PANEL_BORDER_W         = 1    # عرض border لـ QFrame الرئيسي في _LinesPanel
LINES_PANEL_BORDER_RADIUS    = 8    # border-radius لـ QFrame الرئيسي في _LinesPanel
LINES_PANEL_HDR_H            = 38   # ارتفاع header الصفوف في _LinesPanel
LINES_PANEL_HDR_BORDER_RADIUS= "7px 7px 0 0"  # border-radius لـ header (أعلى فقط)
LINES_PANEL_HDR_MARGIN_H     = 12   # left/right margin لـ header layout
LINES_PANEL_HDR_MARGIN_V     = 4    # top/bottom margin لـ header layout
LINES_PANEL_BADGE_RADIUS     = 4    # border-radius لـ badge DR/CR في header
LINES_PANEL_BADGE_PAD_V      = 2    # padding عمودي لـ badge DR/CR
LINES_PANEL_BADGE_PAD_H      = 8    # padding أفقي لـ badge DR/CR
LINES_PANEL_HDR_SPACING      = 8    # addSpacing بين badge DR وبادج CR في header
LINES_PANEL_COL_HDR_MARGIN_L = 28   # left margin لـ col_hdr layout
LINES_PANEL_COL_HDR_MARGIN_R = 8    # right margin لـ col_hdr layout
LINES_PANEL_COL_HDR_MARGIN_V = 2    # top/bottom margin لـ col_hdr layout
LINES_PANEL_COL_HDR_SPACING  = 6    # spacing بين أعمدة col_hdr
LINES_PANEL_ROWS_SPACING     = 3    # spacing بين صفوف _rows_lay
LINES_PANEL_ROWS_MARGIN      = 6    # margin كل جهات _rows_lay (6,6,6,6)
LINES_PANEL_SCROLL_MIN_H     = 150  # min-height لـ QScrollArea
LINES_PANEL_SCROLL_MAX_H     = 380  # max-height لـ QScrollArea
LINES_PANEL_BTN_ADD_MIN_H    = 28   # min-height لزر إضافة صف
LINES_PANEL_BTN_ADD_RADIUS   = 4    # border-radius لزر إضافة صف
LINES_PANEL_BTN_ADD_BORDER_W = 1    # عرض border لزر إضافة صف
LINES_PANEL_BTN_ADD_PAD_V    = 2    # padding عمودي لزر إضافة صف
LINES_PANEL_BTN_ADD_PAD_H    = 12   # padding أفقي لزر إضافة صف
LINES_PANEL_BTN_ADD_MARGIN_V = 4    # top/bottom margin لزر إضافة صف
LINES_PANEL_BTN_ADD_MARGIN_H = 8    # left/right margin لزر إضافة صف

# ── _SmartLine ───────────────────────────────────────────────
SMART_LINE_BORDER_RADIUS     = 6    # border-radius لـ QFrame الرئيسي في _SmartLine
SMART_LINE_BORDER_W          = 1    # عرض border لـ QFrame في _SmartLine
SMART_LINE_MARGIN_H          = 6    # left/right margin لـ root layout في _SmartLine
SMART_LINE_MARGIN_V          = 4    # top/bottom margin لـ root layout في _SmartLine
SMART_LINE_SPACING           = 4    # spacing لـ root VBoxLayout في _SmartLine
SMART_LINE_MAIN_ROW_SPACING  = 6    # spacing للـ main_row HBoxLayout
SMART_LINE_MOVE_BTN_SIZE     = 18   # حجم أزرار ▲▼ (عرض وارتفاع)
SMART_LINE_DIR_FRAME_W       = 130  # عرض ثابت لـ dir_frame
SMART_LINE_DIR_SPACING       = 3    # spacing بين زري الاتجاه
SMART_LINE_AMOUNT_MIN_H      = 28   # min-height لـ QDoubleSpinBox
SMART_LINE_AMOUNT_W          = 110  # عرض ثابت لـ QDoubleSpinBox
SMART_LINE_AMOUNT_MAX        = 999_999_999  # الحد الأقصى للمبلغ
SMART_LINE_AMOUNT_DECIMALS   = 2    # عدد الخانات العشرية للمبلغ
SMART_LINE_DESC_MIN_H        = 28   # min-height لـ QLineEdit البيان
SMART_LINE_DEL_BTN_SIZE      = 22   # حجم زر الحذف ✖ (عرض وارتفاع)
SMART_LINE_INV_ROW_RADIUS    = 4    # border-radius لـ investor_row QFrame
SMART_LINE_INV_ROW_BORDER_W  = 1    # عرض border لـ investor_row QFrame
SMART_LINE_INV_ROW_MARGIN_T  = 2    # margin-top لـ investor_row
SMART_LINE_INV_MARGIN_H      = 8    # left/right margin لـ inv_lay
SMART_LINE_INV_MARGIN_V      = 4    # top/bottom margin لـ inv_lay
SMART_LINE_INV_SPACING       = 8    # spacing بين عناصر inv_lay
SMART_LINE_INV_LBL_W         = 95   # عرض ثابت لـ lbl_inv
SMART_LINE_INV_CMB_MIN_H     = 24   # min-height لـ cmb_investor
SMART_LINE_ACCENT_BORDER_W   = 3    # عرض border-right للـ accent bar (DR/CR) في _SmartLine

# ── _JournalFilterBar ────────────────────────────────────
JOURNAL_FILTER_BORDER_W       = 1    # عرض border لـ QFrame و inputs في _JournalFilterBar
JOURNAL_FILTER_MARGIN_H       = 10   # left/right margin لـ root layout
JOURNAL_FILTER_MARGIN_V       = 8    # top/bottom margin لـ root layout
JOURNAL_FILTER_SPACING        = 6    # spacing لـ root VBoxLayout
JOURNAL_FILTER_ROW_SPACING    = 8    # spacing لـ row1 و row2 HBoxLayout
JOURNAL_FILTER_INPUT_MIN_H    = 30   # min-height للـ inputs والـ combos
JOURNAL_FILTER_ICON_W         = 20   # عرض ثابت لـ icon labels (🔍 📅)
JOURNAL_FILTER_INPUT_RADIUS   = 5    # border-radius للـ inputs والـ combos
JOURNAL_FILTER_INPUT_PAD_V    = 2    # padding عمودي للـ inputs والـ combos
JOURNAL_FILTER_INPUT_PAD_H    = 8    # padding أفقي للـ inputs والـ combos
JOURNAL_FILTER_DROP_W         = 20   # عرض drop-down arrow في QComboBox
JOURNAL_FILTER_GROUP_CMB_MIN_W= 200  # min-width لـ cmb_group
JOURNAL_FILTER_GROUP_CMB_MAX_W= 280  # max-width لـ cmb_group
JOURNAL_FILTER_BAL_CMB_W      = 120  # عرض ثابت لـ cmb_balance
JOURNAL_FILTER_BTN_RESET_MIN_H= 28   # min-height لزر مسح الفلاتر
JOURNAL_FILTER_BTN_RESET_W    = 95   # عرض ثابت لزر مسح الفلاتر
JOURNAL_FILTER_COUNT_MIN_W    = 70   # min-width لـ lbl_count

# ── _JournalForm ─────────────────────────────────────────
JOURNAL_FORM_MARGIN_H         = 12   # left/right margin لـ root layout في _JournalForm
JOURNAL_FORM_MARGIN_V         = 10   # top/bottom margin لـ root layout في _JournalForm
JOURNAL_FORM_SPACING          = 8    # spacing لـ root VBoxLayout و _btn_row
JOURNAL_FORM_BTN_MIN_H        = 34   # min-height لأزرار الحفظ والمسح
JOURNAL_FORM_BTN_RADIUS       = 6    # border-radius لأزرار _JournalForm
JOURNAL_FORM_BTN_SAVE_PAD_H   = 20   # padding أفقي لزر الحفظ
JOURNAL_FORM_BTN_CANCEL_PAD_H = 14   # padding أفقي لزر المسح
JOURNAL_FORM_BORDER_W         = 1    # عرض border لزر المسح

# ── _JournalFilterBar — logic constants ─────────────────
JOURNAL_BALANCE_EPSILON            = 0.01   # حد التسامح لاعتبار القيد متوازناً
JOURNAL_FILTER_DEFAULT_FROM_YEAR   = 2020   # سنة بداية نطاق التاريخ الافتراضي
JOURNAL_FILTER_DEFAULT_FROM_MONTH  = 1      # شهر بداية نطاق التاريخ الافتراضي
JOURNAL_FILTER_DEFAULT_FROM_DAY    = 1      # يوم بداية نطاق التاريخ الافتراضي

# ── JournalTab (journal_tab_widget) ──────────────────────
JOURNAL_TAB_SPLITTER_HANDLE_W  = 6          # handleWidth للـ QSplitter الرأسي في JournalTab
JOURNAL_TAB_SPLITTER_SIZES     = (440, 360) # الأحجام الافتراضية (form, table) في JournalTab

# ── _JournalTreeTable — layout & columns ─────────────────
JOURNAL_TREE_COL_TOGGLE_W   = 28   # عرض عمود ▶/▼ في _JournalTreeTable
JOURNAL_TREE_COL_DATE_W     = 92   # عرض عمود التاريخ في _JournalTreeTable
JOURNAL_TREE_COL_REF_W      = 85   # عرض عمود رقم القيد في _JournalTreeTable
JOURNAL_TREE_COL_DR_W       = 95   # عرض عمود المدين في _JournalTreeTable
JOURNAL_TREE_COL_CR_W       = 95   # عرض عمود الدائن في _JournalTreeTable
JOURNAL_TREE_COL_STATUS_W   = 85   # عرض عمود الحالة في _JournalTreeTable

# ── _LedgerFilterBar — move type combo ───────────────────
LEDGER_MOVE_CMB_MIN_H    = 28    # ارتفاع أدنى لـ cmb_move_type في _LedgerFilterBar
LEDGER_MOVE_CMB_W        = 120   # عرض ثابت لـ cmb_move_type في _LedgerFilterBar

# ── _StatCards (ledger) ───────────────────────────────────
LEDGER_STAT_BORDER_RADIUS = 8    # border-radius لـ QFrame في _StatCards
LEDGER_STAT_BORDER_W      = 1    # عرض border لـ QFrame في _StatCards

# ── _TAccountPanel — T-table columns ─────────────────────
T_ACCOUNT_COL_DATE_W    = 90    # عرض عمود التاريخ في T-table
T_ACCOUNT_COL_REF_W     = 80    # عرض عمود رقم القيد في T-table
T_ACCOUNT_COL_AMT_W     = 90    # عرض عمود المبلغ في T-table
T_ACCOUNT_FRAME_RADIUS  = 8     # border-radius لإطار T-Account
T_ACCOUNT_HDR_RADIUS    = 5     # border-radius لهيدر جانب DR/CR
T_ACCOUNT_HDR_PAD       = 5     # padding هيدر جانب DR/CR
T_ACCOUNT_TOT_RADIUS    = 4     # border-radius لـ lbl_dr/cr_total
T_ACCOUNT_TOT_PAD_V     = 4     # padding عمودي لـ lbl_dr/cr_total
T_ACCOUNT_TOT_PAD_H     = 8     # padding أفقي لـ lbl_dr/cr_total
T_ACCOUNT_DR_MARGIN     = (8, 8, 4, 8)  # margins جانب المدين (l,t,r,b)
T_ACCOUNT_CR_MARGIN     = (4, 8, 8, 8)  # margins جانب الدائن (l,t,r,b)
T_ACCOUNT_SEP_W         = 2     # عرض فاصل VLine بين جانبي DR/CR في T-Account
T_ACCOUNT_SIDE_SPACING  = 4     # spacing بين عناصر جانب DR/CR
T_ACCOUNT_FRAME_BORDER_W = 2     # عرض border إطار T-Account الخارجي
T_ACCOUNT_HDR_BORDER_W   = 1     # عرض border-bottom لـ QHeaderView::section في T-table
T_ACCOUNT_HDR_CELL_PAD   = 4     # padding خلايا header الجدول في T-table
T_ACCOUNT_ROOT_SPACING  = 6     # spacing الـ root layout في _TAccountPanel

# ── _AccountsPanel — columns ──────────────────────────────
ACCOUNTS_PANEL_COL_CODE_W          = 65   # عرض عمود الكود في _AccountsPanel
ACCOUNTS_PANEL_COL_BAL_W           = 90   # عرض عمود الرصيد في _AccountsPanel
ACCOUNTS_PANEL_TYPE_FILTER_MARGIN  = (8, 4, 8, 4)  # margins لـ AccountTypeFilter في _AccountsPanel

# ── _AccountForm ──────────────────────────────────────────
ACCOUNT_FORM_ROOT_MARGIN       = (6, 8, 10, 10)  # contentsMargins الـ root layout في _AccountForm
ACCOUNT_FORM_ROOT_SPACING      = 8                # spacing الـ root layout في _AccountForm
ACCOUNT_FORM_GRP_BORDER_W      = 1                # عرض border لـ QGroupBox في _AccountForm
ACCOUNT_FORM_GRP_BORDER_RADIUS = 6                # border-radius لـ QGroupBox في _AccountForm
ACCOUNT_FORM_GRP_MARGIN_TOP    = 8                # margin-top لـ QGroupBox في _AccountForm
ACCOUNT_FORM_GRP_PAD_TOP       = 8                # padding-top لـ QGroupBox في _AccountForm
ACCOUNT_FORM_GRP_TITLE_PAD_H   = 6                # padding أفقي لعنوان QGroupBox في _AccountForm
ACCOUNT_FORM_FL_SPACING        = 8                # spacing لـ QFormLayout في _AccountForm
ACCOUNT_FORM_INPUT_MIN_H       = 28               # min-height للـ inputs والـ combos في _AccountForm
ACCOUNT_FORM_BTN_MIN_H         = 28               # min-height لأزرار _AccountForm
