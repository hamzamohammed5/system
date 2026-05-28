"""
ui/themes.py
=============
نظام الثيمات الكامل للتطبيق.

يدعم:
  - Light (الافتراضي — Warm Neutral)
  - Dark
  - Custom (ألوان مخصصة لكل شركة)

الاستخدام:
    from ui.themes import theme_manager

    # تبديل الثيم
    theme_manager.set_theme("dark")

    # الحصول على الألوان
    colors = theme_manager.colors   # dict

    # الاشتراك في التغييرات
    theme_manager.theme_changed.connect(my_fn)

التصميم:
  - ThemeManager singleton — المصدر الوحيد للألوان
  - _C في app_settings يُحدَّث تلقائياً عند تغيير الثيم
  - AppState.invalidate() يُستدعى تلقائياً لمسح الـ stylesheet cache
"""

from __future__ import annotations

from typing import Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal


# ══════════════════════════════════════════════════════════
# تعريف الثيمات
# ══════════════════════════════════════════════════════════

_LIGHT_THEME: Dict[str, str] = {
    # Backgrounds
    "bg_page":      "#F5F4F0",
    "bg_surface":   "#FAFAF8",
    "bg_surface_2": "#F0EEE9",
    "bg_hover":     "#ECEAE4",
    "bg_active":    "#E4E2DA",
    "bg_input":     "#FFFFFF",

    # Borders
    "border":        "#DDD9CF",
    "border_med":    "#C8C4B8",
    "border_focus":  "#8B8680",
    "border_strong": "#6B6760",

    # Text
    "text_primary":  "#1C1B18",
    "text_sec":      "#4A4843",
    "text_muted":    "#7A7870",
    "text_disabled": "#A8A69E",

    # Accent — Slate Blue
    "accent":        "#3D5A80",
    "accent_hover":  "#2E4460",
    "accent_light":  "#D6E4F0",
    "accent_mid":    "#98C1D9",
    "accent_text":   "#2A3F5A",

    # Sidebar
    "sidebar_bg":     "#1E1D1A",
    "sidebar_text":   "#E8E6E1",
    "sidebar_muted":  "#7A7870",
    "sidebar_hover":  "#2E2D2A",
    "sidebar_active": "#3A3835",
    "sidebar_border": "#2E2D2A",

    # States
    "danger":         "#C0392B",
    "danger_bg":      "#FDF0EF",
    "danger_border":  "#E8A39D",
    "success":        "#2E7D52",
    "success_bg":     "#EDF7F2",
    "success_border": "#8EC5A8",
    "warning":        "#7A5C00",
    "warning_bg":     "#FDF8E7",
    "warning_border": "#D4B84A",
    "info":           "#1A5276",
    "info_bg":        "#EBF5FB",
    "info_border":    "#7FB3D3",

    # Tab
    "tab_active":    "#3D5A80",
    "tab_indicator": "#3D5A80",

    # Purple
    "purple":        "#6a1b9a",
    "purple_bg":     "#f3e5f5",
    "purple_border": "#ce93d8",

    # Orange
    "orange":        "#e65100",
    "orange_bg":     "#fff3e0",
    "orange_border": "#ffcc80",
}


_DARK_THEME: Dict[str, str] = {
    # Backgrounds
    "bg_page":      "#0F0F0F",
    "bg_surface":   "#1A1A1A",
    "bg_surface_2": "#242424",
    "bg_hover":     "#2E2E2E",
    "bg_active":    "#383838",
    "bg_input":     "#1E1E1E",

    # Borders
    "border":        "#2E2E2E",
    "border_med":    "#3A3A3A",
    "border_focus":  "#5A5A5A",
    "border_strong": "#6E6E6E",

    # Text
    "text_primary":  "#E8E6E1",
    "text_sec":      "#B8B5AE",
    "text_muted":    "#7A7870",
    "text_disabled": "#4A4843",

    # Accent — Slate Blue (أفتح قليلاً في الـ dark)
    "accent":        "#5B8DB8",
    "accent_hover":  "#7AABD4",
    "accent_light":  "#1A2A3A",
    "accent_mid":    "#2A4A6A",
    "accent_text":   "#A8D4F0",

    # Sidebar (أغمق في الـ dark)
    "sidebar_bg":     "#080808",
    "sidebar_text":   "#E8E6E1",
    "sidebar_muted":  "#5A5850",
    "sidebar_hover":  "#181614",
    "sidebar_active": "#242220",
    "sidebar_border": "#181614",

    # States (مكيّفة للـ dark)
    "danger":         "#E57373",
    "danger_bg":      "#2A1010",
    "danger_border":  "#5A2020",
    "success":        "#66BB8A",
    "success_bg":     "#0A2018",
    "success_border": "#1A4030",
    "warning":        "#FFD54F",
    "warning_bg":     "#2A2000",
    "warning_border": "#4A3800",
    "info":           "#64B5F6",
    "info_bg":        "#0A1828",
    "info_border":    "#1A3050",

    # Tab
    "tab_active":    "#5B8DB8",
    "tab_indicator": "#5B8DB8",

    # Purple
    "purple":        "#CE93D8",
    "purple_bg":     "#1A0828",
    "purple_border": "#4A1060",

    # Orange
    "orange":        "#FFB74D",
    "orange_bg":     "#281400",
    "orange_border": "#503000",
}


# قاموس الثيمات المتاحة
THEMES: Dict[str, Dict[str, str]] = {
    "light": _LIGHT_THEME,
    "dark":  _DARK_THEME,
}

# أسماء عرض الثيمات
THEME_DISPLAY_NAMES: Dict[str, str] = {
    "light": "فاتح",
    "dark":  "داكن",
}


# ══════════════════════════════════════════════════════════
# ThemeManager
# ══════════════════════════════════════════════════════════

class ThemeManager(QObject):
    """
    Singleton يدير الثيم الحالي ويبلّغ الـ widgets عند التغيير.

    الاستخدام:
        from ui.themes import theme_manager

        theme_manager.set_theme("dark")
        current = theme_manager.current_theme   # "dark"
        colors  = theme_manager.colors          # dict

    Signal:
        theme_changed(str) — اسم الثيم الجديد
    """

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._current_theme: str = "light"
        self._custom_overrides: Dict[str, str] = {}

    # ── API العام ──────────────────────────────────────────

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def colors(self) -> Dict[str, str]:
        """يرجع dict الألوان الكاملة للثيم الحالي مع الـ overrides."""
        base = dict(THEMES.get(self._current_theme, _LIGHT_THEME))
        base.update(self._custom_overrides)
        return base

    @property
    def is_dark(self) -> bool:
        return self._current_theme == "dark"

    def set_theme(self, theme_name: str, save: bool = True):
        """
        يبدّل الثيم فوراً.

        theme_name: "light" | "dark" | اسم ثيم مخصص
        save: يحفظ في DB لو True
        """
        if theme_name not in THEMES and theme_name != "custom":
            theme_name = "light"

        if theme_name == self._current_theme and not self._custom_overrides:
            return

        self._current_theme = theme_name
        self._apply_to_app_settings()

        if save:
            self._save_to_db()

        # أبطل stylesheet cache ثم أعد بناءه
        self._invalidate_caches()
        self._rebuild_stylesheet()

        self.theme_changed.emit(theme_name)

    def set_custom_color(self, key: str, value: str, save: bool = True):
        """
        يعيّن لوناً مخصصاً يتجاوز الثيم الحالي.

        مثال:
            theme_manager.set_custom_color("accent", "#E74C3C")
        """
        self._custom_overrides[key] = value
        self._apply_to_app_settings()
        if save:
            self._save_custom_overrides()
        self._invalidate_caches()
        self._rebuild_stylesheet()
        self.theme_changed.emit(self._current_theme)

    def clear_custom_colors(self, save: bool = True):
        """يمسح الألوان المخصصة ويرجع للثيم الأساسي."""
        self._custom_overrides.clear()
        self._apply_to_app_settings()
        if save:
            self._save_custom_overrides()
        self._invalidate_caches()
        self._rebuild_stylesheet()
        self.theme_changed.emit(self._current_theme)

    def get_available_themes(self) -> list[dict]:
        """يرجع قائمة الثيمات المتاحة للعرض في الـ UI."""
        result = []
        for key, display in THEME_DISPLAY_NAMES.items():
            result.append({
                "key":     key,
                "name":    display,
                "active":  key == self._current_theme,
            })
        return result

    # ── تحميل من DB ───────────────────────────────────────

    def load_from_db(self):
        """يحمّل الثيم المحفوظ من DB عند بدء التطبيق."""
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import get_setting
            conn = get_connection()
            theme = get_setting(conn, "ui_theme", "light")
            custom_json = get_setting(conn, "ui_custom_colors", "")
            if custom_json:
                import json
                try:
                    self._custom_overrides = json.loads(custom_json)
                except Exception:
                    self._custom_overrides = {}
            # لا نستدعي set_theme هنا لتجنب الـ loop — نطبّق مباشرة
            if theme in THEMES:
                self._current_theme = theme
            self._apply_to_app_settings()
        except Exception:
            pass  # Fallback للـ light theme

    # ── Internal ──────────────────────────────────────────

    def _apply_to_app_settings(self):
        """يحدّث _C في app_settings بألوان الثيم الحالي."""
        try:
            import ui.app_settings as _as
            colors = self.colors
            for key, value in colors.items():
                _as._C[key] = value
        except Exception:
            pass

    def _invalidate_caches(self):
        """يمسح كل الـ caches المرتبطة بالثيم."""
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

    def _save_custom_overrides(self):
        try:
            import json
            from db.shared.connection import get_connection
            from db.shared.settings_repo import set_setting
            conn = get_connection()
            set_setting(conn, "ui_custom_colors",
                        json.dumps(self._custom_overrides, ensure_ascii=False))
        except Exception:
            pass


# ── Singleton ─────────────────────────────────────────────
theme_manager = ThemeManager()


# ══════════════════════════════════════════════════════════
# Helper دوال
# ══════════════════════════════════════════════════════════

def get_theme_colors(theme_name: str = "light") -> Dict[str, str]:
    """يرجع dict الألوان لثيم معين بدون تطبيقه."""
    return dict(THEMES.get(theme_name, _LIGHT_THEME))


def preview_color(key: str, theme_name: str = "dark") -> str:
    """
    يرجع قيمة لون معين في ثيم معين.
    مفيد لعرض preview في الـ UI.
    """
    return THEMES.get(theme_name, _LIGHT_THEME).get(key, "#000000")