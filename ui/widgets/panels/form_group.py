"""
ui/widgets/panels/form_group.py
"""
import weakref

from PyQt5.QtWidgets import QGroupBox, QFormLayout, QFrame, QWidget
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ui.widgets.core.events import bus


def _connect_theme_refresh(widget, slot) -> None:
    _weak = weakref.ref(widget)

    def _on_theme_changed(_theme_name=None):
        obj = _weak()
        if obj is not None:
            slot(obj)

    widget._theme_refresh_slot = _on_theme_changed
    bus.theme_changed.connect(widget._theme_refresh_slot, Qt.UniqueConnection)


class FormGroup(QGroupBox):

    def __init__(self, title: str = "", accent: str = None, parent=None):
        super().__init__(title, parent)
        # None = يقرأ من _C في كل refresh بدل تجميده وقت الإنشاء
        self._custom_accent = accent
        self.form = QFormLayout(self)
        self.form.setSpacing(10)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setContentsMargins(12, 14, 12, 12)
        self.form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self._apply_style()
        _connect_theme_refresh(self, FormGroup._apply_style)

    def _apply_style(self, *_):
        base  = get_font_size()
        color = self._custom_accent or _C['accent']
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 700;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_sec']};
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
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


class _ThemedSeparator(QFrame):
    """فاصل يتابع الثيم — بدل بناء stylesheet ثابت في add_separator."""

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self._refresh_style()
        _connect_theme_refresh(self, _ThemedSeparator._refresh_style)

    def _refresh_style(self, *_):
        self.setStyleSheet(f"background:{_C['border']}; border:none;")