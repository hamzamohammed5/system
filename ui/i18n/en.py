"""
ui/i18n/en.py
==============
القاموس الإنجليزي الكامل للتطبيق.

يُستخدم من I18nManager في ui/i18n.py كمصدر للترجمة الإنجليزية.
يُصدّر EN_STRINGS للاستخدام المستقل أو للاستيراد من أدوات الترجمة.

[Sync] متطابق في المفاتيح مع ar.py — كل مفتاح موجود في الملفين بالضبط.
[Update] إضافة مفاتيح جديدة للماكينات وعمليات التشغيل والعمالة وعامة
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

    # ── Orders — section tab titles ───────────────────────
    "orders_section_tab_dashboard": "📊  Dashboard",
    "orders_section_tab_orders":    "📋  Orders",
    "orders_section_tab_customers": "👥  Customers",

    # ── Orders — fields and dialogs ───────────────────────
    "order_internal_notes":    "Internal Notes",
    "order_new_btn":           "＋  New Order",
    "customer_new_btn":        "＋  New Customer",
    "order_reorder_btn":       "📋  Re-order",
    "order_change_status_btn": "🔄  Change Status",
    "order_cancel_btn_action": "❌  Cancel Order",
    "order_edit_btn":          "✏️  Edit",
    "order_delete_btn":        "🗑️  Delete",
    "order_add_item_btn":      "＋  Add Item",
    "order_edit_item_btn":     "✏️  Edit Item",
    "order_del_item_btn":      "🗑️  Delete Item",
    "order_import_offer_btn":  "📥  Import",
    "order_select_offer_lbl":  "Or import an offer:",
    "order_subtotal_lbl":      "Subtotal (before discount):",
    "order_items_count_lbl":   "Items:",
    "order_no_items_warn":     "Add at least one item",
    "order_no_customer_warn":  "Select a customer first",
    "order_save_btn":          "💾  Save Order",
    "order_new_title":         "📋  New Order",
    "order_edit_title":        "✏️  Edit Order",
    "order_customer_section":  "👤  Customer Info",
    "order_details_section":   "📋  Order Details",
    "order_items_section":     "📦  Order Items",
    "order_notes_section":     "📝  Notes",
    "order_customer_notes":    "Customer Notes:",
    "order_internal_notes_lbl":"Internal Notes:",
    "order_customer_search":   "Search customer by name, phone or code...",
    "order_item_search":       "🔍 Search...",
    "order_select_product":    "— Select Product —",
    "order_select_offer":      "— Select Offer —",
    "order_unit_label":        "Unit",
    "order_unit_default":      "piece",
    "order_discount_total":    "Total Discount",
    "order_paid_amount":       "Paid",
    "order_priority_label":    "Priority",
    "order_type_label":        "Order Type",
    "order_due_date_label":    "Delivery Date",
    "order_status_label":      "Status",
    "order_search_placeholder":"🔍  Search by order number or customer...",
    "order_all_statuses":      "All Statuses",
    "order_all_priorities":    "All Priorities",
    "order_reset_filter":      "↺  Clear",
    "order_refresh_btn":       "↺  Refresh",
    "order_delete_confirm":    "Permanently delete order {number}?\nThis action cannot be undone.",
    "order_delete_failed":     "Order can only be deleted in pending or cancelled status.",
    "order_reorder_confirm":   "Create a new order based on {number}?",
    "order_cancel_reason":     "Reason for cancelling order {number}:",
    "order_cancel_title":      "Cancel Order",
    "item_unit_price":         "Unit Price:",
    "item_discount_lbl":       "Discount:",
    "item_qty_lbl":            "Qty:",
    "item_total_lbl":          "Total:",
    "item_notes_lbl":          "Notes:",
    "item_design_ref_lbl":     "Design Ref:",
    "item_name_lbl":           "Item *",
    "item_desc_lbl":           "Description:",
    "item_save_btn":           "💾  Save Item",
    "item_add_title":          "➕  Add Item",
    "item_edit_title":         "✏️  Edit Item",
    "item_name_warn":          "Enter item name",
    "contact_name_lbl":        "Name * :",
    "contact_role_lbl":        "Role :",
    "contact_phone_lbl":       "Phone :",
    "contact_email_lbl":       "Email :",
    "contact_notes_lbl":       "Notes :",
    "contact_add_btn":         "➕  Add Contact",
    "contact_del_btn":         "🗑️  Delete",
    "contact_ok_btn":          "✅  Add",
    "contact_title":           "Contact",
    "contact_name_warn":       "Enter contact name",
    "customer_basic_section":  "Basic Info",
    "customer_contacts_section":"Additional Contacts",
    "customer_type_individual":"Individual",
    "customer_type_company":   "Company",
    "customer_name_lbl":       "Name * :",
    "customer_type_lbl":       "Type :",
    "customer_phone_lbl":      "Phone :",
    "customer_phone2_lbl":     "Phone 2 :",
    "customer_email_lbl":      "Email :",
    "customer_city_lbl":       "City :",
    "customer_address_lbl":    "Address :",
    "customer_notes_lbl":      "Notes :",
    "customer_save_btn":       "💾  Save",
    "customer_new_title":      "👤  New Customer",
    "customer_edit_title":     "✏️  Edit Customer",
    "customer_name_warn":      "Enter customer name",
    "customer_delete_confirm": "Permanently delete customer «{name}»?\nCustomers with orders cannot be deleted.",
    "customer_delete_failed":  "Cannot delete this customer — linked orders exist.\nYou can deactivate instead.",
    "customer_toggle_active":  "✅  Activate",
    "customer_toggle_inactive":"⏸  Deactivate",
    "status_change_title":     "Change Order Status",
    "status_current_lbl":      "Current Status:",
    "status_new_lbl":          "New Status:",
    "status_note_lbl":         "Notes (optional):",
    "status_note_placeholder": "Reason for change...",
    "status_change_btn":       "✅  Change Status",
    "dashboard_recent_orders": "Recent Orders",
    "dashboard_status_dist":   "Orders by Status",
    "order_type_new":          "🆕 New",
    "order_type_reorder":      "🔄 Re-order",
    "order_type_custom":       "⚙️ Custom",
    "priority_low":            "⬇ Low",
    "priority_normal":         "➡ Normal",
    "priority_high":           "⬆ High",
    "priority_urgent":         "🔴 Urgent",
    "status_on_hold":          "⏸ On Hold",
    "status_in_progress":      "🔧 In Progress",
    "order_total_value":       "Total Value",
    "order_total_paid":        "Total Paid",
    "order_urgent_count":      "Urgent",
    "order_total_count":       "Total Orders",
    "order_no_items_title":    "No items in this order",
    "order_no_items_hint":     "Press «＋ Add Item» to add a product",
    "order_select_first":      "Select an order from the list",
    "order_select_subtitle":   "Or create a new order by pressing ＋ New Order",
    "customer_select_first":   "Select a customer from the list",
    "customer_select_subtitle":"Or add a new customer by pressing ＋",
    "log_section_title":       "Status Change Log",
    "log_col_from":            "From",
    "log_col_to":              "To",
    "log_col_notes":           "Notes",
    "log_col_time":            "Time",
    "items_col_name":          "Item",
    "items_col_desc":          "Description",
    "items_col_qty":           "Qty",
    "items_col_unit":          "Unit",
    "items_col_price":         "Price",
    "items_col_discount":      "Disc%",
    "items_col_total":         "Total",
    "customer_col_code":       "Code",
    "customer_col_name":       "Name",
    "customer_col_phone":      "Phone",
    "customer_col_city":       "City",
    "customer_col_orders":     "Orders",
    "order_col_number":        "Order No.",
    "order_col_customer":      "Customer",
    "order_col_status":        "Status",
    "order_col_priority":      "⚑",
    "order_col_date":          "Date",
    "customer_total_orders":   "Total Orders",
    "customer_active_orders":  "Active Orders",
    "customer_total_value":    "Total Value",
    "customer_balance":        "Balance",
    "customer_contacts_title": "📞  Contacts",
    "customer_orders_title":   "📋  Recent Orders",
    "customer_no_contacts":    "No contacts",
    "offer_select_label":      "— Select Offer —",
    "order_header_total":      "Total",
    "order_header_paid":       "Paid",
    "order_header_balance":    "Balance",
    "order_header_due":        "Due Date",

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
    "currency_sym":           "EGP",           # short symbol for compact display
    "amount_fmt":             "{amount:.2f}  EGP",
    "amount_disc_fmt":        "{amount:.2f}  EGP  ({pct:.1f}%)",
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

    # ══════════════════════════════════════════════
    # Machine Form — New Keys
    # ══════════════════════════════════════════════
    "machine_form_title":         "Machine Data",
    "machine_name":               "Machine Name",
    "machine_name_placeholder":   "e.g. Sewing Machine, Oven, Press...",
    "machine_name_required":      "Enter machine name",
    "rate_per_hour":              "Rate / Hour",
    "rate_per_unit":              "Rate / Unit",
    "add_machine_new":            "Add New Machine",
    "editing_prefix":             "Edit",
    "enter_name":                 "Enter Name",

    # ══════════════════════════════════════════════
    # Machine Op Form — New Keys
    # ══════════════════════════════════════════════
    "machine_op_form_title":       "Machine Operation Data",
    "machine_op_name_placeholder": "e.g. Stitch, Press...",
    "add_machine_op_new":          "Add New Machine Operation",
    "op_name":                     "Operation Name",
    "machine_label":               "Machine",
    "select_machine_first":        "Select a machine first",
    "add_op_first_hint":           "Add the operation first to see rows",
    "mode_time_label":             "⏱ By Time",
    "mode_unit_label":             "📦 By Unit",
    "total_cost_label":            "Total Cost",
    "op_added_success":            "Operation «{name}» added\nAdd rows now then click Save",

    # ══════════════════════════════════════════════
    # Labor Op Form — New Keys
    # ══════════════════════════════════════════════
    "labor_op_form_title":        "Operation Data",
    "time_label":                 "Time",
    "cost_label":                 "Cost",
    "minutes_label":              "minutes",

    # ══════════════════════════════════════════════
    # Raw Form — New Keys
    # ══════════════════════════════════════════════
    "raw_form_title":             "Raw Material Data",
    "raw_name_label":             "Raw Material Name",
    "raw_name_required":          "Enter raw material name...",
    "raw_price_label":            "Total Price",
    "raw_qty_label":              "Total Quantity",
    "raw_qty_unit":               "unit",
    "raw_qty_tooltip":            "Leave at zero if price is per unit\nUnit Price = Total Price ÷ Total Quantity",
    "raw_hint_with_qty":          "💡 Unit Price = {price} ÷ {qty} = {unit} EGP/unit",
    "raw_hint_qty_only":          "💡 Unit Price = Total Price ÷ Total Quantity",
    "raw_hint_no_qty":            "💡 Without total quantity: entered price = unit price directly",
    "raw_add_variants_mode":      "Add production units for: {name}",

    # ══════════════════════════════════════════════
    # Ledger
    # ══════════════════════════════════════════════
    "ledger":                  "Ledger",
    "t_account":               "T-Account",
    "normal_balance_dr":       "Debit Nature (DR↑)",
    "normal_balance_cr":       "Credit Nature (CR↑)",

    # ══════════════════════════════════════════════
    # Journal Form
    # ══════════════════════════════════════════════
    "journal_balanced":        "✅ Balanced — can save",
    "journal_unbalanced":      "⚠️ Unbalanced",
    "add_journal_line":        "➕  Add Row",
    "journal_lines_title":     "📋  Journal Lines",
    "journal_increase":        "Increase ✚",
    "journal_decrease":        "Decrease ✖",
    "entry_type_manual":       "📝 Manual",
    "entry_type_opening":      "🟢 Opening",
    "entry_type_closing":      "🔴 Closing",
    "entry_type_transfer":     "🔄 Transfer",
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
    # Pagination
    # ══════════════════════════════════════════════
    "load_more":               "Load {count} More  ▼",
    "show_all_records":        "Show All",
    "showing_records":         "Showing {shown:,} of {total:,}",
    "showing_all_records":     "Showing all {shown:,} records",

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

    # ══════════════════════════════════════════════════════════════════
    # Inventory
    # ══════════════════════════════════════════════════════════════════
    "inventory_purchase_success":   "✅ Inbound recorded and accounting entry created",
    "inventory_supplier_keyword":   "supplier",
    "inventory_select_item":        "Select an item first",
    "inventory_select_payment":     "Select a payment account",
    "inventory_valid_qty_cost":     "Enter valid quantity and price",
    "inventory_adjust_negative":    "Adjustment quantity cannot be negative",
    "record_outbound_success":      "Outbound recorded successfully",
    "inventory_item_name":          "Item Name",
    "inventory_new_item":           "New Item",
    "inventory_unit_placeholder":   "piece / meter / kg...",
    "inventory_min_qty_label":      "Min Level",
    "inventory_link_raw":           "Link to Raw Material",
    "inventory_acc_account":        "Inventory Account",
    "inventory_outbound_title":     "📤  Issue / Consumption",
    "inventory_inbound_title":      "📥  Receive / Purchase",
    "inventory_recent_inbound":     "─── Recent Inbound Movements ───",
    "inventory_recent_outbound":    "─── Recent Outbound Movements ───",
    "inventory_items_header":       "─── Inventory Items ───",
    "inventory_purpose":            "Purpose of issue...",
    "inventory_payment_account":    "Payment Account",
    "inventory_available_qty":      "Balance: {qty} {unit}",
    "inventory_available_none":     "Balance: —",
    "inventory_item_data_group":    "Item Data",
    "inventory_item_new_mode":      "─── New Item ───",
    "edit_mode_fmt":                "─── Edit: {name} ───",
    "inventory_item_name_placeholder": "Item name...",
    "inventory_qty_min_tooltip":    "Minimum quantity to trigger a reorder alert",
    "inventory_raw_item_fmt":       "🧱 {name}",
    "inventory_default_account_placeholder": "— Default Inventory Account —",
    "notes_placeholder":            "Notes...",
    "inventory_add_item":           "Add Item",
    "item":                         "Item",
    "inventory_select_item_placeholder": "— Select Item —",
    "entry_no_col":                 "Entry No.",
    "id_col":                       "ID",
    "avg_cost":                     "Average Cost",
    "total_value":                  "Total Value",
    "inventory_below_min_tooltip":  "⚠️ Below minimum ({min})",
    "inventory_outbound_save":      "Record Outbound",
    "inventory_inbound_save":       "Record Inbound + Accounting Entry",
    "statement_col":                "Statement",
    "inventory_total_items_card":   "Item Count",
    "inventory_total_value_card":   "Total Inventory Value",
    "inventory_low_stock_card":     "Items Below Minimum",
    "inventory_zero_stock_card":    "Out of Stock Items",
    "inventory_detailed_report_header": "─── Detailed Inventory Report ───",
    "inventory_status_out":         "❌ Out of Stock",
    "inventory_status_low":         "⚠️ Low",
    "inventory_status_ok":          "✅ Available",
    "inventory_select_item_for_moves": "Select an item to view its movements",
    "inventory_item_moves_title_fmt": "📦  Movements: {name}  (Balance: {qty} {unit})",
    "move_type_in":                 "📥 In",
    "move_type_out":                "📤 Out",
    "move_type_adjust":             "⚖️ Adjustment",

    # ══════════════════════════════════════════════════════════════════
    # Pricing
    # ══════════════════════════════════════════════════════════════════
    "pricing_product_label":        "Product",
    "pricing_margin_label":         "Profit Margin",
    "pricing_final_price_label":    "Final Price",
    "pricing_cost_stat":            "Cost",
    "pricing_suggested_stat":       "Suggested Selling Price",
    "pricing_manual_stat":          "Manual Price",
    "pricing_profit_stat":          "Profit",
    "pricing_margin_actual_stat":   "Actual Margin %",
    "pricing_select_product":       "Select a product first",
    "pricing_price_positive":       "Price must be greater than zero",
    "pricing_delete_confirm":       "Delete price for «{name}»?",
    "pricing_saved_prices":         "─── Price List ───",
    "pricing_new_mode":             "─── Price a Product ───",
    "pricing_edit_mode":            "─── Edit Price: {name} ───",
    "offer_new_mode":               "─── New Offer ───",
    "offer_edit_mode":              "─── Edit: {name} ───",
    "offer_name_label":             "Offer Name",
    "offer_discount_label":         "Discount",
    "offer_category_label":         "Category",
    "offer_notes_label":            "Notes",
    "offer_add_product_btn":        "➕  Add Product to Offer",
    "offer_save_btn":               "💾  Save Offer",
    "offer_total_before_disc":      "Total Price Before Discount",
    "offer_discount_value":         "Discount Amount",
    "offer_sell_price":             "Final Selling Price",
    "offer_total_cost":             "Total Cost",
    "offer_profit":                 "Profit",
    "offer_select_product_search":  "🔍 Search...",
    "offer_col_product":            "Product",
    "offer_col_category":           "Category",
    "offer_col_qty":                "Qty",
    "offer_col_unit_cost":          "Cost/Unit",
    "offer_col_unit_price":         "Price/Unit",
    "offer_col_line_total":         "Line Total",
    "offer_col_line_profit":        "Line Profit",
    "offer_select_first":           "Select an offer first",
    "offer_details_placeholder":    "Select an offer to view details",
    "offer_saved_list":             "─── Saved Offers ───",
    "offer_products_tab":           "🎁  Offers",
    "offer_categories_tab":         "🏷️  Offer Categories",
    "pricing_prices_tab":           "💰  Prices",
    "pricing_categories_tab":       "🏷️  Categories",

    "offer_name_required":          "Enter offer name first",
    "offer_product_required":       "Add at least one product",
    "offer_cancel_btn":             "✖  Cancel",
    "offer_header_search":          "Search",
    "offer_header_total_col":       "Total",
    "offer_item_final_icon":        "🏭 {name}",
    "offer_item_semi_icon":         "🔧 {name}",
    "offer_no_price_tooltip":       "This product has no price in pricing",
    "offer_cost_lbl":               "Cost:",
    "offer_price_lbl":              "Price:",
    "offer_times_sym":              "×",
    "offer_equals_sym":             "=",
    "offer_min_one_product":        "Add at least one product",
    "offer_name_placeholder":       "e.g. Ramadan offer, Holiday bundle...",
    "offer_notes_placeholder":      "Optional...",
    "offer_name_field":             "Offer Name:",
    "offer_discount_field":         "Discount:",
    "offer_category_field":         "Category:",
    "offer_notes_field":            "Notes:",
    "offer_row_search_hdr":         "Search",
    "offer_row_product_hdr":        "Product",
    "offer_row_cost_hdr":           "Cost/U",
    "offer_row_price_hdr":          "Price/U",
    "offer_row_qty_hdr":            "Qty",
    "offer_row_total_hdr":          "Total",
    "offer_row_cost_label":         "Cost:",
    "offer_row_price_label":        "Price:",
    "offer_row_multiply_sign":      "×",
    "offer_row_equals_sign":        "=",
    "offer_row_unit_cost_tooltip":  "Production cost / unit",
    "offer_row_unit_price_tooltip": "Pricing price / unit",
    "offer_row_no_pricing_tooltip": "This product has no price in pricing",
    "offer_row_line_total_tooltip": "Line total price before discount",
    "offer_details_notes_prefix":   "📝 {notes}",
    "offer_details_title":          "📋  {name}  —  {discount:.1f}% discount  │  {created_at}{category}",
    "offer_details_category_part":  "  │  🏷 {category}",
    "offer_col_count":              "Products",
    "offer_col_discount_pct":       "Disc. %",
    "offer_col_total_listed":       "Total Price",
    "offer_col_sell_price":         "Sell Price",
    "offer_col_cost":               "Cost",
    "offer_col_profit":             "Profit",
    "offer_col_date":               "Date",
    "pricing_select_product_table": "Select a product from the table first",
    "pricing_edit_selected_btn":    "✏️  Edit Selected",
    "pricing_save_price_btn":       "💾  Save Price",
    "pricing_delete_price_btn":     "🗑️  Delete Price",
    "pricing_cost_suffix":          "{cost:.2f}  EGP (cost)",

    # ══════════════════════════════════════════════════════════════════
    # Companies & Shared Items
    # ══════════════════════════════════════════════════════════════════
    "companies_registered":         "Registered Companies",
    "company_add_btn":              "➕  Add Company",
    "company_name_label":           "Company Name *",
    "company_short_name_label":     "Short Name",
    "company_color_label":          "Brand Color",
    "company_notes_label":          "Notes",
    "company_choose_color":         "Choose Color",
    "company_new_title":            "✨  New Company",
    "company_edit_title":           "✏️  Edit: {name}",
    "company_status_active":        "✅ Active",
    "company_status_paused":        "⏸ Paused",
    "company_updated_msg":          "Company «{name}» updated",
    "company_created_msg":          "Company «{name}» created successfully.\nDatabases have been initialized.",
    "company_delete_confirm":       "Delete company «{name}»?\n\nNote: Database files will remain on disk.",
    "shared_item_hint":             "💡  Shared items are stored centrally — any change is reflected across all linked companies.",
    "shared_publish_hint":          "💡  Shared item is stored centrally and appears in all selected companies.\n    Any changes will be reflected immediately.",
    "shared_item_header":           "🔗  Manage Shared Items Between Companies",
    "shared_add_btn":               "➕  Add Shared Item",
    "shared_edit_btn":              "✏️  Edit Selected",
    "shared_delete_btn":            "🗑️  Delete Selected",
    "shared_refresh_btn":           "🔄  Refresh",
    "shared_close_btn":             "✖  Close",
    "shared_link_btn":              "➕  Link Company",
    "shared_unlink_btn":            "✖  Unlink",
    "shared_save_btn":              "💾  Save Changes",
    "shared_publish_btn":           "📤  Publish Item",
    "shared_name_required":         "Enter item name",
    "shared_updated_msg":           "✅ Changes saved — reflected immediately across all linked companies.",
    "shared_published_msg":         "✅ «{name}» published as shared and linked to selected companies.",
    "shared_linked_msg":            "✅ Selected companies linked to «{name}»",
    "shared_already_linked":        "This company is already linked",
    "shared_not_linked":            "This company is not linked",
    "shared_unlink_confirm":        "Unlink this company from the shared item?",
    "shared_delete_with_companies": "This item is linked to {count} company(ies). Deleting it will remove all links. Continue?",
    "shared_delete_simple":         "Delete this shared item?",
    "shared_deleted_msg":           "✅ Shared item deleted",
    "shared_companies_section":     "Companies Sharing This Item",
    "shared_item_data_section":     "Item Data",
    "shared_companies_share":       "Share with Companies",
    "shared_select_all_btn":        "✅ All",
    "shared_select_none_btn":       "☐ None",
    "shared_quick_select":          "Quick Select:",
    "link_item_title":              "🔗  Select Item to Link",
    "link_item_prompt":             "Select the shared item you want to link to your company:",
    "link_item_btn":                "✅  Link",
    "no_company_welcome":           "Welcome to the ERP System",
    "no_company_subtitle":          "Select a company from the list above to start\nor create a new company",
    "no_company_add_btn":           "➕  Create New Company",
    "company_name_placeholder":     "e.g. Al-Nour Printing Co.",
    "company_short_placeholder":    "e.g. Al-Nour",
    "raw_price_lbl":                "Total Price (EGP)",
    "raw_total_qty_lbl":            "Total Quantity",
    "machine_rate_hour_lbl":        "Rate / Hour (EGP)",
    "machine_rate_unit_lbl":        "Rate / Unit (EGP)",
    "labor_time_lbl":               "Time (minutes)",
    "raw_unit_preview_lbl":         "Unit Price",
    "machine_name_col":             "Machine",
    "shared_type_raw":              "Raw Material",
    "shared_type_machine":          "Machine",
    "shared_type_labor_op":         "Labor Operation",
    "shared_type_machine_op":       "Machine Operation",
    "shared_companies_col":         "Linked Companies",
    "shared_last_update_col":       "Last Updated",
    "shared_main_data_col":         "Main Data",
    "shared_publish_title":         "📤  Publish Item as Shared",
    "shared_name_colon":            "Name:",
    "shared_exists_title":          "Item Exists",
    "shared_exists_msg":            "A shared item named «{name}» already exists.\nDo you want to use it instead of creating a new copy?",
    "without_value":                "─ None",
    "dash":                         "—",
    "companies_manage_title":       "🏢  Manage Companies",
    "company_col_name":             "Name",
    "company_col_short":            "Short Name",
    "company_col_status":           "Status",
    "company_col_actions":          "Actions",
    "company_tooltip_edit":         "Edit",
    "company_tooltip_toggle":       "Pause / Activate",
    "company_tooltip_delete":       "Delete",
    "company_pick_color_title":     "Choose Company Color",
    "company_name_required":        "Company name is required",
    "shared_item_not_found":        "⚠️  Item not found",
    "no_companies_available":       "— No Companies —",
    "link_item_from":               "—  From: {company}",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Dimension Sets Tab (orchestrator)
    # ══════════════════════════════════════════════════════════════════
    "dimension_sets_tab_values":    "📏  Enter Sizes",
    "dimension_sets_tab_groups":    "📋  Groups",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Source Picker
    # ══════════════════════════════════════════════════════════════════
    "dim_src_picker_title":         "Select Auto-Calculation Source",
    "dim_src_picker_header":        "Select Source Value Set",
    "dim_src_picker_from_group":    "From group",
    "dim_src_picker_field":         "Field",
    "dim_src_picker_hint":          "Select the value set to calculate this field from",
    "dim_src_picker_no_values":     "No saved values in this group",
    "dim_src_picker_apply":         "✓  Apply Calculation",
    "dim_src_picker_no_value_short": "No value",
    "dim_src_preview_fmt":          "✓  {name}:  {val}  {sign}  =  {result}  {unit}",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Dimension Set Categories
    # ══════════════════════════════════════════════════════════════════
    "dim_cat_panel_title":          "📁  Design Categories",
    "dim_cat_col_name":             "Category",
    "dim_cat_col_count":            "Group Count",
    "dim_cat_new_mode":             "─── New Category ───",
    "dim_cat_edit_mode":            "─── Edit: {name} ───",
    "dim_cat_no_parent":            "— No Parent (Top Level) —",
    "dim_cat_pick_color":           "Pick Color",
    "dim_cat_pick_color_title":     "Pick Category Color",
    "dim_cat_has_children_warn":    "⚠️ Contains {count} sub-categories — they will be deleted.",
    "dim_cat_has_sets_warn":        "⚠️ {count} dimension sets will lose their category.",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Dimension Sets Panel
    # ══════════════════════════════════════════════════════════════════
    "dim_sets_panel_title":         "📐  Dimension Sets",
    "dim_sets_search_placeholder":  "🔍 Search by group name...",
    "dim_sets_all_categories":      "— All Categories —",
    "dim_sets_col_id":              "ID",
    "dim_sets_col_name":            "Set Name",
    "dim_sets_col_category":        "Category",
    "dim_sets_col_unit":            "Unit",
    "dim_sets_col_fields":          "Fields Count",
    "dim_sets_form_title":          "Set Data",
    "dim_sets_new_mode":            "─── New Set ───",
    "dim_sets_edit_mode":           "─── Edit: {name} ───",
    "dim_sets_name_placeholder":    "Example: Dress sizes, Pants sizes...",
    "dim_sets_default_unit_label":  "Default Unit",
    "dim_sets_add_btn":             "➕  Add Set",
    "dim_sets_fields_header":       "📋  Selected Set Fields",
    "dim_sets_linked_designs_warn": "Set «{name}» linked to {count} designs.\nRemove the link from designs first.",
    "dim_sets_has_fields_warn":     "⚠️ Contains {count} fields — all will be deleted.",
    "dim_sets_delete_blocked_title": "Cannot Delete",
    "dim_sets_delete_confirm_title": "Confirm Delete",
    "dim_sets_delete_confirm_msg":   "Delete set «{name}»?",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Instance Popup
    # ══════════════════════════════════════════════════════════════════
    "dim_inst_dlg_new_title":       "Add New Value Set",
    "dim_inst_dlg_edit_title":      "Edit Value Set",
    "dim_inst_hdr_new":             "➕  Add New Value Set",
    "dim_inst_hdr_edit":            "✏️  Edit Values",
    "dim_inst_name_label":          "Name:",
    "dim_inst_name_placeholder":    "Example: A4, Size L, First Model...",
    "dim_inst_values_label":        "Values:",
    "dim_inst_no_numeric_fields":   "This set has no numeric fields.",
    "dim_inst_calc_all_btn":        "⟳  Calculate All Automatically",
    "dim_inst_auto_tooltip":        "Auto-calculate from source",
    "dim_inst_no_source_value":     "No source field value yet.\nEnter the source value in this set first.",
    "dim_inst_no_cross_value":      "No source field value in the selected group.\nEnter the value in the source value set first.",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Fields Panel & Field Dialog
    # ══════════════════════════════════════════════════════════════════
    "dim_field_panel_title":            "Set Fields",
    "dim_field_col_order":              "Order",
    "dim_field_col_name_en":            "Name",
    "dim_field_col_label":              "Label",
    "dim_field_col_unit":               "Unit",
    "dim_field_col_type":               "Type",
    "dim_field_col_required":           "Required",
    "dim_field_col_depends":            "Depends On",
    "dim_field_type_number":            "Number",
    "dim_field_type_text":              "Text",
    "dim_field_add_btn":                "➕  Add Field",
    "dim_field_select_first":           "Select a field first",
    "dim_field_move_up":                "▲",
    "dim_field_move_down":              "▼",
    "dim_field_dlg_new_title":          "Add New Field",
    "dim_field_dlg_edit_title":         "Edit Field",
    "dim_field_name_en_label":          "Name (English)",
    "dim_field_name_en_placeholder":    "Example: length, width ...",
    "dim_field_label_ar_label":         "Label (Arabic)",
    "dim_field_label_ar_placeholder":   "Example: Length, Width ...",
    "dim_field_required_check":         "Required Field",
    "dim_field_dep_group_title":        "Depends on field from dimension set (optional)",
    "dim_field_source_set_label":       "Source Set",
    "dim_field_source_field_label":     "Source Field",
    "dim_field_offset_label":           "Add / Subtract",
    "dim_field_preview_label":          "Preview",
    "dim_field_same_set_prefix":        "← Same Set: {name}",
    "dim_field_select_source_set":      "— Select Dimension Set —",
    "dim_field_no_numeric_fields":      "— No numeric fields —",
    "dim_field_dep_hint":               "Value = source field value + offset (negative to subtract)",
    "dim_field_preview_no_value":       "No saved value yet in the source set",
    "dim_field_name_required":          "Enter name and label",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Sets List Panel
    # ══════════════════════════════════════════════════════════════════
    "dim_sets_list_title":              "📐  Dimension Sets",
    "dim_sets_list_search":             "🔍  Search...",
    "dim_sets_list_all_cats":           "All Categories",
    "dim_sets_list_count_all":          "{count} sets",
    "dim_sets_list_count_filtered":     "{shown} of {total} sets",
    "dim_sets_card_hint":               "💡 To add or edit sets and categories — go to the «Groups» tab",
    "dim_sets_card_field_suffix":       "{count} fields",
    "dim_sets_badge_values":            "{count} values",
    "dim_sets_empty_select_title":      "Select a dimension set from the list",
    "dim_sets_empty_select_hint":       "Click on any group from the left list",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Instances Table
    # ══════════════════════════════════════════════════════════════════
    "dim_unnamed_set_fallback":         "Set #{id}",
    "dim_inst_table_placeholder":       "Select a dimension set from the list",
    "dim_inst_table_status":            "{count} value sets  ·  Double-click to edit",
    "dim_inst_add_btn":                 "➕  Add Value",
    "dim_inst_edit_btn":                "✏️  Edit",
    "dim_inst_copy_btn":                "📋  Copy",
    "dim_inst_delete_confirm":          "Delete «{name}» and all its values?",
    "dim_inst_copy_title":              "Copy Value Set",
    "dim_inst_copy_label":              "New copy name:",
    "dim_inst_copy_default":            "{name} (copy)",
    "dim_inst_col_name":                "Name",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Size Dialog
    # ══════════════════════════════════════════════════════════════════
    "design_size_dlg_new_title":        "Add New Size",
    "design_size_dlg_edit_title":       "Edit Size",
    "design_size_set_label":            "Dimension Set",
    "design_size_instance_label":       "Size",
    "design_size_width_label":          "Width Field",
    "design_size_height_label":         "Height Field",
    "design_size_dpi_label":            "DPI Field",
    "design_size_canvas_label":         "Canvas Size",
    "design_size_gimp_path_label":      "GIMP File Path",
    "design_size_gimp_browse_tooltip":  "Select existing .xcf file",
    "design_size_select_set":           "─ Select Dimension Set ─",
    "design_size_select_instance":      "─ Select a Size ─",
    "design_size_select_width":         "─ Select Width Field ─",
    "design_size_select_height":        "─ Select Height Field ─",
    "design_size_select_dpi":           "─ Optional: DPI Field ─",
    "design_size_canvas_no_dpi":        "{w} × {h} {unit}  (select DPI field to calculate px)",
    "design_size_canvas_with_dpi":      "{w} × {h} {unit}  →  {w_px} × {h_px} px  @  {dpi} DPI",
    "design_size_canvas_incomplete":    "⚠️  Incomplete values in this size",
    "design_size_canvas_dash":          "─",
    "design_size_gimp_placeholder":     "Path to .xcf file — leave empty to create new",
    "design_size_choose_set":           "Select dimension set",
    "design_size_choose_instance":      "Select size",
    "design_size_already_used":         "This size is already added to this design",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Size Card
    # ══════════════════════════════════════════════════════════════════
    "design_size_card_fallback_name":       "Size #{id}",
    "design_size_card_open_gimp_btn":       "Open in GIMP",
    "design_size_card_create_gimp_btn":     "Create in GIMP",
    "design_size_card_link_file_btn":       "Link File",
    "design_size_card_file_exists":         "File exists",
    "design_size_card_file_missing":        "File not found",
    "design_size_card_file_none":           "No file",
    "design_size_card_file_not_found_msg":  "File:\n{path}\n\nUse «Link File» to update the path.",
    "design_size_card_create_canvas_title": "Create Canvas",
    "design_size_card_create_canvas_msg":   "Dimensions: {w} × {h} {unit}\nPixels: {w_px} × {h_px} px  @  {dpi} DPI\nFile: {path}",
    "design_size_card_save_gimp_title":     "Choose GIMP File Save Location",
    "design_size_card_link_file_title":     "Choose Existing GIMP File",
    "design_size_card_gimp_filter":         "GIMP Files (*.xcf);;All Files (*)",
    "design_size_card_dims_unknown":        "Dimensions not set",
    "design_size_card_dims_no_dpi":         "{w} × {h} {unit}",
    "design_size_card_dims_with_dpi":       "{w} × {h} {unit}  →  {w_px} × {h_px} px",
    "design_size_card_missing_gimp":        "GIMP not found.\nSet its path from ⚙️ Settings.",
    "design_size_card_pillow_missing":      "Pillow required:\n\npip install Pillow",
    "design_size_card_open_failed":         "Failed to open GIMP:\n{error}",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Designs Table & Card
    # ══════════════════════════════════════════════════════════════════
    "design_table_new_btn":                 "New Design  +",
    "design_table_set_filter_label":        "Set:",
    "design_table_all_sets":                "All Sets",
    "design_table_reset_filters_btn":       "↺  Clear",
    "design_table_count":                   "{count} designs",
    "design_table_empty_no_designs":        "No Designs",
    "design_table_empty_start":             "Press «New Design» to start",
    "design_table_empty_no_results":        "No results",
    "design_table_empty_change_criteria":   "Try changing search criteria",
    "design_table_search_placeholder":      "Search by name...",
    "design_card_size_badge_tooltip":       "{count} sizes",
    "design_card_status_all_files":         "✓  {count}/{total} files",
    "design_card_status_partial_files":     "⚡  {count}/{total} files",
    "design_card_status_no_files":          "○  {count} sizes — no files",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Design Detail Panel
    # ══════════════════════════════════════════════════════════════════
    "design_detail_new_badge":          "New",
    "design_detail_saved_badge":        "Saved",
    "design_detail_new_title":          "New Design",
    "design_detail_new_btn":            "New",
    "design_detail_save_btn":           "Save Design",
    "design_detail_name_label":         "Name",
    "design_detail_name_placeholder":   "Design name...",
    "design_detail_category_label":     "Category",
    "design_detail_notes_label":        "Notes",
    "design_detail_notes_placeholder":  "Optional...",
    "design_detail_sizes_section":      "Sizes",
    "design_detail_add_size_btn":       "+ Add Size",
    "design_detail_save_first_warn":    "Save the design first before adding sizes",
    "design_detail_no_sizes_title":     "No sizes yet",
    "design_detail_no_sizes_hint":      "Press «+ Add Size» to add the first size",
    "design_detail_delete_size_confirm": "Delete this size from the design?",
    "design_detail_name_required":      "Enter design name",
    "design_detail_no_category":        "— No Category —",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Design Categories Panel
    # ══════════════════════════════════════════════════════════════════
    "design_cats_panel_title":          "Categories",
    "design_cats_add_tooltip":          "New Category",
    "design_cats_all":                  "All Designs",
    "design_cats_search_placeholder":   "Search categories...",
    "design_cats_edit_btn":             "Edit",
    "design_cats_delete_btn":           "Delete",
    "design_cats_new_form_title":       "New Category",
    "design_cats_edit_form_title":      "Edit: {name}",
    "design_cats_name_placeholder":     "Category name...",
    "design_cats_parent_label":         "Parent:",
    "design_cats_color_label":          "Color:",
    "design_cats_pick_color_btn":       "Pick Color",
    "design_cats_save_btn":             "Save",
    "design_cats_cancel_btn":           "Cancel",
    "design_cats_no_parent":            "— No Parent —",
    "design_cats_has_children_warn":    "⚠️ {count} sub-categories will be deleted.",
    "design_cats_has_designs_warn":     "⚠️ {count} designs will lose their category.",

}
