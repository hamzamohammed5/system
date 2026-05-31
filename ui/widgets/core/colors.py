"""
ui/widgets/core/colors.py
==================================
لوحة الألوان الموحدة للتطبيق.

التغييرات:
  - status_colors() أصبحت دالة تقرأ من _C مباشرة
    بدل dict ثابت بـ hardcoded hex.
    هذا يضمن التزامن الكامل — لو غيّرت لون في _C
    يتغير تلقائياً في كل مكان يستخدم status_colors().

  - [إصلاح] status_colors() كانت تستورد من ui.app_settings (غير موجود كملف مستقل).
    المصدر الصحيح هو ui.theme حيث يُعرَّف _C.
    تغيير: from ui.app_settings import _C → from ui.theme import _C

  - [إصلاح ألوان] حذف _PURPLE_FALLBACK/_ORANGE_FALLBACK وغيرها —
    كانت مكررة من theme_manager.py. status_colors() تستخدم _C.get() مباشرة
    مع fallback من نفس الـ dict بدل ثوابت hardcoded منفصلة.

  - [إصلاح waste] WASTE_ZERO_BG/BORDER/COLOR/TEXT_COLOR أصبحت دوال
    تقرأ من _C بدل ثوابت hardcoded تتجمد عند أول import.
    الاستخدام: waste_zero_bg() بدل WASTE_ZERO_BG.

  - [إصلاح card_colors] إضافة _DARK_CARD_PALETTE و card_colors()
    تتحقق من الثيم الحالي تلقائياً.

  - [تحسين 10] تحقق من circular imports:
    هذا الملف لا يستورد من أي ملف يستورد منه — آمن.
"""

# ── لوحة ألوان البطاقات — Light Theme ────────────────────────────────────────
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

# ── لوحة ألوان البطاقات — Dark Theme ─────────────────────────────────────────
_DARK_CARD_PALETTE: dict[str, tuple[str, str]] = {
    # أزرق
    "#1565c0": ("#1a2a3a", "#2a4a6a"),
    "#0d47a1": ("#152030", "#1e3a5f"),
    "#1d4ed8": ("#1a2540", "#2a4080"),
    "#1e40af": ("#1a2540", "#2a4080"),
    "#0891b2": ("#0a2830", "#1a5060"),
    "#0369a1": ("#0a2030", "#1a4060"),
    # أخضر
    "#10b981": ("#0a2820", "#1a5040"),
    "#2e7d32": ("#0a2010", "#1a4020"),
    "#065f46": ("#0a2818", "#1a5030"),
    "#15803d": ("#0a2018", "#1a4030"),
    "#16a34a": ("#0a2018", "#1a4030"),
    # أحمر
    "#ef4444": ("#2a1010", "#5a2020"),
    "#dc2626": ("#2a1010", "#5a2020"),
    "#c62828": ("#281010", "#4a1818"),
    "#991b1b": ("#2a1010", "#4a1818"),
    "#b91c1c": ("#2a1010", "#4a1818"),
    # برتقالي / أصفر
    "#f59e0b": ("#2a2000", "#4a3800"),
    "#e65100": ("#281400", "#503000"),
    "#b45309": ("#281c00", "#4a3400"),
    "#d97706": ("#281c00", "#4a3400"),
    "#ea580c": ("#281800", "#503800"),
    # رمادي
    "#6b7280": ("#1e2028", "#2e3040"),
    "#374151": ("#1a1c24", "#2a2e38"),
    "#9ca3af": ("#1e2028", "#2e3040"),
    "#555555": ("#1e1e1e", "#2e2e2e"),
    "#555":    ("#1e1e1e", "#2e2e2e"),
    "#4b5563": ("#1a1c24", "#2a2e38"),
    # بنفسجي / وردي
    "#8b5cf6": ("#1a1028", "#3a2060"),
    "#6d28d9": ("#180c28", "#301860"),
    "#6a1b9a": ("#1a0828", "#3a1060"),
    "#7c3aed": ("#1a0c2a", "#341860"),
    "#9333ea": ("#1c0a28", "#3c1860"),
    "#db2777": ("#280a18", "#501830"),
    "#be185d": ("#280a18", "#501830"),
    # بني
    "#4e342e": ("#201010", "#3a1c18"),
    "#5d4037": ("#221210", "#3c1e18"),
}

_FALLBACK: tuple[str, str] = ("#f5f5f5", "#e0e0e0")
_FALLBACK_DARK: tuple[str, str] = ("#2a2a2a", "#3a3a3a")


def card_colors(color: str) -> tuple[str, str]:
    """
    يرجع (bg, border) للون المعطى حسب الثيم الحالي.

    [إصلاح] يتحقق من theme_manager.is_dark تلقائياً —
    لو dark يرجع _DARK_CARD_PALETTE، وإلا CARD_PALETTE.
    """
    from ui.theme_manager import theme_manager
    if theme_manager.is_dark:
        return _DARK_CARD_PALETTE.get(color, _FALLBACK_DARK)
    return CARD_PALETTE.get(color, _FALLBACK)


# ── status_colors — مبنية من _C (بدل dict ثابت) ─────────────────────────────

def status_colors(level: str) -> dict[str, str]:
    """
    يرجع dict ألوان الـ status (fg, bg, border) من _C.

    [إصلاح] استبدال `from ui.app_settings import _C` بـ `from ui.theme import _C`.
    ui.app_settings ليس ملفاً مستقلاً — _C معرَّف في ui.theme وهو المصدر الوحيد.
    الـ import داخل الدالة (lazy) مقصود لتجنب circular imports — لا تنقله خارجها.

    [إصلاح fallbacks] حذف _PURPLE_FALLBACK/_ORANGE_FALLBACK وغيرها —
    كانت hardcoded مكررة من theme_manager. الـ fallback الآن من نفس _C
    (يرجع neutral عوضاً عن hardcoded hex).
    """
    from ui.theme import _C  # [إصلاح] المصدر الصحيح بدل ui.app_settings

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
        "purple": {
            # [إصلاح] _C.get() مع fallback من نفس _C — لا hardcoded fallback
            "fg":     _C.get("purple",        _C["text_sec"]),
            "bg":     _C.get("purple_bg",     _C["bg_surface_2"]),
            "border": _C.get("purple_border", _C["border"]),
        },
        "orange": {
            # [إصلاح] _C.get() مع fallback من نفس _C — لا hardcoded fallback
            "fg":     _C.get("orange",        _C["warning"]),
            "bg":     _C.get("orange_bg",     _C["warning_bg"]),
            "border": _C.get("orange_border", _C["warning_border"]),
        },
    }
    return _map.get(level, _map["neutral"])


# ── ألوان نسبة الهادر (waste) ─────────────────────────────────────────────────
# [إصلاح] WASTE_COLORS يبقى كـ dict ثابت — هو palette مستقل للمستويات
# وليس ألوان UI تتأثر بالثيم مباشرة.
WASTE_COLORS: dict[str, tuple[str, str]] = {
    "high":   ("#ffcdd2", "#e53935"),   # >= 20%
    "medium": ("#ffe0b2", "#f57c00"),   # >= 10%
    "low":    ("#fff8e1", "#ffe082"),   # > 0%
}


def waste_zero_bg() -> str:
    """
    [إصلاح] دالة بدل ثابت — تقرأ من _C الحالي عند كل استدعاء.
    القديم: WASTE_ZERO_BG = "#f5f5f5" (يتجمد عند import)
    الجديد: waste_zero_bg() → _C["waste_zero_bg"] (يعكس الثيم الحالي دائماً)
    """
    from ui.theme import _C
    return _C["waste_zero_bg"]


def waste_zero_border() -> str:
    """دالة بدل ثابت — تقرأ waste_zero_border من _C."""
    from ui.theme import _C
    return _C["waste_zero_border"]


def waste_zero_color() -> str:
    """دالة بدل ثابت — تقرأ waste_zero_color من _C."""
    from ui.theme import _C
    return _C["waste_zero_color"]


def waste_text_color() -> str:
    """
    دالة بدل ثابت — تقرأ orange من _C.
    WASTE_TEXT_COLOR كان "#e65100" = _C['orange'] في light theme.
    """
    from ui.theme import _C
    return _C["orange"]


def waste_level(pct: float) -> str:
    """يرجع مستوى الهادر: 'high' | 'medium' | 'low' | 'zero'."""
    if pct >= 20: return "high"
    if pct >= 10: return "medium"
    if pct > 0:   return "low"
    return "zero"


def waste_colors(pct: float) -> tuple[str, str]:
    """يرجع (bg, border) حسب نسبة الهادر."""
    level = waste_level(pct)
    return WASTE_COLORS.get(level, (waste_zero_bg(), waste_zero_border()))