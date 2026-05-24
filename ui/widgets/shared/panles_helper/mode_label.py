"""
ui/widgets/shared/panles_helper/mode_label.py
==============================================
ModeLabel — label الوضع الحالي الموحد لكل فورم CRUD.

يحل محل self.lbl_mode المتفرقة في كل فورم.

الاستخدام:
    self.lbl_mode = ModeLabel("إضافة جديدة")
    layout.addWidget(self.lbl_mode)

    # عند التعديل:
    self.lbl_mode.set_edit_mode("اسم العنصر")

    # عند العودة:
    self.lbl_mode.set_add_mode()
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

from ui.app_settings import _C, fs
from .colors_and_base import _base


class ModeLabel(QLabel):
    """
    Label الوضع الحالي الموحد.
    يدعم وضعين: الإضافة (أزرق) والتعديل (برتقالي).

    الاستخدام:
        lbl = ModeLabel(add_text="مستثمر جديد", icon="👤")
        form_layout.addRow(lbl)
        lbl.set_edit_mode("محمد علي")
        lbl.set_add_mode()
    """

    def __init__(self, add_text: str = "جديد",
                 icon: str = "",
                 parent=None):
        super().__init__(parent)
        self._add_text  = add_text
        self._icon      = icon
        self._is_edit   = False
        self.set_add_mode()

    def set_add_mode(self, text: str = None):
        """يضع الـ label في وضع الإضافة."""
        self._is_edit = False
        display = text or self._add_text
        prefix  = f"{self._icon}  " if self._icon else ""
        self.setText(f"─── {prefix}{display} ───")
        base = _base()
        self.setStyleSheet(
            f"font-weight: bold; font-size: {fs(base, 0)}pt;"
            f"color: {_C['accent']}; background: transparent; border: none;"
        )

    def set_edit_mode(self, name: str = ""):
        """يضع الـ label في وضع التعديل."""
        self._is_edit = True
        prefix = f"{self._icon}  " if self._icon else ""
        display = f": {name}" if name else ""
        self.setText(f"─── {prefix}تعديل{display} ───")
        base = _base()
        self.setStyleSheet(
            f"font-weight: bold; font-size: {fs(base, 0)}pt;"
            "color: #e65100; background: transparent; border: none;"
        )

    def set_custom(self, text: str, color: str = None):
        """يضع نص مخصص."""
        self.setText(text)
        base = _base()
        c = color or _C['text_sec']
        self.setStyleSheet(
            f"font-weight: bold; font-size: {fs(base, 0)}pt;"
            f"color: {c}; background: transparent; border: none;"
        )

    @property
    def is_edit_mode(self) -> bool:
        return self._is_edit