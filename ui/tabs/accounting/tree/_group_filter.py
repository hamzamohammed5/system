"""
ui/tabs/accounting/tree/_group_filter.py
==================================================
_GroupFilterCombo — Combo فلتر التصنيفات في شجرة الحسابات.

[إصلاح v2] SafeConnMixin بدل self.conn الثابت.
  - _get_safe_conn() في كل query بدل self.conn المحفوظ.
  - refresh(conn=None) تقبل conn خارجي (من AccountsTreePanel عند تغيير الشركة).
"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import fetch_all_groups, build_group_tree
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin


class _GroupFilterCombo(SafeConnMixin, QComboBox, WidgetMixin):
    """Combo لفلترة الحسابات بالتصنيف."""

    def __init__(self, conn, acc_types: list, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._init_widget_mixin(theme=False, font=False, lang=True, data=False)
        self.acc_types = acc_types
        self.refresh()

    def _refresh_lang(self, *_):
        self.refresh()

    def refresh(self, restore_id=None, conn=None):
        """
        يُعيد تحميل التصنيفات.
        conn: لو مُمرر من الخارج (عند تغيير الشركة) يستخدمه مباشرةً،
              وإلا يستخدم _get_safe_conn().
        """
        effective_conn = conn if conn is not None else self._get_safe_conn()

        self.blockSignals(True)
        prev = restore_id if restore_id is not None else self.currentData()
        self.clear()
        self.addItem(tr("all_groups"), None)
        for t in self.acc_types:
            try:
                rows = fetch_all_groups(effective_conn, t)
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
        arrow  = tr("tree_node_arrow") if depth > 0 else ""
        for node in nodes:
            self.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            self.setItemData(
                self.count() - 1, QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_nodes(node["children"], depth + 1)