"""
ui/font_utils.py
================
أدوات مساعدة للخط النسبي.

بعد الـ refactoring:
  - الألوان كلها من _C في ui.app_settings — لا hardcoded
  - الـ style functions تستخدم get_font_size() و fs() فقط
  - الـ QLabel factories تفوّض لـ ui.widgets.panels.form_parts
    و ui.widgets.components.stat_row في الكود الجديد
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.app_settings import get_font_size, fs, _C


# ══════════════════════════════════════════════════════════
# دوال الـ stylesheet
# ══════════════════════════════════════════════════════════

def badge_style(side: str = "neutral") -> str:
    """ستايل badge (DR↑ / CR↑). side: 'dr' | 'cr' | 'neutral'"""
    b = get_font_size()
    if side == "dr":
        from ui.widgets.core.colors import status_colors
        s = status_colors("primary")
        return (
            f"font-size:{fs(b,-1)}pt; font-weight:bold; color:{s['fg']};"
            f"background:{s['bg']}; border-radius:3px; padding:2px 4px;"
        )
    if side == "cr":
        from ui.widgets.core.colors import status_colors
        s = status_colors("danger")
        return (
            f"font-size:{fs(b,-1)}pt; font-weight:bold; color:{s['fg']};"
            f"background:{s['bg']}; border-radius:3px; padding:2px 4px;"
        )
    return (
        f"font-size:{fs(b,-1)}pt; font-weight:bold;"
        "border-radius:3px; padding:2px 4px;"
    )


def card_title_style(color: str = None) -> str:
    b = get_font_size()
    c = color or _C['text_muted']
    return f"font-size:{fs(b,-1)}pt; color:{c}; background:transparent; border:none;"


def card_value_style(color: str = None) -> str:
    b = get_font_size()
    c = color or _C['accent']
    return (
        f"font-size:{fs(b,+1)}pt; font-weight:bold; color:{c};"
        "background:transparent; border:none;"
    )


def section_label_style(color: str = None) -> str:
    b = get_font_size()
    c = color or _C['text_primary']
    return f"font-weight:bold; font-size:{fs(b,+1)}pt; color:{c};"


def mode_label_style(color: str = None) -> str:
    b = get_font_size()
    c = color or _C['accent']
    return f"font-weight:bold; color:{c}; font-size:{fs(b,0)}pt;"


def hint_label_style(color: str = None) -> str:
    b = get_font_size()
    c = color or _C['text_sec']
    return (
        f"font-size:{fs(b,-1)}pt; color:{c};"
        f"background:{_C['accent_light']}; border-radius:4px; padding:4px 8px;"
    )


def count_label_style() -> str:
    b = get_font_size()
    return (
        f"color:{_C['accent']}; font-size:{fs(b,-1)}pt; font-weight:bold;"
        "background:transparent; border:none;"
    )


def group_title_style(color: str = None) -> str:
    b = get_font_size()
    c = color or _C['accent']
    return (
        f"font-weight:bold; color:{c}; font-size:{fs(b,+1)}pt;"
        f"border:1px solid {_C['border']}; border-radius:6px;"
        "margin-top:6px; padding-top:6px;"
    )


def header_label_style(color: str = None,
                        bg: str = None,
                        border: str = None) -> str:
    b = get_font_size()
    from ui.widgets.core.colors import card_colors
    c   = color  or _C['accent']
    _bg, _bdr = card_colors(c)
    bg  = bg     or _bg
    bdr = border or _bdr
    return (
        f"font-size:{fs(b,+1)}pt; font-weight:bold; color:{c};"
        f"background:{bg}; border:1px solid {bdr};"
        "border-radius:8px; padding:8px 16px;"
    )


# ══════════════════════════════════════════════════════════
# مقاسات الـ widgets الديناميكية
# ══════════════════════════════════════════════════════════

def widget_height() -> int:
    return get_font_size() * 2 + 6


def badge_width() -> int:
    return get_font_size() * 4


def small_btn_size() -> int:
    return get_font_size() * 2


# ══════════════════════════════════════════════════════════
# QLabel factories
# ══════════════════════════════════════════════════════════

def make_badge_label(text: str = "", side: str = "neutral") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(badge_style(side))
    lbl.setFixedWidth(badge_width())
    return lbl


def make_section_label(text: str, color: str = None) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(section_label_style(color))
    return lbl


def make_card_title(text: str, color: str = None) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(card_title_style(color))
    lbl.setAlignment(Qt.AlignCenter)
    return lbl


def make_card_value(text: str = "─", color: str = None) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(card_value_style(color))
    lbl.setAlignment(Qt.AlignCenter)
    return lbl


# ── aliases للتوافق مع الكود القديم ──────────────────────
styled_label = make_badge_label
badge_label  = make_badge_label
card_title   = make_card_title
card_value   = make_card_value
