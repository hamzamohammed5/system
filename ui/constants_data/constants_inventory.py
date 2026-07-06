"""
ui/constants_data/inventory.py
=========================
ثوابت قسم المخزون
جزء من تقسيم ui/constants.py — راجع ui/constants/__init__.py.
"""

# ── Inventory Tabs (items, inbound, outbound, report) ──────
INVENTORY_SPIN_MAX          = 999999999  # الحد الأقصى للـ QDoubleSpinBox في تبويبات المخزون
INVENTORY_SPIN_DEC          = 4          # خانات عشرية افتراضية للـ spin في تبويبات المخزون
INVENTORY_INPUT_MIN_H       = 30         # ارتفاع أدنى لحقول الإدخال الرئيسية (QLineEdit, QDoubleSpinBox)
INVENTORY_CMB_MIN_H         = 28         # ارتفاع أدنى لـ QComboBox في تبويبات المخزون
INVENTORY_UNIT_W            = 120        # عرض ثابت لحقل الوحدة وحقل الحد الأدنى
INVENTORY_DATE_W            = 130        # عرض ثابت لـ QDateEdit في تبويبات المخزون
INVENTORY_SAVE_BTN_H        = 36         # ارتفاع زر الحفظ الرئيسي (وارد/صادر)
INVENTORY_ITEM_MIN_W        = 220        # عرض أدنى لـ cmb_item في تبويب الوارد
INVENTORY_GRP_BORDER_RADIUS = 8          # border-radius لـ QGroupBox في تبويبات المخزون
INVENTORY_GRP_MARGIN_TOP    = 8          # margin-top لـ QGroupBox في تبويبات المخزون
INVENTORY_GRP_PAD_TOP       = 8          # padding-top لـ QGroupBox في تبويبات المخزون
INVENTORY_GRP_TITLE_PAD_H   = 6          # padding أفقي لعنوان QGroupBox في تبويبات المخزون
INVENTORY_SAVE_BTN_RADIUS   = 6          # border-radius لزر الحفظ الرئيسي
INVENTORY_SAVE_BTN_PAD_H    = 18         # padding أفقي لزر الحفظ الرئيسي
INVENTORY_COL_MAX_W         = 150        # max_width في auto_fit_columns لجداول المخزون
INVENTORY_CARD_BORDER_L     = 4          # عرض border-left لبطاقات الإحصاء في تقرير المخزون
INVENTORY_ITEMS_SPLITTER_HANDLE_W = 6    # handleWidth لـ QSplitter في _ItemsTab
INVENTORY_ITEMS_SPLITTER_FORM_SIZE  = 320  # حجم لوحة الفورم الابتدائي في splitter _ItemsTab
INVENTORY_ITEMS_SPLITTER_TABLE_SIZE = 580  # حجم لوحة الجدول الابتدائي في splitter _ItemsTab
INVENTORY_ITEMS_TABLE_ROOT_MARGIN = (12, 8, 12, 12)  # contentsMargins الـ root layout لـ _ItemsTable

