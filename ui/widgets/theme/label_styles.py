"""
ui/widgets/theme/label_styles.py
==================================
Stylesheet generators للـ labels والأزرار النصية.

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.
"""
from ui.theme import _C
from ui.font  import fs, get_font_size


def status_label_style(status: str = "info", font_offset: int = 0) -> str:
    from ui.widgets.core.colors import status_colors
    base = get_font_size()
    s = status_colors(status)
    return (
        f"font-size:{fs(base,font_offset)}pt; font-weight:bold;"
        f"color:{s['fg']}; background:{s['bg']};"
        f"border:1px solid {s['border']}; border-radius:6px; padding:6px 14px;"
    )


def muted_label_style(font_offset: int = -1) -> str:
    base = get_font_size()
    return (
        f"color:{_C['text_muted']}; font-size:{fs(base,font_offset)}pt;"
        "background:transparent; border:none;"
    )


def section_title_style(color: str = None, font_offset: int = 0) -> str:
    base = get_font_size()
    c = color or _C["text_primary"]
    return (
        f"font-weight:bold; font-size:{fs(base,font_offset)}pt;"
        f"color:{c}; background:transparent; border:none;"
    )


def icon_btn_style(color: str = "#aaa", hover_color: str = "#e53935") -> str:
    return (
        f"QPushButton {{ background:transparent; border:none; color:{color}; }}"
        f"QPushButton:hover {{ color:{hover_color}; }}"
    )


def link_btn_style(color: str = None) -> str:
    base = get_font_size()
    c = color or _C["accent"]
    return f"""
        QPushButton {{
            background:transparent; border:none;
            color:{c}; font-size:{fs(base,0)}pt;
            text-decoration:underline; padding:0;
        }}
        QPushButton:hover {{ color:{c}cc; }}
    """