"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.

الإصلاحات:
  - [إصلاح Phase 5 محفوظ] _refresh_guard كـ instance variable.
  - [تحسين 17] إضافة _disconnect_bus() للفصل الآمن عند حذف الـ widget.
    بدون فصل، PyQt بيتعامل مع deleted objects في معظم الأحوال،
    لكن في حالات الـ sip deleted objects أو الـ weak references ممكن crash.
"""
from PyQt5.QtCore import QTimer, Qt


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

        data=True    → يربط bus.data_changed (global، للتوافق مع الكود القديم)
                       و bus.company_data_changed مع filter تلقائي.
        company=True → يربط bus.company_data_changed فقط لـ _on_company_changed.

        Qt.UniqueConnection: يمنع تضاعف الـ slots لو اتستدعى أكتر من مرة.
        """
        # instance variable — يمنع التشارك بين الـ instances
        self._refresh_guard = False

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
        """
        if getattr(self, "_refresh_guard", False):
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