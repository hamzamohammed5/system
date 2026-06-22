"""
ui/widgets/panels/form_labels.py
"""
from PyQt5.QtWidgets import QLabel, QFrame
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import SEPARATOR_LINE_H


# ── FormLabel ─────────────────────────────────────────────

class _FormLabel(QLabel, WidgetMixin):
    def __init__(self, text: str, color: str = None):
        super().__init__(text)
        self._color = color
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(
            f"color:{self._color or _C['text_sec']}; font-size:{fs(base,0)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )


def form_label(text: str, color: str = None) -> QLabel:
    return _FormLabel(text, color)


# ── RequiredLabel ─────────────────────────────────────────

class _RequiredLabel(QLabel, WidgetMixin):
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self.setTextFormat(Qt.RichText)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setText(f"<span style='color:{_C['danger']};'>*</span> {self._text}")
        self.setStyleSheet(
            f"font-size:{fs(base,0)}pt; font-weight:600;"
            f"color:{_C['text_sec']}; background:transparent; border:none;"
        )


def required_label(text: str) -> QLabel:
    return _RequiredLabel(text)


# ── HintLabel ─────────────────────────────────────────────

class _HintLabel(QLabel, WidgetMixin):
    def __init__(self, text: str, color: str = None):
        super().__init__(text)
        self._color = color
        self.setWordWrap(True)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(
            f"color:{self._color or _C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )


def hint_label(text: str, color: str = None) -> QLabel:
    return _HintLabel(text, color)


# ── SectionTitle ──────────────────────────────────────────

class _SectionTitle(QLabel, WidgetMixin):
    def __init__(self, text: str, color: str = None, icon: str = ""):
        display = f"{icon}  {text}" if icon else text
        super().__init__(display)
        self._color = color
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,0)}pt; color:{self._color or _C['accent']};"
            "background:transparent; border:none;"
        )


def section_title(text: str, color: str = None, icon: str = "") -> QLabel:
    return _SectionTitle(text, color, icon)


# ── SeparatorLine ─────────────────────────────────────────

class _SeparatorLine(QFrame, WidgetMixin):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(SEPARATOR_LINE_H)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(f"background:{_C['border']}; border:none;")


def separator_line() -> QFrame:
    return _SeparatorLine()