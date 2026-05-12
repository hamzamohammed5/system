"""
ui/tabs/accounting/journal/account_picker/_account_tree_popup.py
=================================================================
_AccountTreePopup — نافذة popup شجرية لاختيار حساب.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.accounting_repo import (
    fetch_all_accounts, fetch_account,
    fetch_all_groups, build_group_tree,
    get_normal_balance,
)
from db.accounting_schema import TYPE_AR, EQUITY_TYPES
from ...helpers import TYPE_COLORS

_TYPE_ORDER = ["asset", "liability", "capital", "drawings", "revenue", "expense"]

_TYPE_ICONS = {
    "asset":     "🏦",
    "liability": "📋",
    "capital":   "👑",
    "drawings":  "💸",
    "revenue":   "💹",
    "expense":   "📤",
}

_EQUITY_COLOR = "#2e7d32"
_EQUITY_LABEL = "حقوق الملكية"


class _AccountTreePopup(QDialog):
    """نافذة popup تعرض الحسابات في شجرة قابلة للطي مع بحث نصي."""

    def __init__(self, conn, acc_types=None, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.conn           = conn
        self.acc_types      = acc_types or _TYPE_ORDER
        self._selected_id   = None
        self._selected_name = None
        self._expanded: set = set()
        self._expanded.add("group:equity")
        for t in self.acc_types:
            self._expanded.add(f"type:{t}")
        self._all_accounts = []
        self._filter_text  = ""
        self._build()
        self._load_accounts()

    def _build(self):
        self.setMinimumWidth(440)
        self.setMaximumHeight(520)
        self.setStyleSheet("""
            QDialog {
                background: white;
                border: 1px solid #c5cae9;
                border-radius: 8px;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث بالاسم أو الكود...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: #f0f4ff; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #1565c0; background: white; }
        """)
        self.inp_search.textChanged.connect(self._on_search)
        root.addWidget(self.inp_search)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { border: 1px solid #e0e0e0; border-radius: 4px;
                          background: white; outline: none; }
            QListWidget::item { padding: 3px 6px; border-bottom: 1px solid #f0f0f0; }
            QListWidget::item:selected { background: #e3f2fd; color: #1565c0; }
            QListWidget::item:hover:!selected { background: #f5f5f5; }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        root.addWidget(self.list_widget)

        hint = QLabel("اضغط مرتين أو Enter للاختيار")
        hint.setStyleSheet("font-size:9px; color:#aaa; background:transparent;")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

    def _load_accounts(self):
        self._all_accounts = []
        for acc_type in self.acc_types:
            try:
                rows = fetch_all_accounts(self.conn, acc_type)
                for r in rows:
                    if r["is_leaf"]:
                        self._all_accounts.append({
                            "id":         r["id"],
                            "code":       r["code"],
                            "name":       r["name"],
                            "type":       r["type"],
                            "group_id":   r["group_id"],
                            "group_name": r["group_name"] if "group_name" in r.keys() else None,
                        })
            except Exception:
                pass
        self._render()

    def _on_search(self, text):
        self._filter_text = text.strip().lower()
        if self._filter_text:
            self._expanded.add("group:equity")
            for t in self.acc_types:
                self._expanded.add(f"type:{t}")
        self._render()

    def _render(self):
        self.list_widget.clear()
        q = self._filter_text

        by_type: dict = {}
        for acc in self._all_accounts:
            t = acc["type"]
            if t not in by_type:
                by_type[t] = {}
            grp_key  = acc["group_name"] or "─── بدون تصنيف ───"
            grp_id   = acc["group_id"]   or -1
            grp_full = (grp_id, grp_key)
            if grp_full not in by_type[t]:
                by_type[t][grp_full] = []
            by_type[t][grp_full].append(acc)

        standalone_types = [t for t in self.acc_types if t not in EQUITY_TYPES]
        equity_types     = [t for t in self.acc_types if t in EQUITY_TYPES]

        for acc_type in standalone_types:
            if acc_type not in by_type:
                continue
            groups = by_type[acc_type]
            if q:
                has_match = any(
                    q in acc["name"].lower() or q in acc["code"].lower()
                    for accs in groups.values() for acc in accs
                )
                if not has_match:
                    continue
            self._render_type_section(acc_type, groups, q, indent=0)

        equity_has_match = False
        if equity_types:
            for t in equity_types:
                if t not in by_type:
                    continue
                if q:
                    for accs in by_type[t].values():
                        for acc in accs:
                            if q in acc["name"].lower() or q in acc["code"].lower():
                                equity_has_match = True
                                break
                        if equity_has_match:
                            break
                else:
                    equity_has_match = True
                if equity_has_match:
                    break

        if equity_types and equity_has_match:
            equity_key = "group:equity"
            expanded   = equity_key in self._expanded
            toggle     = "▼" if expanded else "▶"

            eq_item = QListWidgetItem(f"{toggle} 👑  {_EQUITY_LABEL}")
            eq_item.setData(Qt.UserRole, {"kind": "equity_group", "key": equity_key})
            f = QFont(); f.setBold(True); f.setPointSize(f.pointSize() + 1)
            eq_item.setFont(f)
            eq_item.setForeground(QColor(_EQUITY_COLOR))
            eq_item.setBackground(QColor("#f1f8e9"))
            self.list_widget.addItem(eq_item)

            if expanded:
                equity_order = ["capital", "drawings", "revenue", "expense"]
                for acc_type in equity_order:
                    if acc_type not in equity_types or acc_type not in by_type:
                        continue
                    groups = by_type[acc_type]
                    if q:
                        has_match = any(
                            q in acc["name"].lower() or q in acc["code"].lower()
                            for accs in groups.values() for acc in accs
                        )
                        if not has_match:
                            continue
                    self._render_type_section(acc_type, groups, q, indent=1)

    def _render_type_section(self, acc_type, groups, q, indent=0):
        type_key   = f"type:{acc_type}"
        expanded   = type_key in self._expanded
        icon       = _TYPE_ICONS.get(acc_type, "📁")
        type_label = TYPE_AR.get(acc_type, acc_type)
        toggle     = "▼" if expanded else "▶"
        color      = TYPE_COLORS.get(acc_type, "#333")
        pad        = "    " * indent

        type_item = QListWidgetItem(f"{pad}{toggle} {icon}  {type_label}")
        type_item.setData(Qt.UserRole, {"kind": "type", "type": acc_type, "key": type_key})
        f = QFont(); f.setBold(True); f.setPointSize(f.pointSize() + (0 if indent else 1))
        type_item.setFont(f)
        type_item.setForeground(QColor(color))
        type_item.setBackground(QColor("#f0f4ff" if indent == 0 else "#fafffe"))
        self.list_widget.addItem(type_item)

        if not expanded:
            return

        for (grp_id, grp_name), accs in sorted(groups.items(), key=lambda x: x[0][1]):
            matched_accs = accs
            if q:
                matched_accs = [a for a in accs
                                if q in a["name"].lower() or q in a["code"].lower()]
            if not matched_accs:
                continue

            grp_key_full = f"grp:{acc_type}:{grp_id}"
            grp_expanded = grp_key_full in self._expanded
            toggle_g  = "▼" if grp_expanded else "▶"
            inner_pad = "    " * (indent + 1)

            grp_item = QListWidgetItem(f"{inner_pad}{toggle_g} 🏷  {grp_name}")
            grp_item.setData(Qt.UserRole, {"kind": "group", "key": grp_key_full})
            gf = QFont(); gf.setBold(True); gf.setItalic(True)
            grp_item.setFont(gf)
            grp_item.setForeground(QColor("#546e7a"))
            grp_item.setBackground(QColor("#fafbff"))
            self.list_widget.addItem(grp_item)

            if not grp_expanded and not q:
                continue

            acc_pad = "    " * (indent + 2)
            for acc in sorted(matched_accs, key=lambda a: a["code"]):
                nb = get_normal_balance(acc["type"])
                nb_text = "DR↑" if nb == "dr" else "CR↑"
                label = f"{acc_pad}{acc['code']} — {acc['name']}  [{nb_text}]"
                acc_item = QListWidgetItem(label)
                acc_item.setData(Qt.UserRole, {
                    "kind": "account",
                    "id":   acc["id"],
                    "name": f"{acc['code']} — {acc['name']}",
                    "type": acc["type"],
                })
                acc_item.setForeground(QColor(color))
                self.list_widget.addItem(acc_item)

    def _on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        kind = data.get("kind")
        if kind in ("type", "group", "equity_group"):
            key = data["key"]
            if key in self._expanded:
                self._expanded.discard(key)
            else:
                self._expanded.add(key)
            self._render()

    def _on_item_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data or data.get("kind") != "account":
            return
        self._selected_id   = data["id"]
        self._selected_name = data["name"]
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current = self.list_widget.currentItem()
            if current:
                self._on_item_double_clicked(current)
            return
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def get_selected(self):
        return self._selected_id, self._selected_name

    def get_selected_type(self):
        if not self._selected_id:
            return None
        acc = fetch_account(self.conn, self._selected_id)
        return acc["type"] if acc else None