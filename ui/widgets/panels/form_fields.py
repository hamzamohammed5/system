"""
ui/widgets/panels/form_fields.py
==================================
Field builders للفورمات.

مستخرج من panels/form_parts.py:
  spin_field, int_spin_field, labeled_widget,
  field_row, labeled_row, make_form_layout
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFormLayout,
    QDoubleSpinBox, QSpinBox,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ..theme.styles import spinbox_style

from .form_labels import form_label, required_label, hint_label


def spin_field(max_: float = 999999, dec: int = 2,
               min_: float = 0, min_height: int = 30) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(spinbox_style(min_height, widget="QDoubleSpinBox"))
    return s


def int_spin_field(max_: int = 9999, min_: int = 0,
                   min_height: int = 30) -> QSpinBox:
    s = QSpinBox()
    s.setRange(min_, max_)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(spinbox_style(min_height, widget="QSpinBox"))
    return s


def labeled_widget(widget: QWidget, unit: str,
                   unit_color: str = None, spacing: int = 6) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    lay.addWidget(widget)
    lbl = QLabel(unit)
    lbl.setStyleSheet(
        f"color:{unit_color or _C['text_muted']}; background:transparent; border:none;"
        f"font-size:{fs(get_font_size(),-1)}pt;"
    )
    lay.addWidget(lbl)
    lay.addStretch()
    return w


def field_row(label_text: str, widget: QWidget,
              required: bool = False, hint: str = "") -> tuple:
    from PyQt5.QtWidgets import QVBoxLayout
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