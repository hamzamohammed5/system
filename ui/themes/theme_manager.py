"""
ui/themes/theme_manager.py
============================
ThemeManager — يدير الثيم الحالي للتطبيق.

يدعم:
  - Light  (افتراضي — Warm Neutral)
  - Dark

الاستخدام:
    from ui.themes import theme_manager

    theme_manager.set_theme("dark")
    current = theme_manager.current_theme   # "dark"

    # الاستماع لتغيير الثيم عبر signal مباشر:
    theme_manager.theme_changed.connect(my_fn)

    # أو عبر bus (للـ widgets المنتشرة):
    from ui.events import bus
    bus.theme_changed.connect(my_fn)

ملاحظة:
    هذا الملف يحتوي على ThemeManager فقط.
    تعريف الثيمات (THEMES, THEME_DISPLAY_NAMES) موجود في ui/themes.py
    لأن ذلك الملف هو المستورَد في باقي التطبيق.
    ThemeManager هنا يستورد من ui/themes.py عند الحاجة لتجنب الـ circular import.
"""

from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal


class ThemeManager(QObject):
    """
    Singleton يدير الثيم الحالي.

    set_theme() يُحدّث _C في app_settings + يمسح الـ stylesheet cache
    + يُطبّق الـ stylesheet الجديد + يُطلق theme_changed عبر bus.

    الاستخدام:
        from ui.themes import theme_manager
        theme_manager.set_theme("dark")
        theme_manager.theme_changed.connect(my_fn)
    """

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._current_theme: str = "light"

    # ── Properties ────────────────────────────────────────

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        return self._current_theme == "dark"

    # ── Public API ────────────────────────────────────────

    def set_theme(self, theme_name: str, save: bool = True):
        """
        يبدّل الثيم فوراً ويطبّقه على كامل التطبيق.

        الخطوات:
          1. يتحقق أن الثيم موجود
          2. يُحدّث _C عبر apply_theme() في app_settings
          3. يحفظ في DB لو save=True
          4. يُطلق theme_changed عبر bus + signal المباشر
        """
        # استيراد هنا لتجنب circular import
        try:
            from ui.themes import THEMES
        except ImportError:
            # fallback لو ui/themes.py غير موجود
            THEMES = {"light": {}, "dark": {}}

        if theme_name not in THEMES:
            theme_name = "light"

        if theme_name == self._current_theme:
            return

        self._current_theme = theme_name
        colors = THEMES[theme_name]

        # تحديث _C + مسح cache + تطبيق stylesheet
        try:
            from ui.app_settings import apply_theme
            apply_theme(colors)
        except Exception as e:
            print(f"[ThemeManager] apply_theme warning: {e}")

        if save:
            self._save_to_db()

        # إطلاق events
        self._emit_bus_signal(theme_name)
        self.theme_changed.emit(theme_name)

    def load_from_db(self):
        """
        يحمّل الثيم المحفوظ من DB عند بدء التطبيق.
        يُطبّق الثيم بدون save وبدون إطلاق events (لأن التطبيق بيشتغل لأول مرة).
        """
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import get_setting
            from ui.themes import THEMES

            conn  = get_connection()
            theme = get_setting(conn, "ui_theme", "light")

            if theme in THEMES:
                self._current_theme = theme
            else:
                self._current_theme = "light"

            # تطبيق بدون events
            colors = THEMES.get(self._current_theme, {})
            try:
                from ui.app_settings import apply_theme
                apply_theme(colors)
            except Exception as e:
                print(f"[ThemeManager.load_from_db] apply_theme warning: {e}")

        except Exception as e:
            print(f"[ThemeManager.load_from_db] warning: {e}")

    def get_available_themes(self) -> list[dict]:
        """
        يرجع قائمة الثيمات المتاحة.

        مثال النتيجة:
            [
                {"key": "light", "name": "فاتح",  "active": True},
                {"key": "dark",  "name": "داكن",  "active": False},
            ]
        """
        try:
            from ui.themes import THEMES, THEME_DISPLAY_NAMES
        except ImportError:
            THEMES = {"light": {}, "dark": {}}
            THEME_DISPLAY_NAMES = {"light": "فاتح", "dark": "داكن"}

        return [
            {
                "key":    key,
                "name":   THEME_DISPLAY_NAMES.get(key, key),
                "active": key == self._current_theme,
            }
            for key in THEMES
        ]

    # ── Internal ──────────────────────────────────────────

    def _emit_bus_signal(self, theme_name: str):
        """يُطلق bus.theme_changed لإشعار الـ widgets المشتركة."""
        try:
            from ui.events import bus
            bus.theme_changed.emit(theme_name)
        except Exception as e:
            print(f"[ThemeManager] bus.theme_changed warning: {e}")

    def _save_to_db(self):
        """يحفظ الثيم الحالي في DB."""
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import set_setting
            conn = get_connection()
            set_setting(conn, "ui_theme", self._current_theme)
        except Exception as e:
            print(f"[ThemeManager._save_to_db] warning: {e}")


# ── Singleton ──────────────────────────────────────────────
# يُستورد من هنا في باقي التطبيق:
#   from ui.themes.theme_manager import ThemeManager
# لكن الـ singleton نفسه موجود في ui/themes.py:
#   from ui.themes import theme_manager
theme_manager = ThemeManager()