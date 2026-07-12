"""
ui/theme_manager_data/_light_theme.py
==================================
تعريف ألوان الثيم الفاتح (Light — Warm Neutral).
جزء من تقسيم ui/theme_manager.py — راجع ui/theme_manager/__init__.py.
"""

from __future__ import annotations
from typing import Dict


# ══════════════════════════════════════════════════════════
# تعريف الثيمات — المصدر الوحيد للألوان
# ══════════════════════════════════════════════════════════

_LIGHT_THEME: Dict[str, str] = {
    "bg_page":      "#F5F4F0",
    "bg_surface":   "#FAFAF8",
    "bg_surface_2": "#F0EEE9",
    "bg_hover":     "#ECEAE4",
    "bg_active":    "#E4E2DA",
    "bg_input":     "#FFFFFF",
    "bg_input_focus": "#FFFFFF",
    "border":       "#DDD9CF",
    "border_med":   "#C8C4B8",
    "border_focus": "#8B8680",
    "border_strong":"#6B6760",
    "text_primary": "#1C1B18",
    "text_sec":     "#4A4843",
    "text_muted":   "#7A7870",
    "text_disabled":"#A8A69E",
    "text_state_neutral": "#888888",   # نص حالات محايدة (تحميل، تنبيه عام)
    "text_hint":    "#B0ADA5",
    "accent":       "#3D5A80",
    "accent_hover": "#2E4460",
    "accent_light": "#D6E4F0",
    "accent_mid":   "#98C1D9",
    "accent_text":  "#2A3F5A",
    "btn_primary_text": "#FFFFFF",
    "success_hover_bg": "#D4EDDF",
    "danger_hover_bg":  "#FCDBD9",
    "sidebar_bg":    "#EFEDE7",
    "sidebar_text":  "#1C1B18",
    "sidebar_muted": "#6B6760",
    "sidebar_hover": "#E4E2DA",
    "sidebar_active":"#D8D5CB",
    "sidebar_border":"#DDD9CF",
    "danger":        "#C0392B",
    "danger_strong": "#e53935",   # أحمر أعمق لأيقونات التحذير
    "danger_bg":     "#FDF0EF",
    "danger_border": "#E8A39D",
    "text_neutral":  "#555555",   # رمادي محايد للنصوص الثانوية
    "border_light":  "#cccccc",   # حد فاتح للفواصل
    "input_accent_border": "#c5cae9",  # حد حقل بحث indigo
    "row_alt_bg":    "#fafafa",   # خلفية صف متبادلة
    "row_alt_border":"#e8e8e8",   # حد صف متبادل
    "border_subtle": "#e0e0e0",   # حد خفيف جداً (بطاقات، فواصل رؤوس جداول)
    "table_gridline":"#f0f0f0",   # خطوط شبكة الجدول
    "scroll_warm_bg":"#fffaf5",   # خلفية scroll ذهبي فاتح
    "success":       "#2E7D52",
    "success_bg":    "#EDF7F2",
    "success_border":"#8EC5A8",
    "warning":       "#7A5C00",
    "warning_bg":    "#FDF8E7",
    "warning_border":"#D4B84A",
    "info":          "#1A5276",
    "info_bg":       "#EBF5FB",
    "info_border":   "#7FB3D3",
    "tab_active":    "#3D5A80",
    "tab_indicator": "#3D5A80",
    "purple":        "#6a1b9a",
    "purple_bg":     "#f3e5f5",
    "purple_border": "#ce93d8",
    "orange":        "#e65100",
    "orange_bg":     "#fff3e0",
    "orange_border": "#ffcc80",
    "blue":          "#1565c0",
    "blue_bg":       "#e3f2fd",
    "blue_border":   "#90caf9",
    "blue_hover":    "#1976d2",
    "blue_strong":   "#0d47a1",
    "teal":          "#0891b2",
    "teal_bg":       "#e0f7fa",
    "teal_border":   "#80deea",

    # ── Waste (نسبة الهادر) ──────────────────────────────
    "waste_zero_bg":         "#f5f5f5",
    "waste_zero_border":     "#e0e0e0",
    "waste_zero_color":      "#999999",
    # waste_text_color → يُستخدم _C['orange'] مباشرة

    # ── Waste levels ─────────────────────────────────────
    "waste_high_bg":         "#ffcdd2",
    "waste_high_border":     "#e53935",
    "waste_medium_bg":       "#ffe0b2",
    "waste_medium_border":   "#f57c00",
    "waste_low_bg":          "#fff8e1",
    "waste_low_border":      "#ffe082",

    # ── Input states ─────────────────────────────────────
    "input_error_bg":        "#fef2f2",
    "input_error_border":    "#f87171",
    "input_positive_bg":     "#f0fdf4",
    "input_positive_border": "#86efac",
    "input_positive_color":  "#15803d",

    # ── Card fallback ─────────────────────────────────────
    "card_fallback_bg":      "#f5f5f5",
    "card_fallback_border":  "#e0e0e0",

    # ── Accounting Journal ────────────────────────────────────
    # journal_dr_accent == badge_dr_text == acc_type_asset (#1565c0)
    # journal_cr_accent == badge_cr_text == acc_type_liability (#c62828)
    "journal_dr_bg":          "#f4f8ff",
    "journal_dr_border":      "#c5d8f7",
    "journal_dr_accent":      "#1565c0",   # == badge_dr_text == acc_type_asset
    "journal_cr_bg":          "#fff4f4",
    "journal_cr_border":      "#f7c5c5",
    "journal_cr_accent":      "#c62828",   # == badge_cr_text == acc_type_liability
    "journal_neutral_bg":     "#fafbff",
    "journal_neutral_border": "#dde3f0",
    "journal_header_bg":      "#f0f4ff",
    "journal_header_border":  "#c5cae9",
    # ── Investor ─────────────────────────────────────────────
    # investor_capital_text == acc_type_capital (#2e7d32)
    # investor_drawings_text == badge_cr_text == acc_type_liability (#c62828)
    # investor_drawings_bg == badge_cr_bg == t_account_cr_bg (#fdecea)
    "investor_capital_bg":    "#f1f8e9",
    "investor_capital_text":  "#2e7d32",   # == acc_type_capital
    "investor_drawings_bg":   "#fdecea",   # == badge_cr_bg == t_account_cr_bg
    "investor_drawings_text": "#c62828",   # == badge_cr_text == acc_type_liability
    "investor_link_bg":       "#fff8e1",
    "investor_link_border":   "#ffe082",
    "investor_link_text":     "#f57f17",
    # ── Audit Log — يعكس danger/warning/success مباشرة ──────
    # audit_delete_fg == danger,        audit_delete_bg == danger_bg
    # audit_update_fg == warning,       audit_update_bg == warning_bg
    # audit_create_fg == success,       audit_create_bg == success_bg
    "audit_delete_fg":        "#C0392B",   # == danger
    "audit_delete_bg":        "#FDF0EF",   # == danger_bg
    "audit_update_fg":        "#7A5C00",   # == warning
    "audit_update_bg":        "#FDF8E7",   # == warning_bg
    "audit_create_fg":        "#2E7D52",   # == success
    "audit_create_bg":        "#EDF7F2",   # == success_bg
    # ── T-Account ────────────────────────────────────────────
    # t_account_dr_bg == badge_dr_bg,  t_account_cr_bg == badge_cr_bg == investor_drawings_bg
    "t_account_dr_bg":        "#e3f2fd",   # == badge_dr_bg
    "t_account_cr_bg":        "#fdecea",   # == badge_cr_bg == investor_drawings_bg
    "t_account_frame":        "#c5cae9",
    # ── Badge ────────────────────────────────────────────────
    # badge_dr_text == journal_dr_accent == acc_type_asset
    # badge_cr_text == journal_cr_accent == acc_type_liability == investor_drawings_text
    "badge_dr_bg":            "#e3f2fd",   # == t_account_dr_bg
    "badge_dr_text":          "#1565c0",   # == journal_dr_accent == acc_type_asset
    "badge_cr_bg":            "#fdecea",   # == t_account_cr_bg == investor_drawings_bg
    "badge_cr_text":          "#c62828",   # == journal_cr_accent == acc_type_liability
    # ── Account type colors ──────────────────────────────────
    # acc_type_asset    == badge_dr_text == journal_dr_accent (#1565c0)
    # acc_type_liability== badge_cr_text == journal_cr_accent == investor_drawings_text (#c62828)
    # acc_type_capital  == investor_capital_text (#2e7d32)
    # acc_type_revenue  == purple (#6a1b9a)
    # acc_type_expense  == orange (#e65100)
    "acc_type_asset":         "#1565c0",
    "acc_type_liability":     "#c62828",
    "acc_type_capital":       "#2e7d32",
    "acc_type_revenue":       "#6a1b9a",
    "acc_type_expense":       "#e65100",
    "acc_type_drawings":      "#4e342e",
    # ── Separator / muted ────────────────────────────────────
    "text_separator":         "#78909c",
    "group_label_text":       "#546e7a",   # نص رأس المجموعة في الأشجار/القوائم (popup، tree)
    
    # ── Shared / Published items ──────────────────────────────
    "shared_item_fg":      "#6a1b9a",   # نص العنصر المشترك
    "shared_item_bg":      "#f3e5f5",   # خلفية صف العنصر المشترك
    "published_item_fg":   "#0891b2",   # نص العنصر المنشور محلياً
    "published_item_bg":   "#e0f7fa",   # خلفية صف العنصر المنشور
    
    # ── Inventory Stock Levels ────────────────────────────────
    "stock_critical_fg":   "#c62828",   # صفر مخزون (نص)
    "stock_low_fg":        "#e65100",   # تحت الحد الأدنى (نص)
    "stock_ok_fg":         "#2e7d32",   # مخزون كافٍ (نص)

    # ── Action button hover variants ──────────────────────────
    "success_hover":       "#1b5e38",
    "danger_hover":        "#ffcdd2",
    "warning_hover":       "#ffecb3",
    "orange_hover":        "#bf360c",

    # ── Design Module ───────────────────────────────────────────
    "design_thumb_bg":          "#E9ECF7",   # خلفية الـ thumbnail في بطاقات التصميم
    "design_thumb_bg_start":    "#F0F1FA",   # بداية تدرج placeholder الـ XCF
    "design_thumb_bg_end":      "#E3E6F5",   # نهاية تدرج placeholder الـ XCF
    "design_thumb_border":      "#B8C0E8",   # حد إطار placeholder الـ XCF
    "design_thumb_icon":        "#6C7BC4",   # أيقونة 🎨 في placeholder
    "design_thumb_text":        "#7178A0",   # اسم الملف في placeholder
    "card_badge_text":          "#FFFFFF",   # نص badge العدد فوق الـ thumbnail الداكن
    "card_badge_bg":            "rgba(0,0,0,0.55)",      # خلفية badge العدد فوق الـ thumbnail
    "card_badge_border":        "rgba(255,255,255,0.2)", # حد badge العدد فوق الـ thumbnail

    # ── BOM Tree — Scenario node ──────────────────────────────
    "bom_scenario_default_bg":  "#e8f5e9",   # خلفية node السيناريو الافتراضي
    "bom_scenario_default_fg":  "#1b5e20",   # نص node السيناريو الافتراضي
    "bom_scenario_normal_bg":   "#e3f2fd",   # == blue_bg — خلفية node سيناريو عادي
    "bom_scenario_normal_fg":   "#0d47a1",   # نص node سيناريو عادي

    "overlay_bg":               "rgba(255,255,255,180)",   # خلفية شفافة لطبقة LoadingOverlay

    # ── Dialog Shell header ───────────────────────────────
    "dialog_hdr_sub_text":      "rgba(255,255,255,0.8)",  # نص الـ subtitle في header النافذة
    # ── ColorPickerWidget ────────────────────────────────
    "color_picker_default":     "#607d8b",   # اللون الافتراضي لـ ColorPickerWidget

    # ── Icon button ───────────────────────────────────────
    "icon_btn_color":           "#7A7870",   # == text_muted — لون أيقونة زر الـ icon افتراضي
    "icon_btn_hover_color":     "#e53935",   # == danger_strong — لون hover لزر الأيقونة
}
