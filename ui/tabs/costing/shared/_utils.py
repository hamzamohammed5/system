"""
ui/tabs/costing/shared/_utils.py
=================================
أدوات مشتركة لكل ملفات costing tabs.

- to_dict()         : تحويل sqlite row → dict بأمان
- SHARED_COLOR      : لون العناصر المشتركة (نص) — يُقرأ حياً من ui.theme_manager
- SHARED_BG         : خلفية العناصر المشتركة — يُقرأ حياً من ui.theme_manager
- PUBLISHED_COLOR   : لون العناصر المنشورة (نص) — يُقرأ حياً من ui.theme_manager
- PUBLISHED_BG      : خلفية العناصر المنشورة — يُقرأ حياً من ui.theme_manager

[Fix] إزالة الألوان الـ hardcoded بالكامل.
      المصدر الوحيد لكل الألوان هو ui/theme_manager.py (_LIGHT_THEME / _DARK_THEME):
        shared_item_fg / shared_item_bg / published_item_fg / published_item_bg
      هذا الملف لا يعرّف أي قيمة لون بنفسه — فقط يقرأ من _C عبر دوال،
      حتى يتغيّر اللون تلقائياً مع تبديل الثيم (light/dark) دون أي تعديل هنا.

      ملاحظة: SHARED_COLOR وما شابهها أصبحت دوال (callables) لا قيم ثابتة،
      لأن الاستيراد المباشر للقيمة وقت تحميل الموديول كان سيجمّد اللون على الثيم
      الافتراضي فقط. استخدم SHARED_COLOR() بدل SHARED_COLOR في أي كود جديد.
"""

from ui.theme import _C


def to_dict(row) -> dict:
    """
    يحوّل sqlite3.Row أو أي iterable مشابه لـ dict.
    لو كان dict بالفعل يرجعه كما هو.
    """
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {}


# ── ألوان العناصر المشتركة / المنشورة ───────────────────────
# المصدر الوحيد: ui/theme_manager.py — لا قيم لون هنا إطلاقاً.

def SHARED_COLOR() -> str:
    """لون نص العنصر المشترك (يتبع الثيم الحالي)."""
    return _C['shared_item_fg']


def SHARED_BG() -> str:
    """خلفية صف العنصر المشترك (يتبع الثيم الحالي)."""
    return _C['shared_item_bg']


def PUBLISHED_COLOR() -> str:
    """لون نص العنصر المنشور محلياً (يتبع الثيم الحالي)."""
    return _C['published_item_fg']


def PUBLISHED_BG() -> str:
    """خلفية صف العنصر المنشور (يتبع الثيم الحالي)."""
    return _C['published_item_bg']