"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.

التغييرات:
  - [i18n/themes] إضافة theme=, lang= parameters في _connect_bus().
    يسمح للـ widgets بالاشتراك في bus.theme_changed و bus.language_changed.
  - [i18n/themes] _on_theme_changed() و _on_language_changed() hooks جديدة.
  - [i18n/themes] _disconnect_bus() يشمل الـ signals الجديدة.
  - [تحسين 39 محفوظ] _bus_connected guard.
  - [إصلاح Phase 5 محفوظ] _refresh_guard كـ instance variable.
  - [تحسين 17 محفوظ] _disconnect_bus() للفصل الآمن.
  - [تحسين 24 محفوظ] debug log عند التخطي.
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

    للاشتراك في تغيير الثيم أو اللغة:
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                self._connect_bus(data=True, theme=True, lang=True)

            def _on_theme_changed(self, theme_name: str):
                self._rebuild_styles()

            def _on_language_changed(self, lang_code: str):
                self._update_texts()

    للـ cleanup عند حذف الـ widget:
        def closeEvent(self, event):
            self._disconnect_bus()
            super().closeEvent(event)
    """

    def _connect_bus(self, data: bool = True, company: bool = False,
                     theme: bool = False, lang: bool = False):
        """
        يربط الـ widget بالـ event bus.

        [تحسين 39] Guard يمنع double-connect.

        data=True    → يربط bus.data_changed و bus.company_data_changed.
        company=True → يربط bus.company_data_changed لـ _on_company_changed.
        theme=True   → يربط bus.theme_changed لـ _on_theme_changed.
        lang=True    → يربط bus.language_changed لـ _on_language_changed.
        """
        if getattr(self, "_bus_connected", False):
            return

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

        if theme:
            bus.theme_changed.connect(
                self._on_theme_changed, Qt.UniqueConnection
            )

        if lang:
            bus.language_changed.connect(
                self._on_language_changed, Qt.UniqueConnection
            )

        # حفظ ما تم ربطه للـ disconnect لاحقاً
        self._bus_theme_connected = theme
        self._bus_lang_connected  = lang

    def _disconnect_bus(self):
        """
        [تحسين 17] يفصل الـ widget عن الـ bus.
        [تحسين 39] يُعيد ضبط _bus_connected.
        [i18n/themes] يشمل theme_changed و language_changed.
        """
        try:
            from ui.events import bus

            # data + company signals
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

            # theme signal
            if getattr(self, "_bus_theme_connected", False):
                try:
                    bus.theme_changed.disconnect(self._on_theme_changed)
                except (TypeError, RuntimeError):
                    pass

            # language signal
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

    def _on_company_data_changed(self, company_id: int):
        from ui.widgets.core.events import is_same_company
        if is_same_company(company_id):
            self._refresh_guard = True
            self._on_data_changed()
            QTimer.singleShot(0, self._clear_refresh_guard)

    def _on_data_changed_guarded(self):
        """
        [تحسين 24] يُسجّل debug log عند التخطي.
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

    def _on_theme_changed(self, theme_name: str):
        """
        [i18n/themes] Override هنا لإعادة تطبيق الـ styles عند تغيير الثيم.

        مثال:
            def _on_theme_changed(self, theme_name: str):
                self.setStyleSheet(f"background:{_C['bg_input']};")
                self._empty_state.setStyleSheet(...)
        """
        pass

    def _on_language_changed(self, lang_code: str):
        """
        [i18n/themes] Override هنا لتحديث النصوص عند تغيير اللغة.

        مثال:
            def _on_language_changed(self, lang_code: str):
                self.btn_add.setText(tr("btn_add"))
                self._search_bar.set_placeholder(tr("list_search_placeholder"))
        """
        pass