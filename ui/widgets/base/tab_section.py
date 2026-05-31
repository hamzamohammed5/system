"""
ui/widgets/base/tab_section.py
==========================================
TabSectionBase — قاعدة مشتركة للأقسام التي تحتوي على QTabWidget.

التغيير: closeEvent لم يعد يستدعي conn.close() بشكل أعمى.
get_connection() ترجع shared connection من company_state،
إغلاقها هنا يكسر كل الـ widgets الأخرى.
الإغلاق الصحيح يحدث فقط في company_state عند تغيير الشركة.

[إصلاح 18] توضيح سلوك _is_owned_connection:
  - دالة آمنة تماماً: عند أي exception ترجع False (لا تُغلق).
  - السلوك المقصود: الشركة لم تتحمل بعد → company_state.get_erp_conn يرمي → False → لا إغلاق.
  - هذا مقصود لأن الأمان أهم من إغلاق connection ربما لا يحتاج إغلاقاً.

[FIX] استبدال company_state._get_conn("erp") (private API) بـ
      company_state.get_erp_conn() (public API).
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from db.shared.connection      import get_connection
from ..theme.layout_styles     import tab_style


def _is_owned_connection(conn) -> bool:
    """
    يتحقق إذا كان الـ connection ملك هذا الـ widget
    (يعني مش shared من company_state).

    الاتصالات المشتركة لا يجب إغلاقها من الـ widgets.

    السلوك المقصود عند الفشل:
    - لو company_state لم يُحمَّل بعد → get_erp_conn يرمي → except → False
    - لو conn is None → False
    - لو conn هو نفس الـ shared connection → False (shared → لا تُغلق)
    - لو conn مختلف (مُنشأ يدوياً) → True (owned → يُغلق)

    الإرجاع بـ False عند الشك هو الاختيار الآمن:
    أفضل من إغلاق connection لا يجب إغلاقه وكسر widgets أخرى.

    [FIX] استخدام get_erp_conn() (public) بدل _get_conn("erp") (private).
    """
    if conn is None:
        return False
    try:
        from db.companies.company_state import company_state
        # [FIX] get_erp_conn() بدل _get_conn("erp") — استخدام الـ public API
        shared = company_state.get_erp_conn()
        return conn is not shared
    except Exception:
        # لو مش قادر يتحقق (شركة غير محملة، company_state غير جاهز)
        # → الأأمن هو عدم الإغلاق
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

        [إصلاح 18] _is_owned_connection ترجع False عند أي شك،
        وهو السلوك الآمن المقصود. راجع docstring الدالة للتفاصيل.
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