"""
ui/widgets/shared/panles_helper/form_row.py
============================================
أدوات بناء صفوف الفورم الموحدة.

تحل محل الكود المكرر في فورم إضافة/تعديل العناصر.

المتوفر:
  form_label(text)           — QLabel موحد لعنوان الحقل
  required_label(text)       — QLabel مع نجمة (*)  للحقول المطلوبة
  field_row(label, widget)   — صف فورم أفقي
  separator_line()           — خط فاصل أفقي
  hint_label(text)           — label توضيحي صغير
  make_form_layout()         — QFormLayout موحد
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
    """
    Label موحد لعنوان الحقل في الفورم.

    الاستخدام:
        form.addRow(form_label("الاسم:"), inp_name)
    """
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
    """
    Label مع نجمة حمراء للحقول المطلوبة.

    الاستخدام:
        form.addRow(required_label("الاسم:"), inp_name)
    """
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
    """
    Label توضيحي صغير للمساعدة.

    الاستخدام:
        form.addRow("", hint_label("أدخل الاسم بالعربية"))
    """
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
    """
    عنوان قسم داخل الفورم.

    الاستخدام:
        form.addRow(section_title("بيانات المنتج", icon="📦"))
    """
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
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {_C['border']}; border: none;")
    return sep


# ══════════════════════════════════════════════════════════
# صفوف الفورم
# ══════════════════════════════════════════════════════════

def field_row(label_text: str, widget: QWidget,
              required: bool = False,
              hint: str = "",
              spacing: int = 8) -> tuple:
    """
    يبني صف فورم أفقي (label + widget).
    يرجع (label, container_widget) أو (label, widget) مباشرةً.

    الاستخدام في QFormLayout:
        lbl, w = field_row("الاسم:", inp_name, required=True)
        form.addRow(lbl, w)
    """
    lbl = required_label(label_text) if required else form_label(label_text)

    if hint:
        # لو فيه hint نلف الـ widget في container مع hint تحته
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
    """
    يبني صف أفقي مع label على اليمين وwidgets على اليسار.

    مفيد لـ:
      - حقل + وحدة قياس
      - حقل + زر
      - عدة حقول في سطر واحد

    الاستخدام:
        row = labeled_row("السعر:", sp_price, QLabel("جنيه"))
        layout.addWidget(row)
    """
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
    """
    يبني QFormLayout بإعدادات موحدة.

    الاستخدام:
        form = make_form_layout()
        form.addRow(required_label("الاسم:"), inp_name)
        grp.setLayout(form)
    """
    form = QFormLayout()
    form.setSpacing(spacing)
    form.setLabelAlignment(label_align)
    form.setContentsMargins(*contents_margins)
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
    return form


# ══════════════════════════════════════════════════════════
# Preview Label (معاينة القيود/النتائج)
# ══════════════════════════════════════════════════════════

def make_preview_label(text: str = "─",
                       status: str = "info") -> QLabel:
    """
    Label معاينة موحد مع ستايل ملون.

    status: "info" | "success" | "warning" | "danger"

    الاستخدام:
        self.lbl_preview = make_preview_label()
        form.addRow("المعاينة:", self.lbl_preview)
        self.lbl_preview.setText("DR: الصندوق ← 1000 ج")
    """
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