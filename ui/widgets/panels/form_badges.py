"""
ui/widgets/panels/form_badges.py
==================================
Badge & Preview widgets للفورمات.

مستخرج من panels/form_parts.py:
  ResultBadge, ModeBadge, InlinePreview, make_preview_label
"""

from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ..core.colors import status_colors


def make_preview_label(text: str = "─", status: str = "info") -> QLabel:
    s = status_colors(status)
    lbl = QLabel(text)
    base = get_font_size()
    lbl.setStyleSheet(
        f"background:{s['bg']}; border:1px solid {s['border']}; color:{s['fg']};"
        f"border-radius:6px; padding:8px 12px; font-size:{fs(base,-1)}pt;"
    )
    lbl.setWordWrap(True)
    return lbl


class ResultBadge(QLabel):
    """Label لعرض نتيجة / تكلفة محسوبة."""

    def __init__(self, text: str = "─", color: str = None,
                 status: str = "success", parent=None):
        super().__init__(text, parent)
        self._custom_color = color
        self._status       = status
        self._apply()

    def _apply(self):
        base = get_font_size()
        s = status_colors(self._status)
        if self._custom_color:
            self.setStyleSheet(
                f"color:{self._custom_color}; font-weight:bold; font-size:{fs(base,0)}pt;"
                f"background:{s['bg']}; border:1px solid {s['border']};"
                "border-radius:4px; padding:4px 8px;"
            )
        else:
            self.setStyleSheet(
                f"color:{s['fg']}; font-weight:bold; font-size:{fs(base,0)}pt;"
                f"background:{s['bg']}; border:1px solid {s['border']};"
                "border-radius:4px; padding:4px 8px;"
            )

    def set_value(self, text: str, color: str = None):
        self.setText(text)
        if color and color != self._custom_color:
            self._custom_color = color
            self._apply()

    def set_status(self, status: str):
        if status != self._status:
            self._status = status
            self._apply()

    def reset(self):
        self.setText("─")


class ModeBadge(QLabel):
    """Label لعرض الوضع الحالي مع ستايل ملون."""

    def __init__(self, text: str = "─", color: str = "blue", parent=None):
        super().__init__(text, parent)
        self._color_key = color
        self._apply_style(color)

    def _apply_style(self, color: str):
        _map = {
            "blue":   "primary",
            "orange": "warning",
            "green":  "success",
            "red":    "danger",
            "purple": "purple",
        }
        s = status_colors(_map.get(color, "info"))
        base = get_font_size()
        self.setStyleSheet(
            f"color:{s['fg']}; font-weight:bold; font-size:{fs(base,-1)}pt;"
            f"background:{s['bg']}; border:1px solid {s['border']};"
            "border-radius:4px; padding:3px 8px;"
        )

    def set_mode(self, text: str, color: str = None):
        self.setText(text)
        if color and color != self._color_key:
            self._color_key = color
            self._apply_style(color)

    def reset(self):
        self.setText("─")


class InlinePreview(QWidget):
    """يعرض: [label] [القيمة المحسوبة]"""

    def __init__(self, label: str = "النتيجة:", color: str = None,
                 status: str = "success", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color:{_C['text_sec']}; font-weight:600;"
            f"font-size:{fs(get_font_size(),-1)}pt; background:transparent;"
        )
        self._lbl_value = ResultBadge("─", color=color, status=status)
        lay.addWidget(lbl)
        lay.addWidget(self._lbl_value)
        lay.addStretch()

    def set_value(self, text: str):
        self._lbl_value.set_value(text)

    def reset(self):
        self._lbl_value.reset()