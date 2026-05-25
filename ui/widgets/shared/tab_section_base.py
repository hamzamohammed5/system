"""
ui/widgets/shared/tab_section_base.py
======================================
TabSectionBase — قاعدة مشتركة للأقسام التي تحتوي على QTabWidget.

[إصلاح v2]:
  - _tab_stylesheet() استُبدلت بـ get_tab_style() من theme بدل inline CSS مكرر

الاستخدام:
    class RawTab(TabSectionBase):
        def _build_tabs(self, tabs: QTabWidget):
            tabs.addTab(_RawSection(self.conn), "📦  الخامات")
            tabs.addTab(CategoryManager(self.conn, scope="raw"), "🏷️  التصنيفات")
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.shared.connection import get_connection
from ui.widgets.shared.panles_helper.theme import get_tab_style


class TabSectionBase(QWidget):
    """
    قاعدة مشتركة للأقسام ذات التبويبات.

    المعاملات:
        conn_fn : دالة لجلب الـ connection (افتراضياً get_connection)
        parent  : الـ parent widget
    """

    def __init__(self, conn_fn=None, parent=None):
        super().__init__(parent)
        self.conn = (conn_fn or get_connection)()
        self._tabs: QTabWidget | None = None
        self._setup()

    def _setup(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(get_tab_style())
        self._build_tabs(self._tabs)
        root.addWidget(self._tabs)

    def _build_tabs(self, tabs: QTabWidget):
        """Override هنا لإضافة التبويبات."""
        raise NotImplementedError

    def closeEvent(self, event):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        super().closeEvent(event)

    @property
    def current_tab(self) -> QWidget | None:
        if self._tabs:
            return self._tabs.currentWidget()
        return None