"""
ui/widgets/mixins/validate.py
======================================
FormValidationMixin — تحقق موحد من حقول الفورم.
"""
from PyQt5.QtWidgets import QLineEdit, QComboBox


class FormValidationMixin:
    """
    Mixin يوفر دوال تحقق موحدة.

    الاستخدام:
        class MyForm(QWidget, FormValidationMixin):
            def _save(self):
                if not self.validate_required([
                    (self.inp_name, "الاسم"),
                ]):
                    return
    """

    def _warn(self, msg: str):
        # ← استخدام msg_warning الموحد بدل QMessageBox.warning
        from ..dialogs.message import msg_warning
        msg_warning(self, "تنبيه", msg)

    def validate_required(self, fields: list, parent=None) -> bool:
        for widget, label in fields:
            if isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    self._warn(f"أدخل {label}")
                    widget.setFocus()
                    return False
            elif isinstance(widget, QComboBox):
                if widget.currentData() is None:
                    self._warn(f"اختر {label}")
                    return False
        return True

    def validate_amount(self, spinbox, label: str = "المبلغ",
                        min_val: float = 0.01, parent=None) -> bool:
        if spinbox.value() < min_val:
            self._warn(f"أدخل {label} أكبر من صفر")
            spinbox.setFocus()
            return False
        return True

    def validate_positive(self, value: float, label: str = "القيمة",
                          parent=None) -> bool:
        if value <= 0:
            self._warn(f"{label} يجب أن يكون أكبر من صفر")
            return False
        return True