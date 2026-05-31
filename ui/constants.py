"""
ui/constants.py
===============
ثوابت التطبيق — المصدر الوحيد لكل الثوابت.
لا يستورد من أي ملف آخر في ui/.
"""

# ── حجم الخط ──────────────────────────────────────────────
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20

# ── أبعاد الـ Sidebar ─────────────────────────────────────
SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56

# ── أبعاد النافذة ─────────────────────────────────────────
CONTENT_MIN_WIDTH = 820
WINDOW_DEFAULT_W  = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH