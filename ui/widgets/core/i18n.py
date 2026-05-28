"""
ui/widgets/core/i18n.py
================================
دالة tr() الموحدة للترجمة في الـ widgets.

الاستخدام:
    from ui.widgets.core.i18n import tr

    btn = make_btn(tr("إضافة"), "primary")
    lbl.setText(tr("الاسم"))
    msg = tr("هل تريد حذف «{name}»؟", name=item_name)

لو i18n غير مُفعّل أو حدث خطأ → يرجع النص الأصلي (fallback آمن).
"""


def tr(text: str, **kwargs) -> str:
    """
    يترجم النص للغة النشطة حالياً.

    Parameters
    ----------
    text : str
        النص العربي الأصلي — يُستخدم كـ key للترجمة وكـ fallback.
    **kwargs :
        قيم لتنسيق النص بعد الترجمة.
        مثال: tr("هل تريد حذف «{name}»؟", name="المنتج")

    Returns
    -------
    str
        النص المترجم، أو النص الأصلي لو الترجمة غير متاحة.

    أمثلة
    -----
        tr("إضافة")                                    # "Add" بالإنجليزية
        tr("أدخل {label}", label="الاسم")              # "Enter الاسم"
        tr("هل تريد حذف «{name}»؟", name="منتج A")    # "Delete «منتج A»?"
    """
    try:
        from ui.i18n import i18n_manager
        translated = i18n_manager.translate(text)
        # لو الترجمة مش موجودة (ترجع النص نفسه)، استخدم الـ fallback
        result = translated if translated else text
    except Exception:
        result = text

    if kwargs:
        try:
            result = result.format(**kwargs)
        except (KeyError, ValueError):
            # لو فشل الـ format، جرب على النص الأصلي
            try:
                result = text.format(**kwargs)
            except Exception:
                pass

    return result


def tr_plural(singular: str, plural: str, count: int, **kwargs) -> str:
    """
    يختار بين المفرد والجمع حسب العدد.

    مثال:
        tr_plural("{count} عنصر", "{count} عناصر", 5, count=5)
        # "5 عناصر"
    """
    text = singular if count == 1 else plural
    return tr(text, count=count, **kwargs)