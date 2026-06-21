"""
ui/widgets/panels/form_labels.py
"""
import weakref

from PyQt5.QtWidgets import QLabel, QFrame
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ui.widgets.core.events import bus
from ui.widgets.core.widget_mixin import ThemeRefreshMixin


def _connect_theme_refresh(widget, slot) -> None:
    _weak = weakref.ref(widget)

    def _on_theme_changed(_theme_name=None):
        obj = _weak()
        if obj is not None:
            slot(obj)

    widget._theme_refresh_slot = _on_theme_changed
    bus.theme_changed.connect(widget._theme_refresh_slot, Qt.UniqueConnection)


# ── FormLabel ─────────────────────────────────────────────

class _FormLabel(QLabel, ThemeRefreshMixin):
    def __init__(self, text: str, color: str = None):
        super().__init__(text)
        self._color = color
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._init_theme_refresh()
        self._refresh_style()
        _connect_theme_refresh(self, _FormLabel._refresh_style)

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(
            f"color:{self._color or _C['text_sec']}; font-size:{fs(base,0)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )


def form_label(text: str, color: str = None) -> QLabel:
    return _FormLabel(text, color)


# ── RequiredLabel ─────────────────────────────────────────

class _RequiredLabel(QLabel):
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self.setTextFormat(Qt.RichText)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._refresh_style()
        _connect_theme_refresh(self, _RequiredLabel._refresh_style)

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

class _HintLabel(QLabel):
    def __init__(self, text: str, color: str = None):
        super().__init__(text)
        self._color = color
        self.setWordWrap(True)
        self._refresh_style()
        _connect_theme_refresh(self, _HintLabel._refresh_style)

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(
            f"color:{self._color or _C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )


def hint_label(text: str, color: str = None) -> QLabel:
    return _HintLabel(text, color)


# ── SectionTitle ──────────────────────────────────────────

class _SectionTitle(QLabel):
    def __init__(self, text: str, color: str = None, icon: str = ""):
        display = f"{icon}  {text}" if icon else text
        super().__init__(display)
        self._color = color
        self._refresh_style()
        _connect_theme_refresh(self, _SectionTitle._refresh_style)

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,0)}pt; color:{self._color or _C['accent']};"
            "background:transparent; border:none;"
        )


def section_title(text: str, color: str = None, icon: str = "") -> QLabel:
    return _SectionTitle(text, color, icon)


# ── SeparatorLine ─────────────────────────────────────────

class _SeparatorLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self._refresh_style()
        _connect_theme_refresh(self, _SeparatorLine._refresh_style)

    def _refresh_style(self, *_):
        self.setStyleSheet(f"background:{_C['border']}; border:none;")


def separator_line() -> QFrame:
    return _SeparatorLine()