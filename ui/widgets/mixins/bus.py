"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.

التغييرات:
  - [P-04] حفظ _cached_company_id على مستوى الـ instance بدل استدعاء
    is_same_company() في كل إشعار.
  - [i18n/themes] إضافة theme=, lang= parameters في _connect_bus().
  - [تحسين 39 محفوظ] _bus_connected guard.
  - [إصلاح Phase 5 محفوظ] _refresh_guard كـ instance variable.
  - [تحسين 17 محفوظ] _disconnect_bus() للفصل الآمن.
  - [تحسين 24 محفوظ] debug log عند التخطي.

  [Phase 6 إصلاح] _on_company_data_changed:
    القديم: لو _cached_company_id == None يُضبط من company_state ثم يُقارن —
            لو company_state لم يُحمَّل بعد يرجع None → company_id != None → يُتجاهل الإشعار الأول!
    الجديد: لو _cached_company_id لا يزال None بعد القراءة من company_state،
            نضبطه من company_id المُستلم ونتابع بدل التجاهل.
"""
import logging
from PyQt5.QtCore import QTimer, Qt

logger = logging.getLogger(__name__)


class BusConnectedMixin:
    """
    Mixin يوفر ربطاً موحداً بـ event bus.

    [Phase 6] إصلاح حالة أول إشعار: لو _cached_company_id لا يزال None
    بعد محاولة قراءته من company_state (شركة لم تُحمَّل بعد)، نضبطه
    من company_id الواصل ونتابع بدل إسقاط الإشعار.
    """

    def _connect_bus(self, data: bool = True, company: bool = False,
                     theme: bool = False, lang: bool = False):
        """
        يربط الـ widget بالـ event bus.

        [تحسين 39] Guard يمنع double-connect.
        [P-04] يُهيّئ _cached_company_id = None عند الاشتراك.
        """
        if getattr(self, "_bus_connected", False):
            return

        self._bus_connected  = True
        self._refresh_guard  = False
        self._cached_company_id: "int | None" = None

        from ui.events import bus

        if data:
            bus.company_data_changed.connect(
                self._on_company_data_changed, Qt.UniqueConnection
            )
            bus.data_changed.connect(
                self._on_data_changed_guarded, Qt.UniqueConnection
            )

        if company:
            bus.company_data_changed.connect(
                self._on_company_changed, Qt.UniqueConnection
            )

        if theme:
            bus.theme_changed.connect(
                self._on_theme_changed, Qt.UniqueConnection
            )

        if lang:
            bus.language_changed.connect(
                self._on_language_changed, Qt.UniqueConnection
            )

        self._bus_theme_connected = theme
        self._bus_lang_connected  = lang

    def _disconnect_bus(self):
        """يفصل الـ widget عن الـ bus."""
        try:
            from ui.events import bus

            for signal in (bus.company_data_changed, bus.data_changed):
                for slot in (
                    self._on_company_data_changed,
                    self._on_data_changed_guarded,
                    self._on_company_changed,
                ):
                    try:
                        signal.disconnect(slot)
                    except (TypeError, RuntimeError):
                        pass

            if getattr(self, "_bus_theme_connected", False):
                try:
                    bus.theme_changed.disconnect(self._on_theme_changed)
                except (TypeError, RuntimeError):
                    pass

            if getattr(self, "_bus_lang_connected", False):
                try:
                    bus.language_changed.disconnect(self._on_language_changed)
                except (TypeError, RuntimeError):
                    pass

        except Exception:
            pass

        self._bus_connected       = False
        self._bus_theme_connected = False
        self._bus_lang_connected  = False
        self._cached_company_id   = None

    def _on_company_data_changed(self, company_id: int):
        """
        [Phase 6 إصلاح] معالجة أول إشعار بشكل صحيح.

        الخطوات:
          1. لو _cached_company_id = None → جرب القراءة من company_state.
          2. لو لا يزال None (شركة لم تُحمَّل بعد) → اضبطه من company_id الواصل وتابع.
             (القديم: يُقارن None != company_id → يُتجاهل → أول إشعار يضيع)
          3. لو company_id != _cached_company_id → شركة مختلفة → تجاهل.
          4. نفس الشركة → تنفيذ التحديث.
        """
        # الخطوة 1: جرب ملء الـ cache من company_state
        if self._cached_company_id is None:
            self._cached_company_id = self._get_active_company_id()

        # الخطوة 2: لو لا يزال None → اضبطه من الإشعار نفسه وتابع
        if self._cached_company_id is None:
            self._cached_company_id = company_id
            # لا نرجع — نتابع لتنفيذ التحديث

        # الخطوة 3: مقارنة مباشرة
        elif company_id != self._cached_company_id:
            logger.debug(
                "%s: تجاهل company_data_changed لشركة %d (النشطة: %d)",
                type(self).__name__, company_id, self._cached_company_id,
            )
            return

        # الخطوة 4: نفس الشركة → تنفيذ التحديث
        self._refresh_guard = True
        self._on_data_changed()
        QTimer.singleShot(0, self._clear_refresh_guard)

    @staticmethod
    def _get_active_company_id() -> "int | None":
        """يقرأ company_id النشط من company_state."""
        try:
            from db.companies.company_state import company_state
            return company_state.company_id if company_state.is_ready else None
        except Exception:
            return None

    def invalidate_company_cache(self):
        """يُعيد ضبط الـ cache لإجباره على إعادة القراءة من company_state."""
        self._cached_company_id = None

    def _on_data_changed_guarded(self):
        """[تحسين 24] يُسجّل debug log عند التخطي."""
        if getattr(self, "_refresh_guard", False):
            logger.debug(
                "%s: تخطّي data_changed المكرر (refresh_guard نشط)",
                type(self).__name__,
            )
            return
        self._on_data_changed()

    def _clear_refresh_guard(self):
        self._refresh_guard = False

    def _on_data_changed(self):
        """Override هنا لتحديث الـ widget عند تغيير البيانات."""
        pass

    def _on_company_changed(self, company_id: int):
        """Override هنا لإعادة البناء عند تغيير الشركة النشطة."""
        self._cached_company_id = company_id

    def _on_theme_changed(self, theme_name: str):
        """Override هنا لإعادة تطبيق الـ styles عند تغيير الثيم."""
        pass

    def _on_language_changed(self, lang_code: str):
        """Override هنا لتحديث النصوص عند تغيير اللغة."""
        pass