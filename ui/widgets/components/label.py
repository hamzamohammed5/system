"""
ui/widgets/components/label.py
================================
كل الـ labels والـ display helpers في مكان واحد:

  InfoRow              — صف معلومات ثانوية مع separator
  ModeLabel            — label وضع الفورم (إضافة / تعديل)
  AmountLabel          — label مبلغ ذكي مع ألوان تلقائية
  DebitCreditDisplay   — عرض DR و CR في شريط أفقي
  BalanceDisplay       — label رصيد موحد مع تلوين تلقائي
  ProgressBar          — شريط تقدم
  MultiProgressBar     — أشرطة تقدم متعددة

  format_amount()      — تنسيق مبلغ
  amount_color()       — لون حسب الإشارة
  dr_cr_color()        — لون DR/CR
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from ui.app_settings import get_font_size


# ══════════════════════════════════════════════════════════
# InfoRow
# ══════════════════════════════════════════════════════════

class InfoRow(QWidget):
    """صف معلومات ثانوية مفصولة بـ separator."""

    def __init__(self, separator: str = "  ·  ", parent=None):
        super().__init__(parent)
        self._separator = separator
        self._lbl = QLabel()
        self._lbl.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(get_font_size(),-1)}pt;"
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


# ══════════════════════════════════════════════════════════
# ModeLabel
# ══════════════════════════════════════════════════════════

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
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            f"color:{_C['accent']}; background:transparent; border:none;"
        )

    def set_edit_mode(self, name: str = ""):
        self._is_edit = True
        prefix = f"{self._icon}  " if self._icon else ""
        suffix = f": {name}" if name else ""
        self.setText(f"─── {prefix}تعديل{suffix} ───")
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            "color:#e65100; background:transparent; border:none;"
        )

    def set_custom(self, text: str, color: str = None):
        self.setText(text)
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            f"color:{color or _C['text_sec']}; background:transparent; border:none;"
        )

    @property
    def is_edit_mode(self) -> bool:
        return self._is_edit


# ══════════════════════════════════════════════════════════
# Amount helpers
# ══════════════════════════════════════════════════════════

def format_amount(value: float, decimals: int = 2, currency: str = "ج") -> str:
    fmt = f"{{:,.{decimals}f}}"
    return f"{fmt.format(value)} {currency}" if currency else fmt.format(value)


def amount_color(value: float,
                 positive_color: str = "#1b5e20",
                 negative_color: str = "#b71c1c",
                 zero_color: str = "#555555") -> str:
    if value > 0: return positive_color
    if value < 0: return negative_color
    return zero_color


def dr_cr_color(side: str) -> str:
    return "#1565c0" if side == "dr" else "#c62828"


# ══════════════════════════════════════════════════════════
# AmountLabel
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# DebitCreditDisplay
# ══════════════════════════════════════════════════════════

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

        for attr, text, color, bg in [
            ("_lbl_dr", "إجمالي DR:", "#1565c0", "#e3f2fd"),
            ("_lbl_cr", "إجمالي CR:", "#c62828", "#fdecea"),
        ]:
            lbl_t = QLabel(text)
            lbl_t.setStyleSheet(
                f"font-weight:bold; color:{color}; background:transparent; border:none;"
            )
            lbl_v = QLabel("0.00")
            lbl_v.setStyleSheet(
                f"font-size:14px; font-weight:bold; color:{color};"
                f"background:{bg}; border-radius:4px; padding:3px 10px;"
            )
            setattr(self, attr, lbl_v)
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            if color == "#1565c0":
                sep = QLabel("│")
                sep.setStyleSheet(
                    "color:#c5cae9; font-size:18px; background:transparent; border:none;"
                )
                lay.addWidget(sep)

        lay.addStretch()

    def update(self, total_dr: float, total_cr: float):
        self._lbl_dr.setText(f"{total_dr:,.2f} {self._currency}")
        self._lbl_cr.setText(f"{total_cr:,.2f} {self._currency}")

    def reset(self):
        self._lbl_dr.setText("0.00")
        self._lbl_cr.setText("0.00")


# ══════════════════════════════════════════════════════════
# BalanceDisplay
# ══════════════════════════════════════════════════════════

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

        _color = color or ("#1565c0" if value >= 0 else "#c62828")
        self.setStyleSheet(f"""
            font-size:14px; font-weight:bold; color:{_color};
            background:#f0f8ff; border:1px solid #90caf9;
            border-radius:6px; padding:6px 16px;
        """)

    def set_debit_credit_balance(self, dr: float, cr: float):
        balance = dr - cr
        self.set_balance(balance, "مدين" if balance >= 0 else "دائن")

    def reset(self):
        self.setText("الرصيد: ─")
        self._apply_neutral()

    def _apply_neutral(self):
        self.setStyleSheet("""
            font-size:14px; font-weight:bold; color:#888;
            background:#f5f5f5; border:1px solid #e0e0e0;
            border-radius:6px; padding:6px 16px;
        """)


# ══════════════════════════════════════════════════════════
# ProgressBar
# ══════════════════════════════════════════════════════════

class ProgressBar(QWidget):
    """شريط تقدم: [label] [████░░░] [75%]"""

    def __init__(self, label: str = "", color: str = "#1565c0",
                 height: int = 8, show_pct: bool = True,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color    = color
        self._height   = height
        self._show_pct = show_pct
        self._value    = 0.0
        self._build(label)

    def _build(self, label: str):
        self.setStyleSheet("background:transparent;")
        base = get_font_size()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        if label:
            self._lbl_title = QLabel(label)
            self._lbl_title.setStyleSheet(
                f"color:{_C['text_sec']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            top_row.addWidget(self._lbl_title)

        top_row.addStretch()

        if self._show_pct:
            self._lbl_pct = QLabel("0%")
            f = QFont()
            f.setPointSize(fs(base, -1))
            f.setBold(True)
            self._lbl_pct.setFont(f)
            self._lbl_pct.setStyleSheet(
                f"color:{self._color}; background:transparent; border:none;"
            )
            self._lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            top_row.addWidget(self._lbl_pct)

        root.addLayout(top_row)

        track = QFrame()
        track.setFixedHeight(self._height)
        track.setStyleSheet(f"""
            QFrame {{
                background:{_C['border']}; border-radius:{self._height//2}px; border:none;
            }}
        """)

        track_lay = QHBoxLayout(track)
        track_lay.setContentsMargins(0, 0, 0, 0)
        track_lay.setSpacing(0)

        self._fill = QFrame()
        self._fill.setFixedHeight(self._height)
        self._fill.setStyleSheet(f"""
            QFrame {{
                background:{self._color}; border-radius:{self._height//2}px; border:none;
            }}
        """)
        self._fill.setFixedWidth(0)
        track_lay.addWidget(self._fill)
        track_lay.addStretch()

        self._track = track
        root.addWidget(track)

    def set_value(self, value: float, label: str = None):
        self._value = max(0.0, min(100.0, value))
        total_w = self._track.width()
        fill_w  = int(total_w * self._value / 100) if total_w > 0 else 0
        self._fill.setFixedWidth(fill_w)

        if self._show_pct:
            self._lbl_pct.setText(label if label is not None else f"{self._value:.0f}%")

        self._update_color()

    def _update_color(self):
        if self._value >= 90:
            color = "#2e7d32"
        elif self._value >= 60:
            color = self._color
        elif self._value >= 30:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        self._fill.setStyleSheet(f"""
            QFrame {{
                background:{color}; border-radius:{self._height//2}px; border:none;
            }}
        """)
        if self._show_pct:
            self._lbl_pct.setStyleSheet(
                f"color:{color}; background:transparent; border:none;"
            )

    def set_color(self, color: str):
        self._color = color
        self._update_color()

    def value(self) -> float:
        return self._value

    def reset(self):
        self.set_value(0, "─")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total_w = self._track.width()
        if total_w > 0:
            self._fill.setFixedWidth(int(total_w * self._value / 100))


# ══════════════════════════════════════════════════════════
# MultiProgressBar
# ══════════════════════════════════════════════════════════

class MultiProgressBar(QWidget):
    """أشرطة تقدم متعددة في عمود."""

    def __init__(self, spacing: int = 8, parent=None):
        super().__init__(parent)
        self._bars: list[ProgressBar] = []
        self.setStyleSheet("background:transparent;")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(spacing)

    def add_bar(self, label: str, value: float = 0,
                color: str = "#1565c0") -> ProgressBar:
        bar = ProgressBar(label=label, color=color)
        bar.set_value(value)
        self._lay.addWidget(bar)
        self._bars.append(bar)
        return bar

    def clear_bars(self):
        for bar in self._bars:
            self._lay.removeWidget(bar)
            bar.deleteLater()
        self._bars.clear()

    def update_bar(self, index: int, value: float):
        if 0 <= index < len(self._bars):
            self._bars[index].set_value(value)