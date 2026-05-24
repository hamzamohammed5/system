"""
ui/widgets/shared/panles_helper/form_row.py
============================================
أدوات بناء صفوف الفورم الموحدة.

[تحديث]: separator_line() تستخدم make_divider() من divider_utils.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QFormLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.app_settings import _C, fs
from .colors_and_base import _base


# ══════════════════════════════════════════════════════════
# Labels
# ══════════════════════════════════════════════════════════

def form_label(text: str, color: str = None) -> QLabel:
    lbl = QLabel(text)
    base = _base()
    c = color or _C['text_sec']
    lbl.setStyleSheet(
        f"color: {c}; font-size: {fs(base, 0)}pt; font-weight: 600;"
        "background: transparent; border: none;"
    )
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl


def required_label(text: str) -> QLabel:
    base = _base()
    lbl  = QLabel(f"<span style='color:#c62828;'>*</span> {text}")
    lbl.setStyleSheet(
        f"font-size: {fs(base, 0)}pt; font-weight: 600;"
        f"color: {_C['text_sec']}; background: transparent; border: none;"
    )
    lbl.setTextFormat(Qt.RichText)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl


def hint_label(text: str, color: str = None) -> QLabel:
    lbl = QLabel(text)
    base = _base()
    c = color or _C['text_muted']
    lbl.setStyleSheet(
        f"color: {c}; font-size: {fs(base, -1)}pt;"
        "background: transparent; border: none;"
    )
    lbl.setWordWrap(True)
    return lbl


def section_title(text: str, color: str = None,
                  icon: str = "") -> QLabel:
    display = f"{icon}  {text}" if icon else text
    lbl = QLabel(display)
    base = _base()
    c = color or _C['accent']
    lbl.setStyleSheet(
        f"font-weight: 700; font-size: {fs(base, 0)}pt; color: {c};"
        "background: transparent; border: none;"
    )
    return lbl


# ══════════════════════════════════════════════════════════
# Separators
# ══════════════════════════════════════════════════════════

def separator_line() -> QFrame:
    """خط فاصل أفقي داخل الفورم."""
    from ui.widgets.shared.panles_helper.divider_utils import make_divider
    return make_divider()


# ══════════════════════════════════════════════════════════
# صفوف الفورم
# ══════════════════════════════════════════════════════════

def field_row(label_text: str, widget: QWidget,
              required: bool = False,
              hint: str = "",
              spacing: int = 8) -> tuple:
    lbl = required_label(label_text) if required else form_label(label_text)

    if hint:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(widget)
        lay.addWidget(hint_label(hint))
        return lbl, container

    return lbl, widget


def labeled_row(label_text: str, *widgets,
                spacing: int = 6) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)

    lbl = form_label(label_text)
    lay.addWidget(lbl)

    for widget in widgets:
        if widget is None:
            continue
        if isinstance(widget, str):
            lay.addWidget(hint_label(widget))
        else:
            lay.addWidget(widget)

    lay.addStretch()
    return w


# ══════════════════════════════════════════════════════════
# QFormLayout موحد
# ══════════════════════════════════════════════════════════

def make_form_layout(spacing: int = 10,
                     label_align: int = Qt.AlignRight | Qt.AlignVCenter,
                     contents_margins: tuple = (12, 10, 12, 10)) -> QFormLayout:
    form = QFormLayout()
    form.setSpacing(spacing)
    form.setLabelAlignment(label_align)
    form.setContentsMargins(*contents_margins)
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
    return form


# ══════════════════════════════════════════════════════════
# Preview Label
# ══════════════════════════════════════════════════════════

def make_preview_label(text: str = "─",
                       status: str = "info") -> QLabel:
    _styles = {
        "info":    f"background: #f8f9ff; border: 1px solid {_C.get('border_med', '#c5cae9')}; color: #333;",
        "success": "background: #f0faf0; border: 1px solid #b2dfb2; color: #1a6e1a;",
        "warning": "background: #fffde7; border: 1px solid #ffe082; color: #e65100;",
        "danger":  "background: #fdecea; border: 1px solid #ef9a9a; color: #c62828;",
    }
    lbl = QLabel(text)
    base = _base()
    style = _styles.get(status, _styles["info"])
    lbl.setStyleSheet(
        f"{style} border-radius: 6px; padding: 8px 12px;"
        f"font-size: {fs(base, -1)}pt;"
    )
    lbl.setWordWrap(True)
    return lbl