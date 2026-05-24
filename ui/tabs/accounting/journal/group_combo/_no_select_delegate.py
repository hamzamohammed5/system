"""
ui/tabs/accounting/journal/group_combo/_no_select_delegate.py
==============================================================
_NoSelectDelegate — يجعل عناصر الرأس في الشجرة غير قابلة للاختيار.
مُستخرج من journal_group_combo.py.
"""

from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QStyle

_ROLE_IS_HEADER = None  # يُعرَّف في _tree_group_combo لتجنب circular import


class _NoSelectDelegate(QStyledItemDelegate):
    """يجعل عناصر الرأس غير قابلة للاختيار."""

    # القيمة تُمرر من الخارج عند الإنشاء
    def __init__(self, parent=None, is_header_role=None):
        super().__init__(parent)
        from PyQt5.QtCore import Qt
        self._is_header_role = is_header_role or (Qt.UserRole + 2)

    def paint(self, painter, option, index):
        is_header = index.data(self._is_header_role)
        if is_header:
            option.state &= ~QStyle.State_Selected
        super().paint(painter, option, index)