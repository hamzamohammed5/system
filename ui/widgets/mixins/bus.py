"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.

التغييرات:
  - [تحسين 39] إضافة _bus_connected guard في _connect_bus().
    القديم: رغم Qt.UniqueConnection، لو استُدعيت _connect_bus مرتين
    (compound inheritance أو rebuild) ممكن يتصل مرتين في بعض الحالات.
    الجديد: guard instance variable يمنع أي استدعاء ثانٍ بصمت.
    _disconnect_bus() تُعيد ضبط الـ guard عند الفصل.

  - [إصلاح Phase 5 محفوظ] _refresh_guard كـ instance variable.
  - [تحسين 17 محفوظ] _disconnect_bus() للفصل الآمن.

  - [تحسين 24] _on_data_changed_guarded تُسجّل debug log عند التخطي.
    القديم: الـ guard يمنع double-refresh بصمت تاماً.
    الجديد: logger.debug يُسجّل الاسم عند التخطي لتسهيل debugging.
"""
import logging
from PyQt5.QtCore import QTimer, Qt

logger = logging.getLogger(__name__)


class BusConnectedMixin:
    """
    Mixin يوفر ربطاً موحداً بـ event bus.

    الاستخدام الأساسي:
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                self._connect_bus(data=True)

            def _on_data_changed(self):
                self._load()

    للـ cleanup عند حذف الـ widget:
        def closeEvent(self, event):
            self._disconnect_bus()
            super().closeEvent(event)
    """

    def _connect_bus(self, data: bool = True, company: bool = False):
        """
        يربط الـ widget بالـ event bus.

        [تحسين 39] Guard يمنع double-connect:
        لو استُدعيت مرتين (compound inheritance، rebuild، إلخ)
        تُتجاهل الاستدعاءات بعد الأولى بصمت.
        Qt.UniqueConnection وحدها لا تكفي في كل الحالات.

        data=True    → يربط bus.data_changed (global، للتوافق مع الكود القديم)
                       و bus.company_data_changed مع filter تلقائي.
        company=True → يربط bus.company_data_changed فقط لـ _on_company_changed.
        """
        # [تحسين 39] منع double-connect
        if getattr(self, "_bus_connected", False):
            return

        # instance variables — يمنع التشارك بين الـ instances
        self._bus_connected  = True
        self._refresh_guard  = False

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

    def _disconnect_bus(self):
        """
        [تحسين 17] يفصل الـ widget عن الـ bus.

        [تحسين 39] يُعيد ضبط _bus_connected لو احتجت reconnect لاحقاً
        (مثلاً بعد rebuild الـ widget).

        استدعه من closeEvent() أو cleanup() لضمان عدم وجود
        dangling references بعد حذف الـ widget.

        TypeError يُبلع بصمت لأن disconnect يرمي TypeError
        لو الـ slot لم يكن مربوطاً أصلاً.
        """
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
                        pass  # لم يكن مربوطاً — مقبول
        except Exception:
            pass  # bus غير متاح — مقبول أيضاً

        # [تحسين 39] أعد ضبط الـ guard لو احتجت reconnect
        self._bus_connected = False

    def _on_company_data_changed(self, company_id: int):
        """
        Handler داخلي لـ company_data_changed.
        يتحقق إذا كان company_id هو الشركة النشطة.
        """
        from ui.widgets.core.events import is_same_company
        if is_same_company(company_id):
            self._refresh_guard = True
            self._on_data_changed()
            QTimer.singleShot(0, self._clear_refresh_guard)

    def _on_data_changed_guarded(self):
        """
        Wrapper لـ _on_data_changed يتحقق من الـ guard أولاً.
        يمنع double-refresh لو company_data_changed أطلقه بالفعل.

        [تحسين 24] يُسجّل debug log عند التخطي لتسهيل debugging.
        القديم: بصمت تام.
        الجديد: logger.debug يُسجّل اسم الـ class عند التخطي.
        """
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
        pass