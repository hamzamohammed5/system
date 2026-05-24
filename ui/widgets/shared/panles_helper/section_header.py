"""
ui/widgets/shared/panles_helper/section_header.py

[إصلاح v2]:
  - accent bar بيستخدم _C['accent'] بدل hardcoded style مكرر
  - add_button يُرجع QPushButton للتوافق مع الكود القديم
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from ui.app_settings import _C, fs
from .make_btn import _make_btn
from .colors_and_base import _base


class SectionHeader(QWidget):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._build(title)

    def _build(self, title):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(10)

        # Accent bar — لون من theme مباشرة
        accent_bar = QLabel()
        accent_bar.setFixedSize(3, 18)
        accent_bar.setStyleSheet(
            f"background:{_C['accent']}; border-radius:2px; border:none;"
        )
        lay.addWidget(accent_bar)

        base = _base()
        self._lbl = QLabel(title)
        self._lbl.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,+1)}pt;"
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl)
        lay.addStretch()
        self._btn_layout = lay

    def set_title(self, title: str):
        self._lbl.setText(title)

    def add_button(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        btn = _make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        self._btn_layout.addWidget(btn)
        return btn