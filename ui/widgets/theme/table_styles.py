"""
ui/widgets/theme/table_styles.py
==================================
Stylesheet generators للجداول والـ splitters.

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.
"""
from ui.theme import _C
from ui.font  import fs, get_font_size

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48


def table_style(variant: str = "normal") -> str:
    """Stylesheet موحد للجداول."""
    base = get_font_size()
    c    = _C

    padding_map = {
        "compact": ("4px 6px",  "4px 6px",  fs(base, -1)),
        "large":   ("8px 12px", "8px 12px", fs(base,  0)),
    }
    item_pad, header_pad, font_sz = padding_map.get(
        variant, ("5px 10px", "6px 10px", fs(base, 0))
    )

    return f"""
        QTableWidget {{
            font-size:{font_sz}pt; color:{c['text_primary']};
            background:{c['bg_input']}; border:1px solid {c['border']};
            border-radius:8px; gridline-color:{c['border']};
            alternate-background-color:{c['bg_surface']}; outline:none;
        }}
        QTableWidget::item {{
            padding:{item_pad}; border:none;
            border-bottom:1px solid {c['border']};
        }}
        QTableWidget::item:selected {{
            background:{c['accent_light']}; color:{c['accent_text']};
        }}
        QTableWidget::item:hover {{ background:{c['bg_hover']}; }}
        QHeaderView::section {{
            font-size:{fs(base,-1)}pt; font-weight:600;
            color:{c['text_muted']}; background:{c['bg_surface_2']};
            border:none; border-bottom:2px solid {c['border_med']};
            border-right:1px solid {c['border']}; padding:{header_pad};
        }}
        QHeaderView::section:last {{ border-right:none; }}
        QHeaderView::section:hover {{
            background:{c['bg_hover']}; color:{c['text_primary']};
        }}
    """


def splitter_style() -> str:
    return f"""
        QSplitter::handle {{ background:{_C['border_med']}; border-radius:3px; }}
        QSplitter::handle:hover {{ background:{_C['accent_mid']}; }}
        QSplitter::handle:pressed {{ background:{_C['accent']}; }}
    """