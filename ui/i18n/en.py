"""
ui/i18n/en.py
==============
القاموس الإنجليزي الكامل للتطبيق.

يُستخدم من I18nManager في ui/i18n.py كمصدر للترجمة الإنجليزية.
يُصدّر EN_STRINGS للاستخدام المستقل أو للاستيراد من أدوات الترجمة.
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

    # Panel placeholders
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

    # ══════════════════════════════════════════════
    # Field Validation Messages
    # ══════════════════════════════════════════════
    "enter_field":          "Enter {label}",
    "select_field":         "Select {label}",
    "field_positive":       "{label} must be greater than zero",
    "field_positive_enter": "Enter {label} greater than zero",

    # ══════════════════════════════════════════════
    # Fields
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

    # ══════════════════════════════════════════════
    # Inventory
    # ══════════════════════════════════════════════
    "inventory":            "Inventory",
    "stock_in":             "In",
    "stock_out":            "Out",
    "current_stock":        "Current Stock",

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
    # BOM
    # ══════════════════════════════════════════════
    "components":           "Components",
    "raw_material":         "Raw Material",
    "semi_product":         "Semi-Product",
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
    "category_data":         "Category Data",
    "category_name":         "Name",
    "category_parent":       "Parent",
    "category_color":        "Color",
    "category_add":          "New Category",
    "category_new":          "Children",
    "category_edit":         "Edit",
    "category_delete":       "Delete",
    "category_select_first": "Select a category first",
    "category_name_required":"Enter category name",

    # ══════════════════════════════════════════════
    # Operations
    # ══════════════════════════════════════════════
    "operation_add":        "Add",
    "operation_edit":       "Edit",
    "operation_delete":     "Delete",
    "operation_save":       "Save",
    "operation_cancel":     "Cancel",

    # ══════════════════════════════════════════════
    # Designs
    # ══════════════════════════════════════════════
    "designs":              "Designs",
    "design_add":           "Add Design",
    "design_categories":    "Design Categories",
    "dimension_sets":       "Dimension Sets",

    # ══════════════════════════════════════════════
    # Orders
    # ══════════════════════════════════════════════
    "orders":               "Orders",
    "order_add":            "Add Order",
    "customers":            "Customers",
    "customer_add":         "Add Customer",
    "order_status":         "Order Status",
    "order_date":           "Order Date",

    # ══════════════════════════════════════════════
    # Pricing
    # ══════════════════════════════════════════════
    "pricing":              "Pricing",
    "offers":               "Offers",
    "offer_add":            "Add Offer",

    # ══════════════════════════════════════════════
    # Custom Delete Messages
    # ══════════════════════════════════════════════
    "delete_has_children":  "Cannot delete — has sub-items",
    "delete_has_items":     "Cannot delete — linked to other items",

    # ══════════════════════════════════════════════
    # Shared Items
    # ══════════════════════════════════════════════
    "shared_items":         "Shared Items",
    "publish":              "Publish",
    "published":            "Published",
    "not_published":        "Not Published",
}
