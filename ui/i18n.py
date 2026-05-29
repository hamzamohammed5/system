"""
ui/i18n.py
===========
نظام الترجمة للتطبيق — عربي وإنجليزي.

الاستخدام:
    from ui.i18n import tr, i18n_manager

    text = tr("save")
    text = tr("delete_confirm_msg", name="X")

    i18n_manager.set_language("en")
    i18n_manager.language_changed.connect(my_fn)

التغييرات:
  - [i18n] يستورد الآن من ui/i18n/ar.py و ui/i18n/en.py ويدمجهم مع
    الـ _TRANSLATIONS الداخلي — الملفات الخارجية لها الأولوية.
    هذا يسمح بتوسيع الترجمات بدون تعديل هذا الملف.
  - إضافة مفاتيح التحقق الناقصة:
      enter_field, select_field, field_positive, field_positive_enter
  - إضافة مفاتيح نصوص الـ panels الافتراضية:
      list_search_placeholder, detail_select_item
  - إضافة مفاتيح رسائل الأزرار الشائعة.
  - إضافة مفاتيح التصنيفات (category_*).
"""

from __future__ import annotations

from typing import Dict
from PyQt5.QtCore import QObject, pyqtSignal, Qt


# ══════════════════════════════════════════════════════════
# قاموس الترجمات الداخلي (fallback)
# ══════════════════════════════════════════════════════════

_TRANSLATIONS: Dict[str, Dict[str, str]] = {

    "ar": {
        # أزرار وإجراءات
        "save":              "حفظ",
        "save_edit":         "حفظ التعديل",
        "add":               "إضافة",
        "edit":              "تعديل",
        "delete":            "حذف",
        "cancel":            "إلغاء",
        "confirm":           "تأكيد",
        "close":             "إغلاق",
        "search":            "بحث",
        "reset":             "إعادة تعيين",
        "refresh":           "تحديث",
        "export":            "تصدير",
        "import":            "استيراد",
        "print":             "طباعة",
        "back":              "رجوع",
        "next":              "التالي",
        "previous":          "السابق",
        "yes":               "نعم",
        "no":                "لا",
        "ok":                "حسناً",
        "apply":             "تطبيق",
        "browse":            "تصفح",
        "select":            "اختيار",
        "clear":             "مسح",
        "copy":              "نسخ",
        "paste":             "لصق",
        "open":              "فتح",
        "new":               "جديد",
        # تنقل
        "nav_costing":       "حساب التكلفة",
        "nav_pricing":       "التسعير",
        "nav_accounting":    "الحسابات",
        "nav_inventory":     "المخزن",
        "nav_design":        "التصميمات",
        "nav_orders":        "الطلبات",
        "nav_shared":        "العناصر المشتركة",
        "nav_settings":      "الإعدادات",
        # إعدادات
        "settings":          "الإعدادات",
        "settings_font":     "حجم الخط",
        "settings_gimp":     "مسار GIMP",
        "settings_units":    "وحدات القياس",
        "settings_theme":    "المظهر",
        "settings_language": "اللغة",
        "theme_light":       "فاتح",
        "theme_dark":        "داكن",
        "lang_ar":           "العربية",
        "lang_en":           "English",
        "preview":           "معاينة",
        # حالات فارغة
        "no_data":              "لا توجد بيانات",
        "no_results":           "لا توجد نتائج",
        "no_search_results":    "جرب تغيير كلمة البحث أو الفلتر",
        "select_item_first":    "اختر عنصراً أولاً",
        "select_company":       "اختر شركة نشطة أولاً",
        # placeholder نصوص الـ panels
        "list_search_placeholder": "🔍  بحث...",
        "detail_select_item":      "اختر عنصراً من القائمة",
        # تأكيد
        "confirm_delete":       "تأكيد الحذف",
        "confirm_save":         "تأكيد الحفظ",
        "confirm_action":       "تأكيد",
        "delete_confirm_msg":   "هل تريد حذف «{name}»؟",
        "save_confirm_msg":     "تأكيد حفظ «{name}»؟",
        # نجاح/خطأ
        "success_add":          "تم الإضافة بنجاح",
        "success_save":         "تم الحفظ بنجاح",
        "success_delete":       "تم الحذف بنجاح",
        "error_load":           "خطأ في تحميل البيانات",
        "error_save":           "خطأ في الحفظ",
        "error_delete":         "خطأ في الحذف",
        "warning":              "تنبيه",
        "error":                "خطأ",
        "info":                 "معلومة",
        # رسائل التحقق من الحقول
        "enter_field":          "أدخل {label}",
        "select_field":         "اختر {label}",
        "field_positive":       "{label} يجب أن يكون أكبر من صفر",
        "field_positive_enter": "أدخل {label} أكبر من صفر",
        # حقول
        "name":                 "الاسم",
        "code":                 "الكود",
        "description":          "الوصف",
        "notes":                "ملاحظات",
        "date":                 "التاريخ",
        "amount":               "المبلغ",
        "price":                "السعر",
        "quantity":             "الكمية",
        "unit":                 "الوحدة",
        "category":             "التصنيف",
        "status":               "الحالة",
        "type":                 "النوع",
        "total":                "الإجمالي",
        "subtotal":             "المجموع الفرعي",
        "discount":             "الخصم",
        "tax":                  "الضريبة",
        # محاسبة
        "accounts":             "الحسابات",
        "journal_entries":      "القيود المحاسبية",
        "trial_balance":        "ميزان المراجعة",
        "income_statement":     "قائمة الدخل",
        "balance_sheet":        "الميزانية العمومية",
        "debit":                "مدين",
        "credit":               "دائن",
        "balance":              "الرصيد",
        "ref_no":               "رقم المرجع",
        # مخزن
        "inventory":            "المخزن",
        "stock_in":             "وارد",
        "stock_out":            "صادر",
        "current_stock":        "المخزون الحالي",
        # شركات
        "company":              "الشركة",
        "select_company_msg":   "اختر شركة للبدء",
        "no_company":           "لا توجد شركة نشطة",
        "manage_companies":     "إدارة الشركات",
        # تكلفة
        "cost":                 "التكلفة",
        "cost_per_unit":        "التكلفة للوحدة",
        "selling_price":        "سعر البيع",
        "profit_margin":        "هامش الربح",
        "waste":                "الهادر",
        "waste_pct":            "نسبة الهادر",
        # BOM
        "components":           "المكونات",
        "raw_material":         "خامة",
        "semi_product":         "نصف مصنع",
        "labor_op":             "عملية عمالة",
        "machine_op":           "عملية تشغيل",
        # فلاتر
        "filter_all":               "— الكل —",
        "filter_all_categories":    "— كل التصنيفات —",
        "date_from":                "من:",
        "date_to":                  "إلى:",
        "today":                    "اليوم",
        "this_month":               "الشهر",
        "this_year":                "العام",
        # شريط الحالة
        "showing_of":   "{shown} / {total}",
        "showing_all":  "{total}",
        # أزرار فورم
        "btn_add":      "➕  إضافة",
        "btn_save":     "💾  حفظ التعديل",
        "btn_cancel":   "✖  إلغاء",
        "btn_delete":   "🗑️  حذف",
        "btn_edit":     "✏️  تعديل",
        "btn_refresh":  "🔄  تحديث",
        # تصنيفات
        "category_data":         "بيانات التصنيف",
        "category_name":         "الاسم",
        "category_parent":       "تابع لـ",
        "category_color":        "اللون",
        "category_add":          "تصنيف جديد",
        "category_new":          "الأبناء",
        "category_edit":         "تعديل",
        "category_delete":       "حذف",
        "category_select_first": "اختر تصنيفاً أولاً",
        "category_name_required":"أدخل اسم التصنيف",
        # عمليات عامة
        "operation_add":        "إضافة",
        "operation_edit":       "تعديل",
        "operation_delete":     "حذف",
        "operation_save":       "حفظ",
        "operation_cancel":     "إلغاء",
        # تصميمات
        "designs":              "التصميمات",
        "design_add":           "إضافة تصميم",
        "design_categories":    "تصنيفات التصميم",
        "dimension_sets":       "مجموعات الأبعاد",
        # طلبات
        "orders":               "الطلبات",
        "order_add":            "إضافة طلب",
        "customers":            "العملاء",
        "customer_add":         "إضافة عميل",
        "order_status":         "حالة الطلب",
        "order_date":           "تاريخ الطلب",
        # تسعير
        "pricing":              "التسعير",
        "offers":               "العروض",
        "offer_add":            "إضافة عرض",
        # رسائل حذف مخصصة
        "delete_has_children":  "لا يمكن الحذف — يحتوي على عناصر فرعية",
        "delete_has_items":     "لا يمكن الحذف — مرتبط بعناصر أخرى",
        # شركات مشتركة
        "shared_items":         "العناصر المشتركة",
        "publish":              "نشر",
        "published":            "منشور",
        "not_published":        "غير منشور",
    },

    "en": {},  # سيُملأ من ui/i18n/en.py عند التهيئة
}

_LANGUAGE_DIRECTION: Dict[str, str] = {
    "ar": "rtl",
    "en": "ltr",
}

_LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    "ar": "العربية",
    "en": "English",
}


def _load_external_translations():
    """
    يحمّل الترجمات من ui/i18n/ar.py و ui/i18n/en.py ويدمجها.
    الملفات الخارجية لها الأولوية على الـ _TRANSLATIONS الداخلي.
    """
    # تحميل العربية من ar.py
    try:
        from ui.i18n.ar import AR_STRINGS
        _TRANSLATIONS["ar"].update(AR_STRINGS)
    except Exception:
        pass

    # تحميل الإنجليزية من en.py
    try:
        from ui.i18n.en import EN_STRINGS
        _TRANSLATIONS["en"].update(EN_STRINGS)
    except Exception:
        pass


# تحميل الترجمات الخارجية عند استيراد الملف
_load_external_translations()


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

    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._language: str = "ar"

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
        if lang not in _TRANSLATIONS:
            lang = "ar"
        if lang == self._language:
            return
        self._language = lang
        self._apply_direction()
        if save:
            self._save_to_db()
        self.language_changed.emit(lang)

    def translate(self, key: str, lang: str = None, **kwargs) -> str:
        target = lang or self._language
        text   = _TRANSLATIONS.get(target, {}).get(key)
        if text is None:
            # fallback للعربية
            text = _TRANSLATIONS["ar"].get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return text

    def load_from_db(self):
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

    def get_available_languages(self) -> list:
        return [
            {
                "code":   code,
                "name":   _LANGUAGE_DISPLAY_NAMES.get(code, code),
                "active": code == self._language,
                "is_rtl": _LANGUAGE_DIRECTION.get(code, "ltr") == "rtl",
            }
            for code in _TRANSLATIONS
        ]

    def add_translations(self, lang_code: str, translations: Dict[str, str]):
        """إضافة ترجمات جديدة أو تحديث موجودة."""
        if lang_code not in _TRANSLATIONS:
            _TRANSLATIONS[lang_code] = {}
        _TRANSLATIONS[lang_code].update(translations)

    # ── Internal ──────────────────────────────────────────

    def _apply_direction(self):
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
