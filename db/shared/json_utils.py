"""
db/shared/json_utils.py
========================
دوال JSON مشتركة — بديل عن _decode/_encode المكررة في:
  - db/companies/shared_items_repo.py
  - db/shared/shared_items_bridge.py
  - db/shared/items_repo.py

إصلاح 33: مركزة الكود المكرر في مكان واحد.
أي bug يُصلَح هنا يُطبَّق على كل الملفات تلقائياً.

تحسين 13: decode_json_list وencode_json_list مُستخدمتان الآن في:
  - db/shared/categories_repo.py → template_fields
  بدل json.dumps/json.loads المباشرة.

الاستخدام:
    from db.shared.json_utils import decode_json, encode_json
    from db.shared.json_utils import decode_json_list, encode_json_list
"""

import json


def decode_json(data_str: str) -> dict:
    """
    يحول نص JSON إلى dict بشكل آمن.
    يرجع dict فارغ عند أي خطأ (None، نص فارغ، JSON غير صالح).
    """
    if not data_str:
        return {}
    try:
        result = json.loads(data_str)
        # تأكد أن النتيجة dict وليست list أو قيمة أخرى
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}


def encode_json(data: dict) -> str:
    """
    يحول dict إلى نص JSON مع دعم العربية.
    يرجع '{}' عند أي خطأ.
    """
    if not isinstance(data, dict):
        return "{}"
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return "{}"


def decode_json_list(data_str: str) -> list:
    """
    يحول نص JSON إلى list بشكل آمن.
    يرجع list فارغة عند أي خطأ (None، نص فارغ، JSON غير صالح).

    [تحسين 13] مُستخدمة في categories_repo.py لـ template_fields
    بدل json.loads المباشر الذي لا يعالج الأخطاء.

    مثال:
        fields = decode_json_list(row["template_fields"])
        # → [] لو NULL أو نص فارغ أو JSON فاسد
        # → [{"name": "width", "type": "number"}, ...] لو صحيح
    """
    if not data_str:
        return []
    try:
        result = json.loads(data_str)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def encode_json_list(data: list) -> str:
    """
    يحول list إلى نص JSON مع دعم العربية.
    يرجع '[]' عند أي خطأ.

    [تحسين 13] مُستخدمة في categories_repo.py لـ template_fields
    بدل json.dumps المباشر.

    مثال:
        fields_json = encode_json_list([{"name": "width"}, {"name": "height"}])
        # → '[{"name": "width"}, {"name": "height"}]'
    """
    if not isinstance(data, list):
        return "[]"
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return "[]"