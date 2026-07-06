"""
ui/i18n/en_data/accounting.py
========================
Accounting section strings (ledger, journal, financial statements, investors, audit log)
جزء من تقسيم ui/i18n/en.py — راجع ui/i18n/en/__init__.py.
"""

EN_STRINGS_ACCOUNTING: dict[str, str] = {
    # ══════════════════════════════════════════════
    # Accounting
    # ══════════════════════════════════════════════
    "accounts":             "Accounts",
    "journal_entries":      "Journal Entries",
    "trial_balance":        "Trial Balance",
    "income_statement":     "Income Statement",
    "balance_sheet":        "Balance Sheet",
    "debit":                "Debit",
    "credit":               "Credit",
    "balance":              "Balance",
    "ref_no":               "Reference No.",
    "investors":            "Investors",
    "investor_add":         "Add Investor",
    "investor_movement":    "Investor Movement",
    "link_to_entry":        "Link to Entry",
    "account_group":        "Account Group",
    "account_nature":       "Account Nature",
    "account_tree":         "Account Tree",
    "account_form_new":          "── New Account ──",
    "account_form_edit":         "── Edit: {name} ──",
    "account_form_enter_code_name": "Enter the code and name",
    "fiscal_year":          "Fiscal Year",
    "owners_equity":        "Owners Equity",
    "assets":               "Assets",
    "liabilities":          "Liabilities",
    "audit_log":            "Audit Log",
    "debit_nature":         "Debit Nature",
    "credit_nature":        "Credit Nature",
    "account_level":        "Account Level",
    "account_code":         "Account Code",
    "account_type":         "Account Type",
    "account_balance":      "Account Balance",
    "opening_balance":      "Opening Balance",
    "closing_balance":      "Closing Balance",
    "journal_date":         "Entry Date",
    "journal_description":  "Entry Description",
    "total_debit":          "Total Debit",
    "total_credit":         "Total Credit",
    "balanced":             "Balanced",
    "unbalanced":           "Unbalanced",
    "post_entry":           "Post Entry",
    "reverse_entry":        "Reverse Entry",
    "draft":                "Draft",
    "posted":               "Posted",

    # ══════════════════════════════════════════════
    # Ledger
    # ══════════════════════════════════════════════
    "ledger":                  "Ledger",
    "t_account":               "T-Account",
    "normal_balance_dr":       "Debit Nature (DR↑)",
    "normal_balance_cr":       "Credit Nature (CR↑)",
    "ledger_accounts_title":      "📚  Accounts",
    "ledger_search_placeholder":  "Search description or entry number...",
    "ledger_select_account_prompt": "Select an account from the list to view its movements",
    "t_account_dr_header":     "📥  Debit  (DR)",
    "t_account_cr_header":     "📤  Credit  (CR)",
    "t_account_total":         "{label}: {amount}",
    "t_account_summary":       "{code} — {name}  │  {type}  │  Normal balance: {nb}",
    "ledger_movements_count":  "Movements Count",
    "ledger_normal_balance_card": "Normal Balance",
    "ledger_card_nb_dr":       "Debit (DR↑)",
    "ledger_card_nb_cr":       "Credit (CR↑)",
    "ledger_nb_short_dr":      "DR↑",
    "ledger_nb_short_cr":      "CR↑",

    # ══════════════════════════════════════════════
    # Journal Form
    # ══════════════════════════════════════════════
    "journal_balanced":        "✅ Balanced — can save",
    "journal_unbalanced":      "⚠️ Unbalanced",
    "add_journal_line":        "➕  Add Row",
    "journal_lines_title":     "📋  Journal Lines",
    "journal_dr_total":        "DR: {amount}",
    "journal_cr_total":        "CR: {amount}",
    "journal_dr_col":          "DR",
    "journal_cr_col":          "CR",
    "journal_increase":        "Increase ✚",
    "journal_decrease":        "Decrease ✖",
    "entry_type_manual":        "📝 Manual",
    "entry_type_opening":       "🟢 Opening",
    "entry_type_closing":       "🔴 Closing",
    "entry_type_transfer":      "🔄 Transfer",
    "entry_type_manual_short":  "Manual",
    "entry_type_opening_short": "Opening",
    "entry_type_closing_short": "Closing",
    "entry_type_transfer_short":"Transfer",
    "entry_type_auto_short":    "Auto",
    "select_account":          "— Select Account —",
    "select_journal_first":    "Select an entry first",
    "journal_saved_success":   "✅ Entry saved successfully",
    "no_dr_line":              "No debit (DR) line found",
    "no_cr_line":              "No credit (CR) line found",
    "entry_description_placeholder": "Entry description...",
    "line_description_placeholder":  "Description...",
    "balance_bar_diff":        "Diff:",
    "balance_bar_add_rows":    "○ Add rows",
    "entry_save_btn":          "💾  Save Entry",
    "entry_clear_btn":         "✖  Clear",
    "new_journal_entry":       "── New Journal Entry ──",

    # ══════════════════════════════════════════════
    # Audit Log
    # ══════════════════════════════════════════════
    "audit_log_delete":        "🗑️ Delete",
    "audit_log_update":        "✏️ Update",
    "audit_log_create":        "➕ Create",
    "audit_detail_title":      "Operation Details",
    "old_data":                "Old Data",
    "changed_by":              "Changed By",
    "no_audit_records":        "No records found",
    "no_audit_yet":            "No operations logged yet",
    "audit_all_tables":        "— All Tables —",
    "audit_all_types":         "— All Types —",

    "audit_log_header_title":       "🔍  Audit Log",
    "audit_table_filter_label":     "Table:",
    "audit_meta_line":              "Table: {table}  ·  Record ID: {record_id}  ·  By: {changed_by}",
    "audit_col_index":              "#",
    "audit_col_type":               "Type",
    "audit_col_table":              "Table",
    "audit_col_record_id":          "Record ID",
    "audit_col_date":               "Date",
    "audit_table_journal_entries":  "Journal Entries",
    "audit_table_journal_lines":    "Journal Lines",
    "audit_table_accounts":         "Accounts",
    "audit_table_inventory_moves":  "Inventory Moves",
    "audit_table_investor_entries": "Investor Entries",
    "group_delete_accounts_warn":   "⚠️ {count} account(s) will lose their category.",

    # ══════════════════════════════════════════════
    # Investors
    # ══════════════════════════════════════════════
    "investor_capital_badge":  "💰 Capital",
    "investor_drawings_badge": "💸 Drawings",
    "initial_capital":         "Initial Capital",
    "capital_account":         "Capital Account",
    "deposit_account":         "Deposit Account",
    "payment_account":         "Payment Account",
    "link_investor_to_entry":  "🔗  Link to Accounting Entry",
    "link_success":            "✅ Entry linked to investor successfully",
    "investor_join_date":      "Join Date",
    "investor_new":            "New Investor",
    "select_investor":         "Select Investor",
    "investor_movements":      "─── Financial Movements ───",
    "delete_movement_title":   "Confirm Delete Movement",
    "delete_movement_msg":     "Delete {type} (entry {ref})?\n\n⚠️ This will delete the movement and its accounting entry.",
    "investor_list_title":     "─── Investors ───",
    "add_capital_title":       "💰  Add Capital",
    "add_drawings_title":      "💸  Record Drawings",
    "expected_entry":          "Expected Entry:",
    "link_entry_info":         "🔗  Link an existing accounting entry to an investor\nUse this if you added the entry manually in the journal tab.",
    "entry_ref_placeholder":   "e.g. JE-00012",
    "link_entry_btn":          "🔗  Link",

    # ══════════════════════════════════════════════
    # Filters
    # ══════════════════════════════════════════════
    "group_filter":            "🏷 Group:",
    "balance_status_filter":   "Status:",
    "all_groups":              "— All Groups —",
    "balanced_filter":         "✅ Balanced",
    "unbalanced_filter":       "⚠️ Unbalanced",
    "move_type_all":           "All Movements",
    "move_type_dr":            "Debit Only",
    "move_type_cr":            "Credit Only",
    "clear_filters":           "↺ Clear Filters",
    "entry_date_label":        "Date:",
    "entry_type_label":        "Type:",
    "entry_desc_label":        "Description:",

    # ══════════════════════════════════════════════
    # Accounts messages
    # ══════════════════════════════════════════════
    "account_has_lines_msg":   "Account «{name}» or one of its sub-accounts\nhas {count} journal lines — cannot delete.",
    "delete_failed_msg":       "Delete failed:\n{error}",
    "select_category_first":   "Select a category first",
    "sub_accounts_delete_warning": "⚠️ {count} sub-account(s) will also be deleted.",

    # ══════════════════════════════════════════════
    # Accounting section tabs
    # ══════════════════════════════════════════════
    "assets_tab":              "🏦  Assets",
    "liabilities_tab":         "📋  Liabilities",
    "equity_tab":              "👑  Owners' Equity",
    "capital_tab":             "👑 Capital",
    "drawings_tab":            "💸 Drawings",
    "revenue_tab":             "💹 Revenue",
    "expense_tab":             "📤 Expenses",
    "income_statement_tab":    "📊 Income Statement",
    "owners_equity_tab":       "👑 Owners' Equity",
    "balance_sheet_tab":       "🏛️ Balance Sheet",
    "trial_balance_tab":       "⚖️ Trial Balance",

    # ══════════════════════════════════════════════
    # Accounts tree & group manager
    # ══════════════════════════════════════════════
    "no_accounts_msg":         "No accounts — add from the form on the right",
    "group_categories_header": "{type_name} Categories",
    "group_add_edit_header":   "➕ Add / Edit {type_name} Category",
    "group_new_placeholder":   "New Category",
    "group_name_placeholder":  "Category name...",
    "group_parent_label":      "Parent:",
    "group_color_label":       "Color:",
    "group_without_parent":    "— No Parent (Top Level) —",
    "group_default_color":     "#607d8b",
    "accounts_col":            "Code",
    "account_name_col":        "Account Name",
    "group_count_col":         "Account Count",
    "group_tree_col":          "Category",
    "group_tag_icon":          "🏷",
    "all_types_label":         "— All Categories —",
    "all_accounts_label":      "— All Categories —",

    # ══════════════════════════════════════════════
    # account_combo
    # ══════════════════════════════════════════════
    "select_account_combo":    "— Select Account —",
    "all_types_combo":         "— All Categories —",
    "dr_badge":                "DR↑",
    "cr_badge":                "CR↑",

    # ══════════════════════════════════════════════
    # Connection / loading state messages
    # ══════════════════════════════════════════════
    "conn_error_msg":          "❌  Database connection error:\n{error}",
    "init_failed_msg":         "❌  Failed to initialize accounting database\nTry restarting the app or re-selecting the company",
    "loading_db_msg":          "⏳  Initializing database... ({attempt}/{max})",
    "accounting_no_company_msg": "⚠️  Select a company first to view accounts",
    "group_filter_tooltip":    "Filter by category",
    "search_placeholder":      "🔍 Search...",

    # ══════════════════════════════════════════════
    # Journal movements table (_details_table)
    # ══════════════════════════════════════════════
    "movement_type_col":       "Type",
    "movement_amount":         "Amount",
    "movement_desc":           "Description",
    "capital_movement":        "💰 Capital",
    "drawings_movement":       "💸 Drawings",

    # ══════════════════════════════════════════════
    # Investor details (_investor_details)
    # ══════════════════════════════════════════════
    "investor_detail_placeholder": "Select an investor to view details",
    "total_capital":           "Total Capital",
    "total_drawings":          "Total Drawings",
    "net_investment":          "Net Investment",
    "investor_movements_header": "─── Financial Movements ───",
    "delete_movement_btn":     "🗑️  Delete Selected Movement",
    "select_movement_first":   "Select a movement first",
    "investor_joined":         "Joined",
    "investor_title_fmt":      "👤  {name}  │  {joined_label}: {date}",

    # ══════════════════════════════════════════════
    # Investor form (_investor_form)
    # ══════════════════════════════════════════════
    "investor_data_header":    "Investor Data",
    "investor_name_placeholder": "Investor name...",
    "initial_capital_header":  "💰  Initial Capital (Optional)",
    "amount_label":            "Amount:",
    "capital_account_label":   "Capital Account:",
    "deposit_account_label":   "Deposit Account:",
    "expected_entry_label":    "Entry:",
    "enter_amount_preview":    "─ Enter amount to preview entry",
    "enter_investor_name":     "Enter investor name",
    "add_investor_btn":        "➕  Add Investor",
    "investor_added_failed_entry": "Investor added but entry failed:\n{error}",

    # ══════════════════════════════════════════════
    # Investors table (_investors_table)
    # ══════════════════════════════════════════════
    "investor_name_col":       "Name",
    "join_date_col":           "Join Date",
    "capital_col":             "Capital",
    "drawings_col":            "Drawings",
    "net_col":                 "Net Investment",
    "add_investment_btn":      "💰  Add Investment",
    "select_investor_first":   "Select an investor first",

    # ══════════════════════════════════════════════
    # Movement dialog (_movement_dialog)
    # ══════════════════════════════════════════════
    "capital_account_row":     "Capital Account:",
    "drawings_account_row":    "Drawings Account:",
    "payment_account_label":   "Payment Account (Asset):",
    "deposit_account_row":     "Deposit Account (Asset):",
    "enter_amount_warning":    "Enter an amount greater than zero",
    "select_accounts_warning": "Select the required accounts",
    "record_btn":              "✅  Record",

    # ══════════════════════════════════════════════
    # Link to entry panel (_link_to_entry_panel)
    # ══════════════════════════════════════════════
    "link_data_header":        "Link Data",
    "move_type_label":         "Movement Type:",
    "ref_no_label":            "Entry Reference:",
    "investor_not_found":      "Select an investor",
    "entry_not_found":         "No entry found with reference «{ref}»",
    "enter_ref_no":            "Enter entry reference",
    "enter_positive_amount":   "Enter an amount greater than zero",

    # ══════════════════════════════════════════════
    # Investors layout tabs (_investors_layout)
    # ══════════════════════════════════════════════
    "investors_tab_title":     "👥  Investors",
    "link_to_entry_tab_title": "🔗  Link to Accounting Entry",

    # ══════════════════════════════════════════════
    # Balance Sheet (balance_sheet_tab)
    # ══════════════════════════════════════════════
    "balance_sheet_title":     "Balance Sheet",
    "balance_sheet_balanced":  "✅ Balanced",
    "total_assets":            "Total Assets",
    "total_liabilities":       "Total Liabilities",
    "equity_label":            "Owners' Equity",
    "assets_section":          "🏦 Assets",
    "liabilities_equity_section": "📋 Liabilities & Equity",
    "liabilities_label":       "Liabilities",
    "capital_label_bs":        "Capital",
    "drawings_bs":             "Drawings",
    "net_income_bs":           "Net Income",
    "equity_type_col":         "Type",
    "balance_sheet_diff":      "⚠️ Diff: {diff}",

    # ══════════════════════════════════════════════
    # Income Statement (income_statement_tab)
    # ══════════════════════════════════════════════
    "income_statement_title":  "Income Statement",
    "total_revenues":          "Total Revenues",
    "total_expenses":          "Total Expenses",
    "net_profit_loss":         "Net Profit / Loss",
    "revenues_section":        "💹 Revenues",
    "expenses_section":        "📤 Expenses",

    # ══════════════════════════════════════════════
    # Owners Equity (owners_equity_tab)
    # ══════════════════════════════════════════════
    "owners_equity_title":     "Owners' Equity Statement",
    "net_income_col":          "Net Income",
    "drawings_label":          "Drawings",
    "net_equity":              "Net Owners' Equity",
    "equity_increases":        "📈 Increases Equity (CR↑)",
    "equity_decreases":        "📉 Decreases Equity (DR↑)",
    "net_income_row":          "Net Income for Period",
    "income_minus_expenses":   "Revenues − Expenses",
    "equity_equation":         "Capital  {capital}  +  Net Income  {net_income}  −  Drawings  {drawings}  =  Net Equity  {total}",

    # ══════════════════════════════════════════════
    # Trial Balance (trial_balance_tab)
    # ══════════════════════════════════════════════
    "trial_balance_title":     "Trial Balance",
    "trial_balance_legend":    "🔵 Debit (Normal Balance DR)     🔴 Credit (Normal Balance CR)    — Amount always shown positive",
    "balance_col":             "Balance",
    "dr_balance":              "Debit",
    "cr_balance":              "Credit",
    "account_code_col":        "Code",
    "type_col":                "Type",
    "total_debit_col":         "Total Debit",
    "total_credit_col":        "Total Credit",
    "balance_balanced":        "✅ Trial Balance is Balanced",
    "balance_diff":            "⚠️ Diff: {diff}",
    "sum_debit_label":         "Total Debit: {val}",
    "sum_credit_label":        "Total Credit: {val}",

    # ══════════════════════════════════════════════
    # Shared table columns
    # ══════════════════════════════════════════════
    "item_col":                "Item",
    "link_no_col":             "ID",

    # ══════════════════════════════════════════════
    # Investor entry descriptions (helpers)
    # ══════════════════════════════════════════════
    "capital_entry_desc":   "Capital — {name}  {amount} {currency}",
    "drawings_entry_desc":  "Drawings — {name}  {amount} {currency}",

    # ══════════════════════════════════════════════
    # Journal tree table (journal_tree_table)
    # ══════════════════════════════════════════════
    "journal_table_title":         "── Saved Journal Entries ──",
    "journal_expand_all":          "⊞ Expand All",
    "journal_collapse_all":        "⊟ Collapse All",
    "journal_delete_selected":     "🗑️  Delete Selected",
    "journal_search_placeholder":  "Search description or entry number...",
    "journal_status_balanced":     "✅ Balanced",
    "journal_status_unbalanced":   "⚠️ {diff}",
    "select_entry_first":          "Select an entry first",
    "entry_type_auto":             "🤖 Auto",
    # entry_type_auto_short مُعرَّف أعلاه ضمن مجموعة entry_type_*_short
    "journal_unbalanced_detail":   "⚠️  Unbalanced ({side} by {diff})",
    "dr_bigger":                   "DR larger",
    "cr_bigger":                   "CR larger",
    "add_at_least_one_line":       "Add at least one line",
    "balance_error_title":         "Balance Error",
    "balance_error_msg":           "Total DR ({dr}) ≠ Total CR ({cr})",

    # ══════════════════════════════════════════════
    # Journal lines (_lines_panel, _smart_line)
    # ══════════════════════════════════════════════
    "lines_col_account":           "Account",
    "lines_col_direction":         "Direction",
    "lines_col_amount":            "Amount",
    "lines_col_desc":              "Description",
    "investor_link_label":         "👤  Link to Investor:",
    "investor_link_optional":      "(optional)",
    "investor_no_link":            "— No link —",
    "journal_filter_all_statuses": "All",
    "journal_count_label":         "({count} entries)",
    "journal_count_filtered":      "({shown} / {total})",
    "popup_hint_select":           "Double-click or press Enter to select",
    "account_search_placeholder":  "🔍 Search by name or code...",
    "account_group_unassigned":    "─── Unassigned ───",
    "account_code_placeholder":    "1141",
    "account_name_placeholder":    "Account name...",
    "account_tree_type_header":    "── {type} ──",
    "account_node_tooltip_with_group": "{name}  |  🏷 {group}",

    # ══════════════════════════════════════════════════════════════════
    # Shared Components — AmountLabel / DebitCreditDisplay / BalanceDisplay
    # ══════════════════════════════════════════════════════════════════
    "amount_dash_placeholder":          "─",
    "dr_total_label":                   "Total DR:",
    "cr_total_label":                   "Total CR:",
    "amount_zero_placeholder":          "0.00",
    "vertical_separator":               "│",
    "slash_separator":                  "/",
    "info_row_separator":               "  ·  ",
    "mode_label_wrap":                  "─── {content} ───",
    "balance_with_side":                " ({side_label})",
    "balance_dash":                     "Balance: ─",
    "progress_zero_pct":                "0%",
    "spinner_loading_text":             "Loading...",
    "spinner_done_check":               "✓",
    "loading_button_saving_text":       "Saving...",
    "notif_icon_success":                "✅",
    "notif_icon_info":                   "ℹ️",
    "notif_icon_warning":                "⚠️",
    "notif_icon_danger":                 "❌",
    "dismiss_icon":                      "✖",
    "icon_edit_pencil":                  "✏️",
    "icon_delete_trash":                 "🗑️",
    "icon_save_disk":                    "💾",
    "warning_bar_fix_text":              "🗑️ Delete Missing",
    "warning_bar_edit_text":             "✏️ Edit",
    "warning_bar_icon":                  "⚠️",
    "orphan_type_raw":                   "Raw Material",
    "orphan_type_semi":                  "Semi-Finished",
    "orphan_type_labor_op":              "Labor Operation",
    "orphan_type_machine_op":            "Machine Operation",
    "orphan_line_item":                  "• {type_label}: \u00ab{name}\u00bb",
    "orphans_warning_msg":               "\u00ab{product_name}\u00bb — {count} missing component(s):\n{lines}",

    # ── ColorPickerWidget ──────────────────────────────────
    "color_picker_btn":   "Pick Color",
    "color_picker_title": "Pick Color",

    # ── CategoryManager ────────────────────────────────────
    "category_tree_arrow": "↳ ",

    # ── FilterToolbar ──────────────────────────────────────
    "filter_reset_btn":         "↺",
    "filter_reset_tooltip":     "Clear All",
    "filter_cat_icon":          "🏷",
    "filter_date_icon":         "📅",

    # ── CollapsibleCard ────────────────────────────────────
    "collapsible_arrow_expanded":  "▼",
    "collapsible_arrow_collapsed": "▶",

    # ── InlinePreview / DataTable ──────────────────────────
    "inline_preview_label": "Result:",
    "empty_icon_search":    "🔍",
    "empty_icon_table":     "📋",

    # ── SharedOpsMixin ─────────────────────────────────────
    "shared_item_not_shared_use_edit": "This is a regular item — use «✏️ Edit» instead.",

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
