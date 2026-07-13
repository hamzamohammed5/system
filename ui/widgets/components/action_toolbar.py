"""
ui/widgets/components/action_toolbar.py
===================================================
ActionToolbar — شريط أزرار بـ FlowLayout.
نسخة refactored من panles_helper/action_toolbar.py
"""
from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy

from ui.widgets.panels.themed_inputs import ThemedFrame
from ui.widgets.core.widget_mixin import WidgetMixin

from .button            import make_btn
from ..theme.builders   import v_divider
from ..utils.flow_layout import FlowLayout
from ui.constants import SPACING_XS, ACTION_TOOLBAR_FLOW_V_SPACING, ACTION_TOOLBAR_MARGIN_V, ACTION_TOOLBAR_DEFAULT_SPACING


class ActionToolbar(QWidget, WidgetMixin):
    """
    شريط أزرار أفقي بـ FlowLayout — الأزرار تنزل لسطر تاني تلقائياً.

    [إصلاح ثيم] الكلاس كان QWidget عادي من غير WidgetMixin — يعني مالوش
    أي اشتراك في bus.theme_changed خالص. الخلفية "transparent" كانت
    بتتحط مرة واحدة بس وقت _build() وتفضل كده، وده سليم من ناحية اللون
    نفسه، لكن الأزرار المضافة عبر add_action()/add_danger() (make_btn)
    كانت بتتبني *قبل* ما يبقى ليها parent فعلي جوه ActionToolbar، وكان
    مفيش أي نداء refresh_visible_buttons() يضمن تحديثها بعد تغيير الثيم —
    فكانت تفضل بستايل الثيم اللي كانت موجودة فيه وقت add_action().

    الحل: نضيف WidgetMixin زي كل باقي widgets المشروع، مع _refresh_style()
    بتعيد ضبط الخلفية الشفافة وتنادي refresh_visible_buttons() على كل
    الأزرار الموجودة فعليًا جوه الـ toolbar.

    الاستخدام:
        toolbar = ActionToolbar(spacing=8)
        btn = toolbar.add_action("✏️ تعديل", style="primary", callback=self._edit)
        toolbar.add_separator()
        toolbar.add_danger("🗑️ حذف", callback=self._delete)
    """

    def __init__(self, spacing: int = ACTION_TOOLBAR_DEFAULT_SPACING, parent=None):
        super().__init__(parent)
        self._spacing     = spacing
        self._normal_btns : list = []
        self._danger_btns : list[QPushButton] = []
        self._group_seps  : list[ThemedFrame] = []
        self._inline_seps : list[ThemedFrame] = []
        self._build()
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        self._flow = FlowLayout(self, h_spacing=self._spacing, v_spacing=ACTION_TOOLBAR_FLOW_V_SPACING)
        self._flow.setContentsMargins(0, ACTION_TOOLBAR_MARGIN_V, 0, ACTION_TOOLBAR_MARGIN_V)
        self.setLayout(self._flow)

    def _refresh_style(self, *_):
        self.setStyleSheet("background:transparent;")
        from .button import refresh_visible_buttons
        refresh_visible_buttons(self)

    # ── إضافة أزرار ───────────────────────────────────────

    def add_action(self, text: str, style: str = "normal",
                   callback=None, enabled: bool = True) -> QPushButton:
        btn = make_btn(text, style)
        btn.setEnabled(enabled)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setParent(self)
        if callback:
            btn.clicked.connect(callback)
        self._normal_btns.append(btn)
        self._rebuild()
        return btn

    def add_danger(self, text: str, callback=None,
                   enabled: bool = True) -> QPushButton:
        btn = make_btn(text, "danger")
        btn.setEnabled(enabled)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setParent(self)
        if callback:
            btn.clicked.connect(callback)
        self._danger_btns.append(btn)
        self._rebuild()
        return btn

    def add_separator(self):
        """فاصل مرئي بين الأزرار العادية."""
        self._normal_btns.append(_SeparatorMarker())
        self._rebuild()

    # ── بناء داخلي ────────────────────────────────────────

    def _rebuild(self):
        while self._flow.count():
            self._flow.takeAt(0)

        for sep in self._group_seps + self._inline_seps:
            sep.deleteLater()
        self._group_seps.clear()
        self._inline_seps.clear()

        for item in self._normal_btns:
            if isinstance(item, _SeparatorMarker):
                sep = v_divider()
                sep.setParent(self)
                self._inline_seps.append(sep)
                self._flow.addWidget(sep)
                sep.show()
            else:
                self._flow.addWidget(item)
                item.show()

        if self._normal_btns and self._danger_btns:
            sep = v_divider()
            sep.setParent(self)
            self._group_seps.append(sep)
            self._flow.addWidget(sep)
            sep.show()

        for w in self._danger_btns:
            self._flow.addWidget(w)
            w.show()

        self.updateGeometry()
        # [إصلاح ثيم] لو تم استدعاء add_action بعد تغيير الثيم مباشرة
        # (مثلاً toolbar اتبنت lazy عبر DetailHeader._ensure_toolbar بعد
        # أول theme_changed)، الأزرار الجديدة كانت بتاخد ستايل make_btn()
        # وقت الإنشاء بس. هنا بنضمن كل الأزرار المرئية فعليًا متسقة مع
        # الثيم الحالي فورًا.
        from .button import refresh_visible_buttons
        refresh_visible_buttons(self)


class _SeparatorMarker:
    """Marker داخلي للإشارة لمكان الفاصل — لا يرث من QWidget."""
    pass