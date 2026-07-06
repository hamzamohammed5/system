"""
ui/i18n/en_data/shared_items.py
==========================
Shared items, currency & units strings
جزء من تقسيم ui/i18n/en.py — راجع ui/i18n/en/__init__.py.
"""

EN_STRINGS_SHARED_ITEMS: dict[str, str] = {
    # ══════════════════════════════════════════════
    # Shared Items
    # ══════════════════════════════════════════════
    "shared_items":  "Shared Items",
    "publish":       "Publish",
    "published":     "Published",
    "not_published": "Not Published",

    # ══════════════════════════════════════════════
    # Currency & Units
    # ══════════════════════════════════════════════
    "currency_abbr":          "EGP",
    "currency_sym":           "EGP",           # short symbol for compact display
    "amount_fmt":             "{amount:.2f}  EGP",
    "amount_disc_fmt":        "{amount:.2f}  EGP  ({pct:.1f}%)",
    "currency":               "EGP",
    "currency_per_piece":     "EGP / piece",
    "currency_per_hour":      "EGP / hour",
    "currency_per_unit":      "EGP / unit",
    "piece":                  "piece",
    "minutes_abbr":           "min",

    "unit_label_px":          "px — pixel",
    "unit_label_mm":          "mm — millimeter",
    "unit_label_cm":          "cm — centimeter",
    "unit_label_m":           "m  — meter",
    "unit_label_inch":        "in — inch",

    "tree_node_arrow":        "↳ ",
    "arrow_right_icon":       "→",

}
