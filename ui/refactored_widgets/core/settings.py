"""
ui/widgets/core/settings.py
===================================
نقطة وصول موحدة لإعدادات التطبيق (حجم الخط، الألوان).

لا توجد منطق هنا — فقط تمرير من app_settings.
"""
from ui.app_settings import get_font_size, fs, _C  # noqa: F401


def get_base() -> int:
    """حجم الخط الأساسي الحالي."""
    return get_font_size()