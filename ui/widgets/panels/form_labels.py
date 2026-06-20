"""
ui/widgets/panels/form_labels.py
==================================
Label builders للفورمات.

مستخرج من panels/form_parts.py:
  form_label, required_label, hint_label, section_title, separator_line
"""

from PyQt5.QtWidgets import QLabel, QFrame
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs


def form_label(text: str, color: str = None) -> QLabel:
    lbl = QLabel(text)
    base = get_font_size()
    lbl.setStyleSheet(
        f"color:{color or _C['text_sec']}; font-size:{fs(base,0)}pt; font-weight:600;"
        "background:transparent; border:none;"
    )
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl


def required_label(text: str) -> QLabel:
    base = get_font_size()
    lbl = QLabel(f"<span style='color:{_C["danger"]};'>*</span> {text}")
    lbl.setStyleSheet(
        f"font-size:{fs(base,0)}pt; font-weight:600;"
        f"color:{_C['text_sec']}; background:transparent; border:none;"
    )
    lbl.setTextFormat(Qt.RichText)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl


def hint_label(text: str, color: str = None) -> QLabel:
    lbl = QLabel(text)
    base = get_font_size()
    lbl.setStyleSheet(
        f"color:{color or _C['text_muted']}; font-size:{fs(base,-1)}pt;"
        "background:transparent; border:none;"
    )
    lbl.setWordWrap(True)
    return lbl


def section_title(text: str, color: str = None, icon: str = "") -> QLabel:
    display = f"{icon}  {text}" if icon else text
    lbl = QLabel(display)
    base = get_font_size()
    lbl.setStyleSheet(
        f"font-weight:700; font-size:{fs(base,0)}pt; color:{color or _C['accent']};"
        "background:transparent; border:none;"
    )
    return lbl


def separator_line() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background:{_C['border']}; border:none;")
    return sep