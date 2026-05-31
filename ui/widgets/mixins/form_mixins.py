"""
ui/widgets/mixins/form_mixins.py
=================================
دمج mixin-ين ليهم علاقة بالفورمات:
  - EditModeMixin       (كان في edit.py)
  - FormValidationMixin (كان في validate.py)

الملفات المحذوفة: edit.py, validate.py
"""

from PyQt5.QtWidgets import QLineEdit, QComboBox

from ..core.i18n import tr


# ══════════════════════════════════════════════════════════
# EditModeMixin
# ══════════════════════════════════════════════════════════

class EditModeMixin:
    """
    Mixin يدير الـ Add/Edit mode للفورمات.

    الاستخدام:
        self.init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode)
        self.enter_edit_mode(item_id, "─── تعديل: الاسم ───")
        self.exit_edit_mode("─── إضافة جديدة ───")
    """

    _editing_id: int | None = None

    def init_edit_mode(self, btn_add, btn_save, btn_cancel, lbl_mode=None):
        self._em_btn_add    = btn_add
        self._em_btn_save   = btn_save
        self._em_btn_cancel = btn_cancel
        self._em_lbl_mode   = lbl_mode
        self._set_add_state()

    def enter_edit_mode(self, item_id: int, mode_text: str = ""):
        self._editing_id = item_id
        self._em_btn_add.setVisible(False)
        self._em_btn_save.setVisible(True)
        self._em_btn_cancel.setVisible(True)
        if self._em_lbl_mode and mode_text:
            self._em_lbl_mode.setText(mode_text)

    def exit_edit_mode(self, add_text: str = ""):
        self._editing_id = None
        self._set_add_state()
        if self._em_lbl_mode and add_text:
            self._em_lbl_mode.setText(add_text)

    def _set_add_state(self):
        if hasattr(self, "_em_btn_add"):
            self._em_btn_add.setVisible(True)
            self._em_btn_save.setVisible(False)
            self._em_btn_cancel.setVisible(False)

    @property
    def is_edit_mode(self) -> bool:
        return self._editing_id is not None


# ══════════════════════════════════════════════════════════
# FormValidationMixin
# ══════════════════════════════════════════════════════════

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