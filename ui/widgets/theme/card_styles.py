"""
ui/widgets/theme/card_styles.py
=================================
Stylesheet generators للبطاقات والـ frames.

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.
"""
from ui.theme import _C
from ui.font  import fs, get_font_size
from ui.constants import CARD_BORDER_RADIUS, STATUS_CARD_STYLE_RADIUS, FORM_GROUP_MARGIN_TOP, FORM_GROUP_PADDING_TOP, FORM_GROUP_TITLE_PAD_H, FORM_GROUP_BORDER_RADIUS


def card_style(bg: str = None, border: str = None, radius: int = CARD_BORDER_RADIUS) -> str:
    return f"""
        QFrame {{
            background:{bg or _C['bg_surface']};
            border:1px solid {border or _C['border']};
            border-radius:{radius}px;
        }}
    """


def status_card_style(status: str = "info", radius: int = STATUS_CARD_STYLE_RADIUS) -> str:
    from ui.widgets.core.colors import status_colors
    s = status_colors(status)
    return f"""
        QFrame {{
            background:{s['bg']}; border:1px solid {s['border']};
            border-radius:{radius}px;
        }}
    """


def group_box_style(accent: str = None) -> str:
    base  = get_font_size()
    color = accent or _C["accent"]
    return f"""
        QGroupBox {{
            font-weight:700; font-size:{fs(base,0)}pt;
            color:{_C['text_sec']}; background:{_C['bg_surface']};
            border:1px solid {_C['border']}; border-radius:{FORM_GROUP_BORDER_RADIUS}px;
            margin-top:{FORM_GROUP_MARGIN_TOP}px; padding-top:{FORM_GROUP_PADDING_TOP}px;
        }}
        QGroupBox::title {{
            subcontrol-origin:margin; subcontrol-position:top right;
            padding:0 {FORM_GROUP_TITLE_PAD_H}px; color:{color};
        }}
    """