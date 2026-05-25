"""
ui/widgets/shared/components/label.py
========================================
Labels متخصصة: InfoRow, ModeLabel, AmountLabel + دوال مساعدة.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.core.settings import get_base


# ══════════════════════════════════════════════════════════════════
# InfoRow — صف معلومات ثانوية مع فاصل
# ══════════════════════════════════════════════════════════════════

class InfoRow(QWidget):
    """صف معلومات ثانوية مفصولة بـ separator."""

    def __init__(self, separator: str = "  ·  ", parent=None):
        super().__init__(parent)
        self._separator = separator
        self._lbl = QLabel()
        self._lbl.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(get_base(),-1)}pt;"
            "background:transparent; border:none;"
        )
        self._lbl.setWordWrap(True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lbl)

    def set_parts(self, parts: list):
        filtered = [str(p) for p in parts if p]
        self._lbl.setText(self._separator.join(filtered) if filtered else "")

    def set_text(self, text: str):
        self._lbl.setText(text)

    def label(self) -> QLabel:
        return self._lbl


# ══════════════════════════════════════════════════════════════════
# ModeLabel — label وضع الفورم (إضافة / تعديل)
# ══════════════════════════════════════════════════════════════════

class ModeLabel(QLabel):
    """
    Label يُظهر وضع الفورم الحالي.
    أزرق = إضافة، برتقالي = تعديل.
    """

    def __init__(self, add_text: str = "جديد",
                 icon: str = "", parent=None):
        super().__init__(parent)
        self._add_text = add_text
        self._icon     = icon
        self._is_edit  = False
        self.set_add_mode()

    def set_add_mode(self, text: str = None):
        self._is_edit = False
        prefix  = f"{self._icon}  " if self._icon else ""
        display = text or self._add_text
        self.setText(f"─── {prefix}{display} ───")
        base = get_base()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            f"color:{_C['accent']}; background:transparent; border:none;"
        )

    def set_edit_mode(self, name: str = ""):
        self._is_edit = True
        prefix  = f"{self._icon}  " if self._icon else ""
        suffix  = f": {name}" if name else ""
        self.setText(f"─── {prefix}تعديل{suffix} ───")
        base = get_base()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            "color:#e65100; background:transparent; border:none;"
        )

    def set_custom(self, text: str, color: str = None):
        self.setText(text)
        base = get_base()
        c = color or _C["text_sec"]
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            f"color:{c}; background:transparent; border:none;"
        )

    @property
    def is_edit_mode(self) -> bool:
        return self._is_edit


# ══════════════════════════════════════════════════════════════════
# AmountLabel + helpers
# ══════════════════════════════════════════════════════════════════

def format_amount(value: float, decimals: int = 2, currency: str = "ج") -> str:
    fmt = f"{{:,.{decimals}f}}"
    return f"{fmt.format(value)} {currency}" if currency else fmt.format(value)


def amount_color(value: float, pos: str = "#1b5e20",
                 neg: str = "#b71c1c", zero: str = "#555555") -> str:
    if value > 0: return pos
    if value < 0: return neg
    return zero


def dr_cr_color(side: str) -> str:
    return "#1565c0" if side == "dr" else "#c62828"


class AmountLabel(QLabel):
    """
    Label يعرض مبلغ مع ألوان تلقائية وتنسيق موحد.

    الاستخدام:
        lbl = AmountLabel()
        lbl.set_amount(1500.5)   # → "1,500.50 ج" بلون أخضر
    """

    def __init__(self, value: float = None, currency: str = "ج",
                 decimals: int = 2, bold: bool = True,
                 font_offset: int = 0, auto_color: bool = True,
                 parent=None):
        super().__init__(parent)
        self._currency   = currency
        self._decimals   = decimals
        self._auto_color = auto_color

        base = get_base()
        f = QFont()
        f.setPointSize(fs(base, font_offset))
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
            self._set_color("#555555")
            return
        self.setText(format_amount(value, self._decimals, self._currency))
        self._set_color(color or (amount_color(value) if self._auto_color else "#555555"))

    def set_debit(self, value: float):
        self.set_amount(value, "#1565c0") if value > 0 else self.reset()

    def set_credit(self, value: float):
        self.set_amount(value, "#c62828") if value > 0 else self.reset()

    def reset(self, placeholder: str = "─"):
        self.setText(placeholder)
        self._set_color("#555555")

    def _set_color(self, color: str):
        self.setStyleSheet(f"color:{color}; background:transparent; border:none;")