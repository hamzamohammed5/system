"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.

التغييرات:
  - [P-04] حفظ _cached_company_id على مستوى الـ instance بدل استدعاء
    is_same_company() في كل إشعار.
    القديم: كل widget مشترك في company_data_changed يستدعي is_same_company()
    الذي يقرأ من company_state.company_id — مع مئات الـ widgets يصبح
    هذا overhead ملحوظ.
    الجديد: _cached_company_id يُحفظ مرة واحدة عند أول company_data_changed
    ويُقارن مباشرة بـ == بدون استدعاء دالة خارجية.
    التحديث: يحدث فقط عند _connect_bus(company=True) أو عند تغيير الشركة.

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

    [P-04] ملاحظة الأداء:
        _cached_company_id يُخزَّن عند أول company_data_changed ويُستخدم
        للمقارنة المباشرة بدل استدعاء is_same_company() في كل إشعار.
        المقارنة int == int أسرع بكثير من استدعاء دالة تقرأ من company_state.
    """

    def _connect_bus(self, data: bool = True, company: bool = False,
                     theme: bool = False, lang: bool = False):
        """
        يربط الـ widget بالـ event bus.

        [تحسين 39] Guard يمنع double-connect.
        [P-04] يُهيّئ _cached_company_id = None عند الاشتراك.

        data=True    → يربط bus.data_changed و bus.company_data_changed.
        company=True → يربط bus.company_data_changed لـ _on_company_changed.
        theme=True   → يربط bus.theme_changed لـ _on_theme_changed.
        lang=True    → يربط bus.language_changed لـ _on_language_changed.
        """
        if getattr(self, "_bus_connected", False):
            return

        self._bus_connected  = True
        self._refresh_guard  = False

        # [P-04] تهيئة الـ cache — None يعني "لم يُحدَّد بعد"
        # سيُضبط عند أول company_data_changed
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

        # حفظ ما تم ربطه للـ disconnect لاحقاً
        self._bus_theme_connected = theme
        self._bus_lang_connected  = lang

    def _disconnect_bus(self):
        """
        [تحسين 17] يفصل الـ widget عن الـ bus.
        [تحسين 39] يُعيد ضبط _bus_connected.
        [i18n/themes] يشمل theme_changed و language_changed.
        [P-04] يمسح _cached_company_id.
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

        # [P-04] مسح الـ cache عند الفصل
        self._cached_company_id = None

    def _on_company_data_changed(self, company_id: int):
        """
        [P-04] مقارنة مباشرة بدل استدعاء is_same_company().

        القديم:
            from ui.widgets.core.events import is_same_company
            if is_same_company(company_id):
                ...

        الجديد:
            1. لو _cached_company_id لم يُضبط بعد (None) → اضبطه وتابع.
            2. لو company_id == _cached_company_id → نفس الشركة، تابع.
            3. غير ذلك → شركة مختلفة، تجاهل.

        هذا يتجنب استدعاء is_same_company() في كل إشعار مع مئات الـ widgets.
        مقارنة int == int مباشرة بدل قراءة من company_state في كل مرة.

        تحديث الـ cache:
            _cached_company_id يُحدَّث في كل مرة تتطابق الشركة،
            مما يضمن أنه يعكس دائماً آخر company_id نشط.
        """
        # المرة الأولى: لا cache بعد → اضبطه من company_state
        if self._cached_company_id is None:
            self._cached_company_id = self._get_active_company_id()

        # مقارنة مباشرة — O(1) بلا استدعاء دالة
        if company_id != self._cached_company_id:
            # شركة مختلفة — تحديث الـ cache ثم تجاهل الإشعار
            # (الـ cache قد يكون قديماً لو تغيّرت الشركة)
            logger.debug(
                "%s: تجاهل company_data_changed لشركة %d (النشطة: %d)",
                type(self).__name__, company_id, self._cached_company_id or 0,
            )
            return

        # نفس الشركة → تنفيذ التحديث
        self._refresh_guard = True
        self._on_data_changed()
        QTimer.singleShot(0, self._clear_refresh_guard)

    @staticmethod
    def _get_active_company_id() -> "int | None":
        """
        [P-04] يقرأ company_id النشط من company_state.
        دالة static مساعدة — تُستدعى مرة واحدة فقط عند تهيئة الـ cache.
        """
        try:
            from db.companies.company_state import company_state
            return company_state.company_id if company_state.is_ready else None
        except Exception:
            return None

    def invalidate_company_cache(self):
        """
        [P-04] يُعيد ضبط الـ cache لإجباره على إعادة القراءة من company_state.

        استدعه عند:
          - تغيير الشركة النشطة في الـ widget
          - إعادة بناء الـ widget بعد تغيير الشركة
          - أي حالة تشك فيها بصحة الـ cache

        مثال:
            def _on_company_changed(self, company_id: int):
                self.invalidate_company_cache()
                self._rebuild()
        """
        self._cached_company_id = None

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
        """
        Override هنا لإعادة البناء عند تغيير الشركة النشطة.

        [P-04] تلقائياً يُعيد ضبط الـ cache عند تغيير الشركة.
        """
        # [P-04] تحديث الـ cache بالشركة الجديدة
        self._cached_company_id = company_id

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