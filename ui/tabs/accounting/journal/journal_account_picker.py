"""
ui/tabs/accounting/journal/journal_account_picker.py
=====================================================
Facade للتوافق مع الكود القديم.

التقسيم الداخلي:
  account_picker/_account_tree_popup.py    → _AccountTreePopup
  account_picker/_account_picker_button.py → _AccountPickerButton
"""

from .account_picker._account_tree_popup    import _AccountTreePopup     # noqa: F401
from .account_picker._account_picker_button import _AccountPickerButton  # noqa: F401

__all__ = ["_AccountTreePopup", "_AccountPickerButton"]