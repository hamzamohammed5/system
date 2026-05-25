"""
ui/widgets/shared/panles_helper/theme.py

التغييرات:
  - STATUS_COLORS هو المصدر الوحيد لألوان الحالات
    (notification_bar.py و base_warning_bar.py بيستخدموه بدل dict منفصل)
  - get_status_label_style يستخدم STATUS_COLORS مباشرة (كان مكرر جزئياً)
  - _tab_stylesheet() (كانت محلية في tab_section_base) حُذفت وتوحّدت هنا
  - get_tab_style: size="small" alias لـ size="inner" (محتفظ بالتوافق)
  - make_divider / make_vline_sep موحدتان مع divider_utils
"""
from PyQt5.QtWidgets import QFrame
from ui.app_settings import _C, fs
from .colors_and_base import _base


# ══════════════════════════════════════════════════════════
# المصدر الوحيد لألوان الحالات — يُستورد من هنا في كل مكان
# ══════════════════════════════════════════════════════════

STATUS_COLORS = {
    "success": {"fg": "#065f46", "bg": "#ecfdf5", "border": "#6ee7b7"},
    "warning": {"fg": "#92400e", "bg": "#fffbeb", "border": "#fcd34d"},
    "danger":  {"fg": "#991b1b", "bg": "#fef2f2", "border": "#fca5a5"},
    "info":    {"fg": "#1e40af", "bg": "#eff6ff", "border": "#93c5fd"},
    "neutral": {"fg": "#374151", "bg": "#f9fafb", "border": "#d1d5db"},
    "primary": {"fg": "#1565c0", "bg": "#e8f0fe", "border": "#90caf9"},
    "purple":  {"fg": "#6a1b9a", "bg": "#f3e5f5", "border": "#ce93d8"},
    "orange":  {"fg": "#e65100", "bg": "#fff3e0", "border": "#ffcc80"},
}


# ══════════════════════════════════════════════════════════
# فواصل موحدة (re-exported من divider_utils للتوافق)
# ══════════════════════════════════════════════════════════

def make_divider(color: str = None, height: int = 1) -> QFrame:
    """فاصل أفقي (HLine)."""
    c = color or _C.get("border", "#e0e0e0")
    div = QFrame()
    div.setFrameShape(QFrame.HLine)
    div.setFixedHeight(height)
    div.setStyleSheet(f"background:{c}; border:none;")
    return div


def make_vline_sep(color: str = None, width: int = 1,
                   margin_v: int = 4) -> QFrame:
    """فاصل عمودي (VLine) للـ toolbars."""
    c = color or _C.get("border_med", "#bdbdbd")
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setFixedWidth(width)
    sep.setStyleSheet(f"background:{c}; border:none; margin:{margin_v}px 2px;")
    return sep


# ══════════════════════════════════════════════════════════
# Input styles
# ══════════════════════════════════════════════════════════

def get_input_style(height: int = 30, radius: int = 6) -> str:
    base = _base()
    return f"""
        QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
            background:{_C['bg_input']};
            border:1.5px solid {_C['border_med']};
            border-radius:{radius}px; padding:0 8px;
            min-height:{height}px;
            font-size:{fs(base,0)}pt; color:{_C['text_primary']};
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color:{_C['accent']}; background:white;
        }}
        QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled,
        QSpinBox:disabled, QDoubleSpinBox:disabled {{
            background:{_C['bg_surface_2']}; color:{_C['text_disabled']};
            border-color:{_C['border']};
        }}
        QComboBox::drop-down {{ border:none; width:24px; }}
        QDateEdit::drop-down  {{ border:none; width:24px; }}
    """


def get_search_input_style(height: int = 30) -> str:
    base = _base()
    return f"""
        QLineEdit {{
            background:{_C['bg_input']};
            border:1.5px solid {_C['border_med']};
            border-radius:6px; padding:0 10px;
            min-height:{height}px;
            font-size:{fs(base,0)}pt; color:{_C['text_primary']};
        }}
        QLineEdit:focus {{ border-color:{_C['accent']}; background:white; }}
    """


# ══════════════════════════════════════════════════════════
# Card / status card styles
# ══════════════════════════════════════════════════════════

def get_card_style(bg: str = None, border: str = None,
                   radius: int = 10) -> str:
    return f"""
        QFrame {{
            background:{bg or _C['bg_surface']};
            border:1px solid {border or _C['border']};
            border-radius:{radius}px;
        }}
    """


def get_status_card_style(status: str = "info", radius: int = 8) -> str:
    s = STATUS_COLORS.get(status, STATUS_COLORS["neutral"])
    return f"""
        QFrame {{
            background:{s['bg']};
            border:1px solid {s['border']};
            border-radius:{radius}px;
        }}
    """


# ══════════════════════════════════════════════════════════
# Table styles
# ══════════════════════════════════════════════════════════

def get_table_header_style() -> str:
    base = _base()
    return f"""
        QHeaderView::section {{
            font-size:{fs(base,-1)}pt; font-weight:600;
            color:{_C['text_muted']}; background:{_C['bg_surface_2']};
            border:none;
            border-bottom:2px solid {_C['border_med']};
            border-right:1px solid {_C['border']};
            padding:6px 10px;
        }}
        QHeaderView::section:last {{ border-right:none; }}
        QHeaderView::section:hover {{
            background:{_C['bg_hover']}; color:{_C['text_primary']};
        }}
    """


# ══════════════════════════════════════════════════════════
# GroupBox / frames
# ══════════════════════════════════════════════════════════

def get_group_box_style(accent: str = None) -> str:
    base  = _base()
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


def get_filter_bar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_surface_2']};
            border:1px solid {_C['border']};
            border-radius:8px;
        }}
    """


def get_toolbar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_input']};
            border-bottom:1px solid {_C['border']};
        }}
    """


# ══════════════════════════════════════════════════════════
# Scroll / splitter
# ══════════════════════════════════════════════════════════

def get_scroll_style(width: int = 6) -> str:
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


def get_splitter_style() -> str:
    return f"""
        QSplitter::handle {{ background:{_C['border']}; }}
        QSplitter::handle:hover {{ background:{_C['accent_mid']}; }}
        QSplitter::handle:pressed {{ background:{_C['accent']}; }}
    """


# ══════════════════════════════════════════════════════════
# Buttons
# ══════════════════════════════════════════════════════════

def get_icon_btn_style(color: str = "#aaa",
                       hover_color: str = "#e53935") -> str:
    return (
        f"QPushButton {{ background:transparent; border:none; color:{color}; }}"
        f"QPushButton:hover {{ color:{hover_color}; }}"
    )


def get_link_btn_style(color: str = None) -> str:
    c = color or _C["accent"]
    base = _base()
    return f"""
        QPushButton {{
            background:transparent; border:none;
            color:{c}; font-size:{fs(base,0)}pt;
            text-decoration:underline; padding:0;
        }}
        QPushButton:hover {{ color:{c}cc; }}
    """


# ══════════════════════════════════════════════════════════
# Tab styles
# ══════════════════════════════════════════════════════════

def get_tab_style(accent: str = None, size: str = "normal") -> str:
    """
    ستايل موحد للتبويبات.
    size: "normal" | "inner" | "small"  (small = alias لـ inner)
    """
    base    = _base()
    c       = accent or _C["accent"]
    is_small = size in ("inner", "small")
    padding  = "6px 12px" if is_small else "8px 16px"
    font_size = fs(base, -1) if is_small else fs(base, 0)
    min_width = "60px"      if is_small else "80px"

    return f"""
        QTabWidget::pane {{ border:none; background:{_C['bg_page']}; }}
        QTabBar::tab {{
            background:{_C['bg_surface_2']};
            border:1px solid {_C['border']};
            border-bottom:none;
            padding:{padding}; margin-left:2px;
            font-size:{font_size}pt; color:{_C['text_muted']};
            min-width:{min_width};
        }}
        QTabBar::tab:selected {{
            background:{_C['bg_input']}; color:{c};
            font-weight:bold; border-top:2px solid {c};
        }}
        QTabBar::tab:hover:!selected {{
            background:{_C['bg_hover']}; color:{_C['text_primary']};
        }}
    """


# ══════════════════════════════════════════════════════════
# Tree / list styles
# ══════════════════════════════════════════════════════════

def get_tree_style() -> str:
    return f"""
        QTreeWidget {{
            border:1px solid {_C['border']};
            border-radius:6px; background:white; outline:none;
        }}
        QTreeWidget::item {{ padding:3px 2px; }}
        QTreeWidget::item:selected {{
            background:{_C['accent_light']}; color:{_C['accent_text']};
        }}
        QTreeWidget::item:hover:!selected {{ background:{_C['bg_hover']}; }}
    """


def get_list_style() -> str:
    return f"""
        QListWidget {{
            border:1px solid {_C['border']};
            border-radius:4px; background:white; outline:none;
        }}
        QListWidget::item {{
            padding:3px 6px; border-bottom:1px solid {_C['border']};
        }}
        QListWidget::item:selected {{
            background:{_C['accent_light']}; color:{_C['accent_text']};
        }}
        QListWidget::item:hover:!selected {{ background:{_C['bg_hover']}; }}
    """


# ══════════════════════════════════════════════════════════
# Label styles — يستخدم STATUS_COLORS بدل hardcoded
# ══════════════════════════════════════════════════════════

def get_status_label_style(status: str = "info",
                            font_size_offset: int = 0) -> str:
    base = _base()
    s = STATUS_COLORS.get(status, STATUS_COLORS["neutral"])
    return (
        f"font-size:{fs(base,font_size_offset)}pt; font-weight:bold;"
        f"color:{s['fg']}; background:{s['bg']};"
        f"border:1px solid {s['border']}; border-radius:6px; padding:6px 14px;"
    )


def get_muted_label_style(font_size_offset: int = -1) -> str:
    base = _base()
    return (
        f"color:{_C['text_muted']}; font-size:{fs(base,font_size_offset)}pt;"
        "background:transparent; border:none;"
    )


def get_section_title_style(color: str = None,
                             font_size_offset: int = 0) -> str:
    base = _base()
    c = color or _C["text_primary"]
    return (
        f"font-weight:bold; font-size:{fs(base,font_size_offset)}pt;"
        f"color:{c}; background:transparent; border:none;"
    )