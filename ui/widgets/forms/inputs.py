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
          الحل: كل widget يستخدم WidgetMixin (theme=True) بدل الربط اليدوي
          بـ bus.theme_changed، ويعيد بناء الـ stylesheet بقيم _C المحدثة.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QLabel,
    QDoubleSpinBox, QSpinBox, QDateEdit, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate

from ui.theme import _C
from ui.font  import fs, get_font_size
# [إصلاح 1] المسار الصحيح بعد Refactor V3
from ..theme.input_styles import input_style as _input_style, spinbox_style as _spinbox_style
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.constants import (
    BTN_BORDER_RADIUS, SPACING_MD, DROPDOWN_ARROW_W, LABELED_INPUT_SPACING,
    INPUT_HEIGHT, AMOUNT_SPINBOX_MAX, NOTES_LINE_EDIT_HEIGHT,
)
# [إصلاح 2] السطر المحذوف: from ..core import get_font_size as _get_font_size


# ── AmountSpinBox ─────────────────────────────────────────

class AmountSpinBox(QDoubleSpinBox, WidgetMixin):
    """QDoubleSpinBox للمبالغ المالية."""

    def __init__(self, max_: float = AMOUNT_SPINBOX_MAX, dec: int = 2,
                 min_: float = 0, height: int = INPUT_HEIGHT,
                 currency: str = "", parent=None):
        super().__init__(parent)
        self.setRange(min_, max_)
        self.setDecimals(dec)
        self.setMinimumHeight(height)
        self._h = height
        if currency:
            self.setSuffix(f"  {currency}")
        self._init_widget_mixin(theme=True, font=False)
        self._refresh_style()
        self.valueChanged.connect(self._refresh_style)

    def _refresh_style(self, *_):
        self.setStyleSheet(_spinbox_style(self._h, positive=self.value() > 0))


# ── DateField ─────────────────────────────────────────────

class DateField(QDateEdit, WidgetMixin):
    """QDateEdit موحد."""

    def __init__(self, date: QDate = None, height: int = INPUT_HEIGHT,
                 width: int = None, parent=None):
        super().__init__(date or QDate.currentDate(), parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setMinimumHeight(height)
        self._h = height
        if width:
            self.setFixedWidth(width)
        self._init_widget_mixin(theme=True, font=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(
            f"QDateEdit {{ {_input_style(self._h)} }}"
            f"QDateEdit::drop-down {{ border:none; width:{DROPDOWN_ARROW_W}px; }}"
        )

    def date_str(self) -> str:
        return self.date().toString("yyyy-MM-dd")

    def set_date_str(self, s: str):
        if s:
            d = QDate.fromString(s, "yyyy-MM-dd")
            if d.isValid():
                self.setDate(d)


# ── StyledComboBox ────────────────────────────────────────

class StyledComboBox(QComboBox, WidgetMixin):
    """QComboBox بستايل موحد."""

    def __init__(self, height: int = INPUT_HEIGHT, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(height)
        self._h = height
        self._init_widget_mixin(theme=True, font=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(
            f"QComboBox {{ {_input_style(self._h)} }}"
            f"QComboBox::drop-down {{ border:none; width:{DROPDOWN_ARROW_W}px; }}"
            f"QComboBox:disabled {{ background:{_C['bg_surface_2']};"
            f" color:{_C['text_disabled']}; }}"
        )


# ── LabeledInput ──────────────────────────────────────────

class LabeledInput(QWidget, WidgetMixin):
    """حقل مع label أفقي."""

    def __init__(self, label: str, widget: QWidget, unit: str = "",
                 spacing: int = LABELED_INPUT_SPACING, label_width: int = None, parent=None):
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

        self._init_widget_mixin(theme=True, font=True)
        self._refresh_style()

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

class RequiredLineEdit(QLineEdit, WidgetMixin):
    """QLineEdit مع تحقق بصري من الفراغ."""

    def __init__(self, placeholder: str = "", height: int = INPUT_HEIGHT, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        self._h     = height
        self._error = False
        self._init_widget_mixin(theme=True, font=False)
        self._refresh_style()
        self.textChanged.connect(self._on_change)

    def _refresh_style(self, *_):
        self.setStyleSheet(f"QLineEdit {{ {_input_style(self._h, self._error)} }}")

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


# ── NotesLineEdit ─────────────────────────────────────────

class NotesLineEdit(QLineEdit, WidgetMixin):
    """حقل ملاحظات بستايل مخصص يتزامن مع الثيم."""

    def __init__(self, placeholder: str = "",
                 height: int = NOTES_LINE_EDIT_HEIGHT, parent=None):
        super().__init__(parent)
        self._custom_placeholder = placeholder
        self.setMinimumHeight(height)
        self._h = height
        self._init_widget_mixin(theme=True, font=False, lang=True)
        self._refresh_style()
        self._refresh_lang()

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(f"""
            QLineEdit {{
                background:{_C['bg_surface_2']};
                border:1px solid {_C['border']};
                border-radius:{BTN_BORDER_RADIUS}px; padding:0 {SPACING_MD}px;
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

    def _refresh_lang(self, *_):
        from ui.widgets.core.i18n import tr
        self.setPlaceholderText(
            self._custom_placeholder if self._custom_placeholder
            else tr('notes_optional_placeholder')
        )
