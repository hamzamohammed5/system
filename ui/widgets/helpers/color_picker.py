"""
widgets/helpers/color_picker.py
================================
ColorPickerWidget — widget موحد لاختيار اللون.

لا تغييرات جوهرية — تنظيف imports فقط.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QColorDialog
from PyQt5.QtCore    import pyqtSignal
from PyQt5.QtGui     import QColor

from ..components.button import make_btn
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.constants import SPACING_SM, COLOR_PICKER_PREVIEW_SIZE, COLOR_PICKER_PREVIEW_RADIUS


class ColorPickerWidget(QWidget, WidgetMixin):
    """
    Widget مدمج: [■ مربع اللون] [اختر لون]

    Signals:
        color_changed(str) — يُطلق عند تغيير اللون (hex)
    """

    color_changed = pyqtSignal(str)

    def __init__(self, default: str = "",
                 btn_text: str = "",
                 parent=None):
        super().__init__(parent)
        self._color = default
        self._btn_text = btn_text
        self._build()
        self._init_widget_mixin(theme=True, font=False, lang=True, data=False)
        self._refresh_style()
        self._refresh_lang()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(SPACING_SM)

        self._preview = QLabel()
        self._preview.setFixedSize(COLOR_PICKER_PREVIEW_SIZE, COLOR_PICKER_PREVIEW_SIZE)
        self._apply_preview()
        lay.addWidget(self._preview)

        self._btn = make_btn("", "normal")
        self._btn.clicked.connect(self._pick)
        lay.addWidget(self._btn)
        lay.addStretch()

    def _refresh_style(self, *_):
        self._apply_preview()

    def _refresh_lang(self, *_):
        label = self._btn_text if self._btn_text else tr("color_picker_btn")
        self._btn.setText(label)

    def _apply_preview(self):
        color = self._color if self._color else _C['color_picker_default']
        self._preview.setStyleSheet(
            f"background:{color}; border-radius:{COLOR_PICKER_PREVIEW_RADIUS}px;"
            f" border:1px solid {_C['border_light']};"
        )

    def _pick(self):
        color = self._color if self._color else _C['color_picker_default']
        col = QColorDialog.getColor(QColor(color), self, tr("color_picker_title"))
        if col.isValid():
            self._color = col.name()
            self._apply_preview()
            self.color_changed.emit(self._color)

    def current_color(self) -> str:
        return self._color

    def set_color(self, color: str):
        self._color = color
        self._apply_preview()
