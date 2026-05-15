"""
ui/tabs/accounting/ledger/ledger_accounts_panel.py
===================================================
_AccountsPanel — قائمة الحسابات في دفتر الأستاذ.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import fetch_all_accounts
from db.accounting.accounting_schema import TYPE_AR
from ui.events import bus
from ui.tabs.accounting.helpers import TYPE_COLORS


class _AccountsPanel(QWidget):
    def __init__(self, conn, on_select, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_select = on_select
        self._all       = []
        self._build()
        self._refresh_accounts()
        bus.data_changed.connect(self._refresh_accounts)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        hdr = QLabel("📚  الحسابات")
        hdr.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #1565c0;
            background: #e8f4fd;
            border: 1px solid #90caf9;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        self.cmb_type.addItem("── كل الأنواع ──", None)
        for key, label in TYPE_AR.items():
            self.cmb_type.addItem(label, key)
        self.cmb_type.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_type.currentIndexChanged.connect(self._filter_accounts)
        root.addWidget(self.cmb_type)

        search_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث بالاسم أو الكود...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }
            QLineEdit:focus { border-color: #1565c0; }
        """)
        self.inp_search.textChanged.connect(self._filter_accounts)
        search_row.addWidget(self.inp_search)
        root.addLayout(search_row)

        self.lst = QTreeWidget()
        self.lst.setHeaderLabels(["الكود", "الاسم", "الرصيد"])
        hh = self.lst.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.lst.setColumnWidth(0, 65)
        self.lst.setColumnWidth(2, 90)
        self.lst.setAlternatingRowColors(True)
        self.lst.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
            }
            QTreeWidget::item { padding: 3px 2px; }
            QTreeWidget::item:selected {
                background: #e3f2fd;
                color: #1565c0;
            }
            QTreeWidget::item:hover:!selected { background: #f5f5f5; }
        """)
        self.lst.itemSelectionChanged.connect(self._on_selected)
        root.addWidget(self.lst, stretch=1)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            "color:#888; font-size:10px; background:transparent;"
            "border:none; padding:2px;"
        )
        self.lbl_count.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_count)

    def _refresh_accounts(self):
        self._all = fetch_all_accounts(self.conn)
        self._filter_accounts()

    def _filter_accounts(self):
        q         = self.inp_search.text().strip().lower()
        type_filt = self.cmb_type.currentData()

        self.lst.clear()
        count = 0

        for acc in self._all:
            if not acc["is_leaf"]:
                continue
            if type_filt and acc["type"] != type_filt:
                continue
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            try:
                bal_row = self.conn.execute("""
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
        if count == total:
            self.lbl_count.setText(f"({count} حساب)")
        else:
            self.lbl_count.setText(f"({count} / {total})")

    def _on_selected(self):
        items = self.lst.selectedItems()
        if not items:
            return
        acc_id = items[0].data(0, Qt.UserRole)
        if acc_id:
            self._on_select(acc_id)