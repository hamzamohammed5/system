"""
ui/tabs/accounting/tree/_tree_headers.py
========================================
دوال بناء رؤوس أقسام شجرة الحسابات.

مستخرجة من _tree_builder.py لتقليل حجم الملف.

المتوفر:
  add_type_header(tree_widget, acc_type, nodes, conn) → يضيف عقدة رأسية
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_schema import TYPE_AR
from ui.tabs.accounting.helpers import TYPE_COLORS
from ui.theme import _C
from ._tree_nodes import add_acc_nodes


def add_type_header(tree_widget: QTreeWidget, acc_type: str, nodes: list,
                    conn) -> QTreeWidgetItem:
    """يضيف عقدة رأسية لنوع حساب مستقل."""
    type_item = QTreeWidgetItem()
    type_item.setText(1, f"── {TYPE_AR.get(acc_type, acc_type)} ──")
    type_item.setForeground(1, QColor(TYPE_COLORS.get(acc_type, _C["text_primary"])))
    f = type_item.font(1)
    f.setBold(True)
    type_item.setFont(1, f)
    type_item.setFlags(type_item.flags() & ~Qt.ItemIsSelectable)
    tree_widget.addTopLevelItem(type_item)
    add_acc_nodes(conn, tree_widget, nodes, type_item)
    type_item.setExpanded(True)
    return type_item