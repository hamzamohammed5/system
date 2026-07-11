"""
services/shared/unit_service.py
==================================
Business logic لوحدات القياس — مفصول عن الـ widget.

[إصلاح هيكلة] نُقل من ui/widgets/combo/unit_service.py إلى هنا:
  widgets/ (base classes) ممنوعة تستدعي repos/ (db/) مباشرة حسب
  الهيكلة المعمارية للمشروع. هذا الملف كان يستدعي
  db.shared.settings_repo مباشرة من داخل widgets/ — كسر هيكلي.
  النقل لـ services/shared/ يحل المشكلة لأن services/ هي الطبقة
  الوحيدة المسموح لها تستدعي repos/ (بنفس نمط font_service.py).

مستخرج أصلاً من combo/unit.py:
  - _cache_key
  - invalidate_units_cache
  - load_units / save_units
  - get_last_unit / set_last_unit
  - add_unit / remove_unit / get_all_units / reset_units_to_default
"""

import json
import logging


logger = logging.getLogger(__name__)

_UNITS_KEY = "custom_units"

# قيم الوحدات الافتراضية كمعرّفات داخلية فقط (بدون نص معروض) —
# تُستخدم في remove_unit للتحقق من كون الوحدة "افتراضية" أم لا
_DEFAULT_UNIT_KEYS = ("px", "mm", "cm", "m", "inch")


def _default_units() -> list:
    """
    [i18n] الوحدات الافتراضية بقت دالة تُستدعى وقت الحاجة، بدل ثابت
    module-level كان يُحسب وقت import (قبل تحميل اللغة) ولا يتحدث
    بعد ذلك أبداً عند تغيير اللغة.
    """
    return [
        ("px",   "px"),
        ("mm",   "mm"),
        ("cm",   "cm"),
        ("m",    "m"),
        ("inch", "inch"),
    ]

# cache: db_path → list[tuple[str, str]]
_units_cache: dict = {}


def _cache_key(conn) -> str:
    """
    يرجع database path كـ cache key.
    fallback آمن (id(conn)) لو فشل.
    """
    try:
        row = conn.execute("PRAGMA database_list").fetchone()
        if row and row[2]:
            return row[2]
    except Exception:
        pass
    logger.debug("_cache_key: couldn't get db path, using id fallback")
    return f"_id_{id(conn)}"


def invalidate_units_cache(conn=None):
    """يمسح الـ cache — استدعه بعد تغيير الوحدات أو تغيير الشركة."""
    if conn is None:
        _units_cache.clear()
    else:
        key = _cache_key(conn)
        _units_cache.pop(key, None)


def load_units(conn, force: bool = False) -> list:
    """يجلب قائمة الوحدات من settings مع cache."""
    key = _cache_key(conn)

    if not force and key in _units_cache:
        return _units_cache[key]

    result = _default_units()
    try:
        from db.shared.settings_repo import get_setting
        raw = get_setting(conn, _UNITS_KEY, "")
        if raw:
            result = [(d[0], d[1]) for d in json.loads(raw)]
    except Exception as e:
        logger.debug("load_units failed, using defaults: %s", e)

    _units_cache[key] = result
    return result


def save_units(conn, units: list):
    try:
        from db.shared.settings_repo import set_setting
        set_setting(conn, _UNITS_KEY, json.dumps(units, ensure_ascii=False))
        invalidate_units_cache(conn)
    except Exception as e:
        logger.warning("save_units failed: %s", e)


def get_last_unit(conn, key: str, fallback: str = "cm") -> str:
    try:
        from db.shared.settings_repo import get_setting
        val = get_setting(conn, f"last_unit_{key}", "")
        return val if val else fallback
    except Exception:
        return fallback


def set_last_unit(conn, key: str, unit: str):
    try:
        from db.shared.settings_repo import set_setting
        set_setting(conn, f"last_unit_{key}", unit)
    except Exception as e:
        logger.debug("set_last_unit failed: %s", e)


def add_unit(conn, value: str, label: str) -> bool:
    value, label = value.strip().lower(), label.strip()
    if not value or not label:
        return False
    units = load_units(conn)
    if any(u[0] == value for u in units):
        return False
    units.append((value, label))
    save_units(conn, units)
    return True


def remove_unit(conn, value: str) -> bool:
    if value in _DEFAULT_UNIT_KEYS:
        return False
    units = load_units(conn)
    new_units = [u for u in units if u[0] != value]
    if len(new_units) == len(units):
        return False
    save_units(conn, new_units)
    return True


def get_all_units(conn) -> list:
    return load_units(conn)


def reset_units_to_default(conn):
    save_units(conn, _default_units())