"""
ui/theme.py
===========
الألوان النشطة والـ Stylesheet — مسؤولية واحدة فقط.

المسؤولية:
  - _C dict: يحتفظ بالألوان النشطة حالياً
  - apply_theme(colors): يُحدّث _C ويُعيد بناء الـ stylesheet
  - build_stylesheet(base): يبني الـ stylesheet الكامل للتطبيق
  - get_theme_color(key, fallback): قراءة آمنة من _C
  - invalidate_stylesheet_cache(): مسح الـ cache

المصدر الوحيد لتعريف الألوان: ui/theme_manager.py
لا ألوان hardcoded هنا — أي إضافة أو تغيير يكون في theme_manager.py فقط.
"""

from __future__ import annotations
from PyQt5.QtWidgets import QApplication

# ══════════════════════════════════════════════════════════
# Stylesheet cache — key = (font_size, theme_hash)
# ══════════════════════════════════════════════════════════
_ss_cache: dict[tuple, str] = {}
_current_theme_hash: str    = ""

# ══════════════════════════════════════════════════════════
# _C — dict الألوان النشطة
# يُملأ من _LIGHT_THEME في theme_manager عند الـ import الأول.
# المصدر الوحيد للألوان: ui/theme_manager.py
# ══════════════════════════════════════════════════════════
_C: dict = {}


def _init_default_theme():
    """
    يُملّي _C بالثيم الافتراضي (Light) عند أول import.
    المصدر الوحيد للألوان: ui/theme_manager.py — لا ألوان hardcoded هنا.
    """
    from ui.theme_manager import _LIGHT_THEME
    _C.update(_LIGHT_THEME)


_init_default_theme()


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
    _current_theme_hash = ""
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

        # [إصلاح ثيم — مركزي] QApplication.setStyleSheet() فوق بيحدّث الـ
        # stylesheet العام، لكن أي QTableWidget بُني بستايل محلي مباشر
        # عليه (self.table.setStyleSheet(table_style())) — زي كل الجداول
        # المبنية عبر make_table/make_splitter_table/... في tables.py —
        # الستايل المحلي ده بياخد أولوية على الستايل العام في Qt ومش
        # بيتحدّث تلقائياً مع QApplication.setStyleSheet().
        #
        # فبالتالي لو widget معيّن (زي أي panel فيه أكتر من جدول واحد،
        # مثال: CustomerDetailPanel وفيها self.table + self.contacts_table
        # + self.orders_table) مالوش _refresh_style() بيعيد ضبط *كل*
        # الجداول بتاعته بنفسه، الجداول الإضافية دي بتفضل بستايل الثيم
        # القديم — وده سبب "الصف الفاتح" اللي بيفضل ظاهر بعد التحويل لـ dark.
        #
        # الحل: بدل ما نعتمد إن كل widget يتذكر يعمل كده بنفسه، بعد كل
        # apply_theme() ندور مركزياً على كل النوافذ المفتوحة فعلياً
        # ونعيد تطبيق table_style() على كل جدول فيها دفعة واحدة.
        try:
            from ui.widgets.tables.tables import refresh_table_styles
            for _win in _app.topLevelWidgets():
                try:
                    refresh_table_styles(_win)
                except RuntimeError:
                    pass
        except Exception:
            pass


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
    from ui.constants import MIN_FONT_SIZE, MAX_FONT_SIZE, INPUT_HEIGHT_PAD, BTN_HEIGHT_PAD
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
    input_h = normal * 2 + INPUT_HEIGHT_PAD
    btn_h   = normal * 2 + BTN_HEIGHT_PAD

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
    font-size: {small}pt; color: {c['text_primary']};
    background-color: {c['bg_surface']};
    border: 1px solid {c['border_med']};
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