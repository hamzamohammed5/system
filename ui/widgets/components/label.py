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

[تحسين 15] ProgressBar.resizeEvent:
  التحقق من total_w > 0 موجود ومقصود — لا مشكلة في الكود.
  الـ _fill.setFixedWidth يُستدعى فقط عندما يكون العرض أكبر من صفر،
  وهذا يمنع رسم خاطئ عند أول ظهور الـ widget قبل حساب العرض الفعلي.
  التوثيق هنا للتوضيح فقط ومنع أي تعديل مستقبلي يُزيل هذا التحقق.
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
from ..core.colors   import status_colors


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
            f"color:{_C['text_muted']}; font-size:{fs(get_font_size(), -1)}pt;"
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
            f"font-weight:bold; font-size:{fs(base, 0)}pt;"
            f"color:{_C['accent']}; background:transparent; border:none;"
        )

    def set_edit_mode(self, name: str = ""):
        self._is_edit = True
        prefix = f"{self._icon}  " if self._icon else ""
        suffix = f": {name}" if name else ""
        self.setText(f"─── {prefix}تعديل{suffix} ───")
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base, 0)}pt;"
            f"color:{_C['warning']}; background:transparent; border:none;"
        )

    def set_custom(self, text: str, color: str = None):
        self.setText(text)
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base, 0)}pt;"
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


# ══════════════════════════════════════════════════════════
# ProgressBar
# ══════════════════════════════════════════════════════════

class ProgressBar(QWidget):
    """شريط تقدم: [label] [████░░░] [75%]"""

    def __init__(self, label: str = "", color: str = None,
                 height: int = 8, show_pct: bool = True,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color    = color or _C.get("accent")
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
                f"color:{_C['text_sec']}; font-size:{fs(base, -1)}pt;"
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
                background:{_C['border']}; border-radius:{self._height // 2}px; border:none;
            }}
        """)

        track_lay = QHBoxLayout(track)
        track_lay.setContentsMargins(0, 0, 0, 0)
        track_lay.setSpacing(0)

        self._fill = QFrame()
        self._fill.setFixedHeight(self._height)
        self._fill.setStyleSheet(f"""
            QFrame {{
                background:{self._color}; border-radius:{self._height // 2}px; border:none;
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
        s_success = status_colors("success")
        s_warning = status_colors("warning")
        s_danger  = status_colors("danger")

        if self._value >= 90:
            color = s_success["fg"]
        elif self._value >= 60:
            color = self._color
        elif self._value >= 30:
            color = s_warning["fg"]
        else:
            color = s_danger["fg"]

        self._fill.setStyleSheet(f"""
            QFrame {{
                background:{color}; border-radius:{self._height // 2}px; border:none;
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
        """
        [تحسين 15] يُعيد حساب عرض الـ fill عند تغيير حجم الـ widget.

        التحقق من total_w > 0 مقصود ومهم:
          - عند أول ظهور الـ widget، العرض قد يكون صفراً قبل حساب الـ layout.
          - setFixedWidth(0) في هذه الحالة صحيح (لا fill مرئي).
          - لو أُزيل التحقق وكان total_w صفراً، ينتج fill_w = 0 وهو نفس النتيجة،
            لكن الكود يصبح أقل وضوحاً في نيّته.
          - لا تُزِل هذا التحقق — هو guard مقصود وليس كوداً زائداً.
        """
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
                color: str = None) -> ProgressBar:
        bar = ProgressBar(label=label, color=color or _C.get("accent"))
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