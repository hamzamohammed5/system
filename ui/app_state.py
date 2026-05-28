"""
ui/app_state.py
================
AppState — Cache مركزي لإعدادات التطبيق.

التغييرات:
  - [تحسين 37] invalidate() يستدعي invalidate_stylesheet_cache() من app_settings
    بدل invalidate_button_cache() فقط.
    هذا يضمن أن تغيير الشركة يمسح الـ stylesheet cache كاملاً
    (مهم لو كان لكل شركة ثيم مختلف مستقبلاً).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20


class AppState:
    """
    Cache مركزي لإعدادات التطبيق.
    كل الـ attributes هي class-level — مفيش instance.
    """

    _font_size: int | None = None

    # ── Font Size ──────────────────────────────────────────

    @classmethod
    def font_size(cls) -> int:
        """
        يرجع حجم الخط الحالي.
        يحمّل من DB مرة واحدة فقط — بعدها يرجع من الـ cache.
        """
        if cls._font_size is None:
            cls._font_size = cls._load_font_size_from_db()
        return cls._font_size

    @classmethod
    def on_font_changed(cls, size: int):
        """
        يُستدعى عند تغيير حجم الخط من الإعدادات.
        يحدّث الـ cache ويبطّل stylesheet cache الأزرار.
        """
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
        cls._font_size = size
        # [تحسين 43] زامن module-level cache في app_settings
        try:
            from ui.app_settings import _set_module_font_cache
            _set_module_font_cache(size)
        except Exception:
            pass
        cls._invalidate_button_cache()
        logger.debug("AppState.on_font_changed: %d", size)

    @classmethod
    def invalidate(cls):
        """
        يبطّل كل الـ cache — للاستخدام عند تغيير الشركة النشطة.
        (الشركة الجديدة ممكن يكون ليها font_size مختلف)

        [تحسين 37] يستدعي invalidate_stylesheet_cache() من app_settings
        بدل _invalidate_button_cache() فقط، لضمان مسح الـ stylesheet cache
        كاملاً عند تغيير الشركة (ضروري للـ Dark Mode مستقبلاً).
        """
        cls._font_size = None
        cls._invalidate_stylesheet_cache()
        logger.debug("AppState.invalidate: cache cleared")

    # ── Internal ───────────────────────────────────────────

    @classmethod
    def _load_font_size_from_db(cls) -> int:
        """يحمّل font_size من DB — fallback للـ DEFAULT لو فشل."""
        try:
            from db.shared.connection import get_connection
            conn = get_connection()
        except RuntimeError:
            return DEFAULT_FONT_SIZE
        except Exception:
            return DEFAULT_FONT_SIZE

        try:
            from db.shared.settings_repo import get_setting, set_setting
            raw = get_setting(conn, "font_size", None)
            if raw is None:
                set_setting(conn, "font_size", DEFAULT_FONT_SIZE)
                return DEFAULT_FONT_SIZE
            val = int(float(raw))
            if val < MIN_FONT_SIZE or val > MAX_FONT_SIZE:
                set_setting(conn, "font_size", DEFAULT_FONT_SIZE)
                return DEFAULT_FONT_SIZE
            return val
        except Exception:
            return DEFAULT_FONT_SIZE

    @classmethod
    def _invalidate_stylesheet_cache(cls):
        """
        [تحسين 37] يبطّل stylesheet cache الكامل من app_settings.
        يشمل كل الـ stylesheets المبنية لكل (font_size, theme_hash).
        """
        try:
            from ui.app_settings import invalidate_stylesheet_cache
            invalidate_stylesheet_cache()
        except Exception as e:
            logger.debug("AppState._invalidate_stylesheet_cache: %s", e)
            # fallback — ابطل button cache على الأقل
            cls._invalidate_button_cache()

    @classmethod
    def _invalidate_button_cache(cls):
        """يبطّل stylesheet cache الأزرار لما يتغير حجم الخط."""
        try:
            from ui.widgets.components.button import invalidate_stylesheet_cache
            invalidate_stylesheet_cache()
        except Exception as e:
            logger.debug("AppState._invalidate_button_cache: %s", e)