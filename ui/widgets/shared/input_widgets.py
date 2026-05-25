"""
ui/widgets/shared/input_widgets.py

التغييرات:
  - _input_style() دالة مشتركة للـ stylesheet الأساسي بدل تكراره في كل كلاس
  - _spinbox_style() مشتركة بين AmountSpinBox و spin_field في form_utils
  - StyledComboBox و DateField يستخدمان _input_style مباشرة
  - NotesLineEdit stylesheet مبسط (كان يعيد كتابة نفس pattern)
  - RequiredLineEdit: _apply_style بتستخدم _input_style بدل hardcoded ألوان
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout,
    QLineEdit, QLabel, QPushButton,
    QDoubleSpinBox, QSpinBox, QDateEdit,
    QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base


# ══════════════════════════════════════════════════════════
# Shared style builders — مصدر واحد بدل تكرار في كل كلاس
# ══════════════════════════════════════════════════════════

def _input_style(height: int = 32, error: bool = False) -> str:
    """Stylesheet موحد لكل الـ QLineEdit / QComboBox / QDateEdit."""
    base = _base()
    bg     = "#fef2f2" if error else _C["bg_input"]
    border = "#f87171" if error else _C["border_med"]
    focus  = "#f87171" if error else _C["accent"]
    return f"""
        background:{bg}; border:1.5px solid {border};
        border-radius:6px; padding:0 8px;
        font-size:{fs(base,0)}pt; color:{_C["text_primary"]};
        min-height:{height}px;
    """


def _spinbox_style(height: int = 32,
                   positive: bool = False,
                   widget: str = "QDoubleSpinBox") -> str:
    """Stylesheet موحد لكل الـ QDoubleSpinBox / QSpinBox."""
    base = _base()
    if positive:
        bg, border, color = "#f0fdf4", "#86efac", "#15803d"
        weight = "bold"
    else:
        bg, border, color = _C["bg_input"], _C["border_med"], _C["text_primary"]
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


def _combo_style(height: int = 32) -> str:
    """Stylesheet موحد لكل الـ QComboBox."""
    return f"""
        {_input_style(height)}
        min-height:{height}px;
    """


# ══════════════════════════════════════════════════════════
# SearchLineEdit — حقل بحث موحد
# ══════════════════════════════════════════════════════════

class SearchLineEdit(QWidget):
    """
    حقل بحث موحد مع delay قبل إطلاق الـ signal.

    Signals:
        text_changed(str)
    """

    text_changed = pyqtSignal(str)

    def __init__(self, placeholder: str = "🔍  بحث...",
                 delay_ms: int = 250,
                 height: int = 34,
                 parent=None):
        super().__init__(parent)
        self._delay = delay_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._emit)
        self._build(placeholder, height)

    def _build(self, placeholder: str, height: int):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._inp = QLineEdit()
        self._inp.setPlaceholderText(placeholder)
        self._inp.setFixedHeight(height)
        self._inp.setClearButtonEnabled(True)
        self._inp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._inp.setStyleSheet(_input_style(height))
        self._inp.textChanged.connect(self._on_change)
        lay.addWidget(self._inp)

    def _on_change(self):
        if self._delay > 0:
            self._timer.start()
        else:
            self._emit()

    def _emit(self):
        self.text_changed.emit(self._inp.text().strip().lower())

    def text(self) -> str:
        return self._inp.text().strip().lower()

    def clear(self):
        self._inp.clear()

    def set_placeholder(self, text: str):
        self._inp.setPlaceholderText(text)

    @property
    def line_edit(self) -> QLineEdit:
        return self._inp


# ══════════════════════════════════════════════════════════
# AmountSpinBox — QDoubleSpinBox للمبالغ المالية
# ══════════════════════════════════════════════════════════

class AmountSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox للمبالغ المالية بستايل موحد."""

    def __init__(self, max_: float = 999_999_999,
                 dec: int = 2,
                 min_: float = 0,
                 height: int = 32,
                 currency: str = "",
                 parent=None):
        super().__init__(parent)
        self.setRange(min_, max_)
        self.setDecimals(dec)
        self.setMinimumHeight(height)
        self._height = height
        if currency:
            self.setSuffix(f"  {currency}")
        self.setStyleSheet(_spinbox_style(height))
        self.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val: float):
        self.setStyleSheet(_spinbox_style(self._height, positive=val > 0))


# ══════════════════════════════════════════════════════════
# DateField — QDateEdit موحد
# ══════════════════════════════════════════════════════════

class DateField(QDateEdit):
    """QDateEdit موحد مع popup تقويم."""

    def __init__(self, date: QDate = None,
                 height: int = 32,
                 width: int = None,
                 parent=None):
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

    def set_date_str(self, date_str: str):
        if date_str:
            d = QDate.fromString(date_str, "yyyy-MM-dd")
            if d.isValid():
                self.setDate(d)


# ══════════════════════════════════════════════════════════
# StyledComboBox — QComboBox بستايل موحد
# ══════════════════════════════════════════════════════════

class StyledComboBox(QComboBox):
    """QComboBox بستايل موحد مع الـ theme."""

    def __init__(self, height: int = 32, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(height)
        self.setStyleSheet(
            f"QComboBox {{ {_input_style(height)} }}"
            "QComboBox::drop-down { border:none; width:24px; }"
            f"QComboBox:disabled {{ background:{_C['bg_surface_2']};"
            f" color:{_C['text_disabled']}; }}"
        )


# ══════════════════════════════════════════════════════════
# LabeledInput — حقل مع label أفقي
# ══════════════════════════════════════════════════════════

class LabeledInput(QWidget):
    """حقل مع label على اليمين في سطر أفقي."""

    def __init__(self, label: str, widget: QWidget,
                 unit: str = "",
                 spacing: int = 8,
                 label_width: int = None,
                 parent=None):
        super().__init__(parent)
        self._widget = widget
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(spacing)

        base = _base()
        lbl = QLabel(label)
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
            lbl_unit = QLabel(unit)
            lbl_unit.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_unit)

    @property
    def widget(self) -> QWidget:
        return self._widget


# ══════════════════════════════════════════════════════════
# RequiredLineEdit — QLineEdit مع تحقق بصري
# ══════════════════════════════════════════════════════════

class RequiredLineEdit(QLineEdit):
    """QLineEdit مع تحقق بصري من الفراغ."""

    def __init__(self, placeholder: str = "",
                 height: int = 32,
                 parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        self._height = height
        self._error  = False
        self._refresh_style()
        self.textChanged.connect(self._on_change)

    def _refresh_style(self):
        self.setStyleSheet(f"QLineEdit {{ {_input_style(self._height, self._error)} }}")

    def _on_change(self):
        if self._error and self.text().strip():
            self._error = False
            self._refresh_style()

    def validate(self) -> bool:
        if not self.text().strip():
            self._error = True
            self._refresh_style()
            self.setFocus()
            return False
        return True

    def text_stripped(self) -> str:
        return self.text().strip()

    def clear_error(self):
        self._error = False
        self._refresh_style()


# ══════════════════════════════════════════════════════════
# NotesLineEdit — حقل ملاحظات موحد
# ══════════════════════════════════════════════════════════

class NotesLineEdit(QLineEdit):
    """QLineEdit للملاحظات بستايل مخصص."""

    def __init__(self, placeholder: str = "ملاحظات اختيارية...",
                 height: int = 30,
                 parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        base = _base()
        self.setStyleSheet(f"""
            QLineEdit {{
                background:#fafafa;
                border:1px solid {_C['border']};
                border-radius:6px; padding:0 8px;
                font-size:{fs(base,-1)}pt; color:{_C['text_sec']};
                font-style:italic; min-height:{height}px;
            }}
            QLineEdit:focus {{
                border-color:{_C['border_med']}; background:white;
                font-style:normal; color:{_C['text_primary']};
            }}
        """)