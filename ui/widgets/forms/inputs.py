"""
ui/widgets/forms/inputs.py
===========================
Input widgets الموحدة للتطبيق.

[إصلاح 1] from ..theme.styles → from ..theme.input_styles
          theme/styles.py محذوف بعد Refactor V3.
[إصلاح 2] حذف from ..core import get_font_size as _get_font_size
          مكرر مع from ui.font import get_font_size أعلاه.
[إصلاح ثيم] كل الـ widgets هنا كانت تبني stylesheet مرة واحدة في __init__
          بقيم _C وقت الإنشاء فقط، ولا تستمع لـ bus.theme_changed.
          بما أن setStyleSheet المحلي على الـ widget له أولوية أعلى من
          الـ global app stylesheet في Qt، كانت الألوان تتجمد على الثيم
          الذي بُني فيه الـ widget ولا تتحدث عند تبديل الثيم لاحقاً.
          الحل: كل widget يربط نفسه بـ bus.theme_changed عبر weakref slot
          ويعيد بناء الـ stylesheet بقيم _C المحدثة.
"""
import weakref

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QLabel,
    QDoubleSpinBox, QSpinBox, QDateEdit, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate

from ui.theme import _C
from ui.font  import fs, get_font_size
# [إصلاح 1] المسار الصحيح بعد Refactor V3
from ..theme.input_styles import input_style as _input_style, spinbox_style as _spinbox_style
from ui.widgets.core.events import bus
# [إصلاح 2] السطر المحذوف: from ..core import get_font_size as _get_font_size


def _connect_theme_refresh(widget, slot) -> None:
    """
    [إصلاح ثيم] يربط widget بـ bus.theme_changed عبر weakref حتى لا يمنع GC.
    slot يُحفظ كـ attribute على الـ widget نفسه لمنع جمعه قبل الـ widget.
    """
    _weak = weakref.ref(widget)

    def _on_theme_changed(_theme_name=None):
        obj = _weak()
        if obj is not None:
            slot(obj)

    widget._theme_refresh_slot = _on_theme_changed
    bus.theme_changed.connect(widget._theme_refresh_slot, Qt.UniqueConnection)


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
        self._refresh_style()
        self.valueChanged.connect(self._refresh_style)
        # [إصلاح ثيم] إعادة بناء الستايل عند تغيير الثيم
        _connect_theme_refresh(self, AmountSpinBox._refresh_style)

    def _refresh_style(self, *_):
        self.setStyleSheet(_spinbox_style(self._h, positive=self.value() > 0))


# ── DateField ─────────────────────────────────────────────

class DateField(QDateEdit):
    """QDateEdit موحد."""

    def __init__(self, date: QDate = None, height: int = 32,
                 width: int = None, parent=None):
        super().__init__(date or QDate.currentDate(), parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setMinimumHeight(height)
        self._h = height
        if width:
            self.setFixedWidth(width)
        self._refresh_style()
        # [إصلاح ثيم]
        _connect_theme_refresh(self, DateField._refresh_style)

    def _refresh_style(self, *_):
        self.setStyleSheet(
            f"QDateEdit {{ {_input_style(self._h)} }}"
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
        self._h = height
        self._refresh_style()
        # [إصلاح ثيم]
        _connect_theme_refresh(self, StyledComboBox._refresh_style)

    def _refresh_style(self, *_):
        self.setStyleSheet(
            f"QComboBox {{ {_input_style(self._h)} }}"
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
        self._widget      = widget
        self._label_text  = label
        self._unit_text   = unit
        self._label_width = label_width
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(spacing)

        self._lbl = QLabel(label)
        self._lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if label_width:
            self._lbl.setFixedWidth(label_width)
        lay.addWidget(self._lbl)
        lay.addWidget(widget, stretch=1)

        self._unit_lbl = None
        if unit:
            self._unit_lbl = QLabel(unit)
            lay.addWidget(self._unit_lbl)

        self._refresh_style()
        # [إصلاح ثيم]
        _connect_theme_refresh(self, LabeledInput._refresh_style)

    def _refresh_style(self, *_):
        base = get_font_size()
        self._lbl.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,0)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )
        if self._unit_lbl is not None:
            self._unit_lbl.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )

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
        # [إصلاح ثيم]
        _connect_theme_refresh(self, RequiredLineEdit._refresh)

    def _refresh(self, *_):
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
    """حقل ملاحظات بستايل مخصص يتزامن مع الثيم."""

    def __init__(self, placeholder: str = "ملاحظات اختيارية...",
                 height: int = 30, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        self._h = height
        self._refresh_style()
        # [إصلاح ثيم]
        _connect_theme_refresh(self, NotesLineEdit._refresh_style)

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(f"""
            QLineEdit {{
                background:{_C['bg_surface_2']};
                border:1px solid {_C['border']};
                border-radius:6px; padding:0 8px;
                font-size:{fs(base,-1)}pt; color:{_C['text_sec']};
                font-style:italic; min-height:{self._h}px;
            }}
            QLineEdit:focus {{
                border-color:{_C['border_med']};
                background:{_C['bg_input']};
                font-style:normal;
                color:{_C['text_primary']};
            }}
        """)
