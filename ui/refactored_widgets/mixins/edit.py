"""
ui/widgets/shared/mixins/edit.py
==================================
EditModeMixin — إدارة وضع الإضافة/التعديل في الفورمات.
"""


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