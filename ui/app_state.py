"""
ui/app_state.py
===============
AppState — Cache مركزي لإعدادات التطبيق.

المسؤولية الوحيدة:
  - cache حجم الخط (يُقرأ من DB مرة واحدة)
  - invalidate عند تغيير الشركة النشطة
"""

from __future__ import annotations
import logging
from ui.constants import DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE

logger = logging.getLogger(__name__)


class AppState:
    """
    Cache مركزي لإعدادات التطبيق.
    كل الـ attributes هي class-level — مفيش instance.
    """

    _font_size: int | None = None

    # ── Font Size ──────────────────────────────────────────

    @classmethod
    def font_size(cls) -> int:
        """يرجع حجم الخط — يحمّل من DB مرة واحدة ثم يرجع من الـ cache."""
        if cls._font_size is None:
            cls._font_size = cls._load_font_size_from_db()
        return cls._font_size

    @classmethod
    def on_font_changed(cls, size: int):
        """يُستدعى عند تغيير حجم الخط — يحدّث الـ cache."""
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
        cls._font_size = size
        try:
            from ui.font import _set_module_font_cache
            _set_module_font_cache(size)
        except Exception:
            pass
        cls._invalidate_button_cache()
        logger.debug("AppState.on_font_changed: %d", size)

    @classmethod
    def invalidate(cls):
        """
        يبطّل كل الـ cache.
        يُستدعى عند تغيير الشركة النشطة فقط.
        """
        cls._font_size = None
        try:
            from ui.theme import invalidate_stylesheet_cache
            invalidate_stylesheet_cache()
        except Exception as e:
            logger.debug("AppState.invalidate: %s", e)
            cls._invalidate_button_cache()
        logger.debug("AppState.invalidate: cache cleared")

    # ── Internal ───────────────────────────────────────────

    @classmethod
    def _load_font_size_from_db(cls) -> int:
        """يحمّل font_size من DB — fallback للـ DEFAULT لو فشل."""
        try:
            from db.shared.connection import get_connection
            conn = get_connection()
        except Exception:
            return DEFAULT_FONT_SIZE

        try:
            from db.shared.settings_repo import get_setting, set_setting
            raw = get_setting(conn, "font_size", None)
            if raw is None:
                set_setting(conn, "font_size", DEFAULT_FONT_SIZE)
                return DEFAULT_FONT_SIZE
            val = int(float(raw))
            if not (MIN_FONT_SIZE <= val <= MAX_FONT_SIZE):
                set_setting(conn, "font_size", DEFAULT_FONT_SIZE)
                return DEFAULT_FONT_SIZE
            return val
        except Exception:
            return DEFAULT_FONT_SIZE

    @classmethod
    def _invalidate_button_cache(cls):
        """يبطّل stylesheet cache الأزرار."""
        try:
            from ui.widgets.components.button import invalidate_stylesheet_cache
            invalidate_stylesheet_cache()
        except Exception as e:
            logger.debug("AppState._invalidate_button_cache: %s", e)