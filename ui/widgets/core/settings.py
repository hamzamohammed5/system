"""
ui/widgets/core/settings.py
===================================
نقطة وصول موحدة لإعدادات التطبيق (حجم الخط، الألوان).

دمج: core/base.py + core/settings.py
"""
from ui.app_settings import get_font_size, fs, _C  # noqa: F401


def get_base() -> int:
    """حجم الخط الأساسي الحالي."""
    return get_font_size()


# ── helpers للألوان والقيم الشائعة ────────────────────────
# (كانت في core/base.py — مدموجة هنا مباشرة)

def _base() -> int:
    return get_font_size()


def _accent() -> str:
    return _C.get("accent", "#1565c0")


def _text_primary() -> str:
    return _C.get("text_primary", "#1c1b18")


def _text_muted() -> str:
    return _C.get("text_muted", "#9ca3af")


def _text_sec() -> str:
    return _C.get("text_sec", "#555555")


def _bg_surface() -> str:
    return _C.get("bg_surface", "#ffffff")


def _bg_input() -> str:
    return _C.get("bg_input", "#f9f9f9")


def _border() -> str:
    return _C.get("border", "#e0e0e0")


def _border_med() -> str:
    return _C.get("border_med", "#bdbdbd")