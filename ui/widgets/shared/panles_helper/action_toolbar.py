"""
ui/widgets/shared/panles_helper/action_toolbar.py
==================================================
ActionToolbar — أزرار بحجم ثابت، مش بتتمدد ومش بتتضغط.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout,
    QPushButton, QSizePolicy,
)

from ui.app_settings import _C
from .make_btn import _make_btn


class ActionToolbar(QWidget):
    def __init__(self, spacing: int = 6, parent=None):
        super().__init__(parent)
        self._spacing    = spacing
        self._has_danger = False
        self._buttons    = []   # لتتبع الأزرار وحساب min width
        self._build()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        # ✅ لا يتضغط أفقياً — يحتفظ بحجمه الكامل
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(self._spacing)

        self._left_lay = QHBoxLayout()
        self._left_lay.setSpacing(self._spacing)

        self._right_lay = QHBoxLayout()
        self._right_lay.setSpacing(self._spacing)

        lay.addLayout(self._left_lay)
        lay.addStretch()

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.VLine)
        self._sep.setFixedWidth(1)
        self._sep.setStyleSheet(
            f"background:{_C['border_med']}; border:none; margin:4px 0;"
        )
        self._sep.setVisible(False)
        lay.addWidget(self._sep)

        lay.addLayout(self._right_lay)

    def _update_min_width(self):
        """يحسب الحد الأدنى للعرض بناءً على مجموع أعراض الأزرار."""
        total = sum(btn.minimumWidth() for btn in self._buttons)
        total += self._spacing * max(0, len(self._buttons) - 1)
        total += 8  # padding
        self.setMinimumWidth(total)

    def add_action(self, text: str, style: str = "normal",
                   callback=None, enabled: bool = True) -> QPushButton:
        btn = _make_btn(text, style)
        btn.setEnabled(enabled)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if callback:
            btn.clicked.connect(callback)
        self._left_lay.addWidget(btn)
        self._buttons.append(btn)
        self._update_min_width()
        return btn

    def add_danger(self, text: str, callback=None,
                   enabled: bool = True) -> QPushButton:
        btn = _make_btn(text, "danger")
        btn.setEnabled(enabled)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if callback:
            btn.clicked.connect(callback)
        self._right_lay.addWidget(btn)
        self._sep.setVisible(True)
        self._has_danger = True
        self._buttons.append(btn)
        self._update_min_width()
        return btn

    def add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none; margin:4px 0;")
        self._left_lay.addWidget(sep)