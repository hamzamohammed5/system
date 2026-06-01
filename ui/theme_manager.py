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

الاستخدام:
    from ui.theme_manager import theme_manager

    theme_manager.set_theme("dark")
    current = theme_manager.current_theme   # "dark"

    theme_manager.theme_changed.connect(my_fn)
    # أو عبر bus:
    from ui.events import bus
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
    "border":       "#DDD9CF",
    "border_med":   "#C8C4B8",
    "border_focus": "#8B8680",
    "border_strong":"#6B6760",
    "text_primary": "#1C1B18",
    "text_sec":     "#4A4843",
    "text_muted":   "#7A7870",
    "text_disabled":"#A8A69E",
    "accent":       "#3D5A80",
    "accent_hover": "#2E4460",
    "accent_light": "#D6E4F0",
    "accent_mid":   "#98C1D9",
    "accent_text":  "#2A3F5A",
    "sidebar_bg":    "#1E1D1A",
    "sidebar_text":  "#E8E6E1",
    "sidebar_muted": "#7A7870",
    "sidebar_hover": "#2E2D2A",
    "sidebar_active":"#3A3835",
    "sidebar_border":"#2E2D2A",
    "danger":        "#C0392B",
    "danger_bg":     "#FDF0EF",
    "danger_border": "#E8A39D",
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
}

_DARK_THEME: Dict[str, str] = {
    "bg_page":      "#0F0F0F",
    "bg_surface":   "#1A1A1A",
    "bg_surface_2": "#242424",
    "bg_hover":     "#2E2E2E",
    "bg_active":    "#383838",
    "bg_input":     "#1E1E1E",
    "border":       "#2E2E2E",
    "border_med":   "#3A3A3A",
    "border_focus": "#5A5A5A",
    "border_strong":"#6E6E6E",
    "text_primary": "#E8E6E1",
    "text_sec":     "#B8B5AE",
    "text_muted":   "#7A7870",
    "text_disabled":"#4A4843",
    "accent":       "#5B8DB8",
    "accent_hover": "#7AABD4",
    "accent_light": "#1A2A3A",
    "accent_mid":   "#2A4A6A",
    "accent_text":  "#A8D4F0",
    "sidebar_bg":   "#080808",
    "sidebar_text": "#E8E6E1",
    "sidebar_muted":"#5A5850",
    "sidebar_hover":"#181614",
    "sidebar_active":"#242220",
    "sidebar_border":"#181614",
    "danger":        "#E57373",
    "danger_bg":     "#2A1010",
    "danger_border": "#5A2020",
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
}

THEMES: Dict[str, Dict[str, str]] = {
    "light": _LIGHT_THEME,
    "dark":  _DARK_THEME,
}

THEME_DISPLAY_NAMES: Dict[str, str] = {
    "light": "فاتح",
    "dark":  "داكن",
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
        return [
            {
                "key":    key,
                "name":   THEME_DISPLAY_NAMES.get(key, key),
                "active": key == self._current_theme,
            }
            for key in THEMES
        ]

    # ── Internal ──────────────────────────────────────────

    def _emit_theme_changed(self, theme_name: str):
        try:
            from ui.events import bus
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