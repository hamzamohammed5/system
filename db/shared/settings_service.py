"""
services/shared/settings_service.py
=====================================
SettingsService — يغلّف كل عمليات db/shared/settings_repo لأي مفتاح إعداد عام.

بخلاف FontService (مخصص حصراً لمفتاح font_size)، هذا الـ service عام
ويُستخدم من أي tab يحتاج قراءة/كتابة مفاتيح متعددة من جدول settings
(مثل labor_settings.py: monthly_salary, working_days, holiday_days, ...).

الاستخدام:
    from services.shared.settings_service import SettingsService
    svc = SettingsService(conn)
    val = svc.get("monthly_salary", 3000)
    svc.set("monthly_salary", 3500)
"""

from __future__ import annotations


class SettingsService:
    """
    Business Logic لقراءة/كتابة جدول settings.

    الاستخدام:
        svc = SettingsService(conn)
        val = svc.get("working_days", 25)
        svc.set("working_days", 26)
    """

    def __init__(self, conn):
        self._conn = conn

    def get(self, key: str, default=None):
        """يقرأ قيمة من جدول settings، أو يرجع default لو المفتاح مش موجود."""
        from db.shared.settings_repo import get_setting
        return get_setting(self._conn, key, default)

    def set(self, key: str, value) -> None:
        """يكتب قيمة في جدول settings."""
        from db.shared.settings_repo import set_setting
        set_setting(self._conn, key, value)
