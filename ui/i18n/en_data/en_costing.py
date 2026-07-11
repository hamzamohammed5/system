"""
ui/i18n/en_data/costing.py
=====================
Costing section strings (BOM, products, raw materials, labor, machines, scenarios)
جزء من تقسيم ui/i18n/en.py — راجع ui/i18n/en/__init__.py.
"""

EN_STRINGS_COSTING: dict[str, str] = {
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
    "component_type_raw":        "🧱 Raw Material",
    "component_type_semi":       "🔧 Semi-Finished",
    "component_type_labor_op":   "👷 Labor Operation",
    "component_type_machine_op": "⚙️ Machine Operation",

    # ══════════════════════════════════════════════
    # ComponentRow (BOM row)
    # ══════════════════════════════════════════════
    "component_row_orphan_display":   "⚠️  {name_part}deleted  (ID: {item_id})",
    "component_row_orphan_tooltip":   "⚠️ This component ({type_}{name_part} ID:{item_id}) was deleted from the database.\nChoose a replacement from the list or delete this row.",
    "component_row_orphan_name_part": " «{name}»",
    "component_row_cost_tooltip":     "Unit cost: {unit_cost}\nTotal price: {price}{total_qty_line}",
    "component_row_total_qty_line":   "\nTotal quantity: {total_qty}",
    "op_row_fallback_label":          "Row {id}",
    "op_row_cost_suffix":             "= {cost} EGP/pc",
    "op_row_combo_approx_cost":       "  ≈ {cost} EGP",
    "op_row_combo_fraction":          "({value} ÷ {count})",
    "variant_combo_tooltip":          "Production unit — Unit cost = Raw material price ÷ piece count",
    "waste_spin_tooltip":             "Waste %\nExample: 10% → Actual quantity = Quantity × 1.10",
    "total_qty_placeholder":          "Total",
    "total_qty_tooltip":              "Total quantity of the raw material.",
    "divide_symbol":                  "÷",
    "sub_row_label":                  "↳ Operation row:",
    "variant_combo_none":             "─ No variant ─",
    "variant_combo_item_priced":      "📐 {name}  ({pieces} pc → {unit_cost} EGP/pc)",
    "variant_combo_item_plain":       "📐 {name}  ({pieces} pc)",
    "variant_cost_suffix":            "= {cost} EGP",
    "waste_icon":                     "⚠️",
    "component_row_remove_btn":       "❌",
    "waste_spin_suffix":              " %",

    # ══════════════════════════════════════════════
    # Products
    # ══════════════════════════════════════════════
    "new_product":              "New Product",
    "product_name_placeholder": "Product name...",
    "saved_products":           "Saved Products",
    "products_table_title":     "─── Saved Products ───",
    "no_products":              "No products found",
    "enter_product_name":       "Please enter a product name first",
    "add_one_component":        "Please add at least one component",
    "product_name":             "Product Name",
    "add_component":            "Component",
    "edit_selected_btn":        "✏️ Edit Selected",
    "delete_selected_btn":      "🗑️ Delete Selected",
    "editing_product_label":          "Editing: {name}",
    "editing_product_orphans_label":  "Editing: {name}  {count} missing component(s)",
    "orphans_deleted_title":          "Done",
    "orphans_deleted_with_product_title": "Done — Product Deleted",
    "orphans_deleted_msg":            "✅ Deleted {count} missing component(s):\n{names}",
    "orphans_deleted_product_removed_msg": "✅ Deleted {count} missing component(s):\n{names}\n\nSince «{product_name}» no longer has any components,\nit was deleted automatically.",
    'component_row_no_items_placeholder': 'No {type_label} registered',

    # ══════════════════════════════════════════════
    # Components / BOM
    # ══════════════════════════════════════════════
    "element":            "Element",
    "row_or_variant":     "Row / Variant",
    "qty":                "Qty",
    "waste_pct_col":      "Waste %",
    "effective_qty":      "Effective Qty",
    "component_scenario": "Component / Scenario",
    "total_cost":         "Total Cost",

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
    "bom_delete_from_scenario_msg":    "{node_name} from scenario «{sc_name}»",
    "delete_sub_components_from_semi": "Delete sub-components from the semi-finished product itself",

    # ── BOM Tree — header & button icons ─────────────
    "bom_tree_header_icon":            "🔩 ",
    "bom_tree_expand_icon":            "⊞ ",
    "bom_tree_collapse_icon":          "⊟ ",
    "bom_tree_del_icon":               "🗑 ",
    "bom_tree_warning_icon":           "⚠️",
    "bom_tree_star_icon":              "⭐",
    "bom_tree_multiply_sign":          "×",
    "preview_eq_dash":                 "= ─",

    # ── BOM Tree — Scenario node ──────────────────
    "bom_scenario_default_suffix":     "  (Default)",
    "bom_scenario_star_icon":          "⭐ ",
    "bom_scenario_normal_icon":        "📋 ",

    # ── _BomScenariosPanel icons ──────────────────
    "scenarios_panel_target_icon":     "🎯",
    "scenarios_panel_star_badge":      "⭐ ",
    "scenarios_panel_btn_star_icon":   "⭐ ",
    "scenarios_panel_btn_edit_icon":   "✏️ ",
    "scenarios_panel_btn_clone_icon":  "📋 ",
    "scenarios_panel_btn_add_icon":    "➕ ",
    "scenarios_panel_btn_del_icon":    "🗑",

    # ── BOM Tree — Component node (tooltips) ──────
    "bom_tooltip_qty_entered":         "Entered quantity: {qty}",
    "bom_tooltip_waste":               "Waste {pct} %\nEffective qty = {qty} × (1 + {pct}/100) = {eff_qty}",
    "bom_tooltip_effective_qty":       "Effective qty = {eff_qty}",
    "bom_tooltip_unit_cost":           "Unit cost: {cost}",
    "bom_tooltip_total_cost":          "Total cost = {unit_cost} × {eff_qty} = {total_cost}",
    "bom_tooltip_machine_op_row_cost": "Selected row cost (ID:{row_id}): {cost}",
    "bom_qty_no_value":                "—",
    "bom_type_label_raw":              "🧱 {label}",
    "bom_type_label_semi":             "🔧 {label}",
    "bom_type_label_labor_op":         "👷 {label}",
    "bom_type_label_machine_op":       "⚙️ {label}",

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
    "default_scenario_initial_name": "Scenario 1",
    "new_name":                    "New Name",
    "copy_of":                     "Copy of",
    "cannot_delete_last_scenario": "Cannot delete the only scenario",
    "delete_scenario_confirm":     "Delete scenario",
    "delete_scenario_confirm_msg": "Delete scenario «{name}»?",
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
    "scenario_comparison_icon":   "📊",
    "scenario_comparison_higher_icon": "⬆",
    "scenario_comparison_lower_icon":  "⬇",
    "positive_sign":              "+",
    "percent_sign":               "%",
    "scenario_combo_placeholder": "─ {label} ─",

    # ══════════════════════════════════════════════
    # Bulk Replace
    # ══════════════════════════════════════════════
    "operation_required":     "Operation Required",
    "operation_section_title": "⚙️  Operation Required",
    "replace_element":        "Replace Element",
    "replace_element_btn":    "🔀  Replace Element",
    "edit_qty_only":          "Edit Qty Only",
    "edit_qty_only_btn":      "🔢  Edit Qty Only",
    "both_operations":        "Both Operations",
    "both_operations_btn":    "✅  Both Operations",
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
    "bulk_replace_window_title":     "🔄  Bulk Replace / Edit",
    "bulk_replace_header_title":     "Bulk Replace  —  {name}",
    "select_at_least_one_product":   "Select at least one product",
    "select_replacement_first":      "Select the replacement element first\nor choose “Edit quantity only” if you don’t want to replace it.",
    "bulk_replace_desc_line":        "•  Replace  “{old}”  with  “{new}”",
    "bulk_set_qty_desc_line":        "•  Set quantity = {qty}",
    "bulk_keep_qty_desc_line":       "•  Keep the custom quantity for each product",
    "bulk_apply_confirm_msg":        "The following will be applied to {count} product(s):\n\n{ops}\n\nDo you want to continue?",
    "confirm_apply_title":           "Confirm Apply",
    "bulk_completed_with_errors_title": "Completed with Errors",
    "bulk_completed_success_msg":    "✅ {count} product(s) updated successfully",
    "bulk_completed_with_errors_msg":   "✅ {updated} product(s) updated successfully\n\n⚠️ {failed} product(s) failed:\n{errors}",

    # ══════════════════════════════════════════════
    # Machine Op Rows
    # ══════════════════════════════════════════════
    "op_rows_editor":              "Operation Rows",
    "op_rows_editor_icon":         "📋  ",
    "op_rows_time_icon":           "⏱",
    "op_rows_unit_icon":           "📦",
    "op_rows_add_icon":            "➕ ",
    "op_rows_save_icon":           "💾 ",
    "op_rows_edit_icon":           "✏️ ",
    "op_rows_del_icon":            "🗑️ ",
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
    "raw_variants_icon":           "📐  ",
    "raw_variants_info_icon":      "💡 ",
    "raw_variants_add_icon":       "➕ ",
    "raw_variants_save_icon":      "💾 ",
    "raw_variants_edit_icon":      "✏️ ",
    "raw_variants_del_icon":       "🗑️ ",
    "raw_variants_equals_sign":    "= ",
    "variant_description_line1":   "Each variant defines how many pieces come from one unit of raw material",
    "variant_unit_cost_formula":   "Unit Cost = Total Price ÷ Pieces Count",
    "variant_name_placeholder":    "Variant name...",
    "pieces_count":                "Pieces Count",
    "pieces_tooltip_line1":        "Number of pieces produced from one raw material unit",
    "add_variant":                 "Add Variant",
    "enter_variant_name":          "Please enter a variant name",
    "select_variant_first":        "Please select a variant first",
    "delete_variant_confirm":      "Delete variant",
    "delete_variant_confirm_msg":  "Delete variant «{name}»?",
    "currency_per_piece_short":    "EGP/piece",

    # ══════════════════════════════════════════════
    # Raw Materials
    # ══════════════════════════════════════════════
    "raw_materials": "Raw Materials",
    "no_raws":       "No raw materials found",
    "saved_raws":    "Saved Raw Materials",
    "raw_empty_icon":        "🧱",
    "raw_table_list_title":  "─── Saved Raw Materials ───",
    "raw_select_first":              "Select a raw material from the table first",
    "raw_bulk_replace_btn":          "🔄 Bulk Replace",
    "raw_edit_shared_btn":           "🔗 Edit Shared",
    "raw_publish_btn":               "📤 Publish as Shared",
    "shared_bulk_replace_btn":       "🔄 Bulk Replace",
    "shared_edit_shared_btn":        "🔗 Edit Shared",
    "shared_publish_as_shared_btn":  "📤 Publish as Shared",
    "raw_bulk_replace_not_available":"Bulk replace is not available for shared items.",
    "shared_item_title":             "Shared Item",
    "raw_shared_edit_notice":        "This is an incoming shared raw material — use the «🔗 Edit Shared» button to edit it.",
    "raw_shared_delete_blocked":     "A shared raw material cannot be deleted from here.\nUse the «Shared Items» window to delete it or unlink it.",
    "raw_col_id":                    "ID",
    "raw_col_name":                  "Name",
    "raw_col_category":              "Category",
    "raw_col_total_price":           "Total Price",
    "raw_col_qty":                   "Quantity",
    "raw_col_unit_price":            "Unit Price",
    'raw_col_actions':   'Actions',      # en: ''
    'btn_edit_short':    'Edit',        # en: ''
    'btn_delete_short':  'Delete',          # en: ''
    'btn_edit':          'Edit Material', # tooltip
    'btn_delete':        'Delete Material',   # tooltip
    
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
    # Costing Section & Tabs
    # ══════════════════════════════════════════════
    "costing_section":    "Cost Management",
    "final_product":      "Final Product",
    "labor":              "Labor",
    "machine":            "Machine",
    "machines":           "Machines",
    "machines_icon":      "🖥️",
    "machine_operations": "Machine Operations",
    "machine_operations_icon": "⚙️",
    "labor_settings":     "Labor Settings",
    "labor_settings_icon": "⚙️",
    "labor_operations":   "Labor Operations",
    "labor_operations_icon": "📋",

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
    "currency_per_hour_short":    "/hr",
    "currency_per_unit_short":    "/unit",
    "machines_table_title":       "─── Saved Machines ───",

    # ══════════════════════════════════════════════
    # Machine Op Form — New Keys
    # ══════════════════════════════════════════════
    "machine_op_form_title":       "Machine Operation Data",
    "machine_op_name_placeholder": "e.g. Stitch, Press...",
    "add_machine_op_new":          "Add New Machine Operation",
    "add_op":                      "Add Operation",
    "op_name":                     "Operation Name",
    "machine_label":               "Machine",
    "select_machine_first":        "Select a machine first",
    "add_op_first_hint":           "Add the operation first to see rows",
    "mode_time_label":             "⏱ By Time",
    "mode_unit_label":             "📦 By Unit",
    "calc_mode_label":             "Calculation Mode",
    "machine_mode_tooltip":        "How the machine cost is calculated: by time or by unit",
    "total_cost_label":            "Total Cost",
    "op_added_success":            "Operation «{name}» added\nAdd rows now then click Save",
    "editing_rows_prefix":         "Editing Rows",
    "enter_op_name":               "Enter operation name",
    "machine_op_table_title":      "─── Saved Machine Operations ───",
    "mode_col":                    "Mode",
    "value_col":                   "Value",
    "cost_col":                    "Cost",
    "time_mode_short":             "⏱ Time",
    "unit_mode_short":             "📦 Unit",

    # ══════════════════════════════════════════════
    # Labor Op Form — New Keys
    # ══════════════════════════════════════════════
    "labor_op_form_title":        "Operation Data",
    "time_label":                 "Time",
    "cost_label":                 "Cost",
    "minutes_label":              "minutes",
    "labor_op_name_placeholder":  "e.g. Sewing, Packaging...",
    "labor_op_table_title":       "─── Saved Labor Operations ───",
    "cost_per_unit_col":          "Cost / Unit",

    # ══════════════════════════════════════════════
    # Raw Form — New Keys
    # ══════════════════════════════════════════════
    "raw_form_title":             "Raw Material Data",
    "raw_add_btn":                "➕  Add Raw Material",
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

}
