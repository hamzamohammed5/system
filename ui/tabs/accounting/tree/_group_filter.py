"""
ui/tabs/accounting/tree/_group_filter.py
==================================================
_GroupFilterCombo — Combo فلتر التصنيفات في شجرة الحسابات.
"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import fetch_all_groups, build_group_tree
from ui.tabs.accounting.helpers import TYPE_COLORS


class _GroupFilterCombo(QComboBox):
    """Combo لفلترة الحسابات بالتصنيف."""

    def __init__(self, conn, acc_types: list, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.acc_types = acc_types
        self.refresh()

    def refresh(self, restore_id=None):
        self.blockSignals(True)
        prev = restore_id if restore_id is not None else self.currentData()
        self.clear()
        self.addItem("— كل التصنيفات —", None)
        for t in self.acc_types:
            try:
                rows = fetch_all_groups(self.conn, t)
                tree = build_group_tree(rows)
                self._add_nodes(tree, 0)
            except Exception as e:
                print(f"[_GroupFilterCombo] error for {t}: {e}")
        for i in range(self.count()):
            if self.itemData(i) == prev:
                self.setCurrentIndex(i)
                break
        self.blockSignals(False)

    def _add_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            self.setItemData(
                self.count() - 1, QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_nodes(node["children"], depth + 1)