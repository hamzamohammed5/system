"""
ui/widgets/shared/panles_helper/action_toolbar.py
==================================================
ActionToolbar — بـ FlowLayout.

الإصلاح: _rebuild مكانش بيعمل setParent(None) صح على الـ widgets
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
        self._spacing     = spacing
        self._normal_btns : list[QPushButton] = []
        self._danger_btns : list[QPushButton] = []
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
        """فاصل إضافي بين مجموعات الأزرار العادية."""
        sep = self._make_sep()
        sep.setParent(self)
        self._normal_btns.append(sep)
        self._rebuild()

    # ── بناء داخلي ─────────────────────────────────────

    def _rebuild(self):
        """
        يعيد ترتيب الـ flow بالكامل.
        
        المهم: بنمسح الـ items من الـ layout بس —
        مش بنعمل setParent(None) أو deleteLater على الـ widgets
        اللي هنضيفهم تاني، لأن ده بيعمل access violation.
        """
        # امسح كل الـ items من الـ layout بدون تدمير الـ widgets
        while self._flow.count():
            item = self._flow.takeAt(0)
            # لا نعمل حاجة بالـ item أو الـ widget — بس نشيله من الـ layout

        # أضف الأزرار العادية
        for w in self._normal_btns:
            self._flow.addWidget(w)
            w.show()

        # separator + أزرار خطرة
        if self._normal_btns and self._danger_btns:
            sep = self._make_sep()
            sep.setParent(self)
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