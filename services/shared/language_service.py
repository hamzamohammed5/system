"""
services/shared/language_service.py
=====================================
LanguageService — الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات
لقراءة وكتابة لغة الواجهة (ui_language).

لماذا service وليس تواصل مباشر؟
  ui/widgets/core/i18n.py كان يستدعي db.shared.settings_repo مباشرة
  من داخل widgets/ — كسر هيكلي (تجاوز لطبقة services/).
  هذا الملف يحل المشكلة بنفس نمط item_service.get_gimp_path():
  إعداد مشترك غير مرتبط بشركة معينة، يفتح اتصاله الخاص عبر
  db.shared.connection.get_connection() ويغلقه فور الانتهاء.

الاستخدام (من I18nManager فقط):
    from services.shared.language_service import LanguageService
    lang = LanguageService.load()          # يقرأ من DB
    LanguageService.save("en")             # يكتب للـ DB

لا يُستخدم هذا الملف مباشرةً من أي ملف في ui/ عدا i18n.py.
"""

from __future__ import annotations
import logging

from db.shared.connection import get_connection
from db.shared.settings_repo import get_setting, set_setting

logger = logging.getLogger(__name__)


class LanguageService:
    """
    Service لقراءة وكتابة لغة الواجهة من/إلى DB.
    كل الـ methods هي class-level — مفيش instance.

    يفتح اتصاله الخاص (الإعدادات مشتركة وليست مرتبطة بـ conn
    الشركة النشطة)، ويغلقه فور الانتهاء — بنفس نمط
    ItemService.get_gimp_path().
    """

    _SETTINGS_KEY = "ui_language"
    _DEFAULT_LANG = "ar"

    # ──────────────────────────────────────────────────────
    # القراءة
    # ──────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> str:
        """
        يقرأ ui_language من DB.
        يرجع _DEFAULT_LANG لو الإعداد غير محفوظ أو حدث خطأ.
        """
        try:
            conn = get_connection()
            try:
                lang = get_setting(conn, cls._SETTINGS_KEY, cls._DEFAULT_LANG)
                return lang or cls._DEFAULT_LANG
            finally:
                conn.close()
        except Exception as e:
            logger.debug("LanguageService.load: read error — %s", e)
            return cls._DEFAULT_LANG

    # ──────────────────────────────────────────────────────
    # الكتابة
    # ──────────────────────────────────────────────────────

    @classmethod
    def save(cls, lang: str) -> bool:
        """
        يكتب ui_language إلى DB.
        يرجع True عند النجاح، False عند الفشل (بصمت — لا يُوقف التطبيق).
        """
        try:
            conn = get_connection()
            try:
                set_setting(conn, cls._SETTINGS_KEY, lang)
                logger.debug("LanguageService.save: saved ui_language=%s", lang)
                return True
            finally:
                conn.close()
        except Exception as e:
            logger.debug("LanguageService.save: write error — %s", e)
            return False
