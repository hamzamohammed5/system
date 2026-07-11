"""
ui/widgets/components/amount_label.py
=======================================
Label widgets للمبالغ والأرصدة.

مستخرج من components/label.py:
  format_amount, amount_color, dr_cr_color,
  AmountLabel, DebitCreditDisplay, BalanceDisplay
"""

from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors import status_colors
from ..core.i18n import tr
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    DR_CR_DISPLAY_SPACING, DR_CR_CHIP_BORDER_RADIUS,
    DR_CR_CHIP_PAD_V, DR_CR_CHIP_PAD_H,
    BALANCE_DISPLAY_BORDER_W, BALANCE_DISPLAY_RADIUS,
    BALANCE_DISPLAY_PAD_V, BALANCE_DISPLAY_PAD_H,
)


# ── helpers ───────────────────────────────────────────────

def format_amount(value: float, decimals: int = 2, currency: str = None) -> str:
    _currency = currency if currency is not None else tr('currency_sym')
    fmt = f"{{:,.{decimals}f}}"
    return f"{fmt.format(value)} {_currency}" if _currency else fmt.format(value)


def amount_color(value: float,
                 positive_color: str = None,
                 negative_color: str = None,
                 zero_color: str = None) -> str:
    pos  = positive_color or _C["success"]
    neg  = negative_color or _C["danger"]
    zero = zero_color     or _C["text_muted"]
    if value > 0:
        return pos
    if value < 0:
        return neg
    return zero


def dr_cr_color(side: str) -> str:
    s = status_colors("primary" if side == "dr" else "danger")
    return s["fg"]


# ── AmountLabel ───────────────────────────────────────────

class AmountLabel(QLabel, WidgetMixin):
    """Label يعرض مبلغ مع ألوان تلقائية وتنسيق موحد."""

    def __init__(self, value: float = None, currency: str = None,
                 decimals: int = 2, bold: bool = True,
                 font_size_offset: int = 0, auto_color: bool = True,
                 parent=None):
        super().__init__(parent)
        self._custom_currency = currency
        self._currency   = currency if currency is not None else tr('currency_sym')
        self._decimals   = decimals
        self._bold       = bold
        self._font_size_offset = font_size_offset
        self._auto_color = auto_color
        self._value      = value

        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()
        if value is not None:
            self.set_amount(value)
        else:
            self.reset()

    def _refresh_style(self, *_):
        base = get_font_size()
        f = QFont()
        f.setPointSize(fs(base, self._font_size_offset))
        if self._bold:
            f.setBold(True)
        self.setFont(f)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setStyleSheet("background:transparent; border:none;")
        # أعد تطبيق اللون الحالي بعد تغيير الثيم/الخط
        if self._value is not None and self._value != 0:
            self._set_color(amount_color(self._value) if self._auto_color else _C["text_muted"])
        else:
            self._set_color(_C["text_muted"])

    def _refresh_lang(self, *_):
        if self._custom_currency is None:
            self._currency = tr('currency_sym')
        # أعد رسم النص لو كان الرصيد صفر/فارغ (نص قابل للترجمة)
        if self._value is None or self._value == 0:
            self.setText(tr('amount_dash_placeholder'))
        elif self._custom_currency is None:
            self.setText(format_amount(self._value, self._decimals, self._currency))

    def set_amount(self, value: float, color: str = None):
        self._value = value
        if value == 0:
            self.setText(tr('amount_dash_placeholder'))
            self._set_color(_C["text_muted"])
            return
        self.setText(format_amount(value, self._decimals, self._currency))
        self._set_color(color or (amount_color(value) if self._auto_color else _C["text_muted"]))

    def set_debit(self, value: float):
        color = status_colors("primary")["fg"]
        self.set_amount(value, color) if value > 0 else self.reset()

    def set_credit(self, value: float):
        color = status_colors("danger")["fg"]
        self.set_amount(value, color) if value > 0 else self.reset()

    def reset(self, placeholder: str = None):
        self._value = None
        self.setText(placeholder if placeholder is not None else tr('amount_dash_placeholder'))
        self._set_color(_C["text_muted"])

    def _set_color(self, color: str):
        self.setStyleSheet(f"color:{color}; background:transparent; border:none;")


# ── DebitCreditDisplay ────────────────────────────────────

class DebitCreditDisplay(QWidget, WidgetMixin):
    """عرض DR و CR في شريط أفقي."""

    def __init__(self, currency: str = None, parent=None):
        super().__init__(parent)
        self._custom_currency = currency
        self._currency = currency if currency is not None else tr('currency_sym')
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(DR_CR_DISPLAY_SPACING)

        for attr, attr_t, key in [
            ("_lbl_dr", "_lbl_dr_t", "dr_total_label"),
            ("_lbl_cr", "_lbl_cr_t", "cr_total_label"),
        ]:
            lbl_t = QLabel(tr(key))
            lbl_t.setStyleSheet("background:transparent; border:none;")
            lbl_v = QLabel(tr('amount_zero_placeholder'))
            lbl_v.setStyleSheet("background:transparent; border:none;")
            setattr(self, attr, lbl_v)
            setattr(self, attr_t, lbl_t)
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            if attr == "_lbl_dr":
                sep = QLabel(tr('vertical_separator'))
                sep.setStyleSheet("background:transparent; border:none;")
                self._sep = sep
                lay.addWidget(sep)

        lay.addStretch()

    def _refresh_style(self, *_):
        base = get_font_size()
        dr_s = status_colors("primary")
        cr_s = status_colors("danger")
        self._lbl_dr_t.setStyleSheet(
            f"font-weight:bold; color:{dr_s['fg']};"
            "background:transparent; border:none;"
        )
        self._lbl_dr.setStyleSheet(
            f"font-size:{fs(base, +1)}pt; font-weight:bold; color:{dr_s['fg']};"
            f"background:{dr_s['bg']}; border-radius:{DR_CR_CHIP_BORDER_RADIUS}px; padding:{DR_CR_CHIP_PAD_V}px {DR_CR_CHIP_PAD_H}px;"
        )
        self._lbl_cr_t.setStyleSheet(
            f"font-weight:bold; color:{cr_s['fg']};"
            "background:transparent; border:none;"
        )
        self._lbl_cr.setStyleSheet(
            f"font-size:{fs(base, +1)}pt; font-weight:bold; color:{cr_s['fg']};"
            f"background:{cr_s['bg']}; border-radius:{DR_CR_CHIP_BORDER_RADIUS}px; padding:{DR_CR_CHIP_PAD_V}px {DR_CR_CHIP_PAD_H}px;"
        )
        self._sep.setStyleSheet(
            f"color:{_C['border_med']}; font-size:{fs(base, +4)}pt;"
            "background:transparent; border:none;"
        )

    def _refresh_lang(self, *_):
        if self._custom_currency is None:
            self._currency = tr('currency_sym')
        self._lbl_dr_t.setText(tr('dr_total_label'))
        self._lbl_cr_t.setText(tr('cr_total_label'))
        self._sep.setText(tr('vertical_separator'))

    def update(self, total_dr: float, total_cr: float):
        self._lbl_dr.setText(f"{total_dr:,.2f} {self._currency}")
        self._lbl_cr.setText(f"{total_cr:,.2f} {self._currency}")

    def reset(self):
        self._lbl_dr.setText(tr('amount_zero_placeholder'))
        self._lbl_cr.setText(tr('amount_zero_placeholder'))


# ── BalanceDisplay ────────────────────────────────────────

class BalanceDisplay(QLabel, WidgetMixin):
    """Label رصيد موحد مع تلوين تلقائي."""

    def __init__(self, currency: str = None, parent=None):
        super().__init__(parent)
        self._custom_currency = currency
        self._currency = currency if currency is not None else tr('currency_sym')
        self._last_value = None
        self._last_side_label = ""
        self._last_color = None
        self._is_neutral = True
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self.setAlignment(Qt.AlignCenter)
        self._apply_neutral()

    def set_balance(self, value: float, side_label: str = "", color: str = None):
        self._last_value = value
        self._last_side_label = side_label
        self._last_color = color
        self._is_neutral = False

        abs_val = abs(value)
        text = tr('balance')
        if side_label:
            text += tr('balance_with_side').format(side_label=side_label)
        text += f": {abs_val:,.2f} {self._currency}"
        self.setText(text)

        s = status_colors("primary" if value >= 0 else "danger")
        _color = color or s["fg"]
        base = get_font_size()

        self.setStyleSheet(
            f"font-size:{fs(base, +1)}pt; font-weight:bold; color:{_color};"
            f"background:{s['bg']}; border:{BALANCE_DISPLAY_BORDER_W}px solid {s['border']};"
            f"border-radius:{BALANCE_DISPLAY_RADIUS}px; padding:{BALANCE_DISPLAY_PAD_V}px {BALANCE_DISPLAY_PAD_H}px;"
        )

    def set_debit_credit_balance(self, dr: float, cr: float):
        balance = dr - cr
        self.set_balance(balance, tr('debit') if balance >= 0 else tr('credit'))

    def reset(self):
        self._is_neutral = True
        self.setText(tr('balance_dash'))
        self._apply_neutral()

    def _apply_neutral(self):
        base = get_font_size()
        self.setStyleSheet(
            f"font-size:{fs(base, +1)}pt; font-weight:bold; color:{_C['text_muted']};"
            f"background:{_C['bg_surface_2']}; border:{BALANCE_DISPLAY_BORDER_W}px solid {_C['border']};"
            f"border-radius:{BALANCE_DISPLAY_RADIUS}px; padding:{BALANCE_DISPLAY_PAD_V}px {BALANCE_DISPLAY_PAD_H}px;"
        )

    def _refresh_style(self, *_):
        if self._is_neutral:
            self._apply_neutral()
        else:
            self.set_balance(self._last_value, self._last_side_label, self._last_color)

    def _refresh_lang(self, *_):
        if self._custom_currency is None:
            self._currency = tr('currency_sym')
        if self._is_neutral:
            self.setText(tr('balance_dash'))
        else:
            self.set_balance(self._last_value, self._last_side_label, self._last_color)