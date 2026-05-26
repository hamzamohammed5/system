"""
ui/widgets/panels/form_parts.py
================================
أدوات بناء الفورمات الموحدة:

  form_label / required_label / hint_label / section_title
  separator_line / field_row / labeled_row
  make_form_layout / make_preview_label
  FormGroup      — QGroupBox مع QFormLayout جاهز
  spin_field / int_spin_field / labeled_widget
  ResultBadge / ModeBadge / InlinePreview
  CrudButtonsBar — شريط أزرار CRUD موحد

  ModeLabel — مستوردة من components/label (مصدر واحد)
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QGroupBox, QFormLayout, QDoubleSpinBox,
    QSpinBox, QSizePolicy, QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.app_settings import _C, fs, get_font_size
from ..components.button import make_btn
from ..theme.styles      import spinbox_style       # المصدر الوحيد — لا تكرار
from ..core.colors       import status_colors       # المصدر الوحيد — لا _STATUS_COLORS محلية

# ModeLabel مصدرها الوحيد components/label — re-export للتوافق
from ..components.label import ModeLabel  # noqa: F401


# ══════════════════════════════════════════════════════════
# Label builders
# ══════════════════════════════════════════════════════════

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
    lbl = QLabel(f"<span style='color:#c62828;'>*</span> {text}")
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


# ══════════════════════════════════════════════════════════
# Row builders
# ══════════════════════════════════════════════════════════

def field_row(label_text: str, widget: QWidget,
              required: bool = False, hint: str = "") -> tuple:
    lbl = required_label(label_text) if required else form_label(label_text)
    if hint:
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(widget)
        lay.addWidget(hint_label(hint))
        return lbl, container
    return lbl, widget


def labeled_row(label_text: str, *widgets, spacing: int = 6) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    lay.addWidget(form_label(label_text))
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
# make_form_layout / make_preview_label
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


# ══════════════════════════════════════════════════════════
# Spin fields — يستخدم spinbox_style من theme/styles
# ══════════════════════════════════════════════════════════

def spin_field(max_: float = 999999, dec: int = 2,
               min_: float = 0, min_height: int = 30) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(spinbox_style(min_height, widget="QDoubleSpinBox"))
    return s


def int_spin_field(max_: int = 9999, min_: int = 0,
                   min_height: int = 30) -> QSpinBox:
    s = QSpinBox()
    s.setRange(min_, max_)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(spinbox_style(min_height, widget="QSpinBox"))
    return s


def labeled_widget(widget: QWidget, unit: str,
                   unit_color: str = None, spacing: int = 6) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    lay.addWidget(widget)
    lbl = QLabel(unit)
    lbl.setStyleSheet(
        f"color:{unit_color or _C['text_muted']}; background:transparent; border:none;"
        f"font-size:{fs(get_font_size(),-1)}pt;"
    )
    lay.addWidget(lbl)
    lay.addStretch()
    return w


# ══════════════════════════════════════════════════════════
# ResultBadge — يستخدم status_colors بدل hardcoded
# ══════════════════════════════════════════════════════════

class ResultBadge(QLabel):
    """
    Label لعرض نتيجة / تكلفة محسوبة.
    يستخدم status_colors من core/colors — لا hardcoded.
    """

    def __init__(self, text: str = "─", color: str = None,
                 status: str = "success", parent=None):
        super().__init__(text, parent)
        # color يأخذ الأولوية لو مُعطى — وإلا نستخدم status_colors
        self._custom_color = color
        self._status       = status
        self._apply()

    def _apply(self):
        base = get_font_size()
        if self._custom_color:
            # استخدام اللون المخصص مع خلفية خضراء فاتحة افتراضية
            s = status_colors(self._status)
            self.setStyleSheet(
                f"color:{self._custom_color}; font-weight:bold; font-size:{fs(base,0)}pt;"
                f"background:{s['bg']}; border:1px solid {s['border']};"
                "border-radius:4px; padding:4px 8px;"
            )
        else:
            s = status_colors(self._status)
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
        """يغير الـ status (success/warning/danger/info) ويعيد رسم الستايل."""
        if status != self._status:
            self._status = status
            self._apply()

    def reset(self):
        self.setText("─")


# ══════════════════════════════════════════════════════════
# ModeBadge
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# FormGroup
# ══════════════════════════════════════════════════════════

class FormGroup(QGroupBox):
    """QGroupBox مع QFormLayout جاهز وستايل موحد."""

    def __init__(self, title: str = "", accent: str = None, parent=None):
        super().__init__(title, parent)
        self._accent = accent or _C["accent"]
        self._apply_style()
        self.form = QFormLayout(self)
        self.form.setSpacing(10)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setContentsMargins(12, 14, 12, 12)

    def _apply_style(self):
        base = get_font_size()
        color = self._accent
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight:700; font-size:{fs(base,0)}pt;
                color:{_C['text_sec']}; background:{_C['bg_surface']};
                border:1px solid {_C['border']}; border-radius:10px;
                margin-top:10px; padding-top:6px;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; subcontrol-position:top right;
                padding:0 8px; color:{color};
            }}
        """)

    def add_row(self, label: str, widget: QWidget):
        self.form.addRow(label, widget)

    def add_label_row(self, label_widget: QWidget):
        self.form.addRow(label_widget)

    def add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        self.form.addRow(sep)


# ══════════════════════════════════════════════════════════
# InlinePreview
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# CrudButtonsBar
# ══════════════════════════════════════════════════════════

class CrudButtonsBar(QWidget):
    """شريط أزرار موحد: إضافة / حفظ / إلغاء + label الوضع."""

    add_clicked    = pyqtSignal()
    save_clicked   = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(self, add_text: str = "➕  إضافة",
                 save_text: str = "💾  حفظ التعديل",
                 cancel_text: str = "✖  إلغاء",
                 show_mode: bool = True, parent=None):
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

        self.btn_add    = make_btn(add_text,    "primary")
        self.btn_save   = make_btn(save_text,   "success")
        self.btn_cancel = make_btn(cancel_text, "ghost")

        self.btn_add.clicked.connect(self.add_clicked.emit)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)

        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        if not show_mode:
            self.lbl_mode = QLabel()

    def set_mode_text(self, text: str):
        self.lbl_mode.setText(text)