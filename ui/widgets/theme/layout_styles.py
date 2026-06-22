"""
ui/widgets/theme/layout_styles.py
====================================
Stylesheet generators للـ layout widgets (tabs, scroll, tree, list, etc).

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.
"""
from ui.theme import _C
from ui.font  import fs, get_font_size
from ui.constants import SCROLL_BAR_WIDTH, TAB_MIN_W_SMALL, TAB_MIN_W_NORMAL, FILTER_TOOLBAR_BORDER_RADIUS, FILTER_BAR_BORDER_RADIUS, TREE_BORDER_RADIUS, LIST_BORDER_RADIUS


def tab_style(accent: str = None, size: str = "normal") -> str:
    """
    Stylesheet للتبويبات.
    size: "normal" | "inner" | "small"
    """
    base     = get_font_size()
    c        = accent or _C["accent"]
    is_small = size in ("inner", "small")
    padding  = "6px 12px" if is_small else "8px 16px"
    font_sz  = fs(base, -1) if is_small else fs(base, 0)
    min_w    = f"{TAB_MIN_W_SMALL}px" if is_small else f"{TAB_MIN_W_NORMAL}px"

    return f"""
        QTabWidget::pane {{ border:none; background:{_C['bg_page']}; }}
        QTabBar::tab {{
            background:{_C['bg_surface_2']}; border:1px solid {_C['border']};
            border-bottom:none; padding:{padding}; margin-left:2px;
            font-size:{font_sz}pt; color:{_C['text_muted']}; min-width:{min_w};
        }}
        QTabBar::tab:selected {{
            background:{_C['bg_input']}; color:{c};
            font-weight:bold; border-top:2px solid {c};
        }}
        QTabBar::tab:hover:!selected {{
            background:{_C['bg_hover']}; color:{_C['text_primary']};
        }}
    """


def scroll_style(width: int = SCROLL_BAR_WIDTH) -> str:
    """Stylesheet موحد لـ QScrollArea / QScrollBar — المصدر الوحيد."""
    r = width // 2
    return f"""
        QScrollArea {{ border:none; background:transparent; }}
        QScrollBar:vertical {{
            background:transparent; width:{width}px; border-radius:{r}px;
        }}
        QScrollBar::handle:vertical {{
            background:{_C['border_med']}; border-radius:{r}px; min-height:30px;
        }}
        QScrollBar::handle:vertical:hover {{ background:{_C['border_strong']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
        QScrollBar:horizontal {{
            background:transparent; height:{width}px; border-radius:{r}px;
        }}
        QScrollBar::handle:horizontal {{
            background:{_C['border_med']}; border-radius:{r}px; min-width:30px;
        }}
        QScrollBar::handle:horizontal:hover {{ background:{_C['border_strong']}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0px; }}
    """


def filter_bar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_surface_2']}; border:1px solid {_C['border']};
            border-radius:{FILTER_BAR_BORDER_RADIUS}px;
        }}
    """


def toolbar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_input']};
            border-bottom:1px solid {_C['border']};
        }}
    """


def tree_style() -> str:
    return f"""
        QTreeWidget {{
            border:1px solid {_C['border']}; border-radius:{TREE_BORDER_RADIUS}px;
            background:{_C['bg_surface']}; outline:none;
        }}
        QTreeWidget::item {{ padding:3px 2px; }}
        QTreeWidget::item:selected {{
            background:{_C['accent_light']}; color:{_C['accent_text']};
        }}
        QTreeWidget::item:hover:!selected {{ background:{_C['bg_hover']}; }}
    """


def list_style() -> str:
    return f"""
        QListWidget {{
            border:1px solid {_C['border']}; border-radius:{LIST_BORDER_RADIUS}px;
            background:{_C['bg_surface']}; outline:none;
        }}
        QListWidget::item {{
            padding:3px 6px; border-bottom:1px solid {_C['border']};
        }}
        QListWidget::item:selected {{
            background:{_C['accent_light']}; color:{_C['accent_text']};
        }}
        QListWidget::item:hover:!selected {{ background:{_C['bg_hover']}; }}
    """
