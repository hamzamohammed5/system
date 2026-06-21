"""
ui/widgets/panels/form_fields.py
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFormLayout,
    QDoubleSpinBox, QSpinBox, QVBoxLayout,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ..theme.input_styles import spinbox_style
from .form_labels import form_label, required_label, hint_label
from ui.widgets.core.widget_mixin import WidgetMixin


# ── spin_field ────────────────────────────────────────────

class _ThemedDoubleSpinBox(QDoubleSpinBox, WidgetMixin):
    def __init__(self, min_height: int = 30):
        super().__init__()
        self._h = min_height
        self._init_widget_mixin(font=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(spinbox_style(self._h, widget="QDoubleSpinBox"))


class _ThemedSpinBox(QSpinBox, WidgetMixin):
    def __init__(self, min_height: int = 30):
        super().__init__()
        self._h = min_height
        self._init_widget_mixin(font=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(spinbox_style(self._h, widget="QSpinBox"))


def spin_field(max_: float = 999999, dec: int = 2,
               min_: float = 0, min_height: int = 30) -> QDoubleSpinBox:
    s = _ThemedDoubleSpinBox(min_height)
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(min_height)
    return s


def int_spin_field(max_: int = 9999, min_: int = 0,
                   min_height: int = 30) -> QSpinBox:
    s = _ThemedSpinBox(min_height)
    s.setRange(min_, max_)
    s.setMinimumHeight(min_height)
    return s


# ── labeled_widget ────────────────────────────────────────

class _LabeledWidgetContainer(QWidget, WidgetMixin):
    def __init__(self, widget: QWidget, unit: str,
                 unit_color: str = None, spacing: int = 6):
        super().__init__()
        self._unit_color = unit_color
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(spacing)
        lay.addWidget(widget)
        self._lbl = QLabel(unit)
        lay.addWidget(self._lbl)
        lay.addStretch()
        self._init_widget_mixin(font=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        color = self._unit_color or _C['text_muted']
        self._lbl.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
            f"font-size:{fs(get_font_size(), -1)}pt;"
        )


def labeled_widget(widget: QWidget, unit: str,
                   unit_color: str = None, spacing: int = 6) -> QWidget:
    return _LabeledWidgetContainer(widget, unit, unit_color, spacing)


# ── field_row / labeled_row / make_form_layout ────────────
# (دوال تبني widgets مؤقتة — لا stylesheet محلي ثابت، تعتمد على الـ children)

def field_row(label_text: str, widget: QWidget,
              required: bool = False, hint: str = "") -> tuple:
    lbl = required_label(label_text) if required else form_label(label_text)
    if hint:
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(widget)
        lay.addWidget(hint_label(hint))
        return lbl, container
    return lbl, widget


def labeled_row(label_text: str, *widgets, spacing: int = 6) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    lay.addWidget(form_label(label_text))
    for widget in widgets:
        if widget is None:
            continue
        if isinstance(widget, str):
            lay.addWidget(hint_label(widget))
        else:
            lay.addWidget(widget)
    lay.addStretch()
    return w


def make_form_layout(spacing: int = 10,
                     label_align: int = Qt.AlignRight | Qt.AlignVCenter,
                     contents_margins: tuple = (12, 10, 12, 10)) -> QFormLayout:
    form = QFormLayout()
    form.setSpacing(spacing)
    form.setLabelAlignment(label_align)
    form.setContentsMargins(*contents_margins)
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
    return form