"""
ui/widgets/shared/form_utils.py
================================
أدوات بناء الفورم المشتركة — تُستخدم في كل أقسام التطبيق.

تحل محل الكود المتكرر في:
  machine_form.py, labor_op_form.py, machine_op_form.py,
  labor_settings.py, raw_variants_panel.py, machine_op_rows_editor.py

المتوفر:
  labeled_widget(widget, unit)     — widget + label وحدة في سطر واحد
  spin_field(max_, dec)            — QDoubleSpinBox موحد
  int_spin_field(max_)             — QSpinBox موحد
  ModeBadge                        — label لعرض الوضع الحالي (مثل وضع الحساب)
  FormGroup                        — QGroupBox موحد مع QFormLayout جاهز
  CrudButtonsBar                   — شريط أزرار إضافة/حفظ/إلغاء موحد
  build_form_row(label, widget)    — صف فورم بـ QHBoxLayout
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QSpinBox,
    QGroupBox, QFormLayout, QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base


# ══════════════════════════════════════════════════════════
# labeled_widget — widget + وحدة في سطر
# ══════════════════════════════════════════════════════════

def labeled_widget(widget: QWidget, unit: str,
                   unit_color: str = None,
                   spacing: int = 6) -> QWidget:
    """
    يلف widget مع label الوحدة في QHBoxLayout.

    الاستخدام:
        form.addRow("الراتب:", labeled_widget(sp_salary, "جنيه / شهر"))
        form.addRow("الوقت:", labeled_widget(sp_minutes, "دقيقة"))
    """
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    lay.addWidget(widget)

    lbl = QLabel(unit)
    lbl.setStyleSheet(
        f"color: {unit_color or _C['text_muted']};"
        "background: transparent; border: none;"
        f"font-size: {fs(_base(), -1)}pt;"
    )
    lay.addWidget(lbl)
    lay.addStretch()
    return w


# ══════════════════════════════════════════════════════════
# spin_field — QDoubleSpinBox موحد
# ══════════════════════════════════════════════════════════

def spin_field(max_: float = 999999,
               dec: int = 2,
               min_: float = 0,
               min_height: int = 30) -> QDoubleSpinBox:
    """
    يبني QDoubleSpinBox بإعدادات موحدة.

    الاستخدام:
        self.sp_salary = spin_field(max_=999999, dec=2)
    """
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(f"""
        QDoubleSpinBox {{
            background: {_C['bg_input']};
            border: 1.5px solid {_C['border_med']};
            border-radius: 6px;
            padding: 0 8px;
            font-size: {fs(_base(), 0)}pt;
            color: {_C['text_primary']};
        }}
        QDoubleSpinBox:focus {{
            border-color: {_C['accent']};
        }}
        QDoubleSpinBox:disabled {{
            background: {_C['bg_surface_2']};
            color: {_C['text_disabled']};
        }}
    """)
    return s


def int_spin_field(max_: int = 9999,
                   min_: int = 0,
                   min_height: int = 30) -> QSpinBox:
    """
    يبني QSpinBox بإعدادات موحدة.

    الاستخدام:
        self.sp_days = int_spin_field(max_=31)
    """
    s = QSpinBox()
    s.setRange(min_, max_)
    s.setMinimumHeight(min_height)
    s.setStyleSheet(f"""
        QSpinBox {{
            background: {_C['bg_input']};
            border: 1.5px solid {_C['border_med']};
            border-radius: 6px;
            padding: 0 8px;
            font-size: {fs(_base(), 0)}pt;
            color: {_C['text_primary']};
        }}
        QSpinBox:focus {{
            border-color: {_C['accent']};
        }}
    """)
    return s


# ══════════════════════════════════════════════════════════
# ModeBadge — label عرض الوضع الحالي
# ══════════════════════════════════════════════════════════

class ModeBadge(QLabel):
    """
    Label لعرض الوضع الحالي مع ستايل موحد.

    الاستخدام:
        self.badge_mode = ModeBadge()
        self.badge_mode.set_mode("⏱ بالوقت  │  50.00 جنيه/ساعة", color="orange")

    الألوان المتاحة: "blue" (افتراضي), "orange", "green", "red", "purple"
    """

    _COLORS = {
        "blue":   ("#e3f2fd", "#1565c0", "#90caf9"),
        "orange": ("#fff3e0", "#e65100", "#ffcc80"),
        "green":  ("#e8f5e9", "#2e7d32", "#a5d6a7"),
        "red":    ("#ffebee", "#c62828", "#ef9a9a"),
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
            f"color: {fg}; font-weight: bold; font-size: {fs(base, -1)}pt;"
            f"background: {bg}; border: 1px solid {border};"
            "border-radius: 4px; padding: 3px 8px;"
        )

    def set_mode(self, text: str, color: str = None):
        """يحدّث النص والألوان."""
        self.setText(text)
        if color and color != self._color_key:
            self._color_key = color
            self._apply_style(color)

    def set_info(self, text: str):
        """يحدّث النص فقط بدون تغيير اللون."""
        self.setText(text)

    def reset(self):
        self.setText("─")


# ══════════════════════════════════════════════════════════
# ResultBadge — label لعرض نتيجة / تكلفة محسوبة
# ══════════════════════════════════════════════════════════

class ResultBadge(QLabel):
    """
    Label لعرض تكلفة أو نتيجة محسوبة.

    الاستخدام:
        self.lbl_cost = ResultBadge()
        self.lbl_cost.set_value("50.25 جنيه / ساعة")
    """

    def __init__(self, text: str = "─", color: str = "#1a6e1a", parent=None):
        super().__init__(text, parent)
        self._color = color
        self._apply()

    def _apply(self):
        base = _base()
        self.setStyleSheet(
            f"color: {self._color}; font-weight: bold; font-size: {fs(base, 0)}pt;"
            "background: #f0faf0; border: 1px solid #b2dfb2;"
            "border-radius: 4px; padding: 4px 8px;"
        )

    def set_value(self, text: str, color: str = None):
        self.setText(text)
        if color and color != self._color:
            self._color = color
            self._apply()

    def reset(self):
        self.setText("─")


# ══════════════════════════════════════════════════════════
# FormGroup — QGroupBox موحد مع QFormLayout
# ══════════════════════════════════════════════════════════

class FormGroup(QGroupBox):
    """
    QGroupBox مع QFormLayout جاهز وستايل موحد.

    الاستخدام:
        grp = FormGroup("بيانات الماكينة")
        grp.add_row("الاسم:", self.inp_name)
        grp.add_row("المعدل:", labeled_widget(self.sp_rate, "جنيه/ساعة"))
        layout.addWidget(grp)

    يمكن الوصول للـ layout عبر grp.form
    """

    def __init__(self, title: str = "", accent: str = None, parent=None):
        super().__init__(title, parent)
        self._accent = accent or _C['accent']
        self._build_style()
        self.form = QFormLayout(self)
        self.form.setSpacing(10)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setContentsMargins(12, 14, 12, 12)

    def _build_style(self):
        base = _base()
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 700;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_sec']};
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
                color: {self._accent};
            }}
        """)

    def add_row(self, label: str, widget: QWidget):
        """يضيف صف للفورم."""
        self.form.addRow(label, widget)

    def add_label_row(self, label_widget: QWidget):
        """يضيف label كامل العرض (بدون label يمين)."""
        self.form.addRow(label_widget)

    def add_separator(self):
        """يضيف فاصل أفقي."""
        from ui.widgets.shared.panles_helper.divider_utils import make_divider
        self.form.addRow(make_divider())


# ══════════════════════════════════════════════════════════
# CrudButtonsBar — شريط أزرار CRUD موحد
# ══════════════════════════════════════════════════════════

class CrudButtonsBar(QWidget):
    """
    شريط أزرار موحد: إضافة / حفظ / إلغاء + label الوضع.

    يعمل مع EditModeMixin من ui.helpers.

    الاستخدام:
        self._crud = CrudButtonsBar(add_text="➕ إضافة", save_text="💾 حفظ")
        layout.addWidget(self._crud)

        # ربط:
        self.init_edit_mode(
            self._crud.btn_add,
            self._crud.btn_save,
            self._crud.btn_cancel,
            self._crud.lbl_mode
        )

    Signals:
        add_clicked    → زر الإضافة
        save_clicked   → زر الحفظ
        cancel_clicked → زر الإلغاء
    """

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
        self.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(6)

        if show_mode:
            self.lbl_mode = QLabel("─── إضافة جديدة ───")
            self.lbl_mode.setStyleSheet(
                f"font-weight: bold; color: {_C['accent']}; background: transparent;"
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

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        if not show_mode:
            self.lbl_mode = QLabel()  # dummy — للتوافق مع EditModeMixin

    def _make_btn(self, text: str, style: str) -> QPushButton:
        from ui.widgets.shared.panles_helper.make_btn import _make_btn
        return _make_btn(text, style)

    def set_mode_text(self, text: str):
        self.lbl_mode.setText(text)


# ══════════════════════════════════════════════════════════
# InlinePreview — صف معاينة حية (تكلفة / نتيجة)
# ══════════════════════════════════════════════════════════

class InlinePreview(QWidget):
    """
    يعرض: [أيقونة] [label] [القيمة المحسوبة]
    مفيد للمعاينة الحية في الفورم.

    الاستخدام:
        self.preview = InlinePreview("التكلفة المتوقعة:")
        form.addRow(self.preview)
        self.preview.set_value("50.25 جنيه")
    """

    def __init__(self, label: str = "النتيجة:",
                 color: str = "#1a6e1a", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {_C['text_sec']}; font-weight: 600;"
            f"font-size: {fs(_base(), -1)}pt; background: transparent;"
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
# build_inner_scroll — wrapper موحد لبناء form بـ scroll
# ══════════════════════════════════════════════════════════

def build_inner_scroll(parent_widget: QWidget,
                       min_width: int = 280) -> tuple:
    """
    يبني الهيكل الأساسي لأي form panel بـ scroll.

    Returns: (outer_layout, inner_widget, inner_layout)

    الاستخدام:
        outer, inner, lay = build_inner_scroll(self, min_width=280)
        grp = FormGroup("بيانات")
        lay.addWidget(grp)
        lay.addStretch()
    """
    from ui.widgets.shared.scrollable_form import wrap_in_scroll

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