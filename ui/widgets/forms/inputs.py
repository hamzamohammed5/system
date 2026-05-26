"""
ui/widgets/forms/inputs.py
===========================
Input widgets الموحدة للتطبيق.

_input_style / _spinbox_style مستوردتان من theme/styles — لا تكرار.

ملاحظة: للبحث استخدم SearchBar من components/headers مباشرة.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QLabel,
    QDoubleSpinBox, QSpinBox, QDateEdit, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from ..core          import get_font_size
from ..theme.styles  import input_style as _input_style, spinbox_style as _spinbox_style


# ── AmountSpinBox ─────────────────────────────────────────

class AmountSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox للمبالغ المالية."""

    def __init__(self, max_: float = 999_999_999, dec: int = 2,
                 min_: float = 0, height: int = 32,
                 currency: str = "", parent=None):
        super().__init__(parent)
        self.setRange(min_, max_)
        self.setDecimals(dec)
        self.setMinimumHeight(height)
        self._h = height
        if currency:
            self.setSuffix(f"  {currency}")
        self.setStyleSheet(_spinbox_style(height))
        self.valueChanged.connect(lambda v: self.setStyleSheet(
            _spinbox_style(self._h, positive=v > 0)
        ))


# ── DateField ─────────────────────────────────────────────

class DateField(QDateEdit):
    """QDateEdit موحد."""

    def __init__(self, date: QDate = None, height: int = 32,
                 width: int = None, parent=None):
        super().__init__(date or QDate.currentDate(), parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setMinimumHeight(height)
        if width:
            self.setFixedWidth(width)
        self.setStyleSheet(
            f"QDateEdit {{ {_input_style(height)} }}"
            "QDateEdit::drop-down { border:none; width:24px; }"
        )

    def date_str(self) -> str:
        return self.date().toString("yyyy-MM-dd")

    def set_date_str(self, s: str):
        if s:
            d = QDate.fromString(s, "yyyy-MM-dd")
            if d.isValid():
                self.setDate(d)


# ── StyledComboBox ────────────────────────────────────────

class StyledComboBox(QComboBox):
    """QComboBox بستايل موحد."""

    def __init__(self, height: int = 32, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(height)
        self.setStyleSheet(
            f"QComboBox {{ {_input_style(height)} }}"
            "QComboBox::drop-down { border:none; width:24px; }"
            f"QComboBox:disabled {{ background:{_C['bg_surface_2']};"
            f" color:{_C['text_disabled']}; }}"
        )


# ── LabeledInput ──────────────────────────────────────────

class LabeledInput(QWidget):
    """حقل مع label أفقي."""

    def __init__(self, label: str, widget: QWidget, unit: str = "",
                 spacing: int = 8, label_width: int = None, parent=None):
        super().__init__(parent)
        self._widget = widget
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(spacing)

        base = get_font_size()
        lbl  = QLabel(label)
        lbl.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,0)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if label_width:
            lbl.setFixedWidth(label_width)

        lay.addWidget(lbl)
        lay.addWidget(widget, stretch=1)

        if unit:
            u = QLabel(unit)
            u.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            lay.addWidget(u)

    @property
    def widget(self) -> QWidget:
        return self._widget


# ── RequiredLineEdit ──────────────────────────────────────

class RequiredLineEdit(QLineEdit):
    """QLineEdit مع تحقق بصري من الفراغ."""

    def __init__(self, placeholder: str = "", height: int = 32, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        self._h     = height
        self._error = False
        self._refresh()
        self.textChanged.connect(self._on_change)

    def _refresh(self):
        self.setStyleSheet(f"QLineEdit {{ {_input_style(self._h, self._error)} }}")

    def _on_change(self):
        if self._error and self.text().strip():
            self._error = False
            self._refresh()

    def validate(self) -> bool:
        if not self.text().strip():
            self._error = True
            self._refresh()
            self.setFocus()
            return False
        return True

    def text_stripped(self) -> str:
        return self.text().strip()

    def clear_error(self):
        self._error = False
        self._refresh()


# ── NotesLineEdit ─────────────────────────────────────────

class NotesLineEdit(QLineEdit):
    """حقل ملاحظات بستايل مخصص."""

    def __init__(self, placeholder: str = "ملاحظات اختيارية...",
                 height: int = 30, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        base = get_font_size()
        self.setStyleSheet(f"""
            QLineEdit {{
                background:#fafafa; border:1px solid {_C['border']};
                border-radius:6px; padding:0 8px;
                font-size:{fs(base,-1)}pt; color:{_C['text_sec']};
                font-style:italic; min-height:{height}px;
            }}
            QLineEdit:focus {{
                border-color:{_C['border_med']}; background:white;
                font-style:normal; color:{_C['text_primary']};
            }}
        """)