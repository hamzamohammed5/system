"""
ui/app_state.py
===============
AppState — Cache مركزي لإعدادات التطبيق.

المسؤولية الوحيدة:
  - cache حجم الخط (يُقرأ من DB مرة واحدة عبر FontService)
  - invalidate عند تغيير الشركة النشطة

التسلسل الكامل لحجم الخط:
    ui/font.py  →  AppState  →  FontService  →  settings_repo  →  DB

AppState لا يتواصل مع DB أو settings_repo مباشرةً —
كل عمليات القراءة والكتابة تمر عبر FontService.
"""

from __future__ import annotations
import logging
from ui.constants import DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE

logger = logging.getLogger(__name__)


class AppState:
    """
    Cache مركزي لإعدادات التطبيق.
    كل الـ attributes هي class-level — مفيش instance.

    القاعدة الذهبية:
        AppState يكلّم FontService فقط — لا يعرف settings_repo أو DB.
    """

    _font_size: int | None = None

    # ── Font Size ──────────────────────────────────────────

    @classmethod
    def font_size(cls) -> int:
        """
        يرجع حجم الخط الحالي.
        يقرأ من الـ cache أولاً — إن لم يوجد يحمّل عبر FontService.
        """
        if cls._font_size is None:
            cls._font_size = cls._load_font_size()
        return cls._font_size

    @classmethod
    def on_font_changed(cls, size: int):
        """
        يُستدعى عند تغيير حجم الخط (من SettingsDialog أو font.set_font_size).
        - يحدّث الـ cache
        - يحفظ في DB عبر FontService
        - يبطّل caches الـ widgets
        """
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
        cls._font_size = size

        # تحديث module cache في font.py
        try:
            from ui.font import _set_module_font_cache
            _set_module_font_cache(size)
        except Exception:
            pass

        # الحفظ في DB عبر FontService (لا نتواصل مع DB مباشرة)
        try:
            from services.shared.font_service import FontService
            FontService.save(size)
        except Exception as e:
            logger.debug("AppState.on_font_changed: FontService.save failed — %s", e)

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
    def _load_font_size(cls) -> int:
        """
        يحمّل font_size عبر FontService.
        لا يتواصل مع DB مباشرة.
        """
        try:
            from services.shared.font_service import FontService
            return FontService.load()
        except Exception as e:
            logger.debug("AppState._load_font_size: FontService.load failed — %s", e)
            return DEFAULT_FONT_SIZE

    @classmethod
    def _invalidate_button_cache(cls):
        """يبطّل stylesheet cache الأزرار."""
        try:
            from ui.widgets.components.button import invalidate_stylesheet_cache
            invalidate_stylesheet_cache()
        except Exception as e:
            logger.debug("AppState._invalidate_button_cache: %s", e)
