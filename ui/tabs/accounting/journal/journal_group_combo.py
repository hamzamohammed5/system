"""
ui/tabs/accounting/journal/journal_group_combo.py
==========================================
_NoSelectDelegate  — يمنع اختيار عناصر الرأس في الشجرة
_TreeGroupCombo    — QComboBox مع QTreeView شجري لعرض تصنيفات الحسابات
"""

from PyQt5.QtWidgets import (
    QComboBox, QStyledItemDelegate, QTreeView,
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui  import QColor, QFont, QStandardItemModel, QStandardItem

from db.accounting_repo import fetch_all_groups, build_group_tree
from db.accounting_schema import TYPE_AR, EQUITY_TYPES
from ui.events import bus
from ..helpers  import TYPE_COLORS

_TYPE_ORDER = ["asset", "liability", "capital", "drawings", "revenue", "expense"]

_TYPE_ICONS = {
    "asset":     "🏦",
    "liability": "📋",
    "capital":   "👑",
    "drawings":  "💸",
    "revenue":   "💹",
    "expense":   "📤",
}

_ROLE_GROUP_ID  = Qt.UserRole + 1
_ROLE_IS_HEADER = Qt.UserRole + 2

_EQUITY_COLOR = "#2e7d32"
_EQUITY_LABEL = "حقوق الملكية"


class _NoSelectDelegate(QStyledItemDelegate):
    """يجعل عناصر الرأس غير قابلة للاختيار."""
    def paint(self, painter, option, index):
        is_header = index.data(_ROLE_IS_HEADER)
        if is_header:
            from PyQt5.QtWidgets import QStyle
            option.state &= ~QStyle.State_Selected
        super().paint(painter, option, index)


class _TreeGroupCombo(QComboBox):
    """
    QComboBox يعرض التصنيفات في شجرة هرمية.
    عناصر الرأس (أنواع الحسابات) غير قابلة للاختيار.
    عناصر التصنيف تعيد group_id عبر currentData().
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._group_entry_ids = None

        self._model = QStandardItemModel()
        self.setModel(self._model)

        self._tree_view = QTreeView(self)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setItemDelegate(_NoSelectDelegate(self._tree_view))
        self._tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self._tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self._tree_view.setStyleSheet("""
            QTreeView {
                border: 1px solid #c5cae9;
                background: white;
                outline: none;
                font-size: 11px;
            }
            QTreeView::item {
                padding: 3px 6px;
                min-height: 24px;
            }
            QTreeView::item:selected {
                background: #e3f2fd;
                color: #1565c0;
            }
            QTreeView::item:hover:!selected {
                background: #f5f5f5;
            }
        """)
        self.setView(self._tree_view)
        self._tree_view.clicked.connect(self._on_tree_clicked)

        self._populate()
        bus.data_changed.connect(self._reload)

    def _populate(self):
        prev_gid = self.currentData()
        self._model.clear()

        all_item = QStandardItem("— كل التصنيفات —")
        all_item.setData(None, _ROLE_GROUP_ID)
        all_item.setData(False, _ROLE_IS_HEADER)
        all_item.setFlags(all_item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        f = QFont(); f.setItalic(True)
        all_item.setFont(f)
        all_item.setForeground(QColor("#555"))
        self._model.appendRow(all_item)

        try:
            all_groups = fetch_all_groups(self.conn)
        except Exception:
            all_groups = []

        groups_by_type: dict = {}
        for g in all_groups:
            groups_by_type.setdefault(g["acc_type"], []).append(dict(g))

        for acc_type in _TYPE_ORDER:
            if acc_type not in groups_by_type:
                continue
            type_rows = groups_by_type[acc_type]
            tree = build_group_tree(type_rows)
            if not tree:
                continue

            icon = _TYPE_ICONS.get(acc_type, "📁")
            type_label = f"{icon}  {TYPE_AR.get(acc_type, acc_type)}"
            header_item = QStandardItem(type_label)
            header_item.setData(None, _ROLE_GROUP_ID)
            header_item.setData(True, _ROLE_IS_HEADER)
            header_item.setFlags(Qt.ItemIsEnabled)
            hf = QFont(); hf.setBold(True); hf.setPointSize(hf.pointSize() + 1)
            header_item.setFont(hf)
            header_item.setForeground(QColor(TYPE_COLORS.get(acc_type, "#333")))
            bg = "#f1f8e9" if acc_type in EQUITY_TYPES else "#f0f4ff"
            header_item.setBackground(QColor(bg))
            self._model.appendRow(header_item)
            self._add_group_items(header_item, tree, acc_type)

        self._tree_view.expandAll()
        self._restore_selection(prev_gid)

    def _add_group_items(self, parent_item: QStandardItem, nodes: list, acc_type: str):
        color = QColor(TYPE_COLORS.get(acc_type, "#333"))
        for node in nodes:
            item = QStandardItem(f"  {node['name']}")
            item.setData(node["id"], _ROLE_GROUP_ID)
            item.setData(False, _ROLE_IS_HEADER)
            item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setForeground(QColor(node.get("color", TYPE_COLORS.get(acc_type, "#333"))))
            parent_item.appendRow(item)
            if node.get("children"):
                self._add_group_items(item, node["children"], acc_type)

    def _restore_selection(self, prev_gid):
        if prev_gid is None:
            self.setCurrentIndex(0)
            return
        idx = self._find_index_by_gid(self._model.invisibleRootItem(), prev_gid)
        if idx.isValid():
            self.setCurrentIndex(0)

    def _find_index_by_gid(self, parent: QStandardItem, gid: int) -> QModelIndex:
        for row in range(parent.rowCount()):
            child = parent.child(row)
            if child and child.data(_ROLE_GROUP_ID) == gid:
                return child.index()
            if child and child.rowCount() > 0:
                found = self._find_index_by_gid(child, gid)
                if found.isValid():
                    return found
        return QModelIndex()

    def _on_tree_clicked(self, index: QModelIndex):
        item = self._model.itemFromIndex(index)
        if not item:
            return
        is_header = item.data(_ROLE_IS_HEADER)
        if is_header:
            if self._tree_view.isExpanded(index):
                self._tree_view.collapse(index)
            else:
                self._tree_view.expand(index)
            return
        gid = item.data(_ROLE_GROUP_ID)
        self._update_selection(item, gid)
        self.hidePopup()

    def _update_selection(self, item: QStandardItem, gid):
        if gid is None:
            self.setCurrentText("— كل التصنيفات —")
            self._group_entry_ids = None
        else:
            self.setCurrentText(item.text().strip())
            try:
                from db.accounting_repo import _get_group_descendants
                desc_ids = _get_group_descendants(self.conn, gid)
                if not desc_ids:
                    self._group_entry_ids = set()
                else:
                    placeholders = ",".join("?" * len(desc_ids))
                    rows = self.conn.execute(f"""
                        SELECT DISTINCT jl.entry_id
                        FROM journal_lines jl
                        JOIN accounts a ON a.id = jl.account_id
                        WHERE a.group_id IN ({placeholders})
                    """, list(desc_ids)).fetchall()
                    self._group_entry_ids = {r["entry_id"] for r in rows}
            except Exception:
                self._group_entry_ids = None

    def currentData(self, role=Qt.UserRole):
        indexes = self._tree_view.selectedIndexes()
        if not indexes:
            return None
        item = self._model.itemFromIndex(indexes[0])
        if not item:
            return None
        return item.data(_ROLE_GROUP_ID)

    def get_group_entry_ids(self) -> set | None:
        return self._group_entry_ids

    def _reload(self):
        self._populate()
        self._tree_view.expandAll()

    def reset(self):
        self._tree_view.clearSelection()
        self._group_entry_ids = None
        self.setCurrentIndex(0)