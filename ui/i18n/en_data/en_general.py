"""
ui/i18n/en_data/general.py
=====================
General shared strings (buttons, navigation, settings, empty states, filters, etc.)
جزء من تقسيم ui/i18n/en.py — راجع ui/i18n/en/__init__.py.
"""

EN_STRINGS_GENERAL: dict[str, str] = {
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
    "field_colon":       ":",
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
    "btn_add_op":   "➕  Add Operation",
    "btn_add_component": "+  Component",

    # ── Table shared/published row icons ──────────────────
    "table_shared_icon":      "🔗",
    "table_shared_prefix":    "🔗 ",
    "table_published_icon":   "📤",
    "table_published_prefix": "📤 ",

    # ── Catalog: shared category badge (CatalogService.SHARED_CATEGORY_KEY) ──
    "shared":                 "🔗 Shared",

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

    # ── sidebar — section labels, icons, toggle ────────────
    "nav_section_production": "Production",
    "nav_section_finance":    "Finance",
    "nav_section_work":       "Operations",
    "nav_icon_costing":       "📊",
    "nav_icon_pricing":       "💰",
    "nav_icon_accounting":    "🏦",
    "nav_icon_inventory":     "📦",
    "nav_icon_design":        "🎨",
    "nav_icon_orders":        "📋",
    "nav_icon_shared":        "🔗",
    "nav_icon_settings":      "⚙️",
    "tab_icon_raw":           "📦",
    "tab_icon_semi":          "🔧",
    "tab_icon_final":         "🏭",
    "tab_icon_labor":         "👷",
    "tab_icon_machine":       "⚙️",
    "sidebar_collapse_tip":   "Collapse Sidebar",
    "sidebar_expand_tip":     "Expand Sidebar",
    "sidebar_collapse_icon":  "◀",
    "sidebar_expand_icon":    "▶",

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

    # ── Settings — tab titles and UI ──────────────────────
    "settings_title":            "⚙️  Settings",
    "settings_tab_font":         "🔤  Font",
    "settings_tab_theme":        "🎨  Appearance",
    "settings_tab_lang":         "🌐  Language",
    "settings_tab_units":        "📏  Units",
    "settings_tab_gimp":         "🖼️  GIMP",
    "settings_btn_save":         "✅  Save",
    "settings_btn_cancel":       "✖  Cancel",
    "settings_grp_font":         "Font Size",
    "settings_font_preview":     "Preview Text — Preview 123\nArabic Text — The quick brown fox\n1234567890 — ABCDEFG abcdefg",
    "settings_font_hint":        "💡  Press Save to apply the new font size across the entire interface",
    "settings_font_sample_small": "A",
    "settings_font_sample_big":   "A",
    "settings_grp_theme":        "Choose Application Appearance",
    "settings_grp_theme_preview":"Color Preview",
    "settings_grp_lang":         "Choose Interface Language",
    "settings_lang_hint":        "💡  Language change takes effect after saving",
    "settings_grp_units":        "Available Measurement Units",
    "settings_units_hint":       "💡  Default units (shown in gray) cannot be deleted",
    "settings_unit_default_tip": "Default unit — cannot be deleted",
    "settings_btn_add_unit":     "➕  Add Unit",
    "settings_btn_del_unit":     "🗑️  Delete Selected",
    "settings_btn_reset_units":  "↺  Restore Defaults",
    "settings_grp_gimp":         "GIMP Executable Path",
    "settings_gimp_hint":        "💡  Leave empty to auto-detect from common paths",
    "settings_gimp_placeholder": r"Example: C:\Program Files\GIMP 2\bin\gimp-2.10.exe",
    "settings_btn_browse":       "📂  Browse",
    "settings_no_company_notice":"⚠️  Select an active company to view measurement units and GIMP path",
    "settings_add_unit_title":   "Add Unit",
    "settings_add_unit_prompt":  "Enter unit symbol (e.g. ft, yd, pt):",
    "settings_add_unit_label":   "Enter full label for unit «{val}» (e.g. ft — foot):",
    "settings_unit_exists":      "Unit «{val}» already exists.",
    "settings_select_unit":      "Select a unit first",
    "settings_no_del_default":   "Cannot delete default unit «{val}».",
    "settings_del_unit_title":   "Confirm Delete",
    "settings_del_unit_msg":     "Delete unit «{label}»?",
    "settings_del_unit_btn":     "Delete",
    "settings_reset_units_title":"Restore Defaults",
    "settings_reset_units_msg":  "Delete all added units and restore the default list?",
    "settings_reset_units_btn":  "Restore",
    "settings_warning_title":    "Warning",
    "settings_error_title":      "Error",
    "settings_no_company_units": "Select an active company first to add measurement units",
    "settings_no_company_del":   "Select an active company first to delete measurement units",
    "settings_no_company_reset": "Select an active company first to restore default units",
    "settings_browse_gimp":      "Select GIMP Executable",
    "settings_gimp_filter":      "GIMP (gimp*.exe);;Executable Files (*.exe);;All Files (*)",
    "settings_theme_light_name": "Light",
    "settings_theme_light_desc": "Warm white background, easy on the eyes",
    "settings_theme_dark_name":  "Dark",
    "settings_theme_dark_desc":  "Dark background for nighttime use",
    "settings_lang_ar_name":     "العربية",
    "settings_lang_ar_desc":     "Arabic interface (RTL)",
    "settings_lang_en_name":     "English",
    "settings_lang_en_desc":     "Interface in English (LTR)",

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
    "empty_icon_default":      "📭",
    "icon_question":           "❓",
    "icon_info":               "ℹ️",
    "icon_warning":            "⚠️",
    "icon_critical":           "❌",
    "icon_dialog_default":     "📋",
    "icon_reset":              "↺",
    "font_pt_suffix":          "{size} pt",
    "icon_theme_light":        "☀️",
    "icon_theme_dark":         "🌙",
    "icon_flag_ar":            "🇸🇦",
    "icon_flag_en":            "🇬🇧",
    "swatch_label_accent":     "accent",
    "swatch_label_success":    "success",
    "swatch_label_warning":    "warning",
    "swatch_label_danger":     "danger",
    "swatch_label_surface":    "surface",
    "swatch_label_text":       "text",
    "value_dash":              "—",
    "empty_placeholder":       "─",

    # ══════════════════════════════════════════════
    # Confirm
    # ══════════════════════════════════════════════
    "confirm_delete":       "Confirm Delete",
    "confirm_save":         "Confirm Save",
    "confirm_save_q":       "Confirm Save?",
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
    "detail_load_error":    "Error loading details: {error}",
    "tab_load_error":       "Error loading tab: {error}",
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
    "combo_clear_search":     "✖",
    "combo_sep_no_category":  "─── No Category ───",
    "combo_id_name_fmt":      "{id} — {name}",

    # ══════════════════════════════════════════════
    # Operations
    # ══════════════════════════════════════════════
    "operation_add":    "Add",
    "operation_edit":   "Edit",
    "operation_delete": "Delete",
    "operation_save":   "Save",
    "operation_cancel": "Cancel",

    # ══════════════════════════════════════════════
    # Custom Delete Messages
    # ══════════════════════════════════════════════
    "delete_has_children":  "Cannot delete — has sub-items",
    "delete_has_items":     "Cannot delete — linked to other items",

    # ══════════════════════════════════════════════
    # Section Tab Names
    # ══════════════════════════════════════════════

    # Costing tabs
    "raw_tab":        "Raw Materials",
    "labor_tab":      "Labor",
    "machine_tab":    "Machine Ops",
    "product_tab":    "Products",
    "categories_tab": "Categories",
    "categories_tab_icon": "🏷️",

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
    "inventory_section_tab_moves": "Moves",
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
    # Pagination
    # ══════════════════════════════════════════════
    "load_more":               "Load {count} More  ▼",
    "show_all_records":        "Show All",
    "showing_records":         "Showing {shown:,} of {total:,}",
    "showing_all_records":     "Showing all {shown:,} records",

}
