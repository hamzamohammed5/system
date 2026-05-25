"""
ui/tabs/accounting/ledger/ledger_t_account.py
==============================================
_TAccountPanel — لوحة حساب T في دفتر الأستاذ.

[إصلاح v4 — توحيد الـ UI]:
  - PageHeader بدل lbl_title اليدوي.
  - BalanceDisplay بدل lbl_balance اليدوي.
  - الباقي كما هو (conn isolation من v3).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.accounting.accounting_repo import fetch_t_account
from db.accounting.accounting_schema import TYPE_AR
from ui.tabs.accounting.helpers import TYPE_COLORS
from ui.widgets.shared.panels import PageHeader, BalanceDisplay
from .ledger_filter_bar import _LedgerFilterBar
from .ledger_stat_cards import _StatCards


class _TAccountPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_data = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── هيدر الحساب (بدل lbl_title اليدوي) ──
        self._page_hdr = PageHeader(
            title="اختر حسابًا من القائمة لعرض حركاته",
            icon="📒",
            accent="#1565c0",
            compact=True,
        )
        root.addWidget(self._page_hdr)

        self._stats = _StatCards()
        root.addWidget(self._stats)

        self._filter = _LedgerFilterBar()
        self._filter.inp_search.textChanged.connect(self._apply_filter)
        self._filter.cmb_move_type.currentIndexChanged.connect(self._apply_filter)
        self._filter.dt_from.dateChanged.connect(self._apply_filter)
        self._filter.dt_to.dateChanged.connect(self._apply_filter)
        orig_reset = self._filter.reset

        def _reset_and_apply():
            orig_reset()
            self._apply_filter()

        self._filter.reset = _reset_and_apply
        root.addWidget(self._filter)

        t_frame = QFrame()
        t_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #c5cae9;
                border-radius: 8px;
            }
        """)
        t_lay = QHBoxLayout(t_frame)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(0)

        # جانب المدين
        dr_widget = QWidget()
        dr_widget.setStyleSheet("background: transparent;")
        dr_lay = QVBoxLayout(dr_widget)
        dr_lay.setContentsMargins(8, 8, 4, 8)
        dr_lay.setSpacing(4)

        dr_hdr = QLabel("📥  مدين  (DR)")
        dr_hdr.setAlignment(Qt.AlignCenter)
        dr_hdr.setStyleSheet("""
            font-weight: bold; color: #1565c0; font-size: 12px;
            background: #e3f2fd; border-radius: 5px; padding: 5px;
        """)
        dr_lay.addWidget(dr_hdr)
        self.t_dr_table = self._make_t_table()
        dr_lay.addWidget(self.t_dr_table, stretch=1)

        self.lbl_dr_total = QLabel("الإجمالي: 0.00")
        self.lbl_dr_total.setAlignment(Qt.AlignCenter)
        self.lbl_dr_total.setStyleSheet("""
            font-weight: bold; color: #1565c0; font-size: 11px;
            background: #e3f2fd; border-radius: 4px; padding: 4px 8px;
        """)
        dr_lay.addWidget(self.lbl_dr_total)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #1565c0; background: #c5cae9;")
        sep.setFixedWidth(2)

        # جانب الدائن
        cr_widget = QWidget()
        cr_widget.setStyleSheet("background: transparent;")
        cr_lay = QVBoxLayout(cr_widget)
        cr_lay.setContentsMargins(4, 8, 8, 8)
        cr_lay.setSpacing(4)

        cr_hdr = QLabel("📤  دائن  (CR)")
        cr_hdr.setAlignment(Qt.AlignCenter)
        cr_hdr.setStyleSheet("""
            font-weight: bold; color: #c62828; font-size: 12px;
            background: #fdecea; border-radius: 5px; padding: 5px;
        """)
        cr_lay.addWidget(cr_hdr)
        self.t_cr_table = self._make_t_table()
        cr_lay.addWidget(self.t_cr_table, stretch=1)

        self.lbl_cr_total = QLabel("الإجمالي: 0.00")
        self.lbl_cr_total.setAlignment(Qt.AlignCenter)
        self.lbl_cr_total.setStyleSheet("""
            font-weight: bold; color: #c62828; font-size: 11px;
            background: #fdecea; border-radius: 4px; padding: 4px 8px;
        """)
        cr_lay.addWidget(self.lbl_cr_total)

        t_lay.addWidget(dr_widget, stretch=1)
        t_lay.addWidget(sep)
        t_lay.addWidget(cr_widget, stretch=1)
        root.addWidget(t_frame, stretch=1)

        # ── رصيد الحساب (بدل lbl_balance اليدوي) ──
        self._balance_disp = BalanceDisplay()
        root.addWidget(self._balance_disp)

    def _make_t_table(self) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(["التاريخ", "رقم القيد", "البيان", "المبلغ"])
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setAlternatingRowColors(True)

        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        tbl.setColumnWidth(0, 90)
        tbl.setColumnWidth(1, 80)
        tbl.setColumnWidth(3, 90)

        tbl.setStyleSheet("""
            QTableWidget { border: none; background: transparent; gridline-color: #f0f0f0; }
            QHeaderView::section {
                background: #fafafa; border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px; font-weight: bold; font-size: 11px; color: #555;
            }
        """)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(True)
        return tbl

    def load(self, conn, account_id: int):
        data = fetch_t_account(conn, account_id)
        if not data:
            return
        self._all_data = data

        acc = data["account"]
        nb  = data["normal_balance"]

        type_ar  = TYPE_AR.get(acc["type"], "")
        color    = TYPE_COLORS.get(acc["type"], "#1565c0")
        nb_ar    = "DR↑" if nb == "dr" else "CR↑"

        # تحديث PageHeader بدل lbl_title
        self._page_hdr.set_title(
            f"{acc['code']} — {acc['name']}  │  {type_ar}  │  رصيد طبيعي: {nb_ar}"
        )
        self._apply_filter()

    def _apply_filter(self):
        if not self._all_data:
            return

        data    = self._all_data
        lines   = data["lines"]
        acc     = data["account"]
        nb      = data["normal_balance"]

        filtered = [ln for ln in lines if self._filter.matches(ln)]

        self.t_dr_table.setRowCount(0)
        self.t_cr_table.setRowCount(0)

        filt_dr = filt_cr = 0.0

        for line in filtered:
            if line["debit"] > 0:
                r = self.t_dr_table.rowCount()
                self.t_dr_table.insertRow(r)
                self._fill_t_row(self.t_dr_table, r, line, line["debit"], "#1565c0")
                filt_dr += line["debit"]

            if line["credit"] > 0:
                r = self.t_cr_table.rowCount()
                self.t_cr_table.insertRow(r)
                self._fill_t_row(self.t_cr_table, r, line, line["credit"], "#c62828")
                filt_cr += line["credit"]

        self.lbl_dr_total.setText(f"الإجمالي: {filt_dr:,.2f}")
        self.lbl_cr_total.setText(f"الإجمالي: {filt_cr:,.2f}")

        # BalanceDisplay بدل lbl_balance اليدوي
        self._balance_disp.set_debit_credit_balance(filt_dr, filt_cr)

        total_count = len(lines)
        filt_count  = len(filtered)
        filt_bal    = filt_dr - filt_cr
        self._stats.update(
            filt_dr, filt_cr, filt_bal,
            filt_count, nb, acc["type"]
        )
        self._filter.set_count(filt_count, total_count)

    def _fill_t_row(self, tbl: QTableWidget, r: int, line: dict,
                    amount: float, color: str):
        date_item = QTableWidgetItem(line.get("date", "—"))
        date_item.setTextAlignment(Qt.AlignCenter)
        date_item.setForeground(QColor("#555"))
        tbl.setItem(r, 0, date_item)

        ref_item = QTableWidgetItem(line.get("ref_no", "—"))
        ref_item.setTextAlignment(Qt.AlignCenter)
        ref_item.setForeground(QColor("#1565c0"))
        tbl.setItem(r, 1, ref_item)

        desc = line.get("description") or line.get("entry_desc") or "—"
        desc_item = QTableWidgetItem(desc)
        desc_item.setToolTip(f"{line.get('date','—')}  {desc}")
        tbl.setItem(r, 2, desc_item)

        amt_item = QTableWidgetItem(f"{amount:,.2f}")
        amt_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        amt_item.setForeground(QColor(color))
        f = QFont()
        f.setBold(True)
        amt_item.setFont(f)
        tbl.setItem(r, 3, amt_item)

    def clear(self):
        self._all_data = None
        self.t_dr_table.setRowCount(0)
        self.t_cr_table.setRowCount(0)
        self.lbl_dr_total.setText("الإجمالي: 0.00")
        self.lbl_cr_total.setText("الإجمالي: 0.00")
        self._balance_disp.reset()
        self._stats.clear()
        self._page_hdr.set_title("اختر حسابًا من القائمة لعرض حركاته")