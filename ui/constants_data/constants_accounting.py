"""
ui/constants_data/accounting.py
==========================
ثوابت قسم المحاسبة (دفتر الأستاذ، القيود، الحسابات، المستثمرون، Audit Log)
جزء من تقسيم ui/constants.py — راجع ui/constants/__init__.py.
"""

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

# ── AccountsTreePanel ─────────────────────────────────────
ACCOUNTS_TREE_COL_CODE_W   = 70    # عرض عمود الكود في AccountsTreePanel
ACCOUNTS_TREE_COL_BAL_W    = 110   # عرض عمود الرصيد في AccountsTreePanel
ACCOUNTS_TREE_SPLITTER_L   = 420   # عرض الجانب الأيسر (شجرة) في AccountsTreePanel
ACCOUNTS_TREE_SPLITTER_R   = 280   # عرض الجانب الأيمن (فورم) في AccountsTreePanel
ACCOUNTS_TREE_FILTER_MIN_H = 26    # ارتفاع أدنى لفلتر التصنيف في AccountsTreePanel

# ── _AuditDetailDialog ────────────────────────────────────
AUDIT_DETAIL_MIN_W         = 560   # عرض أدنى لـ _AuditDetailDialog
AUDIT_DETAIL_MIN_H         = 420   # ارتفاع أدنى لـ _AuditDetailDialog
AUDIT_DETAIL_BODY_MARGIN_H = 20    # left/right margin لـ root layout في _AuditDetailDialog
AUDIT_DETAIL_BODY_MARGIN_V = 16    # top/bottom margin لـ root layout في _AuditDetailDialog
AUDIT_DETAIL_BODY_SPACING  = 12    # spacing لـ root layout في _AuditDetailDialog
AUDIT_DETAIL_HDR_RADIUS    = 8     # border-radius لـ header frame في _AuditDetailDialog
AUDIT_DETAIL_HDR_MARGIN_H  = 12    # left/right margin لـ hdr_lay في _AuditDetailDialog
AUDIT_DETAIL_HDR_MARGIN_V  = 8     # top/bottom margin لـ hdr_lay في _AuditDetailDialog
AUDIT_DETAIL_TXT_RADIUS    = 6     # border-radius لـ QTextEdit في _AuditDetailDialog
AUDIT_DETAIL_TXT_PAD       = 8     # padding لـ QTextEdit في _AuditDetailDialog

# ── AuditLogTab — Header ──────────────────────────────────
AUDIT_HDR_MARGIN_H  = 16   # left/right margin لـ header في AuditLogTab
AUDIT_HDR_MARGIN_V  = 12   # top/bottom margin لـ header في AuditLogTab

# ── AuditLogTab — Filter Bar ──────────────────────────────
AUDIT_FILTER_MARGIN_H     = 12    # left/right margin لـ filter bar في AuditLogTab
AUDIT_FILTER_MARGIN_V     = 8     # top/bottom margin لـ filter bar في AuditLogTab
AUDIT_FILTER_SPACING      = 12    # spacing لـ filter bar في AuditLogTab
AUDIT_FILTER_CMB_TABLE_W  = 180   # عرض أدنى لـ cmb_table في AuditLogTab
AUDIT_FILTER_CMB_ACTION_W = 130   # عرض أدنى لـ cmb_action في AuditLogTab

# ── AuditLogTab — Table columns ───────────────────────────
AUDIT_COL_INDEX_W    = 55    # عرض عمود الرقم في جدول AuditLogTab
AUDIT_COL_TYPE_W     = 90    # عرض عمود النوع في جدول AuditLogTab
AUDIT_COL_TABLE_W    = 140   # عرض عمود الجدول في جدول AuditLogTab
AUDIT_COL_RECORD_W   = 80    # عرض عمود ID السجل في جدول AuditLogTab
AUDIT_COL_BY_W       = 100   # عرض عمود "بواسطة" في جدول AuditLogTab
AUDIT_ROW_H          = 32    # ارتفاع الصف الافتراضي في جدول AuditLogTab

# ── AuditLogTab — Pagination Bar ──────────────────────────
AUDIT_PAGIN_BAR_H     = 44   # ارتفاع شريط الـ pagination في AuditLogTab
AUDIT_PAGIN_MARGIN_H  = 12   # left/right margin لـ pagination bar في AuditLogTab
AUDIT_PAGIN_MARGIN_V  = 6    # top/bottom margin لـ pagination bar في AuditLogTab
AUDIT_PAGIN_SPACING   = 10   # spacing لـ pagination bar في AuditLogTab
AUDIT_FILTER_CMB_RADIUS    = 5    # border-radius للـ combo في AuditLogTab filter bar
AUDIT_FILTER_CMB_PAD_V     = 3    # padding عمودي للـ combo في AuditLogTab filter bar
AUDIT_FILTER_CMB_PAD_H     = 10   # padding أفقي للـ combo في AuditLogTab filter bar
AUDIT_FILTER_DROP_W        = 20   # عرض drop-down arrow للـ combo في AuditLogTab filter bar
ACCOUNTS_TREE_LEFT_MARGIN_L = 10   # left margin للـ left panel في AccountsTreePanel
ACCOUNTS_TREE_LEFT_MARGIN_T = 8    # top margin للـ left panel في AccountsTreePanel
ACCOUNTS_TREE_LEFT_MARGIN_R = 6    # right margin للـ left panel في AccountsTreePanel
ACCOUNTS_TREE_LEFT_MARGIN_B = 10   # bottom margin للـ left panel في AccountsTreePanel
ACCOUNTS_TREE_LEFT_SPACING  = 6    # spacing للـ left panel layout في AccountsTreePanel

# ── AccountTypeFilter (accounts_combo_widget) ─────────────
ACCT_TYPE_FILTER_CMB_RADIUS = 5   # border-radius للـ combo في AccountTypeFilter
ACCT_TYPE_FILTER_CMB_PAD_V  = 2   # padding عمودي للـ combo في AccountTypeFilter
ACCT_TYPE_FILTER_SPACING     = 6   # spacing لـ layout في AccountTypeFilter (= SPACING_SM)

# ── AccountsTreePanel — tree depth ────────────────────────
ACCOUNTS_TREE_EXPAND_DEPTH  = 2   # عمق التوسع الافتراضي في AccountsTreePanel

# ── AuditLogTab — pagination & timers ─────────────────────
AUDIT_PAGE_SIZE   = 200   # عدد سجلات كل صفحة في AuditLogTab
AUDIT_LOAD_DELAY  = 100   # ms — QTimer.singleShot قبل أول تحميل في AuditLogTab

# ── _GroupManagerPanel ─────────────────────────────────────
GROUP_MGR_ROOT_MARGIN    = (8, 8, 8, 8)   # contentsMargins لـ root layout في _GroupManagerPanel
GROUP_MGR_ROOT_SPACING   = 8              # spacing لـ root layout في _GroupManagerPanel
GROUP_MGR_COL_COUNT_W    = 100            # عرض عمود العدد في شجرة _GroupManagerPanel
GROUP_MGR_INPUT_MIN_H    = 28             # min-height للـ inputs والـ combos في _GroupManagerPanel

# ── LedgerTab ──────────────────────────────────────────────
LEDGER_SPLITTER_HANDLE_W  = 6                # handleWidth للـ QSplitter في LedgerTab
LEDGER_LEFT_MARGIN        = (10, 10, 6, 10)  # contentsMargins للـ left panel في LedgerTab
LEDGER_RIGHT_MARGIN       = (6, 10, 10, 10)  # contentsMargins للـ right panel في LedgerTab
LEDGER_SPLITTER_SIZES     = (240, 760)       # أحجام الـ splitter الافتراضية في LedgerTab

# ── AccountingTab (accounting_section) — رسائل الحالة ──────
ACCOUNTING_TAB_MSG_PAD       = 40   # padding لرسالة «لا توجد شركة نشطة» ورسالة خطأ الاتصال
ACCOUNTING_TAB_ERR_RADIUS    = 8    # border-radius لإطار رسالة خطأ الاتصال
ACCOUNTING_TAB_ERR_MARGIN    = 20   # margin لإطار رسالة خطأ الاتصال



