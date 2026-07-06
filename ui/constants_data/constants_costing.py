"""
ui/constants_data/costing.py
=======================
ثوابت قسم حساب التكلفة (BOM، المنتجات، الخامات، العمالة، الماكينات)
جزء من تقسيم ui/constants.py — راجع ui/constants/__init__.py.
"""

# ── ComponentRow ──────────────────────────────────────────
COMPONENT_ROW_LOAD_DELAY = 50    # ms — QTimer deferred load للـ variants/op_rows

# ComponentRow — أبعاد الـ widgets
COMPONENT_ROW_OUTER_MARGIN_V   = 2    # top/bottom margin للـ outer layout
COMPONENT_ROW_OUTER_SPACING    = 2    # spacing الـ outer VBoxLayout
COMPONENT_ROW_WASTE_MAX_PCT    = 100  # الحد الأقصى لنسبة الهادر (%)
COMPONENT_ROW_WASTE_MIN_PCT    = 0    # الحد الأدنى لنسبة الهادر (%)
COMPONENT_ROW_WASTE_DECIMALS   = 1    # عدد الخانات العشرية لـ waste_spin
COMPONENT_ROW_MAIN_SPACING     = 6    # spacing الصف الرئيسي
COMPONENT_ROW_VARIANT_MIN_W    = 130  # عرض أدنى لـ cmb_variant
COMPONENT_ROW_VARIANT_MAX_W    = 180  # عرض أقصى لـ cmb_variant
COMPONENT_ROW_QTY_MIN_W        = 60   # عرض أدنى لـ qty_edit / total_qty_edit
COMPONENT_ROW_QTY_MAX_W        = 90   # عرض أقصى لـ qty_edit / total_qty_edit
COMPONENT_ROW_WASTE_MIN_W      = 75   # عرض أدنى لـ waste_spin
COMPONENT_ROW_WASTE_MAX_W      = 90   # عرض أقصى لـ waste_spin
COMPONENT_ROW_WIDGET_MIN_H     = 26   # ارتفاع أدنى للـ widgets (variant, waste, op_row)
COMPONENT_ROW_WASTE_ICON_W     = 18   # عرض ثابت لـ lbl_waste
COMPONENT_ROW_DIVIDE_ICON_W    = 14   # عرض ثابت لـ lbl_total_qty
COMPONENT_ROW_DELETE_BTN_W     = 32   # عرض ثابت لزر الحذف
COMPONENT_ROW_OP_CMB_MIN_W     = 280  # عرض أدنى لـ cmb_op_row
COMPONENT_ROW_SUB_MARGIN_H     = 8    # left/right margin لصف العملية الفرعي
COMPONENT_ROW_SUB_MARGIN_V     = 3    # top/bottom margin لصف العملية الفرعي
COMPONENT_ROW_SUB_SPACING      = 8    # spacing صف العملية الفرعي
COMPONENT_ROW_BORDER_RADIUS    = 4    # border-radius للـ widgets داخل ComponentRow

# ── LaborSettingsPanel ─────────────────────────────────────
LABOR_SETTINGS_MIN_W           = 260   # setMinimumWidth لـ inner widget
LABOR_SETTINGS_INNER_MARGIN    = (8, 8, 8, 8)  # contentsMargins لـ inner layout
LABOR_SETTINGS_INNER_SPACING   = 8    # spacing لـ inner layout
LABOR_SETTINGS_BTN_MIN_H       = 32   # ارتفاع أدنى لزر الحفظ
LABOR_SETTINGS_SPIN_MAX_SALARY = 999999  # الحد الأقصى لـ spinbox الراتب
LABOR_SETTINGS_SPIN_MAX_DAYS   = 31   # الحد الأقصى لـ spinbox أيام العمل/الإجازة
LABOR_SETTINGS_SPIN_MAX_HOURS  = 24   # الحد الأقصى لـ spinbox ساعات العمل
LABOR_SETTINGS_SPIN_MAX_OVHD   = 10   # الحد الأقصى لـ spinbox معامل التحميل
LABOR_SETTINGS_SPIN_DEC_SALARY = 2    # خانات عشرية لـ spinbox الراتب
LABOR_SETTINGS_SPIN_DEC_DAYS   = 0    # خانات عشرية لـ spinbox الأيام
LABOR_SETTINGS_SPIN_DEC_HOURS  = 1    # خانات عشرية لـ spinbox الساعات
LABOR_SETTINGS_SPIN_DEC_OVHD   = 2    # خانات عشرية لـ spinbox معامل التحميل

# ── LaborOpTable ───────────────────────────────────────────
LABOR_TABLE_COL0_W  = 40    # عرض عمود الـ ID في جدول العمالة
LABOR_TABLE_COL2_W  = 110   # عرض عمود الفئة في جدول العمالة
LABOR_TABLE_COL3_W  = 110   # عرض عمود الوقت في جدول العمالة
LABOR_TABLE_COL4_W  = 130   # عرض عمود التكلفة في جدول العمالة

# ── LaborOpForm ────────────────────────────────────────────
LABOR_FORM_SPIN_MAX_MINUTES = 99999  # الحد الأقصى لـ spinbox الدقائق في فورم العمالة
LABOR_FORM_SPIN_DEC_MINUTES = 2      # خانات عشرية لـ spinbox الدقائق

# ── MachineForm ────────────────────────────────────────────
MACHINE_FORM_SPIN_MAX_RATE  = 999999  # الحد الأقصى لـ spinbox المعدل (rate_per_hour/unit)
MACHINE_FORM_SPIN_DEC_RATE  = 2       # خانات عشرية لـ spinbox المعدل
MACHINE_FORM_INP_MIN_H      = 30      # ارتفاع أدنى لحقل الاسم في فورم الماكينة

# ── MachineOpForm ──────────────────────────────────────────
MACHINE_OP_FORM_MIN_W       = 280     # setMinimumWidth لـ inner widget في فورم العملية

# ── MachineOpTable ─────────────────────────────────────────
MACHINE_OP_TABLE_COL0_W     = 40      # عرض عمود ID
MACHINE_OP_TABLE_COL1_W     = 140     # عرض عمود الاسم
MACHINE_OP_TABLE_COL2_W     = 100     # عرض عمود الفئة
MACHINE_OP_TABLE_COL3_W     = 120     # عرض عمود الماكينة
MACHINE_OP_TABLE_COL4_W     = 70      # عرض عمود الوضع
MACHINE_OP_TABLE_COL5_W     = 70      # عرض عمود القيمة
MACHINE_OP_TABLE_COL6_W     = 110     # عرض عمود التكلفة

# ── MachineTable ───────────────────────────────────────────
MACHINE_TABLE_COL0_W        = 40      # عرض عمود ID
MACHINE_TABLE_COL2_W        = 110     # عرض عمود الفئة
MACHINE_TABLE_COL3_W        = 90      # عرض عمود المعدل/ساعة
MACHINE_TABLE_COL4_W        = 90      # عرض عمود المعدل/وحدة

# ── ProductForm (_header_bar.py / _rows_manager.py) ────────
PRODUCT_FORM_HEADER_MIN_W       = 700   # setMinimumWidth لـ header_inner
PRODUCT_FORM_HEADER_H           = 130   # setFixedHeight لـ header_scroll
PRODUCT_FORM_HEADER_MARGIN      = (10, 8, 10, 4)   # contentsMargins للـ header_lay
PRODUCT_FORM_HEADER_SPACING     = 4    # spacing لـ header_lay
PRODUCT_FORM_TOP_SPACING        = 8    # spacing لـ top HBoxLayout
PRODUCT_FORM_MODE_MIN_W         = 130  # setMinimumWidth لـ lbl_mode
PRODUCT_FORM_INP_MIN_H          = 28   # setMinimumHeight للـ inputs والأزرار
PRODUCT_FORM_CAT_W              = 160  # setFixedWidth لـ cmb_category
PRODUCT_FORM_TOP_INNER_SPACING  = 4    # addSpacing بين التصنيف والأزرار
PRODUCT_FORM_TOP_BTN_SPACING    = 6    # addSpacing بين زر الإضافة والحفظ
PRODUCT_FORM_ROWS_SPACING       = 4    # spacing لـ rows_layout
PRODUCT_FORM_ROWS_MARGIN        = (6, 4, 6, 4)   # contentsMargins لـ rows_layout
PRODUCT_FORM_ROWS_SCROLL_MIN_H  = 200  # setMinimumHeight للـ scroll area

# ── _ProductMainPanel ──────────────────────────────────────
PRODUCT_MAIN_SPLITTER_HANDLE_W  = 6              # handleWidth للـ QSplitter الرئيسي
PRODUCT_MAIN_SPLITTER_SIZES     = (280, 220, 250) # توزيع الأحجام الابتدائي (form, table, bom)

# ── LaborTab ─────────────────────────────────────────────
LABOR_TAB_SPLITTER_HANDLE_W     = 6           # handleWidth للـ QSplitter في LaborTab
LABOR_TAB_SPLITTER_SIZES        = (280, 400)  # الأحجام الافتراضية (form, table) في LaborTab

# ── MachineTab ───────────────────────────────────────────
MACHINE_TAB_SPLITTER_HANDLE_W       = 6           # handleWidth للـ QSplitter في MachineTab
MACHINE_TAB_MACHINES_SPLITTER_SIZES = (260, 380)  # أحجام splitter تبويب الماكينات (form, table)
MACHINE_TAB_OPS_SPLITTER_SIZES      = (300, 400)  # أحجام splitter تبويب عمليات التشغيل (form, table)

# ── RawInputPanel ──────────────────────────────────────────
RAW_PRICE_INPUT_W    = 110   # عرض ثابت لـ inp_price في RawInputPanel
RAW_QTY_INPUT_W      = 110   # عرض ثابت لـ sp_total_qty في RawInputPanel
RAW_HINT_BORDER_RADIUS = 6   # border-radius لـ lbl_hint في RawInputPanel
RAW_HINT_PAD_V       = 4     # padding عمودي لـ lbl_hint في RawInputPanel
RAW_HINT_PAD_H       = 8     # padding أفقي لـ lbl_hint في RawInputPanel

# ── RawSection ─────────────────────────────────────────────
RAW_SECTION_LIST_MIN_W = 400   # LIST_MIN_W override لـ RawSection (BaseSection)

# ── BulkReplace ────────────────────────────────────────────
BULK_REPLACE_MIN_W          = 750   # setMinimumSize — عرض BulkReplaceDialog
BULK_REPLACE_MIN_H          = 620   # setMinimumSize — ارتفاع BulkReplaceDialog
BULK_REPLACE_HDR_H          = 70    # ارتفاع هيدر BulkReplaceDialog
BULK_REPLACE_HDR_MARGIN_H   = 20    # left/right margin لـ header layout
BULK_REPLACE_BODY_MARGIN_H  = 16    # left/right margin لـ body layout
BULK_REPLACE_BODY_MARGIN_V  = 14    # top/bottom margin لـ body layout
BULK_REPLACE_BODY_SPACING   = 12    # spacing لـ body layout
BULK_REPLACE_BTN_H          = 38    # ارتفاع أزرار Apply/Cancel
BULK_REPLACE_BTN_RADIUS     = 6     # border-radius أزرار BulkReplace
BULK_REPLACE_BTN_PAD_H      = 20    # padding أفقي لزر Apply
BULK_REPLACE_BTN_CANCEL_PAD = 16    # padding أفقي لزر Cancel

# ── _OperationSection ──────────────────────────────────────
OP_SECTION_SPACING          = 10    # spacing الـ VBoxLayout في _OperationSection
OP_SECTION_GRP_RADIUS       = 8     # border-radius لـ QGroupBox
OP_SECTION_GRP_PAD_TOP      = 10    # padding-top لـ QGroupBox
OP_SECTION_GRP_TITLE_PAD_H  = 8     # padding أفقي لعنوان QGroupBox
OP_SECTION_FORM_SPACING     = 8     # spacing الـ QFormLayout
OP_SECTION_CMB_MIN_H        = 32    # min-height لـ cmb_replacement
OP_SECTION_CMB_MIN_W        = 280   # min-width لـ cmb_replacement
OP_SECTION_CMB_RADIUS       = 4     # border-radius لـ cmb_replacement
OP_SECTION_CMB_PAD_H        = 6     # padding أفقي لـ cmb_replacement
OP_SECTION_CMB_PAD_V        = 2     # padding عمودي لـ cmb_replacement
OP_SECTION_SP_W             = 100   # fixed-width لـ sp_uniform
OP_SECTION_FRAME_RADIUS     = 6     # border-radius لـ replace_frame
OP_SECTION_FRAME_PAD        = 4     # padding لـ replace_frame

# ── ProductRow ─────────────────────────────────────────────
PRODUCT_ROW_MARGIN_H        = 10    # left/right margin لـ ProductRow layout
PRODUCT_ROW_MARGIN_V        = 8     # top/bottom margin لـ ProductRow layout
PRODUCT_ROW_SPACING         = 10    # spacing لـ ProductRow layout
PRODUCT_ROW_CHK_W           = 20    # fixed-width للـ checkbox
PRODUCT_ROW_TYPE_ICON_W     = 20    # fixed-width لأيقونة النوع
PRODUCT_ROW_SP_W            = 90    # fixed-width لـ sp_qty
PRODUCT_ROW_SP_MIN_H        = 28    # min-height لـ sp_qty
PRODUCT_ROW_RADIUS          = 6     # border-radius لـ ProductRow

# ── _ProductsPanel ─────────────────────────────────────────
PRODUCTS_PANEL_CMB_H        = 30    # min-height لـ cmb_cat_filter
PRODUCTS_PANEL_CMB_W        = 200   # fixed-width لـ cmb_cat_filter
PRODUCTS_PANEL_CMB_RADIUS   = 4     # border-radius لـ cmb_cat_filter
PRODUCTS_PANEL_CMB_PAD_H    = 6     # padding أفقي لـ cmb_cat_filter
PRODUCTS_PANEL_CMB_PAD_V    = 2     # padding عمودي لـ cmb_cat_filter
PRODUCTS_PANEL_SCROLL_MIN_H = 200   # min-height لـ QScrollArea
PRODUCTS_PANEL_SCROLL_RADIUS= 8     # border-radius لـ QScrollArea
PRODUCTS_PANEL_BAR_RADIUS   = 6     # border-radius لـ quick-select bar
PRODUCTS_PANEL_BAR_PAD      = 2     # padding لـ quick-select bar
PRODUCTS_PANEL_BAR_SPACING  = 8     # spacing داخل quick-select bar
PRODUCTS_PANEL_BTN_H        = 26    # min-height لأزرار الـ quick-select
PRODUCTS_PANEL_BTN_RADIUS   = 4     # border-radius لأزرار quick-select
PRODUCTS_PANEL_BTN_PAD_H    = 10    # padding أفقي لأزرار quick-select
PRODUCTS_PANEL_ROWS_SPACING = 4     # spacing لـ rows_layout
PRODUCTS_PANEL_ROWS_PAD_R   = 4     # right padding لـ rows_layout
PRODUCTS_PANEL_EMPTY_PAD    = 20    # padding لـ empty label

# ── _BomScenariosPanel ─────────────────────────────────────
SCENARIOS_PANEL_H           = 46    # ارتفاع ثابت للوحة السيناريوهات
SCENARIOS_PANEL_MARGIN_H    = 8     # left/right margin للـ layout
SCENARIOS_PANEL_MARGIN_V    = 4     # top/bottom margin للـ layout
SCENARIOS_PANEL_SPACING     = 8     # spacing بين عناصر الـ layout
SCENARIOS_PANEL_CMB_MIN_W   = 200   # عرض أدنى للـ combo السيناريوهات
SCENARIOS_PANEL_CMB_MIN_H   = 30    # ارتفاع أدنى للـ combo السيناريوهات
SCENARIOS_PANEL_CMB_RADIUS  = 4     # border-radius للـ combo
SCENARIOS_PANEL_CMB_PAD_V   = 2     # padding عمودي للـ combo
SCENARIOS_PANEL_CMB_PAD_H   = 8     # padding أفقي للـ combo
SCENARIOS_PANEL_BTN_MIN_H   = 28    # ارتفاع أدنى لأزرار اللوحة
SCENARIOS_PANEL_BTN_RADIUS  = 4     # border-radius لأزرار اللوحة
SCENARIOS_PANEL_BTN_PAD_V   = 2     # padding عمودي لأزرار اللوحة
SCENARIOS_PANEL_BTN_PAD_H   = 6     # padding أفقي لأزرار اللوحة
SCENARIOS_PANEL_FRAME_RADIUS= 6     # border-radius لـ QFrame اللوحة
SCENARIOS_PANEL_BTN_DEFAULT_W = 100  # عرض زر «تعيين افتراضي»
SCENARIOS_PANEL_BTN_RENAME_W  = 80   # عرض زر «تعديل»
SCENARIOS_PANEL_BTN_CLONE_W   = 70   # عرض زر «استنساخ»
SCENARIOS_PANEL_BTN_ADD_W     = 70   # عرض زر «جديد»
SCENARIOS_PANEL_BTN_DEL_W     = 36   # عرض زر «حذف»

# ── _RawVariantsPanel ──────────────────────────────────────
RAW_VARIANTS_SPIN_MAX       = 999999  # الحد الأقصى لـ spinbox عدد القطع
RAW_VARIANTS_SPIN_MIN       = 0.0001  # الحد الأدنى لـ spinbox عدد القطع
RAW_VARIANTS_SPIN_DEC       = 4       # خانات عشرية لـ spinbox عدد القطع
RAW_VARIANTS_SPIN_H         = 28      # ارتفاع أدنى لـ spinbox عدد القطع
RAW_VARIANTS_SPIN_W         = 100     # عرض ثابت لـ spinbox عدد القطع
RAW_VARIANTS_INP_H          = 30      # ارتفاع أدنى لحقل اسم الـ variant
RAW_VARIANTS_PREVIEW_MIN_W  = 120     # عرض أدنى لـ lbl_preview
RAW_VARIANTS_CANCEL_BTN_W   = 28      # عرض ثابت لزر الإلغاء
RAW_VARIANTS_BTN_H          = 30      # ارتفاع أدنى لأزرار الفورم
RAW_VARIANTS_TABLE_MAX_H    = 160     # ارتفاع أقصى للجدول
RAW_VARIANTS_COL_COUNT      = 4       # عدد أعمدة الجدول
RAW_VARIANTS_COL2_W         = 90      # عرض عمود عدد القطع
RAW_VARIANTS_COL3_W         = 110     # عرض عمود التكلفة
RAW_VARIANTS_EDIT_BTN_H     = 26      # ارتفاع أدنى لأزرار التعديل/الحذف

# ── _RawVariantsPanel — layout & stylesheet ────────────────
RAW_VARIANTS_ROOT_SPACING       = 8    # spacing الـ root VBoxLayout
RAW_VARIANTS_ROOT_MARGIN_H      = 10   # left/right margin الـ root layout
RAW_VARIANTS_ROOT_MARGIN_T      = 12   # top margin الـ root layout
RAW_VARIANTS_ROOT_MARGIN_B      = 10   # bottom margin الـ root layout
RAW_VARIANTS_FORM_SPACING       = 8    # spacing الـ form_row HBoxLayout
RAW_VARIANTS_GRP_BORDER_RADIUS  = 8    # border-radius لـ QGroupBox
RAW_VARIANTS_GRP_MARGIN_TOP     = 8    # margin-top لـ QGroupBox
RAW_VARIANTS_GRP_PADDING_TOP    = 8    # padding-top لـ QGroupBox
RAW_VARIANTS_GRP_TITLE_PAD_H    = 6    # padding أفقي لعنوان QGroupBox
RAW_VARIANTS_INFO_RADIUS        = 4    # border-radius لـ lbl_info
RAW_VARIANTS_INFO_PAD_V         = 5    # padding عمودي لـ lbl_info
RAW_VARIANTS_INFO_PAD_H         = 8    # padding أفقي لـ lbl_info
RAW_VARIANTS_INP_RADIUS         = 4    # border-radius لـ inp_name
RAW_VARIANTS_INP_PAD_V          = 2    # padding عمودي لـ inp_name
RAW_VARIANTS_INP_PAD_H          = 6    # padding أفقي لـ inp_name

# ── ScenarioComparisonWidget ───────────────────────────────
SCENARIO_CMP_ROOT_MARGIN        = (12, 10, 12, 12)  # contentsMargins الـ root layout (l,t,r,b)
SCENARIO_CMP_ROOT_SPACING       = 8    # spacing الـ root VBoxLayout
SCENARIO_CMP_CMB_MIN_H          = 28   # ارتفاع أدنى لـ cmb_scenario
SCENARIO_CMP_CMB_MIN_W          = 180  # عرض أدنى لـ cmb_scenario
SCENARIO_CMP_COST_ROW_SPACING   = 6    # spacing صف التكاليف
SCENARIO_CMP_PROFIT_ROW_SPACING = 6    # spacing صف الربح
SCENARIO_CMP_FRAME_RADIUS       = 8    # border-radius لـ QFrame الرئيسي
SCENARIO_CMP_CMB_RADIUS         = 4    # border-radius لـ cmb_scenario
SCENARIO_CMP_CMB_PAD_V          = 2    # padding عمودي لـ cmb_scenario
SCENARIO_CMP_CMB_PAD_H          = 8    # padding أفقي لـ cmb_scenario

# ── _OpRowsEditor ──────────────────────────────────────────
OP_ROWS_ROOT_MARGIN_H       = 10   # left/right margin الـ root layout
OP_ROWS_ROOT_MARGIN_T       = 10   # top margin الـ root layout
OP_ROWS_ROOT_MARGIN_B       = 10   # bottom margin الـ root layout
OP_ROWS_ROOT_SPACING        = 8    # spacing الـ root VBoxLayout
OP_ROWS_FORM_SPACING        = 8    # spacing الـ form_row HBoxLayout
OP_ROWS_INP_MIN_H           = 28   # ارتفاع أدنى لحقول الإدخال
OP_ROWS_SP_VALUE_W          = 100  # عرض ثابت لـ sp_value
OP_ROWS_SP_COUNT_W          = 80   # عرض ثابت لـ sp_count
OP_ROWS_PREVIEW_MIN_W       = 120  # عرض أدنى لـ lbl_preview
OP_ROWS_BTN_CANCEL_W        = 28   # عرض ثابت لزر الإلغاء
OP_ROWS_BTN_MIN_H           = 30   # ارتفاع أدنى لأزرار الفورم
OP_ROWS_TABLE_MAX_H         = 180  # ارتفاع أقصى للجدول
OP_ROWS_TABLE_MIN_H         = 60   # ارتفاع أدنى للجدول
OP_ROWS_COL_VALUE_W         = 90   # عرض عمود القيمة
OP_ROWS_COL_COUNT_W         = 70   # عرض عمود العدد
OP_ROWS_COL_COST_W          = 110  # عرض عمود التكلفة
OP_ROWS_TOTAL_MIN_W         = 120  # عرض أدنى لـ lbl_total
OP_ROWS_BTN_EDIT_MIN_H      = 26   # ارتفاع أدنى لأزرار التعديل/الحذف
OP_ROWS_GRP_BORDER_RADIUS   = 8    # border-radius لـ QGroupBox
OP_ROWS_GRP_MARGIN_TOP      = 8    # margin-top لـ QGroupBox
OP_ROWS_GRP_PAD_TOP         = 8    # padding-top لـ QGroupBox
OP_ROWS_INNER_BORDER_RADIUS = 4    # border-radius لـ widgets داخلية
OP_ROWS_INFO_PAD_V          = 5    # padding عمودي لـ lbl_mode_info
OP_ROWS_INFO_PAD_H          = 8    # padding أفقي لـ lbl_mode_info
OP_ROWS_INP_PAD_V           = 2    # padding عمودي لـ inp_label
OP_ROWS_INP_PAD_H           = 6    # padding أفقي لـ inp_label
OP_ROWS_TOTAL_PAD_V         = 4    # padding عمودي لـ lbl_total
OP_ROWS_TOTAL_PAD_H         = 10   # padding أفقي لـ lbl_total

# ── _OpRowsEditor — حدود القيم العددية وعنوان المجموعة ─────
OP_ROWS_GRP_TITLE_PAD_H     = 6    # padding أفقي لعنوان QGroupBox
OP_ROWS_SP_VALUE_MAX        = 999999   # الحد الأقصى لـ sp_value
OP_ROWS_SP_COUNT_MIN        = 0.0001   # الحد الأدنى لـ sp_count
OP_ROWS_SP_COUNT_MAX        = 999999   # الحد الأقصى لـ sp_count

# ── BomTree ──────────────────────────────────────────────
BOM_TREE_BTN_MIN_H          = 30    # ارتفاع أدنى لأزرار الشجرة
BOM_TREE_BTN_RADIUS         = 4     # border-radius لأزرار الشجرة
BOM_TREE_BTN_PAD_H          = 10    # padding أفقي لأزرار الشجرة
BOM_TREE_BTN_PAD_V          = 4     # padding عمودي لأزرار الشجرة
BOM_TREE_LEGEND_RADIUS      = 4     # border-radius لعنصر الشرح (legend)
BOM_TREE_LEGEND_PAD_H       = 8     # padding أفقي لعنصر الشرح
BOM_TREE_LEGEND_PAD_V       = 4     # padding عمودي لعنصر الشرح
BOM_TREE_HDR_PAD_H          = 6     # padding أفقي لرأس عمود الشجرة
BOM_TREE_HDR_PAD_V          = 4     # padding عمودي لرأس عمود الشجرة
BOM_TREE_COL_QTY_W          = 70    # عرض عمود الكمية
BOM_TREE_COL_WASTE_W        = 70    # عرض عمود نسبة الهادر
BOM_TREE_COL_EFF_QTY_W      = 90    # عرض عمود الكمية الفعلية
BOM_TREE_COL_COST_UNIT_W    = 100   # عرض عمود تكلفة الوحدة
BOM_TREE_COL_TOTAL_COST_W   = 100   # عرض عمود التكلفة الإجمالية
BOM_TREE_COL_TYPE_W         = 90    # عرض عمود النوع
BOM_TREE_MIN_SECTION_SIZE   = 40    # الحد الأدنى لحجم قسم الهيدر

# ── CostingSection — error tab (_make_error_tab) ───────────
COSTING_ERR_TAB_BORDER_W    = 1     # عرض border لتبويب رسالة الخطأ
COSTING_ERR_TAB_RADIUS      = 6     # border-radius لتبويب رسالة الخطأ
COSTING_ERR_TAB_PAD         = 12    # padding لتبويب رسالة الخطأ

