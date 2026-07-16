"""
ui/widgets/base/tab_section.py
==========================================
TabSectionBase — قاعدة مشتركة للأقسام التي تحتوي على QTabWidget.

[إصلاح هيكلة] widgets/ (base classes) ممنوعة تستدعي db/ أو services/
مباشرة حسب الهيكلة المعمارية للمشروع. لذلك:
  - conn_fn أصبح معامل إلزامي (لا default) — يُمرَّر من tabs/ فقط،
    التي تفتح الاتصال عبر الطبقة الصحيحة (services/).
  - _is_owned_connection حُذفت بالكامل: كانت تستدعي
    db.companies.company_state مباشرة من widgets/ لتحديد ملكية
    الـ connection — وهذا كسر هيكلي بحد ذاته.
  - closeEvent لم يعد يغلق self.conn إطلاقاً. الـ widget لا يعرف
    ولا يقرر ملكية الاتصال؛ هذا قرار tabs/ عند اختيار conn_fn.
    الإغلاق الفعلي يحدث في company_state عند تغيير الشركة، أو
    في tabs/ صراحة لو كان الاتصال مملوكاً فعلاً لها.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ..theme.layout_styles           import tab_style, apply_tab_widths, normalize_tab_widget
from ui.widgets.core.widget_mixin    import WidgetMixin


class TabSectionBase(QWidget, WidgetMixin):
    """
    قاعدة مشتركة للأقسام ذات التبويبات.

    الاستخدام:
        class RawTab(TabSectionBase):
            def _build_tabs(self, tabs: QTabWidget):
                tabs.addTab(_RawSection(self.conn), "📦  الخامات")
                tabs.addTab(CategoryManager(self.conn, scope="raw"), "🏷️  التصنيفات")
    """

    def __init__(self, conn_fn, parent=None):
        super().__init__(parent)
        self.conn  = conn_fn()
        self._tabs: "QTabWidget | None" = None
        self._setup()
        self._init_widget_mixin(theme=True, font=False, lang=False)
        self._refresh_style()

    def _setup(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        normalize_tab_widget(self._tabs)
        self._build_tabs(self._tabs)
        # [حل مركزي لقص نص التبويبات] بما إن كل الأقسام الوارثة من
        # TabSectionBase بتضيف تبويباتها داخل _build_tabs()، نحسب
        # العرض الفعلي مرة واحدة هنا بعد ما التبويبات كلها اتضافت —
        # بدل ما كل قسم فرعي يستدعيها بنفسه.
        apply_tab_widths(self._tabs)
        root.addWidget(self._tabs)

    def _refresh_style(self, *_):
        if self._tabs:
            self._tabs.setStyleSheet(tab_style())
            apply_tab_widths(self._tabs)

    def _build_tabs(self, tabs: QTabWidget):
        """Override هنا لإضافة التبويبات."""
        raise NotImplementedError

    def closeEvent(self, event):
        """
        لا يُغلق self.conn إطلاقاً — الـ widget لا يعرف ولا يقرر
        ملكية الاتصال (كان ذلك يتطلب استدعاء company_state مباشرة
        من widgets/، وهو كسر هيكلي). الإغلاق يحدث في company_state
        عند تغيير الشركة، أو في tabs/ صراحة عند الحاجة.
        """
        super().closeEvent(event)

    @property
    def current_tab(self) -> "QWidget | None":
        if self._tabs:
            return self._tabs.currentWidget()
        return None