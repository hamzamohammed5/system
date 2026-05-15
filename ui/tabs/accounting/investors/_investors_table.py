"""
ui/tabs/accounting/investors/_investors_table.py
================================================
_InvestorsTable — جدول المستثمرين مع أزرار الإضافة والتعديل والحذف.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QTableWidgetItem, QMessageBox,
)
from PyQt5.QtGui  import QColor, QFont

from db.inventory.investors_repo import (
    fetch_investor, delete_investor,
    calc_all_investors_summary,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus
from ._investor_form    import _InvestorForm
from ._movement_dialog  import _MovementDialog


class _InvestorsTable(QWidget):
    def __init__(self, acc_conn, erp_conn, form: _InvestorForm,
                 on_select, parent=None):
        super().__init__(parent)
        self.acc_conn   = acc_conn
        self.erp_conn   = erp_conn
        self._form      = form
        self._on_select = on_select
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── المستثمرون ───"))

        self.table = make_table(
            ["ID", "الاسم", "تاريخ الانضمام",
             "رأس المال", "المسحوبات", "صافي الاستثمار"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 40, 2: 100, 3: 110, 4: 100, 5: 120},
            stretch_col=1
        )
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self._selected_id())
        )
        root.addWidget(self.table, stretch=1)

        btn_edit    = QPushButton("✏️  تعديل")
        btn_del     = danger_button("🗑️  حذف")
        btn_capital = QPushButton("💰  إضافة استثمار")
        btn_draw    = QPushButton("💸  مسحوبات")

        btn_capital.setStyleSheet(
            "QPushButton { background:#2e7d32; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#1b5e20; }"
        )
        btn_draw.setStyleSheet(
            "QPushButton { background:#c62828; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#b71c1c; }"
        )
        for btn in (btn_edit, btn_del, btn_capital, btn_draw):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_capital.clicked.connect(lambda: self._open_movement("capital"))
        btn_draw.clicked.connect(lambda: self._open_movement("drawings"))
        root.addLayout(buttons_row(btn_edit, btn_del, btn_capital, btn_draw))

    def _selected_id(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _load(self):
        summaries = calc_all_investors_summary(self.erp_conn)
        self.table.setRowCount(0)
        for s in summaries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(s["investor_id"])))
            self.table.setItem(r, 1, QTableWidgetItem(s["investor_name"]))
            self.table.setItem(r, 2, QTableWidgetItem(s.get("joined_at", "—")))

            cap_item = QTableWidgetItem(f"{s['total_capital']:,.2f}")
            cap_item.setForeground(QColor("#2e7d32"))
            self.table.setItem(r, 3, cap_item)

            draw_item = QTableWidgetItem(f"{s['total_drawings']:,.2f}")
            draw_item.setForeground(QColor("#c62828"))
            self.table.setItem(r, 4, draw_item)

            net      = s["net_investment"]
            net_item = QTableWidgetItem(f"{net:,.2f}")
            net_item.setForeground(
                QColor("#1b5e20") if net >= 0 else QColor("#b71c1c")
            )
            f = QFont()
            f.setBold(True)
            net_item.setFont(f)
            self.table.setItem(r, 5, net_item)

    def _edit(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        self._form.load_for_edit(inv_id)

    def _delete(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        inv = fetch_investor(self.erp_conn, inv_id)
        if confirm_delete(self, inv["name"]):
            delete_investor(self.erp_conn, inv_id)
            bus.data_changed.emit()

    def _open_movement(self, move_type: str):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        inv = fetch_investor(self.erp_conn, inv_id)
        dlg = _MovementDialog(
            self.acc_conn, self.erp_conn,
            inv_id, inv["name"], move_type, parent=self
        )
        dlg.exec_()