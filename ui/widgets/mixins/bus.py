"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.

التغييرات:
  - _connect_bus() بقت تدعم company=True بشكل صح:
    بدل ربط data_changed العام (بيعمل refresh لكل الـ widgets)،
    الآن بتربط company_data_changed وبتتحقق من الشركة قبل الاستجابة.
  - _on_company_data_changed() جديدة — تعمل filter على company_id
    وبتستدعي _on_data_changed() بس لو نفس الشركة النشطة.
  - الـ widgets اللي تورث منها تقدر تـ override أي من الدالتين.

تحذير double-refresh (إصلاح #6):
  لما data=True، بنربط الاتنين:
    - bus.data_changed         → _on_data_changed() مباشرة
    - bus.company_data_changed → _on_company_data_changed() → _on_data_changed()

  لو حد emit الاتنين مع بعض (data_changed + company_data_changed)،
  الـ widget هيعمل refresh مرتين.

  الحل المُطبَّق: _on_company_data_changed بتستخدم _refresh_guard
  لتجاهل الـ refresh التاني لو حصل في نفس الـ event loop cycle.

  التوصية للكود الجديد:
    - استخدم emit_company_data_changed() من ui.widgets.core.events
      دايماً — بتطلق واحد بس (company أو global).
    - تجنب emit data_changed و company_data_changed في نفس الوقت.
"""
from PyQt5.QtCore import QTimer


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
            # _on_data_changed بيتستدعى تلقائياً بس لو نفس الشركة

    للـ widgets اللي محتاجة تعرف الـ company_id:
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                self._connect_bus(company=True)

            def _on_company_changed(self, company_id: int):
                self._rebuild_for(company_id)

    ⚠️  تحذير double-refresh:
        لما data=True بنربط data_changed و company_data_changed معاً.
        لو الكود القديم أطلق الاتنين في نفس الوقت، الـ widget هيعمل
        refresh مرتين. الـ _refresh_guard بيمنع ده تلقائياً.
        الأفضل: استخدم emit_company_data_changed() من ui.widgets.core.events.
    """

    # guard لمنع double-refresh في نفس الـ event loop cycle
    _refresh_guard: bool = False

    def _connect_bus(self, data: bool = True, company: bool = False):
        """
        يربط الـ widget بالـ event bus.

        data=True    → يربط bus.data_changed (global، للتوافق مع الكود القديم)
                       و bus.company_data_changed مع filter تلقائي.
        company=True → يربط bus.company_data_changed فقط لـ _on_company_changed.

        ملاحظة: لو data=True وcompany=True،
        _on_data_changed بتتستدعى بس لو نفس الشركة النشطة.
        """
        from ui.events import bus

        if data:
            # الربط الجديد — مع filter على الشركة + guard لمنع double-refresh
            bus.company_data_changed.connect(self._on_company_data_changed)
            # الربط القديم — للتوافق مع الكود اللي بيطلق bus.data_changed مباشرة
            bus.data_changed.connect(self._on_data_changed_guarded)

        if company:
            bus.company_data_changed.connect(self._on_company_changed)

    def _on_company_data_changed(self, company_id: int):
        """
        Handler داخلي لـ company_data_changed.
        بيتحقق إذا كان company_id هو الشركة النشطة
        قبل ما يستدعي _on_data_changed.

        هذا يمنع كل الـ widgets من عمل refresh
        عند تغيير بيانات شركة مختلفة.
        """
        from ui.widgets.core.events import is_same_company
        if is_same_company(company_id):
            # نشغّل guard لمنع data_changed من إطلاق refresh ثانية
            self._refresh_guard = True
            self._on_data_changed()
            # نرجع للـ False بعد الـ event loop الحالية تخلص
            QTimer.singleShot(0, self._clear_refresh_guard)

    def _on_data_changed_guarded(self):
        """
        Wrapper لـ _on_data_changed يتحقق من الـ guard أولاً.
        يمنع double-refresh لو company_data_changed أطلقه بالفعل.
        """
        if self._refresh_guard:
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