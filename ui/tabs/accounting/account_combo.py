"""
ui/tabs/accounting/account_combo.py
=====================================
_AccountCombo — Combo قابل للبحث والفلترة لاختيار الحسابات.
SafeConnMixin (v4): _get_safe_conn() بدل self.conn في كل query.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QLabel,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from db.accounting.accounting_repo import (
    fetch_leaf_accounts, fetch_account,
    fetch_all_groups, build_group_tree,
    get_normal_balance, _get_group_descendants,
)
from db.accounting.accounting_schema import TYPE_AR
from ui.events import bus
from ui.font_utils import badge_style, badge_width
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from .helpers import TYPE_COLORS


class _AccountCombo(SafeConnMixin, QWidget):
    def __init__(self, conn, acc_types: list = None, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self.acc_types   = acc_types
        self._all_accs   = []
        self._company_id = self._get_company_id()
        self._build()
        self.refresh()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            snapshot_id = company_id
            QTimer.singleShot(0, lambda: self._safe_refresh(snapshot_id))

    def _safe_refresh(self, snapshot_id: int):
        if self._get_company_id() == snapshot_id:
            self.refresh()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self.cmb_group = QComboBox()
        self.cmb_group.setFixedWidth(130)
        self.cmb_group.setToolTip("فلتر بالتصنيف")
        self.cmb_group.currentIndexChanged.connect(self._apply_filter)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(90)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.cmb_account = QComboBox()
        self.cmb_account.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_account.setMinimumWidth(200)

        self.lbl_nb = QLabel("")
        self.lbl_nb.setFixedWidth(badge_width())
        self.lbl_nb.setAlignment(Qt.AlignCenter)
        self.lbl_nb.setStyleSheet(badge_style())
        self.cmb_account.currentIndexChanged.connect(self._update_nb_label)

        lay.addWidget(self.cmb_group)
        lay.addWidget(self.inp_search)
        lay.addWidget(self.cmb_account, stretch=1)
        lay.addWidget(self.lbl_nb)

    def refresh(self):
        self._load_groups()
        self._load_accounts()

    def _load_groups(self):
        conn = self._get_safe_conn()
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem("— كل التصنيفات —", None)
        try:
            all_groups = fetch_all_groups(conn)
            seen_types = set(self.acc_types) if self.acc_types else set(TYPE_AR.keys())
            groups     = [g for g in all_groups if g["acc_type"] in seen_types]
            tree       = build_group_tree(groups)
            self._add_group_nodes(tree, depth=0)
        except Exception:
            pass
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == prev:
                self.cmb_group.setCurrentIndex(i)
                break
        self.cmb_group.blockSignals(False)

    def _add_group_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_group.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            idx = self.cmb_group.count() - 1
            self.cmb_group.setItemData(idx, QColor(node["color"]), Qt.ForegroundRole)
            if node["children"]:
                self._add_group_nodes(node["children"], depth + 1)

    def _load_accounts(self):
        conn = self._get_safe_conn()
        try:
            self._all_accs = list(fetch_leaf_accounts(conn))
            if self.acc_types:
                self._all_accs = [a for a in self._all_accs if a["type"] in self.acc_types]
        except Exception:
            self._all_accs = []
        self._apply_filter()

    def _apply_filter(self):
        conn    = self._get_safe_conn()
        prev_id = self.current_account_id()
        q       = self.inp_search.text().strip().lower()
        gid     = self.cmb_group.currentData()

        self.cmb_account.blockSignals(True)
        self.cmb_account.clear()
        self.cmb_account.addItem("— اختر الحساب —", None)

        last_type = None
        for acc in self._all_accs:
            if gid is not None:
                try:
                    desc = _get_group_descendants(conn, gid)
                    if acc["group_id"] not in desc:
                        continue
                except Exception:
                    pass
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            if acc["type"] != last_type:
                sep_text = f"── {TYPE_AR.get(acc['type'], acc['type'])} ──"
                self.cmb_account.addItem(sep_text, "__sep__")
                sep_index = self.cmb_account.count() - 1
                self._disable_item(sep_index)
                last_type = acc["type"]

            color   = TYPE_COLORS.get(acc["type"], "#333")
            nb      = get_normal_balance(acc["type"])
            nb_text = "DR↑" if nb == "dr" else "CR↑"
            label   = f"{acc['code']} — {acc['name']}  [{nb_text}]"
            self.cmb_account.addItem(label, acc["id"])
            idx2 = self.cmb_account.count() - 1
            self.cmb_account.setItemData(idx2, QColor(color), Qt.ForegroundRole)

        self._remove_trailing_separators()
        self.cmb_account.blockSignals(False)

        if prev_id is not None:
            for i in range(self.cmb_account.count()):
                if self.cmb_account.itemData(i) == prev_id:
                    self.cmb_account.setCurrentIndex(i)
                    self._update_nb_label()
                    return

        self._select_first_real()
        self._update_nb_label()

    def _disable_item(self, idx: int):
        model = self.cmb_account.model()
        item  = model.item(idx)
        if item:
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
            item.setForeground(QColor("#78909c"))
            f = QFont()
            f.setBold(True)
            item.setFont(f)

    def _remove_trailing_separators(self):
        changed = True
        while changed:
            changed = False
            count = self.cmb_account.count()
            for i in range(count - 1, -1, -1):
                d = self.cmb_account.itemData(i)
                if d == "__sep__":
                    if i == count - 1:
                        self.cmb_account.removeItem(i)
                        changed = True
                        break
                    next_d = self.cmb_account.itemData(i + 1)
                    if next_d == "__sep__":
                        self.cmb_account.removeItem(i)
                        changed = True
                        break

    def _select_first_real(self):
        for i in range(self.cmb_account.count()):
            d = self.cmb_account.itemData(i)
            if d is not None and d != "__sep__" and isinstance(d, int):
                self.cmb_account.setCurrentIndex(i)
                return
        self.cmb_account.setCurrentIndex(0)

    def _update_nb_label(self):
        acc_id = self.current_account_id()
        if not acc_id:
            self.lbl_nb.setText("")
            self.lbl_nb.setStyleSheet(badge_style())
            return
        try:
            acc = fetch_account(self._get_safe_conn(), acc_id)
            if not acc:
                return
            nb = get_normal_balance(acc["type"])
            if nb == "dr":
                self.lbl_nb.setText("DR↑")
                self.lbl_nb.setStyleSheet(badge_style("dr"))
            else:
                self.lbl_nb.setText("CR↑")
                self.lbl_nb.setStyleSheet(badge_style("cr"))
        except Exception:
            pass

    def current_account_id(self):
        data = self.cmb_account.currentData()
        if data is None or data == "__sep__":
            return None
        if not isinstance(data, int):
            return None
        return data

    def set_account(self, acc_id):
        for i in range(self.cmb_account.count()):
            if self.cmb_account.itemData(i) == acc_id:
                self.cmb_account.setCurrentIndex(i)
                return
