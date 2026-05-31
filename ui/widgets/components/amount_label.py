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


# ── helpers ───────────────────────────────────────────────

def format_amount(value: float, decimals: int = 2, currency: str = "ج") -> str:
    fmt = f"{{:,.{decimals}f}}"
    return f"{fmt.format(value)} {currency}" if currency else fmt.format(value)


def amount_color(value: float,
                 positive_color: str = None,
                 negative_color: str = None,
                 zero_color: str = None) -> str:
    pos  = positive_color or _C.get("success", "#2E7D52")
    neg  = negative_color or _C.get("danger",  "#C0392B")
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

class AmountLabel(QLabel):
    """Label يعرض مبلغ مع ألوان تلقائية وتنسيق موحد."""

    def __init__(self, value: float = None, currency: str = "ج",
                 decimals: int = 2, bold: bool = True,
                 font_size_offset: int = 0, auto_color: bool = True,
                 parent=None):
        super().__init__(parent)
        self._currency   = currency
        self._decimals   = decimals
        self._auto_color = auto_color

        base = get_font_size()
        f = QFont()
        f.setPointSize(fs(base, font_size_offset))
        if bold:
            f.setBold(True)
        self.setFont(f)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setStyleSheet("background:transparent; border:none;")

        if value is not None:
            self.set_amount(value)
        else:
            self.reset()

    def set_amount(self, value: float, color: str = None):
        if value == 0:
            self.setText("─")
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

    def reset(self, placeholder: str = "─"):
        self.setText(placeholder)
        self._set_color(_C["text_muted"])

    def _set_color(self, color: str):
        self.setStyleSheet(f"color:{color}; background:transparent; border:none;")


# ── DebitCreditDisplay ────────────────────────────────────

class DebitCreditDisplay(QWidget):
    """عرض DR و CR في شريط أفقي."""

    def __init__(self, currency: str = "ج", parent=None):
        super().__init__(parent)
        self._currency = currency
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        dr_s = status_colors("primary")
        cr_s = status_colors("danger")
        base = get_font_size()

        for attr, text, s in [
            ("_lbl_dr", "إجمالي DR:", dr_s),
            ("_lbl_cr", "إجمالي CR:", cr_s),
        ]:
            lbl_t = QLabel(text)
            lbl_t.setStyleSheet(
                f"font-weight:bold; color:{s['fg']};"
                "background:transparent; border:none;"
            )
            lbl_v = QLabel("0.00")
            lbl_v.setStyleSheet(
                f"font-size:{fs(base, +1)}pt; font-weight:bold; color:{s['fg']};"
                f"background:{s['bg']}; border-radius:4px; padding:3px 10px;"
            )
            setattr(self, attr, lbl_v)
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            if attr == "_lbl_dr":
                sep = QLabel("│")
                sep.setStyleSheet(
                    f"color:{_C['border_med']}; font-size:{fs(base, +4)}pt;"
                    "background:transparent; border:none;"
                )
                lay.addWidget(sep)

        lay.addStretch()

    def update(self, total_dr: float, total_cr: float):
        self._lbl_dr.setText(f"{total_dr:,.2f} {self._currency}")
        self._lbl_cr.setText(f"{total_cr:,.2f} {self._currency}")

    def reset(self):
        self._lbl_dr.setText("0.00")
        self._lbl_cr.setText("0.00")


# ── BalanceDisplay ────────────────────────────────────────

class BalanceDisplay(QLabel):
    """Label رصيد موحد مع تلوين تلقائي."""

    def __init__(self, currency: str = "ج", parent=None):
        super().__init__(parent)
        self._currency = currency
        self.setAlignment(Qt.AlignCenter)
        self._apply_neutral()

    def set_balance(self, value: float, side_label: str = "", color: str = None):
        abs_val = abs(value)
        text = "الرصيد"
        if side_label:
            text += f" ({side_label})"
        text += f": {abs_val:,.2f} {self._currency}"
        self.setText(text)

        s = status_colors("primary" if value >= 0 else "danger")
        _color = color or s["fg"]
        base = get_font_size()

        self.setStyleSheet(
            f"font-size:{fs(base, +1)}pt; font-weight:bold; color:{_color};"
            f"background:{s['bg']}; border:1px solid {s['border']};"
            "border-radius:6px; padding:6px 16px;"
        )

    def set_debit_credit_balance(self, dr: float, cr: float):
        balance = dr - cr
        self.set_balance(balance, "مدين" if balance >= 0 else "دائن")

    def reset(self):
        self.setText("الرصيد: ─")
        self._apply_neutral()

    def _apply_neutral(self):
        base = get_font_size()
        self.setStyleSheet(
            f"font-size:{fs(base, +1)}pt; font-weight:bold; color:{_C['text_muted']};"
            f"background:{_C['bg_surface_2']}; border:1px solid {_C['border']};"
            "border-radius:6px; padding:6px 16px;"
        )