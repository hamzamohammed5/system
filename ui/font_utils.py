"""
ui/font_utils.py
================
أدوات مساعدة للخط النسبي — تُستخدم في كل الـ widgets بدل
الـ font-size الـ hard-coded.

الاستخدام:
    from ui.font_utils import styled_label, badge_label, card_title, card_value

    lbl = styled_label("DR↑", role="badge")
    lbl.setStyleSheet(badge_style("dr"))
"""

from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt

from ui.app_settings import get_font_size, fs


# ══════════════════════════════════════════════════════════
# دوال الـ stylesheet الديناميكية
# ══════════════════════════════════════════════════════════

def _base() -> int:
    """الحجم الأساسي الحالي."""
    return get_font_size()


def badge_style(side: str = "neutral") -> str:
    """
    ستايل الـ badge (DR↑ / CR↑).
    side: "dr" | "cr" | "neutral"
    """
    b = _base()
    if side == "dr":
        return (
            f"font-size:{fs(b,-1)}pt; font-weight:bold; color:#1565c0;"
            "background:#e3f2fd; border-radius:3px; padding:2px 4px;"
        )
    elif side == "cr":
        return (
            f"font-size:{fs(b,-1)}pt; font-weight:bold; color:#c62828;"
            "background:#fdecea; border-radius:3px; padding:2px 4px;"
        )
    return (
        f"font-size:{fs(b,-1)}pt; font-weight:bold;"
        "border-radius:3px; padding:2px 4px;"
    )


def card_title_style(color: str = "#888") -> str:
    b = _base()
    return f"font-size:{fs(b,-1)}pt; color:{color}; background:transparent; border:none;"


def card_value_style(color: str = "#1565c0") -> str:
    b = _base()
    return (
        f"font-size:{fs(b,+1)}pt; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )


def section_label_style(color: str = "#333") -> str:
    b = _base()
    return f"font-weight:bold; font-size:{fs(b,+1)}pt; color:{color};"


def mode_label_style(color: str = "#1565c0") -> str:
    b = _base()
    return f"font-weight:bold; color:{color}; font-size:{fs(b,0)}pt;"


def hint_label_style(color: str = "#555") -> str:
    b = _base()
    return (
        f"font-size:{fs(b,-1)}pt; color:{color};"
        "background:#e8f0fe; border-radius:4px; padding:4px 8px;"
    )


def count_label_style() -> str:
    b = _base()
    return (
        f"color:#1565c0; font-size:{fs(b,-1)}pt; font-weight:bold;"
        "background:transparent; border:none;"
    )


def group_title_style(color: str = "#1565c0") -> str:
    b = _base()
    return (
        f"font-weight:bold; color:{color}; font-size:{fs(b,+1)}pt;"
        "border:1px solid #e0e0e0; border-radius:6px;"
        "margin-top:6px; padding-top:6px;"
    )


def header_label_style(color: str = "#1565c0",
                        bg: str = "#e8f4fd",
                        border: str = "#90caf9") -> str:
    b = _base()
    return (
        f"font-size:{fs(b,+1)}pt; font-weight:bold; color:{color};"
        f"background:{bg}; border:1px solid {border};"
        "border-radius:8px; padding:8px 16px;"
    )


# ══════════════════════════════════════════════════════════
# مقاسات الـ widgets الديناميكية
# ══════════════════════════════════════════════════════════

def widget_height() -> int:
    """ارتفاع قياسي للـ inputs والأزرار."""
    return _base() * 2 + 6


def badge_width() -> int:
    """عرض الـ badge (DR↑ / CR↑) — نسبي من حجم الخط."""
    return _base() * 4


def small_btn_size() -> int:
    """حجم الأزرار الصغيرة (مثل ▲ ▼ ✖)."""
    return _base() * 2


# ══════════════════════════════════════════════════════════
# QLabel factories
# ══════════════════════════════════════════════════════════

def make_badge_label(text: str = "", side: str = "neutral") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(badge_style(side))
    lbl.setFixedWidth(badge_width())
    return lbl


def make_section_label(text: str, color: str = "#333") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(section_label_style(color))
    return lbl


def make_card_title(text: str, color: str = "#888") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(card_title_style(color))
    lbl.setAlignment(Qt.AlignCenter)
    return lbl


def make_card_value(text: str = "─", color: str = "#1565c0") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(card_value_style(color))
    lbl.setAlignment(Qt.AlignCenter)
    return lbl