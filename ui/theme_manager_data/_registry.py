"""
ui/theme_manager_data/_registry.py
===============================
THEMES و THEME_DISPLAY_NAME_KEYS — سجل الثيمات المتاحة.
جزء من تقسيم ui/theme_manager.py — راجع ui/theme_manager/__init__.py.
"""

from __future__ import annotations
from typing import Dict

from ui.theme_manager_data._light_theme import _LIGHT_THEME
from ui.theme_manager_data._dark_theme import _DARK_THEME

THEMES: Dict[str, Dict[str, str]] = {
    "light": _LIGHT_THEME,
    "dark":  _DARK_THEME,
}

THEME_DISPLAY_NAME_KEYS: Dict[str, str] = {
    "light": "theme_light",
    "dark":  "theme_dark",
}
