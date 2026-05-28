"""
ui/tabs/accounting/investors/_investor_details.py
=================================================
_InvestorDetails — لوحة تفاصيل مستثمر واحد مع حذف الحركات.

[تحسين v5]:
  - منطق بناء الجدول انتقل لـ _details_table.py
  - يستخدم StatRow / StatItem من panels بدل _stat_card المحلية
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.accounting.investors_repo import (
    calc_investor_summary, delete_investor_link,
)
from db.accounting.accounting_repo import delete_entry
from ui.helpers import buttons_row, section_label, danger_button
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.panels import StatRow, StatItem

from ._details_table import build_movements_table, fill_movement_row


class _InvestorDetails(DualConnMixin, QWidget):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)
        self._inv_id = None

        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            self._refresh()

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

        # ── بطاقات الإحصاء باستخدام StatRow الموحد ──
        self._stat_row = StatRow([
            StatItem(label="إجمالي رأس المال",  color="#2e7d32", icon="💰"),
            StatItem(label="إجمالي المسحوبات",  color="#c62828", icon="💸"),
            StatItem(label="صافي الاستثمار",    color="#1565c0", icon="⚖️"),
        ])
        root.addWidget(self._stat_row)

        root.addWidget(section_label("─── الحركات المالية ───"))

        # ── جدول الحركات ──
        self.table = build_movements_table()
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

        # تحديث StatRow
        self._stat_row.set_value(0, f"{s['total_capital']:,.2f}  ج")
        self._stat_row.set_value(1, f"{s['total_drawings']:,.2f}  ج")

        net   = s["net_investment"]
        color = "#1b5e20" if net >= 0 else "#b71c1c"
        self._stat_row.set_value(2, f"{net:,.2f}  ج", color=color)

        # ملء جدول الحركات
        self.table.setRowCount(0)
        for r_idx, entry in enumerate(s["entries"]):
            self.table.insertRow(r_idx)
            fill_movement_row(self.table, r_idx, entry)

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
        self._stat_row.reset_all()