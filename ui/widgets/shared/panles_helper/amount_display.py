"""
ui/widgets/shared/panles_helper/amount_display.py
==================================================
AmountDisplay — عرض موحد للمبالغ المالية مع ألوان الإشارة.

يحل محل الكود المكرر في عرض الأرصدة والمبالغ عبر التطبيق.

المتوفر:
  AmountLabel         — label مبلغ مع لون تلقائي
  DebitCreditDisplay  — عرض مدين/دائن موحد
  BalanceDisplay      — عرض رصيد موحد
  format_amount()     — دالة تنسيق مبلغ
  amount_color()      — لون المبلغ حسب إشارته
"""

from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.app_settings import _C, fs
from .colors_and_base import _base


# ══════════════════════════════════════════════════════════
# دوال مساعدة
# ══════════════════════════════════════════════════════════

def format_amount(value: float, decimals: int = 2,
                  currency: str = "ج") -> str:
    """
    يُنسق مبلغ مالي.

    الاستخدام:
        format_amount(1500.5)      → "1,500.50 ج"
        format_amount(1500, 0)     → "1,500 ج"
        format_amount(1500, 4)     → "1,500.0000 ج"
    """
    fmt = f"{{:,.{decimals}f}}"
    return f"{fmt.format(value)} {currency}" if currency else fmt.format(value)


def amount_color(value: float,
                 positive_color: str = "#1b5e20",
                 negative_color: str = "#b71c1c",
                 zero_color: str = "#555555") -> str:
    """يرجع لون مناسب حسب إشارة المبلغ."""
    if value > 0:
        return positive_color
    if value < 0:
        return negative_color
    return zero_color


def dr_cr_color(side: str) -> str:
    """يرجع لون DR أو CR."""
    return "#1565c0" if side == "dr" else "#c62828"


# ══════════════════════════════════════════════════════════
# AmountLabel — label مبلغ ذكي
# ══════════════════════════════════════════════════════════

class AmountLabel(QLabel):
    """
    Label يعرض مبلغ مع:
      - ألوان تلقائية (موجب = أخضر، سالب = أحمر)
      - تنسيق موحد
      - تحديث سهل

    الاستخدام:
        lbl = AmountLabel()
        lbl.set_amount(1500.5)   # → "1,500.50 ج" بلون أخضر
        lbl.set_amount(-200)     # → "-200.00 ج" بلون أحمر
        lbl.set_amount(0)        # → "─" بلون رمادي
    """

    def __init__(self, value: float = None,
                 currency: str = "ج",
                 decimals: int = 2,
                 bold: bool = True,
                 font_size_offset: int = 0,
                 auto_color: bool = True,
                 parent=None):
        super().__init__(parent)
        self._currency = currency
        self._decimals = decimals
        self._auto_color = auto_color

        base = _base()
        f = QFont()
        f.setPointSize(fs(base, font_size_offset))
        if bold:
            f.setBold(True)
        self.setFont(f)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setStyleSheet("background: transparent; border: none;")

        if value is not None:
            self.set_amount(value)
        else:
            self.reset()

    def set_amount(self, value: float, color: str = None):
        """يحدّث المبلغ والألوان."""
        if value == 0:
            self.setText("─")
            self._apply_color("#555555")
            return

        text = format_amount(value, self._decimals, self._currency)
        self.setText(text)

        if color:
            self._apply_color(color)
        elif self._auto_color:
            self._apply_color(amount_color(value))

    def set_debit(self, value: float):
        """يعرض مبلغ مدين (أزرق)."""
        if value > 0:
            self.set_amount(value, "#1565c0")
        else:
            self.reset()

    def set_credit(self, value: float):
        """يعرض مبلغ دائن (أحمر)."""
        if value > 0:
            self.set_amount(value, "#c62828")
        else:
            self.reset()

    def reset(self, placeholder: str = "─"):
        self.setText(placeholder)
        self._apply_color("#555555")

    def _apply_color(self, color: str):
        f = self.font()
        self.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )


# ══════════════════════════════════════════════════════════
# DebitCreditDisplay — عرض مدين/دائن
# ══════════════════════════════════════════════════════════

class DebitCreditDisplay(QWidget):
    """
    يعرض DR و CR في شريط أفقي.

    الاستخدام:
        disp = DebitCreditDisplay()
        disp.update(total_dr=1500, total_cr=1500)
        layout.addWidget(disp)
    """

    def __init__(self, currency: str = "ج", parent=None):
        super().__init__(parent)
        self._currency = currency
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # DR
        lbl_dr_t = QLabel("إجمالي DR:")
        lbl_dr_t.setStyleSheet(
            "font-weight: bold; color: #1565c0; background: transparent; border: none;"
        )
        self._lbl_dr = QLabel("0.00")
        self._lbl_dr.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1565c0;"
            "background: #e3f2fd; border-radius: 4px; padding: 3px 10px;"
        )

        sep = QLabel("│")
        sep.setStyleSheet(
            "color: #c5cae9; font-size: 18px; margin: 0 4px;"
            "background: transparent; border: none;"
        )

        # CR
        lbl_cr_t = QLabel("إجمالي CR:")
        lbl_cr_t.setStyleSheet(
            "font-weight: bold; color: #c62828; background: transparent; border: none;"
        )
        self._lbl_cr = QLabel("0.00")
        self._lbl_cr.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #c62828;"
            "background: #fdecea; border-radius: 4px; padding: 3px 10px;"
        )

        for w in (lbl_dr_t, self._lbl_dr, sep, lbl_cr_t, self._lbl_cr):
            lay.addWidget(w)
        lay.addStretch()

    def update(self, total_dr: float, total_cr: float):
        self._lbl_dr.setText(f"{total_dr:,.2f} {self._currency}")
        self._lbl_cr.setText(f"{total_cr:,.2f} {self._currency}")

    def reset(self):
        self._lbl_dr.setText("0.00")
        self._lbl_cr.setText("0.00")


# ══════════════════════════════════════════════════════════
# BalanceDisplay — عرض رصيد موحد
# ══════════════════════════════════════════════════════════

class BalanceDisplay(QLabel):
    """
    Label رصيد موحد مع تلوين تلقائي وبادئة.

    الاستخدام:
        disp = BalanceDisplay()
        disp.set_balance(500, "مدين")    # → "الرصيد (مدين): 500.00 ج"
        disp.set_balance(-200, "دائن")   # → "الرصيد (دائن): 200.00 ج"
    """

    def __init__(self, currency: str = "ج", parent=None):
        super().__init__(parent)
        self._currency = currency
        self.setAlignment(Qt.AlignCenter)
        self._apply_neutral()

    def set_balance(self, value: float, side_label: str = "",
                    color: str = None):
        """يحدّث الرصيد."""
        abs_val = abs(value)
        text    = f"الرصيد"
        if side_label:
            text += f" ({side_label})"
        text += f": {abs_val:,.2f} {self._currency}"
        self.setText(text)

        if color:
            _color = color
        elif value >= 0:
            _color = "#1565c0"
        else:
            _color = "#c62828"

        self.setStyleSheet(f"""
            font-size: 14px; font-weight: bold; color: {_color};
            background: #f0f8ff; border: 1px solid #90caf9;
            border-radius: 6px; padding: 6px 16px;
        """)

    def set_debit_credit_balance(self, dr: float, cr: float):
        """يحسب الرصيد من DR و CR."""
        balance = dr - cr
        side    = "مدين" if balance >= 0 else "دائن"
        self.set_balance(balance, side)

    def reset(self):
        self.setText("الرصيد: ─")
        self._apply_neutral()

    def _apply_neutral(self):
        self.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #888;
            background: #f5f5f5; border: 1px solid #e0e0e0;
            border-radius: 6px; padding: 6px 16px;
        """)