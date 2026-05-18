"""
ui/widgets/shared/panles_helper/action_toolbar.py
==================================================
ActionToolbar — أزرار بحجم ثابت، مش بتتمدد مع النافذة.
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
        self._spacing = spacing
        self._has_danger = False
        self._build()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(self._spacing)

        self._left_lay = QHBoxLayout()
        self._left_lay.setSpacing(self._spacing)

        self._right_lay = QHBoxLayout()
        self._right_lay.setSpacing(self._spacing)

        lay.addLayout(self._left_lay)
        lay.addStretch()   # الـ stretch هنا بس — مش في الأزرار

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.VLine)
        self._sep.setFixedWidth(1)
        self._sep.setStyleSheet(
            f"background:{_C['border_med']}; border:none; margin:4px 0;"
        )
        self._sep.setVisible(False)
        lay.addWidget(self._sep)

        lay.addLayout(self._right_lay)

    def add_action(self, text: str, style: str = "normal",
                   callback=None, enabled: bool = True) -> QPushButton:
        btn = _make_btn(text, style)
        btn.setEnabled(enabled)
        # حجم ثابت — مش Expanding
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if callback:
            btn.clicked.connect(callback)
        self._left_lay.addWidget(btn)
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
        return btn

    def add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none; margin:4px 0;")
        self._left_lay.addWidget(sep)