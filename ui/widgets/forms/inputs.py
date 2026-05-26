"""
ui/widgets/forms/inputs.py
===========================
Input widgets الموحدة للتطبيق.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QLabel,
    QDoubleSpinBox, QSpinBox, QDateEdit, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from ..core          import get_base


# ── Shared style builders ──────────────────────────────────

def _input_style(height: int = 32, error: bool = False) -> str:
    base   = get_base()
    bg     = "#fef2f2" if error else _C["bg_input"]
    border = "#f87171" if error else _C["border_med"]
    return f"""
        background:{bg}; border:1.5px solid {border};
        border-radius:6px; padding:0 8px;
        font-size:{fs(base,0)}pt; color:{_C["text_primary"]};
        min-height:{height}px;
    """


def _spinbox_style(height: int = 32, positive: bool = False,
                   widget: str = "QDoubleSpinBox") -> str:
    base = get_base()
    if positive:
        bg, border, color, weight = "#f0fdf4", "#86efac", "#15803d", "bold"
    else:
        bg     = _C["bg_input"]
        border = _C["border_med"]
        color  = _C["text_primary"]
        weight = "normal"
    return f"""
        {widget} {{
            background:{bg}; border:1.5px solid {border};
            border-radius:6px; padding:0 8px;
            font-size:{fs(base,0)}pt; color:{color};
            font-weight:{weight}; min-height:{height}px;
        }}
        {widget}:focus {{ border-color:{_C["accent"]}; background:white; }}
        {widget}:disabled {{
            background:{_C["bg_surface_2"]}; color:{_C["text_disabled"]};
        }}
    """


# ── SearchLineEdit ─────────────────────────────────────────

class SearchLineEdit(QWidget):
    """حقل بحث موحد مع delay."""
    text_changed = pyqtSignal(str)

    def __init__(self, placeholder: str = "🔍  بحث...",
                 delay_ms: int = 250, height: int = 34, parent=None):
        super().__init__(parent)
        self._delay = delay_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._emit)
        self._build(placeholder, height)

    def _build(self, placeholder, height):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._inp = QLineEdit()
        self._inp.setPlaceholderText(placeholder)
        self._inp.setFixedHeight(height)
        self._inp.setClearButtonEnabled(True)
        self._inp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._inp.setStyleSheet(f"QLineEdit {{ {_input_style(height)} }}")
        self._inp.textChanged.connect(lambda: self._timer.start() if self._delay else self._emit())
        lay.addWidget(self._inp)

    def _emit(self):
        self.text_changed.emit(self._inp.text().strip().lower())

    def text(self) -> str:
        return self._inp.text().strip().lower()

    def clear(self):
        self._inp.clear()

    @property
    def line_edit(self) -> QLineEdit:
        return self._inp


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

        base = get_base()
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
        base = get_base()
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