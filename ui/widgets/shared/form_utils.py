"""
ui/widgets/shared/form_utils.py

التغييرات:
  - spin_field و int_spin_field يستخدمان _spinbox_style من input_widgets
    بدل تعريف نفس الـ QDoubleSpinBox stylesheet من جديد
  - FormGroup._build_style يستخدم get_group_box_style من theme (كان موجود، مُوحَّد)
  - build_inner_scroll مستوردة من scrollable_form (لا تكرار)
  - ModeBadge._COLORS: ألوان بتستخدم STATUS_COLORS لو متطابقة،
    وإلا بتفضل كما هي (success/warning/danger)
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QSpinBox,
    QGroupBox, QFormLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base
from ui.widgets.shared.panles_helper.theme import STATUS_COLORS

from ui.widgets.shared.scrollable_form import wrap_in_scroll  # noqa: F401

# stylesheet مشترك مع AmountSpinBox في input_widgets
from ui.widgets.shared.input_widgets import _spinbox_style


# ══════════════════════════════════════════════════════════
# labeled_widget
# ══════════════════════════════════════════════════════════

def labeled_widget(widget: QWidget, unit: str,
                   unit_color: str = None,
                   spacing: int = 6) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    lay.addWidget(widget)

    lbl = QLabel(unit)
    lbl.setStyleSheet(
        f"color:{unit_color or _C['text_muted']};"
        "background:transparent; border:none;"
        f"font-size:{fs(_base(),-1)}pt;"
    )
    lay.addWidget(lbl)
    lay.addStretch()
    return w


# ══════════════════════════════════════════════════════════
# spin_field / int_spin_field — يستخدمان _spinbox_style المشتركة
# ══════════════════════════════════════════════════════════

def spin_field(max_: float = 999999,
               dec: int = 2,
               min_: float = 0,
               min_height: int = 30) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(_spinbox_style(min_height, widget="QDoubleSpinBox"))
    return s


def int_spin_field(max_: int = 9999,
                   min_: int = 0,
                   min_height: int = 30) -> QSpinBox:
    s = QSpinBox()
    s.setRange(min_, max_)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(_spinbox_style(min_height, widget="QSpinBox"))
    return s


# ══════════════════════════════════════════════════════════
# ModeBadge — يستخدم STATUS_COLORS للألوان المتطابقة
# ══════════════════════════════════════════════════════════

class ModeBadge(QLabel):
    """Label لعرض الوضع الحالي مع ستايل موحد."""

    # الألوان المخصصة (blue/purple ليست في STATUS_COLORS بنفس المعنى)
    _COLORS = {
        "blue":   ("#e3f2fd", "#1565c0", "#90caf9"),
        "orange": (
            STATUS_COLORS["warning"]["bg"],
            STATUS_COLORS["warning"]["fg"],
            STATUS_COLORS["warning"]["border"],
        ),
        "green": (
            STATUS_COLORS["success"]["bg"],
            STATUS_COLORS["success"]["fg"],
            STATUS_COLORS["success"]["border"],
        ),
        "red": (
            STATUS_COLORS["danger"]["bg"],
            STATUS_COLORS["danger"]["fg"],
            STATUS_COLORS["danger"]["border"],
        ),
        "purple": ("#f3e5f5", "#6a1b9a", "#ce93d8"),
    }

    def __init__(self, text: str = "─", color: str = "blue", parent=None):
        super().__init__(text, parent)
        self._color_key = color
        self._apply_style(color)

    def _apply_style(self, color: str):
        bg, fg, border = self._COLORS.get(color, self._COLORS["blue"])
        base = _base()
        self.setStyleSheet(
            f"color:{fg}; font-weight:bold; font-size:{fs(base,-1)}pt;"
            f"background:{bg}; border:1px solid {border};"
            "border-radius:4px; padding:3px 8px;"
        )

    def set_mode(self, text: str, color: str = None):
        self.setText(text)
        if color and color != self._color_key:
            self._color_key = color
            self._apply_style(color)

    def set_info(self, text: str):
        self.setText(text)

    def reset(self):
        self.setText("─")


# ══════════════════════════════════════════════════════════
# ResultBadge
# ══════════════════════════════════════════════════════════

class ResultBadge(QLabel):
    """Label لعرض نتيجة / تكلفة محسوبة."""

    def __init__(self, text: str = "─", color: str = "#1a6e1a", parent=None):
        super().__init__(text, parent)
        self._color = color
        self._apply()

    def _apply(self):
        base = _base()
        self.setStyleSheet(
            f"color:{self._color}; font-weight:bold; font-size:{fs(base,0)}pt;"
            "background:#f0faf0; border:1px solid #b2dfb2;"
            "border-radius:4px; padding:4px 8px;"
        )

    def set_value(self, text: str, color: str = None):
        self.setText(text)
        if color and color != self._color:
            self._color = color
            self._apply()

    def reset(self):
        self.setText("─")


# ══════════════════════════════════════════════════════════
# FormGroup
# ══════════════════════════════════════════════════════════

class FormGroup(QGroupBox):
    """QGroupBox مع QFormLayout جاهز وستايل موحد."""

    def __init__(self, title: str = "", accent: str = None, parent=None):
        super().__init__(title, parent)
        self._accent = accent or _C["accent"]
        from ui.widgets.shared.panles_helper.theme import get_group_box_style
        self.setStyleSheet(get_group_box_style(self._accent))
        self.form = QFormLayout(self)
        self.form.setSpacing(10)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setContentsMargins(12, 14, 12, 12)

    def add_row(self, label: str, widget: QWidget):
        self.form.addRow(label, widget)

    def add_label_row(self, label_widget: QWidget):
        self.form.addRow(label_widget)

    def add_separator(self):
        from ui.widgets.shared.panles_helper.divider_utils import make_divider
        self.form.addRow(make_divider())


# ══════════════════════════════════════════════════════════
# CrudButtonsBar
# ══════════════════════════════════════════════════════════

class CrudButtonsBar(QWidget):
    """شريط أزرار موحد: إضافة / حفظ / إلغاء + label الوضع."""

    add_clicked    = pyqtSignal()
    save_clicked   = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(self,
                 add_text: str    = "➕  إضافة",
                 save_text: str   = "💾  حفظ التعديل",
                 cancel_text: str = "✖  إلغاء",
                 show_mode: bool  = True,
                 parent=None):
        super().__init__(parent)
        self._build(add_text, save_text, cancel_text, show_mode)

    def _build(self, add_text, save_text, cancel_text, show_mode):
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(6)

        if show_mode:
            self.lbl_mode = QLabel("─── إضافة جديدة ───")
            self.lbl_mode.setStyleSheet(
                f"font-weight:bold; color:{_C['accent']}; background:transparent;"
            )
            lay.addWidget(self.lbl_mode)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_add    = self._make_btn(add_text,    "primary")
        self.btn_save   = self._make_btn(save_text,   "success")
        self.btn_cancel = self._make_btn(cancel_text, "ghost")

        self.btn_add.clicked.connect(self.add_clicked.emit)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)

        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        if not show_mode:
            self.lbl_mode = QLabel()

    @staticmethod
    def _make_btn(text: str, style: str) -> QPushButton:
        from ui.widgets.shared.panles_helper.make_btn import _make_btn
        return _make_btn(text, style)

    def set_mode_text(self, text: str):
        self.lbl_mode.setText(text)


# ══════════════════════════════════════════════════════════
# InlinePreview
# ══════════════════════════════════════════════════════════

class InlinePreview(QWidget):
    """يعرض: [label] [القيمة المحسوبة]"""

    def __init__(self, label: str = "النتيجة:",
                 color: str = "#1a6e1a", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color:{_C['text_sec']}; font-weight:600;"
            f"font-size:{fs(_base(),-1)}pt; background:transparent;"
        )
        self._lbl_value = ResultBadge("─", color=color)

        lay.addWidget(lbl)
        lay.addWidget(self._lbl_value)
        lay.addStretch()

    def set_value(self, text: str):
        self._lbl_value.set_value(text)

    def reset(self):
        self._lbl_value.reset()


# ══════════════════════════════════════════════════════════
# build_inner_scroll
# ══════════════════════════════════════════════════════════

def build_inner_scroll(parent_widget: QWidget,
                       min_width: int = 280) -> tuple:
    """يبني الهيكل الأساسي لأي form panel بـ scroll."""
    outer = QVBoxLayout(parent_widget)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    inner = QWidget()
    inner.setMinimumWidth(min_width)
    inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    scroll = wrap_in_scroll(inner)
    outer.addWidget(scroll)

    lay = QVBoxLayout(inner)
    lay.setSpacing(10)
    lay.setContentsMargins(12, 12, 12, 12)

    return outer, inner, lay