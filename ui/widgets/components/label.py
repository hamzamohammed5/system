"""
ui/widgets/components/label.py
================================
InfoRow + ModeLabel — الـ widgets الأصلية لهذا الملف.

باقي الـ classes أصبح لها ملفات مصدر مستقلة:
  - ProgressBar, MultiProgressBar  → progress.py
  - AmountLabel, DebitCreditDisplay, BalanceDisplay,
    format_amount, amount_color, dr_cr_color         → amount_label.py

Re-exports محفوظة هنا للتوافق مع الكود القديم.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import fs, get_font_size

# ── Re-exports للتوافق مع الكود القديم ───────────────────
from .progress import ProgressBar, MultiProgressBar          # noqa: F401
from .amount_label import (                                  # noqa: F401
    AmountLabel, DebitCreditDisplay, BalanceDisplay,
    format_amount, amount_color, dr_cr_color,
)


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