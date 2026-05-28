"""
ui/themes.py
=============
نظام الثيمات الكامل للتطبيق.

يدعم:
  - Light (الافتراضي — Warm Neutral)
  - Dark

الاستخدام:
    from ui.themes import theme_manager

    theme_manager.set_theme("dark")
    current = theme_manager.current_theme   # "dark"

    theme_manager.theme_changed.connect(my_fn)
"""

from __future__ import annotations

from typing import Dict
from PyQt5.QtCore import QObject, pyqtSignal


# ══════════════════════════════════════════════════════════
# تعريف الثيمات
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
# ThemeManager
# ══════════════════════════════════════════════════════════

class ThemeManager(QObject):
    """
    Singleton يدير الثيم الحالي.

    الاستخدام:
        from ui.themes import theme_manager

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
        """يبدّل الثيم فوراً ويطبّقه على كامل التطبيق."""
        if theme_name not in THEMES:
            theme_name = "light"

        if theme_name == self._current_theme:
            return

        self._current_theme = theme_name
        self._apply_to_app_settings()

        if save:
            self._save_to_db()

        self._invalidate_caches()
        self._rebuild_stylesheet()
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
            self._apply_to_app_settings()
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

    def _apply_to_app_settings(self):
        """يحدّث _C في app_settings بألوان الثيم الحالي."""
        try:
            import ui.app_settings as _as
            colors = THEMES.get(self._current_theme, _LIGHT_THEME)
            for key, value in colors.items():
                _as._C[key] = value
        except Exception:
            pass

    def _invalidate_caches(self):
        try:
            from ui.app_settings import invalidate_stylesheet_cache
            invalidate_stylesheet_cache()
        except Exception:
            pass
        try:
            from ui.widgets.components.button import invalidate_stylesheet_cache as inv_btn
            inv_btn()
        except Exception:
            pass

    def _rebuild_stylesheet(self):
        """يعيد بناء stylesheet التطبيق ويطبّقه فوراً."""
        try:
            from PyQt5.QtWidgets import QApplication
            from ui.app_settings import apply_font, get_font_size
            app = QApplication.instance()
            if app:
                apply_font(app, get_font_size())
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