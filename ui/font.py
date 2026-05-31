"""
ui/font.py
==========
إدارة حجم الخط — المصدر الوحيد لكل عمليات الخط.

المسؤولية:
  - قراءة وحفظ حجم الخط (get_font_size / set_font_size)
  - حجم خط نسبي (fs)
  - تطبيق الخط على الـ app (apply_font)
  - module-level cache للأداء
"""

from __future__ import annotations
from PyQt5.QtWidgets import QApplication
from ui.constants import DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE

# ── Module-level cache [تحسين 43] ─────────────────────────
# يُخزن حجم الخط الحالي بدون قراءة من DB في كل مرة
_module_font_size: int | None = None


def _set_module_font_cache(size: int | None):
    """يحدّث الـ module-level font cache. للاستخدام الداخلي."""
    global _module_font_size
    _module_font_size = size


def get_font_size() -> int:
    """
    يرجع حجم الخط الحالي.
    يقرأ من الـ module cache أولاً — إن لم يوجد يقرأ من AppState.
    """
    global _module_font_size
    if _module_font_size is not None:
        return _module_font_size
    from ui.app_state import AppState
    size = AppState.font_size()
    _module_font_size = size
    return size


def set_font_size(size: int):
    """
    يحدّث حجم الخط — cache أولاً ثم AppState ثم DB.
    """
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
    _set_module_font_cache(size)

    from ui.app_state import AppState
    AppState.on_font_changed(size)

    try:
        from db.shared.connection import get_connection
        from db.shared.settings_repo import set_setting
        conn = get_connection()
        set_setting(conn, "font_size", size)
    except Exception:
        pass


def fs(base: int, delta: int = 0) -> int:
    """
    يرجع حجم خط نسبي.
    الحد الأدنى = MIN_FONT_SIZE دائماً.
    """
    return max(MIN_FONT_SIZE, base + delta)


def apply_font(app: QApplication, size: int = None):
    """
    يطبّق حجم الخط على الـ app — يُعيد بناء الـ stylesheet.
    """
    if size is None:
        size = get_font_size()
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))

    _set_module_font_cache(size)

    from ui.app_state import AppState
    AppState.on_font_changed(size)

    # الـ stylesheet يُبنى من theme.py
    from ui.theme import build_stylesheet
    app.setStyleSheet(build_stylesheet(size))