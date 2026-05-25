"""
ui/tabs/accounting/journal_tab.py
==================================
نقطة دخول موحدة — يُعيد تصدير JournalTab فقط.

التقسيم الداخلي (مجلد journal/):
  journal_account_picker.py  → _AccountTreePopup, _AccountPickerButton
  journal_lines.py           → _SmartLine, _LinesPanel
  journal_form.py            → _JournalForm
  journal_group_combo.py     → _TreeGroupCombo, _NoSelectDelegate
  journal_filter.py          → _JournalFilterBar
  journal_tree_table.py      → _JournalTreeTable
  journal_tab_widget.py      → JournalTab
"""

from .journal.journal_tab_widget import JournalTab          # noqa: F401
from .journal.journal_tree_table import _JournalTreeTable   # noqa: F401
from .journal.journal_form       import _JournalForm        # noqa: F401

__all__ = ["JournalTab", "_JournalTreeTable", "_JournalForm"]