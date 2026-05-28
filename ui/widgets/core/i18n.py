"""
ui/widgets/core/i18n.py
================================
دالة tr() الموحدة للترجمة في الـ widgets.

الاستخدام:
    from ui.widgets.core.i18n import tr

    btn = make_btn(tr("save"), "primary")
    lbl.setText(tr("name"))
    msg = tr("delete_confirm_msg", name=item_name)

    # النص العربي المباشر كـ fallback:
    btn = make_btn(tr("إضافة", fallback="إضافة"), "primary")

لو i18n غير مُفعّل أو حدث خطأ → يرجع النص الأصلي (fallback آمن).

ملاحظة:
    tr() تقبل نوعين من الـ keys:
    1. key قصير مثل "save" أو "delete" → يبحث في قاموس _TRANSLATIONS
    2. نص عربي مباشر مثل "إضافة" → يُستخدم كـ fallback لو مفيش ترجمة
"""

from __future__ import annotations


# ── الـ key map: نص عربي مباشر → translation key ─────────────────────────
# يسمح بكتابة tr("إضافة") بدل tr("add") في الكود القديم
_AR_TO_KEY: dict[str, str] = {
    # أزرار وإجراءات
    "إضافة":            "add",
    "حفظ":              "save",
    "حفظ التعديل":      "save_edit",
    "تعديل":            "edit",
    "حذف":              "delete",
    "إلغاء":            "cancel",
    "تأكيد":            "confirm",
    "إغلاق":            "close",
    "بحث":              "search",
    "إعادة تعيين":      "reset",
    "تحديث":            "refresh",
    "تصدير":            "export",
    "استيراد":          "import",
    "طباعة":            "print",
    "رجوع":             "back",
    "التالي":           "next",
    "السابق":           "previous",
    "نعم":              "yes",
    "لا":               "no",
    "حسناً":            "ok",
    "تطبيق":            "apply",
    "مسح":              "clear",
    "جديد":             "new",
    # حالات فارغة
    "لا توجد بيانات":           "no_data",
    "لا توجد نتائج":            "no_results",
    "اختر عنصراً أولاً":        "select_item_first",
    # تأكيد
    "تأكيد الحذف":              "confirm_delete",
    "تأكيد الحفظ":              "confirm_save",
    # نجاح/خطأ
    "تم الإضافة بنجاح":         "success_add",
    "تم الحفظ بنجاح":           "success_save",
    "تم الحذف بنجاح":           "success_delete",
    "خطأ في تحميل البيانات":    "error_load",
    "خطأ في الحفظ":             "error_save",
    "خطأ في الحذف":             "error_delete",
    "تنبيه":                    "warning",
    "خطأ":                      "error",
    "معلومة":                   "info",
    # حقول
    "الاسم":            "name",
    "الكود":            "code",
    "الوصف":            "description",
    "ملاحظات":          "notes",
    "التاريخ":          "date",
    "المبلغ":           "amount",
    "السعر":            "price",
    "الكمية":           "quantity",
    "الوحدة":           "unit",
    "التصنيف":          "category",
    "الحالة":           "status",
    "النوع":            "type",
    "الإجمالي":         "total",
    # محاسبة
    "مدين":             "debit",
    "دائن":             "credit",
    "الرصيد":           "balance",
    # فلاتر
    "اليوم":            "today",
    "الشهر":            "this_month",
    "العام":            "this_year",
}

# ── رسائل بـ format placeholders ──────────────────────────────────────────
_FORMAT_KEYS: dict[str, str] = {
    "هل تريد حذف «{name}»؟":       "delete_confirm_msg",
    "تأكيد حفظ «{name}»؟":          "save_confirm_msg",
    "أدخل {label}":                  "enter_field",
    "اختر {label}":                  "select_field",
    "{label} يجب أن يكون أكبر من صفر": "field_positive",
    "أدخل {label} أكبر من صفر":      "field_positive_enter",
}

# ── قاموس إضافي للرسائل غير الموجودة في i18n.py ──────────────────────────
_EXTRA_EN: dict[str, str] = {
    "enter_field":          "Enter {label}",
    "select_field":         "Select {label}",
    "field_positive":       "{label} must be greater than zero",
    "field_positive_enter": "Enter {label} greater than zero",
}


def tr(text: str, fallback: str = "", **kwargs) -> str:
    """
    يترجم النص للغة النشطة حالياً.

    Parameters
    ----------
    text : str
        إما translation key (مثل "save") أو نص عربي مباشر (مثل "حفظ").
    fallback : str
        النص الافتراضي لو لم تُوجد ترجمة. لو فارغ → يُستخدم text.
    **kwargs :
        قيم لتنسيق النص بعد الترجمة.
        مثال: tr("delete_confirm_msg", name="المنتج")

    Returns
    -------
    str
        النص المترجم، أو النص الأصلي لو الترجمة غير متاحة.

    أمثلة
    -----
        tr("save")                            # "Save" بالإنجليزية
        tr("حفظ")                             # "Save" بالإنجليزية (auto-map)
        tr("delete_confirm_msg", name="X")    # "Delete «X»?"
        tr("أدخل {label}", label="الاسم")    # "Enter الاسم"
    """
    result = _translate(text, fallback)

    if kwargs:
        try:
            result = result.format(**kwargs)
        except (KeyError, ValueError):
            # لو فشل الـ format على المترجم، جرب على النص الأصلي
            try:
                result = (fallback or text).format(**kwargs)
            except Exception:
                pass

    return result


def _translate(text: str, fallback: str = "") -> str:
    """
    البحث عن الترجمة بالترتيب:
    1. النص كـ key مباشر في i18n_manager
    2. النص كـ Arabic text → map إلى key
    3. البحث في format keys
    4. البحث في _EXTRA_EN
    5. Fallback
    """
    _fb = fallback or text

    try:
        from ui.i18n import i18n_manager

        # لو اللغة عربية → أعد النص العربي مباشرة
        if i18n_manager.language == "ar":
            return _fb

        # 1. النص كـ key مباشر (مثل "save", "delete")
        translated = i18n_manager.translate(text)
        if translated and translated != text:
            return translated

        # 2. النص العربي → map إلى key
        key = _AR_TO_KEY.get(text)
        if key:
            translated = i18n_manager.translate(key)
            if translated and translated != key:
                return translated

        # 3. البحث في format keys (بالنص بدون format)
        format_key = _FORMAT_KEYS.get(text)
        if format_key:
            # جرب من i18n_manager أولاً
            translated = i18n_manager.translate(format_key)
            if translated and translated != format_key:
                return translated
            # جرب من _EXTRA_EN
            if format_key in _EXTRA_EN:
                return _EXTRA_EN[format_key]

        # 4. البحث في _EXTRA_EN مباشرة
        if text in _EXTRA_EN:
            return _EXTRA_EN[text]

    except Exception:
        pass

    return _fb


def tr_plural(singular: str, plural: str, count: int, **kwargs) -> str:
    """
    يختار بين المفرد والجمع حسب العدد.

    مثال:
        tr_plural("{count} عنصر", "{count} عناصر", 5, count=5)
        # "5 عناصر" (أو "5 items" بالإنجليزية)
    """
    text = singular if count == 1 else plural
    return tr(text, count=count, **kwargs)