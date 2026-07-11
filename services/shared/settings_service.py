"""
services/shared/settings_service.py
=====================================
SettingsService — الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات
لقراءة وكتابة أي إعداد عام مشترك (settings) غير مرتبط بشركة معينة.

لماذا service وليس تواصل مباشر؟
  ui/widgets/dialogs/settings_dialog.py كان يستدعي
  db.shared.settings_repo (get_setting/set_setting) مباشرة من داخل
  widgets/ — كسر هيكلي (تجاوز لطبقة services/).
  هذا الملف يحل المشكلة بنفس نمط language_service.py:
  إعداد مشترك غير مرتبط بشركة معينة، يفتح اتصاله الخاص عبر
  db.shared.connection.get_connection() ويغلقه فور الانتهاء.

عام (generic) وليس مخصصاً لمفتاح واحد — أي إعداد مشترك مستقبلي
(غير الخط أو اللغة، اللي ليهم service مخصص فعلاً: FontService,
LanguageService) يُقرأ ويُكتب من هنا بدل تكرار نفس نمط
get_connection/get_setting/set_setting في كل مكان.

الاستخدام (من settings_dialog.py أو أي UI آخر):
    from services.shared.settings_service import SettingsService
    path = SettingsService.get("gimp_path", "")   # يقرأ من DB
    SettingsService.set("gimp_path", path)        # يكتب للـ DB

لا يُستخدم مباشرةً من أي ملف في db/ أو خارج services/ أو ui/.
"""

from __future__ import annotations
import logging

from db.shared.connection import get_connection
from db.shared.settings_repo import get_setting, set_setting

logger = logging.getLogger(__name__)


class SettingsService:
    """
    Service عام لقراءة وكتابة أي إعداد مشترك من/إلى DB.
    كل الـ methods هي class-level — مفيش instance.

    يفتح اتصاله الخاص (الإعدادات مشتركة وليست مرتبطة بـ conn
    الشركة النشطة)، ويغلقه فور الانتهاء — بنفس نمط
    LanguageService و ItemService.get_gimp_path().
    """

    # ──────────────────────────────────────────────────────
    # القراءة
    # ──────────────────────────────────────────────────────

    @classmethod
    def get(cls, key: str, default=None):
        """
        يقرأ قيمة إعداد بالمفتاح key من DB.
        يرجع default لو الإعداد غير محفوظ أو حدث خطأ.
        """
        try:
            conn = get_connection()
            try:
                val = get_setting(conn, key, default)
                return val if val is not None else default
            finally:
                conn.close()
        except Exception as e:
            logger.debug("SettingsService.get(%s): read error — %s", key, e)
            return default

    # ──────────────────────────────────────────────────────
    # الكتابة
    # ──────────────────────────────────────────────────────

    @classmethod
    def set(cls, key: str, value) -> bool:
        """
        يكتب قيمة إعداد بالمفتاح key إلى DB.
        يرجع True عند النجاح، False عند الفشل (بصمت — لا يُوقف التطبيق).
        """
        try:
            conn = get_connection()
            try:
                set_setting(conn, key, value)
                logger.debug("SettingsService.set: saved %s=%s", key, value)
                return True
            finally:
                conn.close()
        except Exception as e:
            logger.debug("SettingsService.set(%s): write error — %s", key, e)
            return False
