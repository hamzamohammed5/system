"""
services/shared/font_service.py
================================
FontService — الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات
لكل عمليات حجم الخط.

المسؤولية:
  - قراءة font_size من DB عبر settings_repo
  - كتابة font_size إلى DB عبر settings_repo

لماذا service وليس تواصل مباشر؟
  يحقق هذا الملف الهيكلة المطلوبة:
    ui/font.py  →  AppState  →  FontService  →  settings_repo  →  DB
  أي أن طبقة الـ UI لا تعرف شيئاً عن DB أو settings_repo.
  كل تغيير في طريقة التخزين (مثل تحويل النظام لـ online) يحدث
  هنا فقط دون لمس أي ملف في ui/.

الاستخدام (من AppState فقط):
    from services.shared.font_service import FontService
    size = FontService.load()          # يقرأ من DB
    FontService.save(size)             # يكتب للـ DB

لا يُستخدم هذا الملف مباشرةً من أي ملف في ui/.
"""

from __future__ import annotations
import logging

from ui.constants import DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE

logger = logging.getLogger(__name__)


class FontService:
    """
    Service لقراءة وكتابة font_size من/إلى DB.
    كل الـ methods هي class-level — مفيش instance.

    التسلسل الكامل:
        ui/font.py
            ↓  (get/set_font_size)
        ui/app_state.AppState
            ↓  (font_size / on_font_changed)
        services/shared/font_service.FontService   ← أنت هنا
            ↓  (load / save)
        db/shared/settings_repo
            ↓  (get_setting / set_setting)
        SQLite / DB
    """

    _SETTINGS_KEY = "font_size"

    # ──────────────────────────────────────────────────────
    # القراءة
    # ──────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> int:
        """
        يقرأ font_size من DB.
        - لو المفتاح غير موجود → يحفظ DEFAULT_FONT_SIZE ويرجعه.
        - لو القيمة خارج النطاق المسموح → يحفظ DEFAULT_FONT_SIZE ويرجعه.
        - لو فشل الاتصال بالكامل → يرجع DEFAULT_FONT_SIZE بصمت.
        """
        try:
            conn = cls._get_conn()
        except Exception as e:
            logger.debug("FontService.load: cannot connect — %s", e)
            return DEFAULT_FONT_SIZE

        try:
            from db.shared.settings_repo import get_setting, set_setting
            raw = get_setting(conn, cls._SETTINGS_KEY, None)

            if raw is None:
                set_setting(conn, cls._SETTINGS_KEY, DEFAULT_FONT_SIZE)
                return DEFAULT_FONT_SIZE

            val = int(float(raw))
            if not (MIN_FONT_SIZE <= val <= MAX_FONT_SIZE):
                logger.debug(
                    "FontService.load: value %d out of range [%d, %d], resetting",
                    val, MIN_FONT_SIZE, MAX_FONT_SIZE
                )
                set_setting(conn, cls._SETTINGS_KEY, DEFAULT_FONT_SIZE)
                return DEFAULT_FONT_SIZE

            return val

        except Exception as e:
            logger.debug("FontService.load: read error — %s", e)
            return DEFAULT_FONT_SIZE

    # ──────────────────────────────────────────────────────
    # الكتابة
    # ──────────────────────────────────────────────────────

    @classmethod
    def save(cls, size: int) -> bool:
        """
        يكتب font_size إلى DB.
        يرجع True عند النجاح، False عند الفشل (بصمت — لا يُوقف التطبيق).

        ملاحظة: التحقق من النطاق يحدث في AppState قبل استدعاء هذه الدالة،
        لكن نُعيده هنا كطبقة أمان إضافية.
        """
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))

        try:
            conn = cls._get_conn()
        except Exception as e:
            logger.debug("FontService.save: cannot connect — %s", e)
            return False

        try:
            from db.shared.settings_repo import set_setting
            set_setting(conn, cls._SETTINGS_KEY, size)
            logger.debug("FontService.save: saved font_size=%d", size)
            return True
        except Exception as e:
            logger.debug("FontService.save: write error — %s", e)
            return False


