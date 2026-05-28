"""
ui/widgets/mixins/validate.py
======================================
FormValidationMixin — تحقق موحد من حقول الفورم.

التحسينات:
  - [i18n] رسائل التحقق تستخدم مفاتيح الترجمة من i18n.py
    بدل النصوص العربية المباشرة.
    "enter_field", "select_field", "field_positive", "field_positive_enter"
    يمكن الآن ترجمتها للغات الأخرى.
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
                    (self.inp_name, tr("name")),
                ]):
                    return
    """

    def _warn(self, msg: str):
        from ..dialogs.message import msg_warning
        msg_warning(self, tr("warning"), msg)

    def validate_required(self, fields: list, parent=None) -> bool:
        for widget, label in fields:
            if isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    self._warn(tr("enter_field", label=label))
                    widget.setFocus()
                    return False
            elif isinstance(widget, QComboBox):
                if widget.currentData() is None:
                    self._warn(tr("select_field", label=label))
                    return False
        return True

    def validate_amount(self, spinbox, label: str = "",
                        min_val: float = 0.01, parent=None) -> bool:
        _label = label or tr("amount")
        if spinbox.value() < min_val:
            self._warn(tr("field_positive_enter", label=_label))
            spinbox.setFocus()
            return False
        return True

    def validate_positive(self, value: float, label: str = "",
                          parent=None) -> bool:
        _label = label or tr("amount")
        if value <= 0:
            self._warn(tr("field_positive", label=_label))
            return False
        return True