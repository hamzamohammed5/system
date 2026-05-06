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


def apply_font(app: QApplication, size: int = None):
    """طبّق حجم الخط على التطبيق كله فوراً."""
    if size is None:
        size = get_font_size()
    app.setStyleSheet(f"* {{ font-size: {size}pt; }}")