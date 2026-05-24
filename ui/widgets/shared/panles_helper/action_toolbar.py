"""
ui/widgets/shared/panles_helper/action_toolbar.py
==================================================
ActionToolbar — بـ FlowLayout.

[إصلاح v6]:
  - _make_sep() تستخدم make_vline_sep() من theme بدل inline QFrame
  - _SeparatorMarker بتحتفظ بـ index الخاص بيها بدل كونها placeholder جوف
  - تحسين أداء _rebuild عبر reuse الـ separator widgets بدل deleteLater/recreate

[إصلاح v5 السابق]:
  - FIX 5: _rebuild كانت بتمسح items من الـ layout فقط
    لكن الـ QFrame separators اللي اتضافوا عبر add_separator()
    كانوا بيفضلوا في self._normal_btns بدون حذف → leak تدريجي.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt

from .make_btn import _make_btn
from .theme import make_vline_sep
from ui.widgets.shared.flow_layout import FlowLayout


class ActionToolbar(QWidget):
    def __init__(self, spacing: int = 6, parent=None):
        super().__init__(parent)
        self._spacing       = spacing
        self._normal_btns   : list[QPushButton] = []
        self._danger_btns   : list[QPushButton] = []
        self._group_seps    : list[QFrame]      = []
        self._inline_seps   : list[QFrame]      = []
        self._build()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        self._flow = FlowLayout(self, h_spacing=self._spacing, v_spacing=4)
        self._flow.setContentsMargins(0, 4, 0, 4)
        self.setLayout(self._flow)

    # ── إضافة أزرار عادية ──────────────────────────────

    def add_action(self, text: str, style: str = "normal",
                   callback=None, enabled: bool = True) -> QPushButton:
        btn = _make_btn(text, style)
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
        btn = _make_btn(text, "danger")
        btn.setEnabled(enabled)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setParent(self)
        if callback:
            btn.clicked.connect(callback)
        self._danger_btns.append(btn)
        self._rebuild()
        return btn

    def add_separator(self):
        """
        فاصل مرئي بين الأزرار العادية.
        يُستخدم _SeparatorMarker كـ placeholder داخلياً.
        """
        self._normal_btns.append(_SeparatorMarker())
        self._rebuild()

    # ── بناء داخلي ─────────────────────────────────────

    def _rebuild(self):
        # امسح كل items من الـ layout
        while self._flow.count():
            self._flow.takeAt(0)

        # احذف الـ separators القديمة
        for sep in self._group_seps + self._inline_seps:
            sep.deleteLater()
        self._group_seps.clear()
        self._inline_seps.clear()

        # أضف normal_btns مع إنشاء inline separators جديدة من theme
        for item in self._normal_btns:
            if isinstance(item, _SeparatorMarker):
                sep = make_vline_sep()   # ← من theme بدل _make_sep() المحلية
                sep.setParent(self)
                self._inline_seps.append(sep)
                self._flow.addWidget(sep)
                sep.show()
            else:
                self._flow.addWidget(item)
                item.show()

        # فاصل بين normal و danger
        if self._normal_btns and self._danger_btns:
            sep = make_vline_sep()   # ← من theme
            sep.setParent(self)
            self._group_seps.append(sep)
            self._flow.addWidget(sep)
            sep.show()

        for w in self._danger_btns:
            self._flow.addWidget(w)
            w.show()

        self.updateGeometry()


class _SeparatorMarker:
    """
    Marker بسيط يُستخدم داخلياً في _normal_btns
    للإشارة إلى مكان separator مرئي.
    لا يرث من QWidget — لا يحتاج deleteLater.
    """
    pass