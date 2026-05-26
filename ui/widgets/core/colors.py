"""
ui/widgets/core/colors.py
==================================
لوحة الألوان الموحدة للتطبيق.

المصدر الوحيد لألوان البطاقات وحالات الـ status.
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

# Fallback لأي لون غير موجود في الـ palette
_FALLBACK: tuple[str, str] = ("#f5f5f5", "#e0e0e0")


def card_colors(color: str) -> tuple[str, str]:
    """يرجع (bg, border) للون المعطى، أو الـ fallback لو مش موجود."""
    return CARD_PALETTE.get(color, _FALLBACK)


# ── ألوان حالات الـ status ────────────────────────────────────────────────
STATUS_COLORS: dict[str, dict[str, str]] = {
    "success": {"fg": "#065f46", "bg": "#ecfdf5", "border": "#6ee7b7"},
    "warning": {"fg": "#92400e", "bg": "#fffbeb", "border": "#fcd34d"},
    "danger":  {"fg": "#991b1b", "bg": "#fef2f2", "border": "#fca5a5"},
    "info":    {"fg": "#1e40af", "bg": "#eff6ff", "border": "#93c5fd"},
    "neutral": {"fg": "#374151", "bg": "#f9fafb", "border": "#d1d5db"},
    "primary": {"fg": "#1565c0", "bg": "#e8f0fe", "border": "#90caf9"},
    "purple":  {"fg": "#6a1b9a", "bg": "#f3e5f5", "border": "#ce93d8"},
    "orange":  {"fg": "#e65100", "bg": "#fff3e0", "border": "#ffcc80"},
}


def status_colors(level: str) -> dict[str, str]:
    """يرجع dict ألوان الـ status (fg, bg, border)."""
    return STATUS_COLORS.get(level, STATUS_COLORS["neutral"])