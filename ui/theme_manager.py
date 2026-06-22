"""
ui/theme_manager.py
====================
نظام الثيمات الكامل للتطبيق — المصدر الوحيد لكل الألوان.

[نُقل من ui/themes/theme_manager.py]

يدعم:
  - Light (الافتراضي — Warm Neutral)
  - Dark

هذا الملف هو **المصدر الوحيد** لتعريف الألوان.
ui/theme.py يستورد _LIGHT_THEME منه لملء _C الافتراضي.

[تحديث] نُقلت إليه الألوان التالية من colors.py:
  - ألوان الهادر (waste_high/medium/low) لكل ثيم
  - ألوان الـ fallback للبطاقات (card_fallback_bg/border)
  colors.py لم يعد يحتوي على أي ألوان hardcoded — كل شيء يُقرأ من _C.

[تحديث 2] إضافة CARD_PALETTES — lookup tables لألوان البطاقات حسب الثيم.
  نُقلت من colors.py (CARD_PALETTE و _DARK_CARD_PALETTE) لضمان أن
  المصدر الوحيد لكل الألوان هو هذا الملف.

[دمج events] المصدر الوحيد للـ bus هو ui.widgets.core.events.
  الجديد: from ui.widgets.core.events import bus

الاستخدام:
    from ui.theme_manager import theme_manager

    theme_manager.set_theme("dark")
    current = theme_manager.current_theme   # "dark"

    theme_manager.theme_changed.connect(my_fn)
    # أو عبر bus:
    from ui.widgets.core.events import bus
    bus.theme_changed.connect(my_fn)
"""

from __future__ import annotations

from typing import Dict
from PyQt5.QtCore import QObject, pyqtSignal


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
    "sidebar_bg":    "#1E1D1A",
    "sidebar_text":  "#E8E6E1",
    "sidebar_muted": "#7A7870",
    "sidebar_hover": "#2E2D2A",
    "sidebar_active":"#3A3835",
    "sidebar_border":"#2E2D2A",
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
    "design_thumb_bg":          "#1E1B4B",   # خلفية الـ thumbnail في بطاقات التصميم
    "design_thumb_bg_start":    "#2d2d5e",   # بداية تدرج placeholder الـ XCF
    "design_thumb_bg_end":      "#1a1a2e",   # نهاية تدرج placeholder الـ XCF
    "design_thumb_border":      "#5c6bc0",   # حد إطار placeholder الـ XCF
    "design_thumb_icon":        "#7986cb",   # أيقونة 🎨 في placeholder
    "design_thumb_text":        "#9fa8da",   # اسم الملف في placeholder
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
}

_DARK_THEME: Dict[str, str] = {
    "bg_page":      "#0F0F0F",
    "bg_surface":   "#1A1A1A",
    "bg_surface_2": "#242424",
    "bg_hover":     "#2E2E2E",
    "bg_active":    "#383838",
    "bg_input":     "#1E1E1E",
    "bg_input_focus": "#242424",
    "border":       "#2E2E2E",
    "border_med":   "#3A3A3A",
    "border_focus": "#5A5A5A",
    "border_strong":"#6E6E6E",
    "text_primary": "#E8E6E1",
    "text_sec":     "#B8B5AE",
    "text_muted":   "#7A7870",
    "text_disabled":"#4A4843",
    "text_state_neutral": "#9A9890",   # نص حالات محايدة (dark)
    "text_hint":    "#5A5850",
    "accent":       "#5B8DB8",
    "accent_hover": "#7AABD4",
    "accent_light": "#1A2A3A",
    "accent_mid":   "#2A4A6A",
    "accent_text":  "#A8D4F0",
    "btn_primary_text": "#FFFFFF",
    "success_hover_bg": "#123828",
    "danger_hover_bg":  "#3A1818",
    "sidebar_bg":   "#080808",
    "sidebar_text": "#E8E6E1",
    "sidebar_muted":"#5A5850",
    "sidebar_hover":"#181614",
    "sidebar_active":"#242220",
    "sidebar_border":"#181614",
    "danger":        "#E57373",
    "danger_strong": "#ef5350",   # أحمر أعمق (dark mode)
    "danger_bg":     "#2A1010",
    "danger_border": "#5A2020",
    "text_neutral":  "#888888",   # رمادي محايد (dark)
    "border_light":  "#3A3A3A",   # حد فاتح (dark)
    "input_accent_border": "#5c6bc0",  # حد حقل بحث indigo (dark)
    "row_alt_bg":    "#1E1E1E",   # خلفية صف متبادلة (dark)
    "row_alt_border":"#2A2A2A",   # حد صف متبادل (dark)
    "border_subtle": "#2E2E2E",   # حد خفيف جداً (dark)
    "table_gridline":"#2A2A2A",   # خطوط شبكة الجدول (dark)
    "scroll_warm_bg":"#1A1208",   # خلفية scroll ذهبي (dark)
    "success":       "#66BB8A",
    "success_bg":    "#0A2018",
    "success_border":"#1A4030",
    "warning":       "#FFD54F",
    "warning_bg":    "#2A2000",
    "warning_border":"#4A3800",
    "info":          "#64B5F6",
    "info_bg":       "#0A1828",
    "info_border":   "#1A3050",
    "tab_active":    "#5B8DB8",
    "tab_indicator": "#5B8DB8",
    "purple":        "#CE93D8",
    "purple_bg":     "#1A0828",
    "purple_border": "#4A1060",
    "orange":        "#FFB74D",
    "orange_bg":     "#281400",
    "orange_border": "#503000",
    "blue":          "#5B8DB8",
    "blue_bg":       "#1a2a3a",
    "blue_border":   "#2a4a6a",
    "blue_hover":    "#7AABD4",
    "blue_strong":   "#0d47a1",
    "teal":          "#26C6DA",
    "teal_bg":       "#0a2830",
    "teal_border":   "#1a5060",

    # ── Waste (نسبة الهادر) ──────────────────────────────
    "waste_zero_bg":         "#2a2a2a",
    "waste_zero_border":     "#3a3a3a",
    "waste_zero_color":      "#666666",

    # ── Waste levels ─────────────────────────────────────
    "waste_high_bg":         "#2a1010",
    "waste_high_border":     "#e53935",
    "waste_medium_bg":       "#281400",
    "waste_medium_border":   "#f57c00",
    "waste_low_bg":          "#282000",
    "waste_low_border":      "#ffe082",

    # ── Input states ─────────────────────────────────────
    "input_error_bg":        "#2a1010",
    "input_error_border":    "#e57373",
    "input_positive_bg":     "#0a2018",
    "input_positive_border": "#66bb8a",
    "input_positive_color":  "#66bb8a",

    # ── Card fallback ─────────────────────────────────────
    "card_fallback_bg":      "#2a2a2a",
    "card_fallback_border":  "#3a3a3a",

    # ── Accounting Journal ────────────────────────────────────
    # journal_dr_accent == badge_dr_text == acc_type_asset == accent (#5B8DB8)
    # journal_cr_accent == badge_cr_text == acc_type_liability == danger == investor_drawings_text (#E57373)
    # journal_dr_bg == badge_dr_bg == t_account_dr_bg (#1a2a3a)
    # journal_cr_bg == badge_cr_bg == t_account_cr_bg == danger_bg == audit_delete_bg == investor_drawings_bg (#2a1010)
    # journal_neutral_bg == bg_surface (#1A1A1A)
    # journal_neutral_border == border (#2E2E2E)
    "journal_dr_bg":          "#1a2a3a",   # == badge_dr_bg == t_account_dr_bg
    "journal_dr_border":      "#2a4a6a",
    "journal_dr_accent":      "#5B8DB8",   # == badge_dr_text == acc_type_asset == accent
    "journal_cr_bg":          "#2a1010",   # == badge_cr_bg == t_account_cr_bg == danger_bg == investor_drawings_bg
    "journal_cr_border":      "#5a2020",   # == danger_border
    "journal_cr_accent":      "#E57373",   # == badge_cr_text == acc_type_liability == danger == investor_drawings_text
    "journal_neutral_bg":     "#1A1A1A",   # == bg_surface
    "journal_neutral_border": "#2E2E2E",   # == border
    "journal_header_bg":      "#1a2030",
    "journal_header_border":  "#2a3050",
    # ── Investor ─────────────────────────────────────────────
    # investor_capital_bg == success_bg == audit_create_bg (#0a2018)
    # investor_capital_text == success == audit_create_fg == acc_type_capital (#66BB8A)
    # investor_drawings_bg == danger_bg == audit_delete_bg == journal_cr_bg == badge_cr_bg == t_account_cr_bg (#2a1010)
    # investor_drawings_text == danger == audit_delete_fg == badge_cr_text == journal_cr_accent == acc_type_liability (#E57373)
    "investor_capital_bg":    "#0a2018",   # == success_bg == audit_create_bg
    "investor_capital_text":  "#66BB8A",   # == success == audit_create_fg == acc_type_capital
    "investor_drawings_bg":   "#2a1010",   # == danger_bg == badge_cr_bg == journal_cr_bg
    "investor_drawings_text": "#E57373",   # == danger == badge_cr_text == journal_cr_accent
    "investor_link_bg":       "#282000",
    "investor_link_border":   "#4a3800",
    "investor_link_text":     "#FFD54F",
    # ── Audit Log — يعكس danger/warning/success مباشرة ──────
    # audit_delete_fg == danger == badge_cr_text == journal_cr_accent (#E57373)
    # audit_delete_bg == danger_bg == journal_cr_bg == badge_cr_bg == investor_drawings_bg (#2a1010)
    # audit_update_fg == warning (#FFD54F)
    # audit_update_bg == warning_bg (#2a2000)
    # audit_create_fg == success == investor_capital_text == acc_type_capital (#66BB8A)
    # audit_create_bg == success_bg == investor_capital_bg (#0a2018)
    "audit_delete_fg":        "#E57373",   # == danger
    "audit_delete_bg":        "#2a1010",   # == danger_bg
    "audit_update_fg":        "#FFD54F",   # == warning
    "audit_update_bg":        "#2a2000",   # == warning_bg
    "audit_create_fg":        "#66BB8A",   # == success
    "audit_create_bg":        "#0a2018",   # == success_bg
    # ── T-Account ────────────────────────────────────────────
    # t_account_dr_bg == badge_dr_bg == journal_dr_bg (#1a2a3a)
    # t_account_cr_bg == badge_cr_bg == journal_cr_bg == danger_bg (#2a1010)
    "t_account_dr_bg":        "#1a2a3a",   # == badge_dr_bg == journal_dr_bg
    "t_account_cr_bg":        "#2a1010",   # == badge_cr_bg == journal_cr_bg == danger_bg
    "t_account_frame":        "#2a3050",
    # ── Badge ────────────────────────────────────────────────
    # badge_dr_bg == t_account_dr_bg == journal_dr_bg (#1a2a3a)
    # badge_dr_text == journal_dr_accent == acc_type_asset == accent (#5B8DB8)
    # badge_cr_bg == t_account_cr_bg == journal_cr_bg == danger_bg (#2a1010)
    # badge_cr_text == journal_cr_accent == acc_type_liability == danger (#E57373)
    "badge_dr_bg":            "#1a2a3a",   # == t_account_dr_bg == journal_dr_bg
    "badge_dr_text":          "#5B8DB8",   # == journal_dr_accent == acc_type_asset == accent
    "badge_cr_bg":            "#2a1010",   # == t_account_cr_bg == journal_cr_bg == danger_bg
    "badge_cr_text":          "#E57373",   # == journal_cr_accent == acc_type_liability == danger
    # ── Account type colors ──────────────────────────────────
    # acc_type_asset    == badge_dr_text == journal_dr_accent == accent (#5B8DB8)
    # acc_type_liability== badge_cr_text == journal_cr_accent == danger (#E57373)
    # acc_type_capital  == success == investor_capital_text (#66BB8A)
    # acc_type_revenue  == purple (#CE93D8)
    # acc_type_expense  == orange (#FFB74D)
    "acc_type_asset":         "#5B8DB8",   # == accent == badge_dr_text
    "acc_type_liability":     "#E57373",   # == danger == badge_cr_text
    "acc_type_capital":       "#66BB8A",   # == success == investor_capital_text
    "acc_type_revenue":       "#CE93D8",   # == purple
    "acc_type_expense":       "#FFB74D",   # == orange
    "acc_type_drawings":      "#BCAAA4",
    # ── Separator / muted ────────────────────────────────────
    "text_separator":         "#607d8b",
    "group_label_text":       "#90a4ae",   # نص رأس المجموعة في الأشجار/القوائم (popup، tree)
    # ── Investor link ─────────────────────────────────────────
    # investor_link_bg == warning_bg (#2A2000), investor_link_border == warning_border (#4A3800)
    # investor_link_text == warning (#FFD54F)
    
    # ── Shared / Published items ──────────────────────────────
    "shared_item_fg":      "#CE93D8",
    "shared_item_bg":      "#1a0828",
    "published_item_fg":   "#26C6DA",
    "published_item_bg":   "#0a2830",
    
    # ── Inventory Stock Levels ────────────────────────────────
    "stock_critical_fg":   "#E57373",
    "stock_low_fg":        "#FFB74D",
    "stock_ok_fg":         "#66BB8A",

    # ── Action button hover variants ──────────────────────────
    "success_hover":       "#1A4030",
    "danger_hover":        "#5A2020",
    "warning_hover":       "#4A3800",
    "orange_hover":        "#CC5500",

    # ── Design Module ───────────────────────────────────────────
    "design_thumb_bg":          "#0A0A1E",   # خلفية الـ thumbnail في بطاقات التصميم
    "design_thumb_bg_start":    "#1d1d3e",   # بداية تدرج placeholder الـ XCF
    "design_thumb_bg_end":      "#0a0a1e",   # نهاية تدرج placeholder الـ XCF
    "design_thumb_border":      "#3c4a8a",   # حد إطار placeholder الـ XCF
    "design_thumb_icon":        "#5a6bb0",   # أيقونة 🎨 في placeholder
    "design_thumb_text":        "#6f7aa0",   # اسم الملف في placeholder
    "card_badge_text":          "#FFFFFF",   # نص badge العدد فوق الـ thumbnail الداكن
    "card_badge_bg":            "rgba(0,0,0,0.55)",      # خلفية badge العدد فوق الـ thumbnail
    "card_badge_border":        "rgba(255,255,255,0.2)", # حد badge العدد فوق الـ thumbnail

    # ── BOM Tree — Scenario node ──────────────────────────────
    "bom_scenario_default_bg":  "#0a2018",   # == success_bg — خلفية node السيناريو الافتراضي
    "bom_scenario_default_fg":  "#66BB8A",   # == success — نص node السيناريو الافتراضي
    "bom_scenario_normal_bg":   "#1a2a3a",   # == blue_bg — خلفية node سيناريو عادي
    "bom_scenario_normal_fg":   "#5B8DB8",   # == blue — نص node سيناريو عادي

    "overlay_bg":               "rgba(15,15,15,180)",   # خلفية شفافة لطبقة LoadingOverlay (dark)

    # ── Dialog Shell header ───────────────────────────────
    "dialog_hdr_sub_text":      "rgba(255,255,255,0.7)",  # نص الـ subtitle في header النافذة (dark)
    # ── ColorPickerWidget ────────────────────────────────
    "color_picker_default":     "#607d8b",   # اللون الافتراضي لـ ColorPickerWidget (dark)
}

THEMES: Dict[str, Dict[str, str]] = {
    "light": _LIGHT_THEME,
    "dark":  _DARK_THEME,
}

THEME_DISPLAY_NAME_KEYS: Dict[str, str] = {
    "light": "theme_light",
    "dark":  "theme_dark",
}


# ══════════════════════════════════════════════════════════
# CARD_PALETTES — lookup tables لألوان البطاقات
# المصدر الوحيد لهذه الألوان — نُقلت من colors.py
# ══════════════════════════════════════════════════════════

CARD_PALETTES: Dict[str, Dict[str, tuple]] = {
    "light": {
        # أزرق
        "#1565c0": ("#e8f0fe", "#90caf9"),
        "#0d47a1": ("#e3f2fd", "#64b5f6"),
        "#1d4ed8": ("#eff6ff", "#93c5fd"),
        "#1e40af": ("#eff6ff", "#93c5fd"),
        "#0891b2": ("#e0f7fa", "#80deea"),
        "#0369a1": ("#e0f2fe", "#7dd3fc"),
        # أخضر
        "#10b981": ("#ecfdf5", "#6ee7b7"),
        "#2e7d32": ("#e8f5e9", "#a5d6a7"),
        "#065f46": ("#ecfdf5", "#a7f3d0"),
        "#15803d": ("#f0fdf4", "#86efac"),
        "#16a34a": ("#f0fdf4", "#86efac"),
        # أحمر
        "#ef4444": ("#fef2f2", "#fca5a5"),
        "#dc2626": ("#fef2f2", "#fca5a5"),
        "#c62828": ("#ffebee", "#ef9a9a"),
        "#991b1b": ("#fef2f2", "#fecaca"),
        "#b91c1c": ("#fef2f2", "#fecaca"),
        # برتقالي / أصفر
        "#f59e0b": ("#fffbeb", "#fcd34d"),
        "#e65100": ("#fff3e0", "#ffcc80"),
        "#b45309": ("#fffbeb", "#fde68a"),
        "#d97706": ("#fffbeb", "#fde68a"),
        "#ea580c": ("#fff7ed", "#fdba74"),
        # رمادي
        "#6b7280": ("#f9fafb", "#d1d5db"),
        "#374151": ("#f9fafb", "#e5e7eb"),
        "#9ca3af": ("#f9fafb", "#e5e7eb"),
        "#555555": ("#f5f5f5", "#e0e0e0"),
        "#555":    ("#f5f5f5", "#e0e0e0"),
        "#4b5563": ("#f9fafb", "#d1d5db"),
        # بنفسجي / وردي
        "#8b5cf6": ("#f5f3ff", "#c4b5fd"),
        "#6d28d9": ("#f5f3ff", "#ddd6fe"),
        "#6a1b9a": ("#f3e5f5", "#ce93d8"),
        "#7c3aed": ("#f5f3ff", "#c4b5fd"),
        "#9333ea": ("#faf5ff", "#d8b4fe"),
        "#db2777": ("#fdf2f8", "#f9a8d4"),
        "#be185d": ("#fdf2f8", "#fbcfe8"),
        # بني
        "#4e342e": ("#efebe9", "#bcaaa4"),
        "#5d4037": ("#efebe9", "#bcaaa4"),
    },
    "dark": {
        # أزرق
        "#1565c0": ("#1a2a3a", "#2a4a6a"),
        "#0d47a1": ("#152030", "#1e3a5f"),
        "#1d4ed8": ("#1a2540", "#2a4080"),
        "#1e40af": ("#1a2540", "#2a4080"),
        "#0891b2": ("#0a2830", "#1a5060"),
        "#0369a1": ("#0a2030", "#1a4060"),
        # أخضر
        "#10b981": ("#0a2820", "#1a5040"),
        "#2e7d32": ("#0a2010", "#1a4020"),
        "#065f46": ("#0a2818", "#1a5030"),
        "#15803d": ("#0a2018", "#1a4030"),
        "#16a34a": ("#0a2018", "#1a4030"),
        # أحمر
        "#ef4444": ("#2a1010", "#5a2020"),
        "#dc2626": ("#2a1010", "#5a2020"),
        "#c62828": ("#281010", "#4a1818"),
        "#991b1b": ("#2a1010", "#4a1818"),
        "#b91c1c": ("#2a1010", "#4a1818"),
        # برتقالي / أصفر
        "#f59e0b": ("#2a2000", "#4a3800"),
        "#e65100": ("#281400", "#503000"),
        "#b45309": ("#281c00", "#4a3400"),
        "#d97706": ("#281c00", "#4a3400"),
        "#ea580c": ("#281800", "#503800"),
        # رمادي
        "#6b7280": ("#1e2028", "#2e3040"),
        "#374151": ("#1a1c24", "#2a2e38"),
        "#9ca3af": ("#1e2028", "#2e3040"),
        "#555555": ("#1e1e1e", "#2e2e2e"),
        "#555":    ("#1e1e1e", "#2e2e2e"),
        "#4b5563": ("#1a1c24", "#2a2e38"),
        # بنفسجي / وردي
        "#8b5cf6": ("#1a1028", "#3a2060"),
        "#6d28d9": ("#180c28", "#301860"),
        "#6a1b9a": ("#1a0828", "#3a1060"),
        "#7c3aed": ("#1a0c2a", "#341860"),
        "#9333ea": ("#1c0a28", "#3c1860"),
        "#db2777": ("#280a18", "#501830"),
        "#be185d": ("#280a18", "#501830"),
        # بني
        "#4e342e": ("#201010", "#3a1c18"),
        "#5d4037": ("#221210", "#3c1e18"),
    },
}


# ══════════════════════════════════════════════════════════
# ThemeManager
# ══════════════════════════════════════════════════════════

class ThemeManager(QObject):
    """
    Singleton يدير الثيم الحالي.

    الاستخدام:
        from ui.theme_manager import theme_manager

        theme_manager.set_theme("dark")
        theme_manager.theme_changed.connect(my_fn)
    """

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._current_theme: str = "light"

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        return self._current_theme == "dark"

    def set_theme(self, theme_name: str, save: bool = True):
        """
        يبدّل الثيم فوراً ويطبّقه على كامل التطبيق.
        """
        if theme_name not in THEMES:
            theme_name = "light"

        if theme_name == self._current_theme:
            return

        self._current_theme = theme_name
        colors = THEMES[theme_name]

        try:
            from ui.theme import apply_theme
            apply_theme(colors)
        except Exception:
            pass

        if save:
            self._save_to_db()

        self._emit_theme_changed(theme_name)
        self.theme_changed.emit(theme_name)

    def load_from_db(self):
        """يحمّل الثيم المحفوظ من DB عند بدء التطبيق."""
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import get_setting
            conn  = get_connection()
            theme = get_setting(conn, "ui_theme", "light")
            if theme in THEMES:
                self._current_theme = theme
            colors = THEMES.get(self._current_theme, _LIGHT_THEME)
            try:
                from ui.theme import apply_theme
                apply_theme(colors)
            except Exception:
                pass
        except Exception:
            pass

    def get_available_themes(self) -> list:
        from ui.widgets.core.i18n import tr
        return [
            {
                "key":    key,
                "name":   tr(THEME_DISPLAY_NAME_KEYS.get(key, key)),
                "active": key == self._current_theme,
            }
            for key in THEMES
        ]

    # ── Internal ──────────────────────────────────────────

    def _emit_theme_changed(self, theme_name: str):
        try:
            from ui.widgets.core.events import bus
            bus.theme_changed.emit(theme_name)
        except Exception:
            pass

    def _save_to_db(self):
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import set_setting
            conn = get_connection()
            set_setting(conn, "ui_theme", self._current_theme)
        except Exception:
            pass


# ── Singleton ─────────────────────────────────────────────
theme_manager = ThemeManager()