"""
ui/widgets/mixins/rebuild.py
=====================================
RebuildMixin — إعادة بناء محتوى الـ tab عند تغيير الشركة.
"""
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget


class RebuildMixin:
    """
    Mixin يوفر _replace_widget() لإعادة بناء محتوى الـ tab.

    يفترض: self._root_layout (QVBoxLayout)
    """

    def _replace_widget(self, new_widget: QWidget):
        root = getattr(self, "_root_layout", None)
        if root is None:
            return

        old = getattr(self, "_current_widget", None)
        if old is not None:
            root.removeWidget(old)
            old.hide()
            old.deleteLater()

        self._current_widget = new_widget
        if new_widget is not None:
            root.addWidget(new_widget)

    def _schedule_rebuild(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._rebuild)

    def _rebuild(self):
        pass