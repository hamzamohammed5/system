"""
ui/widgets/panels/form_group.py
"""
from PyQt5.QtWidgets import QGroupBox, QFormLayout, QFrame, QWidget
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import SEPARATOR_LINE_H


class FormGroup(QGroupBox, WidgetMixin):

    def __init__(self, title: str = "", accent: str = None, parent=None):
        super().__init__(title, parent)
        self._custom_accent = accent
        from ui.constants import FORM_LAYOUT_SPACING, FORM_GROUP_FORM_MARGIN
        self.form = QFormLayout(self)
        self.form.setSpacing(FORM_LAYOUT_SPACING)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setContentsMargins(*FORM_GROUP_FORM_MARGIN)
        self.form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.constants import (
            FORM_GROUP_BORDER_RADIUS, FORM_GROUP_MARGIN_TOP,
            FORM_GROUP_PADDING_TOP, FORM_GROUP_TITLE_PAD_H,
        )
        base  = get_font_size()
        color = self._custom_accent or _C['accent']
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 700;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_sec']};
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: {FORM_GROUP_BORDER_RADIUS}px;
                margin-top: {FORM_GROUP_MARGIN_TOP}px;
                padding-top: {FORM_GROUP_PADDING_TOP}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 {FORM_GROUP_TITLE_PAD_H}px;
                color: {color};
            }}
        """)

    def add_row(self, label: str, widget: QWidget):
        self.form.addRow(label, widget)

    def add_label_row(self, label_widget: QWidget):
        self.form.addRow(label_widget)

    def add_separator(self):
        sep = _ThemedSeparator()
        self.form.addRow(sep)


class _ThemedSeparator(QFrame, WidgetMixin):
    """فاصل يتابع الثيم — بدل بناء stylesheet ثابت في add_separator."""

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(SEPARATOR_LINE_H)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(f"background:{_C['border']}; border:none;")