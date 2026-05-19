"""
ui/widgets/shared/panles_helper/action_toolbar.py
==================================================
ActionToolbar — بـ FlowLayout.

الأزرار بتنزل لسطر تاني تلقائياً لما المساحة تضيق —
بدل ما تتقطع أو تتخفى.

  - add_action() → أزرار عادية (على اليسار/في الترتيب)
  - add_danger()  → أزرار خطرة (حمراء) — في الآخر مع separator
  - add_separator() → فاصل بصري اختياري
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
        self._has_danger  = False
        self._normal_btns : list[QPushButton] = []
        self._danger_btns : list[QPushButton] = []
        self._sep_widget  = None
        self._build()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        # FlowLayout مباشرة على الـ widget
        self._flow = FlowLayout(self, h_spacing=self._spacing, v_spacing=4)
        self._flow.setContentsMargins(0, 4, 0, 4)
        self.setLayout(self._flow)

    # ── إضافة أزرار عادية ──────────────────────────────

    def add_action(self, text: str, style: str = "normal",
                   callback=None, enabled: bool = True) -> QPushButton:
        btn = _make_btn(text, style)
        btn.setEnabled(enabled)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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
        if callback:
            btn.clicked.connect(callback)
        self._danger_btns.append(btn)
        self._has_danger = True
        self._rebuild()
        return btn

    def add_separator(self):
        """فاصل إضافي بين مجموعات الأزرار العادية."""
        sep = self._make_sep()
        self._normal_btns.append(sep)
        self._rebuild()

    # ── بناء داخلي ─────────────────────────────────────

    def _rebuild(self):
        """يعيد بناء الـ flow بالترتيب الصحيح دايماً."""
        # امسح كل العناصر الحالية
        while self._flow.count():
            item = self._flow.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        # أزرار عادية
        for w in self._normal_btns:
            w.setParent(self)
            self._flow.addWidget(w)

        # separator + أزرار خطرة
        if self._danger_btns and self._normal_btns:
            sep = self._make_sep()
            self._flow.addWidget(sep)

        for w in self._danger_btns:
            w.setParent(self)
            self._flow.addWidget(w)

        self.updateGeometry()

    def _make_sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedSize(1, 28)
        sep.setStyleSheet(
            f"background:{_C['border_med']}; border:none; margin:2px 2px;"
        )
        return sep