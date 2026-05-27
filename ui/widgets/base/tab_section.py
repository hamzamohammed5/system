"""
ui/widgets/base/tab_section.py
==========================================
TabSectionBase — قاعدة مشتركة للأقسام التي تحتوي على QTabWidget.

التغيير: closeEvent لم يعد يستدعي conn.close() بشكل أعمى.
get_connection() ترجع shared connection من company_state،
إغلاقها هنا يكسر كل الـ widgets الأخرى.
الإغلاق الصحيح يحدث فقط في company_state عند تغيير الشركة.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.shared.connection      import get_connection
from ..theme.styles            import tab_style


def _is_owned_connection(conn) -> bool:
    """
    يتحقق إذا كان الـ connection ملك هذا الـ widget
    (يعني مش shared من company_state).

    الاتصالات المشتركة لا يجب إغلاقها من الـ widgets.
    """
    if conn is None:
        return False
    try:
        from db.companies.company_state import company_state
        # لو نفس الـ connection اللي company_state بيديه → shared → لا تقفله
        shared = company_state._get_conn("erp")
        return conn is not shared
    except Exception:
        # لو مش قادر يتحقق → الأأمن هو عدم الإغلاق
        return False


class TabSectionBase(QWidget):
    """
    قاعدة مشتركة للأقسام ذات التبويبات.

    الاستخدام:
        class RawTab(TabSectionBase):
            def _build_tabs(self, tabs: QTabWidget):
                tabs.addTab(_RawSection(self.conn), "📦  الخامات")
                tabs.addTab(CategoryManager(self.conn, scope="raw"), "🏷️  التصنيفات")
    """

    def __init__(self, conn_fn=None, parent=None):
        super().__init__(parent)
        self.conn  = (conn_fn or get_connection)()
        self._tabs: "QTabWidget | None" = None
        self._setup()

    def _setup(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(tab_style())
        self._build_tabs(self._tabs)
        root.addWidget(self._tabs)

    def _build_tabs(self, tabs: QTabWidget):
        """Override هنا لإضافة التبويبات."""
        raise NotImplementedError

    def closeEvent(self, event):
        """
        لا يُغلق الـ connection إلا لو كان مملوكاً فعلاً لهذا الـ widget
        (أي مش shared من company_state).

        في الغالب الـ connection مشترك، لذا لا شيء يُغلق هنا —
        الإغلاق يحدث في company_state عند تغيير الشركة.
        """
        if _is_owned_connection(self.conn):
            try:
                self.conn.close()
            except Exception:
                pass
        super().closeEvent(event)

    @property
    def current_tab(self) -> "QWidget | None":
        if self._tabs:
            return self._tabs.currentWidget()
        return None