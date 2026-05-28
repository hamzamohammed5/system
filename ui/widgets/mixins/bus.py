"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.

التغييرات في هذا الإصدار (Phase 5):
  - _refresh_guard أصبح instance variable بدل class variable.
    الـ class variable القديم كان مشتركاً بين كل الـ instances،
    يعني لو instance واحد عمله True، كل التانية بتتجاهل الـ refresh.
    الإصلاح: self._refresh_guard = False في بداية _connect_bus.
"""
from PyQt5.QtCore import QTimer, Qt


class BusConnectedMixin:
    """
    Mixin يوفر ربطاً موحداً بـ event bus.

    الاستخدام الأساسي (data فقط — الأكثر شيوعاً):
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                self._connect_bus(data=True)

            def _on_data_changed(self):
                self._load()

    الاستخدام مع company filter (الأفضل للـ widgets المرتبطة بشركة):
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                self._connect_bus(data=True, company=True)

            def _on_data_changed(self):
                self._load()

    للـ widgets اللي محتاجة تعرف الـ company_id:
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                self._connect_bus(company=True)

            def _on_company_changed(self, company_id: int):
                self._rebuild_for(company_id)

    ⚠️  تحذير double-connect:
        Qt.UniqueConnection تمنع تضاعف الـ slots لو _connect_bus()
        اتستدعت أكتر من مرة على نفس الـ widget instance.

    ⚠️  تحذير double-refresh:
        لما data=True بنربط data_changed و company_data_changed معاً.
        لو الكود القديم أطلق الاتنين في نفس الوقت، الـ widget هيعمل
        refresh مرتين. الـ _refresh_guard بيمنع ده تلقائياً.
        الأفضل: استخدم emit_company_data_changed() من ui.widgets.core.events.
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

    def _on_company_data_changed(self, company_id: int):
        """
        Handler داخلي لـ company_data_changed.
        بيتحقق إذا كان company_id هو الشركة النشطة
        قبل ما يستدعي _on_data_changed.
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