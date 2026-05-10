"""
ui/tabs/accounting/ledger_tab.py
==================================
LedgerTab — دفتر الأستاذ (حسابات T).
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTableWidgetItem, QFrame,  # ← أضف QTableWidgetItem هنا
    QLabel, QLineEdit, QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting_repo import (
    fetch_all_accounts, fetch_t_account, get_normal_balance,
)
from db.accounting_schema import TYPE_AR
from ui.helpers import make_table, section_label
from ui.events  import bus
from .helpers   import TYPE_COLORS


class LedgerTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        bus.data_changed.connect(self._refresh_accounts)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # ── يسار: قائمة الحسابات ──
        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(10, 8, 6, 10)
        ll.setSpacing(6)
        ll.addWidget(section_label("── الحسابات ──"))

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._filter_accounts)
        ll.addWidget(self.inp_search)

        self.lst = QTreeWidget()
        self.lst.setHeaderLabels(["الكود", "الاسم"])
        self.lst.setColumnWidth(0, 70)
        self.lst.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.lst.itemSelectionChanged.connect(self._on_selected)
        ll.addWidget(self.lst, stretch=1)
        splitter.addWidget(left)

        # ── يمين: حساب T ──
        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(6, 8, 10, 10)
        rl.setSpacing(8)

        self.lbl_title = QLabel("اختر حسابًا لعرض حركاته")
        self.lbl_title.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#1565c0;"
            "background:#e8f4fd; border:1px solid #90caf9;"
            "border-radius:6px; padding:8px 16px;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        rl.addWidget(self.lbl_title)

        t_frame = QFrame()
        t_frame.setStyleSheet(
            "QFrame { background:white; border:2px solid #1565c0; border-radius:8px; }"
        )
        t_lay = QHBoxLayout(t_frame)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(0)

        def _t_side(title, color, bg):
            w  = QWidget()
            w.setStyleSheet("background:transparent;")
            l  = QVBoxLayout(w)
            l.setContentsMargins(8, 8, 4, 8)
            hdr = QLabel(title)
            hdr.setAlignment(Qt.AlignCenter)
            hdr.setStyleSheet(
                f"font-weight:bold; color:{color}; font-size:12px;"
                f"background:{bg}; border-radius:4px; padding:4px;"
            )
            tbl = make_table(["البيان", "المبلغ"], stretch_col=0)
            tbl.setColumnWidth(1, 100)
            total = QLabel("الإجمالي: 0.00")
            total.setAlignment(Qt.AlignCenter)
            total.setStyleSheet(
                f"font-weight:bold; color:{color}; font-size:11px;"
                f"background:{bg}; border-radius:4px; padding:4px 8px;"
            )
            l.addWidget(hdr)
            l.addWidget(tbl, stretch=1)
            l.addWidget(total)
            return w, tbl, total

        left_t,  self.t_dr_table, self.lbl_dr_total = _t_side("مدين (DR)", "#1565c0", "#e8f4fd")
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#1565c0;")
        right_t, self.t_cr_table, self.lbl_cr_total = _t_side("دائن (CR)", "#c62828", "#fdecea")
        for w in (left_t, sep, right_t):
            t_lay.addWidget(w if w is not sep else sep,
                            stretch=0 if w is sep else 1)
        rl.addWidget(t_frame, stretch=1)

        self.lbl_balance = QLabel("الرصيد: —")
        self.lbl_balance.setAlignment(Qt.AlignCenter)
        self.lbl_balance.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#2e7d32;"
            "background:#f0faf0; border:1px solid #a5d6a7;"
            "border-radius:6px; padding:6px 16px;"
        )
        rl.addWidget(self.lbl_balance)

        splitter.addWidget(right)
        splitter.setSizes([220, 580])
        root.addWidget(splitter)
        self._refresh_accounts()

    def _refresh_accounts(self):
        self._all = fetch_all_accounts(self.conn)
        self._filter_accounts()

    def _filter_accounts(self):
        q = self.inp_search.text().strip().lower()
        self.lst.clear()
        for acc in self._all:
            if not acc["is_leaf"]:
                continue
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue
            item = QTreeWidgetItem()
            item.setText(0, acc["code"])
            item.setText(1, acc["name"])
            item.setData(0, Qt.UserRole, acc["id"])
            item.setForeground(0, QColor(TYPE_COLORS.get(acc["type"], "#333")))
            self.lst.addTopLevelItem(item)

    def _on_selected(self):
        items = self.lst.selectedItems()
        if not items:
            return
        aid  = items[0].data(0, Qt.UserRole)
        data = fetch_t_account(self.conn, aid)
        if not data:
            return
        acc   = data["account"]
        lines = data["lines"]
        nb    = data["normal_balance"]
        self.lbl_title.setText(
            f"حساب: {acc['code']} — {acc['name']}  │  "
            f"{TYPE_AR.get(acc['type'],'')}  │  "
            f"رصيد طبيعي: {'DR↑' if nb=='dr' else 'CR↑'}"
        )
        self.t_dr_table.setRowCount(0)
        self.t_cr_table.setRowCount(0)
        for line in lines:
            if line["debit"] > 0:
                r = self.t_dr_table.rowCount()
                self.t_dr_table.insertRow(r)
                d = QTableWidgetItem(f"{line['date']}  {line['entry_desc']}")
                d.setToolTip(f"{line['date']}  {line['entry_desc']}")
                self.t_dr_table.setItem(r, 0, d)
                self.t_dr_table.setItem(r, 1,
                    QTableWidgetItem(f"{line['debit']:,.2f}"))
            if line["credit"] > 0:
                r = self.t_cr_table.rowCount()
                self.t_cr_table.insertRow(r)
                c = QTableWidgetItem(f"{line['date']}  {line['entry_desc']}")
                c.setToolTip(f"{line['date']}  {line['entry_desc']}")
                self.t_cr_table.setItem(r, 0, c)
                self.t_cr_table.setItem(r, 1,
                    QTableWidgetItem(f"{line['credit']:,.2f}"))

        self.lbl_dr_total.setText(f"الإجمالي: {data['total_debit']:,.2f}")
        self.lbl_cr_total.setText(f"الإجمالي: {data['total_credit']:,.2f}")

        bal    = data["balance"]
        b_side = "مدين" if bal >= 0 else "دائن"
        b_color = "#1565c0" if bal >= 0 else "#c62828"
        self.lbl_balance.setText(f"الرصيد ({b_side}): {abs(bal):,.2f}  ج")
        self.lbl_balance.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{b_color};"
            "background:#f0f8ff; border:1px solid #90caf9;"
            "border-radius:6px; padding:6px 16px;"
        )