"""
ui/theme_manager/__init__.py
==============================
نظام الثيمات الكامل للتطبيق — المصدر الوحيد لكل الألوان.

[مُقسّم] هذا الملف كان ui/theme_manager.py (ملف واحد ~680 سطر) وتم تقسيمه
إلى حزمة (package) للحفاظ على قابلية القراءة، مع إبقاء نفس واجهة
الاستيراد العامة تمامًا — أي كود يستورد `from ui.theme_manager import X`
يستمر بالعمل دون أي تعديل.

هيكل الحزمة:
    ui/theme_manager/__init__.py        ← هذا الملف: يجمّع كل شيء ويصدّره
    ui/theme_manager/_light_theme.py    ← _LIGHT_THEME
    ui/theme_manager/_dark_theme.py     ← _DARK_THEME
    ui/theme_manager/_registry.py       ← THEMES, THEME_DISPLAY_NAME_KEYS
    ui/theme_manager/_card_palettes.py  ← CARD_PALETTES
    ui/theme_manager/_manager.py        ← class ThemeManager

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

from ui.theme_manager_data._light_theme import _LIGHT_THEME
from ui.theme_manager_data._dark_theme import _DARK_THEME
from ui.theme_manager_data._registry import THEMES, THEME_DISPLAY_NAME_KEYS
from ui.theme_manager_data._card_palettes import CARD_PALETTES
from ui.theme_manager_data._manager import ThemeManager

# ── Singleton ─────────────────────────────────────────────
theme_manager = ThemeManager()

__all__ = [
    "_LIGHT_THEME",
    "_DARK_THEME",
    "THEMES",
    "THEME_DISPLAY_NAME_KEYS",
    "CARD_PALETTES",
    "ThemeManager",
    "theme_manager",
]
