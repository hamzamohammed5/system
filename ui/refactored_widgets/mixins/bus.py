"""
ui/widgets/mixins/bus.py
=================================
BusConnectedMixin — ربط تلقائي بـ event bus.
"""


class BusConnectedMixin:
    """
    Mixin يوفر ربطاً موحداً بـ event bus.

    الاستخدام:
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                self._connect_bus(data=True, company=True)

            def _on_data_changed(self):
                self._load()

            def _on_company_changed(self, company_id: int):
                self._rebuild()
    """

    def _connect_bus(self, data: bool = True, company: bool = False):
        from ui.events import bus
        if data:
            bus.data_changed.connect(self._on_data_changed)
        if company:
            bus.company_data_changed.connect(self._on_company_changed)

    def _on_data_changed(self):
        pass

    def _on_company_changed(self, company_id: int):
        pass