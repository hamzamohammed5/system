"""
ui/widgets/theme/builders.py
=====================================
دوال بناء الـ QFrame widgets الأساسية (dividers, separators).
"""
from PyQt5.QtWidgets import QFrame
from ui.app_settings import _C


def h_divider(color: str = None, height: int = 1) -> QFrame:
    """فاصل أفقي موحد."""
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(height)
    sep.setStyleSheet(f"background:{color or _C.get('border','#e0e0e0')}; border:none;")
    return sep


def v_divider(color: str = None, width: int = 1, margin_v: int = 4) -> QFrame:
    """فاصل عمودي موحد — للـ toolbars."""
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setFixedWidth(width)
    sep.setStyleSheet(
        f"background:{color or _C.get('border_med','#bdbdbd')};"
        f"border:none; margin:{margin_v}px 2px;"
    )
    return sep