"""
ui/tabs/accounting/journal/journal_group_combo.py
==========================================
Facade للتوافق مع الكود القديم.

التقسيم الداخلي:
  group_combo/_no_select_delegate.py → _NoSelectDelegate
  group_combo/_tree_group_combo.py   → _TreeGroupCombo
"""

from .group_combo._no_select_delegate import _NoSelectDelegate  # noqa: F401
from .group_combo._tree_group_combo   import _TreeGroupCombo    # noqa: F401

__all__ = ["_NoSelectDelegate", "_TreeGroupCombo"]