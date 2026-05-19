"""
ui/widgets/shared/panles_helper/colors_and_base.py
"""
from ui.app_settings import get_font_size

def _base() -> int:
    return get_font_size()

_CARD_PALETTE = {
    "#1565c0": ("#e8f0fe", "#90caf9"),
    "#0d47a1": ("#e3f2fd", "#64b5f6"),
    "#1d4ed8": ("#eff6ff", "#93c5fd"),
    "#10b981": ("#ecfdf5", "#6ee7b7"),
    "#2e7d32": ("#e8f5e9", "#a5d6a7"),
    "#065f46": ("#ecfdf5", "#a7f3d0"),
    "#ef4444": ("#fef2f2", "#fca5a5"),
    "#dc2626": ("#fef2f2", "#fca5a5"),
    "#c62828": ("#ffebee", "#ef9a9a"),
    "#991b1b": ("#fef2f2", "#fecaca"),
    "#f59e0b": ("#fffbeb", "#fcd34d"),
    "#e65100": ("#fff3e0", "#ffcc80"),
    "#b45309": ("#fffbeb", "#fde68a"),
    "#6b7280": ("#f9fafb", "#d1d5db"),
    "#374151": ("#f9fafb", "#e5e7eb"),
    "#8b5cf6": ("#f5f3ff", "#c4b5fd"),
    "#6d28d9": ("#f5f3ff", "#ddd6fe"),
    "#6a1b9a": ("#f3e5f5", "#ce93d8"),
    "#9ca3af": ("#f9fafb", "#e5e7eb"),
    "#555555": ("#f5f5f5", "#e0e0e0"),
    "#555":    ("#f5f5f5", "#e0e0e0"),
}

def _card_colors(color: str) -> tuple:
    return _CARD_PALETTE.get(color, ("#f5f5f5", "#e0e0e0"))