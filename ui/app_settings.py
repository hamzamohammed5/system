"""
ui/app_settings.py
==================
يحفظ ويطبّق إعداد حجم الخط على التطبيق كله.
الـ stylesheet يتبع نظام رمادي محايد متسق مع الـ sidebar الجديد.
"""

from PyQt5.QtWidgets import QApplication
from db.shared.settings_repo import get_setting, set_setting
from db.shared.connection import get_connection

DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20

# ── ألوان النظام الرمادي المحايد ──────────────────────────
# كل اللون من palette واحدة متسقة
_C = {
    "bg_page":      "#F7F6F3",   # خلفية الصفحة
    "bg_surface":   "#FAFAF8",   # سطح البطاقات والـ panels
    "bg_hover":     "#F1EFE8",   # hover الخفيف
    "bg_active":    "#F1EFE8",   # الحالة المحددة
    "border":       "#E8E6DF",   # حدود عامة
    "border_focus": "#B4B2A9",   # حدود الـ focus
    "text_primary": "#2C2C2A",   # نص رئيسي
    "text_sec":     "#5F5E5A",   # نص ثانوي
    "text_muted":   "#888780",   # نص خافت
    "accent":       "#444441",   # accent محايد
    "accent_light": "#D3D1C7",   # accent فاتح
    "danger":       "#D85A30",   # خطأ / حذف
    "danger_bg":    "#FAECE7",   # خلفية الخطأ
    "success":      "#3B6D11",   # نجاح
    "success_bg":   "#EAF3DE",   # خلفية النجاح
    "info":         "#185FA5",   # معلومات
    "info_bg":      "#E6F1FB",   # خلفية المعلومات
    "warning":      "#854F0B",   # تحذير
    "warning_bg":   "#FAEEDA",   # خلفية التحذير
    "tab_active":   "#2C2C2A",   # لون التبويب المحدد
}


def get_font_size() -> int:
    conn = get_connection()
    try:
        raw = get_setting(conn, "font_size", None)
        if raw is None:
            set_setting(conn, "font_size", DEFAULT_FONT_SIZE)
            return DEFAULT_FONT_SIZE
        val = int(float(raw))
        if val < MIN_FONT_SIZE or val > MAX_FONT_SIZE:
            set_setting(conn, "font_size", DEFAULT_FONT_SIZE)
            return DEFAULT_FONT_SIZE
        return val
    except Exception:
        return DEFAULT_FONT_SIZE
    finally:
        conn.close()


def set_font_size(size: int):
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
    conn = get_connection()
    try:
        set_setting(conn, "font_size", size)
    finally:
        conn.close()


def fs(base: int, delta: int = 0) -> int:
    """حجم خط نسبي — الحد الأدنى 7 دائماً."""
    return max(7, base + delta)


def _build_stylesheet(base: int) -> str:
    base   = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, base))

    tiny   = fs(base, -2)
    small  = fs(base, -1)
    normal = fs(base,  0)
    large  = fs(base, +1)

    c = _C  # اختصار

    return f"""
/* ── Base ──────────────────────────────────────────── */
* {{
    font-size: {normal}pt;
    color: {c['text_primary']};
}}

QMainWindow, QDialog {{
    background: {c['bg_page']};
}}

QWidget {{
    background: transparent;
}}

/* ── Labels ─────────────────────────────────────────── */
QLabel {{
    font-size: {normal}pt;
    color: {c['text_primary']};
    background: transparent;
}}

/* ── GroupBox ───────────────────────────────────────── */
QGroupBox {{
    font-size: {large}pt;
    font-weight: bold;
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 8px;
    background: {c['bg_surface']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 8px;
    color: {c['text_sec']};
}}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {{
    font-size: {normal}pt;
    color: {c['text_primary']};
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    padding: 3px 12px;
    min-height: {normal * 2 + 4}px;
}}
QPushButton:hover {{
    background: {c['bg_hover']};
    border-color: {c['accent_light']};
}}
QPushButton:pressed {{
    background: {c['accent_light']};
}}
QPushButton:disabled {{
    color: {c['text_muted']};
    background: {c['bg_page']};
    border-color: {c['border']};
}}

/* ── Inputs ──────────────────────────────────────────── */
QLineEdit,
QDoubleSpinBox,
QSpinBox,
QDateEdit,
QTimeEdit {{
    font-size: {normal}pt;
    color: {c['text_primary']};
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    min-height: {normal * 2 + 4}px;
    padding: 2px 8px;
    selection-background-color: {c['accent_light']};
}}
QLineEdit:focus,
QDoubleSpinBox:focus,
QSpinBox:focus,
QDateEdit:focus,
QTimeEdit:focus {{
    border-color: {c['border_focus']};
    background: white;
}}
QLineEdit:disabled,
QDoubleSpinBox:disabled,
QSpinBox:disabled {{
    color: {c['text_muted']};
    background: {c['bg_page']};
}}

QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button,
QSpinBox::up-button,
QSpinBox::down-button {{
    border: none;
    background: transparent;
    width: 16px;
}}

/* ── ComboBox ────────────────────────────────────────── */
QComboBox {{
    font-size: {normal}pt;
    color: {c['text_primary']};
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    min-height: {normal * 2 + 4}px;
    padding: 2px 8px;
}}
QComboBox:focus {{
    border-color: {c['border_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    selection-background-color: {c['bg_hover']};
    selection-color: {c['text_primary']};
    outline: none;
}}

/* ── Tables ──────────────────────────────────────────── */
QTableWidget {{
    font-size: {normal}pt;
    color: {c['text_primary']};
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    gridline-color: {c['border']};
    alternate-background-color: {c['bg_page']};
}}
QTableWidget::item {{
    padding: 4px 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {c['bg_active']};
    color: {c['text_primary']};
}}
QHeaderView::section {{
    font-size: {small}pt;
    font-weight: bold;
    color: {c['text_sec']};
    background: {c['bg_page']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 4px 8px;
}}
QHeaderView::section:first {{
    border-right: none;
}}

/* ── TreeWidget ──────────────────────────────────────── */
QTreeWidget {{
    font-size: {normal}pt;
    color: {c['text_primary']};
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    alternate-background-color: {c['bg_page']};
}}
QTreeWidget::item {{
    padding: 3px 4px;
    border: none;
}}
QTreeWidget::item:selected {{
    background: {c['bg_active']};
    color: {c['text_primary']};
}}
QTreeWidget QHeaderView::section {{
    font-size: {small}pt;
    font-weight: bold;
    color: {c['text_sec']};
    background: {c['bg_page']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 4px 8px;
}}

/* ── Tabs ────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    border-radius: 5px;
    background: {c['bg_surface']};
}}
QTabBar::tab {{
    font-size: {normal}pt;
    color: {c['text_sec']};
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 16px;
    min-width: 70px;
}}
QTabBar::tab:selected {{
    color: {c['tab_active']};
    border-bottom: 2px solid {c['tab_active']};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    color: {c['text_primary']};
    background: {c['bg_hover']};
}}

/* ── Scrollbars ──────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c['accent_light']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['text_muted']};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {c['accent_light']};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c['text_muted']};
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── ListWidget ──────────────────────────────────────── */
QListWidget {{
    font-size: {normal}pt;
    color: {c['text_primary']};
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    outline: none;
}}
QListWidget::item {{
    padding: 5px 10px;
    border: none;
}}
QListWidget::item:selected {{
    background: {c['bg_active']};
    color: {c['text_primary']};
}}
QListWidget::item:hover {{
    background: {c['bg_hover']};
}}

/* ── Splitter ────────────────────────────────────────── */
QSplitter::handle {{
    background: {c['border']};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── ToolTip ─────────────────────────────────────────── */
QToolTip {{
    font-size: {small}pt;
    color: {c['text_primary']};
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}

/* ── MessageBox ──────────────────────────────────────── */
QMessageBox {{
    background: {c['bg_surface']};
}}

/* ── Dialog ──────────────────────────────────────────── */
QDialog {{
    background: {c['bg_surface']};
}}

/* ── Roles ───────────────────────────────────────────── */
QLabel[role="section"] {{
    font-size: {large}pt;
    font-weight: bold;
    color: {c['text_sec']};
}}
QLabel[role="card-title"] {{
    font-size: {small}pt;
    color: {c['text_muted']};
}}
QLabel[role="card-value"] {{
    font-size: {large}pt;
    font-weight: bold;
    color: {c['text_primary']};
}}
QLabel[role="badge"] {{
    font-size: {small}pt;
    font-weight: bold;
    border-radius: 3px;
    padding: 2px 6px;
}}
QLabel[role="mode"] {{
    font-size: {normal}pt;
    font-weight: bold;
    color: {c['info']};
}}

/* ── Sidebar nav (override) ──────────────────────────── */
QLabel#nav_icon {{
    font-size: 16pt;
    background: transparent;
    border: none;
}}
QLabel#nav_label {{
    font-size: {normal}pt;
    background: transparent;
    border: none;
}}
"""


def apply_font(app: QApplication, size: int = None):
    if size is None:
        size = get_font_size()
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
    app.setStyleSheet(_build_stylesheet(size))