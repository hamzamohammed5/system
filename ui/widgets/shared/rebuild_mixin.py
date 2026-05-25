"""
ui/widgets/shared/rebuild_mixin.py
====================================
RebuildMixin — مكسن موحد للـ widgets التي تحتاج إعادة بناء عند تغيير الشركة.

يحل التكرار في:
  - FinancialStatementsTab._rebuild()
  - InvestorsTab._rebuild()
  - AccountingTab._build()
  وأي tab آخر يحتاج نفس النمط.

الاستخدام:
    class MyTab(RebuildMixin, QWidget):
        def __init__(self, conn, parent=None):
            super().__init__(parent)
            self._root_layout = QVBoxLayout(self)
            self._root_layout.setContentsMargins(0, 0, 0, 0)
            self._current_widget = None
            self._build()

        def _build_widget(self):
            \"\"\"Override: يرجع الـ widget الجديد.\"\"\"
            return MyInnerWidget(self.conn)

        def _build(self):
            self._replace_widget(self._build_widget())
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer


class RebuildMixin:
    """
    مكسن يوفر _replace_widget() لإعادة بناء محتوى الـ tab.

    يفترض وجود:
      - self._root_layout : QVBoxLayout
      - self._current_widget : QWidget | None  (اختياري)
    """

    def _replace_widget(self, new_widget: QWidget):
        """
        يستبدل الـ widget الحالي بآخر جديد.
        يتعامل مع الـ cleanup بأمان.
        """
        root = getattr(self, '_root_layout', None)
        if root is None:
            return

        old = getattr(self, '_current_widget', None)
        if old is not None:
            root.removeWidget(old)
            old.hide()
            old.deleteLater()

        self._current_widget = new_widget
        if new_widget is not None:
            root.addWidget(new_widget)

    def _schedule_rebuild(self, delay_ms: int = 0):
        """يجدول إعادة البناء بعد delay اختياري."""
        QTimer.singleShot(delay_ms, self._rebuild)

    def _rebuild(self):
        """Override لإعادة البناء الكامل."""
        pass