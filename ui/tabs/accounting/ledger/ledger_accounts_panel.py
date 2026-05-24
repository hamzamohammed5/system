"""
ui/tabs/accounting/ledger/ledger_accounts_panel.py
===================================================
_AccountsPanel — قائمة الحسابات في دفتر الأستاذ.

[تحسين v4]:
  - استخدام ListHeader + SearchBar من widgets/shared بدل بناء يدوي.
  - استخدام make_list_table من table_utils.
  - SafeConnMixin كما هو.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QTreeWidget, QTreeWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import fetch_all_accounts
from db.accounting.accounting_schema import TYPE_AR
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.panels import ListHeader, ListStatusBar, get_tree_style
from ui.tabs.accounting.helpers import TYPE_COLORS


class _AccountsPanel(SafeConnMixin, QWidget):
    def __init__(self, conn, on_select, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._on_select  = on_select
        self._all        = []
        self._build()
        self._refresh_accounts()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── هيدر موحد بدل بناء يدوي ──
        self._header = ListHeader(
            title="📚  الحسابات",
            show_search=True,
            search_placeholder="🔍  بحث بالاسم أو الكود...",
        )
        self._header.search_changed.connect(self._filter_accounts)
        root.addWidget(self._header)

        # ── فلتر النوع ──
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        self.cmb_type.addItem("── كل الأنواع ──", None)
        for key, label in TYPE_AR.items():
            self.cmb_type.addItem(label, key)
        self.cmb_type.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
                margin: 4px 8px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_type.currentIndexChanged.connect(self._filter_accounts)
        root.addWidget(self.cmb_type)

        # ── شجرة الحسابات باستخدام get_tree_style الموحد ──
        self.lst = QTreeWidget()
        self.lst.setHeaderLabels(["الكود", "الاسم", "الرصيد"])
        hh = self.lst.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.lst.setColumnWidth(0, 65)
        self.lst.setColumnWidth(2, 90)
        self.lst.setAlternatingRowColors(True)
        self.lst.setStyleSheet(get_tree_style())
        self.lst.itemSelectionChanged.connect(self._on_selected)
        root.addWidget(self.lst, stretch=1)

        # ── شريط الحالة الموحد ──
        self._status = ListStatusBar()
        root.addWidget(self._status)

    def _refresh_accounts(self):
        try:
            self._all = fetch_all_accounts(self._get_safe_conn())
        except Exception as e:
            print(f"[_AccountsPanel] _refresh_accounts error: {e}")
            self._all = []
        self._filter_accounts()

    def _filter_accounts(self, q: str = ""):
        if not q:
            q = self._header.search_text()
        type_filt = self.cmb_type.currentData()

        self.lst.clear()
        conn  = self._get_safe_conn()
        count = 0

        for acc in self._all:
            if not acc["is_leaf"]:
                continue
            if type_filt and acc["type"] != type_filt:
                continue
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            try:
                bal_row = conn.execute("""
                    SELECT COALESCE(SUM(debit)-SUM(credit), 0) AS bal
                    FROM journal_lines WHERE account_id=?
                """, (acc["id"],)).fetchone()
                bal = bal_row["bal"] if bal_row else 0.0
            except Exception:
                bal = 0.0

            item = QTreeWidgetItem()
            item.setText(0, acc["code"])
            item.setText(1, acc["name"])
            item.setText(2, f"{bal:,.2f}")
            item.setData(0, Qt.UserRole, acc["id"])

            color = TYPE_COLORS.get(acc["type"], "#333")
            item.setForeground(0, QColor(color))
            item.setToolTip(1, f"{acc['code']} — {acc['name']}")

            if bal < 0:
                item.setForeground(2, QColor("#c62828"))
            elif bal > 0:
                item.setForeground(2, QColor("#2e7d32"))

            self.lst.addTopLevelItem(item)
            count += 1

        total = sum(1 for a in self._all if a["is_leaf"])
        self._status.set_count(count, total)

    def _on_selected(self):
        items = self.lst.selectedItems()
        if not items:
            return
        acc_id = items[0].data(0, Qt.UserRole)
        if acc_id:
            self._on_select(acc_id)
            