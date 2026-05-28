"""
ui/tabs/accounting/investors/_investors_table.py
================================================
_InvestorsTable — جدول المستثمرين مع أزرار الإضافة والتعديل والحذف.

[إصلاح v5 — panels بدل ui.helpers]:
  - make_list_table من panels بدل make_table من ui.helpers
  - confirm_delete من panels
  - _make_btn من panels
  - auto_fit_columns من panels
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QTableWidgetItem, QMessageBox,
)
from PyQt5.QtGui  import QColor, QFont

from db.accounting.investors_repo import (
    fetch_investor, delete_investor,
    calc_all_investors_summary,
)
from ui.widgets.shared.panels import (
    make_list_table,
    _make_btn,
    confirm_delete,
    auto_fit_columns,
    form_section_title,
    ROW_HEIGHT_LARGE,
)
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ._investor_form    import _InvestorForm
from ._movement_dialog  import _MovementDialog

_COLS = ["ID", "الاسم", "تاريخ الانضمام", "رأس المال", "المسحوبات", "صافي الاستثمار"]
_COL_WIDTHS = {0: 40, 2: 100, 3: 110, 4: 100, 5: 120}


class _InvestorsTable(DualConnMixin, QWidget):
    def __init__(self, acc_conn, erp_conn, form: _InvestorForm,
                 on_select, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)
        self._form      = form
        self._on_select = on_select
        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(form_section_title("─── المستثمرون ───"))

        self.table = make_list_table(
            columns=_COLS,
            stretch_col=1,
            col_widths=_COL_WIDTHS,
        )
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self._selected_id())
        )
        root.addWidget(self.table, stretch=1)

        btn_edit    = _make_btn("✏️  تعديل", "normal")
        btn_del     = _make_btn("🗑️  حذف", "danger")
        btn_capital = _make_btn("💰  إضافة استثمار", "success")
        btn_draw    = _make_btn("💸  مسحوبات", "danger")

        for btn in (btn_edit, btn_del, btn_capital, btn_draw):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_capital.clicked.connect(lambda: self._open_movement("capital"))
        btn_draw.clicked.connect(lambda: self._open_movement("drawings"))

        from PyQt5.QtWidgets import QHBoxLayout
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for btn in (btn_edit, btn_del, btn_capital, btn_draw):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

    def _selected_id(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _load(self):
        summaries = calc_all_investors_summary(self._get_erp_conn())
        self.table.setRowCount(0)
        for s in summaries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
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

        if summaries:
            auto_fit_columns(
                self.table,
                fixed_cols=[0, 2, 3, 4, 5],
                stretch_col=1,
                min_width=40,
                max_width=200,
            )

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
        erp = self._get_erp_conn()
        inv = fetch_investor(erp, inv_id)
        if confirm_delete(self, inv["name"]):
            delete_investor(erp, inv_id)
            bus.company_data_changed.emit(self._company_id or 0)

    def _open_movement(self, move_type: str):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        erp = self._get_erp_conn()
        acc = self._get_safe_conn()
        inv = fetch_investor(erp, inv_id)
        dlg = _MovementDialog(
            acc, erp,
            inv_id, inv["name"], move_type, parent=self
        )
        dlg.exec_()