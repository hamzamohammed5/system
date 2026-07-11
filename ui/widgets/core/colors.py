"""
ui/widgets/core/colors.py
==================================
لوحة الألوان الموحدة للتطبيق.

[تحديث] كل الألوان الـ hardcoded انتقلت لـ ui/theme_manager.py.
هذا الملف لا يحتوي على أي لون hardcoded — كل شيء يُقرأ من _C.

المصدر الوحيد للألوان: ui/theme_manager.py
  ↓
الألوان النشطة:          ui/theme.py (_C dict)
  ↓
هذا الملف:               دوال helper تقرأ من _C فقط

التغييرات:
  - [نقل] WASTE_COLORS (dict ثابت) حُذف — استُبدل بدالة waste_colors()
    تقرأ من _C الحالي (waste_high/medium/low من theme_manager).
  - [نقل] _FALLBACK / _FALLBACK_DARK حُذفا — استُبدلا بـ card_fallback_bg/border
    من _C عبر theme_manager.
  - [نقل] CARD_PALETTE و _DARK_CARD_PALETTE حُذفا من هنا ونُقلا إلى
    theme_manager.CARD_PALETTES — المصدر الوحيد لألوان البطاقات.
  - waste_zero_* و card_colors() و status_colors() كلها تقرأ من _C ✅
"""


def card_colors(color: str) -> tuple:
    """
    يرجع (bg, border) للون المعطى حسب الثيم الحالي.
    المصدر الوحيد: theme_manager.CARD_PALETTES
    الـ fallback يجي من _C (card_fallback_bg/border) المعرَّف في theme_manager.
    """
    from ui.theme import _C
    from ui.theme_manager import theme_manager, CARD_PALETTES
    palette = CARD_PALETTES.get(theme_manager.current_theme, CARD_PALETTES["light"])
    return palette.get(
        color,
        (_C["card_fallback_bg"], _C["card_fallback_border"])
    )


# ── status_colors — مبنية من _C ──────────────────────────────────────────────

def status_colors(level: str) -> dict:
    """
    يرجع dict ألوان الـ status (fg, bg, border) من _C.
    المصدر الوحيد: ui/theme_manager.py عبر _C.
    """
    from ui.theme import _C

    _map = {
        "success": {
            "fg":     _C["success"],
            "bg":     _C["success_bg"],
            "border": _C["success_border"],
        },
        "warning": {
            "fg":     _C["warning"],
            "bg":     _C["warning_bg"],
            "border": _C["warning_border"],
        },
        "danger": {
            "fg":     _C["danger"],
            "bg":     _C["danger_bg"],
            "border": _C["danger_border"],
        },
        "info": {
            "fg":     _C["info"],
            "bg":     _C["info_bg"],
            "border": _C["info_border"],
        },
        "neutral": {
            "fg":     _C["text_sec"],
            "bg":     _C["bg_surface_2"],
            "border": _C["border"],
        },
        "primary": {
            "fg":     _C["accent_text"],
            "bg":     _C["accent_light"],
            "border": _C["accent_mid"],
        },
        "purple": {
            "fg":     _C.get("purple",        _C["text_sec"]),
            "bg":     _C.get("purple_bg",     _C["bg_surface_2"]),
            "border": _C.get("purple_border", _C["border"]),
        },
        "orange": {
            "fg":     _C.get("orange",        _C["warning"]),
            "bg":     _C.get("orange_bg",     _C["warning_bg"]),
            "border": _C.get("orange_border", _C["warning_border"]),
        },
    }
    return _map.get(level, _map["neutral"])


# ── ألوان نسبة الهادر (waste) ─────────────────────────────────────────────────

def waste_level(pct: float) -> str:
    """يرجع مستوى الهادر: 'high' | 'medium' | 'low' | 'zero'."""
    from ui.constants import WASTE_LEVEL_HIGH_THRESHOLD_PCT, WASTE_LEVEL_MEDIUM_THRESHOLD_PCT
    if pct >= WASTE_LEVEL_HIGH_THRESHOLD_PCT: return "high"
    if pct >= WASTE_LEVEL_MEDIUM_THRESHOLD_PCT: return "medium"
    if pct > 0:   return "low"
    return "zero"


def waste_colors(pct: float) -> tuple:
    """
    يرجع (bg, border) حسب نسبة الهادر — يقرأ من _C الحالي.
    الألوان معرَّفة في theme_manager.py لكل ثيم.
    """
    from ui.theme import _C
    level = waste_level(pct)
    if level == "zero":
        return (_C["waste_zero_bg"], _C["waste_zero_border"])
    return (_C[f"waste_{level}_bg"], _C[f"waste_{level}_border"])


def waste_zero_bg() -> str:
    """يرجع waste_zero_bg من _C الحالي."""
    from ui.theme import _C
    return _C["waste_zero_bg"]


def waste_zero_border() -> str:
    """يرجع waste_zero_border من _C الحالي."""
    from ui.theme import _C
    return _C["waste_zero_border"]


def waste_zero_color() -> str:
    """يرجع waste_zero_color من _C الحالي."""
    from ui.theme import _C
    return _C["waste_zero_color"]


def waste_text_color() -> str:
    """يرجع orange من _C الحالي — لون نص الهادر."""
    from ui.theme import _C
    return _C["orange"]