"""
ui/widgets/shared/mixins/validate.py
======================================
FormValidationMixin — تحقق موحد من حقول الفورم.
"""
from PyQt5.QtWidgets import QMessageBox, QLineEdit, QComboBox


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

    def validate_required(self, fields: list, parent=None) -> bool:
        p = parent or self
        for widget, label in fields:
            if isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    QMessageBox.warning(p, "تنبيه", f"أدخل {label}")
                    widget.setFocus()
                    return False
            elif isinstance(widget, QComboBox):
                if widget.currentData() is None:
                    QMessageBox.warning(p, "تنبيه", f"اختر {label}")
                    return False
        return True

    def validate_amount(self, spinbox, label: str = "المبلغ",
                        min_val: float = 0.01, parent=None) -> bool:
        p = parent or self
        if spinbox.value() < min_val:
            QMessageBox.warning(p, "تنبيه", f"أدخل {label} أكبر من صفر")
            spinbox.setFocus()
            return False
        return True

    def validate_positive(self, value: float, label: str = "القيمة",
                          parent=None) -> bool:
        p = parent or self
        if value <= 0:
            QMessageBox.warning(p, "تنبيه", f"{label} يجب أن يكون أكبر من صفر")
            return False
        return True