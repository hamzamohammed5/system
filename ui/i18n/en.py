"""
ui/i18n/en.py
==============
القاموس الإنجليزي الكامل للتطبيق.

يُستخدم من I18nManager في ui/i18n.py كمصدر للترجمة الإنجليزية.
يُصدّر EN_STRINGS للاستخدام المستقل أو للاستيراد من أدوات الترجمة.

[Sync] متطابق في المفاتيح مع ar.py — كل مفتاح موجود في الملفين بالضبط.
"""

EN_STRINGS: dict[str, str] = {

    # ══════════════════════════════════════════════
    # Buttons & Actions
    # ══════════════════════════════════════════════
    "save":              "Save",
    "save_edit":         "Save Changes",
    "add":               "Add",
    "edit":              "Edit",
    "delete":            "Delete",
    "cancel":            "Cancel",
    "confirm":           "Confirm",
    "close":             "Close",
    "search":            "Search",
    "reset":             "Reset",
    "refresh":           "Refresh",
    "export":            "Export",
    "import":            "Import",
    "print":             "Print",
    "back":              "Back",
    "next":              "Next",
    "previous":          "Previous",
    "yes":               "Yes",
    "no":                "No",
    "ok":                "OK",
    "apply":             "Apply",
    "browse":            "Browse",
    "select":            "Select",
    "clear":             "Clear",
    "copy":              "Copy",
    "paste":             "Paste",
    "open":              "Open",
    "new":               "New",
    "all":               "All",
    "clone":             "Clone",
    "selected":          "Selected",

    # ══════════════════════════════════════════════
    # Form Buttons
    # ══════════════════════════════════════════════
    "btn_add":      "➕  Add",
    "btn_save":     "💾  Save Changes",
    "btn_cancel":   "✖  Cancel",
    "btn_delete":   "🗑️  Delete",
    "btn_edit":     "✏️  Edit",
    "btn_refresh":  "🔄  Refresh",

    # ══════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════
    "nav_costing":       "Costing",
    "nav_pricing":       "Pricing",
    "nav_accounting":    "Accounting",
    "nav_inventory":     "Inventory",
    "nav_design":        "Designs",
    "nav_orders":        "Orders",
    "nav_shared":        "Shared Items",
    "nav_settings":      "Settings",

    # ══════════════════════════════════════════════
    # Settings
    # ══════════════════════════════════════════════
    "settings":          "Settings",
    "settings_font":     "Font Size",
    "settings_gimp":     "GIMP Path",
    "settings_units":    "Measurement Units",
    "settings_theme":    "Appearance",
    "settings_language": "Language",
    "theme_light":       "Light",
    "theme_dark":        "Dark",
    "lang_ar":           "العربية",
    "lang_en":           "English",
    "preview":           "Preview",

    # ══════════════════════════════════════════════
    # Empty States
    # ══════════════════════════════════════════════
    "no_data":              "No Data",
    "no_results":           "No Results",
    "no_search_results":    "Try changing the search term or filter",
    "select_item_first":    "Select an item first",
    "select_company":       "Please select an active company first",

    "list_search_placeholder": "🔍  Search...",
    "detail_select_item":      "Select an item from the list",

    # ══════════════════════════════════════════════
    # Confirm
    # ══════════════════════════════════════════════
    "confirm_delete":       "Confirm Delete",
    "confirm_save":         "Confirm Save",
    "confirm_action":       "Confirm",
    "delete_confirm_msg":   "Delete «{name}»?",
    "save_confirm_msg":     "Save «{name}»?",

    # ══════════════════════════════════════════════
    # Success / Error
    # ══════════════════════════════════════════════
    "success_add":          "Added successfully",
    "success_save":         "Saved successfully",
    "success_delete":       "Deleted successfully",
    "error_load":           "Error loading data",
    "error_save":           "Error saving",
    "error_delete":         "Error deleting",
    "warning":              "Warning",
    "error":                "Error",
    "info":                 "Info",
    "notice":               "Notice",
    "done":                 "Done",

    # ══════════════════════════════════════════════
    # Field Validation Messages
    # ══════════════════════════════════════════════
    "enter_field":          "Enter {label}",
    "select_field":         "Select {label}",
    "field_positive":       "{label} must be greater than zero",
    "field_positive_enter": "Enter {label} greater than zero",

    # ══════════════════════════════════════════════
    # General Fields
    # ══════════════════════════════════════════════
    "name":                 "Name",
    "code":                 "Code",
    "description":          "Description",
    "notes":                "Notes",
    "date":                 "Date",
    "amount":               "Amount",
    "price":                "Price",
    "quantity":             "Quantity",
    "unit":                 "Unit",
    "category":             "Category",
    "status":               "Status",
    "type":                 "Type",
    "total":                "Total",
    "subtotal":             "Subtotal",
    "discount":             "Discount",
    "tax":                  "Tax",

    # ══════════════════════════════════════════════
    # Time Units
    # ══════════════════════════════════════════════
    "month":                "month",
    "day":                  "day",
    "hour":                 "hour",

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
    "fiscal_year":          "Fiscal Year",
    "owners_equity":        "Owners Equity",
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
    # Inventory
    # ══════════════════════════════════════════════
    "inventory":            "Inventory",
    "stock_in":             "In",
    "stock_out":            "Out",
    "current_stock":        "Current Stock",
    "inbound":              "Inbound",
    "outbound":             "Outbound",
    "inventory_report":     "Inventory Report",
    "item_name":            "Item Name",
    "item_type":            "Item Type",
    "min_stock":            "Min Stock Level",
    "current_balance":      "Current Balance",
    "movement_date":        "Movement Date",
    "movement_type":        "Movement Type",
    "unit_cost":            "Unit Cost",
    "total_inbound":        "Total Inbound",
    "total_outbound":       "Total Outbound",
    "low_stock":            "Low Stock",
    "low_stock_items":      "Low Stock Items",
    "stock_value":          "Stock Value",
    "no_movements":         "No movements found",
    "record_inbound":       "Record Inbound",
    "record_outbound":      "Record Outbound",
    "movement_ref":         "Movement Reference",

    # ══════════════════════════════════════════════
    # Companies
    # ══════════════════════════════════════════════
    "company":              "Company",
    "select_company_msg":   "Select a company to start",
    "no_company":           "No active company",
    "manage_companies":     "Manage Companies",

    # ══════════════════════════════════════════════
    # Costing
    # ══════════════════════════════════════════════
    "cost":                 "Cost",
    "cost_per_unit":        "Cost per Unit",
    "selling_price":        "Selling Price",
    "profit_margin":        "Profit Margin",
    "waste":                "Waste",
    "waste_pct":            "Waste %",

    # ══════════════════════════════════════════════
    # BOM — Component Types
    # ══════════════════════════════════════════════
    "components":           "Components",
    "raw_material":         "Raw Material",
    "semi_product":         "Semi-Finished",
    "labor_op":             "Labor Operation",
    "machine_op":           "Machine Operation",

    # ══════════════════════════════════════════════
    # Filters
    # ══════════════════════════════════════════════
    "filter_all":               "— All —",
    "filter_all_categories":    "— All Categories —",
    "date_from":                "From:",
    "date_to":                  "To:",
    "today":                    "Today",
    "this_month":               "Month",
    "this_year":                "Year",

    # ══════════════════════════════════════════════
    # Status Bar
    # ══════════════════════════════════════════════
    "showing_of":   "{shown} / {total}",
    "showing_all":  "{total}",

    # ══════════════════════════════════════════════
    # Categories
    # ══════════════════════════════════════════════
    "category_data":          "Category Data",
    "category_name":          "Name",
    "category_parent":        "Parent",
    "category_color":         "Color",
    "category_add":           "New Category",
    "category_new":           "Children",
    "category_edit":          "Edit",
    "category_delete":        "Delete",
    "category_select_first":  "Select a category first",
    "category_name_required": "Enter category name",
    "no_category":            "No Category",

    # ══════════════════════════════════════════════
    # Operations
    # ══════════════════════════════════════════════
    "operation_add":    "Add",
    "operation_edit":   "Edit",
    "operation_delete": "Delete",
    "operation_save":   "Save",
    "operation_cancel": "Cancel",

    # ══════════════════════════════════════════════
    # Designs
    # ══════════════════════════════════════════════
    "designs":              "Designs",
    "design_add":           "Add Design",
    "design_categories":    "Design Categories",
    "dimension_sets":       "Dimension Sets",
    "design_name":          "Design Name",
    "design_file":          "Design File",
    "open_in_gimp":         "Open in GIMP",
    "thumbnail":            "Thumbnail",
    "dimension_set_name":   "Dimension Set Name",
    "dimension_group":      "Dimension Group",
    "dimension_field":      "Dimension Field",
    "dimension_value":      "Dimension Value",
    "dimension_instance":   "Dimension Instance",
    "no_designs":           "No designs found",
    "add_size":             "Add Size",
    "size_name":            "Size Name",
    "size_width":           "Width",
    "size_height":          "Height",
    "gimp_not_found":       "GIMP not found",
    "file_not_found":       "File not found",
    "source_set":           "Source Set",
    "target_field":         "Target Field",

    # ══════════════════════════════════════════════
    # Orders
    # ══════════════════════════════════════════════
    "orders":               "Orders",
    "order_add":            "Add Order",
    "customers":            "Customers",
    "customer_add":         "Add Customer",
    "order_status":         "Order Status",
    "order_date":           "Order Date",
    "order_number":         "Order Number",
    "order_total":          "Order Total",
    "customer_name":        "Customer Name",
    "customer_phone":       "Customer Phone",
    "customer_address":     "Customer Address",
    "delivery_date":        "Delivery Date",
    "payment_status":       "Payment Status",
    "order_items":          "Order Items",
    "status_pending":       "Pending",
    "status_confirmed":     "Confirmed",
    "status_in_production": "In Production",
    "status_ready":         "Ready",
    "status_delivered":     "Delivered",
    "status_cancelled":     "Cancelled",
    "dashboard":            "Dashboard",
    "recent_orders":        "Recent Orders",
    "top_customers":        "Top Customers",
    "order_log":            "Order Log",
    "change_status":        "Change Status",
    "no_orders":            "No orders found",
    "no_customers":         "No customers found",
    "paid":                 "Paid",
    "unpaid":               "Unpaid",
    "partial":              "Partial",
    "deposit":              "Deposit",
    "unit_price":           "Unit Price",
    "item_qty":             "Qty",
    "item_total":           "Total",

    # ══════════════════════════════════════════════
    # Pricing
    # ══════════════════════════════════════════════
    "pricing":              "Pricing",
    "offers":               "Offers",
    "offer_add":            "Add Offer",
    "offer_name":           "Offer Name",
    "offer_validity":       "Offer Validity",
    "offer_items":          "Offer Items",
    "base_cost":            "Base Cost",
    "markup_pct":           "Markup %",
    "final_price":          "Final Price",
    "product_cost":         "Product Cost",
    "scenario_used":        "Scenario Used",
    "offer_total":          "Offer Total",
    "no_offers":            "No offers found",
    "pricing_table":        "Pricing Table",
    "cost_breakdown":       "Cost Breakdown",
    "min_price":            "Minimum Price",
    "suggested_price":      "Suggested Price",
    "customer_price":       "Customer Price",

    # ══════════════════════════════════════════════
    # Custom Delete Messages
    # ══════════════════════════════════════════════
    "delete_has_children":  "Cannot delete — has sub-items",
    "delete_has_items":     "Cannot delete — linked to other items",

    # ══════════════════════════════════════════════
    # Shared Items
    # ══════════════════════════════════════════════
    "shared_items":  "Shared Items",
    "publish":       "Publish",
    "published":     "Published",
    "not_published": "Not Published",

    # ══════════════════════════════════════════════
    # Currency & Units
    # ══════════════════════════════════════════════
    "currency_abbr":          "EGP",
    "currency":               "EGP",
    "currency_per_piece":     "EGP / piece",
    "currency_per_hour":      "EGP / hour",
    "currency_per_unit":      "EGP / unit",
    "piece":                  "piece",
    "minutes_abbr":           "min",

    # ══════════════════════════════════════════════
    # Products
    # ══════════════════════════════════════════════
    "new_product":              "New Product",
    "product_name_placeholder": "Product name...",
    "saved_products":           "Saved Products",
    "no_products":              "No products found",
    "enter_product_name":       "Please enter a product name first",
    "add_one_component":        "Please add at least one component",
    "product_name":             "Product Name",
    "add_component":            "Component",

    # ══════════════════════════════════════════════
    # Components / BOM
    # ══════════════════════════════════════════════
    "element":            "Element",
    "row_or_variant":     "Row / Variant",
    "qty":                "Qty",
    "waste_pct_col":      "Waste %",
    "effective_qty":      "Effective Qty",
    "component_scenario": "Component / Scenario",

    # ══════════════════════════════════════════════
    # BOM Tree
    # ══════════════════════════════════════════════
    "bom_tree":                        "BOM Structure",
    "expand_all":                      "Expand All",
    "collapse_all":                    "Collapse All",
    "delete_selected":                 "Delete Selected",
    "default_scenario":                "Default Scenario",
    "delete_from_scenario":            "Delete",
    "from_scenario":                   "from scenario",
    "delete_sub_components_from_semi": "Delete sub-components from the semi-finished product itself",

    # ══════════════════════════════════════════════
    # Scenarios
    # ══════════════════════════════════════════════
    "scenario":                    "Scenario",
    "add_scenario":                "Add Scenario",
    "clone_scenario":              "Clone Scenario",
    "rename_scenario":             "Rename",
    "set_as_default":              "Set as Default",
    "new_scenario":                "New Scenario",
    "new_scenario_name":           "New Scenario Name",
    "scenario_name":               "Scenario Name",
    "new_name":                    "New Name",
    "copy_of":                     "Copy of",
    "cannot_delete_last_scenario": "Cannot delete the only scenario",
    "delete_scenario_confirm":     "Delete scenario",
    "delete_scenario_failed":      "Failed to delete scenario",
    "select_scenario":             "Select scenario",

    # ══════════════════════════════════════════════
    # Scenario Comparison
    # ══════════════════════════════════════════════
    "scenario_comparison":        "Scenario Comparison",
    "compare_scenario":           "Compare with",
    "default_scenario_cost":      "Default Cost",
    "compare_scenario_cost":      "Compare Cost",
    "cost_diff":                  "Cost Diff",
    "fixed_price":                "Fixed Price",
    "default_scenario_profit":    "Default Profit",
    "compare_scenario_profit":    "Compare Profit",
    "profit_diff":                "Profit Diff",
    "compare_profit_margin":      "Compare Margin",
    "select_scenario_to_compare": "Select a scenario to compare",
    "compare_higher_cost":        "higher cost by",
    "profit_decreases":           "profit decreases by",
    "compare_lower_cost":         "lower cost by",
    "profit_increases":           "profit increases by",
    "equal_cost_scenarios":       "Both scenarios have equal cost",
    "select_product_to_compare":  "Select a product to start comparison",

    # ══════════════════════════════════════════════
    # Bulk Replace
    # ══════════════════════════════════════════════
    "operation_required":     "Operation Required",
    "replace_element":        "Replace Element",
    "edit_qty_only":          "Edit Qty Only",
    "both_operations":        "Both Operations",
    "replacement_raw":        "Replacement Raw",
    "replacement_labor_op":   "Replacement Labor Op",
    "replacement_machine_op": "Replacement Machine Op",
    "replacement":            "Replacement",
    "select_replacement":     "Select Replacement",
    "no_alternatives":        "No alternatives available",
    "apply_uniform_qty":      "Apply Uniform Qty",
    "filter_by_category":     "Filter by Category",
    "select_all":             "All",
    "select_none":            "None",
    "invert_selection":       "Invert",
    "no_products_linked":     "No products linked to this element",
    "quick_select":           "Quick Select",
    "apply_to_selected":      "Apply to Selected",

    # ══════════════════════════════════════════════
    # Machine Op Rows
    # ══════════════════════════════════════════════
    "op_rows_editor":              "Operation Rows",
    "add_row":                     "Add Row",
    "edit_row":                    "Edit Row",
    "delete_row":                  "Delete Row",
    "row_description_placeholder": "Row description...",
    "value_minutes":               "Value (minutes)",
    "time_minutes":                "Time (minutes)",
    "units":                       "Units",
    "value":                       "Value",
    "count":                       "Count",
    "total_op_cost":               "Total Operation Cost",
    "select_row_first":            "Please select a row first",
    "min_one_row_required":        "At least one row is required",
    "calc_mode":                   "Calculation Mode",
    "by_time":                     "By Time",
    "by_unit":                     "By Unit",
    "rate":                        "Rate",

    # ══════════════════════════════════════════════
    # Raw Variants
    # ══════════════════════════════════════════════
    "raw_variants":                "Production Units (Variants)",
    "variant_description_line1":   "Each variant defines how many pieces come from one unit of raw material",
    "variant_unit_cost_formula":   "Unit Cost = Total Price ÷ Pieces Count",
    "variant_name_placeholder":    "Variant name...",
    "pieces_count":                "Pieces Count",
    "pieces_tooltip_line1":        "Number of pieces produced from one raw material unit",
    "add_variant":                 "Add Variant",
    "enter_variant_name":          "Please enter a variant name",
    "select_variant_first":        "Please select a variant first",
    "delete_variant_confirm":      "Delete variant",
    "currency_per_piece_short":    "EGP/piece",

    # ══════════════════════════════════════════════
    # Raw Materials
    # ══════════════════════════════════════════════
    "raw_materials": "Raw Materials",
    "no_raws":       "No raw materials found",
    "saved_raws":    "Saved Raw Materials",

    # ══════════════════════════════════════════════
    # Labor
    # ══════════════════════════════════════════════
    "labor_ops": "Labor Operations",

    # ══════════════════════════════════════════════
    # Machine
    # ══════════════════════════════════════════════
    "machine_ops": "Machine Operations",

    # ══════════════════════════════════════════════
    # Labor Cost Settings
    # ══════════════════════════════════════════════
    "labor_cost_settings":    "Labor Cost Settings",
    "base_salary":            "Base Salary",
    "working_days":           "Working Days",
    "holiday_days":           "Holiday Days",
    "working_hours_per_day":  "Working Hours / Day",
    "overhead_factor":        "Overhead Factor",
    "hourly_rate":            "Hourly Rate",
    "save_labor_settings":    "Save Labor Settings",
    "labor_settings_saved":   "Labor settings saved",

    # ══════════════════════════════════════════════
    # Section Tab Names
    # ══════════════════════════════════════════════

    # Costing tabs
    "raw_tab":        "Raw Materials",
    "labor_tab":      "Labor",
    "machine_tab":    "Machine Ops",
    "product_tab":    "Products",
    "categories_tab": "Categories",

    # Accounting tabs
    "accounts_tab":   "Chart of Accounts",
    "journal_tab":    "Journal Entries",
    "ledger_tab":     "Ledger",
    "financial_tab":  "Financial Statements",
    "investors_tab":  "Investors",

    # Inventory tabs
    "inventory_items":          "Inventory Items",
    "inventory_items_tab":      "Items",
    "inventory_inbound_tab":    "Inbound",
    "inventory_outbound_tab":   "Outbound",
    "inventory_report_tab":     "Report",
    "low_stock_alert":          "Low Stock Alert",
    "avg_unit_cost":            "Avg. Unit Cost",
    "total_inbound_value":      "Total Inbound Value",
    "total_outbound_value":     "Total Outbound Value",

    # Orders tabs
    "orders_tab":    "Orders",
    "customers_tab": "Customers",
    "dashboard_tab": "Dashboard",

    # Design tabs
    "designs_tab":           "Designs",
    "dimension_sets_tab":    "Dimension Sets",
    "design_categories_tab": "Design Categories",

    # Pricing tabs
    "pricing_tab": "Pricing",
    "offers_tab":  "Offers",

    # ══════════════════════════════════════════════
    # App
    # ══════════════════════════════════════════════
    "app_title":         "Cost Management System",
    "app_title_company": "Cost Management System — {name}",
    "under_development": "Under Development",

    # ══════════════════════════════════════════════
    # Costing Section & Tabs
    # ══════════════════════════════════════════════
    "costing_section":    "Cost Management",
    "final_product":      "Final Product",
    "labor":              "Labor",
    "machine":            "Machine",
    "machines":           "Machines",
    "machine_operations": "Machine Operations",
    "labor_settings":     "Labor Settings",
    "labor_operations":   "Labor Operations",

    # ══════════════════════════════════════════════
    # Product Messages
    # ══════════════════════════════════════════════
    "select_product_first":     "Select a product from the list first",
    "select_product_to_delete": "Select a product first",
    "delete_orphan_components": "Delete Missing",

}