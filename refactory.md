# خطة إعادة هيكلة وحدة التصميمات — Design Module

> **ملاحظة:** هذه الخطة شاملة وجاهزة للتطبيق المباشر.  
> كل ملف مذكور مرة واحدة فقط بكل تعديلاته.

---

## المبادئ المطبقة

1. **لا Hardcoded Colors** — كل الألوان من `_C` المستورد من `ui/theme.py`
2. **لا Hardcoded Strings** — كل النصوص من `tr()` المستورد من `ui/widgets/core/i18n.py`
3. **Architecture**: `tabs/ UI → services/ → repos/ (db/)`
4. **لا Re-exports أو Wrappers** — الاستدعاءات مباشرة للـ service المناسب

---

## 1. خريطة الألوان — لا توجد ألوان جديدة

جميع الألوان المستخدمة في ملفات Design موجودة بالفعل في `_C`. الخريطة:

| الثابت القديم | القيمة | مفتاح `_C` المقابل |
|---|---|---|
| `_BLUE` / `_ACCENT` | `#1565c0` | `_C["acc_type_asset"]` — للأيقونات والـ badges فقط؛ للأزرار والـ headers: `_C["accent"]` |
| `_BLUE_LIGHT` | `#e8f0fe` | `_C["accent_light"]` |
| `_BLUE_MID` | `#bbdefb` | `_C["accent_mid"]` |
| `_GREEN` | `#2e7d32` | `_C["success"]` |
| `_GREEN_LT` | `#e8f5e9` | `_C["success_bg"]` |
| `_GREEN_BDR` | `#a5d6a7` | `_C["success_border"]` |
| `_GRAY_BG` | `#f8f9fc` | `_C["bg_surface"]` |
| `_BORDER` | `#e0e7f3` | `_C["border"]` |
| `_TEXT` | `#1a2340` | `_C["text_primary"]` |
| `_TEXT_MUTED` | `#7a869a` | `_C["text_muted"]` |
| `_RED` / `_DANGER` | `#c62828` | `_C["danger"]` |
| `_RED_LT` / `_DANGER_BG` | `#fdecea` | `_C["danger_bg"]` |
| `_RED_BDR` / `_DANGER_BDR` | `#ef9a9a` | `_C["danger_border"]` |
| `_WARN` / `_WARNING` | `#d97706` | `_C["warning"]` |
| `_WARN_LT` | `#fffbeb` | `_C["warning_bg"]` |
| `_WARN_BDR` | `#fde68a` | `_C["warning_border"]` |
| White / `bg_input` | `#ffffff` | `_C["bg_input"]` |
| `_BG_SURFACE` | `#f8f9fb` | `_C["bg_surface"]` |
| `_BORDER_MED` | `#cdd3e0` | `_C["border_med"]` |
| `_TEXT_SEC` | `#5a6680` | `_C["text_sec"]` |
| `_TEXT_MUT` | `#9ba5be` | `_C["text_muted"]` |
| `_ACCENT` | `#4f6ef7` | `_C["accent"]` |
| `_ACCENT_LT` | `#eef2ff` | `_C["accent_light"]` |
| `_ACCENT_BDR` | `#c7d2fe` | `_C["accent_mid"]` |
| `_ACCENT_DARK` | `#3d5bef` | `_C["accent_hover"]` |
| `_SUCCESS` | `#16a34a` | `_C["success"]` |
| `_SUCCESS_LT` | `#f0fdf4` | `_C["success_bg"]` |
| `_SUCCESS_BDR` | `#bbf7d0` | `_C["success_border"]` |
| `"#1E1B4B"` (thumb BG) | dark purple | `_C["bg_page"]` — أو أضف `thumb_bg` (انظر أدناه) |

### الاستثناء الوحيد — لون Thumbnail

`#1E1B4B` و `#0F0E17` مستخدمان كخلفية داكنة للـ thumbnail في بطاقات التصميم.  
**لا يوجد مقابل معبّر** في `_C`. الحل: أضف مفتاح واحد فقط في `theme_manager.py`:

```python
# في _LIGHT_THEME — أضف ضمن قسم "Design Module"
"design_thumb_bg": "#1E1B4B",

# في _DARK_THEME
"design_thumb_bg": "#0A0A1E",
```

هذا المفتاح الوحيد الذي يحتاج إضافة.

---

## 2. مفاتيح الترجمة الجديدة

### فحص المفاتيح الموجودة أولاً

المفاتيح الموجودة التي ستُستخدم مباشرة (بدلاً من إضافة جديدة):
- `cancel`, `save`, `edit`, `delete`, `add`, `notes`, `name`, `type`
- `btn_add`, `btn_save`, `btn_cancel`
- `category_name`, `category_parent`, `category_color`, `category_add`
- `category_edit`, `category_delete`, `category_select_first`, `category_name_required`
- `no_category`, `no_data`, `warning`, `error`, `info`
- `dimension_sets`, `dimension_set_name`, `source_set`, `target_field`
- `add_size`, `size_width`, `size_height`
- `open_in_gimp`, `gimp_not_found`, `file_not_found`
- `no_designs`, `design_add`, `design_name`, `design_file`
- `select_item_first`, `confirm_delete`, `delete_confirm_msg`
- `showing_of`, `showing_all`

### المفاتيح الجديدة المطلوبة

التحقق: كل هذه المفاتيح **غير موجودة** في ar.py و en.py الحالية.

#### أ) لـ `_source_picker_dialog.py`

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_src_picker_title` | اختيار مصدر الحساب التلقائي | Select Auto-Calculation Source |
| `dim_src_picker_header` | اختر مجموعة القيم المصدر | Select Source Value Set |
| `dim_src_picker_from_group` | من مجموعة | From group |
| `dim_src_picker_field` | الحقل | Field |
| `dim_src_picker_hint` | اختر مجموعة القيم اللي هيتحسب منها الحقل | Select the value set to calculate this field from |
| `dim_src_picker_no_values` | لا توجد قيم محفوظة في هذه المجموعة | No saved values in this group |
| `dim_src_picker_apply` | ✓  تطبيق الحساب | ✓  Apply Calculation |
| `dim_src_preview_fmt` | ✓  {name}:  {val}  {sign}  =  {result}  {unit} | ✓  {name}:  {val}  {sign}  =  {result}  {unit} |

#### ب) لـ `_categories_panel.py` (تصنيفات مجموعات المقاسات)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_cat_panel_title` | تصنيفات التصميمات | Design Categories |
| `dim_cat_col_name` | التصنيف | Category |
| `dim_cat_col_count` | عدد المجموعات | Group Count |
| `dim_cat_new_mode` | ─── تصنيف جديد ─── | ─── New Category ─── |
| `dim_cat_edit_mode` | ─── تعديل: {name} ─── | ─── Edit: {name} ─── |
| `dim_cat_no_parent` | — بدون أب (رئيسي) — | — No Parent (Top Level) — |
| `dim_cat_pick_color` | اختر لون | Pick Color |
| `dim_cat_pick_color_title` | اختر لون التصنيف | Pick Category Color |
| `dim_cat_has_children_warn` | ⚠️ يحتوي على {count} تصنيف فرعي — سيتم حذفها. | ⚠️ Contains {count} sub-categories — they will be deleted. |
| `dim_cat_has_sets_warn` | ⚠️ {count} مجموعة مقاسات ستفقد تصنيفها. | ⚠️ {count} dimension sets will lose their category. |

#### ج) لـ `_groups_panel.py` (لوحة مجموعات المقاسات)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_sets_panel_title` | 📐  مجموعات المقاسات | 📐  Dimension Sets |
| `dim_sets_search_placeholder` | 🔍 بحث باسم المجموعة... | 🔍 Search by group name... |
| `dim_sets_all_categories` | — كل التصنيفات — | — All Categories — |
| `dim_sets_col_name` | اسم المجموعة | Set Name |
| `dim_sets_col_category` | التصنيف | Category |
| `dim_sets_col_unit` | الوحدة | Unit |
| `dim_sets_col_fields` | عدد الحقول | Fields Count |
| `dim_sets_form_title` | بيانات المجموعة | Set Data |
| `dim_sets_new_mode` | ─── مجموعة جديدة ─── | ─── New Set ─── |
| `dim_sets_edit_mode` | ─── تعديل: {name} ─── | ─── Edit: {name} ─── |
| `dim_sets_name_placeholder` | مثال: مقاسات الثوب، مقاسات البنطلون... | Example: Dress sizes, Pants sizes... |
| `dim_sets_default_unit_label` | الوحدة الافتراضية | Default Unit |
| `dim_sets_add_btn` | ➕  إضافة مجموعة | ➕  Add Set |
| `dim_sets_fields_header` | 📋  حقول المجموعة المختارة | 📋  Selected Set Fields |
| `dim_sets_linked_designs_warn` | المجموعة «{name}» مرتبطة بـ {count} تصميم.\nاحذف الارتباط من التصميمات أولاً. | Set «{name}» linked to {count} designs.\nRemove the link from designs first. |
| `dim_sets_has_fields_warn` | ⚠️ تحتوي على {count} حقل — سيتم حذفها جميعاً. | ⚠️ Contains {count} fields — all will be deleted. |

#### د) لـ `_fields_panel.py` (حقول المجموعة)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_field_panel_title` | حقول المجموعة | Set Fields |
| `dim_field_col_order` | الترتيب | Order |
| `dim_field_col_name_en` | الاسم | Name |
| `dim_field_col_label` | التسمية | Label |
| `dim_field_col_unit` | الوحدة | Unit |
| `dim_field_col_type` | النوع | Type |
| `dim_field_col_required` | إلزامي | Required |
| `dim_field_col_depends` | يعتمد على | Depends On |
| `dim_field_type_number` | رقم | Number |
| `dim_field_type_text` | نص | Text |
| `dim_field_add_btn` | ➕  إضافة حقل | ➕  Add Field |
| `dim_field_select_first` | اختر حقلاً أولاً | Select a field first |

#### هـ) لـ `_field_dialog.py` (نافذة إضافة/تعديل حقل)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_field_dlg_new_title` | إضافة حقل جديد | Add New Field |
| `dim_field_dlg_edit_title` | تعديل حقل | Edit Field |
| `dim_field_name_en_label` | الاسم (إنجليزي) | Name (English) |
| `dim_field_name_en_placeholder` | مثال: length, width ... | Example: length, width ... |
| `dim_field_label_ar_label` | التسمية (عربي) | Label (Arabic) |
| `dim_field_label_ar_placeholder` | مثال: الطول، العرض ... | Example: Length, Width ... |
| `dim_field_required_check` | حقل إلزامي | Required Field |
| `dim_field_dep_group_title` | اعتماد على حقل من مجموعة مقاسات (اختياري) | Depends on field from dimension set (optional) |
| `dim_field_source_set_label` | المجموعة المصدر | Source Set |
| `dim_field_source_field_label` | الحقل المصدر | Source Field |
| `dim_field_offset_label` | إضافة / خصم | Add / Subtract |
| `dim_field_preview_label` | المعاينة | Preview |
| `dim_field_same_set_prefix` | ← نفس المجموعة: {name} | ← Same Set: {name} |
| `dim_field_no_numeric_fields` | — لا توجد حقول رقمية — | — No numeric fields — |
| `dim_field_dep_hint` | القيمة = قيمة الحقل المصدر + الإضافة (سالب للخصم) | Value = source field value + offset (negative to subtract) |
| `dim_field_preview_no_value` | لا توجد قيمة محفوظة بعد في المجموعة المصدر | No saved value yet in the source set |
| `dim_field_name_required` | أدخل الاسم والتسمية | Enter name and label |

#### و) لـ `_instance_popup.py` (نافذة إدخال القيم)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_inst_dlg_new_title` | إضافة مجموعة قيم جديدة | Add New Value Set |
| `dim_inst_dlg_edit_title` | تعديل مجموعة قيم | Edit Value Set |
| `dim_inst_hdr_new` | ➕  إضافة مجموعة قيم جديدة | ➕  Add New Value Set |
| `dim_inst_hdr_edit` | ✏️  تعديل القيم | ✏️  Edit Values |
| `dim_inst_name_label` | الاسم | Name |
| `dim_inst_name_placeholder` | مثال: A4، مقاس L، النموذج الأول... | Example: A4, Size L, First Model... |
| `dim_inst_values_label` | القيم | Values |
| `dim_inst_no_numeric_fields` | هذه المجموعة ليس لها حقول رقمية. | This set has no numeric fields. |
| `dim_inst_calc_all_btn` | ⟳  حساب الكل تلقائياً | ⟳  Calculate All Automatically |
| `dim_inst_auto_tooltip` | حساب تلقائي من المصدر | Auto-calculate from source |
| `dim_inst_no_source_value` | لا توجد قيمة للحقل المصدر بعد.\nأدخل قيمة المصدر في هذه المجموعة أولاً. | No source field value yet.\nEnter the source value in this set first. |
| `dim_inst_no_cross_value` | لا توجد قيمة للحقل المصدر في المجموعة المختارة.\nأدخل القيمة في مجموعة القيم المصدر أولاً. | No source field value in the selected group.\nEnter the value in the source value set first. |

#### ز) لـ `_sets_list_panel.py` (قايمة مجموعات المقاسات)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_sets_list_title` | 📐  مجموعات المقاسات | 📐  Dimension Sets |
| `dim_sets_list_search` | 🔍  بحث... | 🔍  Search... |
| `dim_sets_list_all_cats` | كل التصنيفات | All Categories |
| `dim_sets_list_count_all` | {count} مجموعة | {count} sets |
| `dim_sets_list_count_filtered` | {shown} من {total} مجموعة | {shown} of {total} sets |
| `dim_sets_card_hint` | 💡 لإضافة أو تعديل المجموعات والتصنيفات — اذهب لتبويب «المجموعات» | 💡 To add or edit sets and categories — go to the «Groups» tab |
| `dim_sets_card_field_suffix` | {count} حقل | {count} fields |
| `dim_sets_badge_values` | {count} قيمة | {count} values |
| `dim_sets_empty_select_title` | اختر مجموعة مقاسات من القايمة | Select a dimension set from the list |
| `dim_sets_empty_select_hint` | اضغط على أي مجموعة من القايمة على اليسار | Click on any group from the left list |

#### ح) لـ `_instances_table.py` (جدول قيم المقاسات)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `dim_inst_table_placeholder` | اختر مجموعة مقاسات من القايمة | Select a dimension set from the list |
| `dim_inst_table_status` | {count} مجموعة قيم  ·  انقر مرتين للتعديل | {count} value sets  ·  Double-click to edit |
| `dim_inst_add_btn` | ➕  إضافة قيمة | ➕  Add Value |
| `dim_inst_edit_btn` | ✏️  تعديل | ✏️  Edit |
| `dim_inst_copy_btn` | 📋  نسخ | 📋  Copy |
| `dim_inst_delete_confirm` | حذف «{name}» وكل قيمها؟ | Delete «{name}» and all its values? |
| `dim_inst_copy_title` | نسخ مجموعة القيم | Copy Value Set |
| `dim_inst_copy_label` | اسم النسخة الجديدة: | New copy name: |
| `dim_inst_copy_default` | {name} (نسخة) | {name} (copy) |
| `dim_inst_col_name` | الاسم | Name |

#### ط) لـ `_size_dialog.py` (نافذة إضافة/تعديل مقاس التصميم)

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `design_size_dlg_new_title` | إضافة مقاس جديد | Add New Size |
| `design_size_dlg_edit_title` | تعديل مقاس | Edit Size |
| `design_size_set_label` | مجموعة المقاسات | Dimension Set |
| `design_size_instance_label` | المقاس | Size |
| `design_size_width_label` | حقل العرض | Width Field |
| `design_size_height_label` | حقل الطول | Height Field |
| `design_size_dpi_label` | حقل الدقة (DPI) | DPI Field |
| `design_size_canvas_label` | مقاس الكانفاس | Canvas Size |
| `design_size_gimp_path_label` | مسار ملف GIMP | GIMP File Path |
| `design_size_gimp_browse_tooltip` | اختر ملف .xcf موجود | Select existing .xcf file |
| `design_size_select_set` | ─ اختر مجموعة مقاسات ─ | ─ Select Dimension Set ─ |
| `design_size_select_instance` | ─ اختر مقاساً ─ | ─ Select a Size ─ |
| `design_size_select_width` | ─ اختر حقل العرض ─ | ─ Select Width Field ─ |
| `design_size_select_height` | ─ اختر حقل الطول ─ | ─ Select Height Field ─ |
| `design_size_select_dpi` | ─ اختياري: حقل الدقة (DPI) ─ | ─ Optional: DPI Field ─ |
| `design_size_canvas_no_dpi` | {w} × {h} {unit}  (حدد حقل DPI لحساب الـ px) | {w} × {h} {unit}  (select DPI field to calculate px) |
| `design_size_canvas_with_dpi` | {w} × {h} {unit}  →  {w_px} × {h_px} px  @  {dpi} DPI | {w} × {h} {unit}  →  {w_px} × {h_px} px  @  {dpi} DPI |
| `design_size_canvas_incomplete` | ⚠️  القيم غير مكتملة في هذا المقاس | ⚠️  Incomplete values in this size |
| `design_size_canvas_dash` | ─ | ─ |
| `design_size_gimp_placeholder` | مسار ملف .xcf — اتركه فارغاً لإنشاء ملف جديد | Path to .xcf file — leave empty to create new |
| `design_size_choose_set` | اختر مجموعة مقاسات | Select dimension set |
| `design_size_choose_instance` | اختر المقاس | Select size |
| `design_size_already_used` | هذا المقاس مضاف بالفعل لهذا التصميم | This size is already added to this design |

#### ي) لـ `_size_card.py` و `size_card/helper.py`

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `design_size_card_open_gimp_btn` | فتح في GIMP | Open in GIMP |
| `design_size_card_create_gimp_btn` | إنشاء في GIMP | Create in GIMP |
| `design_size_card_link_file_btn` | ربط ملف | Link File |
| `design_size_card_file_exists` | الملف موجود | File exists |
| `design_size_card_file_missing` | الملف غير موجود | File not found |
| `design_size_card_file_none` | لا يوجد ملف | No file |
| `design_size_card_file_not_found_msg` | الملف:\n{path}\n\nاستخدم «ربط ملف» لتحديث المسار. | File:\n{path}\n\nUse «Link File» to update the path. |
| `design_size_card_create_canvas_title` | إنشاء كانفاس | Create Canvas |
| `design_size_card_create_canvas_msg` | الأبعاد: {w} × {h} {unit}\nالبكسل: {w_px} × {h_px} px  @  {dpi} DPI\nالملف: {path} | Dimensions: {w} × {h} {unit}\nPixels: {w_px} × {h_px} px  @  {dpi} DPI\nFile: {path} |
| `design_size_card_save_gimp_title` | اختر مكان حفظ ملف GIMP | Choose GIMP File Save Location |
| `design_size_card_link_file_title` | اختر ملف GIMP موجود | Choose Existing GIMP File |
| `design_size_card_gimp_filter` | GIMP Files (*.xcf) | GIMP Files (*.xcf) |
| `design_size_card_dims_unknown` | الأبعاد غير محددة | Dimensions not set |
| `design_size_card_missing_gimp` | GIMP غير موجود.\nحدد مساره من ⚙️ الإعدادات. | GIMP not found.\nSet its path from ⚙️ Settings. |
| `design_size_card_pillow_missing` | تحتاج تثبيت Pillow:\n\npip install Pillow | Pillow required:\n\npip install Pillow |
| `design_size_card_open_failed` | فشل فتح GIMP:\n{error} | Failed to open GIMP:\n{error} |

#### ك) لـ `_designs_table.py` و `_design_card.py`

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `design_table_new_btn` | تصميم جديد  + | New Design  + |
| `design_table_set_filter_label` | المجموعة: | Set: |
| `design_table_all_sets` | كل المجموعات | All Sets |
| `design_table_reset_filters_btn` | ↺  مسح | ↺  Clear |
| `design_table_count` | {count} تصميم | {count} designs |
| `design_table_empty_no_designs` | لا توجد تصميمات | No Designs |
| `design_table_empty_start` | اضغط «تصميم جديد» للبدء | Press «New Design» to start |
| `design_table_empty_no_results` | لا توجد نتائج | No results |
| `design_table_empty_change_criteria` | جرّب تغيير معايير البحث | Try changing search criteria |
| `design_table_search_placeholder` | بحث بالاسم... | Search by name... |
| `design_card_size_badge_tooltip` | {count} مقاس | {count} sizes |
| `design_card_status_all_files` | ✓  {count}/{total} ملف | ✓  {count}/{total} files |
| `design_card_status_partial_files` | ⚡  {count}/{total} ملف | ⚡  {count}/{total} files |
| `design_card_status_no_files` | ○  {count} مقاس — بدون ملفات | ○  {count} sizes — no files |

#### ل) لـ `_design_detail_panel.py`

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `design_detail_new_badge` | جديد | New |
| `design_detail_saved_badge` | محفوظ | Saved |
| `design_detail_new_title` | تصميم جديد | New Design |
| `design_detail_new_btn` | جديد | New |
| `design_detail_save_btn` | حفظ التصميم | Save Design |
| `design_detail_name_label` | الاسم | Name |
| `design_detail_name_placeholder` | اسم التصميم... | Design name... |
| `design_detail_category_label` | التصنيف | Category |
| `design_detail_notes_label` | ملاحظات | Notes |
| `design_detail_notes_placeholder` | اختياري... | Optional... |
| `design_detail_sizes_section` | المقاسات | Sizes |
| `design_detail_add_size_btn` | + إضافة مقاس | + Add Size |
| `design_detail_save_first_warn` | احفظ التصميم أولاً قبل إضافة مقاسات | Save the design first before adding sizes |
| `design_detail_no_sizes_title` | لا توجد مقاسات بعد | No sizes yet |
| `design_detail_no_sizes_hint` | اضغط «+ إضافة مقاس» لإضافة أول مقاس | Press «+ Add Size» to add the first size |
| `design_detail_delete_size_confirm` | حذف هذا المقاس من التصميم؟ | Delete this size from the design? |
| `design_detail_name_required` | أدخل اسم التصميم | Enter design name |
| `design_detail_no_category` | — بدون تصنيف — | — No Category — |

#### م) لـ `_designs_categories_panel.py`

| المفتاح | العربية | الإنجليزية |
|---|---|---|
| `design_cats_panel_title` | التصنيفات | Categories |
| `design_cats_add_tooltip` | تصنيف جديد | New Category |
| `design_cats_all` | كل التصميمات | All Designs |
| `design_cats_search_placeholder` | بحث في التصنيفات... | Search categories... |
| `design_cats_edit_btn` | تعديل | Edit |
| `design_cats_delete_btn` | حذف | Delete |
| `design_cats_new_form_title` | تصنيف جديد | New Category |
| `design_cats_edit_form_title` | تعديل: {name} | Edit: {name} |
| `design_cats_name_placeholder` | اسم التصنيف... | Category name... |
| `design_cats_parent_label` | تابع لـ: | Parent: |
| `design_cats_color_label` | اللون: | Color: |
| `design_cats_pick_color_btn` | اختر لون | Pick Color |
| `design_cats_save_btn` | حفظ | Save |
| `design_cats_cancel_btn` | إلغاء | Cancel |
| `design_cats_no_parent` | — بدون أب — | — No Parent — |
| `design_cats_has_children_warn` | ⚠️ {count} تصنيف فرعي سيُحذف. | ⚠️ {count} sub-categories will be deleted. |
| `design_cats_has_designs_warn` | ⚠️ {count} تصميم سيفقد تصنيفه. | ⚠️ {count} designs will lose their category. |

---

## 3. طبقة الـ Services الجديدة

### `services/design/__init__.py`
```python
# فارغ
```

### `services/design/dimension_set_service.py`

```python
"""
services/design/dimension_set_service.py
==========================================
Service layer لمجموعات المقاسات وحقولها واعتمادياتها.
يُستدعى من tabs/design/ بدلاً من repos مباشرة.
"""
from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets, fetch_dimension_set,
    insert_dimension_set, update_dimension_set, delete_dimension_set,
    fetch_fields_for_set, fetch_field,
    insert_field, update_field, delete_field, reorder_fields,
    fetch_field_dep, set_field_dep, remove_field_dep,
    fetch_all_design_categories, fetch_design_category,
    insert_design_category, update_design_category, delete_design_category,
    build_category_tree, fetch_category_descendants,
)
from db.designs.dimension_instances_repo import (
    fetch_instances_for_set, fetch_instance,
    insert_instance, update_instance, delete_instance, duplicate_instance,
    fetch_instance_values, save_instance_values, calc_instance_cross_auto,
)


class DimensionSetService:
    """CRUD كاملة لمجموعات المقاسات وحقولها وتصنيفاتها."""

    def __init__(self, conn):
        self.conn = conn

    # ── Sets ────────────────────────────────────────────
    def list_sets(self): return fetch_all_dimension_sets(self.conn)
    def get_set(self, sid): return fetch_dimension_set(self.conn, sid)
    def create_set(self, name, cat_id, unit, notes):
        return insert_dimension_set(self.conn, name, cat_id, unit, notes)
    def update_set(self, sid, name, cat_id, unit, notes):
        update_dimension_set(self.conn, sid, name, cat_id, unit, notes)
    def delete_set(self, sid): delete_dimension_set(self.conn, sid)

    def count_designs_for_set(self, sid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM design_sizes WHERE set_id=?", (sid,)
        ).fetchone()["c"]

    def count_fields_for_set(self, sid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?", (sid,)
        ).fetchone()["c"]

    def count_instances_for_set(self, sid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_set_instances WHERE set_id=?", (sid,)
        ).fetchone()["c"]

    # ── Fields ──────────────────────────────────────────
    def list_fields(self, set_id): return fetch_fields_for_set(self.conn, set_id)
    def get_field(self, fid): return fetch_field(self.conn, fid)
    def create_field(self, set_id, name, label, unit, ftype, required, sort_order):
        return insert_field(self.conn, set_id, name, label, unit, ftype, required, sort_order)
    def update_field(self, fid, name, label, unit, ftype, required, sort_order):
        update_field(self.conn, fid, name, label, unit, ftype, required, sort_order)
    def delete_field(self, fid): delete_field(self.conn, fid)
    def reorder_fields(self, set_id, ids): reorder_fields(self.conn, set_id, ids)

    # ── Field Dependencies ──────────────────────────────
    def get_field_dep(self, fid): return fetch_field_dep(self.conn, fid)
    def set_field_dep(self, fid, src_fid, offset, notes, src_set_id=None):
        set_field_dep(self.conn, fid, src_fid, offset, notes, source_set_id=src_set_id)
    def remove_field_dep(self, fid): remove_field_dep(self.conn, fid)

    # ── Categories ──────────────────────────────────────
    def list_categories(self): return fetch_all_design_categories(self.conn)
    def get_category(self, cid): return fetch_design_category(self.conn, cid)
    def create_category(self, name, color, parent_id):
        return insert_design_category(self.conn, name, color, parent_id)
    def update_category(self, cid, name, color, parent_id):
        update_design_category(self.conn, cid, name, color, parent_id)
    def delete_category(self, cid): delete_design_category(self.conn, cid)
    def build_tree(self, rows): return build_category_tree(rows)
    def get_descendants(self, cid): return fetch_category_descendants(self.conn, cid)

    def count_sets_in_category(self, cid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_sets WHERE category_id=?", (cid,)
        ).fetchone()["c"]

    # ── Instances ───────────────────────────────────────
    def list_instances(self, set_id): return fetch_instances_for_set(self.conn, set_id)
    def get_instance(self, iid): return fetch_instance(self.conn, iid)
    def create_instance(self, set_id, name):
        return insert_instance(self.conn, set_id, name)
    def update_instance(self, iid, name): update_instance(self.conn, iid, name)
    def delete_instance(self, iid): delete_instance(self.conn, iid)
    def duplicate_instance(self, iid, new_name):
        return duplicate_instance(self.conn, iid, new_name)

    def get_instance_values(self, iid): return fetch_instance_values(self.conn, iid)
    def save_instance_values(self, iid, set_id, values):
        save_instance_values(self.conn, iid, set_id, values)
    def calc_cross_auto(self, field_id, instance_id):
        return calc_instance_cross_auto(self.conn, field_id, instance_id)

    def get_source_instance_value(self, source_instance_id, source_field_id):
        row = self.conn.execute(
            "SELECT value_num FROM dimension_set_values "
            "WHERE instance_id=? AND field_id=?",
            (source_instance_id, source_field_id)
        ).fetchone()
        return float(row["value_num"]) if row and row["value_num"] is not None else None

    def get_set_name(self, set_id) -> str:
        row = self.conn.execute(
            "SELECT name FROM dimension_sets WHERE id=?", (set_id,)
        ).fetchone()
        return row["name"] if row else f"#{set_id}"
```

### `services/design/design_service.py`

```python
"""
services/design/design_service.py
===================================
Service layer للتصميمات وتصنيفاتها.
"""
from db.designs.designs_repo import (
    fetch_all_designs, fetch_design,
    insert_design, update_design, delete_design,
)
from db.designs.design_item_categories_repo import (
    fetch_all_item_categories, fetch_item_category,
    insert_item_category, update_item_category, delete_item_category,
    build_item_category_tree, fetch_item_category_descendants,
    count_designs_per_category,
)


class DesignService:
    def __init__(self, conn):
        self.conn = conn

    # ── Designs ─────────────────────────────────────────
    def list_designs(self, category_id=None, set_id=None, name_q=""):
        return fetch_all_designs(self.conn, category_id, set_id, name_q)
    def get_design(self, did): return fetch_design(self.conn, did)
    def create_design(self, name, cat_id=None, notes=""):
        return insert_design(self.conn, name, cat_id, notes)
    def update_design(self, did, name, cat_id=None, notes=""):
        update_design(self.conn, did, name, cat_id, notes)
    def delete_design(self, did): delete_design(self.conn, did)

    # ── Item Categories ─────────────────────────────────
    def list_item_categories(self): return fetch_all_item_categories(self.conn)
    def get_item_category(self, cid): return fetch_item_category(self.conn, cid)
    def create_item_category(self, name, color, parent_id=None):
        return insert_item_category(self.conn, name, color, parent_id)
    def update_item_category(self, cid, name, color, parent_id=None):
        update_item_category(self.conn, cid, name, color, parent_id)
    def delete_item_category(self, cid): delete_item_category(self.conn, cid)
    def build_tree(self, rows): return build_item_category_tree(rows)
    def get_descendants(self, cid): return fetch_item_category_descendants(self.conn, cid)
    def count_designs_per_category(self): return count_designs_per_category(self.conn)
```

### `services/design/design_size_service.py`

```python
"""
services/design/design_size_service.py
========================================
Service layer لمقاسات التصميم.
"""
from db.designs.designs_sizes_repo import (
    fetch_design_sizes, fetch_design_size,
    insert_design_size, update_design_size, delete_design_size,
    update_design_size_path, fetch_canvas_size, fetch_canvas_dpi,
    fetch_instances_for_set_with_values, instance_already_used,
)
from db.designs.dimension_sets_repo import fetch_all_dimension_sets, fetch_fields_for_set


class DesignSizeService:
    def __init__(self, conn):
        self.conn = conn

    def list_sizes(self, design_id): return fetch_design_sizes(self.conn, design_id)
    def get_size(self, size_id): return fetch_design_size(self.conn, size_id)
    def create_size(self, design_id, set_id, instance_id,
                    width_field_id=None, height_field_id=None,
                    xcf_path=None, notes="", dpi_field_id=None):
        return insert_design_size(
            self.conn, design_id, set_id, instance_id,
            width_field_id, height_field_id, xcf_path, notes,
            dpi_field_id=dpi_field_id
        )
    def update_size(self, size_id, width_field_id, height_field_id,
                    xcf_path, notes, dpi_field_id=None):
        update_design_size(self.conn, size_id, width_field_id, height_field_id,
                           xcf_path, notes, dpi_field_id=dpi_field_id)
    def update_path(self, size_id, path): update_design_size_path(self.conn, size_id, path)
    def delete_size(self, size_id): delete_design_size(self.conn, size_id)

    def get_canvas_size(self, size_id): return fetch_canvas_size(self.conn, size_id)
    def get_canvas_dpi(self, size_id): return fetch_canvas_dpi(self.conn, size_id)

    def list_all_sets(self): return fetch_all_dimension_sets(self.conn)
    def list_fields_for_set(self, set_id): return fetch_fields_for_set(self.conn, set_id)
    def list_instances_for_set(self, set_id):
        return fetch_instances_for_set_with_values(self.conn, set_id)
    def is_instance_used(self, design_id, instance_id, exclude_size_id=None):
        return instance_already_used(self.conn, design_id, instance_id, exclude_size_id)

    def get_set_default_unit(self, set_id) -> str:
        row = self.conn.execute(
            "SELECT default_unit FROM dimension_sets WHERE id=?", (set_id,)
        ).fetchone()
        return row["default_unit"] if row and row["default_unit"] else "cm"

    def get_field_value(self, instance_id, field_id):
        row = self.conn.execute(
            "SELECT value_num FROM dimension_set_values "
            "WHERE instance_id=? AND field_id=?",
            (instance_id, field_id)
        ).fetchone()
        return row["value_num"] if row else None
```

---

## 4. التعديلات على الملفات الموجودة

---

### `ui/tabs/design/dimension_sets/_source_picker_dialog.py`

**التعديلات:**
1. حذف كل ثوابت الألوان المحلية (`_BLUE`, `_GREEN`, إلخ)
2. استيراد `_C` من `ui.theme` و `tr` من `ui.widgets.core.i18n`
3. استيراد `DimensionSetService` بدلاً من repos مباشرة
4. استبدال كل الألوان بـ `_C[...]`
5. استبدال كل النصوص العربية بـ `tr(...)`
6. استخدام `DimensionSetService` في `_build` لجلب البيانات

```python
"""
ui/tabs/design/dimension_sets/_source_picker_dialog.py
=======================================================
Dialog لاختيار الـ instance المصدر قبل الحساب التلقائي.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget,
    QButtonGroup, QRadioButton,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.dimension_set_service import DimensionSetService


def _btn_primary_ss():
    return f"""
        QPushButton {{
            background: {_C['accent']};
            color: {_C['accent_text']};
            border: none; border-radius: 7px;
            padding: 6px 20px; font-weight: bold; font-size: 12px;
        }}
        QPushButton:hover  {{ background: {_C['accent_hover']}; }}
        QPushButton:disabled {{ background: {_C['border_med']}; color: {_C['text_disabled']}; }}
    """


def _btn_ghost_ss():
    return f"""
        QPushButton {{
            background: {_C['bg_input']};
            color: {_C['accent']};
            border: 1.5px solid {_C['accent_mid']};
            border-radius: 7px; padding: 5px 16px; font-size: 12px;
        }}
        QPushButton:hover {{ background: {_C['accent_light']}; }}
    """


class _SourcePickerDialog(QDialog):
    def __init__(self, conn, source_set_id, source_field_id,
                 offset=0.0, target_field_label="", parent=None):
        super().__init__(parent)
        self.conn = conn
        self._svc = DimensionSetService(conn)
        self.source_set_id = source_set_id
        self.source_field_id = source_field_id
        self.offset = offset
        self.target_label = target_field_label
        self.selected_instance_id = None
        self._instance_names: dict[int, str] = {}

        self.setWindowTitle(tr("dim_src_picker_title"))
        self.setMinimumWidth(480)
        self.setMinimumHeight(360)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {_C['bg_surface']}; }}")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # ── رأس ──
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['accent_light']};
                border-radius: 10px;
                border: 1px solid {_C['accent_mid']};
            }}
        """)
        hdr_lay = QVBoxLayout(hdr_frame)
        hdr_lay.setContentsMargins(14, 12, 14, 12)
        hdr_lay.setSpacing(4)

        title = QLabel(f"⟳  {tr('dim_src_picker_header')}")
        title.setStyleSheet(f"""
            font-weight: bold; font-size: 13px; color: {_C['accent']};
            background: transparent; border: none;
        """)

        src_set_name = self._svc.get_set_name(self.source_set_id)
        src_field = self._svc.get_field(self.source_field_id)
        src_field_label = src_field["label"] if src_field else f"#{self.source_field_id}"
        src_field_unit  = src_field["unit"]  if src_field else ""
        self._src_field_label = src_field_label
        self._src_field_unit  = src_field_unit

        sign = f"+{self.offset:g}" if self.offset >= 0 else f"{self.offset:g}"
        formula = (
            f"{src_field_label}  {sign}  →  {self.target_label}"
            if self.offset != 0 else
            f"{src_field_label}  →  {self.target_label}"
        )

        subtitle = QLabel(
            f"{tr('dim_src_picker_from_group')}:  <b>{src_set_name}</b>   ·   "
            f"{tr('dim_src_picker_field')}:  <b>{src_field_label}</b>"
        )
        subtitle.setStyleSheet(f"""
            font-size: 11px; color: {_C['text_primary']};
            background: transparent; border: none;
        """)

        formula_lbl = QLabel(f"📐  {formula}")
        formula_lbl.setStyleSheet(f"""
            font-size: 11px; color: {_C['text_muted']};
            background: transparent; border: none;
        """)

        hdr_lay.addWidget(title)
        hdr_lay.addWidget(subtitle)
        hdr_lay.addWidget(formula_lbl)
        root.addWidget(hdr_frame)

        hint = QLabel(tr("dim_src_picker_hint") + ":")
        hint.setStyleSheet(f"""
            font-size: 11px; font-weight: bold; color: {_C['text_muted']};
            background: transparent;
        """)
        root.addWidget(hint)

        # ── قايمة الـ instances ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: 1.5px solid {_C['border']}; border-radius: 8px; background: {_C['bg_input']}; }}
            QScrollBar:vertical {{ background: {_C['bg_surface']}; width: 6px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background: {_C['border_med']}; border-radius: 3px; min-height: 24px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        container = QWidget()
        container.setStyleSheet(f"background: {_C['bg_input']};")
        self._list_lay = QVBoxLayout(container)
        self._list_lay.setSpacing(4)
        self._list_lay.setContentsMargins(10, 10, 10, 10)

        self._btn_group = QButtonGroup(self)
        self._btn_group.buttonClicked.connect(self._on_instance_selected)

        instances = self._svc.list_instances(self.source_set_id)

        if not instances:
            empty = QLabel(tr("dim_src_picker_no_values"))
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {_C['text_muted']}; padding: 20px;")
            self._list_lay.addWidget(empty)
        else:
            for inst in instances:
                self._add_instance_row(inst)
            if len(instances) == 1:
                first_btn = self._btn_group.button(instances[0]["id"])
                if first_btn and first_btn.isEnabled():
                    first_btn.setChecked(True)
                    self._on_instance_selected(first_btn)

        self._list_lay.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        # ── معاينة النتيجة ──
        self._preview_frame = QFrame()
        self._preview_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['success_bg']};
                border: 1.5px solid {_C['success_border']};
                border-radius: 8px;
            }}
        """)
        self._preview_frame.setVisible(False)
        p_lay = QHBoxLayout(self._preview_frame)
        p_lay.setContentsMargins(14, 10, 14, 10)
        self._preview_lbl = QLabel("")
        self._preview_lbl.setStyleSheet(f"""
            font-size: 12px; font-weight: bold; color: {_C['success']};
            background: transparent; border: none;
        """)
        p_lay.addWidget(self._preview_lbl)
        root.addWidget(self._preview_frame)

        # ── أزرار ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton(tr("cancel"))
        self.btn_cancel.setStyleSheet(_btn_ghost_ss())
        self.btn_cancel.setMinimumHeight(36)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton(tr("dim_src_picker_apply"))
        self.btn_ok.setStyleSheet(_btn_primary_ss())
        self.btn_ok.setMinimumHeight(36)
        self.btn_ok.setMinimumWidth(140)
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_ok)
        root.addLayout(btn_row)

    def _add_instance_row(self, inst):
        iid  = inst["id"]
        name = inst["name"].strip() if inst["name"].strip() else f"#{iid}"
        self._instance_names[iid] = name

        values   = self._svc.get_instance_values(iid)
        val_info = values.get(self.source_field_id, {})
        src_val  = val_info.get("value_num")

        row_frame = QFrame()
        row_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border']};
                border-radius: 8px;
            }}
            QFrame:hover {{ border-color: {_C['accent_mid']}; background: {_C['bg_hover']}; }}
        """)
        row_lay = QHBoxLayout(row_frame)
        row_lay.setContentsMargins(12, 8, 12, 8)
        row_lay.setSpacing(12)

        radio = QRadioButton()
        radio.setStyleSheet(f"""
            QRadioButton {{ spacing: 0px; background: transparent; }}
            QRadioButton::indicator {{
                width: 18px; height: 18px; border-radius: 9px;
                border: 2px solid {_C['accent_mid']}; background: {_C['bg_input']};
            }}
            QRadioButton::indicator:checked {{
                background: {_C['accent']}; border-color: {_C['accent']};
            }}
        """)
        radio.setProperty("instance_id", iid)
        radio.setProperty("src_val", src_val)
        has_value = src_val is not None
        radio.setEnabled(has_value)
        self._btn_group.addButton(radio, iid)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"""
            font-weight: bold; font-size: 12px;
            color: {_C['text_primary'] if has_value else _C['text_muted']};
            background: transparent; border: none;
        """)

        if has_value:
            val_txt = f"{src_val:g}  {self._src_field_unit}".strip()
            result  = src_val + self.offset
            sign    = f"+{self.offset:g}" if self.offset >= 0 else f"{self.offset:g}"
            res_txt = f"= {result:g}" if self.offset == 0 else f"{sign} = {result:g}"
            val_lbl = QLabel(val_txt)
            val_lbl.setStyleSheet(f"font-size: 12px; color: {_C['text_primary']}; background: transparent; border: none;")
            res_lbl = QLabel(res_txt)
            res_lbl.setStyleSheet(f"""
                font-size: 12px; font-weight: bold; color: {_C['success']};
                background: {_C['success_bg']}; border: 1px solid {_C['success_border']};
                border-radius: 5px; padding: 1px 8px;
            """)
        else:
            val_lbl = QLabel(tr("no_data"))
            val_lbl.setStyleSheet(f"font-size: 11px; color: {_C['danger_border']}; background: transparent; border: none;")
            res_lbl = QLabel("—")
            res_lbl.setStyleSheet(f"color: {_C['text_muted']}; background: transparent; border: none;")

        row_lay.addWidget(radio)
        row_lay.addWidget(name_lbl, stretch=1)
        row_lay.addWidget(val_lbl)
        row_lay.addWidget(res_lbl)

        def _frame_click(event, r=radio):
            if r.isEnabled():
                r.setChecked(True)
                self._on_instance_selected(r)
        row_frame.mousePressEvent = _frame_click
        self._list_lay.addWidget(row_frame)

    def _on_instance_selected(self, btn):
        iid     = btn.property("instance_id")
        src_val = btn.property("src_val")
        if iid is None or src_val is None:
            return
        self.selected_instance_id = iid
        self.btn_ok.setEnabled(True)
        inst_name = self._instance_names.get(iid, "")
        result = src_val + self.offset
        sign   = f"+{self.offset:g}" if self.offset >= 0 else f"{self.offset:g}"
        if self.offset != 0:
            txt = f"✓  {inst_name}:  {src_val:g}  {sign}  =  {result:g}  {self._src_field_unit}".strip()
        else:
            txt = f"✓  {inst_name}:  {result:g}  {self._src_field_unit}".strip()
        self._preview_lbl.setText(txt)
        self._preview_frame.setVisible(True)

    def get_selected(self) -> int | None:
        return self.selected_instance_id
```

---

### `ui/tabs/design/dimension_sets/_categories_panel.py`

**التعديلات:**
1. حذف كل ثوابت الألوان المحلية
2. استيراد `_C`, `tr`
3. استبدال استدعاءات `dimension_sets_repo` بـ `DimensionSetService`
4. استبدال كل الألوان والنصوص

```python
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QMessageBox, QColorDialog,
    QTreeWidget, QTreeWidgetItem,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.widgets.dialogs.confirm import confirm_delete
from ui.helpers import buttons_row, danger_button
from services.design.dimension_set_service import DimensionSetService


class _CategoriesPanel(QWidget):
    changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._svc        = DimensionSetService(conn)
        self._editing_id = None
        self._color      = _C["accent"]
        self._build()
        self._load_tree()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        hdr = QLabel(tr("dim_cat_panel_title"))
        hdr.setStyleSheet(f"""
            font-weight: bold; font-size: 13px; color: {_C['accent']};
            background: {_C['accent_light']}; border-radius: 6px; padding: 6px 12px;
        """)
        root.addWidget(hdr)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([tr("dim_cat_col_name"), tr("dim_cat_col_count")])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        root.addWidget(self.tree, stretch=1)

        btn_edit_cat = QPushButton(tr("category_edit"))
        btn_del_cat  = danger_button(tr("category_delete"))
        for b in (btn_edit_cat, btn_del_cat):
            b.setMinimumHeight(28)
        btn_edit_cat.clicked.connect(self._edit_category)
        btn_del_cat.clicked.connect(self._delete_category)
        root.addLayout(buttons_row(btn_edit_cat, btn_del_cat))

        grp  = QGroupBox(tr("category_data"))
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel(tr("dim_cat_new_mode"))
        self.lbl_mode.setStyleSheet(f"font-weight: bold; color: {_C['accent']};")
        form.addRow(self.lbl_mode)

        self.inp_cat_name = QLineEdit()
        self.inp_cat_name.setPlaceholderText(tr("category_name") + "...")
        self.inp_cat_name.setMinimumHeight(30)
        form.addRow(tr("category_name") + " :", self.inp_cat_name)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(28)
        form.addRow(tr("category_parent") + " :", self.cmb_parent)

        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(28, 28)
        self._update_color_preview()
        btn_color = QPushButton(tr("dim_cat_pick_color"))
        btn_color.setMinimumHeight(28)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()
        form.addRow(tr("category_color") + " :", color_row)

        self.btn_cat_add    = QPushButton(tr("btn_add"))
        self.btn_cat_save   = QPushButton(tr("btn_save"))
        self.btn_cat_cancel = QPushButton(tr("btn_cancel"))
        self.btn_cat_save.setVisible(False)
        self.btn_cat_cancel.setVisible(False)
        for b in (self.btn_cat_add, self.btn_cat_save, self.btn_cat_cancel):
            b.setMinimumHeight(30)
        self.btn_cat_add.clicked.connect(self._add_category)
        self.btn_cat_save.clicked.connect(self._save_category)
        self.btn_cat_cancel.clicked.connect(self._reset_form)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_cat_add)
        btn_row.addWidget(self.btn_cat_save)
        btn_row.addWidget(self.btn_cat_cancel)
        form.addRow(btn_row)
        root.addWidget(grp)

        self._reload_parent_combo()

    def _load_tree(self):
        expanded = set()
        def _collect(item):
            if item.isExpanded():
                expanded.add(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                _collect(item.child(i))
        for i in range(self.tree.topLevelItemCount()):
            _collect(self.tree.topLevelItem(i))

        self.tree.clear()
        rows = self._svc.list_categories()
        tree = self._svc.build_tree(rows)
        self._add_tree_nodes(tree, parent=None, expanded=expanded)
        self.tree.expandAll()

    def _add_tree_nodes(self, nodes, parent, expanded):
        for node in nodes:
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))
            cnt = self._svc.count_sets_in_category(node["id"])
            item.setText(1, str(cnt) if cnt else "—")
            if parent is None:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
            if node["id"] in expanded:
                item.setExpanded(True)
            if node["children"]:
                self._add_tree_nodes(node["children"], item, expanded)

    def _selected_cat_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _reload_parent_combo(self, exclude_id=None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem(tr("dim_cat_no_parent"), None)
        rows = self._svc.list_categories()
        tree = self._svc.build_tree(rows)
        excluded = set()
        if exclude_id is not None:
            excluded = set(self._svc.get_descendants(exclude_id))
        self._add_parent_nodes(tree, 0, excluded)
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, excluded):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            if node["id"] in excluded:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, excluded)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, tr("dim_cat_pick_color_title"))
        if col.isValid():
            self._color = col.name()
            self._update_color_preview()

    def _update_color_preview(self):
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid {_C['border_med']};"
        )

    def _add_category(self):
        name = self.inp_cat_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("category_name_required"))
            return
        parent_id = self.cmb_parent.currentData()
        self._svc.create_category(name, self._color, parent_id)
        self._reset_form()
        self._load_tree()
        self.changed.emit()

    def _edit_category(self):
        cat_id = self._selected_cat_id()
        if cat_id is None:
            QMessageBox.information(self, tr("info"), tr("category_select_first"))
            return
        cat = self._svc.get_category(cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color      = cat["color"]
        self.inp_cat_name.setText(cat["name"])
        self._update_color_preview()
        self._reload_parent_combo(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.setText(tr("dim_cat_edit_mode").format(name=cat["name"]))
        self.btn_cat_add.setVisible(False)
        self.btn_cat_save.setVisible(True)
        self.btn_cat_cancel.setVisible(True)

    def _save_category(self):
        if self._editing_id is None:
            return
        name = self.inp_cat_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("category_name_required"))
            return
        parent_id = self.cmb_parent.currentData()
        self._svc.update_category(self._editing_id, name, self._color, parent_id)
        self._reset_form()
        self._load_tree()
        self.changed.emit()

    def _delete_category(self):
        cat_id = self._selected_cat_id()
        if cat_id is None:
            QMessageBox.information(self, tr("info"), tr("category_select_first"))
            return
        cat = self._svc.get_category(cat_id)
        if not cat:
            return
        descendants = self._svc.get_descendants(cat_id)
        sets_count  = self._svc.count_sets_in_category(cat_id)

        msg = tr("delete_confirm_msg").format(name=cat["name"])
        child_count = len(descendants) - 1
        if child_count:
            msg += f"\n{tr('dim_cat_has_children_warn').format(count=child_count)}"
        if sets_count:
            msg += f"\n{tr('dim_cat_has_sets_warn').format(count=sets_count)}"

        if QMessageBox.question(self, tr("confirm_delete"), msg,
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for did in sorted(descendants, reverse=True):
                self._svc.delete_category(did)
            self._load_tree()
            self.changed.emit()

    def _reset_form(self):
        self._editing_id = None
        self._color      = _C["accent"]
        self.inp_cat_name.clear()
        self._update_color_preview()
        self.lbl_mode.setText(tr("dim_cat_new_mode"))
        self.btn_cat_add.setVisible(True)
        self.btn_cat_save.setVisible(False)
        self.btn_cat_cancel.setVisible(False)
        self._reload_parent_combo()

    def refresh(self):
        self._load_tree()
        self._reload_parent_combo()
```

---

### `ui/tabs/design/dimension_sets/_groups_panel.py`

**التعديلات:**
1. حذف ثوابت الألوان
2. استيراد `_C`, `tr`
3. استبدال `fetch_*` بـ `DimensionSetService`
4. استبدال كل النصوص والألوان

**الكود المعدّل** (المقاطع الأساسية فقط — نفس المنطق مع تبديل الألوان والنصوص):

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.dimension_set_service import DimensionSetService

# في _SetsManagerPanel.__init__:
self._svc = DimensionSetService(conn)

# كل self.conn.execute(...) للقراءة → يُعوَّض بـ self._svc.*
# مثال:
#   القديم: fetch_all_dimension_sets(self.conn)
#   الجديد: self._svc.list_sets()

#   القديم: fetch_all_design_categories(self.conn)
#   الجديد: self._svc.list_categories()

#   القديم: insert_dimension_set(self.conn, name, cat_id, unit, notes)
#   الجديد: self._svc.create_set(name, cat_id, unit, notes)

#   القديم: self.conn.execute("SELECT COUNT(*) as c FROM design_dimensions WHERE set_id=?", (sid,)).fetchone()["c"]
#   الجديد: self._svc.count_designs_for_set(sid)

#   القديم: self.conn.execute("SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?", (sid,)).fetchone()["c"]
#   الجديد: self._svc.count_fields_for_set(sid)

# جميع ألوان hdr, form, buttons تستخدم _C[...]
# جميع النصوص تستخدم tr(...)
# مثال على هيدر:
hdr = QLabel(tr("dim_sets_panel_title"))
hdr.setStyleSheet(f"""
    font-weight: bold; font-size: 13px; color: {_C['accent']};
    background: {_C['accent_light']}; border-radius: 6px; padding: 6px 12px;
""")

# مثال على mode label:
self.lbl_mode = QLabel(tr("dim_sets_new_mode"))
self.lbl_mode.setStyleSheet(f"font-weight: bold; color: {_C['accent']};")

# search placeholder:
self.inp_search.setPlaceholderText(tr("dim_sets_search_placeholder"))

# all categories item:
self.cmb_cat_filter.addItem(tr("dim_sets_all_categories"), None)
```

---

### `ui/tabs/design/dimension_sets/_fields_panel.py`

**التعديلات:**
1. حذف ثوابت الألوان
2. استيراد `_C`, `tr`
3. استبدال `fetch_*` و `delete_field` و `reorder_fields` بـ `DimensionSetService`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.dimension_set_service import DimensionSetService

# في __init__:
self._svc = DimensionSetService(conn)

# في _build:
hdr = QLabel(tr("dim_field_panel_title"))
hdr.setStyleSheet(f"font-weight: bold; color: {_C['accent']}; font-size: 12px;")

self.table = make_table(
    [tr("dim_field_col_order"), tr("dim_field_col_name_en"), tr("dim_field_col_label"),
     tr("dim_field_col_unit"), tr("dim_field_col_type"), tr("dim_field_col_required"),
     tr("dim_field_col_depends")],
    stretch_col=2
)

btn_add  = QPushButton(tr("dim_field_add_btn"))
btn_edit = QPushButton(tr("category_edit"))
btn_del  = danger_button(tr("category_delete"))

# في _refresh:
self._svc.list_fields(self._set_id)  # بدلاً من fetch_fields_for_set(self.conn, self._set_id)

# نوع الحقل:
"رقم" if f["field_type"] == "number" else "نص"
# يصبح:
tr("dim_field_type_number") if f["field_type"] == "number" else tr("dim_field_type_text")

# في _edit_field, _del_field, _add_field:
# f = self._svc.get_field(fid)  بدلاً من fetch_field(self.conn, fid)
# self._svc.delete_field(fid)   بدلاً من delete_field(self.conn, fid)
# self._svc.reorder_fields(set_id, ids) بدلاً من reorder_fields(...)

# تحذير اختيار أولاً:
QMessageBox.information(self, tr("info"), tr("dim_field_select_first"))
```

---

### `ui/tabs/design/dimension_sets/_field_dialog.py`

**التعديلات:**
1. حذف imports من `dimension_sets_repo` مباشرة
2. استيراد `_C`, `tr`, `DimensionSetService`
3. استبدال كل `self.conn` calls بـ `self._svc`
4. استبدال النصوص

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.dimension_set_service import DimensionSetService

# في __init__:
self._svc = DimensionSetService(conn)

# setWindowTitle:
self.setWindowTitle(tr("dim_field_dlg_edit_title") if field_data else tr("dim_field_dlg_new_title"))

# حقول الفورم:
form.addRow(tr("dim_field_name_en_label") + " :", self.inp_name)
form.addRow(tr("dim_field_label_ar_label") + " :", self.inp_label)
form.addRow(tr("unit") + " :", self.cmb_unit)
form.addRow(tr("type") + " :", self.cmb_type)

self.inp_name.setPlaceholderText(tr("dim_field_name_en_placeholder"))
self.inp_label.setPlaceholderText(tr("dim_field_label_ar_placeholder"))
self.chk_required = QCheckBox(tr("dim_field_required_check"))

# GroupBox للاعتمادية:
self._dep_grp = QGroupBox(tr("dim_field_dep_group_title"))
dep_lay.addRow(tr("dim_field_source_set_label") + " :", self.cmb_source_set)
dep_lay.addRow(tr("dim_field_source_field_label") + " :", self.cmb_source)
dep_lay.addRow(tr("dim_field_offset_label") + " :", self.sp_offset)
dep_lay.addRow(tr("dim_field_preview_label") + " :", self._source_preview)

hint = QLabel(tr("dim_field_dep_hint"))
hint.setStyleSheet(f"color: {_C['accent']}; font-size: 10px; background: {_C['accent_light']}; border-radius: 4px; padding: 4px 8px;")

# نفس المجموعة prefix:
self.cmb_source_set.addItem(tr("dim_field_same_set_prefix").format(name=ds["name"]), ds["id"])

# لا توجد حقول رقمية:
self.cmb_source.addItem(tr("dim_field_no_numeric_fields"), None)

# preview text لو لا توجد قيمة:
self._source_preview.setText(tr("dim_field_preview_no_value"))

# في _reload_source_fields:
fields = self._svc.list_fields(set_id)  # بدلاً من fetch_fields_for_set

# في _save:
# fetch_field → self._svc.get_field
# insert_field → self._svc.create_field
# update_field → self._svc.update_field
# fetch_fields_for_set → self._svc.list_fields
# set_field_dep → self._svc.set_field_dep
# remove_field_dep → self._svc.remove_field_dep
# fetch_all_dimension_sets → self._svc.list_sets()

if not name or not label:
    QMessageBox.warning(self, tr("warning"), tr("dim_field_name_required"))
```

---

### `ui/tabs/design/dimension_sets/values_panel/_instance_popup.py`

**التعديلات:**
1. حذف ثوابت الألوان
2. استيراد `_C`, `tr`
3. استبدال repos بـ `DimensionSetService`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.dimension_set_service import DimensionSetService

# في __init__:
self._svc = DimensionSetService(conn)

# window title:
title = tr("dim_inst_dlg_edit_title") if instance_id else tr("dim_inst_dlg_new_title")
self.setWindowTitle(title)

# header:
hdr_txt = tr("dim_inst_hdr_edit") if self.instance_id else tr("dim_inst_hdr_new")
hdr = QLabel(hdr_txt)
hdr.setStyleSheet(f"""
    font-size: 14px; font-weight: bold; color: {_C['accent']};
    background: {_C['accent_light']}; border-radius: 8px; padding: 8px 14px;
""")

# name label:
lbl_name = QLabel(tr("dim_inst_name_label") + ":")
self.inp_name.setPlaceholderText(tr("dim_inst_name_placeholder"))

# values label:
fields_lbl = QLabel(tr("dim_inst_values_label") + ":")

# empty fields message:
empty = QLabel(tr("dim_inst_no_numeric_fields"))

# calc all button:
btn_calc_all = QPushButton(tr("dim_inst_calc_all_btn"))

# auto tooltip:
btn_auto.setToolTip(tr("dim_inst_auto_tooltip"))

# في _calc_one (same-set, no value):
QMessageBox.information(self, tr("info"), tr("dim_inst_no_source_value"))

# في _calc_one (cross-set, no value):
QMessageBox.information(self, tr("info"), tr("dim_inst_no_cross_value"))

# في _load_values:
saved = self._svc.get_instance_values(self.instance_id)

# في _save_temp:
if not self.instance_id:
    name = self.inp_name.text().strip()
    self.instance_id = self._svc.create_instance(self.set_id, name)
values = {fid: sp.value() for fid, sp in self._spins.items()}
self._svc.save_instance_values(self.instance_id, self.set_id, values)

# في _save:
if self.instance_id:
    self._svc.update_instance(self.instance_id, name)
else:
    self.instance_id = self._svc.create_instance(self.set_id, name)
values = {fid: sp.value() for fid, sp in self._spins.items()}
self._svc.save_instance_values(self.instance_id, self.set_id, values)

# في _calc_one:
fields = self._svc.list_fields(self.set_id)  # للحصول على dep
# بدلاً من: fetch_fields_for_set, fetch_instance, etc.
# self._svc.calc_cross_auto(field_id, self.instance_id)
# self._svc.get_source_instance_value(src_iid, source_field_id)

# ألوان spin:
spin.setStyleSheet(f"""
    QDoubleSpinBox {{
        border: 1.5px solid {_C['border']}; border-radius: 8px;
        padding: 4px 10px; font-size: 13px; background: {_C['bg_input']};
    }}
    QDoubleSpinBox:focus {{ border-color: {_C['accent']}; }}
""")
```

---

### `ui/tabs/design/dimension_sets/values_panel/_sets_list_panel.py`

**التعديلات:**
1. حذف ثوابت الألوان
2. استيراد `_C`, `tr`
3. استبدال repos بـ `DimensionSetService`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.dimension_set_service import DimensionSetService

# في __init__:
self._svc = DimensionSetService(conn)

# في _build:
self._hdr_lbl = QLabel(tr("dim_sets_list_title"))
self._hdr_lbl.setStyleSheet(f"""
    font-weight: bold; font-size: {fs(base,+1)}pt;
    color: {_C['accent']}; background: {_C['accent_light']};
    padding: 10px 16px; border-bottom: 1px solid {_C['border']};
""")

# hint:
hint = QLabel(tr("dim_sets_card_hint"))

# في _load:
self._all_rows = list(self._svc.list_sets())
# للـ categories:
rows = self._svc.list_categories()
# build_tree:
tree = self._svc.build_tree(rows)

# في _apply_filter (counts):
fields_cnt    = self._svc.count_fields_for_set(ds["id"])
instances_cnt = self._svc.count_instances_for_set(ds["id"])

# badge text:
self._badge = QLabel(tr("dim_sets_badge_values").format(count=instances_cnt))

# count label:
self._count_lbl.setText(
    tr("dim_sets_list_count_all").format(count=shown) if shown == total
    else tr("dim_sets_list_count_filtered").format(shown=shown, total=total)
)

# meta label:
self._meta_lbl = QLabel(
    f"{category or '—'}  ·  {unit}  ·  {tr('dim_sets_card_field_suffix').format(count=fields_cnt)}"
)

# empty state labels:
e_msg = QLabel(tr("dim_sets_empty_select_title"))
e_hint = QLabel(tr("dim_sets_empty_select_hint"))

# filter placeholder:
self._cmb_cat.addItem(tr("dim_sets_list_all_cats"), None)
```

---

### `ui/tabs/design/dimension_sets/values_panel/_instances_table.py`

**التعديلات:**
1. حذف ثوابت الألوان
2. استيراد `_C`, `tr`
3. استبدال repos بـ `DimensionSetService`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.dimension_set_service import DimensionSetService

# في __init__:
self._svc = DimensionSetService(conn)

# placeholders:
self._lbl_set_name.setText(tr("dim_inst_table_placeholder"))

# toolbar أزرار:
self.btn_add  = QPushButton(tr("dim_inst_add_btn"))
self.btn_edit = QPushButton(tr("dim_inst_edit_btn"))
self.btn_copy = QPushButton(tr("dim_inst_copy_btn"))
self.btn_del  = QPushButton(tr("delete"))  # exists

# جدول — عمود الاسم:
col_labels = [tr("dim_inst_col_name")] + [f["label"] for f in self._fields]

# status bar:
self._status_bar.setText(tr("dim_inst_table_status").format(count=cnt))

# في load_set:
instances = self._svc.list_instances(set_id)

# في _refresh_table:
# fetch_fields_for_set → self._svc.list_fields(self._set_id)
# fetch_instances_for_set → self._svc.list_instances(self._set_id)
# fetch_instance_values → self._svc.get_instance_values(inst["id"])

# في _copy_instance:
src_name = inst["name"] if inst else ""
name, ok = QInputDialog.getText(
    self, tr("dim_inst_copy_title"),
    tr("dim_inst_copy_label"),
    text=tr("dim_inst_copy_default").format(name=src_name) if src_name else tr("dim_inst_col_name") + " 2"
)
if ok:
    self._svc.duplicate_instance(iid, name.strip())

# في _delete_instance:
inst = self._svc.get_instance(iid)
name = inst["name"] if inst and inst["name"] else f"#{iid}"
if QMessageBox.question(
    self, tr("confirm_delete"),
    tr("dim_inst_delete_confirm").format(name=name),
    QMessageBox.Yes | QMessageBox.No
) == QMessageBox.Yes:
    self._svc.delete_instance(iid)

# ألوان الجدول — كلها من _C
```

---

### `ui/tabs/design/designs/_size_dialog.py`

**التعديلات:**
1. حذف ثوابت الألوان
2. استيراد `_C`, `tr`
3. استبدال repos بـ `DesignSizeService`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.design_size_service import DesignSizeService

# في __init__:
self._svc = DesignSizeService(conn)

# في _build:
hdr = QLabel("📐  " + (tr("design_size_dlg_edit_title") if self.size_id else tr("design_size_dlg_new_title")))
hdr.setStyleSheet(f"""
    font-size: 13px; font-weight: bold; color: {_C['accent']};
    background: {_C['accent_light']}; border-radius: 8px; padding: 8px 14px;
""")

form.addRow(tr("design_size_set_label") + " :", self.cmb_set)
form.addRow(tr("design_size_instance_label") + " :", self.cmb_instance)
form.addRow(tr("design_size_width_label") + " :", self.cmb_width)
form.addRow(tr("design_size_height_label") + " :", self.cmb_height)
form.addRow(tr("design_size_dpi_label") + " :", self.cmb_dpi)
form.addRow(tr("design_size_canvas_label") + " :", self.lbl_canvas)
form.addRow(tr("design_size_gimp_path_label") + " :", path_row)
form.addRow(tr("notes") + " :", self.inp_notes)

btn_browse.setToolTip(tr("design_size_gimp_browse_tooltip"))
self.inp_path.setPlaceholderText(tr("design_size_gimp_placeholder"))

# canvas values:
self.lbl_canvas.setText(tr("design_size_canvas_dash"))
self.lbl_canvas.setStyleSheet(f"""
    color: {_C['success']}; font-weight: bold; font-size: 12px;
    background: {_C['success_bg']}; border: 1px solid {_C['success_border']};
    border-radius: 6px; padding: 6px 12px;
""")

# في _load_sets_combo:
sets = self._svc.list_all_sets()
self.cmb_set.addItem(tr("design_size_select_set"), None)

# في _on_set_changed:
self.cmb_instance.addItem(tr("design_size_select_instance"), None)
self.cmb_width.addItem(tr("design_size_select_width"), None)
self.cmb_height.addItem(tr("design_size_select_height"), None)
self.cmb_dpi.addItem(tr("design_size_select_dpi"), None)

# instance list:
for inst in self._svc.list_instances_for_set(set_id):
    ...

# fields list:
for f in self._svc.list_fields_for_set(set_id):
    ...

# في _update_canvas_preview:
unit = self._svc.get_set_default_unit(set_id)
w_val = self._svc.get_field_value(inst_id, w_fid)
h_val = self._svc.get_field_value(inst_id, h_fid)
# ...
if dpi_val:
    self.lbl_canvas.setText(tr("design_size_canvas_with_dpi").format(
        w=f"{w_val:g}", h=f"{h_val:g}", unit=unit,
        w_px=w_px, h_px=h_px, dpi=f"{dpi_val:g}"
    ))
else:
    self.lbl_canvas.setText(tr("design_size_canvas_no_dpi").format(
        w=f"{w_val:g}", h=f"{h_val:g}", unit=unit
    ))
# incomplete:
self.lbl_canvas.setText(tr("design_size_canvas_incomplete"))

# في _save — validations:
if not set_id:
    QMessageBox.warning(self, tr("warning"), tr("design_size_choose_set"))
if not inst_id:
    QMessageBox.warning(self, tr("warning"), tr("design_size_choose_instance"))
if self._svc.is_instance_used(self.design_id, inst_id, exclude_size_id=self.size_id):
    QMessageBox.warning(self, tr("warning"), tr("design_size_already_used"))
# CRUD:
self._svc.update_size(...)  # أو create_size(...)
```

---

### `ui/tabs/design/designs/_size_card.py`

**التعديلات:**
1. حذف ثوابت الألوان المحلية
2. استيراد `_C`, `tr`
3. استبدال `fetch_canvas_size`, `fetch_canvas_dpi` بـ `DesignSizeService`
4. استبدال `update_design_size_path` بـ `DesignSizeService`
5. نقل كل النصوص لـ `tr()`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.design_size_service import DesignSizeService

# في __init__:
self._svc = DesignSizeService(conn)

# في _build:
w, h = self._svc.get_canvas_size(self._size_id)
dpi  = self._svc.get_canvas_dpi(self._size_id)
unit = self._svc.get_set_default_unit(self._data.get("set_id", 0))

# أزرار:
btn_main = QPushButton(tr("design_size_card_open_gimp_btn") if file_exists else tr("design_size_card_create_gimp_btn"))
btn_link = QPushButton(tr("design_size_card_link_file_btn"))

# status bar:
if file_exists:
    bg, border, txt, col = _C['success_bg'], _C['success_border'], tr("design_size_card_file_exists"), _C['success']
elif has_file:
    bg, border, txt, col = _C['warning_bg'], _C['warning_border'], tr("design_size_card_file_missing"), _C['warning']
else:
    bg, border, txt, col = _C['bg_surface'], _C['border'], tr("design_size_card_file_none"), _C['text_muted']

# dims unknown:
dims = tr("design_size_card_dims_unknown")

# في _open_in_gimp — warning:
QMessageBox.warning(self, tr("file_not_found"), tr("design_size_card_file_not_found_msg").format(path=xcf))

# في _create_in_gimp:
save_path, _ = QFileDialog.getSaveFileName(
    self, tr("design_size_card_save_gimp_title"), ...,
    tr("design_size_card_gimp_filter")
)
# canvas info:
QMessageBox.information(self, tr("design_size_card_create_canvas_title"),
    tr("design_size_card_create_canvas_msg").format(
        w=f"{w:g}", h=f"{h:g}", unit=unit,
        w_px=f"{w_px:,}", h_px=f"{h_px:,}", dpi=int(actual_dpi), path=save_path
    ))
# update path:
self._svc.update_path(self._size_id, save_path)

# في _set_path:
path, _ = QFileDialog.getOpenFileName(
    self, tr("design_size_card_link_file_title"), ...,
    tr("design_size_card_gimp_filter")
)
if path:
    self._svc.update_path(self._size_id, path)
```

---

### `ui/tabs/design/designs/size_card/helper.py`

**التعديلات:**
1. استيراد `tr`
2. استبدال النصوص في `_open_gimp` و `_find_gimp`

```python
from ui.widgets.core.i18n import tr

# في _open_gimp:
if not gimp_exe:
    QMessageBox.warning(None, tr("gimp_not_found"), tr("design_size_card_missing_gimp"))
    return False
# ImportError:
except ImportError:
    QMessageBox.warning(None, tr("warning"), tr("design_size_card_pillow_missing"))
    return False
# Exception:
except Exception as e:
    QMessageBox.critical(None, tr("error"), tr("design_size_card_open_failed").format(error=e))
    return False
```

---

### `ui/tabs/design/designs/_design_detail_panel.py`

**التعديلات:**
1. حذف ثوابت الألوان المحلية
2. استيراد `_C`, `tr`
3. استبدال repos بـ `DesignService` و `DesignSizeService`
4. استبدال كل النصوص

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.design_service import DesignService
from services.design.design_size_service import DesignSizeService

# في __init__:
self._design_svc = DesignService(conn)
self._size_svc   = DesignSizeService(conn)

# في _build:
# title:
self._lbl_title = QLabel(tr("design_detail_new_title"))
# badge:
self._lbl_badge.setText(tr("design_detail_new_badge"))
# buttons:
self.btn_new  = QPushButton(tr("design_detail_new_btn"))
self.btn_save = QPushButton(tr("design_detail_save_btn"))
# fields:
lbl_name = QLabel(tr("design_detail_name_label"))
self.inp_name.setPlaceholderText(tr("design_detail_name_placeholder"))
lbl_cat   = QLabel(tr("design_detail_category_label"))
lbl_notes = QLabel(tr("design_detail_notes_label"))
self.inp_notes.setPlaceholderText(tr("design_detail_notes_placeholder"))
# sizes section:
self._lbl_sizes = QLabel(tr("design_detail_sizes_section"))
self._btn_add_size = QPushButton(tr("design_detail_add_size_btn"))
# empty state:
self._es_lbl.setText(tr("design_detail_no_sizes_title"))
self._es_sub.setText(tr("design_detail_no_sizes_hint"))
# no category:
self.cmb_cat.addItem(tr("design_detail_no_category"), None)

# في load_design:
design = self._design_svc.get_design(design_id)
self._lbl_badge.setText(tr("design_detail_saved_badge"))

# في _reload_categories:
rows = self._design_svc.list_item_categories()
tree = self._design_svc.build_tree(rows)

# في _save:
if not name:
    QMessageBox.warning(self, tr("warning"), tr("design_detail_name_required"))
if self._design_id:
    self._design_svc.update_design(self._design_id, name, cat_id, notes)
else:
    self._design_id = self._design_svc.create_design(name, cat_id, notes)
self._lbl_badge.setText(tr("design_detail_saved_badge"))

# في _load_sizes:
sizes = self._size_svc.list_sizes(self._design_id)

# في _add_size — warning:
QMessageBox.warning(self, tr("warning"), tr("design_detail_save_first_warn"))

# في _delete_size:
if QMessageBox.question(self, tr("confirm_delete"), tr("design_detail_delete_size_confirm"), ...) == ...:
    self._size_svc.delete_size(size_id)

# ألوان Stylesheet — كلها من _C
```

---

### `ui/tabs/design/designs/_designs_table.py`

**التعديلات:**
1. حذف ثوابت الألوان
2. استيراد `_C`, `tr`
3. استبدال `fetch_all_dimension_sets` بـ `DesignSizeService.list_all_sets()`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.design_size_service import DesignSizeService

# في __init__:
self._size_svc = DesignSizeService(conn)

# في _reload_set_combo:
sets = self._size_svc.list_all_sets()
self.cmb_set.addItem(tr("design_table_all_sets"), None)

# في _build:
self.btn_new = QPushButton(tr("design_table_new_btn"))
lbl_set = QLabel(tr("design_table_set_filter_label"))
btn_rst = QPushButton(tr("design_table_reset_filters_btn"))
self.inp_search.setPlaceholderText(tr("design_table_search_placeholder"))

# count label:
self.lbl_count.setText(tr("design_table_count").format(count=total))

# empty states:
self._empty_msg.setText(tr("design_table_empty_no_designs"))
self._empty_sub.setText(tr("design_table_empty_start"))
# when filtered:
self._empty_msg.setText(tr("design_table_empty_no_results"))
self._empty_sub.setText(tr("design_table_empty_change_criteria"))

# ألوان — كلها من _C
```

---

### `ui/tabs/design/designs/designs_table/_design_card.py`

**التعديلات:**
1. حذف ثوابت الألوان المحلية
2. استيراد `_C`, `tr`
3. استبدال `"#1E1B4B"` بـ `_C["design_thumb_bg"]`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr

# thumb background:
thumb_frame.setStyleSheet(f"""
    QFrame {{
        background: {_C['design_thumb_bg']};
        border-radius: {_RADIUS} {_RADIUS} 0 0;
    }}
""")

# status text:
if fl_cnt == sz_cnt:
    status_col  = _C['success']
    status_text = tr("design_card_status_all_files").format(count=fl_cnt, total=sz_cnt)
elif fl_cnt > 0:
    status_col  = _C['warning']
    status_text = tr("design_card_status_partial_files").format(count=fl_cnt, total=sz_cnt)
else:
    status_col  = _C['text_muted']
    status_text = tr("design_card_status_no_files").format(count=sz_cnt)

# border colors:
_ACCENT = _C['accent']
_ACCENT_LT = _C['accent_light']
_ACCENT_BDR = _C['accent_mid']
# etc.
```

---

### `ui/tabs/design/designs/_designs_categories_panel.py`

**التعديلات:**
1. حذف ثوابت الألوان المحلية
2. استيراد `_C`, `tr`
3. استبدال repos بـ `DesignService`

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.design_service import DesignService

# في __init__:
self._svc = DesignService(conn)

# في _build:
self._lbl_header = QLabel(tr("design_cats_panel_title"))
self._btn_add.setToolTip(tr("design_cats_add_tooltip"))
self._inp_search.setPlaceholderText(tr("design_cats_search_placeholder"))
self.btn_edit.setText(tr("design_cats_edit_btn"))
self.btn_del.setText(tr("design_cats_delete_btn"))

# form mode label:
self._mode_lbl.setText(tr("design_cats_new_form_title"))

# في _load — all designs row:
all_row = _CatRow(None, tr("design_cats_all"), _C['accent'], depth=0)

# في _delete:
cat = self._svc.get_item_category(self._active_id)
desc   = self._svc.get_descendants(self._active_id)
counts = self._svc.count_designs_per_category()
msg = tr("delete_confirm_msg").format(name=cat["name"])
if cc:
    msg += f"\n{tr('design_cats_has_children_warn').format(count=cc)}"
if total:
    msg += f"\n{tr('design_cats_has_designs_warn').format(count=total)}"
# CRUD:
for d in sorted(desc, reverse=True):
    self._svc.delete_item_category(d)

# في _CatForm (داخل _row_and_form.py):
self._mode_lbl.setText(tr("design_cats_new_form_title"))
self._mode_lbl.setText(tr("design_cats_edit_form_title").format(name=cat["name"]))
self.inp_name.setPlaceholderText(tr("design_cats_name_placeholder"))
lbl_p.setText(tr("design_cats_parent_label"))
lbl_c.setText(tr("design_cats_color_label"))
btn_c.setText(tr("design_cats_pick_color_btn"))
self.btn_save.setText(tr("design_cats_save_btn"))
btn_cancel.setText(tr("design_cats_cancel_btn"))
self.cmb_parent.addItem(tr("design_cats_no_parent"), None)
```

---

### `ui/tabs/design/designs/designs_categories/_row_and_form.py`

**التعديلات:**
1. حذف ثوابت الألوان المحلية
2. استيراد `_C`, `tr`
3. استبدال كل الألوان والنصوص

```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
from services.design.design_service import DesignService

# في _btn_ss — استخدام _C بدلاً من ثوابت ثابتة:
def _btn_ss(bg, fg, bdr, hover_bg, height=28):
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:1px solid {bdr}; border-radius:5px;"
        f"  padding:0 12px; font-size:12px; min-height:{height}px;"
        f"}}"
        f"QPushButton:hover{{background:{hover_bg};}}"
    )

# الثوابت المحلية تُحذف، تُستبدل بـ _C في كل مكان:
# _ACCENT → _C["accent"]
# _BG_SELECTED → _C["accent_light"]  
# _BG_HOVER → _C["bg_hover"]
# إلخ

# في _CatRow:
self._dot.setStyleSheet(f"color:{self._color}; font-size:8px; background:transparent; border:none;")
# selected style:
f"background:{_C['accent_light']}; border-left:3px solid {_C['accent']}; ..."
# hover style:
f"QFrame:hover{{background:{_C['bg_hover']};}}"

# في _CatForm:
self._mode_lbl.setText(tr("design_cats_new_form_title"))
# ربط بـ DesignService:
self._svc = DesignService(conn)
# في _save:
if self._editing_id:
    self._svc.update_item_category(self._editing_id, name, self._color, pid)
else:
    self._svc.create_item_category(name, self._color, pid)
```

---

### `ui/tabs/design/design_styles.py`

**التعديلات:**
يجب أن يستورد `_C` من `ui.theme` مباشرة وليس من `ui.app_settings` (لأن `_C` في `app_settings` قد يكون مختلفاً):

```python
# السطر القديم:
from ui.app_settings import get_font_size, fs, _C as APP_COLORS

# السطر الجديد:
from ui.font import get_font_size, fs
from ui.theme import _C as APP_COLORS
```

هذا التغيير الوحيد المطلوب هنا. باقي الملف يعمل بشكل صحيح.

---

### `ui/tabs/design/dimension_sets_tab.py`

لا يحتاج تعديلات هيكلية — هو بالفعل orchestrator. التعديل الوحيد:

```python
# إضافة استيراد tr للاستخدام المستقبلي (اختياري)
from ui.widgets.core.i18n import tr
```

---

### `ui/tabs/design/designs_tab.py`

لا يحتاج تعديلات — هو بالفعل orchestrator جيد.

---

## 5. تعديل `theme_manager.py`

إضافة مفتاح واحد فقط في `_LIGHT_THEME` و `_DARK_THEME`:

```python
# في _LIGHT_THEME — أضف قسماً جديداً:
# ── Design Module ───────────────────────────────────────
"design_thumb_bg": "#1E1B4B",   # خلفية الـ thumbnail في بطاقات التصميم

# في _DARK_THEME:
"design_thumb_bg": "#0A0A1E",
```

---

## 6. تعديل `ui/i18n/ar.py`

أضف في نهاية `AR_STRINGS` قسماً جديداً:

```python
# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — Source Picker
# ══════════════════════════════════════════════════════════════════
"dim_src_picker_title":    "اختيار مصدر الحساب التلقائي",
"dim_src_picker_header":   "اختر مجموعة القيم المصدر",
"dim_src_picker_from_group": "من مجموعة",
"dim_src_picker_field":    "الحقل",
"dim_src_picker_hint":     "اختر مجموعة القيم اللي هيتحسب منها الحقل",
"dim_src_picker_no_values": "لا توجد قيم محفوظة في هذه المجموعة",
"dim_src_picker_apply":    "✓  تطبيق الحساب",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — تصنيفات مجموعات المقاسات
# ══════════════════════════════════════════════════════════════════
"dim_cat_panel_title":        "تصنيفات التصميمات",
"dim_cat_col_name":           "التصنيف",
"dim_cat_col_count":          "عدد المجموعات",
"dim_cat_new_mode":           "─── تصنيف جديد ───",
"dim_cat_edit_mode":          "─── تعديل: {name} ───",
"dim_cat_no_parent":          "— بدون أب (رئيسي) —",
"dim_cat_pick_color":         "اختر لون",
"dim_cat_pick_color_title":   "اختر لون التصنيف",
"dim_cat_has_children_warn":  "⚠️ يحتوي على {count} تصنيف فرعي — سيتم حذفها.",
"dim_cat_has_sets_warn":      "⚠️ {count} مجموعة مقاسات ستفقد تصنيفها.",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — لوحة مجموعات المقاسات
# ══════════════════════════════════════════════════════════════════
"dim_sets_panel_title":         "📐  مجموعات المقاسات",
"dim_sets_search_placeholder":  "🔍 بحث باسم المجموعة...",
"dim_sets_all_categories":      "— كل التصنيفات —",
"dim_sets_col_name":            "اسم المجموعة",
"dim_sets_col_category":        "التصنيف",
"dim_sets_col_unit":            "الوحدة",
"dim_sets_col_fields":          "عدد الحقول",
"dim_sets_form_title":          "بيانات المجموعة",
"dim_sets_new_mode":            "─── مجموعة جديدة ───",
"dim_sets_edit_mode":           "─── تعديل: {name} ───",
"dim_sets_name_placeholder":    "مثال: مقاسات الثوب، مقاسات البنطلون...",
"dim_sets_default_unit_label":  "الوحدة الافتراضية",
"dim_sets_add_btn":             "➕  إضافة مجموعة",
"dim_sets_fields_header":       "📋  حقول المجموعة المختارة",
"dim_sets_linked_designs_warn": "المجموعة «{name}» مرتبطة بـ {count} تصميم.\nاحذف الارتباط من التصميمات أولاً.",
"dim_sets_has_fields_warn":     "⚠️ تحتوي على {count} حقل — سيتم حذفها جميعاً.",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — حقول المجموعة
# ══════════════════════════════════════════════════════════════════
"dim_field_panel_title":    "حقول المجموعة",
"dim_field_col_order":      "الترتيب",
"dim_field_col_name_en":    "الاسم",
"dim_field_col_label":      "التسمية",
"dim_field_col_unit":       "الوحدة",
"dim_field_col_type":       "النوع",
"dim_field_col_required":   "إلزامي",
"dim_field_col_depends":    "يعتمد على",
"dim_field_type_number":    "رقم",
"dim_field_type_text":      "نص",
"dim_field_add_btn":        "➕  إضافة حقل",
"dim_field_select_first":   "اختر حقلاً أولاً",

# ── Field Dialog
"dim_field_dlg_new_title":          "إضافة حقل جديد",
"dim_field_dlg_edit_title":         "تعديل حقل",
"dim_field_name_en_label":          "الاسم (إنجليزي)",
"dim_field_name_en_placeholder":    "مثال: length, width ...",
"dim_field_label_ar_label":         "التسمية (عربي)",
"dim_field_label_ar_placeholder":   "مثال: الطول، العرض ...",
"dim_field_required_check":         "حقل إلزامي",
"dim_field_dep_group_title":        "اعتماد على حقل من مجموعة مقاسات (اختياري)",
"dim_field_source_set_label":       "المجموعة المصدر",
"dim_field_source_field_label":     "الحقل المصدر",
"dim_field_offset_label":           "إضافة / خصم",
"dim_field_preview_label":          "المعاينة",
"dim_field_same_set_prefix":        "← نفس المجموعة: {name}",
"dim_field_no_numeric_fields":      "— لا توجد حقول رقمية —",
"dim_field_dep_hint":               "القيمة = قيمة الحقل المصدر + الإضافة (سالب للخصم)",
"dim_field_preview_no_value":       "لا توجد قيمة محفوظة بعد في المجموعة المصدر",
"dim_field_name_required":          "أدخل الاسم والتسمية",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — Instance Popup (إدخال القيم)
# ══════════════════════════════════════════════════════════════════
"dim_inst_dlg_new_title":   "إضافة مجموعة قيم جديدة",
"dim_inst_dlg_edit_title":  "تعديل مجموعة قيم",
"dim_inst_hdr_new":         "➕  إضافة مجموعة قيم جديدة",
"dim_inst_hdr_edit":        "✏️  تعديل القيم",
"dim_inst_name_label":      "الاسم",
"dim_inst_name_placeholder": "مثال: A4، مقاس L، النموذج الأول...",
"dim_inst_values_label":    "القيم",
"dim_inst_no_numeric_fields": "هذه المجموعة ليس لها حقول رقمية.",
"dim_inst_calc_all_btn":    "⟳  حساب الكل تلقائياً",
"dim_inst_auto_tooltip":    "حساب تلقائي من المصدر",
"dim_inst_no_source_value": "لا توجد قيمة للحقل المصدر بعد.\nأدخل قيمة المصدر في هذه المجموعة أولاً.",
"dim_inst_no_cross_value":  "لا توجد قيمة للحقل المصدر في المجموعة المختارة.\nأدخل القيمة في مجموعة القيم المصدر أولاً.",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — قايمة مجموعات المقاسات
# ══════════════════════════════════════════════════════════════════
"dim_sets_list_title":          "📐  مجموعات المقاسات",
"dim_sets_list_search":         "🔍  بحث...",
"dim_sets_list_all_cats":       "كل التصنيفات",
"dim_sets_list_count_all":      "{count} مجموعة",
"dim_sets_list_count_filtered": "{shown} من {total} مجموعة",
"dim_sets_card_hint":           "💡 لإضافة أو تعديل المجموعات والتصنيفات — اذهب لتبويب «المجموعات»",
"dim_sets_card_field_suffix":   "{count} حقل",
"dim_sets_badge_values":        "{count} قيمة",
"dim_sets_empty_select_title":  "اختر مجموعة مقاسات من القايمة",
"dim_sets_empty_select_hint":   "اضغط على أي مجموعة من القايمة على اليسار",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — جدول قيم المقاسات
# ══════════════════════════════════════════════════════════════════
"dim_inst_table_placeholder":   "اختر مجموعة مقاسات من القايمة",
"dim_inst_table_status":        "{count} مجموعة قيم  ·  انقر مرتين للتعديل",
"dim_inst_add_btn":             "➕  إضافة قيمة",
"dim_inst_edit_btn":            "✏️  تعديل",
"dim_inst_copy_btn":            "📋  نسخ",
"dim_inst_delete_confirm":      "حذف «{name}» وكل قيمها؟",
"dim_inst_copy_title":          "نسخ مجموعة القيم",
"dim_inst_copy_label":          "اسم النسخة الجديدة:",
"dim_inst_copy_default":        "{name} (نسخة)",
"dim_inst_col_name":            "الاسم",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — نافذة إضافة/تعديل مقاس
# ══════════════════════════════════════════════════════════════════
"design_size_dlg_new_title":       "إضافة مقاس جديد",
"design_size_dlg_edit_title":      "تعديل مقاس",
"design_size_set_label":           "مجموعة المقاسات",
"design_size_instance_label":      "المقاس",
"design_size_width_label":         "حقل العرض",
"design_size_height_label":        "حقل الطول",
"design_size_dpi_label":           "حقل الدقة (DPI)",
"design_size_canvas_label":        "مقاس الكانفاس",
"design_size_gimp_path_label":     "مسار ملف GIMP",
"design_size_gimp_browse_tooltip": "اختر ملف .xcf موجود",
"design_size_select_set":          "─ اختر مجموعة مقاسات ─",
"design_size_select_instance":     "─ اختر مقاساً ─",
"design_size_select_width":        "─ اختر حقل العرض ─",
"design_size_select_height":       "─ اختر حقل الطول ─",
"design_size_select_dpi":          "─ اختياري: حقل الدقة (DPI) ─",
"design_size_canvas_no_dpi":       "{w} × {h} {unit}  (حدد حقل DPI لحساب الـ px)",
"design_size_canvas_with_dpi":     "{w} × {h} {unit}  →  {w_px} × {h_px} px  @  {dpi} DPI",
"design_size_canvas_incomplete":   "⚠️  القيم غير مكتملة في هذا المقاس",
"design_size_canvas_dash":         "─",
"design_size_gimp_placeholder":    "مسار ملف .xcf — اتركه فارغاً لإنشاء ملف جديد",
"design_size_choose_set":          "اختر مجموعة مقاسات",
"design_size_choose_instance":     "اختر المقاس",
"design_size_already_used":        "هذا المقاس مضاف بالفعل لهذا التصميم",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — بطاقة المقاس
# ══════════════════════════════════════════════════════════════════
"design_size_card_open_gimp_btn":       "فتح في GIMP",
"design_size_card_create_gimp_btn":     "إنشاء في GIMP",
"design_size_card_link_file_btn":       "ربط ملف",
"design_size_card_file_exists":         "الملف موجود",
"design_size_card_file_missing":        "الملف غير موجود",
"design_size_card_file_none":           "لا يوجد ملف",
"design_size_card_file_not_found_msg":  "الملف:\n{path}\n\nاستخدم «ربط ملف» لتحديث المسار.",
"design_size_card_create_canvas_title": "إنشاء كانفاس",
"design_size_card_create_canvas_msg":   "الأبعاد: {w} × {h} {unit}\nالبكسل: {w_px} × {h_px} px  @  {dpi} DPI\nالملف: {path}",
"design_size_card_save_gimp_title":     "اختر مكان حفظ ملف GIMP",
"design_size_card_link_file_title":     "اختر ملف GIMP موجود",
"design_size_card_gimp_filter":         "GIMP Files (*.xcf);;All Files (*)",
"design_size_card_dims_unknown":        "الأبعاد غير محددة",
"design_size_card_missing_gimp":        "GIMP غير موجود.\nحدد مساره من ⚙️ الإعدادات.",
"design_size_card_pillow_missing":      "تحتاج تثبيت Pillow:\n\npip install Pillow",
"design_size_card_open_failed":         "فشل فتح GIMP:\n{error}",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — قائمة التصميمات وبطاقاتها
# ══════════════════════════════════════════════════════════════════
"design_table_new_btn":               "تصميم جديد  +",
"design_table_set_filter_label":      "المجموعة:",
"design_table_all_sets":              "كل المجموعات",
"design_table_reset_filters_btn":     "↺  مسح",
"design_table_count":                 "{count} تصميم",
"design_table_empty_no_designs":      "لا توجد تصميمات",
"design_table_empty_start":           "اضغط «تصميم جديد» للبدء",
"design_table_empty_no_results":      "لا توجد نتائج",
"design_table_empty_change_criteria": "جرّب تغيير معايير البحث",
"design_table_search_placeholder":    "بحث بالاسم...",
"design_card_status_all_files":       "✓  {count}/{total} ملف",
"design_card_status_partial_files":   "⚡  {count}/{total} ملف",
"design_card_status_no_files":        "○  {count} مقاس — بدون ملفات",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — لوحة تفاصيل التصميم
# ══════════════════════════════════════════════════════════════════
"design_detail_new_badge":          "جديد",
"design_detail_saved_badge":        "محفوظ",
"design_detail_new_title":          "تصميم جديد",
"design_detail_new_btn":            "جديد",
"design_detail_save_btn":           "حفظ التصميم",
"design_detail_name_label":         "الاسم",
"design_detail_name_placeholder":   "اسم التصميم...",
"design_detail_category_label":     "التصنيف",
"design_detail_notes_label":        "ملاحظات",
"design_detail_notes_placeholder":  "اختياري...",
"design_detail_sizes_section":      "المقاسات",
"design_detail_add_size_btn":       "+ إضافة مقاس",
"design_detail_save_first_warn":    "احفظ التصميم أولاً قبل إضافة مقاسات",
"design_detail_no_sizes_title":     "لا توجد مقاسات بعد",
"design_detail_no_sizes_hint":      "اضغط «+ إضافة مقاس» لإضافة أول مقاس",
"design_detail_delete_size_confirm": "حذف هذا المقاس من التصميم؟",
"design_detail_name_required":      "أدخل اسم التصميم",
"design_detail_no_category":        "— بدون تصنيف —",

# ══════════════════════════════════════════════════════════════════
# وحدة التصميمات — تصنيفات التصميمات (Sidebar)
# ══════════════════════════════════════════════════════════════════
"design_cats_panel_title":          "التصنيفات",
"design_cats_add_tooltip":          "تصنيف جديد",
"design_cats_all":                  "كل التصميمات",
"design_cats_search_placeholder":   "بحث في التصنيفات...",
"design_cats_edit_btn":             "تعديل",
"design_cats_delete_btn":           "حذف",
"design_cats_new_form_title":       "تصنيف جديد",
"design_cats_edit_form_title":      "تعديل: {name}",
"design_cats_name_placeholder":     "اسم التصنيف...",
"design_cats_parent_label":         "تابع لـ:",
"design_cats_color_label":          "اللون:",
"design_cats_pick_color_btn":       "اختر لون",
"design_cats_save_btn":             "حفظ",
"design_cats_cancel_btn":           "إلغاء",
"design_cats_no_parent":            "— بدون أب —",
"design_cats_has_children_warn":    "⚠️ {count} تصنيف فرعي سيُحذف.",
"design_cats_has_designs_warn":     "⚠️ {count} تصميم سيفقد تصنيفه.",
```

---

## 7. تعديل `ui/i18n/en.py`

أضف في نهاية `EN_STRINGS` نفس المفاتيح بالإنجليزية:

```python
# ══════════════════════════════════════════════════════════════════
# Design Module — Source Picker
# ══════════════════════════════════════════════════════════════════
"dim_src_picker_title":    "Select Auto-Calculation Source",
"dim_src_picker_header":   "Select Source Value Set",
"dim_src_picker_from_group": "From group",
"dim_src_picker_field":    "Field",
"dim_src_picker_hint":     "Select the value set to calculate this field from",
"dim_src_picker_no_values": "No saved values in this group",
"dim_src_picker_apply":    "✓  Apply Calculation",

# ══════════════════════════════════════════════════════════════════
# Design Module — Dimension Set Categories
# ══════════════════════════════════════════════════════════════════
"dim_cat_panel_title":        "Design Categories",
"dim_cat_col_name":           "Category",
"dim_cat_col_count":          "Group Count",
"dim_cat_new_mode":           "─── New Category ───",
"dim_cat_edit_mode":          "─── Edit: {name} ───",
"dim_cat_no_parent":          "— No Parent (Top Level) —",
"dim_cat_pick_color":         "Pick Color",
"dim_cat_pick_color_title":   "Pick Category Color",
"dim_cat_has_children_warn":  "⚠️ Contains {count} sub-categories — they will be deleted.",
"dim_cat_has_sets_warn":      "⚠️ {count} dimension sets will lose their category.",

# ══════════════════════════════════════════════════════════════════
# Design Module — Dimension Sets Panel
# ══════════════════════════════════════════════════════════════════
"dim_sets_panel_title":         "📐  Dimension Sets",
"dim_sets_search_placeholder":  "🔍 Search by group name...",
"dim_sets_all_categories":      "— All Categories —",
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

# ══════════════════════════════════════════════════════════════════
# Design Module — Fields
# ══════════════════════════════════════════════════════════════════
"dim_field_panel_title":    "Set Fields",
"dim_field_col_order":      "Order",
"dim_field_col_name_en":    "Name",
"dim_field_col_label":      "Label",
"dim_field_col_unit":       "Unit",
"dim_field_col_type":       "Type",
"dim_field_col_required":   "Required",
"dim_field_col_depends":    "Depends On",
"dim_field_type_number":    "Number",
"dim_field_type_text":      "Text",
"dim_field_add_btn":        "➕  Add Field",
"dim_field_select_first":   "Select a field first",

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
"dim_field_no_numeric_fields":      "— No numeric fields —",
"dim_field_dep_hint":               "Value = source field value + offset (negative to subtract)",
"dim_field_preview_no_value":       "No saved value yet in the source set",
"dim_field_name_required":          "Enter name and label",

# ══════════════════════════════════════════════════════════════════
# Design Module — Instance Popup
# ══════════════════════════════════════════════════════════════════
"dim_inst_dlg_new_title":   "Add New Value Set",
"dim_inst_dlg_edit_title":  "Edit Value Set",
"dim_inst_hdr_new":         "➕  Add New Value Set",
"dim_inst_hdr_edit":        "✏️  Edit Values",
"dim_inst_name_label":      "Name",
"dim_inst_name_placeholder": "Example: A4, Size L, First Model...",
"dim_inst_values_label":    "Values",
"dim_inst_no_numeric_fields": "This set has no numeric fields.",
"dim_inst_calc_all_btn":    "⟳  Calculate All Automatically",
"dim_inst_auto_tooltip":    "Auto-calculate from source",
"dim_inst_no_source_value": "No source field value yet.\nEnter the source value in this set first.",
"dim_inst_no_cross_value":  "No source field value in the selected group.\nEnter the value in the source value set first.",

# ══════════════════════════════════════════════════════════════════
# Design Module — Sets List Panel
# ══════════════════════════════════════════════════════════════════
"dim_sets_list_title":          "📐  Dimension Sets",
"dim_sets_list_search":         "🔍  Search...",
"dim_sets_list_all_cats":       "All Categories",
"dim_sets_list_count_all":      "{count} sets",
"dim_sets_list_count_filtered": "{shown} of {total} sets",
"dim_sets_card_hint":           "💡 To add or edit sets and categories — go to the «Groups» tab",
"dim_sets_card_field_suffix":   "{count} fields",
"dim_sets_badge_values":        "{count} values",
"dim_sets_empty_select_title":  "Select a dimension set from the list",
"dim_sets_empty_select_hint":   "Click on any group from the left list",

# ══════════════════════════════════════════════════════════════════
# Design Module — Instances Table
# ══════════════════════════════════════════════════════════════════
"dim_inst_table_placeholder":   "Select a dimension set from the list",
"dim_inst_table_status":        "{count} value sets  ·  Double-click to edit",
"dim_inst_add_btn":             "➕  Add Value",
"dim_inst_edit_btn":            "✏️  Edit",
"dim_inst_copy_btn":            "📋  Copy",
"dim_inst_delete_confirm":      "Delete «{name}» and all its values?",
"dim_inst_copy_title":          "Copy Value Set",
"dim_inst_copy_label":          "New copy name:",
"dim_inst_copy_default":        "{name} (copy)",
"dim_inst_col_name":            "Name",

# ══════════════════════════════════════════════════════════════════
# Design Module — Size Dialog
# ══════════════════════════════════════════════════════════════════
"design_size_dlg_new_title":       "Add New Size",
"design_size_dlg_edit_title":      "Edit Size",
"design_size_set_label":           "Dimension Set",
"design_size_instance_label":      "Size",
"design_size_width_label":         "Width Field",
"design_size_height_label":        "Height Field",
"design_size_dpi_label":           "DPI Field",
"design_size_canvas_label":        "Canvas Size",
"design_size_gimp_path_label":     "GIMP File Path",
"design_size_gimp_browse_tooltip": "Select existing .xcf file",
"design_size_select_set":          "─ Select Dimension Set ─",
"design_size_select_instance":     "─ Select a Size ─",
"design_size_select_width":        "─ Select Width Field ─",
"design_size_select_height":       "─ Select Height Field ─",
"design_size_select_dpi":          "─ Optional: DPI Field ─",
"design_size_canvas_no_dpi":       "{w} × {h} {unit}  (select DPI field to calculate px)",
"design_size_canvas_with_dpi":     "{w} × {h} {unit}  →  {w_px} × {h_px} px  @  {dpi} DPI",
"design_size_canvas_incomplete":   "⚠️  Incomplete values in this size",
"design_size_canvas_dash":         "─",
"design_size_gimp_placeholder":    "Path to .xcf file — leave empty to create new",
"design_size_choose_set":          "Select dimension set",
"design_size_choose_instance":     "Select size",
"design_size_already_used":        "This size is already added to this design",

# ══════════════════════════════════════════════════════════════════
# Design Module — Size Card
# ══════════════════════════════════════════════════════════════════
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
"design_size_card_missing_gimp":        "GIMP not found.\nSet its path from ⚙️ Settings.",
"design_size_card_pillow_missing":      "Pillow required:\n\npip install Pillow",
"design_size_card_open_failed":         "Failed to open GIMP:\n{error}",

# ══════════════════════════════════════════════════════════════════
# Design Module — Designs Table & Card
# ══════════════════════════════════════════════════════════════════
"design_table_new_btn":               "New Design  +",
"design_table_set_filter_label":      "Set:",
"design_table_all_sets":              "All Sets",
"design_table_reset_filters_btn":     "↺  Clear",
"design_table_count":                 "{count} designs",
"design_table_empty_no_designs":      "No Designs",
"design_table_empty_start":           "Press «New Design» to start",
"design_table_empty_no_results":      "No results",
"design_table_empty_change_criteria": "Try changing search criteria",
"design_table_search_placeholder":    "Search by name...",
"design_card_status_all_files":       "✓  {count}/{total} files",
"design_card_status_partial_files":   "⚡  {count}/{total} files",
"design_card_status_no_files":        "○  {count} sizes — no files",

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
```

---

## 8. ملفات لا تحتاج تعديل

- `ui/tabs/design/designs/_xcf_thumbnail.py` — تقني بحت، لا UI ولا نصوص
- `ui/tabs/design/dimension_sets/_values_panel.py` — orchestrator جيد بالفعل
- `ui/tabs/design/dimension_sets_tab.py` — orchestrator جيد
- `ui/tabs/design/designs_tab.py` — orchestrator جيد

---
