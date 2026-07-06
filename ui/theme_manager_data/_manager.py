"""
ui/theme_manager_data/_manager.py
==============================
ThemeManager — الـ singleton الذي يدير الثيم الحالي للتطبيق.
جزء من تقسيم ui/theme_manager.py — راجع ui/theme_manager/__init__.py.
"""

from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal

from ui.theme_manager_data._registry import THEMES, THEME_DISPLAY_NAME_KEYS
from ui.theme_manager_data._light_theme import _LIGHT_THEME


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

