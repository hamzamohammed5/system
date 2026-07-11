"""
ui/widgets/theme/builders.py
===============================
Widget builders — h_divider, v_divider, wrap_in_scroll.

مستخرج من theme/styles.py.
"""
from PyQt5.QtWidgets import QFrame, QScrollArea, QWidget
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.constants import SEPARATOR_LINE_H, V_DIVIDER_WIDTH, V_DIVIDER_MARGIN_V, V_DIVIDER_INNER_MARGIN_H
from .layout_styles import scroll_style


def h_divider(color: str = None, height: int = SEPARATOR_LINE_H) -> QFrame:
    """فاصل أفقي موحد."""
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(height)
    sep.setStyleSheet(f"background:{color or _C['border']}; border:none;")
    return sep


def v_divider(color: str = None, width: int = V_DIVIDER_WIDTH, margin_v: int = V_DIVIDER_MARGIN_V) -> QFrame:
    """فاصل عمودي موحد — للـ toolbars."""
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setFixedWidth(width)
    sep.setStyleSheet(
        f"background:{color or _C['border_med']};"
        f"border:none; margin:{margin_v}px {V_DIVIDER_INNER_MARGIN_H}px;"
    )
    return sep


def wrap_in_scroll(widget: QWidget,
                   min_height: int = 0,
                   horizontal: bool = False) -> QScrollArea:
    """يلف أي widget في QScrollArea موحد."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setHorizontalScrollBarPolicy(
        Qt.ScrollBarAsNeeded if horizontal else Qt.ScrollBarAlwaysOff
    )
    scroll.setStyleSheet(scroll_style())
    if min_height:
        scroll.setMinimumHeight(min_height)
    return scroll