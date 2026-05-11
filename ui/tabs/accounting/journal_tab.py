"""
ui/tabs/accounting/journal_tab.py
==================================
نقطة دخول موحدة — يُعيد تصدير JournalTab فقط.

التقسيم الداخلي:
  journal_account_picker.py  → _AccountTreePopup, _AccountPickerButton
  journal_lines.py           → _SmartLine, _LinesPanel
  journal_form.py            → _JournalForm
  journal_group_combo.py     → _TreeGroupCombo, _NoSelectDelegate
  journal_filter.py          → _JournalFilterBar
  journal_tree_table.py      → _JournalTreeTable, JournalTab
"""

from .journal_tree_table import JournalTab, _JournalTreeTable  # noqa: F401
from .journal_form       import _JournalForm                   # noqa: F401