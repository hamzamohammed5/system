"""
ui/widgets/mixins/validate.py
======================================
FormValidationMixin — تحقق موحد من حقول الفورم.

التحسينات:
  - [i18n] رسائل التحقق تمر بـ tr() لدعم الترجمة.
    "أدخل {label}" و"اختر {label}" و"أدخل {label} أكبر من صفر"
    يمكن الآن ترجمتها للغات الأخرى من خلال i18n_manager.
"""
from PyQt5.QtWidgets import QLineEdit, QComboBox

from ..core.i18n import tr


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
        msg_warning(self, tr("تنبيه"), msg)

    def validate_required(self, fields: list, parent=None) -> bool:
        for widget, label in fields:
            if isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    # [i18n] رسالة "أدخل X" قابلة للترجمة
                    self._warn(tr("أدخل {label}", label=label))
                    widget.setFocus()
                    return False
            elif isinstance(widget, QComboBox):
                if widget.currentData() is None:
                    # [i18n] رسالة "اختر X" قابلة للترجمة
                    self._warn(tr("اختر {label}", label=label))
                    return False
        return True

    def validate_amount(self, spinbox, label: str = "المبلغ",
                        min_val: float = 0.01, parent=None) -> bool:
        if spinbox.value() < min_val:
            # [i18n] رسالة "أدخل X أكبر من صفر" قابلة للترجمة
            self._warn(tr("أدخل {label} أكبر من صفر", label=label))
            spinbox.setFocus()
            return False
        return True

    def validate_positive(self, value: float, label: str = "القيمة",
                          parent=None) -> bool:
        if value <= 0:
            # [i18n] رسالة "X يجب أن يكون أكبر من صفر" قابلة للترجمة
            self._warn(tr("{label} يجب أن يكون أكبر من صفر", label=label))
            return False
        return True