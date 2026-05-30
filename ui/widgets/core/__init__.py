"""
ui/widgets/core/__init__.py
============================
نقطة تصدير موحدة لـ widgets/core.

يُحل الاستدعاءات من النوع:
    from ..core import get_font_size
"""
from ui.app_settings import get_font_size

__all__ = ["get_font_size"]