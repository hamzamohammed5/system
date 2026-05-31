"""
ui/widgets/components/action_toolbar.py
===================================================
ActionToolbar — شريط أزرار بـ FlowLayout.
نسخة refactored من panles_helper/action_toolbar.py
"""
from PyQt5.QtWidgets import QWidget, QFrame, QPushButton, QSizePolicy

from .button            import make_btn
from ..theme.builders   import v_divider
from ..utils.flow_layout import FlowLayout


class ActionToolbar(QWidget):
    """
    شريط أزرار أفقي بـ FlowLayout — الأزرار تنزل لسطر تاني تلقائياً.

    الاستخدام:
        toolbar = ActionToolbar(spacing=8)
        btn = toolbar.add_action("✏️ تعديل", style="primary", callback=self._edit)
        toolbar.add_separator()
        toolbar.add_danger("🗑️ حذف", callback=self._delete)
    """

    def __init__(self, spacing: int = 6, parent=None):
        super().__init__(parent)
        self._spacing     = spacing
        self._normal_btns : list = []
        self._danger_btns : list[QPushButton] = []
        self._group_seps  : list[QFrame] = []
        self._inline_seps : list[QFrame] = []
        self._build()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        self._flow = FlowLayout(self, h_spacing=self._spacing, v_spacing=4)
        self._flow.setContentsMargins(0, 4, 0, 4)
        self.setLayout(self._flow)

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


class _SeparatorMarker:
    """Marker داخلي للإشارة لمكان الفاصل — لا يرث من QWidget."""
    pass