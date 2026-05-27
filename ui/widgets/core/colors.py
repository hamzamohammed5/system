"""
ui/widgets/core/colors.py
==================================
لوحة الألوان الموحدة للتطبيق.

التغييرات:
  - status_colors() أصبحت دالة تقرأ من _C مباشرة
    بدل dict ثابت بـ hardcoded hex.
    هذا يضمن التزامن الكامل — لو غيّرت لون في _C
    يتغير تلقائياً في كل مكان يستخدم status_colors().
  - CARD_PALETTE لم يتغير — هو مصدر ألوان الكروت المستقل.
  - purple/orange محفوظان مؤقتاً كـ hardcoded لحين
    إضافتهم لـ _C في app_settings.
"""

# ── لوحة ألوان البطاقات (لون → (خلفية، حدود)) ──────────────────────────
CARD_PALETTE: dict[str, tuple[str, str]] = {
    # أزرق
    "#1565c0": ("#e8f0fe", "#90caf9"),
    "#0d47a1": ("#e3f2fd", "#64b5f6"),
    "#1d4ed8": ("#eff6ff", "#93c5fd"),
    "#1e40af": ("#eff6ff", "#93c5fd"),
    "#0891b2": ("#e0f7fa", "#80deea"),
    "#0369a1": ("#e0f2fe", "#7dd3fc"),
    # أخضر
    "#10b981": ("#ecfdf5", "#6ee7b7"),
    "#2e7d32": ("#e8f5e9", "#a5d6a7"),
    "#065f46": ("#ecfdf5", "#a7f3d0"),
    "#15803d": ("#f0fdf4", "#86efac"),
    "#16a34a": ("#f0fdf4", "#86efac"),
    # أحمر
    "#ef4444": ("#fef2f2", "#fca5a5"),
    "#dc2626": ("#fef2f2", "#fca5a5"),
    "#c62828": ("#ffebee", "#ef9a9a"),
    "#991b1b": ("#fef2f2", "#fecaca"),
    "#b91c1c": ("#fef2f2", "#fecaca"),
    # برتقالي / أصفر
    "#f59e0b": ("#fffbeb", "#fcd34d"),
    "#e65100": ("#fff3e0", "#ffcc80"),
    "#b45309": ("#fffbeb", "#fde68a"),
    "#d97706": ("#fffbeb", "#fde68a"),
    "#ea580c": ("#fff7ed", "#fdba74"),
    # رمادي
    "#6b7280": ("#f9fafb", "#d1d5db"),
    "#374151": ("#f9fafb", "#e5e7eb"),
    "#9ca3af": ("#f9fafb", "#e5e7eb"),
    "#555555": ("#f5f5f5", "#e0e0e0"),
    "#555":    ("#f5f5f5", "#e0e0e0"),
    "#4b5563": ("#f9fafb", "#d1d5db"),
    # بنفسجي / وردي
    "#8b5cf6": ("#f5f3ff", "#c4b5fd"),
    "#6d28d9": ("#f5f3ff", "#ddd6fe"),
    "#6a1b9a": ("#f3e5f5", "#ce93d8"),
    "#7c3aed": ("#f5f3ff", "#c4b5fd"),
    "#9333ea": ("#faf5ff", "#d8b4fe"),
    "#db2777": ("#fdf2f8", "#f9a8d4"),
    "#be185d": ("#fdf2f8", "#fbcfe8"),
    # بني
    "#4e342e": ("#efebe9", "#bcaaa4"),
    "#5d4037": ("#efebe9", "#bcaaa4"),
}

_FALLBACK: tuple[str, str] = ("#f5f5f5", "#e0e0e0")


def card_colors(color: str) -> tuple[str, str]:
    """يرجع (bg, border) للون المعطى، أو الـ fallback لو مش موجود."""
    return CARD_PALETTE.get(color, _FALLBACK)


# ── status_colors — مبنية من _C (بدل dict ثابت) ─────────────────────────────

def status_colors(level: str) -> dict[str, str]:
    """
    يرجع dict ألوان الـ status (fg, bg, border) من _C.

    التغيير: بدل STATUS_COLORS dict ثابت بـ hardcoded hex،
    الدالة دي بتبني الـ map من _C في كل استدعاء.

    الفايدة: لو غيّرت _C["danger"] في app_settings،
    كل widget بيستخدم status_colors("danger") يتحدث تلقائياً
    بدون ما تحتاج تعدل ملف تاني.

    ملاحظة: purple/orange مش موجودين في _C حالياً.
    عشان تنظفهم 100%، أضف للـ _C في app_settings:
        "purple": "#6a1b9a",  "purple_bg": "#f3e5f5",  "purple_border": "#ce93d8"
        "orange": "#e65100",  "orange_bg": "#fff3e0",  "orange_border": "#ffcc80"
    """
    from ui.app_settings import _C

    _map: dict[str, dict[str, str]] = {
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
        # TODO: أضف لـ _C عشان تنظفهم
        "purple": {"fg": "#6a1b9a", "bg": "#f3e5f5", "border": "#ce93d8"},
        "orange": {"fg": "#e65100", "bg": "#fff3e0", "border": "#ffcc80"},
    }
    return _map.get(level, _map["neutral"])


# ── ألوان نسبة الهادر (waste) ─────────────────────────────────────────────
# المصدر الوحيد — لا تعريف لهذه الألوان في أي ملف آخر
WASTE_COLORS: dict[str, tuple[str, str]] = {
    "high":   ("#ffcdd2", "#e53935"),   # >= 20%
    "medium": ("#ffe0b2", "#f57c00"),   # >= 10%
    "low":    ("#fff8e1", "#ffe082"),   # > 0%
}

WASTE_ZERO_BG     = "#f5f5f5"
WASTE_ZERO_BORDER = "#e0e0e0"
WASTE_ZERO_COLOR  = "#999"
WASTE_TEXT_COLOR  = "#e65100"


def waste_level(pct: float) -> str:
    """يرجع مستوى الهادر: 'high' | 'medium' | 'low' | 'zero'."""
    if pct >= 20: return "high"
    if pct >= 10: return "medium"
    if pct > 0:   return "low"
    return "zero"


def waste_colors(pct: float) -> tuple[str, str]:
    """يرجع (bg, border) حسب نسبة الهادر."""
    level = waste_level(pct)
    return WASTE_COLORS.get(level, (WASTE_ZERO_BG, WASTE_ZERO_BORDER))