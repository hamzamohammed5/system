"""
ui/widgets/theme/table_styles.py
==================================
Stylesheet generators للجداول والـ splitters.

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.
"""
from ui.theme import _C
from ui.font  import fs, get_font_size
from ui.constants import (
    ROW_HEIGHT_COMPACT, ROW_HEIGHT_NORMAL, ROW_HEIGHT_LARGE, TABLE_BORDER_RADIUS,
    TABLE_STYLE_COMPACT_ITEM_PAD_V, TABLE_STYLE_COMPACT_ITEM_PAD_H,
    TABLE_STYLE_LARGE_ITEM_PAD_V, TABLE_STYLE_LARGE_ITEM_PAD_H,
    TABLE_STYLE_NORMAL_ITEM_PAD_V, TABLE_STYLE_NORMAL_ITEM_PAD_H,
    TABLE_STYLE_NORMAL_HEADER_PAD_V, TABLE_STYLE_NORMAL_HEADER_PAD_H,
    SPLITTER_HANDLE_RADIUS,
)


def table_style(variant: str = "normal") -> str:
    """Stylesheet موحد للجداول."""
    base = get_font_size()
    c    = _C

    padding_map = {
        "compact": (f"{TABLE_STYLE_COMPACT_ITEM_PAD_V}px {TABLE_STYLE_COMPACT_ITEM_PAD_H}px",
                    f"{TABLE_STYLE_COMPACT_ITEM_PAD_V}px {TABLE_STYLE_COMPACT_ITEM_PAD_H}px",
                    fs(base, -1)),
        "large":   (f"{TABLE_STYLE_LARGE_ITEM_PAD_V}px {TABLE_STYLE_LARGE_ITEM_PAD_H}px",
                    f"{TABLE_STYLE_LARGE_ITEM_PAD_V}px {TABLE_STYLE_LARGE_ITEM_PAD_H}px",
                    fs(base,  0)),
    }
    item_pad, header_pad, font_sz = padding_map.get(
        variant,
        (f"{TABLE_STYLE_NORMAL_ITEM_PAD_V}px {TABLE_STYLE_NORMAL_ITEM_PAD_H}px",
         f"{TABLE_STYLE_NORMAL_HEADER_PAD_V}px {TABLE_STYLE_NORMAL_HEADER_PAD_H}px",
         fs(base, 0))
    )

    return f"""
        QTableWidget {{
            font-size:{font_sz}pt; color:{c['text_primary']};
            background:{c['bg_input']}; border:1px solid {c['border']};
            border-radius:{TABLE_BORDER_RADIUS}px; gridline-color:{c['border']};
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
        QSplitter::handle {{ background:{_C['border_med']}; border-radius:{SPLITTER_HANDLE_RADIUS}px; }}
        QSplitter::handle:hover {{ background:{_C['accent_mid']}; }}
        QSplitter::handle:pressed {{ background:{_C['accent']}; }}
    """