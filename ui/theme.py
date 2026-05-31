"""
ui/theme.py
===========
إدارة الألوان والثيم — المصدر الوحيد لـ _C وكل عمليات الثيم.

المسؤولية:
  - dict الألوان الحالية (_C)
  - تطبيق ثيم جديد (apply_theme)
  - قراءة لون بأمان (get_theme_color)
  - إدارة stylesheet cache
  - بناء الـ stylesheet الكامل (build_stylesheet)
"""

from __future__ import annotations
from PyQt5.QtWidgets import QApplication

# ══════════════════════════════════════════════════════════
# Stylesheet cache — key = (font_size, theme_hash)
# ══════════════════════════════════════════════════════════
_ss_cache: dict[tuple, str] = {}
_current_theme_hash: str    = ""

# ══════════════════════════════════════════════════════════
# Palette: Warm Neutral + Slate Accents (الثيم الافتراضي)
# ══════════════════════════════════════════════════════════
_C: dict = {
    # Backgrounds
    "bg_page":      "#F5F4F0",
    "bg_surface":   "#FAFAF8",
    "bg_surface_2": "#F0EEE9",
    "bg_hover":     "#ECEAE4",
    "bg_active":    "#E4E2DA",
    "bg_input":     "#FFFFFF",

    # Borders
    "border":        "#DDD9CF",
    "border_med":    "#C8C4B8",
    "border_focus":  "#8B8680",
    "border_strong": "#6B6760",

    # Text
    "text_primary":  "#1C1B18",
    "text_sec":      "#4A4843",
    "text_muted":    "#7A7870",
    "text_disabled": "#A8A69E",

    # Accent — Slate Blue
    "accent":       "#3D5A80",
    "accent_hover": "#2E4460",
    "accent_light": "#D6E4F0",
    "accent_mid":   "#98C1D9",
    "accent_text":  "#2A3F5A",

    # Sidebar
    "sidebar_bg":     "#1E1D1A",
    "sidebar_text":   "#E8E6E1",
    "sidebar_muted":  "#7A7870",
    "sidebar_hover":  "#2E2D2A",
    "sidebar_active": "#3A3835",
    "sidebar_border": "#2E2D2A",

    # States
    "danger":         "#C0392B",
    "danger_bg":      "#FDF0EF",
    "danger_border":  "#E8A39D",
    "success":        "#2E7D52",
    "success_bg":     "#EDF7F2",
    "success_border": "#8EC5A8",
    "warning":        "#7A5C00",
    "warning_bg":     "#FDF8E7",
    "warning_border": "#D4B84A",
    "info":           "#1A5276",
    "info_bg":        "#EBF5FB",
    "info_border":    "#7FB3D3",

    # Tab indicator
    "tab_active":    "#3D5A80",
    "tab_indicator": "#3D5A80",

    # Purple — للـ machine_op rows
    "purple":        "#6a1b9a",
    "purple_bg":     "#f3e5f5",
    "purple_border": "#ce93d8",

    # Orange — للـ filters والـ warnings الثانوية
    "orange":        "#e65100",
    "orange_bg":     "#fff3e0",
    "orange_border": "#ffcc80",
}


# ══════════════════════════════════════════════════════════
# Theme hash — للكشف عن تغييرات الثيم في الـ cache
# ══════════════════════════════════════════════════════════

def _compute_theme_hash() -> str:
    """يحسب hash من _C الحالي."""
    try:
        return str(hash(tuple(sorted(_C.items()))))
    except Exception:
        return "default"


def _get_theme_hash() -> str:
    """يرجع الـ hash الحالي — يحسبه lazy لو لم يُحسب بعد."""
    global _current_theme_hash
    if not _current_theme_hash:
        _current_theme_hash = _compute_theme_hash()
    return _current_theme_hash


# ══════════════════════════════════════════════════════════
# Cache management
# ══════════════════════════════════════════════════════════

def invalidate_stylesheet_cache():
    """
    يمسح الـ stylesheet cache.
    يُستدعى عند: تغيير الثيم / تغيير الشركة / تغيير حجم الخط.
    """
    global _current_theme_hash
    _ss_cache.clear()
    _current_theme_hash = ""          # يُعاد حسابه lazy في الطلب التالي
    from ui.font import _set_module_font_cache
    _set_module_font_cache(None)


# ══════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════

def apply_theme(theme_colors: dict, app: QApplication = None):
    """
    يُحدّث _C بألوان الثيم الجديد ويُعيد بناء الـ stylesheet.
    يُستدعى من ThemeManager.set_theme() — لا تستدعه مباشرة من الـ UI.
    """
    global _C
    _C.update(theme_colors)

    invalidate_stylesheet_cache()

    try:
        from ui.widgets.components.button import invalidate_stylesheet_cache as inv_btn
        inv_btn()
    except Exception:
        pass

    _app = app or QApplication.instance()
    if _app:
        from ui.font import get_font_size
        _app.setStyleSheet(build_stylesheet(get_font_size()))


def get_theme_color(key: str, fallback: str = "#000000") -> str:
    """يرجع لون من _C بأمان مع fallback."""
    return _C.get(key, fallback)


# ══════════════════════════════════════════════════════════
# Stylesheet builder — مقسّم لدوال مساعدة للقراءة
# ══════════════════════════════════════════════════════════

def build_stylesheet(base: int) -> str:
    """
    يبني الـ stylesheet الكامل لحجم خط معين.
    Cache key = (font_size, theme_hash).
    """
    from ui.constants import MIN_FONT_SIZE, MAX_FONT_SIZE
    from ui.font import fs

    base = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, base))

    theme_hash = _get_theme_hash()
    cache_key  = (base, theme_hash)

    if cache_key in _ss_cache:
        return _ss_cache[cache_key]

    c       = _C
    small   = fs(base, -1)
    normal  = fs(base,  0)
    large   = fs(base, +1)
    input_h = normal * 2 + 6
    btn_h   = normal * 2 + 8

    kw = dict(
        base=base, c=c,
        small=small, normal=normal, large=large,
        input_h=input_h, btn_h=btn_h,
        radius="6px", radius_sm="4px", radius_lg="8px",
    )

    sections = [
        _ss_base_reset(**kw),
        _ss_message_box(**kw),
        _ss_dialog(**kw),
        _ss_typography(**kw),
        _ss_groupbox(**kw),
        _ss_buttons(**kw),
        _ss_inputs(**kw),
        _ss_combobox(**kw),
        _ss_tables(**kw),
        _ss_tree(**kw),
        _ss_tabs(**kw),
        _ss_scrollbars(c=c),
        _ss_misc(**kw),
    ]

    result = "\n".join(sections)
    _ss_cache[cache_key] = result
    return result


# ── Stylesheet sections ────────────────────────────────────

def _ss_base_reset(c, normal, btn_h, radius, radius_sm, **_) -> str:
    return f"""
/* ══ Base & Reset ══ */
* {{ font-size: {normal}pt; color: {c['text_primary']}; outline: none; }}
QMainWindow {{ background: {c['bg_page']}; }}
QWidget {{ background: transparent; }}
"""


def _ss_message_box(c, normal, btn_h, radius, radius_sm, **_) -> str:
    return f"""
/* ══ QMessageBox ══ */
QMessageBox {{ background: {c['bg_surface']}; color: {c['text_primary']}; }}
QMessageBox QWidget,
QMessageBox > QWidget,
QMessageBox > QWidget > QWidget,
QMessageBox > QWidget > QWidget > QWidget {{
    background: {c['bg_surface']}; color: {c['text_primary']};
}}
QMessageBox QLabel {{
    background: transparent; color: {c['text_primary']}; font-size: {normal}pt;
}}
QMessageBox QTextEdit {{
    background: {c['bg_surface_2']}; color: {c['text_primary']};
    border: 1px solid {c['border_med']}; border-radius: {radius_sm};
}}
QMessageBox QPushButton {{
    background: {c['bg_surface_2']}; color: {c['text_primary']};
    border: 1px solid {c['border_med']}; border-radius: {radius};
    padding: 4px 18px; min-width: 70px; min-height: {btn_h}px;
    font-size: {normal}pt;
}}
QMessageBox QPushButton:hover {{
    background: {c['bg_hover']}; border-color: {c['border_strong']};
}}
QMessageBox QPushButton:pressed {{ background: {c['bg_active']}; }}
"""


def _ss_dialog(c, **_) -> str:
    return f"""
/* ══ QDialog ══ */
QDialog {{ background: {c['bg_surface']}; color: {c['text_primary']}; }}
QDialog QWidget,
QDialog > QWidget,
QDialog > QWidget > QWidget {{
    background: {c['bg_surface']}; color: {c['text_primary']};
}}
QDialog QLabel {{ background: transparent; color: {c['text_primary']}; }}
QDialog QGroupBox {{ background: {c['bg_surface']}; }}
QDialog QScrollArea {{ background: {c['bg_surface']}; border: none; }}
QDialog QScrollArea > QWidget > QWidget {{ background: {c['bg_surface']}; }}
"""


def _ss_typography(c, normal, small, large, radius_sm, **_) -> str:
    return f"""
/* ══ Typography ══ */
QLabel {{ font-size: {normal}pt; color: {c['text_primary']}; background: transparent; }}
QLabel[role="section"] {{
    font-size: {large}pt; font-weight: 700; color: {c['text_sec']};
    letter-spacing: 0.3px;
}}
QLabel[role="card-title"] {{
    font-size: {small}pt; color: {c['text_muted']};
    letter-spacing: 0.2px; text-transform: uppercase;
}}
QLabel[role="card-value"] {{
    font-size: {large}pt; font-weight: 700; color: {c['text_primary']};
}}
QLabel[role="badge"] {{
    font-size: {small}pt; font-weight: 600;
    border-radius: {radius_sm}; padding: 2px 7px;
}}
QLabel[role="mode"] {{
    font-size: {normal}pt; font-weight: 600; color: {c['accent']};
    background: {c['accent_light']}; border-radius: {radius_sm}; padding: 3px 8px;
}}
"""


def _ss_groupbox(c, normal, small, radius_lg, **_) -> str:
    return f"""
/* ══ GroupBox ══ */
QGroupBox {{
    font-size: {normal}pt; font-weight: 600; color: {c['text_sec']};
    border: 1px solid {c['border']}; border-radius: {radius_lg};
    margin-top: 10px; padding-top: 10px; background: {c['bg_surface']};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top right;
    padding: 0 10px; color: {c['text_muted']};
    font-size: {small}pt; font-weight: 600; letter-spacing: 0.3px;
}}
"""


def _ss_buttons(c, normal, btn_h, radius, **_) -> str:
    return f"""
/* ══ Buttons ══ */
QPushButton {{
    font-size: {normal}pt; font-weight: 500; color: {c['text_sec']};
    background: {c['bg_surface']}; border: 1px solid {c['border_med']};
    border-radius: {radius}; padding: 3px 14px; min-height: {btn_h}px;
}}
QPushButton:hover {{
    background: {c['bg_hover']}; border-color: {c['border_strong']};
    color: {c['text_primary']};
}}
QPushButton:pressed {{ background: {c['bg_active']}; border-color: {c['border_strong']}; }}
QPushButton:disabled {{
    color: {c['text_disabled']}; background: {c['bg_surface_2']};
    border-color: {c['border']};
}}
QPushButton:checked {{
    background: {c['accent_light']}; border-color: {c['accent_mid']};
    color: {c['accent_text']}; font-weight: 600;
}}
"""


def _ss_inputs(c, normal, input_h, radius, **_) -> str:
    return f"""
/* ══ Inputs ══ */
QLineEdit, QDoubleSpinBox, QSpinBox, QDateEdit, QTimeEdit {{
    font-size: {normal}pt; color: {c['text_primary']};
    background: {c['bg_input']}; border: 1px solid {c['border_med']};
    border-radius: {radius}; min-height: {input_h}px; padding: 2px 10px;
    selection-background-color: {c['accent_light']};
    selection-color: {c['accent_text']};
}}
QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover {{
    border-color: {c['border_strong']};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus,
QDateEdit:focus, QTimeEdit:focus {{
    border: 1.5px solid {c['accent']}; background: {c['bg_input']};
}}
QLineEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled {{
    color: {c['text_disabled']}; background: {c['bg_surface_2']};
    border-color: {c['border']};
}}
QLineEdit:read-only {{ background: {c['bg_surface_2']}; color: {c['text_sec']}; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    border: none; background: transparent; width: 18px;
    border-left: 1px solid {c['border']};
}}
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {c['bg_hover']};
}}
"""


def _ss_combobox(c, normal, input_h, radius, radius_sm, **_) -> str:
    return f"""
/* ══ ComboBox ══ */
QComboBox {{
    font-size: {normal}pt; color: {c['text_primary']};
    background: {c['bg_input']}; border: 1px solid {c['border_med']};
    border-radius: {radius}; min-height: {input_h}px; padding: 2px 10px;
}}
QComboBox:hover {{ border-color: {c['border_strong']}; }}
QComboBox:focus {{ border: 1.5px solid {c['accent']}; }}
QComboBox::drop-down {{
    border: none; border-left: 1px solid {c['border']};
    width: 24px; background: transparent;
}}
QComboBox::down-arrow {{ width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: {c['bg_input']}; border: 1px solid {c['border_med']};
    border-radius: {radius};
    selection-background-color: {c['accent_light']};
    selection-color: {c['accent_text']}; outline: none; padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    padding: 5px 10px; min-height: {input_h - 4}px; border-radius: {radius_sm};
}}
QComboBox QAbstractItemView::item:hover {{ background: {c['bg_hover']}; }}
"""


def _ss_tables(c, normal, small, radius, **_) -> str:
    return f"""
/* ══ Tables ══ */
QTableWidget {{
    font-size: {normal}pt; color: {c['text_primary']};
    background: {c['bg_input']}; border: 1px solid {c['border']};
    border-radius: {radius}; gridline-color: {c['border']};
    alternate-background-color: {c['bg_surface']};
}}
QTableWidget::item {{
    padding: 5px 10px; border: none;
    border-bottom: 1px solid {c['border']};
}}
QTableWidget::item:selected {{
    background: {c['accent_light']}; color: {c['accent_text']};
}}
QTableWidget::item:hover {{ background: {c['bg_hover']}; }}
QHeaderView {{ background: {c['bg_surface_2']}; }}
QHeaderView::section {{
    font-size: {small}pt; font-weight: 600; color: {c['text_muted']};
    background: {c['bg_surface_2']}; border: none;
    border-bottom: 2px solid {c['border_med']};
    border-right: 1px solid {c['border']}; padding: 6px 10px;
    letter-spacing: 0.2px;
}}
QHeaderView::section:first {{ border-right: none; }}
QHeaderView::section:hover {{ background: {c['bg_hover']}; color: {c['text_primary']}; }}
"""


def _ss_tree(c, normal, small, radius, radius_sm, **_) -> str:
    return f"""
/* ══ TreeWidget ══ */
QTreeWidget {{
    font-size: {normal}pt; color: {c['text_primary']};
    background: {c['bg_input']}; border: 1px solid {c['border']};
    border-radius: {radius}; alternate-background-color: {c['bg_surface']};
    show-decoration-selected: 1;
}}
QTreeWidget::item {{
    padding: 4px 6px; border: none; border-radius: {radius_sm};
}}
QTreeWidget::item:selected {{
    background: {c['accent_light']}; color: {c['accent_text']};
}}
QTreeWidget::item:hover {{ background: {c['bg_hover']}; }}
QTreeWidget::branch:selected {{ background: {c['accent_light']}; }}
QTreeWidget QHeaderView::section {{
    font-size: {small}pt; font-weight: 600; color: {c['text_muted']};
    background: {c['bg_surface_2']}; border: none;
    border-bottom: 2px solid {c['border_med']}; padding: 6px 10px;
}}
"""


def _ss_tabs(c, normal, **_) -> str:
    return f"""
/* ══ Tabs ══ */
QTabWidget::pane {{
    border: 1px solid {c['border']}; border-top: none;
    background: {c['bg_surface']};
}}
QTabBar {{ background: {c['bg_surface_2']}; }}
QTabBar::tab {{
    font-size: {normal}pt; font-weight: 500; color: {c['text_muted']};
    background: transparent; border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 18px; min-width: 80px;
}}
QTabBar::tab:selected {{
    color: {c['tab_active']}; border-bottom: 2px solid {c['tab_indicator']};
    font-weight: 700; background: {c['bg_surface']};
}}
QTabBar::tab:hover:!selected {{
    color: {c['text_primary']}; background: {c['bg_hover']};
    border-bottom: 2px solid {c['border_med']};
}}
"""


def _ss_scrollbars(c, **_) -> str:
    return f"""
/* ══ Scrollbars ══ */
QScrollBar:vertical {{
    background: transparent; width: 6px; border-radius: 3px; margin: 2px 1px;
}}
QScrollBar::handle:vertical {{
    background: {c['border_med']}; border-radius: 3px; min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['border_strong']}; }}
QScrollBar::handle:vertical:pressed {{ background: {c['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{
    background: transparent; height: 6px; border-radius: 3px; margin: 1px 2px;
}}
QScrollBar::handle:horizontal {{
    background: {c['border_med']}; border-radius: 3px; min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{ background: {c['border_strong']}; }}
QScrollBar::handle:horizontal:pressed {{ background: {c['accent']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
"""


def _ss_misc(c, normal, small, radius, radius_sm, **_) -> str:
    return f"""
/* ══ ListWidget ══ */
QListWidget {{
    font-size: {normal}pt; color: {c['text_primary']};
    background: {c['bg_input']}; border: 1px solid {c['border']};
    border-radius: {radius}; outline: none;
}}
QListWidget::item {{
    padding: 6px 12px; border: none; border-radius: {radius_sm};
}}
QListWidget::item:selected {{
    background: {c['accent_light']}; color: {c['accent_text']}; font-weight: 600;
}}
QListWidget::item:hover {{ background: {c['bg_hover']}; }}

/* ══ Splitter ══ */
QSplitter::handle {{ background: {c['border']}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
QSplitter::handle:hover {{ background: {c['accent_mid']}; }}

/* ══ ToolTip ══ */
QToolTip {{
    font-size: {small}pt; color: {c['bg_surface']};
    background: {c['text_primary']}; border: none;
    border-radius: {radius_sm}; padding: 5px 10px;
}}

/* ══ Frame & Separators ══ */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {c['border']}; border: none; background: {c['border']};
}}

/* ══ ScrollArea ══ */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* ══ ProgressBar ══ */
QProgressBar {{
    font-size: {small}pt; color: {c['text_primary']};
    background: {c['bg_surface_2']}; border: 1px solid {c['border']};
    border-radius: {radius}; text-align: center; height: {normal}px;
}}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: {radius_sm}; }}

/* ══ CheckBox & RadioButton ══ */
QCheckBox, QRadioButton {{
    font-size: {normal}pt; color: {c['text_primary']}; spacing: 8px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: {normal + 4}px; height: {normal + 4}px;
    border: 1.5px solid {c['border_med']}; background: {c['bg_input']};
}}
QCheckBox::indicator {{ border-radius: {radius_sm}; }}
QRadioButton::indicator {{ border-radius: {(normal + 4) // 2}px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {c['accent']};
}}
QCheckBox::indicator:checked {{
    background: {c['accent']}; border-color: {c['accent']};
}}
QRadioButton::indicator:checked {{
    background: {c['accent']}; border-color: {c['accent']};
}}

/* ══ Sidebar nav overrides ══ */
QLabel#nav_icon {{ font-size: 16pt; background: transparent; border: none; }}
QLabel#nav_label {{ font-size: {normal}pt; background: transparent; border: none; }}
"""