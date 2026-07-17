# دليل الكود — UI / Constants

> `ui/constants.py` (المُجمِّع) + كل ملفات `ui/constants_data/*.py` (7 ملفات دومين).
> يغطي كل ثوابت التصميم (أحجام، مسافات، ألوان hex ثابتة، حدود، radii، إلخ) المستخدمة عبر طبقة الـ UI بالكامل.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [constants (مُجمِّع)](#constants-مُجمِّع) | `ui/constants.py` |
| [constants_general](#constants_general) | `ui/constants_data/constants_general.py` |
| [constants_accounting](#constants_accounting) | `ui/constants_data/constants_accounting.py` |
| [constants_costing](#constants_costing) | `ui/constants_data/constants_costing.py` |
| [constants_design](#constants_design) | `ui/constants_data/constants_design.py` |
| [constants_inventory](#constants_inventory) | `ui/constants_data/constants_inventory.py` |
| [constants_orders](#constants_orders) | `ui/constants_data/constants_orders.py` |
| [constants_companies](#constants_companies) | `ui/constants_data/constants_companies.py` |

---

## constants (مُجمِّع)

### `ui/constants.py`

**الغرض:** نقطة الدخول الوحيدة لاستيراد أي ثابت تصميم في المشروع. لا يحتوي أي ثابت مباشرة — **مُجمِّع (aggregator)** فقط يجمع كل ملفات `ui/constants_data/` بـ `import *` بنفس واجهة الاستيراد القديمة (`from ui.constants import X` يستمر بالعمل بلا تغيير).

```python
from ui.constants_data.constants_general import *      # noqa: F401,F403
from ui.constants_data.constants_accounting import *    # noqa: F401,F403
from ui.constants_data.constants_costing import *       # noqa: F401,F403
from ui.constants_data.constants_design import *        # noqa: F401,F403
from ui.constants_data.constants_inventory import *     # noqa: F401,F403
from ui.constants_data.constants_orders import *        # noqa: F401,F403
from ui.constants_data.constants_companies import *     # noqa: F401,F403
```

**لا imports خارجية أخرى، ولا منطق، ولا تعريف ثوابت مباشرة.**

**من يستدعي هذا الملف:** كل ملفات `ui/` تقريباً (widgets, tabs, main_window_helper, main_window) عبر `from ui.constants import CONST_NAME`.

---

## constants_general

### `ui/constants_data/constants_general.py`

**الغرض:** أكبر ملف ثوابت — يغطي الثوابت العامة المشتركة عبر كل التطبيق: حجم الخط، أبعاد الـ sidebar والنافذة، spacing/margins موحّدة، أبعاد الـ panels الأساسية (BaseSection/BaseDetailPanel/BaseCrudForm)، Dialog Shell، Confirm Dialog، Settings Dialog، Splitter، Pagination، جداول (Table helpers)، مكوّنات widgets عامة (SearchableCombo, DateRangeFilter, ActionToolbar, FlowLayout, FlexibleTable)، أزرار وInputs، Sidebar nav بالكامل، Offer Form/StatBox/StatCard/StatusChip/StatusCard، ColorPickerWidget، FilterToolbar، CategoryManager، FormGroup، CollapsibleCard، EmptyState، CardGrid، وPricing Panel.

**لا imports خارجية — قيم رقمية/نصية ثابتة فقط.**

**أهم الثوابت حسب المجموعة:**

```python
# ── حجم الخط ──
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20

# ── Sidebar ──
SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56

# ── النافذة ──
CONTENT_MIN_WIDTH    = 820
WINDOW_DEFAULT_W     = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH
WINDOW_DEFAULT_H     = 700
WINDOW_MIN_H         = 500
WINDOW_MIN_CONTENT_W = 600

# ── Spacing (استخدم بدل أرقام hardcoded) ──
SPACING_XS = 4; SPACING_SM = 6; SPACING_MD = 8; SPACING_LG = 12; SPACING_XL = 16
SPACING_ZERO = 0; SPACING_MD_LG = 10

# ── Margins ──
MARGIN_ZERO          = (0, 0, 0, 0)
MARGIN_FORM          = (8, 8, 8, 8)
MARGIN_CONTENT_PANEL = (16, 14, 16, 16)

# ── أبعاد Panels (BaseSection/BaseDetailPanel/BaseCrudForm) ──
LIST_PANEL_MIN_W = 280; LIST_PANEL_MAX_W = 560; DETAIL_PANEL_MIN_W = 320
DETAIL_CONTENT_MIN_W = 500; DETAIL_MIN_W = 300; DETAIL_EMPTY_MIN_H = 200
FORM_MIN_W = 260; BTN_MIN_HEIGHT = 30
```

**Dialog Shell:**
```python
DIALOG_HDR_H_WITH_SUB = 64; DIALOG_HDR_H = 52; DIALOG_BTN_BAR_H = 54
DIALOG_BTN_MIN_H = 36; DIALOG_MIN_WIDTH = 380
DIALOG_BODY_MARGINS = (20, 16, 20, 12); DIALOG_HDR_MARGIN_H = 16
DIALOG_HDR_COL_SPACING = 2; DIALOG_BTN_PAD_H = 20; MSG_BTN_MIN_H = 32
BASE_DIALOG_DEFAULT_SIZE = (500, 400)
```

**Confirm Dialog:** `CONFIRM_BTN_MIN_H=34`, `CONFIRM_BTN_MIN_W=80`, `CONFIRM_MAX_WIDTH=520`.

**Settings Dialog:** ثوابت شاملة لكل تبويبات `SettingsDialog` (خط/ثيم/لغة/وحدات/GIMP) — `SETTINGS_DLG_MIN_W/H`, `SETTINGS_SWATCH_SIZE`, `SETTINGS_GIMP_DEFAULT_DIR`, `SETTINGS_TAB_MARGINS`, `SETTINGS_CARD_MARGINS`, `SETTINGS_BTN_BAR_MARGINS`, `SETTINGS_UNITS_LIST_MIN_H`, `SETTINGS_VAL_LBL_MIN_W`, `SETTINGS_CLEAR_BTN_W`, `SETTINGS_PREVIEW_RADIUS/PAD`, `SETTINGS_CARD_RADIUS`, `SETTINGS_SWATCH_RADIUS`, `SETTINGS_GIMP_INPUT_RADIUS/PAD_H`, `SETTINGS_NOTICE_RADIUS/PAD_V/PAD_H`, `SETTINGS_TAB_PAD_V/H/MIN_W`.

**Splitter:** `SPLITTER_HANDLE_W=5`, `SPLITTER_HANDLE_BORDER_W=1`, `SPLITTER_RATIO=(1,2)` (list, detail), `SPLITTER_APPLY_DELAY=50`, `SPLITTER_RETRY_DELAY=100`.

**Notifications/Timers:** `NOTIF_AUTO_HIDE_SUCCESS=3000`, `NOTIF_AUTO_HIDE_DEFAULT=0`, `REFRESH_AFTER_SAVE_DELAY=80`.

**Pagination Bar:** `PAGINATION_BAR_H=44`, `PAGINATION_BTN_SPACING=10`, `PAGINATION_BTN_RADIUS=6`, `PAGINATION_BTN_PAD_H=14`, `PAGINATION_BTN_PAD_H_SM=8`.

**BaseListPanel:** `LIST_PANEL_MIN_W_DEFAULT=260`, `FILTER_DEBOUNCE_MS=250`, `LIST_EMPTY_MIN_H=100`.

**Table helpers (عامة ومشتركة بكل الجداول في المشروع):**
```python
TABLE_EXTRA_PAD = 24; COL_MIN_WIDTH = 40; COL_MAX_WIDTH = 300
TABLE_MIN_SECTION_SIZE = 30; TABLE_MIN_HEIGHT_DEFAULT = 120
TABLE_COMPACT_MAX_HEIGHT = 300; TABLE_SPLITTER_MIN_HEIGHT = 80
TABLE_SPLITTER_EXTRA_PAD = 24; TABLE_SPLITTER_HANDLE_W = 0
CALC_WIDTH_EXTRA_PAD = 24; TABLE_COL_DEFAULT_W = 100
TABLE_FIXED_COL_DEFAULT_W = 100; TABLE_FIXED_WIDTH_PAD = 4
TABLE_ROW_MIN_SECTION_PAD = 4
```

**Splitter list panel:** `SPLITTER_LIST_MIN_W=280`, `SPLITTER_LIST_MAX_W=620`, `SMART_SPLITTER_HANDLE_W=4`, `SPLITTER_PANEL_MIN_W=200`, `SPLITTER_SCROLL_GUARD_EXTRA_PAD=20`, `SMART_SPLITTER_FIT_DELAY_MS=50`.

**SearchableCombo:** `SEARCHABLE_COMBO_SEARCH_W=90`, `_SEARCH_H=28`, `_CLEAR_SIZE=20`, `_CMB_MIN_W=150`, `_INNER_RADIUS=4`, `_PAD_H=6`, `_PAD_V=2`, `_SEARCH_DELAY=120` (debounce ms).

**DateRangeFilter:** `DATE_RANGE_EDIT_W=115`, `_EDIT_H=30`, `_EDIT_RADIUS=5`, `_EDIT_PAD_H=6`, `_EDIT_PAD_V=2`, `_DROPDOWN_W=20`, `_LAYOUT_SPACING=6`.

**Widget-specific heights:** `SEARCH_BAR_H=34`, `STATUS_BAR_H=24`, `SEARCH_BAR_BORDER_W=1.5`, `SEARCH_BAR_BORDER_RADIUS=6`, `SEARCH_BAR_PAD_H=10`, `STATUS_BAR_PAD_H=10`, `STATUS_BAR_BORDER_W=1`, `SECTION_BAR_W=3`, `SECTION_BAR_H=18`, `SECTION_BAR_RADIUS=2`.

**أبعاد الأزرار:** `INPUT_HEIGHT_PAD=10` (h = base*2 + PAD → 32px @ size 11), `BTN_HEIGHT_PAD=8`, `BTN_PAD_H=14`, `BTN_BORDER_RADIUS=6`, `BTN_TEXT_PAD=32`, `BTN_BORDER_W=1.5`, `DROPDOWN_ARROW_W=24`.

**List/Detail headers:** `LIST_HEADER_MARGIN_H/T/B`, `LIST_HEADER_BORDER_W`, `DETAIL_HEADER_MARGIN_H/T`, `DETAIL_HEADER_BORDER_W`, `PAGE_HEADER_MARGIN_H/V` (+ نسخة `_COMPACT`), `PAGE_HEADER_BORDER_W`.

**Section header (design/costing/accounting sections):** `SECTION_HEADER_HEIGHT=42`, `SECTION_HEADER_BORDER_W=1`, `SECTION_HEADER_PAD_RIGHT=16`.

**Notification/Warning bars:** `NOTIF_MARGIN_H/V`, `NOTIF_SPACING`, `NOTIF_BORDER_W`, `DISMISS_BTN_SIZE=22`.

**ProgressBar:** `PROGRESS_BAR_H=8`, `PROGRESS_TOP_SPACING=3`, عتبات الألوان: `PROGRESS_THRESHOLD_SUCCESS=90`, `_NORMAL=60`, `_WARNING=30` (% — أقل من WARNING = danger).

**LoadingOverlay:** `OVERLAY_MARGIN=20`, `SPINNER_FRAME_INTERVAL_MS=100`, `OVERLAY_BORDER_RADIUS=8`.

**Offer Form (pricing offers) — أعمدة ورؤوس:** `OFFER_FORM_SCROLL_MIN_H/MAX_H`, `OFFER_FORM_DISC_W=90`, `OFFER_FORM_CAT_W=150`, `OFFER_FORM_HDR_ICON_W/DEL_W/SEARCH_W/COST_W/PRICE_W/QTY_W/TOTAL_W`, `OFFER_ROW_PRODUCT_COMBO_W=180`.

**Offers Tab / Table:** أحجام splitter (`OFFERS_TAB_SPLITTER_HANDLE_W=6`, `_FORM_SIZE`, `_BOTTOM_SIZE`, `_TABLE_SIZE`, `_DETAILS_SIZE`) وأعمدة جدول العروض (`OFFERS_TABLE_COL0_ID_W`...`COL9_DATE_W`).

**StatBox/StatCard/StatusChip/StatusCard:** أبعاد وradii لكل مكوّن إحصائي — `STAT_BOX_*`, `STAT_CARD_MARGIN_COMPACT/NORMAL`, `STAT_INNER_*`, `STATUS_CHIP_*`, `STATUS_CARD_*`.

**ColorPickerWidget:** `COLOR_PICKER_PREVIEW_SIZE=28`, `COLOR_PICKER_PREVIEW_RADIUS=4`.

**FilterToolbar / أنماط الجداول والأشجار:**
```python
FILTER_TOOLBAR_MARGIN_H/V; FILTER_TOOLBAR_SPACING=8
FILTER_COMBO_MIN_H=28; FILTER_COMBO_MIN_W=160; FILTER_RESET_BTN_W=32
FILTER_SEARCH_H=28; FILTER_TOOLBAR_BORDER_RADIUS=6; FILTER_BAR_BORDER_RADIUS=8
TREE_BORDER_RADIUS=6; LIST_BORDER_RADIUS=4; TABLE_BORDER_RADIUS=8
TABLE_STYLE_COMPACT/LARGE/NORMAL_ITEM_PAD_V/H; TABLE_STYLE_NORMAL_HEADER_PAD_V/H
SPLITTER_HANDLE_RADIUS=3
FILTER_COMBO_BORDER_RADIUS=4; FILTER_COMBO_PAD_H/V; FILTER_CAT_ICON_W=20
FILTER_COUNT_LABEL_MIN_W=50; FILTER_DATE_DEFAULT_FROM=(2000,1,1)
```

**DetailSection / TwoColDetails:** `DETAIL_SECTION_RADIUS=10`, `DETAIL_SECTION_MARGIN_B=12`, `DETAIL_SECTION_HDR_MARGIN_H`, `DETAIL_GRID_MARGIN_H/H_SPACING/V_SPACING` (+ `_C` نسخة compact)، `DETAIL_GRID_PAD_COMPACT/NORMAL`، `DETAIL_LABEL_MIN_W=80`، `TWO_COL_H_SPACING=24`، `TWO_COL_V_SPACING=8`.

**FormFields / FormBadges:** `FORM_FIELD_DEFAULT_H=30`, `FORM_HINT_SPACING=2`, `FORM_LAYOUT_SPACING=10`, `FORM_LAYOUT_MARGIN`, `LABELED_WIDGET_SPACING=6`, `LABELED_INPUT_SPACING=8`, وشارات `BADGE_LABEL_*`, `DR_CR_DISPLAY_*`, `BALANCE_DISPLAY_*`, `BADGE_BORDER_RADIUS`, `MODE_BADGE_PAD_V`, `PREVIEW_LABEL_*`, `INLINE_PREVIEW_SPACING`.

**CategoryManager:** `CATEGORY_MANAGER_MARGIN/SPACING`, `CATEGORY_FORM_SPACING`, `CATEGORY_TREE_COL0/1/2_W`.

**FormGroup:** `FORM_GROUP_BORDER_RADIUS=10`, `FORM_GROUP_MARGIN_TOP=10`, `FORM_GROUP_PADDING_TOP=6`, `FORM_GROUP_TITLE_PAD_H=8`, `FORM_GROUP_FORM_MARGIN`.

**CollapsibleCard:** `COLLAPSIBLE_CARD_HDR_BORDER_RADIUS="10px 10px 0 0"`, `_HDR_PAD_V/H`, `_CONTENT_MARGIN_H/V`, `_CONTENT_SPACING`.

**EmptyState:** `EMPTY_STATE_SPACING/_EXPANDED`, `EMPTY_STATE_MARGIN_H/V/_EXPANDED`, `EMPTY_STATE_BORDER_RADIUS=10`, `EMPTY_STATE_ACTION_BTN_W=140`, `EMPTY_STATE_TABLE_ROW_H=60`, `EMPTY_STATE_DEFAULT_MIN_H=80`.

**CardGrid:** `CARD_GRID_DEFAULT_COLS=4`, `CARD_GRID_DEFAULT_SPACING=10`.

**Card/Frame/Input/Scroll:** `CARD_BORDER_RADIUS=10`, `STATUS_CARD_STYLE_RADIUS=8`, `INPUT_HEIGHT=32`, `SEARCH_INPUT_HEIGHT=34`, `AMOUNT_SPINBOX_MAX=999_999_999`, `NOTES_LINE_EDIT_HEIGHT=30`, `SCROLL_BAR_WIDTH=6`, `SCROLL_HANDLE_MIN_LEN=30`.

**Tab sizes:** `TAB_MIN_W_SMALL/NORMAL`, `TAB_PAD_V/H_SMALL/NORMAL`.

**Tree/List item padding & row heights:** `TREE_ITEM_PAD_V/H`, `LIST_ITEM_PAD_V/H`, `LIST_ITEM_BORDER_W`, `ROW_HEIGHT_COMPACT=34`, `_NORMAL=40`, `_LARGE=48`.

**ActionToolbar / FlowLayout:** `ACTION_TOOLBAR_FLOW_V_SPACING`, `_MARGIN_V`, `_DEFAULT_SPACING`, `DETAIL_HEADER_TOOLBAR_SPACING`, `FLOW_LAYOUT_DEFAULT_H_SPACING/V_SPACING`.

**Divider:** `V_DIVIDER_WIDTH=1`, `V_DIVIDER_MARGIN_V=4`, `V_DIVIDER_INNER_MARGIN_H=0`.

**FlexibleTable / WrapDelegate:** `FLEX_WRAP_MIN_ROW_H=36`, `FLEX_WRAP_PADDING=4`, `FLEX_DEFAULT_COL_WIDTH=150`, `FLEX_TABLE_MIN_ROW_H=36`, `FLEX_ROW_HEIGHT_PAD=8`.

**Input/Label/Sidebar nav styles:** `INPUT_BORDER_RADIUS=6`, `INPUT_PAD_H=8`, `INPUT_BORDER_W=1`, `SEARCH_PAD_H=10`, `STATUS_LABEL_RADIUS/PAD_V/H`, `LINK_BTN_RADIUS=4`.

**Sidebar nav (تُستخدم في `ui/main_window_helper/` — راجع `ui_main_window_helper.md`):**
```python
NAV_BTN_H = 38; NAV_BTN_W_OFFSET = 16; NAV_ICO_W = 22; NAV_ICO_FS = 15
NAV_BTN_HEIGHT_PAD = 14; BADGE_FS = 8
SIDEBAR_COMPANY_H = 46; SIDEBAR_TOGGLE_H = 36; SIDEBAR_DIVIDER_H = 1
SIDEBAR_SCROLL_W = 3; SIDEBAR_SCROLL_MIN_H = 20
NAV_LAYOUT_MARGIN_H = 10; NAV_LAYOUT_SPACING = 10
NAV_BTN_BORDER_RADIUS = 6; NAV_BADGE_PAD_V/H; NAV_BADGE_RADIUS = 8
NAV_ACTIVE_BORDER_W = 2; TAB_INDICATOR_BORDER_W = 2
SECTION_LABEL_PAD_TOP = 12; SECTION_LABEL_PAD_H = 16; SECTION_LABEL_PAD_BOT = 4
SECTION_LABEL_LTR_SPACING = "1.5px"
SIDEBAR_NAV_MARGIN = 8; SIDEBAR_NAV_SPACING = 1
SIDEBAR_FOOTER_MARGIN_H/V; SIDEBAR_FOOTER_SPACING = 1
SIDEBAR_DIV_MARGIN_V/H; SIDEBAR_ANIM_DURATION = 200
SIDEBAR_TOGGLE_BORDER_W = 1; SIDEBAR_SCROLL_RADIUS = 1; SIDEBAR_BORDER_W = 1
```

**Offer Form buttons / Offer Item Row / Offer Details table:** `OFFER_ADD_ROW_BTN_PAD_V/H`, `OFFER_SAVE_BTN_PAD_H`, `OFFER_ROW_SEARCH_PAD_V/H`, `OFFER_DET_COL1..6_*_W`.

**Pricing Panel (`_PricingPanel`):** ثوابت شاملة (`PRICING_PANEL_*`) لأبعاد الفورم، أعمدة الجدول (`PRICING_PANEL_TABLE_COL0..7_*_W`)، spinboxes، وspacing الصفوف.

---

## constants_accounting

### `ui/constants_data/constants_accounting.py`

**الغرض:** كل ثوابت قسم المحاسبة — دفتر الأستاذ، القيود، الحسابات، المستثمرون، Audit Log، وكل الـ widgets الفرعية المرتبطة (Account Combo/Picker/Tree Popup، Balance Bar، Journal Header/Filter/Form، Smart Line، Journal Tree Table، T-Account، Group Manager).

**لا imports خارجية.**

**أهم المجموعات:**

- **Accounting Tabs Builder:** `EQUITY_TAB_SPLITTER_SIZES = (600, 300)`.
- **State Widgets:** `STATE_LABEL_PADDING=40`, `STATE_ERROR_BORDER_RADIUS=8`, `STATE_ERROR_MARGIN=20`.
- **`_AccountCombo`:** `ACCOUNT_COMBO_GROUP_W=130`, `_SEARCH_W=90`, `_ACCOUNT_MIN_W=200`, `_NB_BADGE_W=44`, badge radius/padding، `_LAYOUT_SPACING=4`.
- **Financial Tabs (balance_sheet/income_statement/owners_equity/trial_balance):** margins/spacing عامة (`FINANCIAL_TAB_*`)، أعمدة (`FINANCIAL_COL_CODE_W=60`, `_AMOUNT_W=110`, `_TYPE_W=80`, `_AMOUNT_OE_W=100`)، هيدر أقسام (`FINANCIAL_HDR_*`)، إطارات (`FINANCIAL_FRAME_*`)، legend وtotals (`FINANCIAL_LEGEND_*`, `FINANCIAL_TOTALS_SPACING=24`)، أعمدة ميزان المراجعة (`FINANCIAL_TB_COL_CODE/TYPE/DEBIT/CREDIT/BALANCE_W`).
- **Investor Details Panel:** `INVESTOR_DETAIL_MARGIN_H/T/B/SPACING`, `INVESTOR_TITLE_*`, `INVESTOR_DEL_BTN_MIN_H`, أعمدة جدول الحركات (`INVESTOR_MOV_COL_DATE/TYPE/AMOUNT/REF_W`).
- **Investors Panel:** `INVESTOR_FORM_SPLIT_SIZES=(310,600)`, `INVESTOR_PANEL_TOP_H/DETAIL_H=320`.
- **Investors Table:** `INVESTOR_TABLE_COL_MAX_W=200`.
- **Movement Dialog:** `MOVEMENT_DIALOG_MIN_W=500` + margins/spacing/أزرار/عناوين/معاينة.
- **Link To Entry Panel:** `LINK_PANEL_MARGINS/SPACING/INFO_RADIUS/INFO_PAD`.
- **AccountPickerButton:** `ACCOUNT_PICKER_NB_LABEL_W=44` + أبعاد badge وزر + `ACCOUNT_PICKER_FIRE_CHANGED_DELAY=50` (ms).
- **AccountTreePopup:** أحجام خط حسب المستوى (`ACCOUNT_TREE_FONT_SIZE_DELTA_L0/L1`)، أبعاد الـ popup (`ACCOUNT_TREE_POPUP_MIN_W=440`, `_MAX_H=520`, `_MARGINS`, `_OPEN_W=60`, `_OPEN_H=460`)، قائمة (`ACCOUNT_TREE_LIST_*`)، بحث (`ACCOUNT_TREE_SEARCH_*`)، border.
- **`_BalanceBar`:** margins/spacing/radius/badge لشريط توازن القيد.
- **`_EntryTypeBadge`/`_EntryRefLabel`:** border/radius/padding.
- **`_JournalHeader`:** `JOURNAL_HEADER_DATE_W=130`, `_CMB_W=110`, spacing/radius/padding للـ combo، `_GROUP_SPACING=6`.
- **`_TreeGroupCombo`:** border/padding/min-height لعناصر `QTreeView`، `TREE_GROUP_COMBO_HEADER_FONT_DELTA=1`.
- **`_LinesPanel`:** إطار كامل (`LINES_PANEL_BORDER_*`)، هيدر الصفوف (`LINES_PANEL_HDR_H=38` + radius/margins)، badge DR/CR، col_hdr، rows scroll (`LINES_PANEL_SCROLL_MIN_H=150`, `_MAX_H=380`)، زر إضافة صف.
- **`_SmartLine`:** إطار الصف (border/radius/margins/spacing)، `SMART_LINE_MOVE_BTN_SIZE=18`، `_DIR_FRAME_W=130`، `_AMOUNT_MIN_H/W/MAX=999_999_999/DECIMALS=2`، `_DESC_MIN_H=28`، `_DEL_BTN_SIZE=22`، صف المستثمر (`_INV_ROW_*`, `_INV_LBL_W=95`, `_INV_CMB_MIN_H=24`)، `_ACCENT_BORDER_W=3`.
- **`_JournalFilterBar`:** بنية كاملة (border/margins/spacing لصفين)، أيقونات، radius/padding للـ inputs، عرض combos (`_GROUP_CMB_MIN/MAX_W`, `_BAL_CMB_W=120`)، زر مسح الفلاتر.
- **`_JournalForm`:** margins/spacing، أزرار الحفظ/المسح (min-height/radius/padding).
- **منطق `_JournalFilterBar`:** `JOURNAL_BALANCE_EPSILON=0.01` (حد تسامح التوازن)، تاريخ افتراضي (`JOURNAL_FILTER_DEFAULT_FROM_YEAR/MONTH/DAY = 2020/1/1`).
- **JournalTab:** `JOURNAL_TAB_SPLITTER_HANDLE_W=6`, `_SIZES=(440,360)`.
- **`_JournalTreeTable`:** أعمدة (`JOURNAL_TREE_COL_TOGGLE/DATE/REF/DR/CR/STATUS_W`).
- **`_LedgerFilterBar`:** `LEDGER_MOVE_CMB_MIN_H=28`, `_W=120`.
- **`_StatCards` (ledger):** `LEDGER_STAT_BORDER_RADIUS=8`, `_BORDER_W=1`.
- **`_TAccountPanel`:** أعمدة T-table + إطار (`T_ACCOUNT_FRAME_RADIUS=8`)، هيدر جانب DR/CR، فاصل عمودي (`T_ACCOUNT_SEP_W=2`)، `T_ACCOUNT_ROOT_SPACING=6`.
- **`_AccountsPanel`:** `ACCOUNTS_PANEL_COL_CODE_W=65`, `_COL_BAL_W=90`, margins فلتر النوع.
- **`_AccountForm`:** margins/spacing كاملة، `ACCOUNT_FORM_GRP_*` (QGroupBox)، `ACCOUNT_FORM_FL_SPACING=8`، ارتفاعات inputs/أزرار.
- **AccountsTreePanel:** أعمدة (`ACCOUNTS_TREE_COL_CODE_W=70`, `_BAL_W=110`)، عرض splitter (`_SPLITTER_L=420`, `_R=280`)، `_FILTER_MIN_H=26`، عمق التوسع (`ACCOUNTS_TREE_EXPAND_DEPTH=2`)، margins/spacing اللوحة اليسرى.
- **`_AuditDetailDialog`:** أبعاد/margins/spacing/radius/padding كاملة.
- **AuditLogTab:** هيدر (`AUDIT_HDR_MARGIN_H/V`)، شريط فلاتر (`AUDIT_FILTER_*`)، أعمدة الجدول (`AUDIT_COL_INDEX/TYPE/TABLE/RECORD/BY_W`, `AUDIT_ROW_H=32`)، pagination (`AUDIT_PAGIN_*`)، `AUDIT_PAGE_SIZE=200`, `AUDIT_LOAD_DELAY=100` (ms).
- **`_GroupManagerPanel`:** margins/spacing، `GROUP_MGR_COL_COUNT_W=100`, `_INPUT_MIN_H=28`.
- **LedgerTab:** `LEDGER_SPLITTER_HANDLE_W=6`, margins يمين/يسار، `LEDGER_SPLITTER_SIZES=(240,760)`.
- **AccountingTab (قسم عام):** `ACCOUNTING_TAB_MSG_PAD=40`, `_ERR_RADIUS=8`, `_ERR_MARGIN=20`.

---

## constants_costing

### `ui/constants_data/constants_costing.py`

**الغرض:** كل ثوابت قسم حساب التكلفة — BOM، المنتجات، الخامات (Variants)، العمالة، الماكينات، السيناريوهات، الاستبدال الشامل، مقارنة السيناريوهات.

**لا imports خارجية.**

**أهم المجموعات:**

- **`ComponentRow`:** تأخير تحميل (`COMPONENT_ROW_LOAD_DELAY=50` ms)، أبعاد outer layout، حدود نسبة الهادر (`_WASTE_MAX_PCT=100`, `_MIN_PCT=0`, `_DECIMALS=1`)، عتبات مستوى الهادر (`WASTE_LEVEL_HIGH_THRESHOLD_PCT=20`, `_MEDIUM=10`)، أبعاد كل الـ widgets الفرعية (variant combo, qty edit, waste spin, op combo, أزرار)، radii/padding/borders.
- **`LaborSettingsPanel`:** أبعاد اللوحة، حدود spinboxes (راتب/أيام/ساعات/معامل تحميل) بحدودها العليا وخاناتها العشرية.
- **`LaborOpTable` / `LaborOpForm`:** أعمدة الجدول (`LABOR_TABLE_COL0/2/3/4_W`)، حدود spinbox الدقائق.
- **`MachineForm` / `MachineOpForm` / `MachineOpTable` / `MachineTable`:** حدود المعدل، أبعاد فورم/جدول العملية والماكينة، أعمدة الجداول.
- **`ProductForm` (`_header_bar.py`/`_rows_manager.py`):** أبعاد الهيدر (`PRODUCT_FORM_HEADER_MIN_W=700`, `_H=130`)، margins/spacing، عرض التصنيف، ارتفاع الصفوف، min-height لمنطقة الـ scroll.
- **`_ProductMainPanel`:** `PRODUCT_MAIN_SPLITTER_HANDLE_W=6`, `_SIZES=(280,220,250)` (form, table, bom).
- **`LaborTab` / `MachineTab`:** أحجام splitter لكل تبويب.
- **`RawInputPanel` / `RawSection`:** عرض حقول السعر/الكمية، hint label، `RAW_SECTION_LIST_MIN_W=400`.
- **`BulkReplace` (dialog + operation section):** أبعاد النافذة الكاملة، هيدر/body margins، أزرار Apply/Cancel، `_OperationSection` (QGroupBox، cmb_replacement، sp_uniform، replace_frame).
- **`ProductRow`:** margins/spacing/checkbox/type icon/qty spinbox/radius.
- **`_ProductsPanel`:** فلتر التصنيف، scroll area، quick-select bar وأزرارها، rows layout، empty state padding.
- **`_BomScenariosPanel`:** لوحة كاملة الارتفاع (`SCENARIOS_PANEL_H=46`)، combo السيناريوهات، أزرار (تعيين افتراضي/تعديل/استنساخ/جديد/حذف) بعرض كل واحد محدد.
- **`_RawVariantsPanel`:** حدود spinbox عدد القطع (دقة 4 خانات عشرية)، أبعاد الجدول (`RAW_VARIANTS_TABLE_MAX_H=160`, 4 أعمدة)، layout/stylesheet كامل للفورم.
- **`ScenarioComparisonWidget`:** margins، combo السيناريو، صفوف التكلفة والربح، إطار المقارنة.
- **`_OpRowsEditor`:** فورم كامل (margins/spacing)، spinboxes (قيمة/عدد)، جدول الصفوف (`OP_ROWS_TABLE_MAX_H=180`, `_MIN_H=60`)، أعمدة (قيمة/عدد/تكلفة)، حدود القيم العددية.
- **`BomTree`:** أزرار الشجرة، legend، هيدر الأعمدة، أعمدة (`BOM_TREE_COL_QTY/WASTE/EFF_QTY/COST_UNIT/TOTAL_COST/TYPE_W`)، `BOM_TREE_MIN_SECTION_SIZE=40`.
- **`CostingSection` (error tab):** `COSTING_ERR_TAB_BORDER_W/RADIUS/PAD`.

---

## constants_design

### `ui/constants_data/constants_design.py`

**الغرض:** كل ثوابت قسم التصميمات — المقاسات، التصنيفات، مجموعات الأبعاد (Dimension Sets)، بطاقات التصميم/المقاس، GIMP integration، `design_styles._Styles` المشتركة.

**لا imports خارجية.**

**أهم المجموعات:**

- **`_CatRow` / `_CatForm` (design categories):** أبعاد الصف (indent، خط الربط، نقطة اللون، badge العداد)، فورم كامل (radius/margins/spacing/color preview/أزرار).
- **`_DesignCard`:** عرض ثابت `DESIGN_CARD_W=172`, thumbnail `=128`, radii، badge موضع/حجم، margins منطقة المعلومات.
- **`SizeCard` (helper.py) / `_SizeCard` (الكلاس الفعلي):** ثوابت مزدوجة — `SIZE_CARD_*` (helper بسيط، `DEFAULT_DPI=300`, `SCREEN_DPI=96`) و`SIZE_CARD_RADIUS/THUMB_W/MIN_H/...` (الكلاس الكامل بكل تفاصيله: أزرار الأيقونات، شريط الحالة، chips الوحدة/DPI، الزر الرئيسي GIMP).
- **`XcfWatcher`/`_xcf_thumbnail.py`:** `XCF_WATCHER_DEBOUNCE_MS=1500`, `XCF_THUMB_MIN_SIZE=64`.
- **`DesignsCategoriesPanel`:** عرض ثابت الشريط الجانبي (`DESIGN_CATS_SIDEBAR_W=230`)، هيدر، بحث، قائمة، أزرار إجراءات، فواصل.
- **`_DesignsTable`:** toolbar، صفوف بحث/فلترة، grid (margins/spacing)، scroll، تأخيرات (`DESIGNS_TABLE_REFLOW_DELAY=60`, `_SEARCH_DELAY=280` ms)، حساب الأعمدة، حالة فارغة، أحجام splitter `DesignsTab`.
- **`_DesignDetailPanel`:** هيدر (margins/spacing لصفوف العنوان والأزرار)، حقول (تصنيف/ملاحظات)، منطقة المقاسات (scroll)، empty sizes state.
- **`_SizeDialog`:** أبعاد النافذة الكاملة، هيدر، فورم (`SIZE_DLG_FORM_SPACING=12`)، معاينة الكانفاس، زر تصفح GIMP، أزرار الحفظ/الإلغاء.
- **`_SourcePickerDialog`:** أبعاد النافذة، هيدر، قائمة الـ instances، صندوق المعاينة، أزرار primary/ghost، radio button، شارة النتيجة.
- **`_ValuesPanel`:** عرض لوحة القائمة (`DIM_VALUES_LIST_MIN_W=240`, `_MAX_W=360`)، عرض الـ splitter الأيمن `=720`.
- **`_InstancePopup`:** أبعاد النافذة الكاملة، هيدر، حقول القيم (grid)، أزرار (حفظ/إلغاء/حساب الكل)، حدود spinbox القيمة (`DIM_INST_VALUE_SPIN_MIN/MAX/DECIMALS`).
- **`_InstancesTable`:** toolbar (أزرار/ارتفاعات)، خلايا الجدول، أعمدة (اسم/قيم)، حالة فارغة.
- **`_SetsListPanel`/`_SetCard`:** بطاقة مجموعة مقاسات (حدود عادي/مختار، radius، margins، أيقونة، badge)، هيدر اللوحة، إطار البحث، scroll.
- **`_FieldDialog`:** أبعاد النافذة، فورم (name/label/unit/type/source field)، مجموعة الاعتمادية، صندوق المعاينة، حدود spinbox الافتراضي والـ offset.
- **`_FieldsPanel`:** أعمدة (ترتيب/اسم/وحدة/نوع/إلزامي/اعتمادية).
- **`_CategoriesPanel`:** هيدر، أعمدة الشجرة، فورم إضافة/تعديل تصنيف، color swatch.
- **`_SetsPanel`:** هيدر، صندوق تلميح.
- **`_SetsManagerPanel`/`_GroupsPanel`:** هيدر إدارة المجموعات، هيدر `_FieldsPanel` الفرعي، layout رئيسي.
- **`design_styles._Styles`:** ثوابت التصميم المشتركة المُستخدمة عبر كل الـ style helpers في قسم التصميم — radii (`STYLES_RADIUS_LG/SM/XS`)، ارتفاع الأزرار، badges، padding للـ inputs/combo.

---

## constants_inventory

### `ui/constants_data/constants_inventory.py`

**الغرض:** كل ثوابت قسم المخزون — تبويبات (أصناف/وارد/صادر/تقرير).

**لا imports خارجية.**

```python
INVENTORY_SPIN_MAX = 999999999; INVENTORY_SPIN_DEC = 4
INVENTORY_INPUT_MIN_H = 30; INVENTORY_CMB_MIN_H = 28
INVENTORY_UNIT_W = 120; INVENTORY_DATE_W = 130
INVENTORY_SAVE_BTN_H = 36; INVENTORY_ITEM_MIN_W = 220
INVENTORY_GRP_BORDER_RADIUS = 8; INVENTORY_GRP_MARGIN_TOP = 8
INVENTORY_GRP_PAD_TOP = 8; INVENTORY_GRP_TITLE_PAD_H = 6
INVENTORY_SAVE_BTN_RADIUS = 6; INVENTORY_SAVE_BTN_PAD_H = 18
INVENTORY_COL_MAX_W = 150; INVENTORY_CARD_BORDER_L = 4
INVENTORY_ITEMS_SPLITTER_HANDLE_W = 6
INVENTORY_ITEMS_SPLITTER_FORM_SIZE = 320
INVENTORY_ITEMS_SPLITTER_TABLE_SIZE = 580
INVENTORY_ITEMS_TABLE_ROOT_MARGIN = (12, 8, 12, 12)
```

---

## constants_orders

### `ui/constants_data/constants_orders.py`

**الغرض:** كل ثوابت قسم الطلبات والعملاء — لوحة العملاء، لوحة تفاصيل العميل، Dashboard، تفاصيل الطلب (بنود/سجل)، فورم الطلب، فورم العميل وجهة الاتصال، فورم البند، فلاتر الطلبات، جدول الطلبات، Status Delegate.

**لا imports خارجية.**

**أهم المجموعات:**

- **`CustomersListPanel`:** أعمدة الجدول (كود/اسم/هاتف/مدينة/عدد طلبات).
- **`CustomerDetailPanel`:** ارتفاع جداول جهات الاتصال والطلبات، أعمدة كل جدول.
- **Orders Dashboard:** `DASHBOARD_RECENT_TABLE_COL_WIDTHS` (dict لأعمدة 0-6)، `DASHBOARD_TABLE_BORDER_PAD`، spacing البطاقات العلوية، `DASHBOARD_SCROLL_MAX_H=340`، margins (top/recent header/table container)، `DASHBOARD_REFRESH_BTN_MIN_H=30`، `DASHBOARD_RECENT_LIMIT=20`.
- **Order Detail — Items Section:** أعمدة الجدول (dict)، ارتفاع أقصى/أدنى، empty state، toolbar spacing، أزرار.
- **Order Detail — Log Section:** أعمدة سجل الحالة، ارتفاع أقصى.
- **Order Form — Item Row Widget (`_item_row_widget.py`):** إطار كامل — margins/spacing لكل صف وسطر فرعي، عرض حقل البحث/الكمية/الوحدة، حدود min/max/decimals للكمية.
- **Order Detail — Status Dialog:** أبعاد النافذة، هيدر، صندوق الحالة الحالية، combo الحالة الجديدة، زر التأكيد.
- **Orders List — Filter Toolbar:** combo الحالة/الأولوية، زر "طلب جديد" (radius/height/min-width/text pad)، صفوف/margins، حقل البحث.
- **Orders List Panel:** `ORDERS_LIST_COL_WIDTHS` (dict)، حدود عرض اللوحة (min/max)، auto-fit (min/max width)، `CUSTOMERS_LIST_MIN_W=300`، تأخير fit الـ splitter.
- **Orders List — Status Delegate:** padding الـ badge، حدود العرض/الارتفاع، radius، border width، حجم خط أدنى، `sizeHint` الافتراضي.
- **`_OrderDetail`:** مفاتيح `tr()` لأيقونات بطاقات الإجمالي/المدفوع/الرصيد/الاستحقاق (`ORDER_DETAIL_ICON_*`).
- **`_OrderForm`:** أبعاد النافذة الكاملة، QGroupBox، تفاصيل الطلب (`QFormLayout`)، toolbar البنود، combo العروض، صفوف البنود، شريط الإجمالي، ملاحظات، زر الحفظ، معلومات العميل، تاريخ استحقاق افتراضي (`ORDER_FORM_DUE_DATE_DEFAULT=7` يوم)، حدود الخصم/المدفوع.
- **`_CustomerForm`:** أبعاد النافذة، فورم، QGroupBox، ملاحظات، جدول جهات الاتصال، زر الحفظ، هيدر، أعمدة جدول جهات الاتصال.
- **`_ContactDialog`:** أبعاد النافذة، فورم.
- **`_ItemForm`:** أبعاد النافذة، فورم، spinbox (حد أقصى)، label الإجمالي، زر الحفظ، حدود الكمية/السعر/الخصم، هيدر.

---

## constants_companies

### `ui/constants_data/constants_companies.py`

**الغرض:** كل ثوابت قسم الشركات والعناصر المشتركة بين الشركات — `PublishAsSharedDialog`, `CompaniesDialog`, `CompanySelector`, `NoCompanyScreen`, `SharedItemsManagerDialog`, `SharedItemsDialog`, `LinkItemPicker`.

**لا imports خارجية.**

**أهم المجموعات:**

- **`PublishAsSharedDialog` (`_add_shared_item_dialog.py`):** حدود القيم الافتراضية والدقائق لـ `QDoubleSpinBox`، أبعاد النافذة (`PUBLISH_DLG_MIN_W=480`, `_MIN_H=440`)، root layout، hint label، QGroupBox، قائمة الشركات (`PUBLISH_DLG_LIST_MAX_H=120`)، أزرار الاختيار السريع، زر النشر.
- **`CompaniesDialog`:** أبعاد النافذة (`COMPANIES_DLG_MIN_W=820`, `_MIN_H=560`)، عناوين splitter (يسار=460/يمين=320)، زر الإغلاق، لوحة الجدول (spacing/زر إضافة/عمود الأزرار)، لوحة الفورم (radius/margins/spacing)، حقول الإدخال، مربع معاينة اللون، ملاحظات (`QTextEdit`)، أزرار الحفظ/الإلغاء، badge الاسم في الجدول، خلية الأزرار، ارتفاع الصف (`COMPANIES_DLG_ROW_H=42`).
- **`CompanySelector`:** margins/spacing، أيقونة، عرض/ارتفاع الـ combo، radius/padding، سهم القائمة، عناصر القائمة، زر الإدارة (حجم/radius).
- **`NoCompanyScreen`:** حجم أيقونة الترحيب، زر "إنشاء شركة" (ارتفاع/عرض/radius)، spacing.
- **`SharedItemsManagerDialog`:** حجم خط عناصر النوع في الشجرة، حدود الهيدر/hint/زر الحذف، أبعاد النافذة (`SHARED_MGR_MIN_W=820`, `_MIN_H=600`)، body margins/spacing، hint، أزرار الشجرة (إضافة/حذف)، شجرة (`QTreeWidget` كاملة — border/radius/item padding/أعمدة 1-4)، هيدر (`SHARED_MGR_HDR_H=60`)، زر الإغلاق.
- **`SharedItemsDialog`:** حدود الهيدر/أزرار الربط/`QGroupBox`/`QListWidget`، حدود القيم الافتراضية والدقائق لـ spinbox، أبعاد النافذة (`SHARED_DLG_MIN_W=560`, `_MIN_H=500`)، هيدر، `QGroupBox` بيانات العنصر، قائمة الشركات، أزرار الربط، زر الحفظ، label المعاينة (سعر الوحدة).
- **`LinkItemPicker`:** أبعاد النافذة (`LINK_PICKER_MIN_W=460`, `_MIN_H=380`)، `QListWidget` (radius/item padding)، أزرار الربط/الإلغاء.

---

## علاقات الملفات

- `ui/constants.py` هو نقطة الدخول الوحيدة المتوقعة من باقي المشروع — يجمع الـ 7 ملفات عبر `import *` بلا أي منطق إضافي.
- كل ملف `constants_data/constants_<domain>.py` **مستقل تماماً عن الآخرين** — لا استيراد متبادل بينها، ولا استيراد من أي مكان آخر في المشروع (لا حتى من `ui.theme` أو `ui.font`) — قيم رقمية/نصية/tuple ثابتة فقط.
- كل ملفات `ui/widgets/`, `ui/tabs/`, `ui/main_window_helper/`, `ui/main_window.py` تستورد من `ui.constants` (المُجمِّع) حصراً — لا يستورد أي ملف مباشرة من `ui.constants_data.constants_<domain>`.
- `constants_general.py` هو المُعتمَد عليه الأكثر عبر المشروع (يغطي Sidebar المستخدم في `ui_main_window_helper.md`، أبعاد النافذة المستخدمة في `ui_root.md` — `main_window.py`، وكل الـ base widgets العامة).
- الثوابت الخاصة بكل دومين (`constants_accounting`, `constants_costing`, `constants_design`, `constants_inventory`, `constants_orders`, `constants_companies`) تُستخدم حصراً من ملفات `ui/tabs/<domain>/` المقابلة لها (مراجعها الخاصة — خارج نطاق هذا الملف).
- لا علاقة مباشرة بين `ui/constants_data/*.py` و`ui/theme_manager_data/*.py` (راجع `ui_theme_manager.md`) — `constants_data` كلها قياسات/أبعاد رقمية، بينما `theme_manager_data` كلها ألوان hex. الاستثناء الوحيد للتشابه: بعض الأسماء المتشابهة (مثل `_RADIUS`) موجودة في كلا المرجعين لكنها معرّفة بشكل مستقل تماماً في كل واحد.
