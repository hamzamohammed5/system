"""
ui/widgets/shared/base_section.py
===================================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.

توفر:
  - SmartSplitter يقسم الـ list والـ detail
  - عرض الـ list ثابت على قد المحتوى
  - الـ detail يكبر مع النافذة
  - الـ horizontal scroll يختفي لأن العرض مضبوط

الاستخدام:
    class MySection(BaseSection):
        def _create_list(self) -> BaseListPanel:
            return MyListPanel(self.conn)

        def _create_detail(self) -> BaseDetailPanel:
            return MyDetailPanel(self.conn)

        def _connect_signals(self):
            self._list.item_selected.connect(self._detail.load_item)
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore    import Qt

from ui.widgets.shared.splitter_utils import SmartSplitter


class BaseSection(QWidget):
    """
    قاعدة مشتركة للأقسام اللي فيها list + detail.

    Override:
      _create_list(), _create_detail(), _connect_signals()
      LIST_MIN_W, LIST_MAX_W
    """

    LIST_MIN_W : int = 280
    LIST_MAX_W : int = 560

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._connect_signals()
        self._splitter.fit_delayed(80)

    # ══════════════════════════════════════════════════════
    # override في الـ subclass
    # ══════════════════════════════════════════════════════

    def _create_list(self):
        """يرجع الـ list panel."""
        raise NotImplementedError

    def _create_detail(self):
        """يرجع الـ detail panel."""
        raise NotImplementedError

    def _connect_signals(self):
        """يربط الـ signals بين الـ list والـ detail."""
        pass

    def _get_list_table(self):
        """يرجع الجدول الرئيسي في الـ list panel."""
        if hasattr(self._list, 'table'):
            return self._list.table
        return None

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = SmartSplitter(Qt.Horizontal)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)

        table = self._get_list_table()
        if table:
            self._splitter.set_list_widget(
                self._list,
                list_table=table,
                min_w=self.LIST_MIN_W,
                max_w=self.LIST_MAX_W,
            )

        self._splitter.setSizes([self.LIST_MIN_W, 800])
        root.addWidget(self._splitter)

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _fit_splitter(self):
        self._splitter.fit_now()

    def _fit_splitter_delayed(self, delay_ms: int = 80):
        self._splitter.fit_delayed(delay_ms)

    def refresh(self):
        if hasattr(self._list, 'refresh'):
            self._list.refresh()
        self._fit_splitter_delayed()