"""
ui/tabs/accounting/investors/_investor_details.py
=================================================
_InvestorDetails — لوحة تفاصيل مستثمر واحد مع حذف الحركات.

[تحسين v5]:
  - منطق بناء الجدول انتقل لـ _details_table.py
  - يستخدم StatRow / StatItem من panels بدل _stat_card المحلية
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel,
)
from PyQt5.QtCore import Qt

from db.accounting.investors_repo import (
    calc_investor_summary, delete_investor_link,
)
from db.accounting.accounting_repo import delete_entry
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.components.button import make_btn
from ui.widgets.dialogs.confirm import confirm_action
from ui.widgets.dialogs.message import msg_info
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_MD, FS_SM

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

        self.lbl_title = QLabel(tr("investor_detail_placeholder"))
        self.lbl_title.setStyleSheet(
            f"font-weight:bold; font-size:{FS_MD}px; color:{_C['accent']};"
            f"background:{_C['info_bg']}; border:1px solid {_C['info_border']};"
            "border-radius:6px; padding:8px 14px;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        self._stat_row = StatRow([
            StatItem(label=tr("total_capital"),   color=_C["investor_capital_text"],  icon="💰"),
            StatItem(label=tr("total_drawings"),  color=_C["investor_drawings_text"], icon="💸"),
            StatItem(label=tr("net_investment"),  color=_C["accent"],                 icon="⚖️"),
        ])
        root.addWidget(self._stat_row)

        lbl_mov = QLabel(tr("investor_movements_header"))
        lbl_mov.setStyleSheet(
            f"font-weight:bold; color:{_C['accent']}; font-size:{FS_SM}px;"
            "background:transparent; border:none;"
        )
        root.addWidget(lbl_mov)

        self.table = build_movements_table()
        root.addWidget(self.table, stretch=1)

        btn_del_move = make_btn(tr("delete_movement_btn"), "danger")
        btn_del_move.setMinimumHeight(28)
        btn_del_move.clicked.connect(self._delete_movement)
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_del_move)
        btn_row.addStretch()
        root.addLayout(btn_row)

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
            f"👤  {s['investor_name']}  │  {tr('investor_joined')}: {s.get('joined_at','—')}"
        )

        self._stat_row.set_value(0, f"{s['total_capital']:,.2f}  {tr('currency_abbr')}")
        self._stat_row.set_value(1, f"{s['total_drawings']:,.2f}  {tr('currency_abbr')}")

        net   = s["net_investment"]
        color = _C["success"] if net >= 0 else _C["danger"]
        self._stat_row.set_value(2, f"{net:,.2f}  {tr('currency_abbr')}", color=color)

        self.table.setRowCount(0)
        for r_idx, entry in enumerate(s["entries"]):
            self.table.insertRow(r_idx)
            fill_movement_row(self.table, r_idx, entry)

    def _delete_movement(self):
        row = self.table.currentRow()
        if row == -1:
            msg_info(self, tr("warning"), tr("select_movement_first"))
            return
        link_id_item = self.table.item(row, 0)
        if not link_id_item or not link_id_item.text():
            return
        link_id  = int(link_id_item.text())
        ref_text = self.table.item(row, 4).text() if self.table.item(row, 4) else "—"
        move_ar  = self.table.item(row, 2).text() if self.table.item(row, 2) else tr("movement_type")

        if not confirm_action(
            self,
            tr("delete_movement_title"),
            tr("delete_movement_msg").format(type=move_ar, ref=ref_text),
        ):
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
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, tr("error"), str(e))

    def clear(self):
        self._inv_id = None
        self.lbl_title.setText(tr("investor_detail_placeholder"))
        self.table.setRowCount(0)
        self._stat_row.reset_all()