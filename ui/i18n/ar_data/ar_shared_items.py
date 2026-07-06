"""
ui/i18n/ar_data/shared_items.py
==========================
نصوص العناصر المشتركة والعملة والوحدات
جزء من تقسيم ui/i18n/ar.py — راجع ui/i18n/ar/__init__.py.
"""

AR_STRINGS_SHARED_ITEMS: dict[str, str] = {
    # ══════════════════════════════════════════════
    # عناصر مشتركة
    # ══════════════════════════════════════════════
    "shared_items":  "العناصر المشتركة",
    "publish":       "نشر",
    "published":     "منشور",
    "not_published": "غير منشور",

    # ══════════════════════════════════════════════
    # العملة والوحدات
    # ══════════════════════════════════════════════
    "currency_abbr":          "جنيه",
    "currency_sym":           "ج",   # اختصار الجنيه للعرض المضغوط
    "amount_fmt":             "{amount:.2f}  ج",     # تنسيق المبلغ
    "amount_disc_fmt":        "{amount:.2f}  ج  ({pct:.1f}%)",  # مبلغ + نسبة خصم
    "currency":               "جنيه",
    "currency_per_piece":     "جنيه / قطعة",
    "currency_per_hour":      "جنيه / ساعة",
    "currency_per_unit":      "جنيه / وحدة",
    "piece":                  "قطعة",
    "minutes_abbr":           "د",

    "unit_label_px":          "px — بكسل",
    "unit_label_mm":          "mm — مليمتر",
    "unit_label_cm":          "cm — سنتيمتر",
    "unit_label_m":           "m  — متر",
    "unit_label_inch":        "inch — بوصة",

    "tree_node_arrow":        "↳ ",
    "arrow_right_icon":       "→",

}
