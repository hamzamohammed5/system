"""
ui/widgets/panels/form_parts.py
================================
أدوات بناء الفورمات الموحدة:

  form_label / required_label / hint_label / section_title
  separator_line / field_row / labeled_row
  make_form_layout / make_preview_label
  FormGroup      — QGroupBox مع QFormLayout جاهز
  ModeLabel      — label وضع الفورم (إضافة / تعديل)
  spin_field / int_spin_field / labeled_widget
  ResultBadge / ModeBadge / InlinePreview
  CrudButtonsBar — شريط أزرار CRUD موحد
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QGroupBox, QFormLayout, QDoubleSpinBox,
    QSpinBox, QSizePolicy, QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.app_settings import _C, fs, get_font_size

_STATUS_COLORS = {
    "success": {"bg": "#ecfdf5", "fg": "#065f46", "border": "#6ee7b7"},
    "warning": {"bg": "#fffbeb", "fg": "#92400e", "border": "#fcd34d"},
    "danger":  {"bg": "#fef2f2", "fg": "#991b1b", "border": "#fca5a5"},
    "info":    {"bg": "#eff6ff", "fg": "#1e40af", "border": "#93c5fd"},
}


def _base() -> int:
    return get_font_size()


def _make_btn(text: str, style: str = "normal") -> QPushButton:
    from ..panels._btn import make_btn
    return make_btn(text, style)


def _spinbox_style(height: int = 32, positive: bool = False,
                   widget: str = "QDoubleSpinBox") -> str:
    base = _base()
    if positive:
        bg, border, color, weight = "#f0fdf4", "#86efac", "#15803d", "bold"
    else:
        bg = _C["bg_input"]; border = _C["border_med"]
        color = _C["text_primary"]; weight = "normal"
    return f"""
        {widget} {{
            background:{bg}; border:1.5px solid {border};
            border-radius:6px; padding:0 8px;
            font-size:{fs(base,0)}pt; color:{color};
            font-weight:{weight}; min-height:{height}px;
        }}
        {widget}:focus {{ border-color:{_C["accent"]}; background:white; }}
        {widget}:disabled {{
            background:{_C["bg_surface_2"]}; color:{_C["text_disabled"]};
        }}
    """


# ══════════════════════════════════════════════════════════
# Label builders
# ══════════════════════════════════════════════════════════

def form_label(text: str, color: str = None) -> QLabel:
    lbl = QLabel(text)
    base = _base()
    lbl.setStyleSheet(
        f"color:{color or _C['text_sec']}; font-size:{fs(base,0)}pt; font-weight:600;"
        "background:transparent; border:none;"
    )
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl


def required_label(text: str) -> QLabel:
    base = _base()
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
    base = _base()
    lbl.setStyleSheet(
        f"color:{color or _C['text_muted']}; font-size:{fs(base,-1)}pt;"
        "background:transparent; border:none;"
    )
    lbl.setWordWrap(True)
    return lbl


def section_title(text: str, color: str = None, icon: str = "") -> QLabel:
    display = f"{icon}  {text}" if icon else text
    lbl = QLabel(display)
    base = _base()
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
    _styles = {
        "info":    f"background:#f8f9ff; border:1px solid {_C.get('border_med','#c5cae9')}; color:#333;",
        "success": "background:#f0faf0; border:1px solid #b2dfb2; color:#1a6e1a;",
        "warning": "background:#fffde7; border:1px solid #ffe082; color:#e65100;",
        "danger":  "background:#fdecea; border:1px solid #ef9a9a; color:#c62828;",
    }
    lbl = QLabel(text)
    base = _base()
    lbl.setStyleSheet(
        f"{_styles.get(status, _styles['info'])} border-radius:6px; padding:8px 12px;"
        f"font-size:{fs(base,-1)}pt;"
    )
    lbl.setWordWrap(True)
    return lbl


# ══════════════════════════════════════════════════════════
# Spin fields
# ══════════════════════════════════════════════════════════

def spin_field(max_: float = 999999, dec: int = 2,
               min_: float = 0, min_height: int = 30) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(_spinbox_style(min_height, widget="QDoubleSpinBox"))
    return s


def int_spin_field(max_: int = 9999, min_: int = 0,
                   min_height: int = 30) -> QSpinBox:
    s = QSpinBox()
    s.setRange(min_, max_)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(_spinbox_style(min_height, widget="QSpinBox"))
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
        f"font-size:{fs(_base(),-1)}pt;"
    )
    lay.addWidget(lbl)
    lay.addStretch()
    return w


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
# ModeBadge
# ══════════════════════════════════════════════════════════

class ModeBadge(QLabel):
    """Label لعرض الوضع الحالي مع ستايل ملون."""

    _COLORS = {
        "blue":   ("#e3f2fd", "#1565c0", "#90caf9"),
        "orange": (_STATUS_COLORS["warning"]["bg"], _STATUS_COLORS["warning"]["fg"], _STATUS_COLORS["warning"]["border"]),
        "green":  (_STATUS_COLORS["success"]["bg"], _STATUS_COLORS["success"]["fg"], _STATUS_COLORS["success"]["border"]),
        "red":    (_STATUS_COLORS["danger"]["bg"],  _STATUS_COLORS["danger"]["fg"],  _STATUS_COLORS["danger"]["border"]),
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

    def reset(self):
        self.setText("─")


# ══════════════════════════════════════════════════════════
# ModeLabel
# ══════════════════════════════════════════════════════════

class ModeLabel(QLabel):
    """Label وضع الفورم: أزرق = إضافة، برتقالي = تعديل."""

    def __init__(self, add_text: str = "جديد", icon: str = "", parent=None):
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
        base = _base()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            f"color:{_C['accent']}; background:transparent; border:none;"
        )

    def set_edit_mode(self, name: str = ""):
        self._is_edit = True
        prefix = f"{self._icon}  " if self._icon else ""
        suffix = f": {name}" if name else ""
        self.setText(f"─── {prefix}تعديل{suffix} ───")
        base = _base()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            "color:#e65100; background:transparent; border:none;"
        )

    def set_custom(self, text: str, color: str = None):
        self.setText(text)
        base = _base()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,0)}pt;"
            f"color:{color or _C['text_sec']}; background:transparent; border:none;"
        )

    @property
    def is_edit_mode(self) -> bool:
        return self._is_edit


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
        base = _base()
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

    def __init__(self, label: str = "النتيجة:", color: str = "#1a6e1a", parent=None):
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

        self.btn_add    = _make_btn(add_text,    "primary")
        self.btn_save   = _make_btn(save_text,   "success")
        self.btn_cancel = _make_btn(cancel_text, "ghost")

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