"""
ui/tabs/accounting/investors/_investor_details.py
=================================================
_InvestorDetails — لوحة تفاصيل مستثمر واحد مع حذف الحركات.

تغييرات (v3 — SafeConnMixin لكلا الـ connections):
  - SafeConnMixin على acc_conn بدل self.acc_conn الثابت.
  - _erp_conn_ref مع _get_erp_conn() بدل self.erp_conn الثابت.
  - يستمع لـ bus.company_data_changed مع فلترة company_id.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.inventory.investors_repo import (
    calc_investor_summary, delete_investor_link,
)
from db.accounting.accounting_repo import delete_entry
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button,
)
from ui.events import bus
from ui.tabs.accounting.safe_conn_mixin import SafeConnMixin
from ._helpers import _stat_card


class _InvestorDetails(SafeConnMixin, QWidget):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        # acc_conn عبر SafeConnMixin
        self._init_safe_conn(acc_conn, "accounting")
        # erp_conn بنفس الأسلوب — نحفظه ونتحقق منه عند الاستخدام
        self._erp_conn_ref = erp_conn
        self._inv_id       = None
        self._company_id   = self._get_company_id()

        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._refresh()

    def _get_erp_conn(self):
        """يرجع erp conn صالح دايماً."""
        try:
            self._erp_conn_ref.execute("SELECT 1")
            return self._erp_conn_ref
        except Exception:
            pass
        try:
            from db.companies.company_state import company_state
            new = company_state._get_conn("erp")
            self._erp_conn_ref = new
            return new
        except Exception:
            return self._erp_conn_ref

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(8)

        self.lbl_title = QLabel("اختر مستثمراً لعرض تفاصيله")
        self.lbl_title.setStyleSheet(
            "font-weight:bold; font-size:13px; color:#1565c0;"
            "background:#e8f4fd; border:1px solid #90caf9;"
            "border-radius:6px; padding:8px 14px;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        cards = QHBoxLayout()
        cards.setSpacing(8)
        f1, self.lbl_cap  = _stat_card("إجمالي رأس المال",  "#2e7d32")
        f2, self.lbl_draw = _stat_card("إجمالي المسحوبات",  "#c62828")
        f3, self.lbl_net  = _stat_card("صافي الاستثمار",    "#1565c0")
        for f in (f1, f2, f3):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        root.addWidget(section_label("─── الحركات المالية ───"))

        self.table = make_table(
            ["LinkID", "التاريخ", "النوع", "المبلغ", "رقم القيد", "البيان"],
            stretch_col=5
        )
        self.table.setColumnHidden(0, True)
        setup_table_columns(self.table,
            widths={1: 90, 2: 90, 3: 110, 4: 95},
            stretch_col=5
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        btn_del_move = danger_button("🗑️  حذف الحركة المحددة")
        btn_del_move.setMinimumHeight(28)
        btn_del_move.clicked.connect(self._delete_movement)
        root.addLayout(buttons_row(btn_del_move))

    def load(self, inv_id: int):
        self._inv_id = inv_id
        self._refresh()

    def _refresh(self):
        if self._inv_id is None:
            return
        erp = self._get_erp_conn()
        acc = self._get_safe_conn()
        s   = calc_investor_summary(erp, self._inv_id, acc)
        if not s:
            return

        self.lbl_title.setText(
            f"👤  {s['investor_name']}  │  انضم: {s.get('joined_at','—')}"
        )
        self.lbl_cap.setText(f"{s['total_capital']:,.2f}  ج")
        self.lbl_draw.setText(f"{s['total_drawings']:,.2f}  ج")

        net   = s["net_investment"]
        color = "#1b5e20" if net >= 0 else "#b71c1c"
        self.lbl_net.setText(f"{net:,.2f}  ج")
        self.lbl_net.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{color};"
            " background:transparent; border:none;"
        )

        self.table.setRowCount(0)
        type_ar    = {"capital": "💰 رأس مال", "drawings": "💸 مسحوبات"}
        type_color = {"capital": "#2e7d32",    "drawings": "#c62828"}

        for e in s["entries"]:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(e.get("id", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(e.get("date", "—")))
            mt = e["move_type"]
            ti = QTableWidgetItem(type_ar.get(mt, mt))
            ti.setForeground(QColor(type_color.get(mt, "#333")))
            self.table.setItem(r, 2, ti)
            amt_item = QTableWidgetItem(f"{e['amount']:,.2f}")
            amt_item.setForeground(QColor(type_color.get(mt, "#333")))
            self.table.setItem(r, 3, amt_item)
            self.table.setItem(r, 4, QTableWidgetItem(e.get("ref_no") or "—"))
            self.table.setItem(r, 5, QTableWidgetItem(
                e.get("entry_desc") or e.get("notes") or "—"
            ))

    def _delete_movement(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر حركة أولاً")
            return
        link_id_item = self.table.item(row, 0)
        if not link_id_item or not link_id_item.text():
            return
        link_id  = int(link_id_item.text())
        ref_text = self.table.item(row, 4).text() if self.table.item(row, 4) else "—"
        move_ar  = self.table.item(row, 2).text() if self.table.item(row, 2) else "الحركة"

        reply = QMessageBox.question(
            self, "تأكيد حذف الحركة",
            f"حذف {move_ar} (قيد {ref_text})؟\n\n"
            "⚠️ سيتم حذف الحركة من سجل المستثمر وحذف القيد من الحسابات.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            erp = self._get_erp_conn()
            acc = self._get_safe_conn()
            link_row = erp.execute(
                "SELECT entry_id FROM investor_entries WHERE id=?", (link_id,)
            ).fetchone()
            if link_row:
                try:
                    delete_entry(acc, link_row["entry_id"])
                except Exception as e:
                    print(f"[InvestorDetails] could not delete acc entry: {e}")
            delete_investor_link(erp, link_id)
            bus.company_data_changed.emit(self._company_id or 0)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def clear(self):
        self._inv_id = None
        self.lbl_title.setText("اختر مستثمراً لعرض تفاصيله")
        self.table.setRowCount(0)
        for lbl in (self.lbl_cap, self.lbl_draw, self.lbl_net):
            lbl.setText("─")