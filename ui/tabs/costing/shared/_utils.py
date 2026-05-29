"""
ui/tabs/costing/shared/_utils.py
=================================
أدوات مشتركة لكل ملفات costing tabs.

- to_dict()         : تحويل sqlite row → dict بأمان
- SHARED_COLOR      : ألوان العناصر المشتركة
- PUBLISHED_COLOR   : ألوان العناصر المنشورة
"""

# ── ألوان العناصر المشتركة / المنشورة ───────────────────────
SHARED_COLOR    = "#2e7d52"
SHARED_BG       = "#e8f5e9"
PUBLISHED_COLOR = "#1565c0"
PUBLISHED_BG    = "#e3f2fd"


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