"""
ui/widgets/shared/panles_helper/action_toolbar.py
==================================================
ActionToolbar — بـ FlowLayout.

الإصلاحات:
  - FIX 5: _rebuild كانت بتمسح items من الـ layout فقط
    لكن الـ QFrame separators اللي اتضافوا عبر add_separator()
    كانوا بيفضلوا في self._normal_btns بدون حذف → leak تدريجي.
    الحل: نفصل الـ separators في list منفصلة _inline_seps
    ونعمل deleteLater() عليهم في _rebuild.

  - الإصلاح القديم: _rebuild مكانش بيعمل setParent(None) صح على الـ widgets
    اللي لسه موجودين في الـ lists — ده كان بيعمل access violation.
    الحل: نمسح الـ layout items بس من غير ما نعمل setParent أو deleteLater
    على الـ widgets اللي هنضيفهم تاني.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.app_settings import _C
from .make_btn import _make_btn
from ui.widgets.shared.flow_layout import FlowLayout


class ActionToolbar(QWidget):
    def __init__(self, spacing: int = 6, parent=None):
        super().__init__(parent)
        self._spacing       = spacing
        self._normal_btns   : list[QPushButton] = []
        self._danger_btns   : list[QPushButton] = []
        # FIX 5: separators من الـ الوسطى (بين normal/danger groups)
        self._group_seps    : list[QFrame]      = []
        # FIX 5: separators اللي أضافها المستخدم عبر add_separator()
        #         محتاجين deleteLater() في كل rebuild
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

        FIX 5: الـ separator ده بيتحذف في كل _rebuild() ويتعاد إنشاؤه
        عشان نتجنب الـ leak الناتج عن تراكمهم في _normal_btns.
        """
        # نحتفظ بـ marker خاص بدل QFrame عشان نعرف مكانه
        self._normal_btns.append(_SeparatorMarker())
        self._rebuild()

    # ── بناء داخلي ─────────────────────────────────────

    def _rebuild(self):
        # امسح كل items من الـ layout (بدون deleteLater على الـ real widgets)
        while self._flow.count():
            self._flow.takeAt(0)

        # FIX 5: احذف الـ separators القديمة (group + inline)
        for sep in self._group_seps + self._inline_seps:
            sep.deleteLater()
        self._group_seps.clear()
        self._inline_seps.clear()

        # أضف normal_btns مع إنشاء inline separators جديدة
        for item in self._normal_btns:
            if isinstance(item, _SeparatorMarker):
                sep = self._make_sep()
                sep.setParent(self)
                self._inline_seps.append(sep)
                self._flow.addWidget(sep)
                sep.show()
            else:
                self._flow.addWidget(item)
                item.show()

        # فاصل بين normal و danger
        if self._normal_btns and self._danger_btns:
            sep = self._make_sep()
            sep.setParent(self)
            self._group_seps.append(sep)
            self._flow.addWidget(sep)
            sep.show()

        for w in self._danger_btns:
            self._flow.addWidget(w)
            w.show()

        self.updateGeometry()

    def _make_sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedSize(1, 28)
        sep.setStyleSheet(
            f"background:{_C['border_med']}; border:none; margin:2px 2px;"
        )
        return sep


class _SeparatorMarker:
    """
    Marker بسيط يُستخدم داخلياً في _normal_btns
    للإشارة إلى مكان separator مرئي.
    لا يرث من QWidget عشان ما نحتاجش deleteLater.
    """
    pass