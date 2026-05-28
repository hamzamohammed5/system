"""
ui/i18n.py
===========
نظام الترجمة الكامل للتطبيق.

يدعم:
  - عربي (RTL) — الافتراضي
  - إنجليزي (LTR)
  - قابل للتوسع بأي لغة إضافية

الاستخدام:
    from ui.i18n import tr, i18n_manager

    # ترجمة نص
    text = tr("save")          # "حفظ" أو "Save"
    text = tr("save", "ar")    # "حفظ" دايماً

    # تبديل اللغة
    i18n_manager.set_language("en")

    # الاشتراك في التغييرات
    i18n_manager.language_changed.connect(my_fn)

    # معرفة الاتجاه
    is_rtl = i18n_manager.is_rtl   # True للعربي

التنظيم:
  - النصوص مقسّمة لأقسام (common, actions, nav, messages, ...)
  - المفتاح دايماً بالإنجليزي (snake_case)
  - الـ fallback دايماً للعربي لو المفتاح مش موجود
"""

from __future__ import annotations

from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, Qt


# ══════════════════════════════════════════════════════════
# قاموس الترجمات
# ══════════════════════════════════════════════════════════

_TRANSLATIONS: Dict[str, Dict[str, str]] = {

    # ── اللغة العربية ─────────────────────────────────────
    "ar": {

        # ─ أزرار وإجراءات شائعة ─
        "save":           "حفظ",
        "save_edit":      "حفظ التعديل",
        "add":            "إضافة",
        "edit":           "تعديل",
        "delete":         "حذف",
        "cancel":         "إلغاء",
        "confirm":        "تأكيد",
        "close":          "إغلاق",
        "search":         "بحث",
        "reset":          "إعادة تعيين",
        "refresh":        "تحديث",
        "export":         "تصدير",
        "import":         "استيراد",
        "print":          "طباعة",
        "back":           "رجوع",
        "next":           "التالي",
        "previous":       "السابق",
        "yes":            "نعم",
        "no":             "لا",
        "ok":             "حسناً",
        "apply":          "تطبيق",
        "browse":         "تصفح",
        "select":         "اختيار",
        "clear":          "مسح",
        "copy":           "نسخ",
        "paste":          "لصق",
        "open":           "فتح",
        "new":            "جديد",

        # ─ تنقل ─
        "nav_costing":    "حساب التكلفة",
        "nav_pricing":    "التسعير",
        "nav_accounting": "الحسابات",
        "nav_inventory":  "المخزن",
        "nav_design":     "التصميمات",
        "nav_orders":     "الطلبات",
        "nav_shared":     "العناصر المشتركة",
        "nav_settings":   "الإعدادات",

        # ─ إعدادات ─
        "settings":         "الإعدادات",
        "settings_font":    "حجم الخط",
        "settings_gimp":    "مسار GIMP",
        "settings_units":   "وحدات القياس",
        "settings_theme":   "المظهر",
        "settings_language":"اللغة",
        "theme_light":      "فاتح",
        "theme_dark":       "داكن",
        "theme_custom":     "مخصص",
        "lang_ar":          "العربية",
        "lang_en":          "English",
        "preview":          "معاينة",

        # ─ حالات فارغة ─
        "no_data":          "لا توجد بيانات",
        "no_results":       "لا توجد نتائج",
        "no_search_results":"جرب تغيير كلمة البحث أو الفلتر",
        "select_item_first":"اختر عنصراً أولاً",
        "select_company":   "اختر شركة نشطة أولاً",

        # ─ رسائل تأكيد ─
        "confirm_delete":   "تأكيد الحذف",
        "confirm_save":     "تأكيد الحفظ",
        "confirm_action":   "تأكيد",
        "delete_confirm_msg":"هل تريد حذف «{name}»؟",
        "save_confirm_msg": "تأكيد حفظ «{name}»؟",

        # ─ رسائل نجاح/خطأ ─
        "success_add":      "تم الإضافة بنجاح",
        "success_save":     "تم الحفظ بنجاح",
        "success_delete":   "تم الحذف بنجاح",
        "error_load":       "خطأ في تحميل البيانات",
        "error_save":       "خطأ في الحفظ",
        "error_delete":     "خطأ في الحذف",
        "warning":          "تنبيه",
        "error":            "خطأ",
        "info":             "معلومة",

        # ─ حقول بيانات شائعة ─
        "name":             "الاسم",
        "code":             "الكود",
        "description":      "الوصف",
        "notes":            "ملاحظات",
        "date":             "التاريخ",
        "amount":           "المبلغ",
        "price":            "السعر",
        "quantity":         "الكمية",
        "unit":             "الوحدة",
        "category":         "التصنيف",
        "status":           "الحالة",
        "type":             "النوع",
        "total":            "الإجمالي",
        "subtotal":         "المجموع الفرعي",
        "discount":         "الخصم",
        "tax":              "الضريبة",

        # ─ محاسبة ─
        "accounts":         "الحسابات",
        "journal_entries":  "القيود المحاسبية",
        "trial_balance":    "ميزان المراجعة",
        "income_statement": "قائمة الدخل",
        "balance_sheet":    "الميزانية العمومية",
        "debit":            "مدين",
        "credit":           "دائن",
        "balance":          "الرصيد",
        "ref_no":           "رقم المرجع",

        # ─ مخزن ─
        "inventory":        "المخزن",
        "stock_in":         "وارد",
        "stock_out":        "صادر",
        "current_stock":    "المخزون الحالي",

        # ─ شركات ─
        "company":          "الشركة",
        "select_company_msg":"اختر شركة للبدء",
        "no_company":       "لا توجد شركة نشطة",
        "manage_companies": "إدارة الشركات",

        # ─ تكلفة وتسعير ─
        "cost":             "التكلفة",
        "cost_per_unit":    "التكلفة للوحدة",
        "selling_price":    "سعر البيع",
        "profit_margin":    "هامش الربح",
        "waste":            "الهادر",
        "waste_pct":        "نسبة الهادر",

        # ─ BOM ─
        "components":       "المكونات",
        "raw_material":     "خامة",
        "semi_product":     "نصف مصنع",
        "labor_op":         "عملية عمالة",
        "machine_op":       "عملية تشغيل",

        # ─ شريط الحالة ─
        "showing_of":       "{shown} / {total}",
        "showing_all":      "{total}",

        # ─ فلاتر ─
        "filter_all":       "— الكل —",
        "filter_all_categories": "— كل التصنيفات —",
        "date_from":        "من:",
        "date_to":          "إلى:",
        "today":            "اليوم",
        "this_month":       "الشهر",
        "this_year":        "العام",
    },

    # ── اللغة الإنجليزية ──────────────────────────────────
    "en": {

        # ─ أزرار وإجراءات شائعة ─
        "save":           "Save",
        "save_edit":      "Save Changes",
        "add":            "Add",
        "edit":           "Edit",
        "delete":         "Delete",
        "cancel":         "Cancel",
        "confirm":        "Confirm",
        "close":          "Close",
        "search":         "Search",
        "reset":          "Reset",
        "refresh":        "Refresh",
        "export":         "Export",
        "import":         "Import",
        "print":          "Print",
        "back":           "Back",
        "next":           "Next",
        "previous":       "Previous",
        "yes":            "Yes",
        "no":             "No",
        "ok":             "OK",
        "apply":          "Apply",
        "browse":         "Browse",
        "select":         "Select",
        "clear":          "Clear",
        "copy":           "Copy",
        "paste":          "Paste",
        "open":           "Open",
        "new":            "New",

        # ─ تنقل ─
        "nav_costing":    "Costing",
        "nav_pricing":    "Pricing",
        "nav_accounting": "Accounting",
        "nav_inventory":  "Inventory",
        "nav_design":     "Designs",
        "nav_orders":     "Orders",
        "nav_shared":     "Shared Items",
        "nav_settings":   "Settings",

        # ─ إعدادات ─
        "settings":          "Settings",
        "settings_font":     "Font Size",
        "settings_gimp":     "GIMP Path",
        "settings_units":    "Measurement Units",
        "settings_theme":    "Appearance",
        "settings_language": "Language",
        "theme_light":       "Light",
        "theme_dark":        "Dark",
        "theme_custom":      "Custom",
        "lang_ar":           "العربية",
        "lang_en":           "English",
        "preview":           "Preview",

        # ─ حالات فارغة ─
        "no_data":           "No Data",
        "no_results":        "No Results",
        "no_search_results": "Try changing the search term or filter",
        "select_item_first": "Select an item first",
        "select_company":    "Please select an active company first",

        # ─ رسائل تأكيد ─
        "confirm_delete":    "Confirm Delete",
        "confirm_save":      "Confirm Save",
        "confirm_action":    "Confirm",
        "delete_confirm_msg":"Delete «{name}»?",
        "save_confirm_msg":  "Save «{name}»?",

        # ─ رسائل نجاح/خطأ ─
        "success_add":       "Added successfully",
        "success_save":      "Saved successfully",
        "success_delete":    "Deleted successfully",
        "error_load":        "Error loading data",
        "error_save":        "Error saving",
        "error_delete":      "Error deleting",
        "warning":           "Warning",
        "error":             "Error",
        "info":              "Info",

        # ─ حقول بيانات شائعة ─
        "name":              "Name",
        "code":              "Code",
        "description":       "Description",
        "notes":             "Notes",
        "date":              "Date",
        "amount":            "Amount",
        "price":             "Price",
        "quantity":          "Quantity",
        "unit":              "Unit",
        "category":          "Category",
        "status":            "Status",
        "type":              "Type",
        "total":             "Total",
        "subtotal":          "Subtotal",
        "discount":          "Discount",
        "tax":               "Tax",

        # ─ محاسبة ─
        "accounts":          "Accounts",
        "journal_entries":   "Journal Entries",
        "trial_balance":     "Trial Balance",
        "income_statement":  "Income Statement",
        "balance_sheet":     "Balance Sheet",
        "debit":             "Debit",
        "credit":            "Credit",
        "balance":           "Balance",
        "ref_no":            "Reference No.",

        # ─ مخزن ─
        "inventory":         "Inventory",
        "stock_in":          "In",
        "stock_out":         "Out",
        "current_stock":     "Current Stock",

        # ─ شركات ─
        "company":           "Company",
        "select_company_msg":"Select a company to start",
        "no_company":        "No active company",
        "manage_companies":  "Manage Companies",

        # ─ تكلفة وتسعير ─
        "cost":              "Cost",
        "cost_per_unit":     "Cost per Unit",
        "selling_price":     "Selling Price",
        "profit_margin":     "Profit Margin",
        "waste":             "Waste",
        "waste_pct":         "Waste %",

        # ─ BOM ─
        "components":        "Components",
        "raw_material":      "Raw Material",
        "semi_product":      "Semi-Product",
        "labor_op":          "Labor Operation",
        "machine_op":        "Machine Operation",

        # ─ شريط الحالة ─
        "showing_of":        "{shown} / {total}",
        "showing_all":       "{total}",

        # ─ فلاتر ─
        "filter_all":             "— All —",
        "filter_all_categories":  "— All Categories —",
        "date_from":         "From:",
        "date_to":           "To:",
        "today":             "Today",
        "this_month":        "Month",
        "this_year":         "Year",
    },
}

# اتجاه كل لغة
_LANGUAGE_DIRECTION: Dict[str, str] = {
    "ar": "rtl",
    "en": "ltr",
}

# اسم عرض كل لغة
_LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    "ar": "العربية",
    "en": "English",
}


# ══════════════════════════════════════════════════════════
# I18nManager
# ══════════════════════════════════════════════════════════

class I18nManager(QObject):
    """
    Singleton يدير لغة التطبيق.

    الاستخدام:
        from ui.i18n import i18n_manager, tr

        i18n_manager.set_language("en")
        text = tr("save")   # "Save"
    """

    language_changed = pyqtSignal(str)  # اسم اللغة الجديدة

    def __init__(self):
        super().__init__()
        self._language: str = "ar"

    # ── API العام ──────────────────────────────────────────

    @property
    def language(self) -> str:
        return self._language

    @property
    def is_rtl(self) -> bool:
        return _LANGUAGE_DIRECTION.get(self._language, "rtl") == "rtl"

    @property
    def qt_direction(self) -> Qt.LayoutDirection:
        return Qt.RightToLeft if self.is_rtl else Qt.LeftToRight

    def set_language(self, lang: str, save: bool = True):
        """
        يبدّل اللغة فوراً.
        lang: "ar" | "en"
        """
        if lang not in _TRANSLATIONS:
            lang = "ar"

        if lang == self._language:
            return

        self._language = lang

        # تحديث اتجاه التطبيق
        self._apply_direction()

        if save:
            self._save_to_db()

        self.language_changed.emit(lang)

    def translate(self, key: str, lang: str = None,
                  **kwargs) -> str:
        """
        يترجم مفتاحاً معيناً.

        key:    مفتاح النص (snake_case)
        lang:   اللغة (None = اللغة الحالية)
        kwargs: قيم للتعويض في النص ({name}, {count}, ...)

        مثال:
            translate("delete_confirm_msg", name="منتج A")
            # → "هل تريد حذف «منتج A»؟"
        """
        target_lang = lang or self._language
        dict_       = _TRANSLATIONS.get(target_lang, _TRANSLATIONS["ar"])
        text        = dict_.get(key)

        # Fallback للعربي لو المفتاح مش موجود
        if text is None:
            text = _TRANSLATIONS["ar"].get(key, key)

        # تعويض المتغيرات
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return text

    def get_available_languages(self) -> list[dict]:
        """يرجع قائمة اللغات المتاحة."""
        return [
            {
                "code":    code,
                "name":    _LANGUAGE_DISPLAY_NAMES.get(code, code),
                "active":  code == self._language,
                "is_rtl":  _LANGUAGE_DIRECTION.get(code, "ltr") == "rtl",
            }
            for code in _TRANSLATIONS.keys()
        ]

    def add_language(self, lang_code: str, display_name: str,
                     translations: Dict[str, str], rtl: bool = False):
        """
        يضيف لغة جديدة للنظام.

        مثال:
            i18n_manager.add_language(
                "fr", "Français",
                {"save": "Enregistrer", "cancel": "Annuler"},
                rtl=False
            )
        """
        _TRANSLATIONS[lang_code]        = translations
        _LANGUAGE_DISPLAY_NAMES[lang_code] = display_name
        _LANGUAGE_DIRECTION[lang_code]  = "rtl" if rtl else "ltr"

    def add_translations(self, lang_code: str, translations: Dict[str, str]):
        """
        يضيف/يحدّث ترجمات لـ لغة موجودة.
        مفيد للـ plugins أو الـ modules الإضافية.
        """
        if lang_code not in _TRANSLATIONS:
            _TRANSLATIONS[lang_code] = {}
        _TRANSLATIONS[lang_code].update(translations)

    # ── تحميل من DB ───────────────────────────────────────

    def load_from_db(self):
        """يحمّل اللغة المحفوظة من DB."""
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import get_setting
            conn = get_connection()
            lang = get_setting(conn, "ui_language", "ar")
            if lang in _TRANSLATIONS:
                self._language = lang
            self._apply_direction()
        except Exception:
            pass

    # ── Internal ──────────────────────────────────────────

    def _apply_direction(self):
        """يطبّق اتجاه اللغة على التطبيق."""
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setLayoutDirection(self.qt_direction)
        except Exception:
            pass

    def _save_to_db(self):
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import set_setting
            conn = get_connection()
            set_setting(conn, "ui_language", self._language)
        except Exception:
            pass


# ── Singletons ────────────────────────────────────────────
i18n_manager = I18nManager()


def tr(key: str, lang: str = None, **kwargs) -> str:
    """
    دالة ترجمة سريعة.

    مثال:
        from ui.i18n import tr

        btn.setText(tr("save"))
        lbl.setText(tr("delete_confirm_msg", name="المنتج"))
    """
    return i18n_manager.translate(key, lang, **kwargs)