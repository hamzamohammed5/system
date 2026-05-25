"""
ui/widgets/theme/styles.py
===================================
كل الـ stylesheet generators في مكان واحد.

دمج: theme.py + table_styles.py + كل الستايلات المتفرقة
"""
from ui.app_settings import _C, fs
from ..core.settings import get_base


# ══════════════════════════════════════════════════════════════════
# Inputs
# ══════════════════════════════════════════════════════════════════

def input_style(height: int = 32, error: bool = False) -> str:
    """Stylesheet موحد لـ QLineEdit / QComboBox / QDateEdit."""
    base   = get_base()
    bg     = "#fef2f2" if error else _C["bg_input"]
    border = "#f87171" if error else _C["border_med"]
    return (
        f"background:{bg}; border:1.5px solid {border};"
        f"border-radius:6px; padding:0 8px;"
        f"font-size:{fs(base,0)}pt; color:{_C['text_primary']};"
        f"min-height:{height}px;"
    )


def spinbox_style(height: int = 32, positive: bool = False,
                  widget: str = "QDoubleSpinBox") -> str:
    """Stylesheet موحد لـ QDoubleSpinBox / QSpinBox."""
    base = get_base()
    if positive:
        bg, border, color, weight = "#f0fdf4", "#86efac", "#15803d", "bold"
    else:
        bg = _C["bg_input"]
        border = _C["border_med"]
        color = _C["text_primary"]
        weight = "normal"
    return f"""
        {widget} {{
            background:{bg}; border:1.5px solid {border};
            border-radius:6px; padding:0 8px;
            font-size:{fs(base,0)}pt; color:{color};
            font-weight:{weight}; min-height:{height}px;
        }}
        {widget}:focus {{ border-color:{_C['accent']}; background:white; }}
        {widget}:disabled {{
            background:{_C['bg_surface_2']}; color:{_C['text_disabled']};
        }}
    """


def search_input_style(height: int = 34) -> str:
    """Stylesheet لحقول البحث."""
    base = get_base()
    return f"""
        QLineEdit {{
            background:{_C['bg_input']};
            border:1.5px solid {_C['border_med']};
            border-radius:6px; padding:0 10px;
            font-size:{fs(base,0)}pt; color:{_C['text_primary']};
        }}
        QLineEdit:focus {{ border-color:{_C['accent']}; background:white; }}
    """


# ══════════════════════════════════════════════════════════════════
# Tables
# ══════════════════════════════════════════════════════════════════

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48


def table_style(variant: str = "normal") -> str:
    """Stylesheet موحد للجداول."""
    base = get_base()
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


# ══════════════════════════════════════════════════════════════════
# Cards & Frames
# ══════════════════════════════════════════════════════════════════

def card_style(bg: str = None, border: str = None, radius: int = 10) -> str:
    return f"""
        QFrame {{
            background:{bg or _C['bg_surface']};
            border:1px solid {border or _C['border']};
            border-radius:{radius}px;
        }}
    """


def status_card_style(status: str = "info", radius: int = 8) -> str:
    from ..core.colors import status_colors
    s = status_colors(status)
    return f"""
        QFrame {{
            background:{s['bg']}; border:1px solid {s['border']};
            border-radius:{radius}px;
        }}
    """


def group_box_style(accent: str = None) -> str:
    base  = get_base()
    color = accent or _C["accent"]
    return f"""
        QGroupBox {{
            font-weight:700; font-size:{fs(base,0)}pt;
            color:{_C['text_sec']}; background:{_C['bg_surface']};
            border:1px solid {_C['border']}; border-radius:10px;
            margin-top:10px; padding-top:6px;
        }}
        QGroupBox::title {{
            subcontrol-origin:margin; subcontrol-position:top right;
            padding:0 8px; color:{color};
        }}
    """


# ══════════════════════════════════════════════════════════════════
# Tabs
# ══════════════════════════════════════════════════════════════════

def tab_style(accent: str = None, size: str = "normal") -> str:
    """
    Stylesheet للتبويبات.
    size: "normal" | "inner" | "small" (small = alias لـ inner)
    """
    base     = get_base()
    c        = accent or _C["accent"]
    is_small = size in ("inner", "small")
    padding  = "6px 12px" if is_small else "8px 16px"
    font_sz  = fs(base, -1) if is_small else fs(base, 0)
    min_w    = "60px" if is_small else "80px"

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


# ══════════════════════════════════════════════════════════════════
# Scroll / Misc
# ══════════════════════════════════════════════════════════════════

def scroll_style(width: int = 6) -> str:
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


def tree_style() -> str:
    return f"""
        QTreeWidget {{
            border:1px solid {_C['border']}; border-radius:6px;
            background:white; outline:none;
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
            border:1px solid {_C['border']}; border-radius:4px;
            background:white; outline:none;
        }}
        QListWidget::item {{
            padding:3px 6px; border-bottom:1px solid {_C['border']};
        }}
        QListWidget::item:selected {{
            background:{_C['accent_light']}; color:{_C['accent_text']};
        }}
        QListWidget::item:hover:!selected {{ background:{_C['bg_hover']}; }}
    """


def filter_bar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_surface_2']}; border:1px solid {_C['border']};
            border-radius:8px;
        }}
    """


def toolbar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_input']};
            border-bottom:1px solid {_C['border']};
        }}
    """


# ══════════════════════════════════════════════════════════════════
# Labels
# ══════════════════════════════════════════════════════════════════

def status_label_style(status: str = "info", font_offset: int = 0) -> str:
    from ..core.colors import status_colors
    base = get_base()
    s = status_colors(status)
    return (
        f"font-size:{fs(base,font_offset)}pt; font-weight:bold;"
        f"color:{s['fg']}; background:{s['bg']};"
        f"border:1px solid {s['border']}; border-radius:6px; padding:6px 14px;"
    )


def muted_label_style(font_offset: int = -1) -> str:
    base = get_base()
    return (
        f"color:{_C['text_muted']}; font-size:{fs(base,font_offset)}pt;"
        "background:transparent; border:none;"
    )


def section_title_style(color: str = None, font_offset: int = 0) -> str:
    base = get_base()
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
    base = get_base()
    c = color or _C["accent"]
    return f"""
        QPushButton {{
            background:transparent; border:none;
            color:{c}; font-size:{fs(base,0)}pt;
            text-decoration:underline; padding:0;
        }}
        QPushButton:hover {{ color:{c}cc; }}
    """