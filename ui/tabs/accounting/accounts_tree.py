"""
ui/tabs/accounting/accounts_tree.py
=====================================
AccountsTreePanel — شجرة الحسابات مع فورم الإضافة والتعديل.
SafeConnMixin (v3): _get_safe_conn() بدل self.conn في كل query.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QSplitter,
    QPushButton, QLabel, QMessageBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.accounting.accounting_repo import (
    fetch_all_accounts, fetch_account, delete_account,
    fetch_all_groups, build_group_tree,
)
from db.accounting.accounting_schema import TYPE_AR, EQUITY_TYPES
from ui.helpers import section_label, danger_button, confirm_delete
from ui.events  import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin

from .tree._tree_builder import (
    rows_to_tree, filter_by_group, add_acc_nodes, add_type_header, EQUITY_COLOR,
)
from .tree._account_form  import _AccountForm
from .tree._group_filter  import _GroupFilterCombo


class AccountsTreePanel(SafeConnMixin, QWidget):
    def __init__(self, conn, acc_types: list, title: str, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self.acc_types   = acc_types
        self.title       = title
        self._loading    = False
        self._company_id = self._get_company_id()
        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._load()

    def _build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)

        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(10, 8, 6, 10)
        ll.setSpacing(6)

        ll.addWidget(section_label(f"── {self.title} ──"))

        filter_row = QHBoxLayout()
        self.cmb_group_filter = _GroupFilterCombo(self._get_safe_conn(), self.acc_types)
        self.cmb_group_filter.setMinimumHeight(26)
        self.cmb_group_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(QLabel("🏷"))
        filter_row.addWidget(self.cmb_group_filter, stretch=1)
        ll.addLayout(filter_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الكود", "اسم الحساب", "الرصيد"])
        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 70)
        self.tree.setColumnWidth(2, 110)
        self.tree.setAlternatingRowColors(True)
        ll.addWidget(self.tree, stretch=1)

        btn_row  = QHBoxLayout()
        btn_edit = QPushButton("✏️ تعديل")
        btn_del  = danger_button("🗑️ حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        ll.addLayout(btn_row)

        splitter.addWidget(left)

        self._form = _AccountForm(self._get_safe_conn(), self.acc_types)
        splitter.addWidget(self._form)
        splitter.setSizes([420, 280])

        main_layout.addWidget(splitter)

    def _on_filter_changed(self):
        if self._loading:
            return
        self._build_tree()

    def _load(self):
        if self._loading:
            return
        self._loading = True
        try:
            conn = self._get_safe_conn()
            self.cmb_group_filter.refresh(conn=conn)
            self._form.refresh_group_combos(conn=conn)
            self._build_tree()
        finally:
            self._loading = False

    def _build_tree(self):
        self.tree.clear()
        conn       = self._get_safe_conn()
        gid_filter = self.cmb_group_filter.currentData()

        all_nodes_by_type: dict[str, list] = {}
        for acc_type in self.acc_types:
            try:
                rows = fetch_all_accounts(conn, acc_type)
            except Exception as e:
                print(f"[AccountsTreePanel] fetch error ({acc_type}): {e}")
                rows = []
            if not rows:
                continue
            nodes = rows_to_tree(rows)
            if gid_filter is not None:
                nodes = filter_by_group(conn, nodes, gid_filter)
            if nodes:
                all_nodes_by_type[acc_type] = nodes

        if not all_nodes_by_type:
            empty = QTreeWidgetItem()
            empty.setText(1, "لا توجد حسابات — أضف من الفورم على اليمين")
            empty.setForeground(1, QColor("#aaa"))
            self.tree.addTopLevelItem(empty)
            return

        non_equity    = [t for t in self.acc_types if t not in EQUITY_TYPES]
        equity_present = [
            t for t in self.acc_types
            if t in EQUITY_TYPES and t in all_nodes_by_type
        ]

        for acc_type in non_equity:
            if acc_type not in all_nodes_by_type:
                continue
            add_type_header(self.tree, acc_type, all_nodes_by_type[acc_type], conn)

        if equity_present:
            equity_item = QTreeWidgetItem()
            equity_item.setText(0, "")
            equity_item.setText(1, "👑  حقوق الملكية")
            equity_item.setText(2, "")
            equity_item.setFlags(equity_item.flags() & ~Qt.ItemIsSelectable)
            f = equity_item.font(1)
            f.setBold(True)
            f.setPointSize(f.pointSize() + 1)
            equity_item.setFont(1, f)
            equity_item.setForeground(1, QColor(EQUITY_COLOR))
            equity_item.setBackground(0, QColor("#f1f8e9"))
            equity_item.setBackground(1, QColor("#f1f8e9"))
            equity_item.setBackground(2, QColor("#f1f8e9"))
            self.tree.addTopLevelItem(equity_item)

            for acc_type in ["capital", "drawings", "revenue", "expense"]:
                if acc_type not in equity_present:
                    continue
                nodes = all_nodes_by_type[acc_type]
                from ui.tabs.accounting.helpers import TYPE_COLORS
                sub_item = QTreeWidgetItem()
                sub_item.setText(0, "")
                sub_item.setText(1, f"── {TYPE_AR.get(acc_type, acc_type)} ──")
                sub_item.setFlags(sub_item.flags() & ~Qt.ItemIsSelectable)
                sf = sub_item.font(1)
                sf.setBold(True)
                sub_item.setFont(1, sf)
                sub_item.setForeground(1, QColor(TYPE_COLORS.get(acc_type, EQUITY_COLOR)))
                equity_item.addChild(sub_item)
                add_acc_nodes(conn, self.tree, nodes, sub_item)
                sub_item.setExpanded(True)

            equity_item.setExpanded(True)

        self.tree.expandToDepth(2)

    def _selected_id(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def _edit(self):
        aid = self._selected_id()
        if not aid:
            QMessageBox.information(self, "تنبيه", "اختر حسابًا أولًا")
            return
        self._form.load_for_edit(aid)

    def _delete(self):
        aid = self._selected_id()
        if not aid:
            return
        conn = self._get_safe_conn()
        acc  = fetch_account(conn, aid)
        if not acc:
            return

        def get_all_descendants(account_id: int) -> list:
            result = [account_id]
            children = conn.execute(
                "SELECT id FROM accounts WHERE parent_id=?", (account_id,)
            ).fetchall()
            for child in children:
                result.extend(get_all_descendants(child["id"]))
            return result

        all_ids      = get_all_descendants(aid)
        placeholders = ",".join("?" * len(all_ids))

        try:
            has_lines = conn.execute(
                f"SELECT COUNT(*) as c FROM journal_lines "
                f"WHERE account_id IN ({placeholders})",
                all_ids
            ).fetchone()["c"]
        except Exception:
            has_lines = 0

        if has_lines:
            QMessageBox.warning(
                self, "تحذير",
                f"الحساب «{acc['name']}» أو أحد فروعه\n"
                f"له {has_lines} حركة في القيود — لا يمكن حذفه."
            )
            return

        child_count = len(all_ids) - 1
        if child_count:
            msg = (
                f"حذف حساب «{acc['name']}»؟\n"
                f"⚠️ سيتم حذف {child_count} حساب فرعي معه."
            )
            if QMessageBox.question(
                self, "تأكيد الحذف", msg,
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return
        else:
            if not confirm_delete(self, acc["name"]):
                return

        try:
            for del_id in reversed(all_ids):
                conn.execute("DELETE FROM accounts WHERE id=?", (del_id,))
            bus.company_data_changed.emit(self._company_id or 0)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")
