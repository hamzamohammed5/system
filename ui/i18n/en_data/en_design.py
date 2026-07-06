"""
ui/i18n/en_data/design.py
====================
Design section strings (dimension sets, sizes, categories)
جزء من تقسيم ui/i18n/en.py — راجع ui/i18n/en/__init__.py.
"""

EN_STRINGS_DESIGN: dict[str, str] = {
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
    "dim_field_move_up_btn":            "⬆️",
    "dim_field_move_down_btn":          "⬇️",
    "dim_field_required_yes":           "✓",
    "dim_cat_zero_sets":                "—",
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
    "dim_sets_meta_separator":          "  ·  ",
    "dim_sets_badge_values":            "{count} values",
    "dim_sets_empty_select_title":      "Select a dimension set from the list",
    "dim_sets_empty_select_hint":       "Click on any group from the left list",
    "dim_sets_list_default_unit":       "cm",

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
    "dim_inst_dlg_new_title":           "Add New Value",
    "dim_inst_dlg_edit_title":          "Edit Value",
    "dim_inst_hdr_new":                 "➕  Add New Value",
    "dim_inst_hdr_edit":                "✏️  Edit Value",
    "dim_inst_name_label":              "Name",
    "dim_inst_name_placeholder":        "Group name...",
    "dim_inst_values_label":            "Values",
    "dim_inst_auto_tooltip":            "Auto-calculate from source set",
    "dim_inst_no_numeric_fields":       "No numeric fields in this set",
    "dim_inst_no_source_value":         "No saved value in the source set",
    "dim_inst_no_cross_value":          "No value in the selected source field",
    "dim_inst_calc_all_btn":            "⟳  Auto-Calculate All",
    "dim_inst_save_btn":                "💾  Save",
    "dim_inst_auto_icon":               "⟳",
    "dim_inst_empty_icon":              "📋",
    "dim_sets_set_icon":                "📐",
    "dim_sets_card_no_category":        "—",
    "dim_value_empty":                  "—",

    # ══════════════════════════════════════════════════════════════════
    # Design Module — Size Dialog
    # ══════════════════════════════════════════════════════════════════
    "design_size_dlg_new_title":        "Add New Size",
    "design_size_dlg_edit_title":       "Edit Size",
    "design_size_dlg_header_icon":      "📐  ",
    "design_size_gimp_browse_icon":     "📂",
    "design_size_dlg_save_btn":         "💾  Save",
    "design_size_dlg_cancel_btn":       "✖  Cancel",
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
    "design_size_card_edit_icon":           "✏",
    "design_size_card_delete_icon":         "🗑",
    "design_size_card_dpi_chip":            "{dpi} DPI",
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
    "design_card_thumb_placeholder_icon":   "🎨",
    "design_size_card_thumb_no_file_icon":  "📄",

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
    "design_cats_add_icon":             "+",
    "design_table_empty_icon":          "🎨",
    "design_detail_no_sizes_icon":      "📐",
    "design_detail_cat_arrow":          "↳ ",

}
