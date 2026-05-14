"""
ui/app_settings.py
==================
يحفظ ويطبّق إعداد حجم الخط على التطبيق كله.

نظام الأحجام النسبية (كلها تتحرك مع حجم الخط الأساسي):
  tiny   = base - 2pt  → تفاصيل صغيرة جداً
  small  = base - 1pt  → تعليقات، hints
  normal = base        → النص الأساسي
  large  = base + 1pt  → عناوين أقسام
  xlarge = base + 2pt  → عناوين رئيسية
"""

from PyQt5.QtWidgets import QApplication
from db.settings_repo import get_setting, set_setting
from db.connection    import get_connection

DEFAULT_FONT_SIZE = 11


# ══════════════════════════════════════════════════════════
# قراءة وحفظ الإعداد
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# حسابات الأحجام النسبية
# ══════════════════════════════════════════════════════════

def fs(base: int, delta: int = 0) -> int:
    """
    يحسب حجم خط نسبي من الـ base.
    fs(base, -1) → small
    fs(base,  0) → normal
    fs(base, +1) → large
    """
    return max(7, base + delta)


# ══════════════════════════════════════════════════════════
# توليد الـ stylesheet الكامل
# ══════════════════════════════════════════════════════════

def _build_stylesheet(base: int) -> str:
    tiny   = fs(base, -2)
    small  = fs(base, -1)
    normal = fs(base,  0)
    large  = fs(base, +1)
    xlarge = fs(base, +2)

    return f"""
/* ── أساس كل العناصر ── */
* {{
    font-size: {normal}pt;
}}

/* ── تجاوز الـ hard-coded sizes في الـ widgets ── */

/* الـ labels الصغيرة (hints, مؤشرات DR/CR, عداد النتائج) */
QLabel[class="small"],
QLabel[tiny="true"] {{
    font-size: {tiny}pt;
}}

/* الـ labels العادية */
QLabel {{
    font-size: {normal}pt;
}}

/* عناوين الأقسام */
QLabel[class="section"],
QGroupBox {{
    font-size: {large}pt;
    font-weight: bold;
}}

/* عناوين رئيسية */
QLabel[class="title"] {{
    font-size: {xlarge}pt;
    font-weight: bold;
}}

/* الأزرار */
QPushButton {{
    font-size: {normal}pt;
    padding: 3px 10px;
    min-height: {normal * 2 + 4}px;
}}

/* حقول الإدخال */
QLineEdit,
QDoubleSpinBox,
QSpinBox,
QDateEdit,
QComboBox {{
    font-size: {normal}pt;
    min-height: {normal * 2 + 4}px;
    padding: 2px 6px;
}}

/* الجداول */
QTableWidget {{
    font-size: {normal}pt;
}}
QHeaderView::section {{
    font-size: {small}pt;
    font-weight: bold;
    padding: 3px 6px;
}}

/* الشجرة */
QTreeWidget {{
    font-size: {normal}pt;
}}
QTreeWidget QHeaderView::section {{
    font-size: {small}pt;
    font-weight: bold;
}}

/* التبويبات */
QTabBar::tab {{
    font-size: {normal}pt;
    padding: 5px {normal}px;
    min-width: {normal * 5}px;
}}

/* الـ tooltips */
QToolTip {{
    font-size: {small}pt;
}}

/* الـ stat cards — عنوان البطاقة صغير، القيمة كبيرة */
QLabel[role="card-title"] {{
    font-size: {small}pt;
    color: #888;
}}
QLabel[role="card-value"] {{
    font-size: {large}pt;
    font-weight: bold;
}}

/* الـ badge labels (DR↑ / CR↑) */
QLabel[role="badge"] {{
    font-size: {small}pt;
    font-weight: bold;
    border-radius: 3px;
    padding: 2px 4px;
}}

/* section headers */
QLabel[role="section"] {{
    font-size: {large}pt;
    font-weight: bold;
    color: #333;
}}

/* mode labels (تعديل / جديد) */
QLabel[role="mode"] {{
    font-size: {normal}pt;
    font-weight: bold;
    color: #1565c0;
}}
"""


# ══════════════════════════════════════════════════════════
# التطبيق
# ══════════════════════════════════════════════════════════

def apply_font(app: QApplication, size: int = None):
    """طبّق حجم الخط على التطبيق كله فوراً."""
    if size is None:
        size = get_font_size()
    app.setStyleSheet(_build_stylesheet(size))