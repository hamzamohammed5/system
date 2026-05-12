"""
ui/tabs/accounting/accounts_tree/_tree_builder.py
==================================================
دوال مساعدة لبناء شجرة الحسابات وعرضها في QTreeWidget.
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.accounting_repo import get_account_balance
from db.accounting_schema import TYPE_AR, EQUITY_TYPES
from ui.tabs.accounting.helpers import TYPE_COLORS

EQUITY_COLOR = "#2e7d32"


def rows_to_tree(rows) -> list:
    """يحوّل rows إلى شجرة nested مع children."""
    nodes = {}
    for r in rows:
        try:
            nid = r["id"]
            nodes[nid] = {
                "id":         nid,
                "code":       r["code"],
                "name":       r["name"],
                "type":       r["type"],
                "parent_id":  r["parent_id"],
                "is_leaf":    r["is_leaf"],
                "group_id":   r["group_id"],
                "group_name": r["group_name"] if "group_name" in r.keys() else None,
                "children":   [],
            }
        except Exception as e:
            print(f"[_tree_builder] error reading row: {e}")

    roots = []
    for nid, node in nodes.items():
        pid = node["parent_id"]
        if pid and pid in nodes:
            nodes[pid]["children"].append(node)
        else:
            roots.append(node)
    roots.sort(key=lambda n: n["code"])
    return roots


def filter_by_group(conn, nodes: list, gid: int) -> list:
    from db.accounting_repo import _get_group_descendants
    try:
        desc = _get_group_descendants(conn, gid)
    except Exception:
        desc = {gid}
    result = []
    for node in nodes:
        if node.get("group_id") in desc:
            result.append(node)
        elif node.get("children"):
            filtered = filter_by_group(conn, node["children"], gid)
            if filtered:
                node = dict(node)
                node["children"] = filtered
                result.append(node)
    return result


def add_acc_nodes(conn, tree_widget: QTreeWidget, nodes: list, parent):
    """يضيف عقد الحسابات للشجرة بشكل متكرر."""
    for node in sorted(nodes, key=lambda n: n.get("code", "")):
        try:
            bal = get_account_balance(conn, node["id"])
        except Exception:
            bal = 0.0

        color = TYPE_COLORS.get(node["type"], "#333")
        item  = QTreeWidgetItem()
        item.setText(0, node["code"])
        item.setText(1, node["name"])
        item.setText(2, f"{bal:,.2f}")
        item.setData(0, Qt.UserRole, node["id"])
        item.setForeground(0, QColor(color))
        item.setToolTip(1, (
            f"{node['name']}  |  🏷 {node['group_name']}"
            if node.get("group_name") else node["name"]
        ))

        if not node.get("is_leaf", 1):
            f = item.font(1)
            f.setBold(True)
            item.setFont(1, f)

        if bal < 0:
            item.setForeground(2, QColor("#c62828"))
        elif bal > 0:
            item.setForeground(2, QColor("#2e7d32"))

        if parent:
            parent.addChild(item)
        else:
            tree_widget.addTopLevelItem(item)

        if node.get("children"):
            add_acc_nodes(conn, tree_widget, node["children"], item)


def add_type_header(tree_widget: QTreeWidget, acc_type: str, nodes: list,
                    conn) -> QTreeWidgetItem:
    """يضيف عقدة رأسية لنوع حساب مستقل."""
    type_item = QTreeWidgetItem()
    type_item.setText(1, f"── {TYPE_AR.get(acc_type, acc_type)} ──")
    type_item.setForeground(1, QColor(TYPE_COLORS.get(acc_type, "#333")))
    f = type_item.font(1)
    f.setBold(True)
    type_item.setFont(1, f)
    type_item.setFlags(type_item.flags() & ~Qt.ItemIsSelectable)
    tree_widget.addTopLevelItem(type_item)
    add_acc_nodes(conn, tree_widget, nodes, type_item)
    type_item.setExpanded(True)
    return type_item