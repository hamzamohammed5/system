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
CONTENT_MIN_WIDTH = 820
WINDOW_DEFAULT_W  = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH

# ── Spacing & Margins ─────────────────────────────────────
# استخدم دي في كل الـ widgets بدل أرقام hardcoded
SPACING_XS = 4
SPACING_SM = 6
SPACING_MD = 8
SPACING_LG = 12
SPACING_XL = 16

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

# ── Pagination Bar ────────────────────────────────────────
PAGINATION_BAR_H       = 44    # ارتفاع شريط الـ pagination
PAGINATION_BTN_SPACING = 10    # مسافة بين أزرار الـ pagination

# ── BaseListPanel ─────────────────────────────────────────
LIST_PANEL_MIN_W_DEFAULT = 260   # MIN_W الافتراضي لـ BaseListPanel
FILTER_DEBOUNCE_MS       = 250   # تأخير الـ timer قبل تطبيق الفلتر
LIST_EMPTY_MIN_H         = 100   # EmptyState min_height في list panel

# ── Table helpers ──────────────────────────────────────────
TABLE_EXTRA_PAD = 24    # extra_pad في fit_splitter_table
COL_MIN_WIDTH   = 40    # auto_fit_columns — min_width
COL_MAX_WIDTH   = 300   # auto_fit_columns — max_width

# ── Splitter list offset ───────────────────────────────────
LIST_W_OFFSET = 60   # section._apply_sizes: LIST_MIN_W + LIST_W_OFFSET

# ── Widget-specific heights ────────────────────────────────
SEARCH_BAR_H     = 34   # SearchBar fixed height
STATUS_BAR_H     = 24   # StatusBar fixed height
SECTION_BAR_W    = 3    # SectionHeader accent bar width
SECTION_BAR_H    = 18   # SectionHeader accent bar height

# ── Button dimensions ─────────────────────────────────────
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

# ── FormBadges ────────────────────────────────────────────
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
