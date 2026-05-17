"""
ui/app_settings.py
==================
يحفظ ويطبّق إعداد حجم الخط على التطبيق كله.
"""

from PyQt5.QtWidgets import QApplication
from db.settings_repo import get_setting, set_setting
from db.shared.connection import get_connection

DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE     = 8
MAX_FONT_SIZE     = 20


def get_font_size() -> int:
    conn = get_connection()
    try:
        raw = get_setting(conn, "font_size", None)

        # لو مفيش قيمة محفوظة → استخدم الافتراضي واحفظه
        if raw is None:
            set_setting(conn, "font_size", DEFAULT_FONT_SIZE)
            return DEFAULT_FONT_SIZE

        val = int(float(raw))

        # لو القيمة خارج النطاق → أصلحها واحفظها
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
    # تأكد إن base في نطاق سليم قبل بناء الـ stylesheet
    base   = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, base))

    tiny   = fs(base, -2)
    small  = fs(base, -1)
    normal = fs(base,  0)
    large  = fs(base, +1)
    xlarge = fs(base, +2)

    TAB_FONT  = 13
    TAB_PAD_V = 8
    TAB_PAD_H = 14
    TAB_MIN_W = 80

    return f"""
* {{
    font-size: {normal}pt;
}}

QLabel {{
    font-size: {normal}pt;
}}

QGroupBox {{
    font-size: {large}pt;
    font-weight: bold;
}}

QPushButton {{
    font-size: {normal}pt;
    padding: 3px 10px;
    min-height: {normal * 2 + 4}px;
}}

QLineEdit,
QDoubleSpinBox,
QSpinBox,
QDateEdit,
QComboBox {{
    font-size: {normal}pt;
    min-height: {normal * 2 + 4}px;
    padding: 2px 6px;
}}

QTableWidget {{
    font-size: {normal}pt;
}}

QHeaderView::section {{
    font-size: {small}pt;
    font-weight: bold;
    padding: 3px 6px;
}}

QTreeWidget {{
    font-size: {normal}pt;
}}

QTreeWidget QHeaderView::section {{
    font-size: {small}pt;
    font-weight: bold;
}}

QTabBar::tab {{
    font-size: {TAB_FONT}pt;
    padding: {TAB_PAD_V}px {TAB_PAD_H}px;
    min-width: {TAB_MIN_W}px;
}}

QTabWidget::pane {{
    border: none;
}}

QLabel#nav_icon {{
    font-size: 22pt;
    background: transparent;
    border: none;
}}

QLabel#nav_label {{
    font-size: 10pt;
    background: transparent;
    border: none;
}}

QToolTip {{
    font-size: {small}pt;
}}

QLabel[role="card-title"] {{
    font-size: {small}pt;
    color: #888;
}}

QLabel[role="card-value"] {{
    font-size: {large}pt;
    font-weight: bold;
}}

QLabel[role="badge"] {{
    font-size: {small}pt;
    font-weight: bold;
    border-radius: 3px;
    padding: 2px 4px;
}}

QLabel[role="section"] {{
    font-size: {large}pt;
    font-weight: bold;
    color: #333;
}}

QLabel[role="mode"] {{
    font-size: {normal}pt;
    font-weight: bold;
    color: #1565c0;
}}
"""


def apply_font(app: QApplication, size: int = None):
    if size is None:
        size = get_font_size()
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
    app.setStyleSheet(_build_stylesheet(size))