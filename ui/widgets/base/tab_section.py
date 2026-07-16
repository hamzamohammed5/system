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
        # [إصلاح lang] كان lang=False هنا يعني إن كل الأقسام الوارثة من
        # TabSectionBase (RawTab/LaborTab/MachineTab/ProductTab وغيرهم)
        # مش بتستجيب لتغيير اللغة لايف — عناوين تباتها الفرعية (📦 الخامات،
        # 🏷️ التصنيفات...) كانت بتتبني مرة واحدة بس وقت _build_tabs()
        # وتفضل زي ما هي حتى لو المستخدم بدّل اللغة من الإعدادات.
        # بقى lang=True هنا؛ _refresh_lang() العامة تحت بتستخدم hook
        # اختياري (_tab_label) كل وريث يقدر يوفره لو حابب يدعم إعادة
        # بناء نص تاباته عند تغيير اللغة — من غير ما نجبر كل وريث حالي
        # على تنفيذه فورًا (لو محدش وفّرها، السلوك زي الأول تمامًا).
        self._init_widget_mixin(theme=True, font=False, lang=True)
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

    def _tab_label(self, index: int) -> "str | None":
        """
        Hook اختياري — Override هنا في الوريث لو عايز عنوان التاب رقم
        `index` يتحدث تلقائيًا عند تغيير اللغة لايف. يرجع النص الجديد
        (مبني بـ tr() الحالية) أو None لو مفيش تحديث لازم لهذا الـ index.

        مثال في RawTab:
            def _tab_label(self, index):
                return {
                    0: f"{tr('tab_icon_raw')}  {tr('raw_tab')}",
                    1: f"{tr('categories_tab_icon')}  {tr('categories_tab')}",
                }.get(index)

        لو الوريث ملوش override، _refresh_lang() ماتعملش حاجة —
        نفس السلوك القديم بالظبط (لا كسر لأي كود موجود).
        """
        return None

    def _refresh_lang(self, *_):
        """
        [إصلاح lang] عامة لكل الورثة — بتنادي _tab_label() الاختيارية
        لكل تاب وتحدث النص لو الوريث وفّرها، وتعيد حساب عرض التابات
        بعد كده لأن النص العربي/الإنجليزي مش نفس الطول.
        """
        if not self._tabs:
            return
        updated = False
        for i in range(self._tabs.count()):
            label = self._tab_label(i)
            if label is not None:
                self._tabs.setTabText(i, label)
                updated = True
        if updated:
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