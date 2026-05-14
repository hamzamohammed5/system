"""
ui/app_settings.py
==================
يحفظ ويطبّق إعداد حجم الخط على التطبيق كله.
"""

from PyQt5.QtWidgets import QApplication
from db.settings_repo import get_setting, set_setting
from db.connection    import get_connection

DEFAULT_FONT_SIZE = 11


def get_font_size() -> int:
    conn = get_connection()
    try:
        return int(float(get_setting(conn, "font_size", DEFAULT_FONT_SIZE)))
    except Exception:
        return DEFAULT_FONT_SIZE
    finally:
        conn.close()


def set_font_size(size: int):
    conn = get_connection()
    try:
        set_setting(conn, "font_size", size)
    finally:
        conn.close()


def fs(base: int, delta: int = 0) -> int:
    return max(7, base + delta)


def _build_stylesheet(base: int) -> str:
    tiny   = fs(base, -2)
    small  = fs(base, -1)
    normal = fs(base,  0)
    large  = fs(base, +1)
    xlarge = fs(base, +2)

    # التبويبات: حجم خط ثابت لا يتأثر بالـ base
    # لأن الأيقونة الإيموجي هي جزء من نص التبويب،
    # وحجم الخط هو اللي يتحكم في حجمها مباشرة
    TAB_FONT  = 13   # ثابت دايماً — يضمن ظهور الإيموجي بحجم مناسب
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
    app.setStyleSheet(_build_stylesheet(size))