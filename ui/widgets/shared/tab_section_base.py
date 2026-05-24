"""
ui/widgets/shared/tab_section_base.py
======================================
TabSectionBase — قاعدة مشتركة للأقسام التي تحتوي على QTabWidget.

يوفر:
  - بناء QTabWidget موحد الستايل
  - closeEvent يغلق connection تلقائياً
  - نمط موحد للتبويبات

الاستخدام:
    from ui.widgets.shared.tab_section_base import TabSectionBase

    class RawTab(TabSectionBase):
        def _build_tabs(self, tabs: QTabWidget):
            tabs.addTab(_RawSection(self.conn), "📦  الخامات")
            tabs.addTab(CategoryManager(self.conn, scope="raw"), "🏷️  التصنيفات")

    class ProductTab(TabSectionBase):
        def __init__(self, product_type: str, parent=None):
            self.product_type = product_type  # قبل super().__init__
            super().__init__(parent=parent)

        def _build_tabs(self, tabs: QTabWidget):
            ...
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore    import Qt

from db.shared.connection import get_connection
from ui.app_settings      import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base


def _tab_stylesheet() -> str:
    c    = _C
    base = _base()
    return f"""
        QTabWidget::pane {{
            border: none;
            background: {c['bg_page']};
        }}
        QTabBar::tab {{
            background: {c['bg_surface_2']};
            border: 1px solid {c['border']};
            border-bottom: none;
            padding: 7px 16px;
            margin-left: 2px;
            font-size: {fs(base, 0)}pt;
            color: {c['text_muted']};
            min-width: 80px;
        }}
        QTabBar::tab:selected {{
            background: {c['bg_input']};
            color: {c['accent']};
            font-weight: bold;
            border-top: 2px solid {c['accent']};
        }}
        QTabBar::tab:hover:!selected {{
            background: {c['bg_hover']};
            color: {c['text_primary']};
        }}
    """


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
        self._tabs.setStyleSheet(_tab_stylesheet())
        self._build_tabs(self._tabs)
        root.addWidget(self._tabs)

    def _build_tabs(self, tabs: QTabWidget):
        """
        Override هنا لإضافة التبويبات.
        tabs: QTabWidget جاهز للإضافة.
        """
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