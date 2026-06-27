"""
ui/tabs/accounting/journal/group_combo/_tree_group_combo.py
===========================================================
_TreeGroupCombo — QComboBox مع QTreeView شجري لعرض تصنيفات الحسابات.

[v5]:
  - SafeConnMixin بدل self.conn الثابت.
  - استخدام get_active_company_id() من company_utils بدل الدالة المحلية.
  - إزالة التكرار مع journal_group_combo.py.
"""

from PyQt5.QtWidgets import QComboBox, QTreeView
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui  import QColor, QFont, QStandardItemModel, QStandardItem

from db.accounting.accounting_repo import fetch_all_groups, build_group_tree
from db.accounting.accounting_schema import TYPE_AR, EQUITY_TYPES
from ui.widgets.core.events import bus, get_active_company_id
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.font import FS_SM
from ui.tabs.accounting.helpers import TYPE_COLORS
from ui.constants import (
    TREE_GROUP_COMBO_BORDER_W,
    TREE_GROUP_COMBO_ITEM_PAD_V,
    TREE_GROUP_COMBO_ITEM_PAD_H,
    TREE_GROUP_COMBO_ITEM_MIN_H,
    TREE_GROUP_COMBO_HEADER_FONT_DELTA,
)
from ._no_select_delegate import _NoSelectDelegate

_TYPE_ORDER = ["asset", "liability", "capital", "drawings", "revenue", "expense"]

_TYPE_ICON_KEYS = {
    "asset":     "account_tree_icon_asset",
    "liability": "account_tree_icon_liability",
    "capital":   "account_tree_icon_capital",
    "drawings":  "account_tree_icon_drawings",
    "revenue":   "account_tree_icon_revenue",
    "expense":   "account_tree_icon_expense",
}

_ROLE_GROUP_ID  = Qt.UserRole + 1
_ROLE_IS_HEADER = Qt.UserRole + 2

def _equity_color() -> str:
    """لون حقوق الملكية من الثيم — يُقرأ في runtime لدعم تغيير الثيم."""
    from ui.theme import _C
    return _C["investor_capital_text"]


class _TreeGroupCombo(SafeConnMixin, QComboBox, WidgetMixin):
    """
    QComboBox يعرض التصنيفات في شجرة هرمية.
    عناصر الرأس (أنواع الحسابات) غير قابلة للاختيار.
    عناصر التصنيف تعيد group_id عبر currentData().
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._group_entry_ids = None
        self._company_id      = get_active_company_id()

        self._model = QStandardItemModel()
        self.setModel(self._model)

        self._tree_view = QTreeView(self)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setItemDelegate(
            _NoSelectDelegate(self._tree_view, is_header_role=_ROLE_IS_HEADER)
        )
        self._tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self._tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.setView(self._tree_view)
        self._tree_view.clicked.connect(self._on_tree_clicked)

        self._init_widget_mixin(lang=False)
        self._refresh_style()
        self._populate()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self._tree_view.setStyleSheet(
            f"QTreeView {{"
            f"    border: {TREE_GROUP_COMBO_BORDER_W}px solid {_C['border_med']};"
            f"    background: {_C['bg_input']};"
            f"    outline: none;"
            f"    font-size: {FS_SM}px;"
            f"}}"
            f"QTreeView::item {{"
            f"    padding: {TREE_GROUP_COMBO_ITEM_PAD_V}px {TREE_GROUP_COMBO_ITEM_PAD_H}px;"
            f"    min-height: {TREE_GROUP_COMBO_ITEM_MIN_H}px;"
            f"}}"
            f"QTreeView::item:selected {{"
            f"    background: {_C['badge_dr_bg']};"
            f"    color: {_C['accent']};"
            f"}}"
            f"QTreeView::item:hover:!selected {{"
            f"    background: {_C['bg_hover']};"
            f"}}"
        )

    def _refresh_data(self, company_id=None):
        self._reload()

    def _populate(self):
        from ui.theme import _C
        conn = self._get_safe_conn()
        prev_gid = self.currentData()
        self._model.clear()

        all_item = QStandardItem(tr("all_groups"))
        all_item.setData(None, _ROLE_GROUP_ID)
        all_item.setData(False, _ROLE_IS_HEADER)
        all_item.setFlags(all_item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        f = QFont(); f.setItalic(True)
        all_item.setFont(f)
        all_item.setForeground(QColor(_C['text_sec']))
        self._model.appendRow(all_item)

        try:
            all_groups = fetch_all_groups(conn)
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

            icon_key = _TYPE_ICON_KEYS.get(acc_type)
            icon = tr(icon_key) if icon_key else tr("account_tree_default_icon")
            type_label = f"{icon}  {TYPE_AR.get(acc_type, acc_type)}"
            header_item = QStandardItem(type_label)
            header_item.setData(None, _ROLE_GROUP_ID)
            header_item.setData(True, _ROLE_IS_HEADER)
            header_item.setFlags(Qt.ItemIsEnabled)
            hf = QFont(); hf.setBold(True); hf.setPointSize(hf.pointSize() + TREE_GROUP_COMBO_HEADER_FONT_DELTA)
            header_item.setFont(hf)
            header_item.setForeground(QColor(TYPE_COLORS.get(acc_type, _C['text_primary'])))
            bg = _C["investor_capital_bg"] if acc_type in EQUITY_TYPES else _C["journal_header_bg"]
            header_item.setBackground(QColor(bg))
            self._model.appendRow(header_item)
            self._add_group_items(header_item, tree, acc_type)

        self._tree_view.expandAll()
        self._restore_selection(prev_gid)

    def _add_group_items(self, parent_item: QStandardItem, nodes: list, acc_type: str):
        from ui.theme import _C
        for node in nodes:
            item = QStandardItem(f"  {node['name']}")
            item.setData(node["id"], _ROLE_GROUP_ID)
            item.setData(False, _ROLE_IS_HEADER)
            item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setForeground(QColor(node.get("color", TYPE_COLORS.get(acc_type, _C['text_primary']))))
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
        conn = self._get_safe_conn()

        if gid is None:
            self.setCurrentText(tr("all_groups"))
            self._group_entry_ids = None
        else:
            self.setCurrentText(item.text().strip())
            try:
                from db.accounting.accounting_repo import _get_group_descendants
                desc_ids = _get_group_descendants(conn, gid)
                if not desc_ids:
                    self._group_entry_ids = set()
                else:
                    placeholders = ",".join("?" * len(desc_ids))
                    rows = conn.execute(f"""
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