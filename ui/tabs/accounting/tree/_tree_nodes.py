"""
ui/tabs/accounting/tree/_tree_nodes.py
======================================
دوال بناء عقد شجرة الحسابات.

مستخرجة من _tree_builder.py لتقليل حجم الملف وتسهيل الصيانة.

[إصلاح v2]:
  - نقل استيراد _get_group_descendants للأعلى بدل داخل الدالة.
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import get_account_balance, _get_group_descendants
from ui.tabs.accounting.helpers import TYPE_COLORS
from ui.theme import _C


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
            print(f"[_tree_nodes] error reading row: {e}")

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

        color = TYPE_COLORS.get(node["type"], _C["text_primary"])
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
            item.setForeground(2, QColor(_C["journal_cr_accent"]))
        elif bal > 0:
            item.setForeground(2, QColor(_C["investor_capital_text"]))

        if parent:
            parent.addChild(item)
        else:
            tree_widget.addTopLevelItem(item)

        if node.get("children"):
            add_acc_nodes(conn, tree_widget, node["children"], item)