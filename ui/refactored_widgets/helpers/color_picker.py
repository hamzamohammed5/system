"""
widgets/helpers/color_picker.py
================================
ColorPickerWidget — widget موحد لاختيار اللون.

لا تغييرات جوهرية — تنظيف imports فقط.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QColorDialog
from PyQt5.QtCore    import pyqtSignal
from PyQt5.QtGui     import QColor

from ..panels._btn import make_btn


class ColorPickerWidget(QWidget):
    """
    Widget مدمج: [■ مربع اللون] [اختر لون]

    Signals:
        color_changed(str) — يُطلق عند تغيير اللون (hex)
    """

    color_changed = pyqtSignal(str)

    def __init__(self, default: str = "#607d8b",
                 btn_text: str = "اختر لون",
                 parent=None):
        super().__init__(parent)
        self._color = default
        self._build(btn_text)

    def _build(self, btn_text: str):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self._preview = QLabel()
        self._preview.setFixedSize(28, 28)
        self._apply_preview()
        lay.addWidget(self._preview)

        btn = make_btn(btn_text, "normal")
        btn.clicked.connect(self._pick)
        lay.addWidget(btn)
        lay.addStretch()

    def _apply_preview(self):
        self._preview.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )

    def _pick(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر لون")
        if col.isValid():
            self._color = col.name()
            self._apply_preview()
            self.color_changed.emit(self._color)

    def current_color(self) -> str:
        return self._color

    def set_color(self, color: str):
        self._color = color
        self._apply_preview()