"""
ui/widgets/panels/form_group.py
=================================
FormGroup — QGroupBox مع QFormLayout جاهز وستايل موحد.

مستخرج من panels/form_parts.py.
"""

from PyQt5.QtWidgets import QGroupBox, QFormLayout, QFrame, QWidget
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs


class FormGroup(QGroupBox):
    """QGroupBox مع QFormLayout جاهز وستايل موحد."""

    def __init__(self, title: str = "", accent: str = None, parent=None):
        super().__init__(title, parent)
        self._accent = accent or _C["accent"]
        self._apply_style()
        self.form = QFormLayout(self)
        self.form.setSpacing(10)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setContentsMargins(12, 14, 12, 12)

    def _apply_style(self):
        base = get_font_size()
        color = self._accent
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight:700; font-size:{fs(base,0)}pt;
                color:{_C['text_sec']}; background:{_C['bg_surface']};
                border:1px solid {_C['border']}; border-radius:10px;
                margin-top:10px; padding-top:6px;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; subcontrol-position:top right;
                padding:0 8px; color:{color};
            }}
        """)

    def add_row(self, label: str, widget: QWidget):
        self.form.addRow(label, widget)

    def add_label_row(self, label_widget: QWidget):
        self.form.addRow(label_widget)

    def add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        self.form.addRow(sep)