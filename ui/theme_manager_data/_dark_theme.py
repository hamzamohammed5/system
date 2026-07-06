"""
ui/theme_manager_data/_dark_theme.py
=================================
تعريف ألوان الثيم الداكن (Dark).
جزء من تقسيم ui/theme_manager.py — راجع ui/theme_manager/__init__.py.
"""

from __future__ import annotations
from typing import Dict


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

    # ── Icon button ───────────────────────────────────────
    "icon_btn_color":           "#7A7870",   # == text_muted — لون أيقونة زر الـ icon افتراضي (dark)
    "icon_btn_hover_color":     "#ef5350",   # == danger_strong — لون hover لزر الأيقونة (dark)
}

